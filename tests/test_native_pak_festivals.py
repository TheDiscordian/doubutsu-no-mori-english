"""Original Pak and festival messages retain native actions and complete meaning."""

import json
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

PAK_IDS = set('08DF 08E0 08E7 08E8 08EB 08EC 08ED 08EE 1BD5 1BD6 1BD9 1BDA '
              '1BDB 1BDC 1BDD 1BDE 1BDF 1BE0 1BE1 1BE2 1BE3 1BE4 1BE5 1BE6 1BE7 1BE8'.split())
FESTIVAL_IDS = set('0B97 0B98 0BA3 0BA4 119E 119F 11AA 11AB 17FD 17FE 1809 180A '
                   '26FE 26FF 270A 270B 27C2 27C3 27CE 27CF 2816 2817 2822 2823 0BC4'.split())
PATHS = [ROOT/'translations'/name for name in ('n64-pak-storage-dialogue.json', 'n64-carp-fireworks.json')]


class PakFestivalDraftSelectionTests(unittest.TestCase):
    def test_all_fifty_one_drafts_are_available_in_basic_generation(self):
        drafts = load_drafts(PATHS)
        self.assertEqual(len(drafts), 51)
        self.assertEqual({r['id'][8:] for r in drafts}, PAK_IDS | FESTIVAL_IDS)
        self.assertEqual(select_drafts(drafts), (drafts, []))
        self.assertEqual(select_drafts(drafts, english_dialogue_dates=True), (drafts, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local input')
class NativePakFestivalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.drafts = load_drafts(PATHS)
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}

    def test_every_native_command_with_only_pak_colour_count_corrections(self):
        for draft in self.drafts:
            id = draft['id'][8:]; source = self.sources[int(id, 16)]
            output = encode(draft['translation'], self.info)
            controls = lambda raw: [t.data for t in tokenize(raw, self.info) if t.kind == 'cmd']
            expected = controls(source)
            if id in PAK_IDS:
                expected = [bytes.fromhex('7F50198CDC0E') if c == bytes.fromhex('7F50198CDC09') else c
                            for c in expected]
                count = controls(source).count(bytes.fromhex('7F50198CDC09'))
                self.assertEqual(draft['translation'].count('{cmd:7F50198CDC0E}Controller Pak'), count, id)
            else:
                count = 0
            self.assertEqual(controls(output), expected, id)
            self.assertEqual(draft.get('control_policy', 'exact'), 'reference_layout' if count else 'exact', id)
            self.assertEqual(sha256(source), draft['source_sha256'])
            self.assertEqual(draft['status'], 'draft')
            validate_entry(source, output, self.info, 'message', draft.get('control_policy', 'exact'), resident_runtime=True)
            self.assertLessEqual(expanded_bound(output, self.info), 1024)

    def test_layout_fits_with_native_town_name_limit_and_no_reflow(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        warnings = {}
        for draft in self.drafts:
            output = encode(draft['translation'], self.info)
            issues = layout_issues(output, self.info, advances, resident_runtime=True)
            if issues: warnings[draft['id'][8:]] = issues
            # The generic checker reserves sixteen Japanese cells for 2F.
            # Retain that warning; separately test the unchanged native six-
            # cell town-name limit, with Japanese rather than smaller Latin.
            output = output.replace(bytes.fromhex('7F2F'), b'\x00'*6)
            self.assertEqual(layout_issues(output, self.info, advances, resident_runtime=True), [], draft['id'])
        self.assertEqual(warnings, {'27C2': ['page_0_line_1_width_238'],
                                    '2816': ['page_0_line_3_width_210', 'page_0_line_3_width_214']})

    def test_missing_unreadable_space_note_slots_and_removal_remain_distinct(self):
        text = {id: plain(value) for id, value in self.text.items()}
        self.assertIn('you need a Controller Pak', text['08E7'])
        self.assertIn("isn't plugged in", text['08E8'])
        for id in ('08E7', '08E8'):
            self.assertNotIn('corrupt', text[id]); self.assertNotIn('read', text[id])
        for id in ('1BD5', '1BD6'): self.assertIn("couldn't be read", text[id])
        for id in ('08EB', '08EC'): self.assertIn("isn't enough space", text[id])
        self.assertIn('no free note slots', text['1BD9'])
        self.assertIn("can't hold any more notes", text['1BDA'])
        for id in ('1BE5', '1BE6'): self.assertIn('remove', text[id])
        for id in PAK_IDS: self.assertNotIn('Memory Card', text[id])

    def test_repair_warnings_precede_native_choices_and_actions_are_unchanged(self):
        for id, yes, no in (('1BDB', '1BDD', '1BDF'), ('1BDC', '1BDE', '1BE0')):
            text = self.text[id]
            self.assertLess(text.index('saved data'), text.index('{cmd:7F160003000D}'))
            self.assertIn('lost' if id == '1BDB' else 'disappear', text)
            self.assertIn('{cmd:7F0F'+yes+'}{cmd:7F10'+no+'}', text)
        for id in ('1BDD', '1BDE'):
            self.assertIn('Do not remove', self.text[id])
            self.assertIn('the Controller Pak!', self.text[id])
            self.assertIn('{cmd:7F5904}{cmd:7F09090001}', self.text[id])
        for id, target in (('1BE1', '08E9'), ('1BE2', '08EA')):
            self.assertIn('{cmd:7F09090001}{cmd:7F0E'+target+'}', self.text[id])
        for id in ('1BE7', '1BE8'):
            self.assertIn('{cmd:7F09090001}{cmd:7F04}{cmd:7F09090002}{cmd:7F19}', self.text[id])

    def test_post_office_menus_keep_three_services_and_native_targets(self):
        for id, mail, leave in (('08DF', '08B5', '08B3'), ('08E0', '08B6', '08B4')):
            text = self.text[id]
            self.assertIn('{cmd:7F17005B009D0015}', text)
            self.assertIn('{cmd:7F0F'+mail+'}{cmd:7F101BE7}{cmd:7F11'+leave+'}', text)
            self.assertNotIn('{cmd:7F18', text)
        select = next(b for b in banks(self.rom) if b.name == 'select').entries()
        for number, native in ((0x5B, 'てがみをだしたい'), (0x9D, 'てがみをほぞんしたい'), (0x15, 'いや、なにも')):
            self.assertEqual(decode(select[number], self.info).rstrip(' '), native)

    def test_streamer_topics_and_corrected_connected_response(self):
        self.assertIn('carp streamer', self.text['0B98'])
        self.assertIn('{cmd:7F1600DC00DB}', self.text['0B98'])
        self.assertIn('{cmd:7F0F0BC3}{cmd:7F100BC4}', self.text['0B98'])
        for phrase in ('through the tail', 'out of the mouth', 'grown-up', 'Yoo-hoo'):
            self.assertIn(phrase, self.text['0BC4'])
        self.assertIn('no mother', self.text['0B97'])
        self.assertIn('up waterfalls', self.text['119F'])
        self.assertIn('rising in the world', self.text['119F'])
        self.assertIn('Dumpling Festival', self.text['27C3'])
        self.assertIn('{cmd:7F09020003}{cmd:7F09080001}', self.text['27C3'])
        self.assertIn('backbone', self.text['2817'])

    def test_native_fireworks_dates_venues_and_question_branches(self):
        for id in ('0BA4', '270B'):
            self.assertIn('7:00 p.m.', self.text[id])
            self.assertIn('Saturday', self.text[id]); self.assertIn('pond', self.text[id])
        for id in ('270A', '27CE'): self.assertIn('August', self.text[id])
        for id in ('11AA', '27CF'): self.assertIn('pond', self.text[id])
        self.assertIn('shrine plaza', self.text['2823'])
        self.assertIn('Fridays', self.text['2822'])
        self.assertIn('morning aerobics', self.text['27CE'])
        self.assertIn('{cmd:7F16004C0052}', self.text['1809'])
        self.assertIn('{cmd:7F0F182F}{cmd:7F101830}', self.text['1809'])
        for text in self.text.values():
            self.assertNotIn('July 4', text)
            self.assertNotIn('Harvest Festival', text)
