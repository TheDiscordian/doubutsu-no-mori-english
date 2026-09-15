"""Actual construction metadata and combined native shop/scoring table generation."""
import struct
import unittest

import test_v3_furniture_art as static_tests
from test_v3_shops import lists
from aflib import by_vrom, sha256
from v3_construction_items import metadata
import v3_feng_shui as feng
import v3_hra as hra
import v3_shops as shops

ROOT = static_tests.ROOT


@unittest.skipUnless((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').exists(),
                     'Supplied local donor required')
class ConstructionItemsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        if sha256(cls.base) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
            raise ValueError('Changed stable baseline')
        cls.data, cls.rows = metadata(cls.rel, cls.symbols)
        cls.original_imports = [{'item_id': '3224', 'runtime_index': 1161},
                                {'item_id': '32B8', 'runtime_index': 1198}]
        cls.speed_bag = {'item_id': '3350', 'runtime_index': 1236}

    def test_complete_names_prices_properties_and_stock_membership(self):
        self.assertEqual(len(self.data), 7 * 32)
        expected = (
            (0x31F4, 1149, 850, 'wet roadway sign', 1, '40050200', '0300'),
            (0x31F8, 1150, 830, 'detour sign', 1, '40050200', '0300'),
            (0x31FC, 1151, 850, 'men at work sign', 2, '40050400', '0300'),
            (0x320C, 1155, 850, 'flagman sign', 1, '40050200', '0300'),
            (0x3214, 1157, 1050, 'jersey barrier', 1, '40050200', '0000'),
            (0x3218, 1158, 870, 'speed sign', 1, '40050200', '0000'),
            (0x322C, 1163, 900, 'saw horse', 2, '40050400', '0000'),
        )
        for offset, (row, values) in enumerate(zip(self.rows, expected, strict=True)):
            item, index, price, name, group, hra_hex, feng_hex = values
            record = self.data[offset * 32:(offset + 1) * 32]
            self.assertEqual(struct.unpack_from('>HHHBB', record), (index, item, price, 0, 1))
            self.assertEqual(record[8:24], name.encode().ljust(16, b' '))
            self.assertEqual(record[24:], bytes(8))
            self.assertEqual(row['record_sha256'], sha256(record))
            self.assertEqual(row['stock_group'], group)
            self.assertEqual(row['donor_list'], 'ftr_list' + 'ABC'[group])
            self.assertEqual(row['native_hra_hex'], hra_hex)
            self.assertEqual(row['feng_hex'], feng_hex)
            self.assertFalse(row['selectable'])
            self.assertFalse(row['runtime_installed'])

    def test_combined_scoring_retains_all_other_rows_and_native_construction_capacity(self):
        old_hra, _ = hra.table(self.base, self.rel, self.symbols, self.original_imports, speed_bag=True)
        old_feng, _ = feng.table(self.base, self.rel, self.symbols,
                                self.original_imports + [self.speed_bag])
        new_hra, hra_rows = hra.table(self.base, self.rel, self.symbols,
                                      self.original_imports + self.rows, speed_bag=True)
        new_feng, feng_rows = feng.table(self.base, self.rel, self.symbols,
                                         self.original_imports + [self.speed_bag] + self.rows)
        self.assertEqual(len(hra_rows), 10)
        self.assertEqual(len(feng_rows), 10)
        expected_hra, expected_feng = bytearray(old_hra), bytearray(old_feng)
        for row in self.rows:
            index = row['runtime_index']
            expected_hra[index * 4:index * 4 + 4] = bytes.fromhex(row['native_hra_hex'])
            expected_feng[index * 2:index * 2 + 2] = bytes.fromhex(row['feng_hex'])
        self.assertEqual(new_hra, expected_hra)
        self.assertEqual(new_feng, expected_feng)
        self.assertEqual(sum(old_hra[i * 4] >> 2 == 16 for i in range(hra.COUNT)), 21)
        self.assertEqual(sum(new_hra[i * 4] >> 2 == 16 for i in range(hra.COUNT)), 28)

    def test_combined_shop_lists_preserve_all_native_entries_and_ignore_selection_order(self):
        original = by_vrom(self.base)[shops.VROM].extract(self.base)
        native_lists = lists(original, shops.TABLE)
        selection = self.original_imports + [self.speed_bag] + self.rows
        data, table, rows = shops.goods(self.base, self.rel, self.symbols, selection)
        expected = [None if row is None else row.copy() for row in native_lists]
        # The converter appends in canonical item order within each ordinary list.
        for row in rows:
            expected[row['group']].append(int(row['item_id'], 16))
        self.assertEqual(lists(data, table), expected)
        self.assertEqual(len(rows), 10)
        self.assertEqual(table % 4, 0)
        self.assertEqual(len(data) % 16, 0)
        self.assertEqual(shops.goods(self.base, self.rel, self.symbols, selection[::-1]),
                         (data, table, rows))

    def test_unknown_or_duplicate_identity_and_changed_donor_rejected(self):
        for rows in (self.rows + self.rows[:1],
                     [dict(self.rows[0], item_id='31F0')],
                     [dict(self.rows[0], runtime_index=1161)]):
            for build in (hra.table, feng.table, shops.goods):
                with self.subTest(build=build.__module__), self.assertRaises(ValueError):
                    build(self.base, self.rel, self.symbols, self.original_imports + rows)
        with self.assertRaises(ValueError):
            metadata(self.rel[:-1] + bytes((self.rel[-1] ^ 1,)), self.symbols)


if __name__ == '__main__':
    unittest.main()
