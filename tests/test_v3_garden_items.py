"""Keep actual garden identities, special acquisition, and scoring distinctions."""
import struct
import unittest

from tests.test_v3_furniture_art import ROOT
from aflib import sha256
from v3_garden_items import identity_evidence, metadata


@unittest.skipUnless((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').exists(),
                     'Supplied local donor required')
class GardenItemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.records, cls.rows = metadata(cls.rel, cls.symbols)

    def test_actual_identity_prices_acquisition_and_full_native_records(self):
        self.assertEqual(len(self.records), 192)
        self.assertEqual(sha256(self.records), '70c5bff1b773663f15be5d8f50f74e7149a3ebb6075d873daad99467396a6e84')
        expected = (
            (0x3268, 1178, 1620, 'birdhouse', 'ftr_listB', 156),
            (0x3284, 1185, 1260, 'bird feeder', 'ftr_listC', 155),
            (0x3290, 1188, 1530, 'Mr. Flamingo', 'ftr_listB', 162),
            (0x3294, 1189, 4000, 'mailbox', 'ftr_listPostoffice', 505),
            (0x32A0, 1192, 3380, 'garden gnome', 'ftr_listLottery', 158),
            (0x32A4, 1193, 1530, 'Mrs. Flamingo', 'ftr_listA', 163),
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
            self.assertEqual(row['ordinary_stock'], slot not in (3, 4))
            if slot in (3, 4):
                self.assertIsNone(row['stock_group'])
            self.assertFalse(row['runtime_installed'])
            self.assertFalse(row['selectable'])
        evidence = identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx')
        self.assertEqual([r['sheet_row'] for r in evidence], [2567, 2574, 2577, 2578, 2581, 2582])
        self.assertTrue(all(r['native_id_name_and_artwork_absent'] for r in evidence))

    def test_facing_lucky_surface_and_unimplemented_post_office_category_are_retained(self):
        expected = (
            ('e0058200', 56, 1, 0, True, False, '0000'),
            ('e0058400', 56, 2, 0, True, False, '0000'),
            ('e0050200', 56, 1, 0, False, False, '0001'),
            (None, 53, 19, 0, True, True, '0500'),
            ('e0054f00', 56, 7, 2, False, True, '0001'),
            ('e0050000', 56, 0, 0, False, False, '0001'),
        )
        for row, values in zip(self.rows, expected, strict=True):
            self.assertEqual(tuple(row[k] for k in ('native_hra_hex', 'series', 'birth_category',
                'surface', 'face', 'lucky', 'feng_hex')), values)
            self.assertEqual(row['feng_facing_penalty'], values[-1] == '0001')
        self.assertIn('port post-office reward acquisition and scoring category 19',
                      self.rows[3]['runtime_requirements'])
        with self.assertRaises(ValueError):
            metadata(self.rel[:-1] + bytes((self.rel[-1] ^ 1,)), self.symbols)


if __name__ == '__main__':
    unittest.main()
