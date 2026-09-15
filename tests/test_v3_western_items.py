"""Preserve the Western batch's complete metadata and event-reward distinctions."""
import struct
import unittest

from tests.test_v3_furniture_art import ROOT
from aflib import sha256
from v3_western_items import identity_evidence, metadata


@unittest.skipUnless((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').exists(),
                     'Supplied local donor required')
class WesternItemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.records, cls.rows = metadata(cls.rel, cls.symbols)

    def test_actual_complete_records_and_non_native_identities(self):
        self.assertEqual(len(self.records), 224)
        self.assertEqual(sha256(self.records), 'a2b5d07acd0580c431ff7c7b6ccb753a8bf50442375ebae8af16695246f5a2a6')
        expected = (
            (0x32B0, 1196, 520, 'tumbleweed', 'ftr_listC', 259),
            (0x32B4, 1197, 1020, 'cow skull', 'ftr_listA', 255),
            (0x32BC, 1199, 2180, 'saddle fence', 'ftr_listEvent', 257),
            (0x32C0, 1200, 880, 'western fence', 'ftr_listA', 263),
            (0x3328, 1226, 890, 'desert cactus', 'ftr_listB', 256),
            (0x3330, 1228, 1230, 'wagon wheel', 'ftr_listB', 260),
            (0x3334, 1229, 2700, 'well', 'ftr_listEvent', 262),
        )
        for slot, (row, values) in enumerate(zip(self.rows, expected, strict=True)):
            item, index, price, name, route, position = values
            record = self.records[slot * 32:(slot + 1) * 32]
            self.assertEqual(struct.unpack_from('>HHHBB', record), (index, item, price, 0, 1))
            self.assertEqual(record[8:24], name.encode().ljust(16, b' '))
            self.assertEqual(record[24:], bytes(8))
            self.assertEqual(row['record_sha256'], sha256(record))
            self.assertEqual((row['donor_list'], row['donor_catalogue_position'], row['preview_mode']),
                             (route, position, 0))
            self.assertEqual(row['ordinary_stock'], slot not in (2, 6))
            if slot in (2, 6):
                self.assertIsNone(row['stock_group'])
            self.assertFalse(row['runtime_installed'])
            self.assertFalse(row['selectable'])
        evidence = identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx')
        self.assertEqual([r['sheet_row'] for r in evidence], [2585, 2586, 2588, 2589, 2615, 2617, 2618])
        self.assertTrue(all(r['native_id_name_and_artwork_absent'] for r in evidence))

    def test_scoring_keeps_surface_colour_and_true_acquisition(self):
        self.assertEqual([r['native_hra_hex'] for r in self.rows],
                         ['dc050400', 'dc050100', 'dc050600', 'dc050000',
                          'dc050200', 'dc050200', 'dc050600'])
        self.assertEqual([r['birth_category'] for r in self.rows], [2, 0, 3, 0, 1, 1, 3])
        self.assertEqual([r['surface'] for r in self.rows], [0, 2, 0, 0, 0, 0, 0])
        self.assertEqual([r['feng_colour'] for r in self.rows], [0, 0, 0, 0, 4, 0, 0])
        self.assertTrue(all(r['series'] == 55 and not r['lucky'] and not r['face'] for r in self.rows))
        self.assertTrue(all(not r['feng_facing_penalty'] for r in self.rows))
        with self.assertRaises(ValueError):
            metadata(self.rel[:-1] + bytes((self.rel[-1] ^ 1,)), self.symbols)


if __name__ == '__main__':
    unittest.main()
