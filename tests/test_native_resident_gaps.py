"""Complete native conversations with exact actions and explicit display changes."""

from pathlib import Path
import json
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from font import make_halfwidth
from gc_text import plain
from reference_candidates import load_drafts, select_drafts
from reference_content import adapt_content_reference, validate_content_candidate
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

PATH = ROOT/'translations/n64-resident-gaps.json'
IDS = set('02BB 03B9 084F 0850 087B 0AF8 0F8B 10C8 1506 17C9 1C82 '
          '1DCD 213B 2311 23E2 24D5 24D6 2A43'.split())
REFERENCES = {'2BC3': '2DD1', '2BC5': '2DD3', '2BC7': '2DD5', '2BC9': '2DD7'}
COLOURS = {'084F': {'7f504ba00007': '7f504ba0000b',
                    '7f50e11ed706': '7f50e11ed70b', '7f50324be104': '7f50324be108'},
           '0850': {'7f504ba00007': '7f504ba0000b',
                    '7f50e11ed708': '7f50e11ed70b', '7f504ba00005': '7f504ba0000e'}}


class ResidentGapSelectionTests(unittest.TestCase):
    def test_only_the_sleeping_hour_draft_requires_the_module(self):
        drafts = load_drafts([PATH])
        self.assertEqual(len(drafts), 18)
        self.assertEqual({r['id'][8:] for r in drafts}, IDS)
        selected, withheld = select_drafts(drafts)
        self.assertEqual({r['id'][8:] for r in selected}, IDS-{'2311'})
        self.assertEqual(withheld, [{'id': 'message:2311', 'reason': 'resident_runtime_unavailable',
                                     'module_commands': ['7F76']}])
        self.assertEqual(select_drafts(drafts, resident_runtime=True), (drafts, []))
        self.assertTrue(all('runtime_requirements' not in r for r in drafts))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains local')
class ResidentGapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.banks = {b.name: b.entries() for b in banks(cls.rom)}
        cls.drafts = load_drafts([PATH])
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}
        cls.visible = {id: plain(text) for id, text in cls.text.items()}
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k,16): v for k,v in font['advance_by_glyph'].items()}

    def test_complete_sources_and_commands_allow_only_seven_colours_and_one_meridiem(self):
        commands = lambda raw: [t.data.hex() for t in tokenize(raw, self.info) if t.kind == 'cmd']
        colour_changes = 0
        for row in self.drafts:
            id = row['id'][8:]; source = self.banks['message'][int(id,16)]
            output = encode(row['translation'], self.info)
            self.assertEqual(sha256(source), row['source_sha256'], id)
            expected = []
            for cmd in commands(source):
                replacement = COLOURS.get(id, {}).get(cmd, cmd)
                colour_changes += replacement != cmd
                expected.append(replacement)
                if id == '2311' and cmd == '7f21': expected.append('7f76')
            self.assertEqual(commands(output), expected, id)
            policy = 'reference_layout' if id in {'084F', '0850', '2311'} else 'exact'
            self.assertEqual(row.get('control_policy', 'exact'), policy)
            validate_entry(source, output, self.info, 'message', policy, resident_runtime=True)
            self.assertLessEqual(expanded_bound(output, self.info), 1024)
            self.assertEqual(row['status'], 'draft')
        self.assertEqual(colour_changes, 7)

    def test_static_lines_fit_and_conservative_dynamic_warnings_stay_visible(self):
        warned = set()
        for id, text in self.text.items():
            issues = layout_issues(encode(text, self.info), self.info, self.advances, resident_runtime=True)
            if issues: warned.add(id)
            self.assertFalse(any('line_count' in issue for issue in issues), id)
        self.assertEqual(warned, {'0850', '1506', '1C82', '2311', '23E2'})

    def test_known_native_name_and_clock_widths_fit_without_reflow(self):
        # Width check, not proof of ordinary actor preparation or rendering.
        # Preserve every other field at its existing conservative width.
        for hour in range(1,13):
            for meridiem in ('AM', 'PM'):
                for id, text in self.text.items():
                    text = (text.replace('{cmd:7F2F}', 'ア'*6)
                            .replace('{cmd:7F21}', str(hour))
                            .replace('{cmd:7F76}', meridiem)
                            .replace('{cmd:7F32}', '9'*10))
                    self.assertEqual(layout_issues(encode(text, self.info), self.info,
                                     self.advances, resident_runtime=True), [], (id,hour,meridiem))

    def test_native_choices_and_special_actions_remain(self):
        for id, choices, yes, no in (('0F8B','00DC00ED','29A8','29A9'),
                                    ('213B','0044003D','213C','213D')):
            self.assertIn('{cmd:7F16'+choices+'}', self.text[id])
            self.assertIn('{cmd:7F0F'+yes+'}{cmd:7F10'+no+'}{cmd:7F19}', self.text[id])
        self.assertTrue(self.text['02BB'].startswith('{cmd:7F0905006B}{cmd:7F09000010}'))
        self.assertIn('{cmd:7F0C030001}{cmd:7F04}', self.text['0AF8'])
        self.assertTrue(self.text['213B'].startswith('{cmd:7F0C050003}'))
        self.assertIn('{cmd:7F0C090002}', self.text['23E2'])
        self.assertIn('{cmd:7F32}', self.text['23E2'])
        self.assertNotIn('{cmd:7F22}', self.text['23E2'])
        self.assertTrue(self.text['1DCD'].endswith('{cmd:7F5832}'))
        self.assertNotIn('{cmd:7F1D}', self.text['1DCD'])

    def test_native_letter_instructions_and_both_boards_are_complete(self):
        for phrase in ('post office', 'interesting', 'write you back', 'presents',
                       'Grab the item', 'item screen', 'move it over', 'A Button',
                       'attached a present', 'look forward to it'):
            self.assertIn(phrase, self.visible['084F'])
        self.assertEqual(self.visible['0850'].count('bulletin board'), 2)
        for phrase in ('town melody', 'chimes', 'Anybody can change it',
                       'your house', 'no matter where', 'Looking for friends', 'cute boys'):
            self.assertIn(phrase, self.visible['0850'])

    def test_native_moving_capacity_and_flower_topics_do_not_import_other_gameplay(self):
        for phrase in ('all by myself', 'come with you', 'move there', 'visit another town'):
            self.assertIn(phrase, self.visible['087B'])
        for phrase in ('town you visit', 'town I move to', 'think carefully', 'straight back'):
            self.assertIn(phrase, self.visible['1506'])
        self.assertNotIn('{cmd:7F16', self.text['1506'])
        self.assertTrue(self.text['1506'].endswith('{cmd:7F00}'))
        self.assertIn('carry anything more', self.visible['17C9'])
        self.assertNotIn('Gracie', self.visible['17C9'])
        self.assertIn('flowers', self.visible['2A43']); self.assertIn('wilt', self.visible['2A43'])
        for id, field in (('1C82','3B'), ('24D5','39'), ('24D6','39'), ('2A43','33')):
            self.assertNotIn('{cmd:7F'+field+'}', self.text[id])

    def test_four_introductions_use_complete_english_references_at_identical_native_sources(self):
        path = ROOT/'build/gamecube/text/message.jsonl'
        if not path.is_file(): self.skipTest('English extraction stays local')
        gc = {r['id']: r for r in map(json.loads, path.read_text().splitlines())}
        matches = load_matches(ROOT/'translations/reference_matches.json')
        for id, target in REFERENCES.items():
            native = self.banks['message'][int(id,16)]
            self.assertEqual(native, self.banks['message'][int(target,16)])
            record = matches['message:'+id]; reference = gc['message:'+target]
            self.assertEqual(record['reference_id'], reference['id'])
            self.assertNotIn('spans', record['complete_reference'])
            text, changes = adapt_content_reference(reference, native, record, self.info)
            self.assertEqual(text, reference['text']); self.assertEqual(changes, [])
            output = encode(text, self.info)
            validate_content_candidate(record['id'], native, output, matches)
            validate_entry(native, output, self.info, 'message', 'reference_layout', resident_runtime=True)
            self.assertLessEqual(expanded_bound(output, self.info), 1024)
            self.assertTrue(text.startswith('{cmd:7F09020005}{cmd:7F09080000}'))
            self.assertNotIn('{cmd:7F36}', text)
            for phrase in (('middle of the night', 'My name', 'just wanted to say hello') if id == '2BC9'
                           else ('raise your voice', 'your name', 'name!')):
                self.assertIn(phrase, plain(text))


if __name__ == '__main__':
    unittest.main()
