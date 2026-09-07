"""Native seasonal questions, replies, dates, and presentation requests."""

import calendar
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from font import make_halfwidth
from gc_text import plain
from reference_candidates import load_drafts, select_drafts
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

PATH = ROOT/'translations/n64-seasonal-topics.json'
IDS = set('0B9C 0BA7 0BC5 11A2 11A4 11AE 11AF 11B1 1800 180D 180E '
          '270E 270F 27BC 27D0 27D3 27D6 27E2 27E3 27EE 27EF 27F2 '
          '281D 2824 2826 2827 2829 2833 2834'.split())
DATED = set('11AE 11AF 180E 270F 2826 2827'.split())
QUESTIONS = {
    '0B9C': ('002F0069', '0BC5', '0BC6'),
    '11A2': ('002F0069', '11CA', '11CB'),
    '11A4': ('0003004E', '11D4', '11D5'),
    '11B1': ('002F0069', '11CC', '11CD'),
    '1800': ('004C0052', '182B', '182C'),
    '27D0': ('00690161', '27EE', '27EF'),
    '27D6': ('00EF0162', '27F0', '27F1'),
    '2824': ('0069017F', '2841', '2842'),
    '2833': ('0044003B', '2845', '2846'),
    '2834': ('004C0161', '2847', '2848'),
}


