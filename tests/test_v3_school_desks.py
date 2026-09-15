"""Full desk artwork, retained seats/materials, and source-verified metadata."""
from dataclasses import replace
import json
import struct
import unittest
import test_v3_furniture_art as static_tests
from v3_furniture_art import SCHOOL_DESKS,parse_model,prepare,native_profile,scalar_profile
from v3_school_desks import metadata


class SchoolDeskTests(static_tests.FurnitureArtLocalTests):
    output=static_tests.ROOT/'build/v3-school-desks-art-04'
    pilots=SCHOOL_DESKS
    expected_sizes=(3920,4064,2864)
    expected_hashes=('2bbb242ee2997768f7cfbc36680e55d0bdeaef72b378cad138c6b2937d44df16',
                     'f59eb8fc7b0f58f789a867cd0efff46175a5d8e103fb1861ccc5dbe79d8a15ca',
                     'cbbe0a4aae4e5e7663f501e38914f6cd21ded278a90d306be881907ad9d72705')

    def test_exact_seat_flags_and_two_cell_profile_without_dropped_behaviour(self):
        self.assertEqual(tuple(p.contact_action for p in self.pilots),(1,1,0))
        for p,row in zip(self.pilots,self.report['objects'],strict=True):
            profile=native_profile(p,row['object_bytes'],row['model_offsets'],0x02500000)
            self.assertEqual(profile[48:64],scalar_profile(p))
            self.assertEqual(profile[60],p.contact_action)
            self.assertEqual(profile[56:58],bytes((p.shape,p.collision)))
            self.assertEqual(profile[32:48],bytes(16))
        for p in self.pilots[:2]:
            with self.assertRaisesRegex(ValueError,'Unreviewed furniture pilot'):
                prepare(self.rel,self.symbols,replace(p,contact_action=0))

    def test_grey_is_explicit_and_other_parser_modes_remain_strict(self):
        raw,pointers=static_tests.fixture();raw=bytearray(raw)
        struct.pack_into('>I',raw,0x34,0xB2B2B2FF)
        args=(raw,0x100,pointers,0x500,{0x600:(32,32)},0x1000,48)
        with self.assertRaisesRegex(ValueError,'primitive colour'):parse_model(*args)
        rows=parse_model(*args,school=True)
        self.assertIn((0xFA000080,0xB2B2B2FF),[r['words'] for r in rows])
        with self.assertRaises(ValueError):parse_model(*args,school=True,garden=True)
        struct.pack_into('>I',raw,0x34,0xB2B2B280)
        with self.assertRaisesRegex(ValueError,'primitive colour'):parse_model(*args,school=True)

    def test_current_donor_names_stock_scoring_and_identity_evidence(self):
        output=static_tests.ROOT/'build/v3-school-desks-items-01'
        data,rows=metadata(self.rel,self.symbols,static_tests.ROOT/'build/item-identity-megasheet.xlsx')
        report=json.loads((output/'items.json').read_bytes())
        self.assertEqual(data,(output/'items.bin').read_bytes());self.assertEqual(rows,report['rows'])
        self.assertEqual(len(data),96);self.assertFalse(report['runtime_installed'])
        self.assertEqual([r['contact_action'] for r in rows],[1,1,0])
        self.assertEqual([r['size_code'] for r in rows],[0,0,1])
        self.assertEqual([r['price'] for r in rows],[1240,1240,1580])
        self.assertEqual([r['stock_group'] for r in rows],[0,1,1])
        self.assertTrue(all(not r['selectable'] and not r['runtime_installed'] for r in rows))
        self.assertEqual([r['native_hra_hex'] for r in rows],['4c058000','4c058200','4c050280'])


if __name__=='__main__':unittest.main()
