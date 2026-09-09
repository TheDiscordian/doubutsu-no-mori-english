"""Shop selector coverage, complete fields, and a single silent native batch."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mail_record import unpack
from shop_notice_scenario import scenario
from audit_shop_notice_letters import TEMPLATES,RARE_TABLE,REOPENING_TABLE

BUILD = ROOT/'build/shop-notice-letters-pilot'


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete shop notice ROM required')
class ShopNoticeScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.actions = scenario(cls.native,cls.built,cls.report)
        cls.request = cls.actions[3]['test_shop_notices']

    def test_every_shop_type_capital_and_publication_mode(self):
        rows = self.request['cases'];self.assertEqual(len(rows),32)
        self.assertEqual({(r['shop'],r['kind'],r['capital'],r['mode']) for r in rows},
                         {(s,t,c,m) for s in range(4) for t in range(2) for c in range(2) for m in range(2)})
        for row in rows: self.assertEqual(row['template'],RARE_TABLE[row['shop']*2+row['kind']])
        rows = self.request['reopening'];self.assertEqual(len(rows),8)
        for row in rows: self.assertEqual(row['template'],REOPENING_TABLE[row['shop']])

    def test_all_nine_complete_payloads_and_full_selected_item_fields(self):
        rows = self.request['cases']+self.request['reopening']
        self.assertEqual({r['template'] for r in rows},set(TEMPLATES))
        for row in rows:
            payload = unpack(bytes.fromhex(row['wire']),expected_catalog=4)
            self.assertEqual(payload.templates,(row['template'],))
            self.assertEqual(payload.initial_capital,bool(row['capital']))
            self.assertEqual(len(bytes.fromhex(row['text'])),1040)
            if 0x14<=row['template']<=0x17:
                self.assertEqual(len(payload.fields),1);self.assertEqual(payload.fields[0][0],7)
                self.assertEqual(len(payload.fields[0][1].text),16)
            else: self.assertEqual(payload.fields,())

    def test_single_checkpoint_no_visuals_and_changed_rom_rejected(self):
        for key in ('save_state','load_state','pause_game_thread'):
            self.assertEqual(sum(key in action for action in self.actions),1)
        self.assertFalse(any('capture' in action for action in self.actions))
        self.assertEqual(len(bytes.fromhex(self.request['original'])),0x590)
        with self.assertRaisesRegex(ValueError,'Changed shop notice ROM'):
            scenario(self.native,self.built,{**self.report,'output_sha256':'0'*64})


if __name__=='__main__': unittest.main()
