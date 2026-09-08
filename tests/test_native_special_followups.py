"""Complete native special dialogue retains its menus, fields, and handoffs."""

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

IDS = ['23EB', '23FE', '2513']
BOUNDS = [145, 823, 108]


class SpecialFollowupSelectionTests(unittest.TestCase):
    def test_all_three_complete_originals_are_selected_in_both_configurations(self):
        rows = json.loads((ROOT/'translations/n64-special-followups.json').read_text())
        self.assertEqual([r['id'][8:] for r in rows], IDS)
        self.assertTrue(all(r['status'] == 'draft' and isinstance(r['provenance'], str) for r in rows))
        for resident in (False, True):
            self.assertEqual(select_drafts(rows, resident_runtime=resident), (rows, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail input remains local-only')
class SpecialFollowupRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.entries = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.rows = json.loads((ROOT/'translations/n64-special-followups.json').read_text())
        cls.text = {r['id'][8:]: r['translation'] for r in cls.rows}
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k,16): v for k,v in font['advance_by_glyph'].items()}

    def commands(self, data):
        return [t.data for t in tokenize(data, self.info) if t.kind == 'cmd']

    def test_complete_hashes_commands_bounds_and_layouts(self):
        for row, bound in zip(self.rows, BOUNDS):
            source = self.entries[int(row['id'][8:],16)]
            raw = encode(row['translation'], self.info)
            self.assertEqual(sha256(source), row['source_sha256'])
            self.assertEqual(self.commands(raw), self.commands(source), row['id'])
            validate_entry(source, raw, self.info, 'message', 'exact')
            self.assertEqual(expanded_bound(raw, self.info), bound)
            self.assertEqual(layout_issues(raw, self.info, self.advances), [], row['id'])
            self.assertNotRegex(row['translation'], '[\u3040-\u30ff\u3400-\u9fff]')

    def test_apology_quotes_keep_complete_field_and_native_input_handoff(self):
        text = self.text['23EB']
        self.assertIn('Say {cmd:7F502D642301}"{cmd:7F509114A50A}{cmd:7F31}'
                      '{cmd:7F502D642301}"', text)
        self.assertIn('Go on, say it!', text)
        self.assertTrue(text.endswith('{cmd:7F09090001}\n{cmd:7F55}\n{cmd:7F01}'))
        self.assertNotIn('{cmd:7F19}', text)

    def test_gulliver_keeps_complete_native_story_without_new_fields(self):
        text = self.text['23FE']; plain = re.sub(r'\{cmd:[^}]+\}', '', text)
        for phrase in ('I slept so well', 'Where am I', 'Who am I', 'Gulliver',
                       'a huge wave', 'fell into the sea', 'the boat was fine.',
                       'fell overboard', 'rescued me', 'Thank you so much',
                       'already, didn\'t I?', 'a gift to say thanks'):
            self.assertIn(phrase, plain)
        self.assertNotIn('{cmd:7F1D}', text)
        self.assertTrue(text.endswith('{cmd:7F01}'))

    def test_reset_warning_keeps_answer_order_and_weighted_native_destinations(self):
        text = self.text['2513']
        self.assertIn("let's stop resetting!", text)
        self.assertIn('{cmd:7F14251525162516}', text)
        self.assertIn('{cmd:7F160035004E}{cmd:7F5E}{cmd:7F04}{cmd:7F0D}{cmd:7F0F2514}', text)
        self.assertNotIn('2517', text)
        self.assertTrue(text.endswith('{cmd:7F19}\n{cmd:7F01}'))


if __name__ == '__main__':
    unittest.main()
