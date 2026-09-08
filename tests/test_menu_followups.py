"""Native-specific menus and complete sleeping/seasonal dialogue stay coherent."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from font import make_halfwidth
from reference_candidates import select_drafts
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry, expanded_bound, layout_issues
from test_retail import ROM_PATH

IDS = '0467 0970 09D0 0D3F 0F10 10B7 10B8 10BE 17B1'.split()
BOUNDS = [113, 226, 69, 493, 207, 100, 143, 143, 62]


class MenuFollowupSelectionTests(unittest.TestCase):
    def test_nine_complete_originals_are_selected_in_both_configurations(self):
        rows = json.loads((ROOT/'translations/n64-menu-followups.json').read_text())
        self.assertEqual([r['id'][8:] for r in rows], IDS)
        self.assertTrue(all(r['status'] == 'draft' and isinstance(r['provenance'], str) for r in rows))
        for resident in (False, True):
            self.assertEqual(select_drafts(rows, resident_runtime=resident), (rows, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail input remains local-only')
class MenuFollowupRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.entries = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.rows = json.loads((ROOT/'translations/n64-menu-followups.json').read_text())
        cls.text = {r['id'][8:]: r['translation'] for r in cls.rows}
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k,16): v for k,v in font['advance_by_glyph'].items()}

    def commands(self, data):
        return [t.data for t in tokenize(data, self.info) if t.kind == 'cmd']

    def test_all_native_commands_hashes_bounds_and_layouts(self):
        for row, bound in zip(self.rows, BOUNDS):
            number = row['id'][8:]; source = self.entries[int(number,16)]
            raw = encode(row['translation'], self.info)
            self.assertEqual(sha256(source), row['source_sha256'])
            expected = self.commands(source)
            if number == '17B1':
                self.assertEqual(expected[:2], [bytes.fromhex('7F50324BE105'), bytes.fromhex('7F504B1E1406')])
                expected[:2] = [bytes.fromhex('7F50324BE103'), bytes.fromhex('7F504B1E1401')]
            self.assertEqual(self.commands(raw), expected, number)
            validate_entry(source, raw, self.info, 'message', row.get('control_policy','exact'))
            self.assertEqual(expanded_bound(raw,self.info), bound)
            self.assertEqual(layout_issues(raw,self.info,self.advances), [], number)

    def test_original_menu_actions_and_native_destinations_remain(self):
        for number, menu in (('0970','7F16006A0034'), ('09D0','7F16004C00F1'),
                ('10B7','7F1600E2000D'), ('10B8','7F18009E007E00E900A0'),
                ('10BE','7F18009F007E00E900A0'), ('17B1','7F1601AA01AB')):
            self.assertIn('{cmd:'+menu+'}', self.text[number])
            self.assertNotIn('{cmd:7F62}',self.text[number])
        self.assertIn('{cmd:7F0F0973}{cmd:7F100970}', self.text['0970'])
        self.assertIn('{cmd:7F0F09C9}{cmd:7F1009C8}', self.text['09D0'])
        self.assertIn('{cmd:7F0F17B5}', self.text['17B1'])
        self.assertEqual([self.text[n].count('{cmd:7F31}') for n in ('10B8','10BE')], [1,1])

    def test_sleeping_apology_keeps_full_meaning_and_does_not_wake(self):
        text = self.text['0D3F']; plain = re.sub(r'\{cmd:[^}]+\}', '', text)
        for phrase in ('Sorry, Daddy', "Long ago, Daddy's", 'precious turnips',
                       'the one who ate them', 'it was me', 'mumble, mumble', 'Snooore'):
            self.assertIn(phrase, plain)
        self.assertTrue(text.startswith('{cmd:7F4F}{cmd:7F09000013}'))
        self.assertTrue(text.endswith('{cmd:7F00}'))
        self.assertNotIn('{cmd:7F09000002}', text)
        self.assertNotIn('{cmd:7F09000017}', text)

    def test_name_entry_weather_and_nes_keep_native_context(self):
        self.assertIn('{cmd:7F09090001}\n{cmd:7F55}',self.text['0467'])
        self.assertNotIn('{cmd:7F090000',self.text['0467'])
        self.assertIn('sky',self.text['0F10']);self.assertIn('morning',self.text['0F10'])
        self.assertIn('{cmd:7F1C}',self.text['0F10'])
        self.assertNotIn('{cmd:7F15',self.text['0F10'])
        self.assertTrue(self.text['0F10'].endswith('{cmd:7F00}'))
        self.assertIn('{cmd:7F50324BE103}NES{cmd:7F504B1E1401}?',self.text['17B1'])


if __name__ == '__main__':
    unittest.main()
