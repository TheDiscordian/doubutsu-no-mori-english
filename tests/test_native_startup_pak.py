"""Native startup travel preserves storage warnings, choices, and requests."""

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
from textcodec import encode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

PATH = ROOT/'translations/n64-startup-pak.json'
BASES = (0x1400, 0x1428, 0x1450, 0x1478, 0x14A0, 0x14C8)
DELTAS = (0x0C, 0x13, 0x15, 0x16, 0x17, 0x18)
IDS = {f'{base+delta:04X}' for base in BASES for delta in DELTAS} - {'14DB'}
COLOURS = {
    '7F50198CDC09': ('7F50198CDC0E', 'Controller Pak'),
    '7F50198CDC06': ('7F50198CDC0A', 'controller'),
    '7F50BE2D2D07': ('7F50BE2D2D0C', 'START button'),
    '7F50324BE104': ('7F50324BE108', 'A Button'),
    '7F50198CDC04': ('7F50198CDC09', 'cartridge'),
}


class StartupPakSelectionTests(unittest.TestCase):
    def test_all_thirty_five_drafts_are_available_without_optional_runtime(self):
        drafts = load_drafts([PATH])
        self.assertEqual(len(drafts), 35)
        self.assertEqual({r['id'][8:] for r in drafts}, IDS)
        self.assertEqual(select_drafts(drafts), (drafts, []))
        self.assertEqual(select_drafts(drafts, english_dialogue_dates=True), (drafts, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local input')
class NativeStartupPakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.drafts = load_drafts([PATH])
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}
        cls.visible = {id: plain(text) for id, text in cls.text.items()}

    def test_complete_sources_and_commands_except_exact_hardware_highlight_lengths(self):
        commands = lambda raw: [t.data.hex().upper() for t in tokenize(raw, self.info) if t.kind == 'cmd']
        for row in self.drafts:
            with self.subTest(id=row['id']):
                native = self.sources[int(row['id'][8:], 16)]
                output = encode(row['translation'], self.info)
                original = commands(native)
                expected = [COLOURS[c][0] if c in COLOURS else c for c in original]
                self.assertEqual(row['source_sha256'], sha256(native))
                self.assertEqual(commands(output), expected)
                for before, (after, term) in COLOURS.items():
                    self.assertEqual(row['translation'].count('{cmd:'+after+'}'+term), original.count(before))
                self.assertEqual(row['status'], 'draft')
                self.assertEqual(row['control_policy'], 'reference_layout')
                validate_entry(native, output, self.info, 'message', 'reference_layout', resident_runtime=True)
                self.assertLessEqual(expanded_bound(output, self.info), 1024)

    def test_all_original_draft_lines_fit_the_approved_font(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        for id, text in self.text.items():
            self.assertEqual(layout_issues(encode(text, self.info), self.info,
                                          advances, resident_runtime=True), [], id)

    def test_six_capacity_messages_keep_the_native_manager_and_start_prompt(self):
        bodies = []
        for base in BASES:
            id, target = f'{base+0xC:04X}', f'{base-0xC:04X}'
            text, visible = self.text[id], self.visible[id]
            for phrase in ('space is insufficient', 'delete any data', 'you no longer need',
                           'START button', 'reset your N64', 'screen used to delete',
                           "If you don't want to use", 'remove it', 'A Button'):
                self.assertIn(phrase, visible, id)
            ending = '{cmd:7F0E'+target+'}\n{cmd:7F01}'
            self.assertTrue(text.endswith(ending))
            self.assertNotIn('{cmd:7F16', text)
            bodies.append(text.removesuffix(ending))
        self.assertTrue(all(body == bodies[0] for body in bodies))

    def test_six_duplicate_return_warnings_precede_the_unchanged_confirmation(self):
        for base in BASES:
            id, yes, no = (f'{base+n:04X}' for n in (0x15, 0x16, 0x17))
            text, visible = self.text[id], self.visible[id]
            self.assertEqual(text.count('{cmd:7F26}'), 2)
            self.assertIn('already come home', visible)
            self.assertIn('from the earlier return will be erased', visible)
            self.assertLess(text.index('will be erased'), text.index('{cmd:7F5E}'))
            self.assertIn('{cmd:7F5E}{cmd:7F160066003D}', text)
            self.assertIn('{cmd:7F0F'+yes+'}{cmd:7F10'+no+'}{cmd:7F19}{cmd:7F09090001}', text)
            self.assertTrue(text.endswith('{cmd:7F01}'))

    def test_accepted_transfer_warns_before_request_and_keeps_post_wait_target(self):
        for base in BASES:
            id, target = f'{base+0x16:04X}', f'{base+7:04X}'
            text, visible = self.text[id], self.visible[id]
            self.assertIn('copy the record from your Controller Pak to the cartridge', visible)
            self.assertEqual(text.count('{cmd:7F05C35F00}'), 4)
            for warning in ('Do not turn the power off!', 'Do not remove the'):
                self.assertLess(text.index(warning), text.index('{cmd:7F5904}{cmd:7F09090001}'))
            self.assertTrue(text.endswith('{cmd:7F5904}{cmd:7F09090001}{cmd:7F0E'+target+'}\n{cmd:7F01}'))

    def test_cancellation_disconnects_pak_then_returns_to_the_native_start_prompt(self):
        for base in BASES:
            id, target = f'{base+0x17:04X}', f'{base-0xC:04X}'
            text, visible = self.text[id], self.visible[id]
            self.assertIn('remove the Controller Pak from your controller', visible)
            self.assertLess(visible.index('remove the'), visible.index('A Button'))
            self.assertTrue(text.endswith('{cmd:7F0E'+target+'}\n{cmd:7F01}'))
            self.assertNotIn('{cmd:7F5904}', text)

    def test_write_failure_and_mid_operation_removal_keep_different_native_meanings(self):
        for base in BASES:
            write, removed = f'{base+0x13:04X}', f'{base+0x18:04X}'
            if write in self.text:
                self.assertIn('Unable to write', self.visible[write])
                self.assertEqual(self.text[write].count('{cmd:7F05C35F00}'), 2)
                self.assertNotIn('Unable to read', self.visible[write])
                self.assertTrue(self.text[write].endswith('{cmd:7F00}'))
            text, visible = self.text[removed], self.visible[removed]
            for phrase in ('during an operation', 'title screen', 'insert it into your controller'):
                self.assertIn(phrase, visible)
            self.assertTrue(text.endswith('{cmd:7F00}'))
        self.assertIn('precious record were lost', self.visible['1440'])
        self.assertIn("how far we'd got", self.visible['1468'])
        self.assertIn('{cmd:7F1C}', self.text['1490'])
        self.assertTrue(self.text['14E0'].startswith('{cmd:7F09000002}Hey!{cmd:7F0312}'))
        for visible in self.visible.values():
            for absent in ('Memory Card', 'Rumble', 'GameCube', 'Slot A', 'Slot B'):
                self.assertNotIn(absent, visible)


if __name__ == '__main__':
    unittest.main()
