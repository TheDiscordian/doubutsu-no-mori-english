"""Mom source binding, atomic installation, legacy variant, and failure gates."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from mail_catalog import VROM as CATALOG_VROM,install as install_catalog
from mail_view_patch import VROM as VIEWER_VROM,install as install_reader
from mother_letters import START,POST,END,CODE_GUARDS,COMPLETE,install,patch,verify_code,verify_installation
from npc_mail_capture import source_hashes
from npc_mail_loader import VROM,CONFIG_OFFSET,configuration,install as install_loader
from runtime_module import MODULE_VROM,add_runtime_module,verify_test_module

CREATOR = ROOT/'build/letter-runtime-fixtures-01/mother'
PILOT = ROOT/'build/v0-hardware-fixes-02'

@unittest.skipUnless((CREATOR/'overlay.json').is_file(),'Compiled system creator required')
class MotherInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = {}
        cls.additions,cls.module = add_runtime_module(cls.native,cls.base,ROOT/'build/notice-seasonal-runtime')
        install_reader(cls.native,cls.base,cls.additions,cls.module,snapshots=True)
        install_catalog(cls.native,cls.additions,cls.module,ROOT/'build/mail-catalog')
        install_loader(cls.native,cls.base,cls.additions,cls.module,CREATOR)

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_whole_source_bound_install_changes_only_creator_and_two_publication_gates(self):
        replacements,additions,module = self.fixture()
        report = install(self.native,replacements,additions,module)
        self.assertEqual(report['complete_templates'],list(COMPLETE))
        self.assertEqual(report['unavailable_templates'],[0x136])
        self.assertEqual(len(report['parts']),342)
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        old,new = self.base[CODE_VROM],replacements[CODE_VROM]
        allowed = set()
        for start,end in ((START,POST),(0x800B90DC,0x800B910C),(0x800B9148,0x800B9150)):
            allowed.update(range(start-CODE_RAM,end-CODE_RAM))
        self.assertTrue(all(i in allowed or a == b for i,(a,b) in enumerate(zip(old,new))))
        self.assertEqual(new[START-CODE_RAM:END-CODE_RAM],
                         patch(old[START-CODE_RAM:END-CODE_RAM],int(module['symbols']['af_npc_mail_load'],16)))
        for address in (0x800B90DC,0x800B9148):
            word = struct.unpack_from('>I',new,address-CODE_RAM)[0]
            self.assertEqual(address+4+4*(word&65535),0x800B915C)
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module)

    def test_missing_dependencies_changed_native_code_or_variant_are_atomic_failures(self):
        for fault in ('variant','reader','catalog','module','creator','config',*range(len(CODE_GUARDS))):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault == 'variant': module['npc_mail_loader']['overlay'].pop('mother_letters')
            elif fault == 'reader': replacements.pop(VIEWER_VROM)
            elif fault == 'catalog': additions.pop(CATALOG_VROM)
            elif fault == 'module': module['module_sha256'] = '0'*64
            elif fault == 'creator': additions[VROM] = additions[VROM][:-16]
            elif fault == 'config':
                value = bytearray(additions[MODULE_VROM]);value[CONFIG_OFFSET+16] ^= 1
                additions[MODULE_VROM] = bytes(value)
            else:
                code = bytearray(replacements[CODE_VROM]);code[CODE_GUARDS[fault][0]-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises(ValueError): install(self.native,*fixture)
            self.assertEqual(fixture,before)

    def test_optional_variant_binds_new_entry_and_keeps_legacy_artifacts_valid(self):
        for directory,mother in (('shared-npc-capture-runtime-followup-01',False),('letter-runtime-fixtures-01/mother',True)):
            folder = ROOT/'build'/directory
            data,reloc = (folder/'overlay.bin').read_bytes(),(folder/'relocation.bin').read_bytes()
            report = json.loads((folder/'overlay.json').read_text())
            config = configuration(data,reloc,report,self.module)
            symbol = 'af_system_mail_create' if mother else 'af_npc_mail_create'
            self.assertEqual(config[4],report['symbols'][symbol])
            self.assertEqual(report['sources'],source_hashes(mother_letters=mother))
            for value in (False,None,0,1,'true'):
                with self.assertRaises(ValueError): configuration(data,reloc,{**report,'mother_letters':value},self.module)
            changed = deepcopy(report);changed['sources'] = {}
            with self.assertRaises(ValueError): configuration(data,reloc,changed,self.module)

    @unittest.skipUnless((PILOT/'build.json').is_file(),'Completed combined cartridge required')
    def test_built_rom_matches_installed_creator_guards_and_reader(self):
        directory = PILOT
        built = (directory/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((directory/'build.json').read_text())
        self.assertEqual(sha256(built),report['output_sha256'])
        verify_test_module(built,report['runtime_module'])
        verify_installation(built,self.native,report['runtime_module'],report['mother_letters'])
        wrong = deepcopy(report['mother_letters']);wrong['complete_templates'].append(0x136)
        with self.assertRaises(ValueError): verify_installation(built,self.native,report['runtime_module'],wrong)

    def test_cli_requires_creator_before_reading_rom(self):
        result = subprocess.run([sys.executable,str(ROOT/'tools/build.py'),'--rom','not-read.z64',
                                 '--english-mother-letters'],capture_output=True,text=True)
        self.assertEqual(result.returncode,2)
        self.assertIn('--english-mother-letters requires',result.stderr)


if __name__ == '__main__': unittest.main()
