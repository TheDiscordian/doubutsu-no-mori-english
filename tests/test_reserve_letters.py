"""Reserve-letter edits retain all other text, commands, runtime, and saves."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups
from textbanks import banks
import reserve_letters as r

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/reserve-letters-pilot'


@unittest.skipUnless(ROM.is_file(), 'Local retail source required')
class ReserveLetterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()

    def test_complete_reference_wording_and_original_blank_lines(self):
        self.assertEqual(r.values(self.native), {'super': b'Extra\xcd',
                         'mail': b'Extra'+b'\xcd'*6, 'ps': b'Extra'})

    @unittest.skipUnless((r.BASE/'build.json').is_file(), 'Complete predecessor required')
    def test_exact_fifteen_parts_and_unchanged_other_records(self):
        base, previous = r.baseline()
        updates, evidence = r.plan(self.native, base, previous)
        self.assertEqual(evidence['changed_records'], 15)
        self.assertEqual(evidence['runtime_changes'], 0)
        self.assertEqual(evidence['saved_layout_changes'], 0)
        self.assertEqual(len(updates), 6)
        old_files = by_vrom(base)
        for bank in banks(self.native):
            if bank.name not in r.LINES:
                continue
            old = replace(bank, data=old_files[bank.data_vrom].extract(base),
                          table=old_files[bank.table_vrom].extract(base)).entries()
            new = replace(bank, data=updates[bank.data_vrom], table=updates[bank.table_vrom]).entries()
            self.assertEqual(len(new), 544)
            for number, data in enumerate(new):
                self.assertEqual(data, b'Extra'+b'\xcd'*r.LINES[bank.name]
                                 if number in r.TEMPLATES else old[number])
            if bank.name == 'mail':
                self.assertEqual(len(updates[bank.data_vrom]), len(bank.data)+16)
                self.assertEqual(updates[bank.data_vrom][-15:], bytes(15))
                self.assertEqual(new[-1], old[-1])
            offset = 0
            for data in new:
                offset += len(data)
                self.assertLessEqual((offset+7)&~7, len(updates[bank.data_vrom]))

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Installed reserve-letter build required')
    def test_complete_cartridge_patch_and_accounting(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        base, previous = r.verify_installation(built, self.native, report)
        self.assertTrue(set(report['reserve_letters']['files']) <= set(report['replacement_files']))
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(base)
        allowed = {int(v, 16) for v in report['reserve_letters']['files']} | {0x19D40}
        self.assertEqual(set(files), set(old))
        for v in files:
            self.assertEqual(files[v].index, old[v].index)
            if v not in allowed:
                self.assertEqual(files[v].extract(built), old[v].extract(base), hex(v))
        from translation_progress import measure
        from mail_omissions import PARTS
        ledger = measure(self.native, built, report)
        self.assertEqual(ledger.summary()['total_source_characters'], 751284)
        self.assertEqual(ledger.summary()['replaced_source_characters'], 750240)
        for name in r.LINES:
            for number in r.TEMPLATES:
                self.assertTrue(ledger.rows[f'{name}:{number:04X}']['replacements'])
        for identity in PARTS:
            self.assertTrue(ledger.rows[identity]['replacements'][0]['intentional_omission'])
        bad = copy.deepcopy(report)
        bad['reserve_letters']['parts'][0]['newlines'] += 1
        with self.assertRaisesRegex(ValueError, 'report'):
            r.verify_installation(built, self.native, bad)


if __name__ == '__main__':
    unittest.main()
