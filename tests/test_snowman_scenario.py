"""Exact complete Snowman cases, fixed native RNG, and isolated test boundaries."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mail_record import unpack
from snowman_scenario import scenario,choice_for_seed
from snowman_actor import native_sources

BUILD = ROOT/'build/v0-hardware-fixes-02'


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete local Snowman build required')
class SnowmanScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.actions = scenario(cls.native,cls.built,cls.report);cls.request = cls.actions[3]['test_snowman_letters']

    def test_all_choices_both_capitals_full_fields_and_original_actor(self):
        cases = self.request['cases']
        self.assertEqual({(c['choice'],c['capital']) for c in cases},{(i,c) for i in range(12) for c in (0,1)})
        self.assertEqual(len(cases),24)
        for c in cases:
            self.assertEqual(choice_for_seed(c['seed']),(c['choice'],c['rng_end']))
            r = unpack(bytes.fromhex(c['wire']),expected_catalog=4)
            self.assertEqual(r.templates,(0x202+c['choice'],));self.assertEqual(len(r.fields[0][1].text),16)
            self.assertEqual(len(bytes.fromhex(c['text'])),1040)
        self.assertEqual(tuple(bytes.fromhex(self.request[k]) for k in ('original','original_relocation')),
                         native_sources(self.native))

    def test_one_silent_checkpoint_and_exact_rom_binding(self):
        for key in ('save_state','load_state','pause_game_thread'):
            self.assertEqual(sum(key in a for a in self.actions),1)
        self.assertFalse(any('capture' in a for a in self.actions))
        self.assertEqual(self.actions[-1],{'read':['8019B000',4],'expect':'00000000'})
        with self.assertRaisesRegex(ValueError,'Changed Snowman ROM'):
            scenario(self.native,self.built,{**self.report,'output_sha256':'0'*64})

    def test_edge_only_resume_keeps_cases_without_repeating_bulk_comparisons(self):
        request = scenario(self.native,self.built,self.report,'edges')[3]['test_snowman_letters']
        self.assertEqual(request['cases'],self.request['cases']);self.assertEqual(request['group'],'edges')
        from snowman_smoke import PLAYER
        self.assertEqual(PLAYER,0x80136EA3)
        code = bytes.fromhex(request['guards']['8009519C'])
        self.assertIn(bytes.fromhex('3C0480130C02546790846EA3'),code)
        with self.assertRaises(ValueError): scenario(self.native,self.built,self.report,'missing')


if __name__=='__main__': unittest.main()
