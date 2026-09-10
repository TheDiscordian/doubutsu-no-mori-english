"""Museum case inventory, empty-field payloads, and exact cartridge approval."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import verified_rom,sha256
from mail_record import unpack
from museum_letters import FOSSILS,TEMPLATES,START,END
from museum_scenario import scenario,case
from museum_smoke import CACHE_GUARDS

BUILD = ROOT/'build/v0-hardware-fixes-02'


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete local museum build required')
class MuseumScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.actions = scenario(cls.native,cls.built,cls.report)
        cls.request = cls.actions[3]['test_museum_letters']

    def test_all_templates_both_capitals_and_single_silent_checkpoint(self):
        self.assertEqual(len(self.request['cases']),54)
        self.assertEqual({(c['template'],c['capital']) for c in self.request['cases']},
                         {(n,c) for n in TEMPLATES for c in (0,1)})
        for key in ('save_state','load_state','pause_game_thread'):
            self.assertEqual(sum(key in a for a in self.actions),1)
        self.assertFalse(any('capture' in a for a in self.actions))
        self.assertEqual(self.actions[-1],{'read':['8019B000',4],'expect':'00000000'})
        self.assertEqual(len(bytes.fromhex(self.request['original_creator'])),END-START)

    def test_full_payloads_all_fossil_variants_and_rejected_pairs(self):
        catalog = bytes.fromhex(self.request['catalog'])
        for c in self.request['cases']:
            self.assertEqual(case(catalog,c['template'],c['gift'],c['capital']),c)
            r = unpack(bytes.fromhex(c['wire']),expected_catalog=4)
            self.assertEqual(r.fields,());self.assertEqual(r.templates,(c['template'],))
        for gift in range(0x1E3C,0x1EA0):
            for capital in (0,1):
                c = case(catalog,FOSSILS[(gift-0x1E3C)//4],gift,capital)
                self.assertEqual(len(bytes.fromhex(c['text'])),1040)
        for number,gift in ((0xBC,0),(0xBD,0x1E3C),(0xBE,1),(0x10E,0),(0x10F,0x1E3C),(0x10E,0x1EA0)):
            with self.assertRaises(ValueError): case(catalog,number,gift,0)
        with self.assertRaises(ValueError): case(catalog,0xBD,0,2)

    def test_original_cache_helpers_and_changed_rom_rejection(self):
        for address,(size,digest) in CACHE_GUARDS.items():
            at = 0x1060+address-0x80025C60
            self.assertEqual(sha256(self.native[at:at+size]),digest)
            self.assertEqual(self.built[at:at+size],self.native[at:at+size])
        with self.assertRaisesRegex(ValueError,'Changed museum ROM'):
            scenario(self.native,self.built,{**self.report,'output_sha256':'0'*64})


if __name__=='__main__': unittest.main()
