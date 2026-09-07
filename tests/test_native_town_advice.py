"""Native town advice keeps event meanings, actions, dates, and the final loan."""

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


class NativeTownAdviceSelectionTests(unittest.TestCase):
    def test_only_converted_date_requires_the_date_patch(self):
        drafts = json.loads((ROOT/'translations/n64-town-advice.json').read_text())
        selected, withheld = select_drafts(drafts)
        self.assertEqual({r['id'] for r in withheld}, {'message:0BA8'})
        self.assertEqual(withheld[0]['reason'], 'runtime_requirement_unavailable')
        self.assertEqual(len(selected), 7)
        self.assertEqual(select_drafts(drafts, english_dialogue_dates=True), (drafts, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local test input')
class NativeTownAdviceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.drafts = json.loads((ROOT/'translations/n64-town-advice.json').read_text())
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}

    def test_source_hashes_complete_commands_and_capacity(self):
        ids = set('0B8D 0B96 0BA8 0BC9 0F35 0F42 0FA9 1082'.split())
        self.assertEqual(set(self.text), ids)
        self.assertEqual(len(self.drafts), len(ids))
        for draft in self.drafts:
            with self.subTest(id=draft['id']):
                source = self.sources[int(draft['id'][8:], 16)]
                output = encode(draft['translation'], self.info)
                self.assertEqual(sha256(source), draft['source_sha256'])
                self.assertEqual(draft['status'], 'draft')
                self.assertNotIn('resident_animations', draft)
                commands = lambda raw: [t.data for t in tokenize(raw, self.info) if t.kind == 'cmd']
                expected = commands(source)
                if draft['id'] == 'message:1082':
                    before, after = bytes.fromhex('7F504BA00007'), bytes.fromhex('7F504BA0000B')
                    self.assertEqual(expected.count(before), 1)
                    expected = [after if t == before else t for t in expected]
                    self.assertEqual(draft['control_policy'], 'reference_layout')
                else:
                    self.assertEqual(draft.get('control_policy', 'exact'), 'exact')
                self.assertEqual(commands(output), expected)
                validate_entry(source, output, self.info, 'message', draft.get('control_policy', 'exact'),
                               resident_runtime=True)
                self.assertLessEqual(expanded_bound(output, self.info), 1024)

    def test_original_draft_layout_uses_approved_advances(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        for draft in self.drafts:
            output = encode(draft['translation'], self.info)
            issues = layout_issues(output, self.info, advances, resident_runtime=True)
            if draft['id'] == 'message:0BA8':
                # The generic checker budgets ten fullwidth cells per free field.
                # This guarded caller supplies English month/day strings instead.
                # Retain the warning, and check the longest possible English values.
                self.assertEqual(issues, ['page_3_line_3_width_296', 'page_3_line_3_width_300'])
                self.assertEqual(draft['runtime_requirements'], ['ordinary_dialogue_dates'])
                output = output.replace(bytes.fromhex('7F3E'), b'September')
                output = output.replace(bytes.fromhex('7F3F'), b'31st')
                issues = layout_issues(output, self.info, advances, resident_runtime=True)
            self.assertEqual(issues, [], draft['id'])

    def test_native_events_and_converted_thirteenth_night_fields(self):
        self.assertIn("chocolates on Valentine's", self.text['0B8D'])
        self.assertIn('gifts back on White Day', self.text['0B8D'])
        self.assertIn('When May comes around', self.text['0B96'])
        self.assertIn('carp streamers', self.text['0B96'])
        self.assertIn('Make them climb', self.text['0B96'])
        self.assertIn('Make them swim', self.text['0B96'])
        self.assertIn('Lunar month nine, day 13', self.text['0BA8'])
        self.assertIn('Thirteenth Night', self.text['0BA8'])
        self.assertIn('{cmd:7F3E} {cmd:7F3F}', self.text['0BA8'])
        self.assertIn("This year's", self.text['0BA8'])
        self.assertIn('by the pond', self.text['0BA8'])
        self.assertNotIn('{cmd:7F3C}', self.text['0BA8'])
        for id in ('0B8D', '0B96', '0BA8'):
            self.assertNotIn('Groundhog', self.text[id])
            self.assertNotIn('Harvest Festival', self.text[id])

    def test_native_fishing_weather_paint_and_town_rating(self):
        fishing = self.text['0BC9']
        for phrase in ('records are set by the size', 'black bass', 'just by looking',
                       "don't rush to show it", 'plenty of prizes'):
            self.assertIn(phrase, fishing)
        self.assertNotIn('weight', fishing)
        self.assertIn('{cmd:7F0C050001}', fishing)
        self.assertIn("When it's raining", self.text['0F35'])
        self.assertIn('{cmd:7F33}', self.text['0F35'])
        self.assertIn('{cmd:7F0C090003}', self.text['0F35'])
        self.assertIn('yellow-green', self.text['0F42'])
        self.assertIn('paint left over', self.text['0F42'])
        self.assertIn('{cmd:7F0C000004}', self.text['0F42'])
        self.assertIn('"slightly dissatisfied"', self.text['0FA9'])
        self.assertIn('{cmd:7F2F}', self.text['0FA9'])
        self.assertNotIn('moving', self.text['0FA9'])

    def test_final_house_fee_and_full_post_office_highlight(self):
        text = self.text['1082']
        for phrase in ('498,000 Bells', "pay it all right now", "Your house can't get",
                       'any bigger than this', 'for what you\'ve bought', 'In full'):
            self.assertIn(phrase, text)
        self.assertNotIn('398', text)
        self.assertEqual(text.count('{cmd:7F02}'), 11)
        output = encode(text, self.info)
        colour = bytes.fromhex('7F504BA0000B')
        at = output.index(colour)+len(colour)
        self.assertEqual(output[at:at+11], b'post office')


if __name__ == '__main__':
    unittest.main()
