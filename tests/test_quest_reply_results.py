"""Frozen evidence for complete cartridge quest-reply delivery and readback."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from quest_reply_scenario import scenario

RUN = ROOT/'build/smoke-quest-reply-01'
BUILD = ROOT/'build/quest-reply-letters-pilot'


@unittest.skipUnless((RUN/'results.json').is_file(), 'Local quest-reply evidence required')
class QuestReplyResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        raw = (RUN/'results.json').read_bytes()
        if sha256(raw) != '85ebdffa4caa1f786dc12cf5140c94d8077812d3192e5a15a3e1d26e2b82da64':
            raise ValueError('Changed quest-reply results')
        cls.rows = json.loads(raw)
        cls.run_info = json.loads((RUN/'run.json').read_text())

    def check_count(self, label, count):
        self.assertEqual(sum(r.get('quest_reply_check') == label and
                             r.get('assertion') == 'passed' for r in self.rows), count, label)

    def test_every_template_capital_home_slot_and_complete_readback(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                           built, json.loads((BUILD/'build.json').read_text()))
        path = ROOT/'build/quest-reply-scenario.json'
        self.assertEqual(actions, json.loads(path.read_text()))
        self.assertEqual(self.run_info['post_scenario_sha256'], sha256(path.read_bytes()))
        self.assertEqual(self.run_info['rom_sha256'], sha256(built))
        self.assertEqual(sha256((ROOT/'tools/quest_reply_smoke.py').read_bytes()),
                         '71e073882508fce0a4dcafc5ac4fd89dc57f523186c98930ee46a855523244fd')
        cases = [r for r in self.rows if 'native_quest_reply_case' in r]
        self.assertEqual([(r['native_quest_reply_case'], r['capital']) for r in cases],
                         [(c['template'], c['capital']) for c in actions[3]['test_quest_replies']['cases']])
        self.assertEqual(len(cases), 144)
        self.assertTrue(all(r['passed'] for r in cases))
        self.assertEqual({r['home'] for r in cases}, set(range(4)))
        self.assertEqual({r['slot'] for r in cases}, set(range(10)))
        for label in ('only selected home slot changes', 'original recipient sender gift font type paper',
                      'original quest and selected reward retained', 'original native temporary fields retained',
                      'original animal identity retained', 'quest generation uses no new random selection',
                      'quest generation retains random temporary', 'final quest reply capitalization',
                      'creator detaches after quest reply'):
            self.check_count(label, 144)
        self.check_count('complete delivered quest reply text', 146)
        summary = next(r for r in self.rows if 'complete_quest_reply_cases' in r)
        for key, value in (('complete_quest_reply_cases', 144), ('full_readbacks', 146),
                           ('owner_fault_cases', 6), ('rank_rejections', 4),
                           ('quest_reply_assertions', 1503), ('debugger_uploaded_creator_bytes', 0)):
            self.assertEqual(summary[key], value)
        for key in ('normal_conversation', 'game_save_validation', 'hardware_verified'):
            self.assertFalse(summary[key])
        self.assertTrue(summary['requires_checkpoint_restore'])

    def test_rejections_retries_guards_and_restored_isolated_state(self):
        rows = self.rows
        self.assertEqual(len(rows), 2420)
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        self.assertEqual(sum(r.get('assertion') == 'passed' for r in rows), 1505)
        calls = [r for r in rows if 'test_only_function_call' in r]
        self.assertEqual(len(calls), 597)
        self.assertTrue(all(r['stack_restored'] for r in calls))
        faults = ('disabled', 'capital', 'full', 'wrong_home', 'null_player', 'absent_player')
        self.assertEqual([r['native_quest_reply_fault'] for r in rows if 'native_quest_reply_fault' in r], list(faults))
        for fault in faults:
            for label in ('quest failure retains save: ', 'quest failure retains selected inputs: ',
                          'quest failure retains capitalization: ', 'quest failure detaches creator: '):
                self.check_count(label+fault, 1)
        for label, count in (('resource retry retains original quest inputs', 2),
                             ('invalid full-width rank retains output', 4), ('quest creator heap retained', 1),
                             ('quest fixture and stack guard', 12), ('resident module guard', 1),
                             ('quest code retained', 5), ('live save restored', 1), ('quest global restored', 5)):
            self.check_count(label, count)
        loaded = next(i for i, r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000', 4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[loaded+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        self.assertEqual(self.run_info['seed_files'], [])
        self.assertEqual(self.run_info['audio'], 'disabled')
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(self.run_info[key])
        for name, digest in (
            ('test.bs1', '013b860253e3a9b216054476f6bd8a77d92f589991d2c1fe560ebbc71c549e8b'),
            ('test.flash', 'b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak', 'ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()), digest)


if __name__ == '__main__':
    unittest.main()
