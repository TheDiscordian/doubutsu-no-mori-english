"""Installed quest reply code, complete accounting, and retained earlier text."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,sha256
from npc_mail_capture import source_hashes
from npc_mail_loader import VROM,configuration
from runtime_layout import MODULE_VROM
from runtime_module import verify_test_module
from quest_reply_letters import START,REGIONS,GUARDS,TEMPLATES,install,validate,verify_installation
from translation_progress import measure

BUILD = ROOT/'build/quest-reply-letters-pilot'
PREVIOUS = ROOT/'build/secret-letters-pilot'
OWNERS = ROOT/'build/quest-reply-owners'


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete local quest reply ROM required')
class QuestReplyInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text());cls.module = cls.report['runtime_module']
        cls.files = by_vrom(cls.built)
        original = by_vrom(cls.native)[CODE_VROM].extract(cls.native)
        code = bytearray(cls.files[CODE_VROM].extract(cls.built))
        for a,b in REGIONS: code[a-CODE_RAM:b-CODE_RAM] = original[a-CODE_RAM:b-CODE_RAM]
        cls.base = {CODE_VROM:bytes(code)}
        cls.additions = {int(v,16):cls.files[int(v,16)].extract(cls.built) for v in cls.report['added_files']}

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_complete_install_only_changes_creator_and_copy_gate(self):
        replacements,additions,module = self.fixture()
        report = install(self.native,replacements,additions,module,OWNERS)
        self.assertEqual(report,self.report['quest_replies'])
        self.assertEqual(len(report['parts']),216);self.assertEqual(report['complete_templates'],list(TEMPLATES))
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        self.assertEqual(replacements[CODE_VROM],self.files[CODE_VROM].extract(self.built))
        allowed = {i for a,b in REGIONS for i in range(a-CODE_RAM,b-CODE_RAM)}
        self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(self.base[CODE_VROM],replacements[CODE_VROM]))))
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module,OWNERS)

    def test_failed_install_never_publishes_and_native_rank_reward_code_is_guarded(self):
        for fault in ('variant','catalog','module','creator','items','config',*range(len(GUARDS))):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault=='variant': module['npc_mail_loader']['overlay'].pop('quest_replies')
            elif fault in ('catalog','module','creator','items'):
                additions.pop({'catalog':0x030A0000,'module':MODULE_VROM,'creator':VROM,'items':0x02A00000}[fault])
            elif fault=='config':
                value = bytearray(additions[MODULE_VROM]);value[0x58] ^= 1;additions[MODULE_VROM] = bytes(value)
            else:
                value = bytearray(replacements[CODE_VROM]);value[GUARDS[fault][0]-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(value)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)):
                install(self.native,*fixture,OWNERS)
            self.assertEqual(fixture,before)

    def test_exact_assembly_and_creator_exports_reject_rehashed_mutations(self):
        data = (OWNERS/'owners.bin').read_bytes();report = json.loads((OWNERS/'owners.json').read_text())
        for i in range(0,len(data),4):
            changed = bytearray(data);changed[i+3] ^= 1
            with self.assertRaises(ValueError): validate(bytes(changed),{**report,'sha256':sha256(changed)},self.module)
        directory = ROOT/'build/quest-reply-creator'
        image,reloc = ((directory/n).read_bytes() for n in ('overlay.bin','relocation.bin'))
        creator = json.loads((directory/'overlay.json').read_text())
        self.assertEqual(configuration(image,reloc,creator,self.module)[4],creator['symbols']['af_quest_reply_mail_create'])
        for value in (False,None,0,1,'true'):
            with self.assertRaises(ValueError): configuration(image,reloc,{**creator,'quest_replies':value},self.module)
        with self.assertRaises(ValueError): source_hashes(quest_replies=True)

    def test_complete_rom_patch_retains_every_earlier_text_and_resident_instruction(self):
        verify_test_module(self.built,self.module)
        verify_installation(self.built,self.native,self.module,self.report['quest_replies'])
        self.assertEqual(apply_ups(self.native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),self.built)
        previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes();old = by_vrom(previous)
        self.assertEqual(old.keys(),self.files.keys())
        self.assertEqual({v for v in old if old[v].extract(previous)!=self.files[v].extract(self.built)},
                         {0x19D40,CODE_VROM,MODULE_VROM,VROM})
        a,b = (bytearray(v) for v in (old[MODULE_VROM].extract(previous),self.files[MODULE_VROM].extract(self.built)))
        a[0x48:0x68] = b[0x48:0x68] = bytes(32)
        self.assertEqual(a,b)

    def test_combined_counter_adds_only_the_216_installed_parts(self):
        ledger = measure(self.native,self.built,self.report)
        baseline = deepcopy(self.report);baseline.pop('quest_replies')
        uncredited = measure(self.native,self.built,baseline)
        self.assertEqual(ledger.summary()['total_source_characters'],751307)
        ids = {f'{bank}:{number:04X}' for bank in ('super','mail','ps') for number in TEMPLATES}
        actual = {k for k,r in ledger.rows.items() if any(v['route']=='quest_replies' for v in r['replacements'])}
        # Three Japanese sign-offs intentionally become a sender command alone.
        # The fourth source already contains only a command and adds no weight.
        dynamic_only = {'ps:009D'}
        self.assertEqual(actual,ids-dynamic_only)
        self.assertEqual(sum(ledger.rows[k]['source_characters'] for k in dynamic_only),0)
        for key,row in uncredited.rows.items():
            if key not in ids: self.assertEqual(row,ledger.rows[key])
            self.assertTrue(all(r in ledger.rows[key]['replacements'] for r in row['replacements']))

    def test_cli_requires_complete_creator_and_item_resources(self):
        for script,args,expected in (
                ('build.py',['--rom','not-read.z64','--english-quest-replies','not-read'],'--english-quest-replies requires'),
                ('build_npc_mail_capture.py',['--quest-replies'],'--quest-replies requires')):
            result = subprocess.run([sys.executable,str(ROOT/'tools'/script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn(expected,result.stderr)


if __name__=='__main__': unittest.main()
