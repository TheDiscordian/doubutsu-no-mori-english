"""Source-bound evidence for the complete secret-letter window boundary cases."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from secret_show_scenario import scenario

RUN = ROOT/'build/smoke-secret-show-01'


@unittest.skipUnless((RUN/'results.json').is_file(),'Local secret-window evidence required')
class SecretShowResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (RUN/'results.json').read_bytes()
        if sha256(raw) != '107aac1b6c9849f7431e63231afadbeaae951677a111586a3023827d37cf4ac3':
            raise ValueError('Changed secret-window results')
        cls.rows = json.loads(raw)
        cls.run_info = json.loads((RUN/'run.json').read_text())

    def test_reproducible_boundary_scenario_and_all_complete_glyphs(self):
        build = ROOT/'build/secret-letters-pilot'
        actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                           (build/'animal-forest-halfwidth.z64').read_bytes(),
                           json.loads((build/'build.json').read_text()))
        self.assertEqual(actions,json.loads((ROOT/'build/secret-show-scenario.json').read_text()))
        self.assertEqual(self.run_info['scenario_sha256'],sha256((ROOT/'build/secret-show-scenario.json').read_bytes()))
        self.assertEqual(actions[3]['test_npc_mail_show']['branches'],['unknown_sender'])
        cases = actions[3]['test_npc_mail_show']['cases']
        self.assertEqual([c['label'] for c in cases],['secret:0022','secret:0024','secret:002B'])
        draws = [r for r in self.rows if 'mail_page_drawing' in r]
        self.assertEqual(len(draws),3)
        for case,row in zip(cases,draws):
            for part in ('header','body','footer'):
                self.assertEqual(row['mail_page_drawing'][part],case[part])
            self.assertEqual(row['mail_page_drawing']['total'],1)
        self.assertEqual(sum(r['glyphs_verified'] for r in draws),504)
        self.assertEqual(sum(r['vertex_positions_verified'] for r in draws),2016)
        self.assertTrue(any('80' in c['footer'] for c in cases))
        traversals = [r for r in self.rows if 'complete_mail_page_traversal' in r]
        self.assertEqual(len(traversals),3)
        self.assertTrue(all(r['complete_mail_page_traversal'] and r['pages']==1
                            and not r['backward_page_checked'] for r in traversals))

    def test_native_calls_retention_shutdown_and_explicit_limits(self):
        rows = self.rows
        self.assertEqual(len(rows),166)
        self.assertFalse(any('error' in r or r.get('assertion')=='failed' for r in rows))
        self.assertEqual(sum(r.get('assertion')=='passed' for r in rows),53)
        calls = [r for r in rows if 'test_only_function_call' in r]
        self.assertEqual(len(calls),15)
        self.assertTrue(all(r['stack_restored'] for r in calls))
        for label in ('complete caller temporary letter','compact source retained after window close',
                      'saved header/footer preferences retained','caller retains saved NPC population',
                      'caller retains saved player state','resident module guard'):
            self.assertEqual(sum(r.get('npc_show_check')==label for r in rows),3)
        summary = next(r for r in rows if 'npc_show_cases' in r)
        self.assertEqual(summary['npc_show_cases'],3);self.assertEqual(summary['native_callers'],1)
        self.assertFalse(summary['normal_actor_gameplay']);self.assertFalse(summary['game_save_validation'])
        self.assertTrue(next(r for r in rows if 'npc_show_allocation_freed' in r)['only_after_window_close'])
        self.assertTrue(any(r.get('loaded_state')=='test.bs1' for r in rows))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        self.assertEqual(self.run_info['audio'],'disabled')
        for key in ('initial_screenshot','expansion_pak','allow_test_flash_write','allow_test_pak_write'):
            self.assertFalse(self.run_info[key])
        for name,digest in (
            ('test.bs1','ff7a0bfd663fe588131ef88e447425f1a54b9d35fa9599da0899e5df46b3f387'),
            ('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()),digest)


if __name__=='__main__': unittest.main()
