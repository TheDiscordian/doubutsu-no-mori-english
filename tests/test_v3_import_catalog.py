"""Synthetic V3 inventory checks; no game assets are required or installed."""

import copy
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import sha256
from v3_import_catalog import checked, fixed_records, item_rows, villager_rows

TABLES = {'CHAR_MAP': [chr(i) for i in range(256)], 'CONT_SIZES': [2] * 123}


class V3ImportCatalogTests(unittest.TestCase):
    def npc_inputs(self):
        names = b'Example ' * 236
        defaults = struct.pack('>HHbB', 0x2405, 1820, 7, 0) * 238
        looks, growth = bytearray(238), bytearray(238)
        for index in range(216, 236):
            looks[index] = (index - 216) % 6
            growth[index] = 0 if index in (232, 235) else 2
        return names, defaults, looks, growth, copy.deepcopy(TABLES)

    def test_only_twenty_additional_villagers_excluding_test_slots(self):
        rows = villager_rows(*self.npc_inputs())
        self.assertEqual(len(rows), 20)
        self.assertEqual(rows[0]['donor_actor_id'], 'E0D8')
        self.assertEqual(rows[-1]['donor_actor_id'], 'E0EB')
        self.assertEqual(sum(r['donor_role'] == 'islander' for r in rows), 18)
        self.assertTrue(all(not r['selectable'] and r['target_actor_id'] is None for r in rows))
        self.assertEqual(rows[0]['donor_clothing_id'], '2405')
        self.assertEqual(rows[0]['donor_catchphrase_index'], 1820)

    def test_villager_bounds_and_unrecognised_metadata_fail(self):
        for field in range(4):
            args = list(self.npc_inputs())
            args[field] = args[field][:-1]
            with self.assertRaises(ValueError):
                villager_rows(*args)
        for field, bad in ((2, 6), (3, 3)):
            args = list(self.npc_inputs())
            args[field][216] = bad
            with self.assertRaisesRegex(ValueError, 'personality or growth'):
                villager_rows(*args)
        args = list(self.npc_inputs())
        args[1] = bytearray(args[1])
        args[1][216 * 6 + 4] = 32
        with self.assertRaisesRegex(ValueError, 'clothing or umbrella'):
            villager_rows(*args)

    def test_furniture_rotations_are_one_identity_per_four_ids(self):
        rows = item_rows(b'Test chair'.ljust(16) * 2, TABLES, base=0x3000, furniture=True)
        self.assertEqual([r['donor_item_id'] for r in rows], ['3000', '3004'])
        self.assertEqual(rows[1]['rotation_ids'], ['3004', '3005', '3006', '3007'])
        self.assertEqual(rows[1]['id'], 'GAFE01-r0/item/3004')
        self.assertTrue(all(r['native_identity'] == 'unreviewed' and not r['selectable'] for r in rows))

    def test_ordinary_items_do_not_share_furniture_id_space(self):
        rows = item_rows(b'Test item'.ljust(16) * 2, TABLES, base=0x2300, furniture=False)
        self.assertEqual([r['donor_item_id'] for r in rows], ['2300', '2301'])
        self.assertEqual(rows[0]['rotation_ids'], [])
        self.assertEqual(rows[0]['name_sha256'], sha256(b'Test item'.ljust(16)))

    def test_reject_invalid_groups_partial_records_and_id_overflow(self):
        for base, furniture, size in ((0x2000, True, 16), (0x3000, False, 16),
                                     (0x2300, False, 17), (0x2300, False, 257 * 16),
                                     (0x1000, True, 1025 * 16)):
            with self.assertRaises(ValueError):
                item_rows(b' ' * size, TABLES, base=base, furniture=furniture)
        with self.assertRaises(ValueError):
            fixed_records(b'', 0)

    def test_resource_identity_requires_both_size_and_digest(self):
        self.assertEqual(checked(b'example', 7, sha256(b'example'), 'Fixture'), b'example')
        for size, digest in ((6, sha256(b'example')), (7, '0' * 64)):
            with self.assertRaisesRegex(ValueError, 'Fixture'):
                checked(b'example', size, digest, 'Fixture')


if __name__ == '__main__':
    unittest.main()
