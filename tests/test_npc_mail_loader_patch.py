"""Complete reader/resource/capture/delivery installation and test-ROM binding."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from mail_catalog import VROM as CATALOG_VROM,install as install_catalog
from mail_view_patch import VROM as VIEWER_VROM,RELOC_VROM,install as install_reader
from npc_mail_capture import HOOKS
from npc_mail_delivery import CREATOR_CALL,FAILURE_BRANCH,ARGUMENT_MOVE,START,END,patch as gate
from npc_mail_loader import VROM,CONFIG_OFFSET,configuration,verify_configuration,install
from runtime_module import MODULE_RAM,MODULE_VROM,add_runtime_module,verify_test_module
from test_retail import ROM_PATH

MODULE = ROOT/'build/notice-seasonal-runtime'
OVERLAY = ROOT/'build/npc-mail-capture-runtime-followup-01'
CATALOG = ROOT/'build/mail-catalog'


@unittest.skipUnless(ROM_PATH.is_file() and all((p/name).is_file() for p,name in
                     ((MODULE,'module.json'),(OVERLAY,'overlay.json'),(CATALOG,'catalog.json'))),
                     'Current local module, NPC creator, catalog, and original ROM required')
class NpcMailLoaderPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes();cls.base = {}
        cls.additions,cls.module = add_runtime_module(cls.rom,cls.base,MODULE)
        install_reader(cls.rom,cls.base,cls.additions,cls.module,snapshots=True)
        install_catalog(cls.rom,cls.additions,cls.module,CATALOG)

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def reject(self,fixture,directory=OVERLAY):
        before = deepcopy(fixture)
        with self.assertRaises(ValueError): install(self.rom,*fixture,directory)
        self.assertEqual(fixture,before)

    def test_exact_capture_calls_submission_gate_and_complete_blob_are_installed_together(self):
        replacements,additions,module = self.fixture()
        report = install(self.rom,replacements,additions,module,OVERLAY)
        code = replacements[CODE_VROM];before = self.base[CODE_VROM]
        changed = set()
        for address,_,name in HOOKS:
            offset = address-CODE_RAM
            changed.update(range(offset,offset+4))
            self.assertEqual(code[offset:offset+4],struct.pack('>I',0x0C000000|((int(module['symbols'][name],16)>>2)&0x3FFFFFF)))
        for address in (CREATOR_CALL,FAILURE_BRANCH,ARGUMENT_MOVE):
            changed.update(range(address-CODE_RAM,address-CODE_RAM+4))
        self.assertEqual(code[START-CODE_RAM:END-CODE_RAM],gate(before[START-CODE_RAM:END-CODE_RAM],int(module['symbols']['af_npc_mail_load'],16)))
        self.assertTrue(all(i in changed or a == b for i,(a,b) in enumerate(zip(before,code))))
        image,reloc = (OVERLAY/'overlay.bin').read_bytes(),(OVERLAY/'relocation.bin').read_bytes()
        self.assertEqual(additions[VROM],image+reloc)
        self.assertEqual(report['temporary_allocation_bytes'],len(image)+len(reloc)+5344+15)
        verify_configuration(additions[MODULE_VROM],additions[VROM],module)
        module_data = bytearray(additions[MODULE_VROM]);module_data[CONFIG_OFFSET:CONFIG_OFFSET+32] = bytes(32)
        self.assertEqual(module_data,self.additions[MODULE_VROM])
        self.assertEqual(replacements[VIEWER_VROM],self.base[VIEWER_VROM])
        self.reject((replacements,additions,module))

    def test_missing_reader_catalog_or_module_fails_without_partial_installation(self):
        for key in (CODE_VROM,VIEWER_VROM,RELOC_VROM,MODULE_VROM,CATALOG_VROM):
            fixture = self.fixture()
            if key in fixture[0]: fixture[0].pop(key)
            else: fixture[1].pop(key)
            # Main code has an original fallback; the standalone installer can
            # add its own hooks there if the separately installed reader exists.
            if key == CODE_VROM: continue
            with self.subTest(resource=key): self.reject(fixture)
        fixture = self.fixture();fixture[2]['runtime_sources'] = {};self.reject(fixture)
        fixture = self.fixture();fixture[2]['source_sha256'] = '0'*64;self.reject(fixture)
        for offset in (56,60,64,68,CONFIG_OFFSET,CONFIG_OFFSET+31,512):
            fixture = self.fixture();data = bytearray(fixture[1][MODULE_VROM]);data[offset] ^= 1
            fixture[1][MODULE_VROM] = bytes(data);self.reject(fixture)
        for key in (VIEWER_VROM,RELOC_VROM,CATALOG_VROM):
            fixture = self.fixture();target = fixture[0] if key in fixture[0] else fixture[1]
            data = bytearray(target[key]);data[-1] ^= 1;target[key] = bytes(data)
            self.reject(fixture)

    def test_capture_delivery_overlap_bad_targets_and_unavailable_dma_space_fail_atomically(self):
        for address in [at for at,_,_ in HOOKS]+[CREATOR_CALL,FAILURE_BRANCH,ARGUMENT_MOVE,0x800A92D0]:
            fixture = self.fixture();data = bytearray(fixture[0][CODE_VROM]);data[address-CODE_RAM] ^= 1
            fixture[0][CODE_VROM] = bytes(data)
            with self.subTest(address=address): self.reject(fixture)
        for target in (0,MODULE_RAM,MODULE_RAM+0x301,MODULE_RAM+0x6000,0x80400000):
            fixture = self.fixture();fixture[2]['symbols']['af_npc_mail_load'] = f'{target:08X}'
            self.reject(fixture)
        for vrom in (VROM,VROM-16,VROM+16):
            fixture = self.fixture();fixture[1][vrom] = bytes(64);self.reject(fixture)
        with patch('npc_mail_loader.DMA_END',0): self.reject(self.fixture())

    def test_stale_overlay_sources_metadata_or_payload_are_rejected(self):
        data,reloc = (OVERLAY/'overlay.bin').read_bytes(),(OVERLAY/'relocation.bin').read_bytes()
        original = json.loads((OVERLAY/'overlay.json').read_text())
        with tempfile.TemporaryDirectory(prefix='af-npc-loader-install-') as temp:
            directory = Path(temp)
            (directory/'overlay.bin').write_bytes(data);(directory/'relocation.bin').write_bytes(reloc)
            for key,value in (('module_sha256','0'*64),('sources',{}),('imports',{}),('symbols',{})):
                report = deepcopy(original);report[key] = value
                (directory/'overlay.json').write_text(json.dumps(report));self.reject(self.fixture(),directory)
            (directory/'overlay.json').write_text(json.dumps(original))
            for name,content in (('overlay.bin',data),('relocation.bin',reloc)):
                bad = bytearray(content);bad[-1] ^= 1;(directory/name).write_bytes(bad)
                self.reject(self.fixture(),directory);(directory/name).write_bytes(content)

    def test_native_symbol_binding_requires_external_whole_blob_approval(self):
        replacements,additions,module = self.fixture()
        install(self.rom,replacements,additions,module,OVERLAY)
        class Entry:
            def __init__(self,data): self.data = data
            def extract(self,rom): return self.data
        files = {vrom:Entry(data) for vrom,data in additions.items()}
        with patch('runtime_module.by_vrom',return_value=files):
            verify_test_module(b'synthetic',module)
            for field in range(8):
                binary = bytearray(additions[MODULE_VROM]);binary[CONFIG_OFFSET+field*4+3] ^= 1
                files[MODULE_VROM] = Entry(bytes(binary))
                with self.assertRaises(ValueError): verify_test_module(b'synthetic',module)
            files[MODULE_VROM] = Entry(additions[MODULE_VROM])
            with self.assertRaisesRegex(ValueError,'configured build report'):
                verify_test_module(b'synthetic',self.module)
            blob = bytearray(additions[VROM]);blob[-1] ^= 1;files[VROM] = Entry(bytes(blob))
            with self.assertRaises(ValueError): verify_test_module(b'synthetic',module)
            files.pop(VROM)
            with self.assertRaisesRegex(ValueError,'no cartridge resource'):
                verify_test_module(b'synthetic',module)
        overlay = json.loads((OVERLAY/'overlay.json').read_text())
        expected = configuration((OVERLAY/'overlay.bin').read_bytes(),(OVERLAY/'relocation.bin').read_bytes(),overlay,module)
        self.assertEqual(expected,module['npc_mail_loader']['configuration'])


class NpcMailLoaderCommandTests(unittest.TestCase):
    def test_optional_generation_requires_the_complete_runtime_reader_and_grading_flags(self):
        result = subprocess.run([sys.executable,str(ROOT/'tools/build.py'),'--rom','not-read.z64',
                                 '--npc-mail-generation','not-read'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('--npc-mail-generation requires',result.stderr)


if __name__ == '__main__': unittest.main()
