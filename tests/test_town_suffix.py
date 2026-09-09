"""Complete English suffix omission, unchanged native readers, and cartridge retention."""
from dataclasses import replace
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, apply_ups
from build import apply_translations
from textbanks import banks
import town_suffix as t

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/town-suffix-pilot'
PREVIOUS = ROOT/'build/world-names-pilot'


@unittest.skipUnless(ROM.is_file() and (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').is_file(),
                     'Supplied N64 and GameCube sources stay local')
class TownSuffixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.bank = next(b for b in banks(cls.native) if b.name == 'string')

    def test_complete_empty_reference_and_conflict_rejection(self):
        evidence = t.references(self.native)
        self.assertEqual(evidence['encoded_sha256'], sha256(b''))
        self.assertEqual(evidence['saved_name_bytes'], 6)
        edits = t.with_candidate(self.native, [])
        self.assertEqual(edits[0]['id'], t.ID)
        self.assertEqual(edits[0]['translation'], '')
        self.assertEqual(t.with_candidate(self.native, edits), edits)
        for bad in ({**edits[0], 'translation': 'village'},
                    {**edits[0], 'source_sha256': '0'*64}):
            with self.assertRaisesRegex(ValueError, 'Conflicting'):
                t.with_candidate(self.native, [bad])

    def test_independent_import_retains_every_other_entry_and_code(self):
        replacements = {}
        count, relocated = apply_translations(self.native, replacements, None, english_town_suffix=True)
        self.assertEqual((count, relocated), (1, {}))
        self.assertEqual(set(replacements), {self.bank.data_vrom, self.bank.table_vrom})
        current = replace(self.bank, data=replacements[self.bank.data_vrom],
                          table=replacements[self.bank.table_vrom])
        expected = self.bank.entries()
        expected[0x1E4] = b''
        self.assertEqual(current.entries(), expected)
        self.assertEqual(len(current.data), len(self.bank.data))
        self.assertEqual(len(current.table), len(self.bank.table))
        # Equal neighbouring cumulative ends represent an empty non-leading
        # entry, not the zero sentinel that terminates the whole text bank.
        before, end = struct.unpack_from('>2I', current.table, 0x1E3*4)
        self.assertGreater(before, 0)
        self.assertEqual(before, end)
        t.planned(self.native, replacements)
        code = bytearray(by_vrom(self.native)[CODE_VROM].extract(self.native))
        code[t.START-CODE_RAM] ^= 1
        with self.assertRaisesRegex(ValueError, 'consumer was modified'):
            t.planned(self.native, {**replacements, CODE_VROM: bytes(code)})
        with self.assertRaisesRegex(ValueError, 'omission is not installed'):
            t.planned(self.native, {})

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete local town-suffix build required')
    def test_complete_cartridge_changes_only_suffix_banks_and_retains_patch(self):
        report = json.loads((BUILD/'build.json').read_text())
        old_report = json.loads((PREVIOUS/'build.json').read_text())
        built, previous = [(p/'animal-forest-halfwidth.z64').read_bytes() for p in (BUILD, PREVIOUS)]
        t.verify_installation(built, self.native, report)
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        a, b = by_vrom(previous), by_vrom(built)
        self.assertEqual(a.keys(), b.keys())
        moved = {int(k, 16): int(v, 16) for k, v in report['vrom_relocations'].items()}
        self.assertEqual({v for v in a if a[v].extract(previous) != b[v].extract(built)},
                         {moved[self.bank.data_vrom], self.bank.table_vrom})
        entries = [replace(self.bank, data=files[moved[self.bank.data_vrom]].extract(rom),
                           table=files[self.bank.table_vrom].extract(rom)).entries()
                   for files, rom in ((a, previous), (b, built))]
        self.assertEqual({i for i, pair in enumerate(zip(*entries)) if pair[0] != pair[1]}, {0x1E4})
        self.assertEqual(report['translation_edits'], old_report['translation_edits']+1)
        for key in ('runtime_module', 'extended_font', 'extended_items', 'display_names', 'catchphrases',
                    'npc_mail_loader', 'noticeboard', 'inventory_english', 'catalogue_names'):
            self.assertEqual(report[key], old_report[key], key)
        with self.assertRaisesRegex(ValueError, 'approval'):
            t.verify_installation(built, self.native, {**report, 'town_suffix': {}})

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete local town-suffix build required')
    def test_counter_credits_only_the_verified_grammatical_omission(self):
        from translation_progress import measure
        report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(self.native, (BUILD/'animal-forest-halfwidth.z64').read_bytes(), report)
        row = ledger.rows[t.ID]
        self.assertEqual(row['source_characters'], 2)
        self.assertEqual(row['replacements'], [{'route': 'town_suffix', 'sha256': t.EMPTY_SHA,
                                               'intentional_omission': True}])


if __name__ == '__main__':
    unittest.main()
