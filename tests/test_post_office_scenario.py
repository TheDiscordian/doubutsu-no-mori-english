"""Native postal case inventory and exact source/ROM approval checks."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import verified_rom,sha256
from mail_record import unpack
from post_office_scenario import scenario,case
from post_office_smoke import CACHE_GUARDS

BUILD = ROOT/'build/post-office-letters-pilot'


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete local postal build required')
class PostOfficeScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.actions = scenario(cls.native,cls.built,cls.report)
        cls.request = cls.actions[3]['test_post_office_letters']

    def test_all_native_shops_capitals_months_counts_and_single_checkpoint(self):
        self.assertEqual(len(self.request['cases']),68)
        shops = [c for c in self.request['cases'] if c['template']!=0x57]
        self.assertEqual({(c['template'],c['capital']) for c in shops},{(n,c) for n in range(0x49,0x4D) for c in (0,1)})
        tickets = [c for c in self.request['cases'] if c['template']==0x57]
        self.assertEqual({c['gift'] for c in tickets},{0x2C00+m*8+c for m in range(12) for c in range(5)})
        for key in ('save_state','load_state','pause_game_thread'):
            self.assertEqual(sum(key in a for a in self.actions),1)
        self.assertFalse(any('capture' in a for a in self.actions))
        self.assertEqual(self.actions[-1],{'read':['8019B000',4],'expect':'00000000'})

    def test_case_payloads_bind_full_names_and_only_used_month_field(self):
        catalog,items = bytes.fromhex(self.request['catalog']),bytes.fromhex(self.request['items'])
        for c in self.request['cases']:
            self.assertEqual(case(catalog,items,c['template'],c['gift'],c['capital']),c)
            record = unpack(bytes.fromhex(c['wire']),expected_catalog=4)
            self.assertEqual([i for i,_ in record.fields],[4 if c['template']==0x57 else 0])
            self.assertEqual(len(record.fields[0][1].text),9 if c['template']==0x57 else 16)
        for number,gift in ((0x48,0x11FC),(0x57,0x2C05),(0x57,0x2C60),(0x49,0xFFFF)):
            with self.assertRaises(ValueError): case(catalog,items,number,gift,0)

    def test_cache_helpers_are_exact_original_code_and_wrong_rom_rejects(self):
        for address,(size,digest) in CACHE_GUARDS.items():
            at = 0x1060+address-0x80025C60
            self.assertEqual(sha256(self.native[at:at+size]),digest)
            self.assertEqual(self.built[at:at+size],self.native[at:at+size])
        with self.assertRaisesRegex(ValueError,'Changed postal ROM'):
            scenario(self.native,self.built,{**self.report,'output_sha256':'0'*64})


if __name__=='__main__': unittest.main()
