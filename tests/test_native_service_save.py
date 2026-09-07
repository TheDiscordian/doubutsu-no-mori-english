"""Native service and saving dialogue preserves decisions and warning context."""

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

PATH = ROOT/'translations/n64-service-save-dialogue.json'
SERVICE_IDS = set('08CF 08D0 08D1 08D2 08D3 08D4 08DD 08DE 08B0 08B2 '
                  '0925 0927 0932 0936'.split())
TRAVEL_IDS = set('0946 0947 0948 094C 094D 094F 0951 0952 0953 0954 0955 0956 '
                 '0957 095E 0967'.split())
SAVE_IDS = {f'{n:04X}' for n in range(0x2B09, 0x2B1B)}
COLOURS = {'7F50198CDC09': ('7F50198CDC0E', 'Controller Pak'),
           '7F50E11ED706': ('7F50E11ED709', 'town data'),
           '7F504BA00002': ('7F504BA00007', 'station')}


class ServiceSaveSelectionTests(unittest.TestCase):
    def test_all_forty_seven_drafts_are_available_without_optional_runtime(self):
        drafts = load_drafts([PATH])
        self.assertEqual(len(drafts), 47)
        self.assertEqual({d['id'][8:] for d in drafts}, SERVICE_IDS | TRAVEL_IDS | SAVE_IDS)
        self.assertEqual(select_drafts(drafts), (drafts, []))
        self.assertEqual(select_drafts(drafts, english_dialogue_dates=True), (drafts, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local input')
class NativeServiceSaveTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.banks = {b.name: b.entries() for b in banks(cls.rom)}
        cls.drafts = load_drafts([PATH]); cls.text = {d['id'][8:]: d['translation'] for d in cls.drafts}

    def test_full_native_command_stream_with_only_exact_colour_length_changes(self):
        controls = lambda raw: [t.data.hex().upper() for t in tokenize(raw, self.info) if t.kind == 'cmd']
        for draft in self.drafts:
            native = self.banks['message'][int(draft['id'][8:], 16)]
            output = encode(draft['translation'], self.info); original = controls(native)
            expected = [COLOURS[c][0] if c in COLOURS else c for c in original]
            self.assertEqual(controls(output), expected, draft['id'])
            for before, (after, term) in COLOURS.items():
                self.assertEqual(draft['translation'].count('{cmd:'+after+'}'+term), original.count(before), draft['id'])
            self.assertEqual(draft.get('control_policy', 'exact'),
                             'reference_layout' if expected != original else 'exact', draft['id'])
            self.assertEqual(sha256(native), draft['source_sha256'])
            self.assertEqual(draft['status'], 'draft')
            validate_entry(native, output, self.info, 'message', draft.get('control_policy', 'exact'), resident_runtime=True)
            self.assertLessEqual(expanded_bound(output, self.info), 1024)

    def test_original_draft_layout_except_explicit_amount_field_width_review(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        warnings = {}
        for draft in self.drafts:
            issues = layout_issues(encode(draft['translation'], self.info), self.info, advances, resident_runtime=True)
            if issues: warnings[draft['id'][8:]] = issues
        amount_warnings = [f'page_1_line_2_width_{n}' for n in (240, 246, 252, 258, 262, 266, 272, 276)]
        self.assertEqual(warnings, {'08D3': amount_warnings, '08D4': amount_warnings})
        # Keep the generic free-field warnings. The loader tests do not prove
        # the ordinary money preparer's values or final rendered amount width.

    def test_post_office_three_and_four_service_branches_are_distinct(self):
        for id, mail, storage, leave in (
                ('08CF', '08AF', '1BE7', '08B3'), ('08D0', '08B0', '1BE8', '08B4'),
                ('08D1', '08B5', '1BE7', '08B3'), ('08D2', '08B6', '1BE8', '08B4'),
                ('08DD', '08AF', '1BE7', '08B3'), ('08DE', '08B0', '1BE7', '08B4')):
            self.assertIn('{cmd:7F17005B009D0015}', self.text[id])
            self.assertIn('{cmd:7F0F'+mail+'}{cmd:7F10'+storage+'}{cmd:7F11'+leave+'}', self.text[id])
            self.assertNotIn('{cmd:7F18', self.text[id])
        self.assertIn('{cmd:7F18005B005D009D0015}', self.text['08B2'])
        self.assertIn('{cmd:7F0F08B6}{cmd:7F1008D4}{cmd:7F111BE8}{cmd:7F1208B4}', self.text['08B2'])

    def test_gyroid_menu_keeps_native_revise_store_save_leave_order(self):
        for id in ('0925', '0927', '0936'):
            self.assertIn('{cmd:7F1800130014005E0015}', self.text[id])
            self.assertIn('{cmd:7F0F0927}{cmd:7F100927}{cmd:7F11092D}{cmd:7F120926}', self.text[id])
        for number, native in ((0x13, 'メッセージをなおす'), (0x14, 'アイテムをあずける'),
                               (0x5E, 'きろくしたい'), (0x15, 'いや、なにも')):
            self.assertEqual(decode(self.banks['select'][number], self.info).rstrip(' '), native)
        self.assertIn('Bells you carry', self.text['0936'])
        self.assertIn('{cmd:7F5900}', self.text['0936'])

    def test_payment_fields_wait_and_phyllis_inner_voice_stay_native(self):
        for id in ('08D3', '08D4'):
            self.assertIn('{cmd:7F25}{cmd:7F26} Bells', self.text[id])
            self.assertTrue(self.text[id].endswith('{cmd:7F04}{cmd:7F19}\n{cmd:7F01}'))
            self.assertNotIn('{cmd:7F55}', self.text[id])
        for phrase in ('booked solid', 'ask Pete', 'extra delivery', "can't take it right now"):
            self.assertIn(phrase, plain(self.text['08B0']))
        self.assertEqual(self.text['08B0'].count('{cmd:7F5100}'), 4)
        self.assertEqual(self.text['08B0'].count('{cmd:7F5101}'), 4)

    def test_travel_erasure_and_repair_outcomes_retain_their_native_meanings(self):
        visible = {id: plain(text) for id, text in self.text.items()}
        self.assertIn("'s record", visible['0947']); self.assertIn('erased', visible['0947'])
        self.assertIn('{cmd:7F25}', self.text['0947'])
        self.assertIn('{cmd:7F0E094B}{cmd:7F04}{cmd:7F19}', self.text['0947'])
        self.assertIn("won't go ahead", visible['0946'])
        self.assertIn('enough free space', visible['0948'])
        self.assertIn('free note slots', visible['0951'])
        for id in ('0948', '0951'):
            self.assertIn('{cmd:7F0F094D}{cmd:7F10094C}', self.text[id])
        self.assertIn('saved data to be lost', visible['0952'])
        self.assertLess(self.text['0952'].index('saved data'), self.text['0952'].index('{cmd:7F160003000D}'))
        for id in ('0952', '0956'):
            self.assertIn('{cmd:7F0F0953}{cmd:7F100954}', self.text[id])
        self.assertIn('connect another Controller Pak', visible['0954'])
        self.assertNotIn('complete', visible['0954']); self.assertNotIn('success', visible['0954'])
        self.assertIn('Repairs are complete', visible['0955'])
        self.assertIn('{cmd:7F0E094B}{cmd:7F04}{cmd:7F19}{cmd:7F09090001}', self.text['0955'])
        self.assertIn("couldn't repair", visible['0956']); self.assertNotIn('format', visible['0956'])
        self.assertIn("Don't remove", visible['0957'])
        self.assertIn("can't board the train", visible['095E'])
        self.assertIn("couldn't write to", visible['0967'])
        for id in TRAVEL_IDS: self.assertNotIn('Memory Card', visible[id])

    def test_saving_and_repair_warnings_precede_native_requests(self):
        ids = ['0932', '094F']+[f'{n:04X}' for n in range(0x2B09, 0x2B1B) if (n-0x2B09)%3]
        for id in ids:
            self.assertLess(self.text[id].index('Do not turn the power off!'),
                            self.text[id].index('{cmd:7F5904}{cmd:7F09090001}'))
        for id in ('094F', '0953'):
            self.assertLess(self.text[id].index('Do not remove the'),
                            self.text[id].index('{cmd:7F5904}{cmd:7F09090001}'))
            self.assertIn('Controller Pak!', self.text[id])

    def test_six_save_questions_keep_quit_continue_targets_and_acknowledgements(self):
        for n in range(0x2B09, 0x2B1B, 3):
            question, quit_id, continue_id = (f'{i:04X}' for i in (n, n+1, n+2))
            self.assertIn('{cmd:7F1601AE01AF}', self.text[question])
            self.assertIn('{cmd:7F0F'+quit_id+'}{cmd:7F10'+continue_id+'}', self.text[question])
            for id in (quit_id, continue_id):
                self.assertIn('{cmd:7F09090001}\n{cmd:7F04}\n{cmd:7F02}', self.text[id])
                self.assertTrue(self.text[id].endswith('{cmd:7F00}'))
                self.assertNotIn('Memory Card', self.text[id]); self.assertNotIn('Slot ', self.text[id])
            # Only the continue ending contains the additional native pause.
            after = self.text[continue_id].split('{cmd:7F09000015}', 1)[1]
            self.assertIn('{cmd:7F0304}', after)
            self.assertNotIn('{cmd:7F0304}', self.text[quit_id].split('{cmd:7F09000015}', 1)[1])
        for number, native in ((0x1AE, 'きろくして おわる'), (0x1AF, 'きろくして つづける')):
            self.assertEqual(decode(self.banks['select'][number], self.info).rstrip(' '), native)


if __name__ == '__main__':
    unittest.main()
