"""Complete native test prose without changing actions or discarding samples."""

from collections import Counter
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

PATH = ROOT/'translations/n64-engine-diagnostics.json'
IDS = set('0001 0002 0003 0006 0007 0008 0009 000A 000B 000C 000D 000E 0012 1354 1355'.split())
SAMPLES = set('0004 0005 000F 0010 0011'.split())


class EngineDiagnosticDraftTests(unittest.TestCase):
    def setUp(self):
        self.rows = load_drafts([PATH])
        self.by_id = {r['id'][8:]: r for r in self.rows}

    def test_complete_unique_batch_and_no_runtime_requirement(self):
        self.assertEqual(len(self.rows), 15)
        self.assertEqual(self.by_id.keys(), IDS)
        self.assertFalse(self.by_id.keys() & SAMPLES)
        self.assertEqual(Counter(r['diagnostic_kind'] for r in self.rows),
                         {'engine_test': 11, 'personality_sample': 2, 'shopping_label': 2})
        for resident in (False, True):
            self.assertEqual(select_drafts(self.rows, resident_runtime=resident), (self.rows, []))
        for row in self.rows:
            self.assertEqual(row['status'], 'draft')
            self.assertNotIn('control_policy', row)
            self.assertNotIn('runtime_requirements', row)

    def test_full_native_meanings_literals_and_unrenumbered_shopping_labels(self):
        wanted = {'0001': ['Test message 1', 'String'],
                  '0002': ["player's state", 'unlucky', 'continuation smoother',
                           'after opening a choice window', '%SFN%'],
                  '0003': ['message continuation', 'next message'],
                  '0007': ['people they can trust', 'more than themselves'],
                  '0008': ['values humour', 'always likes', 'lively'],
                  '0009': ['sound system', 'mood the message uses', 'Which'],
                  '0012': ['Which will you choose?']}
        for short, fragments in wanted.items():
            visible = plain(self.by_id[short]['translation'])
            for fragment in fragments:
                self.assertIn(fragment, visible, short)
        for short, number in (('1354', 4948), ('1355', 4949)):
            row = self.by_id[short]
            self.assertEqual(row['printed_number'], number)
            self.assertEqual(row['translation'], f'Normal girl\nShopping, part 1\n{number}\n{{cmd:7F00}}')
        voice = self.by_id['0006']['translation']
        self.assertEqual(voice.count('Reverse the voice.'), 2)
        self.assertIn('Standard voice.', voice)
        self.assertIn('Restore the voice.', voice)


@unittest.skipUnless(ROM_PATH.is_file(), 'Supplied retail ROM stays local')
class EngineDiagnosticRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.entries = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.rows = load_drafts([PATH]); cls.by_id = {r['id'][8:]: r for r in cls.rows}
        _, report = make_halfwidth(cls.rom)
        cls.advances = {int(k, 16): v for k, v in report['advance_by_glyph'].items()}

    def commands(self, data):
        return [t.data for t in tokenize(data, self.info) if t.kind == 'cmd']

    def test_every_source_command_page_ending_roundtrip_bound_and_layout(self):
        for row in self.rows:
            short = row['id'][8:]
            native = self.entries[int(short, 16)]
            text = row['translation']; candidate = encode(text, self.info)
            self.assertEqual(sha256(native), row['source_sha256'], short)
            self.assertEqual(decode(candidate, self.info), text, short)
            self.assertEqual(self.commands(native), self.commands(candidate), short)
            self.assertEqual(candidate[-2:], native[-2:], short)
            before = decode(native, self.info).split('{cmd:7F02}')
            after = text.split('{cmd:7F02}')
            self.assertEqual(len(before), len(after), short)
            for a, b in zip(before, after):
                self.assertEqual(self.commands(encode(a, self.info)), self.commands(encode(b, self.info)), short)
            for resident in (False, True):
                validate_entry(native, candidate, self.info, 'message', resident_runtime=resident)
                self.assertEqual(layout_issues(candidate, self.info, self.advances,
                                              resident_runtime=resident), [], short)
            self.assertLessEqual(expanded_bound(candidate, self.info), 1024, short)

    def test_exact_mood_actions_menus_and_continuations(self):
        for number, mood, code in zip(range(0xA, 0xF),
                                     ('normal', 'angry', 'sad', 'happy', 'sleepy'), range(0x4B, 0x50)):
            text = self.by_id[f'{number:04X}']['translation']
            self.assertIn(f'Set the mood to {mood}.', text)
            self.assertEqual(self.commands(encode(text, self.info)),
                             [bytes([0x7F, code]), bytes.fromhex('7F0E0003'), bytes.fromhex('7F01')])
        for short, expected in (
                ('0009', ('7F1800D400D500D600B3', '7F04', '7F0D', '7F0F000A',
                          '7F10000B', '7F11000C', '7F120012', '7F19', '7F01')),
                ('0012', ('7F1700D700D800B3', '7F04', '7F0D', '7F0F000D',
                          '7F10000E', '7F110009', '7F19', '7F01')),
                ('0006', ('7F04', '7F5D', '7F04', '7F5C', '7F04', '7F5D', '7F00'))):
            self.assertEqual(self.commands(encode(self.by_id[short]['translation'], self.info)),
                             list(map(bytes.fromhex, expected)))
        self.assertIn('{cmd:7F0FFFFF}{cmd:7F100004}', self.by_id['0002']['translation'])
        self.assertIn('{cmd:7F0E0002}', self.by_id['0003']['translation'])

    def test_other_complete_diagnostic_families_and_glyph_samples_unchanged(self):
        from native_diagnostics import native_definition
        recognised = [native_definition(data, self.info) for data in self.entries]
        self.assertEqual(sum(item is not None for item in recognised), 99)
        inventory = {r['id'][8:]: r for r in map(json.loads,
                     (ROOT/'build/inventory/message.jsonl').read_text().splitlines())}
        for short in SAMPLES:
            self.assertEqual(sha256(self.entries[int(short, 16)]), inventory[short]['source_sha256'])
            self.assertTrue(any('\u3041' <= c <= '\u30FF' for c in inventory[short]['source']))


if __name__ == '__main__':
    unittest.main()
