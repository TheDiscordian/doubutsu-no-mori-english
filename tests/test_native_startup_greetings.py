"""Startup identity, preparation, and menus retain their native flow."""

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

PATH = ROOT/'translations/n64-startup-greetings.json'
BASES = (0x1400, 0x1428, 0x1450, 0x1478, 0x14A0, 0x14C8)
IDS = ({f'{base+delta:04X}' for base in BASES for delta in (-11, -9, 4, 5, 8, 10, 16, 18)}
       - {'143A'}) | {'1437', '14A2', '14D9'}
COLOURS = {'7F50198CDC09': ('7F50198CDC0E', 'Controller Pak'),
           '7F50198CDC04': ('7F50198CDC09', 'cartridge')}
TOWN_WARNINGS = set('1404 1405 140A 1410 142C 142D 1432 1438 1454 1455 '
                    '145A 1460 147D 1482 1488 14A4 14B0'.split())


class StartupGreetingSelectionTests(unittest.TestCase):
    def test_fifty_native_drafts_are_available_without_optional_runtime(self):
        drafts = load_drafts([PATH])
        self.assertEqual(len(drafts), 50)
        self.assertEqual({r['id'][8:] for r in drafts}, IDS)
        self.assertEqual(select_drafts(drafts), (drafts, []))
        self.assertEqual(select_drafts(drafts, english_dialogue_dates=True), (drafts, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local input')
class NativeStartupGreetingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.banks = {b.name: b.entries() for b in banks(cls.rom)}
        cls.drafts = load_drafts([PATH])
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}
        cls.visible = {id: plain(text) for id, text in cls.text.items()}

    def test_complete_native_hashes_and_commands_with_only_two_highlight_changes(self):
        commands = lambda raw: [t.data.hex().upper() for t in tokenize(raw, self.info) if t.kind == 'cmd']
        for row in self.drafts:
            with self.subTest(id=row['id']):
                native = self.banks['message'][int(row['id'][8:], 16)]
                output = encode(row['translation'], self.info)
                original = commands(native)
                expected = [COLOURS[c][0] if c in COLOURS else c for c in original]
                self.assertEqual(row['source_sha256'], sha256(native))
                self.assertEqual(commands(output), expected)
                for before, (after, term) in COLOURS.items():
                    self.assertEqual(row['translation'].count('{cmd:'+after+'}'+term), original.count(before))
                self.assertEqual(row['status'], 'draft')
                self.assertEqual(row.get('control_policy', 'exact'),
                                 'reference_layout' if expected != original else 'exact')
                validate_entry(native, output, self.info, 'message', row.get('control_policy', 'exact'), resident_runtime=True)
                self.assertLessEqual(expanded_bound(output, self.info), 1024)

    def test_only_generic_town_widths_warn_and_all_six_cell_native_towns_fit(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        warnings = set()
        for id, text in self.text.items():
            output = encode(text, self.info)
            issues = layout_issues(output, self.info, advances, resident_runtime=True)
            if issues:
                warnings.add(id)
                self.assertTrue(all('width_' in issue for issue in issues))
                self.assertIn('{cmd:7F2F}', text)
            output = output.replace(bytes.fromhex('7F2F'), b'\x00'*6)
            self.assertEqual(layout_issues(output, self.info, advances, resident_runtime=True), [], id)
        self.assertEqual(warnings, TOWN_WARNINGS)

    def test_eighteen_ordinary_preparations_keep_wait_completion_and_final_farewell(self):
        for base in BASES:
            for delta in (4, 5, 16):
                id = f'{base+delta:04X}'
                text = self.text[id]
                self.assertEqual(text.count('{cmd:7F05C35F00}'), 2)
                self.assertLess(text.index('Do not turn the power off!'), text.index('{cmd:7F5904}{cmd:7F09090001}'))
                self.assertIn('{cmd:7F09090001}\n{cmd:7F04}\n{cmd:7F02}', text)
                self.assertTrue(text.endswith('{cmd:7F00}'))
                self.assertNotIn('{cmd:7F0E', text)
                self.assertNotIn('Memory Card', self.visible[id])
        self.assertIn('{cmd:7F05969696}{cmd:7F5100}(I totally forgot.){cmd:7F5101}', self.text['1454'])
        self.assertEqual(self.text['147C'].count('{cmd:7F1A}'), 2)
        for id in ('14CC', '14CD', '14D8'):
            self.assertIn('Hmhm.', self.visible[id])

    def test_returning_and_visiting_players_keep_different_fields_and_continuations(self):
        for base in BASES:
            for delta, target in ((8, 7), (10, 9)):
                id = f'{base+delta:04X}'
                text = self.text[id]
                self.assertEqual(text.count('{cmd:7F26}'), 1)
                self.assertEqual(text.count('{cmd:7F05C35F00}'), 4)
                for warning in ('Do not turn the power off!', 'Do not remove the'):
                    self.assertLess(text.index(warning), text.index('{cmd:7F5904}{cmd:7F09090001}'))
                self.assertIn('{cmd:7F0E'+f'{base+target:04X}'+'}', text)
                self.assertTrue(text.endswith('{cmd:7F01}'))
            self.assertIn('copy your record from the Controller Pak to the cartridge', self.visible[f'{base+8:04X}'])
            self.assertNotIn('copy your record', self.visible[f'{base+10:04X}'])
        self.assertIn('{cmd:7F504B5F9B01}!', self.text['1480'])
        self.assertNotIn('{cmd:7F2F}', self.text['14AA'])
        self.assertNotIn('{cmd:7F2F}', self.text['14D2'])

    def test_three_option_sound_menu_has_no_rumble_and_other_menu_has_native_order(self):
        for base in BASES:
            first = self.text[f'{base-11:04X}']
            self.assertIn('{cmd:7F17007001B30029}', first)
            branches = '{cmd:7F0F'+f'{base-10:04X}'+'}{cmd:7F10'+f'{base+18:04X}'+'}{cmd:7F11'+f'{base-12:04X}'+'}'
            self.assertIn(branches, first)
            self.assertNotIn('{cmd:7F18', first)
            self.assertIn('{cmd:7F09090003}', first)
            if base == 0x1428:
                continue
            other = self.text[f'{base+18:04X}']
            self.assertIn('{cmd:7F180072007300710029}', other)
            for command, target in ((0x0F, base-7), (0x10, base-1), (0x11, base-9), (0x12, base-12)):
                self.assertIn('{cmd:7F'+f'{command:02X}{target:04X}'+'}', other)
        for id, text in ((0x70, 'おとの せってい'), (0x1B3, 'ほかのこと'), (0x29, 'やっぱ、やめとく'),
                         (0x72, 'おうちを とりこわす'), (0x73, 'むらを つくりなおす'), (0x71, 'とけいを あわせる')):
            self.assertEqual(decode(self.banks['select'][id], self.info).rstrip(' '), text)

    def test_six_clock_acknowledgements_keep_native_target_without_gamecube_command(self):
        for base in BASES:
            text = self.text[f'{base-9:04X}']
            self.assertIn('clock', text)
            self.assertTrue(text.endswith('{cmd:7F04}{cmd:7F0E'+f'{base-8:04X}'+'}{cmd:7F19}\n{cmd:7F01}'))
            self.assertNotIn('{cmd:7F5B}', text)

    def test_away_player_warning_town_reset_cancellation_and_identity_retry(self):
        text = self.text['1437']
        self.assertEqual(text.count('{cmd:7F1A}'), 2)
        for phrase in ('out travelling', 'record left here', 'items and money', 'nothing left here'):
            self.assertIn(phrase, self.visible['1437'])
        self.assertLess(text.index('nothing'), text.index('{cmd:7F160044003D}'))
        self.assertIn('{cmd:7F0F1438}{cmd:7F101439}{cmd:7F19}{cmd:7F09090007}', text)
        self.assertIn('not going to rebuild', self.visible['14A2'])
        self.assertIn('disappear', self.visible['14A2'])
        self.assertTrue(self.text['14A2'].endswith('{cmd:7F0E1494}\n{cmd:7F01}'))
        self.assertIn('{cmd:7F0D}{cmd:7F19}{cmd:7F090000FF}{cmd:7F09090006}', self.text['14D9'])
        self.assertIn('who you are', self.visible['14D9'])


if __name__ == '__main__':
    unittest.main()
