"""Native quest reply batch uses complete installed text and silent fixtures."""
from collections import Counter
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mail_record import unpack
from quest_reply_scenario import scenario

BUILD = ROOT/'build/quest-reply-letters-pilot'


@unittest.skipUnless((BUILD/'build.json').is_file(),'Local complete quest reply cartridge required')
class QuestReplyScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.actions = scenario(cls.native,cls.built,cls.report)

    def test_all_templates_both_capitals_complete_wide_fields(self):
        request = self.actions[3]['test_quest_replies'];cases = request['cases']
        self.assertEqual(len(cases),144)
        self.assertEqual(Counter(c['template'] for c in cases),Counter({n:2 for n in range(0x75,0xBD)}))
        widths = set()
        for case in cases:
            self.assertEqual(case['template'],0x75+case['rank']*6+case['looks'])
            self.assertEqual(bytes.fromhex(case['animal'])[11],case['looks'])
            entry = unpack(bytes.fromhex(case['wire']),expected_catalog=4)
            self.assertEqual(entry.templates,(case['template'],))
            self.assertEqual(entry.initial_capital,bool(case['capital']))
            self.assertEqual(len(bytes.fromhex(case['text'])),1040)
            fields = dict(entry.fields);self.assertEqual(len(fields[6].text),8)
            if 0 in fields: widths.add(len(fields[0].text.rstrip(b' ')))
        self.assertTrue(widths and min(widths)>10)

    def test_source_and_installed_owner_changes_reject(self):
        altered = bytearray(self.built);altered[-1] ^= 1
        with self.assertRaises(ValueError): scenario(self.native,bytes(altered),self.report)
        self.assertEqual(self.actions,json.loads((ROOT/'build/quest-reply-scenario.json').read_text()))

    def test_checkpoint_restoration_and_no_capture_actions(self):
        self.assertEqual(self.actions[1:3],[{'save_state':True},{'pause_game_thread':True}])
        self.assertEqual(self.actions[-4:],
                         [{'load_state':True},{'resume':True},{'wait':2},{'read':['8019B000',4],'expect':'00000000'}])
        def scan(actions):
            for action in actions:
                self.assertNotIn('capture',action)
                if 'repeat' in action: scan(action.get('actions',[]))
        scan(self.actions)
        scan(json.loads((ROOT/'build/quest-reply-silent-boot.json').read_text()))


if __name__=='__main__': unittest.main()
