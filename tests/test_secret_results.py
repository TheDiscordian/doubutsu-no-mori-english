"""Frozen evidence for the complete silent secret-letter cartridge batch."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from secret_scenario import scenario

RUN,BUILD = ROOT/'build/smoke-secret-01',ROOT/'build/secret-letters-pilot'


@unittest.skipUnless((RUN/'results.json').is_file(),'Local secret-letter native evidence required')
class SecretResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (RUN/'results.json').read_bytes()
        if sha256(raw)!='fd7ed4656db4f65e7f98d35a770a62c3512354b35372d26334fa016610968ffc':
            raise ValueError('Changed native secret-letter results')
        cls.rows = json.loads(raw);cls.run_info = json.loads((RUN/'run.json').read_text())
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes();cls.report = json.loads((BUILD/'build.json').read_text())

    def test_all_choices_capitals_real_owner_loading_and_complete_converted_readbacks(self):
        actions = scenario(self.native,self.built,self.report)
        self.assertEqual(actions,json.loads((ROOT/'build/secret-scenario.json').read_text()))
        self.assertEqual(self.run_info['post_scenario_sha256'],sha256((ROOT/'build/secret-scenario.json').read_bytes()))
        self.assertEqual(sha256((ROOT/'tools/secret_smoke.py').read_bytes()),
                         '21b021123986f9bc3de9b654f861b3d0e9a465508ece0153a05a6bef879eed02')
        rows = self.rows;self.assertEqual(len(rows),834)
        self.assertFalse(any('error' in r or r.get('assertion')=='failed' for r in rows))
        self.assertEqual([(r['native_secret_case'],r['capital']) for r in rows if 'native_secret_case'in r],
                         [(c['choice'],c['capital']) for c in actions[3]['test_secret_letters']['cases']])
        for label,count in (('native owner loads complete overlay with original BSS offsets',2),
                            ('native owner does not overwrite allocation tail',2),
                            ('owner releases temporary relocation allocation',2),
                            ('complete compact secret letter',30),('original font paper and gift preserved',30),
                            ('original date and padding preserved',30),('paper selection consumes original RNG sequence',30),
                            ('paper selection retains original RNG temporary',30),('complete compact English readback',30),
                            ('native conversion retains entire snapshot',30),('complete converted English readback',30)):
            self.assertEqual(sum(r.get('secret_check')==label and r.get('assertion')=='passed' for r in rows),count)
        summary = next(r for r in rows if 'complete_secret_cases'in r)
        self.assertEqual(summary['complete_secret_cases'],30);self.assertEqual(summary['secret_rejections'],3)
        self.assertEqual(summary['owner_loader_bases'],2);self.assertEqual(summary['secret_assertions'],437)
        self.assertEqual(summary['debugger_uploaded_creator_bytes'],0)
        self.assertFalse(summary['normal_conversation']);self.assertFalse(summary['show_window_tested']);self.assertFalse(summary['hardware_verified'])

    def test_rejections_restore_state_heap_stack_checkpoint_and_blank_saves(self):
        rows = self.rows
        self.assertEqual([r['native_secret_rejection'] for r in rows if 'native_secret_rejection'in r],
                         ['capital','null_selected','overlap_selected'])
        for fault in ('capital','null_selected','overlap_selected'):
            for label in ('rejection retains compact record: ','rejection retains selected memory: ',
                          'rejection stops before paper RNG: ','rejection retains capital: '):
                self.assertEqual(sum(r.get('secret_check')==label+fault and r.get('assertion')=='passed' for r in rows),1)
        for label in ('secret code data and original BSS retained','secret retains heap accounting','secret does not change save','resident module guard'):
            self.assertEqual(sum(r.get('secret_check')==label and r.get('assertion')=='passed' for r in rows),1)
        self.assertEqual(sum(r.get('secret_check')=='secret global restored' for r in rows),4)
        self.assertEqual(sum(r.get('secret_check')=='secret fixture and stack guard' for r in rows),12)
        calls = [r for r in rows if 'test_only_function_call'in r]
        self.assertEqual(len(calls),194);self.assertTrue(all(r['stack_restored'] for r in calls))
        self.assertEqual(sum(r.get('assertion')=='passed' for r in rows),439)
        self.assertEqual(self.run_info['rom_sha256'],sha256(self.built));self.assertEqual(self.run_info['audio'],'disabled')
        for key in ('initial_screenshot','expansion_pak','allow_test_flash_write','allow_test_pak_write'): self.assertFalse(self.run_info[key])
        loaded = next(i for i,r in enumerate(rows) if r.get('loaded_state')=='test.bs1')
        self.assertTrue(any(r.get('read')==['8019B000',4] and r.get('assertion')=='passed' for r in rows[loaded+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name,digest in (('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51'),
                            ('test.bs1','d70f44f34e1965f75503a75bb78ec2391715028aae11727730e390017306127e')):
            self.assertEqual(sha256((RUN/name).read_bytes()),digest)


if __name__=='__main__': unittest.main()
