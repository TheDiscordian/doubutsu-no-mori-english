"""Clock and town errors keep native hardware, commands, and branch meanings."""

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

PATH = ROOT/'translations/n64-startup-errors.json'


class StartupErrorSelectionTests(unittest.TestCase):
    def test_both_complete_drafts_are_available_without_optional_runtime(self):
        drafts = load_drafts([PATH])
        self.assertEqual({r['id'] for r in drafts}, {'message:09CC', 'message:09D1'})
        self.assertEqual(select_drafts(drafts), (drafts, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local input')
class StartupErrorRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.drafts = load_drafts([PATH])
        cls.text = {r['id'][8:]: r['translation'] for r in cls.drafts}

    def test_complete_native_hashes_and_commands_with_one_exact_colour_change(self):
        commands = lambda raw: [t.data.hex().upper() for t in tokenize(raw, self.info) if t.kind == 'cmd']
        for row in self.drafts:
            source = self.sources[int(row['id'][8:], 16)]
            output = encode(row['translation'], self.info)
            expected = [c.replace('7F50E11ED70C', '7F50E11ED713') for c in commands(source)]
            self.assertEqual(row['source_sha256'], sha256(source))
            self.assertEqual(commands(output), expected)
            self.assertEqual(row['status'], 'draft')
            validate_entry(source, output, self.info, 'message', row['control_policy'])
            self.assertLessEqual(expanded_bound(output, self.info), 1024)
        self.assertIn('{cmd:7F50E11ED713}Instruction Booklet', self.text['09CC'])

    def test_complete_original_english_lines_fit_without_reflowing_references(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        for id, text in self.text.items():
            self.assertEqual(layout_issues(encode(text, self.info), self.info, advances), [], id)

    def test_cartridge_clock_advice_retains_both_native_answers_and_successors(self):
        text = self.text['09CC']; visible = plain(text)
        for phrase in ('clock built into this cartridge', 'seems to have stopped',
                       'Instruction Booklet', 'without using the clock',
                       'wait a bit', 'try again'):
            self.assertIn(phrase, visible)
        self.assertIn('{cmd:7F1600E700E8}', text)
        self.assertTrue(text.endswith('{cmd:7F04}{cmd:7F0D}{cmd:7F0F09CD}{cmd:7F1009CF}{cmd:7F19}\n{cmd:7F01}'))
        self.assertNotIn('01DD', text)

    def test_corrupted_town_notice_keeps_action_and_normal_end_without_new_erasure(self):
        text = self.text['09D1']; visible = plain(text)
        self.assertIn('town data has been corrupted', visible)
        self.assertIn('start again from the beginning', visible)
        self.assertIn("I'm very sorry", visible)
        self.assertTrue(text.endswith('{cmd:7F09090001}\n{cmd:7F00}'))
        for absent in ('erase', '09D7', '{cmd:7F16', '{cmd:7F28}'):
            self.assertNotIn(absent, text)
        for text in self.text.values():
            for absent in ('GameCube', 'Memory Card', 'Slot A', 'Slot B'):
                self.assertNotIn(absent, text)


if __name__ == '__main__':
    unittest.main()
