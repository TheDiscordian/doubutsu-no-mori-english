"""Departed-letter source binding, installation boundaries, and creator variants."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,sha256
from departed_letters import START,POST,END,GUARDS,TEMPLATES,install,patch,verify_installation
from mail_catalog import VROM as CATALOG_VROM,install as install_catalog
from mail_view_patch import install as install_reader
from mother_letters import START as MOM_START,install as install_mother
from npc_mail_capture import source_hashes
from npc_mail_loader import VROM,CONFIG_OFFSET,configuration,install as install_loader
from runtime_module import MODULE_VROM,add_runtime_module,verify_test_module


@unittest.skipUnless((ROOT/'build/departed-mail-creator/overlay.json').is_file(),'Compiled departed creator required')
class DepartedInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = {}
        cls.additions,cls.module = add_runtime_module(cls.native,cls.base,ROOT/'build/runtime-module')
        install_reader(cls.native,cls.base,cls.additions,cls.module,snapshots=True)
        install_catalog(cls.native,cls.additions,cls.module,ROOT/'build/mail-catalog')
        install_loader(cls.native,cls.base,cls.additions,cls.module,ROOT/'build/departed-mail-creator')
        install_mother(cls.native,cls.base,cls.additions,cls.module)

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_all_parts_bound_and_only_creator_and_success_gates_change(self):
        replacements,additions,module = self.fixture()
        report = install(self.native,replacements,additions,module)
        self.assertEqual(report['classic_templates'],list(TEMPLATES))
        self.assertEqual(len(report['parts']),54)
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        old,new = self.base[CODE_VROM],replacements[CODE_VROM]
        allowed = set(range(START-CODE_RAM,POST-CODE_RAM))|set(range(0x800B9E00-CODE_RAM,0x800B9E34-CODE_RAM))
        self.assertTrue(all(i in allowed or a == b for i,(a,b) in enumerate(zip(old,new))))
        self.assertEqual(new[START-CODE_RAM:END-CODE_RAM],
                         patch(old[START-CODE_RAM:END-CODE_RAM],int(module['symbols']['af_npc_mail_load'],16)))
        for address in (0x800B9E10,0x800B9E20):
            word = struct.unpack_from('>I',new,address-CODE_RAM)[0]
            self.assertEqual(word>>16,0x1040)
            self.assertEqual(address+4+4*(word&65535),0x800B9E34)
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module)

    def test_dependencies_and_all_native_guards_fail_without_partial_writes(self):
        for fault in ('variant','catalog','module','creator','config','mother',*range(len(GUARDS))):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault == 'variant': module['npc_mail_loader']['overlay'].pop('departed_letters')
            elif fault == 'catalog': additions.pop(CATALOG_VROM)
            elif fault == 'module': additions.pop(MODULE_VROM)
            elif fault == 'creator': additions[VROM] = additions[VROM][:-16]
            elif fault == 'config':
                value = bytearray(additions[MODULE_VROM]);value[CONFIG_OFFSET+16] ^= 1
                additions[MODULE_VROM] = bytes(value)
            else:
                code = bytearray(replacements[CODE_VROM])
                code[(MOM_START if fault == 'mother' else GUARDS[fault][0])-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises(ValueError): install(self.native,*fixture)
            self.assertEqual(fixture,before)

    def test_legacy_and_extended_variants_remain_source_bound(self):
        for directory,mother,departed,entry in (
                ('npc-mail-capture',False,False,'af_npc_mail_create'),
                ('mother-mail-creator',True,False,'af_system_mail_create'),
                ('departed-mail-creator',True,True,'af_departed_mail_create')):
            folder = ROOT/'build'/directory
            data,reloc = (folder/'overlay.bin').read_bytes(),(folder/'relocation.bin').read_bytes()
            report = json.loads((folder/'overlay.json').read_text())
            self.assertEqual(configuration(data,reloc,report,self.module)[4],report['symbols'][entry])
            self.assertEqual(report['sources'],source_hashes(mother_letters=mother,departed_letters=departed))
            for value in (False,None,0,1,'true'):
                with self.assertRaises(ValueError):
                    configuration(data,reloc,{**report,'departed_letters':value},self.module)
        with self.assertRaises(ValueError): source_hashes(departed_letters=True)
        changed = deepcopy(report);changed.pop('mother_letters')
        with self.assertRaises(ValueError): configuration(data,reloc,changed,self.module)
        changed = deepcopy(report);changed['sources'].pop('overlays/mail_generation/departed_creator.c')
        with self.assertRaises(ValueError): configuration(data,reloc,changed,self.module)

    @unittest.skipUnless((ROOT/'build/departed-letters-pilot/build.json').is_file(),'Completed departed pilot required')
    def test_actual_built_rom_matches_creator_and_retained_native_helpers(self):
        directory = ROOT/'build/departed-letters-pilot'
        built = (directory/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((directory/'build.json').read_text())
        self.assertEqual(sha256(built),report['output_sha256'])
        verify_test_module(built,report['runtime_module'])
        verify_installation(built,self.native,report['runtime_module'],report['departed_letters'])
        for field,value in (('classic_templates',[]),('patch_sha256','0'*64)):
            wrong = deepcopy(report['departed_letters']);wrong[field] = value
            with self.assertRaises(ValueError): verify_installation(built,self.native,report['runtime_module'],wrong)

    def test_patch_rejects_bad_loader_and_changed_source(self):
        original = self.base[CODE_VROM][START-CODE_RAM:END-CODE_RAM]
        loader = int(self.module['symbols']['af_npc_mail_load'],16)
        for target in (True,0,loader+1,0x80400000):
            with self.assertRaises(ValueError): patch(original,target)
        with self.assertRaises(ValueError): patch(original[:-4],loader)
        changed = bytearray(original);changed[-1] ^= 1
        with self.assertRaises(ValueError): patch(changed,loader)

    def test_both_clis_require_the_system_dispatcher_before_reading_inputs(self):
        for script,args,expected in (
                ('build.py',['--rom','not-read.z64','--english-departed-letters'],
                 '--english-departed-letters requires'),
                ('build_npc_mail_capture.py',['--departed-letters'],'--departed-letters requires')):
            result = subprocess.run([sys.executable,str(ROOT/'tools'/script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2)
            self.assertIn(expected,result.stderr)


if __name__ == '__main__': unittest.main()