class SeasonalTopicSelectionTests(unittest.TestCase):
    def test_only_the_six_converted_date_drafts_need_the_date_patch(self):
        drafts = load_drafts([PATH])
        self.assertEqual(len(drafts), 29)
        self.assertEqual({r['id'][8:] for r in drafts}, IDS)
        selected, withheld = select_drafts(drafts)
        self.assertEqual({r['id'][8:] for r in selected}, IDS-DATED)
        self.assertEqual({r['id'][8:] for r in withheld}, DATED)
        self.assertEqual(select_drafts(drafts, english_dialogue_dates=True), (drafts, []))
        for row in drafts:
            if row['id'][8:] in DATED:
                self.assertEqual(row['runtime_requirements'], ['ordinary_dialogue_dates'])
            else:
                self.assertNotIn('runtime_requirements', row)


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local input')
class NativeSeasonalTopicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.banks = {b.name: b.entries() for b in banks(cls.rom)}
        cls.drafts = load_drafts([PATH])
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}
        cls.visible = {id: plain(text) for id, text in cls.text.items()}
        _, report = make_halfwidth(cls.rom)
        cls.advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}

    def test_every_source_hash_and_complete_native_command_stream(self):
        commands = lambda raw: [t.data for t in tokenize(raw, self.info) if t.kind == 'cmd']
        for row in self.drafts:
            with self.subTest(id=row['id']):
                native = self.banks['message'][int(row['id'][8:], 16)]
                output = encode(row['translation'], self.info)
                self.assertEqual(row['source_sha256'], sha256(native))
                self.assertEqual(row['status'], 'draft')
                self.assertEqual(row.get('control_policy', 'exact'), 'exact')
                self.assertEqual(commands(output), commands(native))
                validate_entry(native, output, self.info, 'message', 'exact', resident_runtime=True)
                self.assertLessEqual(expanded_bound(output, self.info), 1024)

    def test_conservative_date_width_warnings_remain_visible(self):
        expected = {
            '11AE': ['page_1_line_2_width_296', 'page_1_line_2_width_301'],
            '11AF': ['page_0_line_1_width_264', 'page_0_line_1_width_268'],
            '180E': ['page_1_line_3_width_246', 'page_1_line_3_width_250'],
            '270F': ['page_4_line_3_width_246', 'page_4_line_3_width_251'],
            '27EE': ['page_1_line_1_width_196'],
            '2826': ['page_1_line_1_width_288', 'page_1_line_1_width_292'],
            '2827': ['page_2_line_1_width_264', 'page_2_line_1_width_268'],
        }
        actual = {}
        for id, text in self.text.items():
            issues = layout_issues(encode(text, self.info), self.info, self.advances, resident_runtime=True)
            if issues:
                actual[id] = issues
        self.assertEqual(actual, expected)

    def test_all_english_months_and_ordinal_days_fit_the_original_draft_lines(self):
        # Rendering-width check only: formatter/conversion correctness belongs
        # to the independent English-date and ordinary-dialogue-date tests.
        # Leave every other dynamic field at the existing conservative width.
        for id in DATED | {'27EE'}:
            for month in list(calendar.month_name)[1:]:
                for day in range(1, 32):
                    suffix = 'th' if 10 <= day % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                    text = (self.text[id].replace('{cmd:7F3E}', month)
                            .replace('{cmd:7F3F}', str(day)+suffix)
                            .replace('{cmd:7F1E}', month))
                    self.assertEqual(layout_issues(encode(text, self.info), self.info,
                                                  self.advances, resident_runtime=True), [], (id, month, day))

    def test_ten_questions_keep_native_choices_and_reply_order(self):
        for id, (choices, yes, no) in QUESTIONS.items():
            self.assertIn('{cmd:7F16'+choices+'}', self.text[id])
            self.assertIn('{cmd:7F0F'+yes+'}{cmd:7F10'+no+'}{cmd:7F19}', self.text[id])
            self.assertTrue(self.text[id].endswith('{cmd:7F01}'))
            for target in (yes, no):
                self.assertTrue(self.banks['message'][int(target, 16)])
        # Native semantics, independent of the existing global English labels.
        for id, text in (('002F', 'おしえて!'), ('0069', 'しってるよ'),
                         ('004E', 'えー、ヤだ!'), ('0052', 'ザンネンながら・・・'),
                         ('0162', 'あんまりー'), ('0044', 'いいよー!')):
            self.assertEqual(decode(self.banks['select'][int(id, 16)], self.info).rstrip(' '), text)

    def test_two_moon_viewings_keep_native_dates_locations_and_complete_jokes(self):
        for id in DATED:
            self.assertIn('{cmd:7F3E} {cmd:7F3F}', self.text[id])
            self.assertNotIn('{cmd:7F3C}', self.text[id])
            self.assertNotIn('{cmd:7F3D}', self.text[id])
        for phrase in ('twice a year', 'harvest moon', 'Thirteenth Night', 'own charm'):
            self.assertIn(phrase, self.visible['11AE'])
        for phrase in ('pond', 'six in the evening', 'Thirteenth Night', 'less than full'):
            self.assertIn(phrase, self.visible['11AF'])
        self.assertIn('samurai', self.visible['270F'])
        self.assertIn('lunar month nine, day 13', self.visible['270F'])
        self.assertIn('I like the SUN best!', self.visible['2826'])
        self.assertIn('Fifteenth Night', self.visible['2827'])
        for id in ('0BA7', '11AE', '11AF', '180D', '180E', '270E', '270F',
                   '27D0', '27D3', '27EE', '27EF', '2824', '2826', '2827'):
            self.assertNotIn('meteor', self.visible[id].lower())

    def test_three_corrected_replies_keep_the_original_rules_and_event(self):
        self.assertIn('any caught so far', self.visible['0BC5'])
        self.assertIn("you'll get a prize", self.visible['0BC5'])
        self.assertNotIn('end of the day', self.visible['0BC5'])
        self.assertIn('moon viewing', self.visible['27EE'])
        self.assertIn('autumn night', self.visible['27EE'])
        self.assertIn('{cmd:7F1E}', self.text['27EE'])
        for phrase in ('lunar month eight', 'day 15', 'dumplings', 'pond', 'someone else'):
            self.assertIn(phrase, self.visible['27EF'])
        self.assertTrue(self.text['27EE'].startswith('{cmd:7F0C050001}'))
        self.assertTrue(self.text['27EF'].startswith('{cmd:7F0C050066}'))

    def test_seasonal_requests_timing_and_sports_date_are_not_reference_substitutes(self):
        for id, request in (('27E2', '01'), ('27E3', '02'), ('281D', '01'), ('2829', '01')):
            self.assertIn('{cmd:7F09020001}{cmd:7F090800'+request+'}', self.text[id])
        for number in '543':
            self.assertIn(number+'{cmd:7F0306}.{cmd:7F0306}.{cmd:7F0306}.{cmd:7F0306}', self.text['27E3'])
        self.assertIn('second Monday', self.visible['11B1'])
        self.assertIn('October', self.visible['11B1'])
        self.assertNotIn('equinox', self.visible['11B1'])
        for phrase in ('6th', '7th', '5th', 'shrine', 'all three days'):
            self.assertIn(phrase, self.visible['27BC'])
        self.assertIn('ball tosses', self.visible['2829'])
        self.assertNotIn('tug', self.visible['2829'])
        self.assertIn('rainy days', self.visible['281D'])
        self.assertIn('matsutake mushrooms', self.visible['27D6'])
        self.assertTrue(self.text['27F2'].startswith('{cmd:7F0C050002}'))
        self.assertIn('get up early', self.visible['27F2'])
        self.assertIn('Christmas', self.visible['2834'])


if __name__ == '__main__':
    unittest.main()
