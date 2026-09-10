"""The classic adapter retains every existing cartridge resource and byte of mail."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups
import classic_letters as c

BUILD = ROOT/'build/classic-letters-pilot'
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


@unittest.skipUnless((BUILD/'build.json').is_file() and ROM.is_file(), 'Local installed classic cartridge required')
class ClassicLetterInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())

    def test_complete_native_reference_parts_and_masks(self):
        catalog = by_vrom(self.built)[0x030A0000].extract(self.built)
        rows = c.reviewed_templates(self.native, catalog)
        self.assertEqual(len(rows), 54)
        self.assertEqual({row['id'] for row in rows},
                         {f'{name}:{n:04X}' for name in ('super', 'mail', 'ps') for n in c.IDS})
        self.assertEqual(rows, self.report['classic_letters']['parts'])

    def test_complete_cartridge_and_patch_retention(self):
        base, previous = c.verify_installation(self.built, self.native, self.report)
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), self.built)
        old, files = by_vrom(base), by_vrom(self.built)
        for vrom in files:
            if vrom not in (*c.CHANGED, 0x19D40):
                self.assertEqual(files[vrom].extract(self.built), old[vrom].extract(base), f'{vrom:08X}')
        # A missing newly replaced bank must fail a later build, never revert
        # silently to Japanese while retaining a translation claim in metadata.
        broken = deepcopy(previous)
        broken['replacement_files'].remove('00D07000')
        updates = {v: files[v].extract(self.built) for v in c.CHANGED}
        with self.assertRaisesRegex(ValueError, 'loses an existing resource'):
            c.assemble(self.native, base, broken, updates)
        broken = deepcopy(self.report)
        broken['classic_letters']['font_hook_offset'] += 4
        with self.assertRaisesRegex(ValueError, 'report'):
            c.verify_installation(self.built, self.native, broken)

    def test_combined_counter_requires_the_installed_complete_adapter(self):
        from translation_progress import measure
        ledger = measure(self.native, self.built, self.report)
        self.assertEqual(ledger.summary()['total_source_characters'], 751307)
        self.assertEqual(ledger.summary()['replaced_source_characters'], 751262)
        remaining = {identity for identity, row in ledger.rows.items()
                     if row['source_characters'] and not row['replacements']}
        self.assertEqual(remaining, {'npc_names:00DA', 'npc_names:00DB', 'item_10:0ECC'})
        for name in ('super', 'mail', 'ps'):
            for number in c.IDS:
                self.assertTrue(any(r['route'] == 'classic_letters'
                                    for r in ledger.rows[f'{name}:{number:04X}']['replacements']))


if __name__ == '__main__':
    unittest.main()
