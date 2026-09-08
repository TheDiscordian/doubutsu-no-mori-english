"""HRA source identity, three instruction ranges, and atomic installation."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from academy_letters import GUARDS,START,END,TEMPLATES,install,patches,verify_installation
from aflib import CODE_RAM,CODE_VROM,sha256
from departed_letters import install as install_departed
from extended_items import install as install_items
from mail_catalog import VROM as CATALOG_VROM,install as install_catalog
from mail_view_patch import install as install_reader
from mother_letters import install as install_mother
from npc_mail_capture import source_hashes
from npc_mail_loader import VROM,CONFIG_OFFSET,configuration,install as install_loader
from runtime_module import MODULE_VROM,add_runtime_module,verify_test_module
from villager_event_letters import START as EVENT_START,install as install_events


@unittest.skipUnless((ROOT/'build/academy-mail-creator/overlay.json').is_file(),'Compiled academy creator required')
class AcademyInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = {}
        cls.additions,cls.module = add_runtime_module(cls.native,cls.base,ROOT/'build/runtime-module')
        install_reader(cls.native,cls.base,cls.additions,cls.module,snapshots=True)
        install_items(cls.native,cls.additions,cls.module,ROOT/'build/mapped-items-final-resource')
        install_catalog(cls.native,cls.additions,cls.module,ROOT/'build/mail-catalog')
        install_loader(cls.native,cls.base,cls.additions,cls.module,ROOT/'build/academy-mail-creator')
        install_mother(cls.native,cls.base,cls.additions,cls.module)
        install_departed(cls.native,cls.base,cls.additions,cls.module)
        install_events(cls.native,cls.base,cls.additions,cls.module)

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_complete_parts_and_exactly_three_allowed_ranges(self):
        replacements,additions,module = self.fixture();report = install(self.native,replacements,additions,module)
        self.assertEqual(report['classic_templates'],list(TEMPLATES));self.assertEqual(len(report['parts']),60)
        self.assertTrue(all(row['fields']==[] for row in report['parts']))
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        old,new = self.base[CODE_VROM],replacements[CODE_VROM]
        changes = patches(old,int(module['symbols']['af_npc_mail_load'],16));allowed = set()
        self.assertEqual([(at,len(v)) for at,v in changes.items()],[(START,END-START),(0x8009CE2C,80),(0x8009CF94,4)])
        for at,value in changes.items():
            offset = at-CODE_RAM;allowed.update(range(offset,offset+len(value)))
            self.assertEqual(new[offset:offset+len(value)],value)
        self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(old,new))))
        for at,target in ((0x8009CE2C,0x8009CF9C),(0x8009CE64,0x8009CE74)):
            word = struct.unpack_from('>I',new,at-CODE_RAM)[0]
            self.assertEqual(word>>16,0x1040);self.assertEqual(at+4+4*(word&65535),target)
        self.assertEqual(struct.unpack_from('>I',new,0x8009CF94-CODE_RAM)[0],0x0C027399)
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module)

    def test_missing_dependencies_and_changed_source_reject_atomically(self):
        for fault in ('variant','catalog','module','creator','config','events',*range(len(GUARDS))):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault == 'variant': module['npc_mail_loader']['overlay'].pop('academy_letters')
            elif fault in ('catalog','module','creator'):
                additions.pop({'catalog':CATALOG_VROM,'module':MODULE_VROM,'creator':VROM}[fault])
            elif fault == 'config':
                value = bytearray(additions[MODULE_VROM]);value[CONFIG_OFFSET+16] ^= 1
                additions[MODULE_VROM] = bytes(value)
            else:
                at = EVENT_START if fault == 'events' else GUARDS[fault][0]
                code = bytearray(replacements[CODE_VROM]);code[at-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises(ValueError): install(self.native,*fixture)
            self.assertEqual(fixture,before)

    def test_optional_variant_and_earlier_exports_remain_valid(self):
        directory = ROOT/'build/academy-mail-creator'
        data,reloc = (directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes()
        report = json.loads((directory/'overlay.json').read_text())
        self.assertEqual(configuration(data,reloc,report,self.module)[4],report['symbols']['af_academy_mail_create'])
        self.assertEqual(report['sources'],source_hashes(mother_letters=True,departed_letters=True,villager_events=True,academy_letters=True))
        for value in (False,None,0,1,'true'):
            with self.assertRaises(ValueError): configuration(data,reloc,{**report,'academy_letters':value},self.module)
        with self.assertRaises(ValueError): source_hashes(mother_letters=True,departed_letters=True,academy_letters=True)

    @unittest.skipUnless((ROOT/'build/academy-letters-pilot/build.json').is_file(),'Completed academy pilot required')
    def test_actual_built_rom_and_changed_report_rejection(self):
        directory = ROOT/'build/academy-letters-pilot';built = (directory/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((directory/'build.json').read_text());self.assertEqual(sha256(built),report['output_sha256'])
        verify_test_module(built,report['runtime_module'])
        verify_installation(built,self.native,report['runtime_module'],report['academy_letters'])
        wrong = deepcopy(report['academy_letters']);wrong['classic_templates'].append(0x34)
        with self.assertRaises(ValueError): verify_installation(built,self.native,report['runtime_module'],wrong)

    def test_clis_reject_missing_dependencies_before_inputs(self):
        for script,args,expected in (
                ('build.py',['--rom','not-read.z64','--english-academy-letters'],'--english-academy-letters requires'),
                ('build_npc_mail_capture.py',['--academy-letters'],'--academy-letters requires')):
            result = subprocess.run([sys.executable,str(ROOT/'tools'/script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn(expected,result.stderr)


if __name__ == '__main__': unittest.main()
