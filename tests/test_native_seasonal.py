"""Native seasonal conversations keep complete controls and branch meanings."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from font import make_halfwidth
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry, layout_issues
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains a local test input')
class NativeSeasonalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.drafts = json.loads((ROOT/'translations/n64-seasonal-conversations.json').read_text())

    def test_complete_native_commands_fields_pages_and_source_hashes(self):
        expected = set('1E09 1E17 1E2A 1E2B 1E3E 1E4E 1EAF 1EB7 1ECB 1EE9 1EEA '
                       '1EF7 1EF8 1EF9 1F55 1F6B 1F76 1F77 1F78 2600 285A'.split())
        self.assertEqual({r['id'][8:] for r in self.drafts}, expected)
        self.assertEqual(len(self.drafts), len(expected))
        for draft in self.drafts:
            with self.subTest(id=draft['id']):
                original = self.sources[int(draft['id'][8:], 16)]
                output = encode(draft['translation'], self.info)
                self.assertEqual(draft['source_sha256'], sha256(original))
                self.assertEqual(draft['status'], 'draft')
                commands = lambda data: [t.data for t in tokenize(data, self.info) if t.kind == 'cmd']
                self.assertEqual(commands(output), commands(original))
                validate_entry(original, output, self.info, 'message', resident_runtime=True)

    def test_original_draft_layout_uses_approved_metrics(self):
        _, report = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}
        # Existing Japanese town names can still make 1F76's last line wider;
        # keep that conservative warning visible instead of changing the font.
        for draft in self.drafts:
            issues = layout_issues(encode(draft['translation'], self.info), self.info,
                                   advances, resident_runtime=True)
            if draft['id'] == 'message:1F76':
                self.assertTrue(all('width_' in issue for issue in issues))
            else:
                self.assertEqual(issues, [], draft['id'])

    def test_spring_question_and_responses_keep_native_choice_order(self):
        by_id = {r['id'][8:]: encode(r['translation'], self.info) for r in self.drafts}
        question = by_id['1F6B']
        self.assertIn(bytes.fromhex('7F16011E0128'), question)
        self.assertIn(bytes.fromhex('7F0F1F777F101F787F19'), question)
        self.assertNotIn(bytes.fromhex('7F16011E006C'), question)
        self.assertIn(bytes.fromhex('7F0C050003'), by_id['1F77'])
        self.assertIn(bytes.fromhex('7F0C050067'), by_id['1F78'])
        self.assertIn(b'bug catching again', by_id['1F77'])
        self.assertIn(b'to the test', by_id['1F78'])
        self.assertIn(bytes.fromhex('7F26'), by_id['1EB7'])
        self.assertNotIn(bytes.fromhex('7F1A'), by_id['1EB7'])


if __name__ == '__main__':
    unittest.main()
