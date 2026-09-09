"""Score-owner installation, fixed relocation layout, and composed HRA gates."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from academy_letters import install as install_advice,verify_installation as verify_advice
from academy_score_letters import COMPLETE,RAM,VROM,RELOCATION,install,verify_installation,patched_overlay,scheduler_patch
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from departed_letters import install as install_departed
from extended_items import install as install_items
from mail_catalog import install as install_catalog
from mail_view_patch import install as install_reader
from mother_letters import install as install_mother
from npc_mail_capture import source_hashes
from npc_mail_loader import CONFIG_OFFSET,VROM as CREATOR,configuration,install as install_loader
from runtime_module import MODULE_VROM,add_runtime_module,verify_test_module
from villager_event_letters import install as install_events


@unittest.skipUnless((ROOT/'build/academy-score-mail-creator/overlay.json').is_file(),'Compiled score creator required')
class AcademyScoreInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = {}
        cls.additions,cls.module = add_runtime_module(cls.native,cls.base,ROOT/'build/runtime-module')
        install_reader(cls.native,cls.base,cls.additions,cls.module,snapshots=True)
        install_items(cls.native,cls.additions,cls.module,ROOT/'build/mapped-items-final-resource')
        install_catalog(cls.native,cls.additions,cls.module,ROOT/'build/mail-catalog')
        install_loader(cls.native,cls.base,cls.additions,cls.module,ROOT/'build/academy-score-mail-creator')
        for installer in (install_mother,install_departed,install_events,install_advice):
            installer(cls.native,cls.base,cls.additions,cls.module)

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_exact_owned_ranges_and_retained_scoring_data(self):
        replacements,additions,module = self.fixture();report = install(self.native,replacements,additions,module)
        self.assertEqual(report['complete_templates'],list(COMPLETE));self.assertEqual(len(report['parts']),63)
        self.assertEqual(report['unavailable_templates'],[0x3D]);self.assertEqual(len(report['series']),55)
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        self.assertEqual(set(replacements)-set(self.base),{VROM,RELOCATION})
        at,value = scheduler_patch();before = self.base[CODE_VROM];after = replacements[CODE_VROM]
        self.assertEqual(after[at-CODE_RAM:at-CODE_RAM+len(value)],value)
        restored = bytearray(after);restored[at-CODE_RAM:at-CODE_RAM+len(value)] = before[at-CODE_RAM:at-CODE_RAM+len(value)]
        self.assertEqual(restored,before)
        files = by_vrom(self.native);original = files[VROM].extract(self.native)
        restored = bytearray(replacements[VROM])
        for start,end in ((0x80925E48,0x809260A4),(0x809281C8,0x809281D4)):
            restored[start-RAM:end-RAM] = original[start-RAM:end-RAM]
        self.assertEqual(restored,original)
        data,reloc,sections = patched_overlay(self.native,int(module['symbols']['af_npc_mail_load'],16))
        self.assertEqual((replacements[VROM],replacements[RELOCATION]),(data,reloc))
        self.assertEqual(sections,(10704,5024,0,1248,245));self.assertEqual(len(reloc),1024)
        old = files[RELOCATION].extract(self.native)
        old_rows = set(struct.unpack_from('>248I',old,20));new_rows = set(struct.unpack_from('>245I',reloc,20))
        self.assertEqual(old_rows-new_rows,{0x440004C8,0x44000524,0x44000540,0x44000560})
        self.assertEqual(new_rows-old_rows,{0x440004B8});self.assertEqual(reloc[-4:],old[-4:])
        self.assertEqual(reloc[1000:1020],bytes(20))
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module)

    def test_missing_dependencies_and_overlap_reject_atomically(self):
        for fault in ('variant','catalog','module','creator','items','config','item_pointer','item_header','advice','scheduler','overlay','relocation'):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault == 'variant': module['npc_mail_loader']['overlay'].pop('academy_scores')
            elif fault in ('catalog','module','creator','items'):
                additions.pop({'catalog':0x03000000,'module':MODULE_VROM,'creator':CREATOR,'items':0x02A00000}[fault])
            elif fault in ('config','item_pointer','item_header'):
                vrom = 0x02A00000 if fault=='item_header' else MODULE_VROM
                offset = {'config':CONFIG_OFFSET+16,'item_pointer':56,'item_header':0}[fault]
                data = bytearray(additions[vrom]);data[offset] ^= 1;additions[vrom] = bytes(data)
            elif fault in ('overlay','relocation'): replacements[VROM if fault=='overlay' else RELOCATION] = b'conflict'
            else:
                offset = (0x8009CE64 if fault=='advice' else 0x8009CF28)-CODE_RAM
                code = bytearray(replacements[CODE_VROM]);code[offset] ^= 1;replacements[CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises(ValueError): install(self.native,*fixture)
            self.assertEqual(fixture,before)

    def test_optional_dispatch_and_bound_series_resource(self):
        directory = ROOT/'build/academy-score-mail-creator'
        data,reloc = (directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes()
        report = json.loads((directory/'overlay.json').read_text())
        self.assertEqual(configuration(data,reloc,report,self.module)[4],report['symbols']['af_academy_score_mail_create'])
        self.assertEqual(report['sources'],source_hashes(mother_letters=True,departed_letters=True,villager_events=True,academy_letters=True,academy_scores=True))
        self.assertLessEqual(len(data),32768)
        for field in ('academy_scores','academy_series_sha256'):
            wrong = deepcopy(report);wrong.pop(field)
            with self.assertRaises(ValueError): configuration(data,reloc,wrong,self.module)
        wrong = deepcopy(report);wrong['academy_series_sha256'] = '0'*64
        with self.assertRaises(ValueError): configuration(data,reloc,wrong,self.module)
        with self.assertRaises(ValueError): source_hashes(mother_letters=True,departed_letters=True,villager_events=True,academy_scores=True)

    @unittest.skipUnless((ROOT/'build/academy-score-letters-pilot/build.json').is_file(),'Completed score ROM required')
    def test_actual_rom_and_both_composed_hra_verifiers(self):
        directory = ROOT/'build/academy-score-letters-pilot';built = (directory/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((directory/'build.json').read_text());self.assertEqual(sha256(built),report['output_sha256'])
        verify_test_module(built,report['runtime_module'])
        verify_advice(built,self.native,report['runtime_module'],report['academy_letters'])
        verify_installation(built,self.native,report['runtime_module'],report['academy_score_letters'])
        for key,value in (('complete_templates',list(range(0x34,0x49))),('scheduler_sha256','0'*64),('relocation_sha256','0'*64)):
            wrong = deepcopy(report['academy_score_letters']);wrong[key] = value
            with self.assertRaises(ValueError): verify_installation(built,self.native,report['runtime_module'],wrong)

    def test_cli_dependencies_before_reading_inputs(self):
        for script,args,expected in (
                ('build.py',['--rom','not-read.z64','--english-academy-scores'],'--english-academy-scores requires'),
                ('build_npc_mail_capture.py',['--academy-scores'],'--academy-scores requires')):
            result = subprocess.run([sys.executable,str(ROOT/'tools'/script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn(expected,result.stderr)


if __name__ == '__main__': unittest.main()
