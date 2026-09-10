"""Retained-name translation is data-only, complete, and source-bound."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups, sha256
from textbanks import banks
import unused_names as u

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/unused-names-pilot'


@unittest.skipUnless(ROM.is_file(), 'Local retail source required')
class UnusedNamesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()

    def test_all_two_hundred_complete_source_bound_spellings(self):
        rows = u.edits(self.native)
        self.assertEqual(len(rows), 200)
        self.assertEqual(tuple(row['id'] for row in rows), u.IDS)
        self.assertEqual(max(len(row['translation']) for row in rows), 13)
        self.assertEqual(u.verify_reference(self.native), u.SOURCE_SHA)
        values = {row['id']: row['translation'] for row in rows}
        self.assertEqual(values['string:009C'], 'Anman')
        self.assertEqual(values['string:0108'], 'Bouquet')
        self.assertEqual(values['string:010C'], 'Chima Chogori')
        self.assertEqual(values['string:0163'], 'Witchy')
        # A retained name matching a live Japanese spelling is not silently
        # substituted with a different localized live character identity.
        self.assertNotEqual(values['string:0108'], 'Rosie')

    def test_changed_or_partial_manifest_cannot_authorize_extra_capacity(self):
        data = u.MANIFEST.read_bytes()
        for rows in (u.edits(self.native)[:-1], u.edits(self.native)+[u.edits(self.native)[0]]):
            with self.assertRaisesRegex(ValueError, 'manifest'):
                u.edits(self.native, json.dumps(rows).encode())
        for old, new in ((b'Anman', b'A'*65), (b'Anman', b'{cmd:7F01}'),
                         (b'string:009C', b'string:0001'), (b'"exact"', b'"presentation"')):
            with self.assertRaisesRegex(ValueError, 'manifest'):
                u.edits(self.native, data.replace(old, new, 1))

    @unittest.skipUnless((u.BASE/'build.json').is_file(), 'Accent predecessor required')
    def test_bank_roundtrip_preserves_every_other_string_and_loader(self):
        base, _ = u.baseline()
        updates, evidence = u.plan(self.native, base)
        self.assertEqual(set(updates), {u.DATA_VROM, u.TABLE_VROM})
        self.assertEqual(evidence['runtime_changes'], 0)
        self.assertEqual(evidence['saved_layout_changes'], 0)
        original = next(b for b in banks(self.native) if b.name == 'string')
        previous = by_vrom(base)
        old = replace(original, data=previous[u.DATA_VROM].extract(base),
                      table=previous[u.TABLE_VROM].extract(base)).entries()
        new = replace(original, data=updates[u.DATA_VROM], table=updates[u.TABLE_VROM]).entries()
        self.assertEqual(len(new), 1562)
        values = [row['translation'].encode() for row in u.edits(self.native)]
        for i, value in enumerate(new):
            self.assertEqual(value, values[i-u.FIRST] if u.FIRST <= i < u.END else old[i])

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Installed retained-name build required')
    def test_cartridge_patch_retention_and_combined_accounting(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        base, previous = u.verify_installation(built, self.native, report)
        self.assertEqual(sha256(base), u.BASE_SHA)
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(base)
        self.assertEqual(set(files), set(old))
        for vrom in files:
            self.assertEqual(files[vrom].index, old[vrom].index)
            if vrom not in (0x19D40, u.DATA_VROM, u.TABLE_VROM):
                self.assertEqual(files[vrom].extract(built), old[vrom].extract(base), hex(vrom))
        from translation_progress import measure
        ledger = measure(self.native, built, report)
        summary = ledger.summary()
        self.assertEqual(summary['total_source_characters'], 751284)
        self.assertEqual(summary['replaced_source_characters'],
                         748567+report['unused_names']['source_characters'])
        for identity in u.IDS:
            self.assertTrue(ledger.rows[identity]['replacements'])
        bad = copy.deepcopy(report)
        bad['unused_names']['runtime_changes'] = 1
        with self.assertRaisesRegex(ValueError, 'report'):
            u.verify_installation(built, self.native, bad)
        wrong = bytearray(built)
        wrong[files[0x02A00000].pstart+40] ^= 1
        with self.assertRaisesRegex(ValueError, 'two-file'):
            u.verify_installation(bytes(wrong), self.native, report)


if __name__ == '__main__':
    unittest.main()
