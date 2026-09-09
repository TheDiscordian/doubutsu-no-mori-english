"""The combined counter credits the actual selected glyph-capable routes."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from translation_progress import measure
from mail_glyph_creator_scenario import scenario,without_captures

BUILD = ROOT/'build/mail-glyph-letters-pilot'


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete local glyph translation ROM required')
class MailGlyphProgressTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())

    def test_installed_bodies_and_reply_footer_share_the_existing_denominator(self):
        ledger = measure(self.native,self.built,self.report)
        self.assertEqual(ledger.summary()['total_source_characters'],751002)
        for identity,route in (('mail:0136','mother_letters'),('mail:00F6','villager_event_letters'),
                               ('mail:003D','academy_score_letters'),('psz:004D','npc_letters')):
            self.assertTrue(any(r['route']==route for r in ledger.rows[identity]['replacements']),identity)

    def test_batched_native_cases_include_complete_source_id_sets(self):
        actions = scenario(self.native,self.built,self.report)
        self.assertEqual(sum('save_state' in a for a in actions),1)
        self.assertEqual(sum('load_state' in a for a in actions),1)
        self.assertEqual(sum('pause_game_thread' in a for a in actions),1)
        for key,expected in (('test_mother_letters',114),('test_villager_event_letters',55),('test_academy_scores',21)):
            request = next(a[key] for a in actions if key in a)
            self.assertEqual(request['catalog_id'],4)
            self.assertEqual(len({c['template'] for c in request['cases']}),expected)
        self.assertTrue(any('test_npc_mail_loader' in a for a in actions))

    def test_resume_only_unfinished_groups_without_losing_checkpoint_checks(self):
        actions = scenario(self.native,self.built,self.report,('scores','npc'))
        self.assertEqual(sum('save_state' in a for a in actions),1)
        self.assertEqual(sum('load_state' in a for a in actions),1)
        self.assertTrue(any('test_academy_scores' in a for a in actions))
        self.assertTrue(any('test_npc_mail_loader' in a for a in actions))
        self.assertFalse(any('test_mother_letters' in a or 'test_villager_event_letters' in a for a in actions))
        for groups in ((),('scores','scores'),('unknown',)):
            with self.assertRaises(ValueError): scenario(self.native,self.built,self.report,groups)


class SilentScenarioTests(unittest.TestCase):
    def test_remove_only_captures_recursively_preserving_input_and_assertions(self):
        actions = [{'capture':'x.png'},{'snapshot_message':True,'capture':'y.png'},
                   {'repeat':2,'actions':[{'capture':'z.png'},{'key':'a','duration':0.1}]}]
        self.assertEqual(without_captures(actions),[{'snapshot_message':True},
                         {'repeat':2,'actions':[{'key':'a','duration':0.1}]}])
        self.assertEqual(actions[0],{'capture':'x.png'})


if __name__ == '__main__': unittest.main()
