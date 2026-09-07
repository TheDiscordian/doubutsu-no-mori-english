"""Native community drafts retain events, complete instructions, and commands."""

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

IDS = set('1084 1194 1195 11F3 1689 17F2 17F3 17F4 17FB 1808 180C '
          '1D43 27B9 27D2 280D 2811 2825 2837'.split())
DATED = {'180C', '2825'}


class CommunityDraftSelectionTests(unittest.TestCase):
    def test_only_two_converted_date_drafts_require_the_patch(self):
        drafts = json.loads((ROOT/'translations/n64-community-conversations.json').read_text())
        selected, withheld = select_drafts(drafts)
        self.assertEqual({r['id'][8:] for r in selected}, IDS-DATED)
        self.assertEqual({r['id'][8:] for r in withheld}, DATED)
        self.assertTrue(all(r['reason'] == 'runtime_requirement_unavailable' for r in withheld))
        self.assertEqual(select_drafts(drafts, english_dialogue_dates=True), (drafts, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local test input')
class NativeCommunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.drafts = json.loads((ROOT/'translations/n64-community-conversations.json').read_text())
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}

    def test_all_original_commands_and_arguments_remain_exact(self):
        self.assertEqual(set(self.text), IDS)
        self.assertEqual(len(self.drafts), len(IDS))
        for draft in self.drafts:
            with self.subTest(id=draft['id']):
                source = self.sources[int(draft['id'][8:], 16)]
                output = encode(draft['translation'], self.info)
                self.assertEqual(sha256(source), draft['source_sha256'])
                self.assertEqual(draft['status'], 'draft')
                self.assertEqual(draft.get('control_policy', 'exact'), 'exact')
                self.assertNotIn('resident_animations', draft)
                controls = lambda raw: [t.data for t in tokenize(raw, self.info) if t.kind == 'cmd']
                self.assertEqual(controls(output), controls(source))
                validate_entry(source, output, self.info, 'message', resident_runtime=True)
                self.assertLessEqual(expanded_bound(output, self.info), 1024)

    def test_approved_font_layout_and_guarded_english_date_values(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        for draft in self.drafts:
            output = encode(draft['translation'], self.info)
            issues = layout_issues(output, self.info, advances, resident_runtime=True)
            if draft['id'][8:] in DATED:
                page = 1 if draft['id'][8:] == '180C' else 3
                self.assertEqual(issues, [f'page_{page}_line_2_width_246', f'page_{page}_line_2_width_250'])
                self.assertEqual(draft['runtime_requirements'], ['ordinary_dialogue_dates'])
                self.assertIn('{cmd:7F3C} {cmd:7F3D}', draft['translation'])
                # Retain generic fullwidth-field warnings; this guarded caller
                # supplies English months and ordinal days instead.
                output = output.replace(bytes.fromhex('7F3C'), b'September')
                output = output.replace(bytes.fromhex('7F3D'), b'31st')
                issues = layout_issues(output, self.info, advances, resident_runtime=True)
            self.assertEqual(issues, [], draft['id'])

    def test_native_white_day_and_blossom_schedule(self):
        for id in ('1194', '1195', '17F3', '17F4', '27B9'):
            self.assertIn('White Day', self.text[id])
        self.assertIn('March 14', self.text['280D'])
        self.assertIn('homemade chocolates', self.text['17F2'])
        self.assertIn('carp streamers', self.text['17FB'])
        self.assertIn('Doll Festival', self.text['17FB'])
        self.assertIn('us girls', self.text['1D43'])
        for phrase in ('The 6th and 7th', 'and the 5th', 'shrine plaza', 'miso soup'):
            self.assertIn(phrase, self.text['2811'])
        for text in self.text.values():
            self.assertNotIn('Groundhog', text)
            self.assertNotIn('wishing well', text)
            self.assertNotIn('Harvest Festival', text)

    def test_moon_fireworks_and_countdown_native_meanings(self):
        self.assertIn('next month', self.text['1808'])
        self.assertNotIn('July', self.text['1808'])
        # Pauses divide the two calls without changing their spoken spelling.
        visible = ''.join(chr(t.data[0]) for t in tokenize(encode(self.text['1689'], self.info), self.info)
                          if t.kind == 'text')
        self.assertIn('Tamayaaa!', visible)
        self.assertIn('Kagiyaaa!', visible)
        self.assertIn('Ask your dad', visible)
        self.assertIn('Thirteenth Night', self.text['27D2'])
        self.assertIn('a little bite', self.text['27D2'])
        self.assertIn('I held back', self.text['27D2'])
        for id in DATED:
            self.assertIn('by the pond', self.text[id])
            self.assertNotIn('meteor', self.text[id])
        self.assertIn('early sleepers', self.text['2837'])
        self.assertIn('cleaning early', self.text['2837'])
        self.assertIn('come to the party', self.text['2837'])

    def test_creature_care_and_nooks_self_made_free_monument(self):
        for phrase in ('Keeping them in your room', 'prepare food or a tank', "Tom Nook's"):
            self.assertIn(phrase, self.text['11F3'])
        self.assertNotIn('museum', self.text['11F3'])
        self.assertNotIn('Blathers', self.text['11F3'])
        for phrase in ('monument', 'Only{cmd:7F0304} joking', 'I made it myself',
                       "You don't owe me a Bell", 'thanking'):
            self.assertIn(phrase, self.text['1084'])
        self.assertEqual(self.text['1084'].count('{cmd:7F02}'), 6)


if __name__ == '__main__':
    unittest.main()
