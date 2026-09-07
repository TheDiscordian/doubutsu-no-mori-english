"""Native instructions keep Pak travel, actual sports dates, and Nook's loan."""

import json
from pathlib import Path
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
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

COLOURS = {
    '0852': {'7F504BA00002': '7F504BA00007', '7F50198CDC09': '7F50198CDC0E',
             '7F504BA00005': '7F504BA0000E'},
    '085C': {'7F504BA00002': '7F504BA00007', '7F50198CDC09': '7F50198CDC0E'},
    '0962': {'7F50C35F000A': '7F50C35F0010', '7F50198CDC09': '7F50198CDC0E',
             '7F509114A503': '7F509114A509'},
    '0BAA': {'7F504BA00007': '7F504BA0000C'},
    '2711': {'7F504BA00007': '7F504BA0000C'},
}
IDS = set('0852 085C 0962 0BAA 11CD 2711 27D5 285C'.split())


class NativeContextSelectionTests(unittest.TestCase):
    def test_all_original_drafts_are_available_without_runtime_requirements(self):
        drafts = json.loads((ROOT/'translations/n64-native-context.json').read_text())
        self.assertEqual({r['id'][8:] for r in drafts}, IDS)
        self.assertEqual(select_drafts(drafts), (drafts, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM stays local')
class NativeContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.drafts = json.loads((ROOT/'translations/n64-native-context.json').read_text())
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}

    def test_every_native_command_argument_and_only_named_colour_counts(self):
        for draft in self.drafts:
            id = draft['id'][8:]; source = self.sources[int(id, 16)]
            raw = encode(draft['translation'], self.info)
            controls = lambda data: [t.data.hex().upper() for t in tokenize(data, self.info) if t.kind == 'cmd']
            self.assertEqual(controls(raw), [COLOURS.get(id, {}).get(c, c) for c in controls(source)], id)
            self.assertEqual(sha256(source), draft['source_sha256'])
            self.assertEqual(draft['status'], 'draft')
            self.assertEqual(draft.get('control_policy', 'exact'), 'reference_layout' if id in COLOURS else 'exact')
            validate_entry(source, raw, self.info, 'message', draft.get('control_policy', 'exact'), resident_runtime=True)
            self.assertLessEqual(expanded_bound(raw, self.info), 1024)

    def test_no_extra_lines_and_native_six_cell_town_names_fit(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        for draft in self.drafts:
            output = encode(draft['translation'], self.info)
            issues = layout_issues(output, self.info, advances, resident_runtime=True)
            self.assertFalse(any('line_count' in item for item in issues), draft['id'])
            # The general check reserves sixteen Japanese cells for 2F.
            # Retain its warnings; test the unchanged six-cell native town
            # limit separately, using fullwidth Japanese rather than Latin.
            output = output.replace(bytes.fromhex('7F2F'), b'\x00'*6)
            self.assertEqual(layout_issues(output, self.info, advances, resident_runtime=True), [], draft['id'])

    def test_pak_rules_and_private_letters_do_not_become_gamecube_card_rules(self):
        for id in ('0852', '085C', '0962'):
            self.assertIn('Controller Pak', self.text[id])
            self.assertNotIn('Memory Card', self.text[id])
        for phrase in ('secrets', 'bulletin board', 'letters'):
            self.assertIn(phrase, self.text['0852'])
        self.assertIn('ticket', self.text['085C'])
        for phrase in ('same travel data', 'different', 'saved over', 'smuggling'):
            self.assertIn(phrase, self.text['0962'])

    def test_native_sports_calendar_and_loan_advice(self):
        for id in ('0BAA', '2711', '27D5'):
            self.assertIn('October', self.text[id])
            self.assertIn('Monday', self.text[id])
            self.assertIn('shrine plaza', self.text[id])
            self.assertNotIn('September', self.text[id])
        self.assertIn('October 10th', self.text['2711'])
        self.assertIn('9:00 a.m.', self.text['11CD'])
        self.assertIn('Sports Day', self.text['11CD'])
        self.assertIn('Tom Nook', self.text['285C'])
        self.assertIn('paying back', self.text['285C'])
        self.assertIn('tiny forever', self.text['285C'])
        self.assertNotIn('Tortimer', self.text['285C'])
