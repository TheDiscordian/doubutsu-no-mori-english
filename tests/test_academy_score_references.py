"""Bound score-letter sources and full English fields before native publication."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from academy_score_letters import TEMPLATES,COMPLETE,GUARDS,VROM,RELOCATION,fields,references,verify_overlay
from aflib import by_vrom,sha256
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field,Record,pack,unpack


@unittest.skipUnless((ROOT/'build/mail-catalog/catalog.bin').is_file(),'Local original and reference resources required')
class AcademyScoreReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.catalog = (ROOT/'build/mail-catalog/catalog.bin').read_bytes()
        cls.report = references(cls.native,cls.catalog)

    def test_all_native_ids_parts_and_unavailable_body_are_explicit(self):
        self.assertEqual(self.report['classic_templates'],list(TEMPLATES));self.assertEqual(len(COMPLETE),20)
        self.assertEqual(self.report['unavailable_templates'],[0x3D]);self.assertFalse(self.report['installed'])
        self.assertEqual(len(self.report['parts']),63)
        self.assertEqual([r['id'] for r in self.report['parts'] if 'unavailable' in r],['mail:003D'])
        self.assertEqual({n for n in self.report['native_selection_table'] if n>=0},set(TEMPLATES))
        self.assertTrue(all(n<0x220 for n in self.report['native_selection_table']))

    def test_all_fifty_five_complete_series_names_retain_source_ids(self):
        self.assertEqual(len(self.report['series']),55)
        for i,row in enumerate(self.report['series']):
            self.assertEqual(row['id'],i);native,english=bytes.fromhex(row['native']),bytes.fromhex(row['english'])
            self.assertEqual(len(native),10);self.assertEqual(len(english),16)
            self.assertEqual(sha256(native),row['source_sha256']);self.assertTrue(english.rstrip())

    def test_every_complete_letter_with_full_fields_and_all_series_names_fits_snapshot(self):
        for row in self.report['series']:
            values = (Field(b'2147483647'),Field(b'abcdefghijklmnop'),Field(bytes.fromhex(row['english'])),
                      Field(b'2000'),Field(b'September'),Field(b'31st'))
            for number in COMPLETE:
                for capital in (False,True):
                    used = fields('mail',number)
                    record = Record(2,0,(number,),tuple((i,v) for i,v in enumerate(values) if i in used),capital)
                    packed = pack(record);self.assertEqual(len(packed),122)
                    self.assertEqual(unpack(packed,expected_catalog=2),record)
                    text = format_letter(record,templates(self.catalog,record))
                    for i in used:
                        value = values[i].text.rstrip(b' ')
                        # Supplied commands can capitalise a field's first
                        # letter; this check concerns complete field capacity.
                        self.assertTrue(value in text.body or value[:1].upper()+value[1:] in text.body)
                    self.assertLessEqual(sum(map(len,(text.header,text.body,text.footer))),1024)

    def test_unknown_parts_and_mutated_overlay_relocations_are_rejected(self):
        for name,number in (('mail',0x220),('ps',0x1DC),('string',0x34)):
            with self.assertRaises(ValueError): fields(name,number)
        files = by_vrom(self.native);data,reloc=(files[v].extract(self.native) for v in (VROM,RELOCATION))
        for start,_,_ in GUARDS:
            changed=bytearray(data);changed[start-0x809259E0] ^= 1
            with self.assertRaises(ValueError): verify_overlay(changed,reloc)
        with self.assertRaises(ValueError): verify_overlay(data,reloc[:-1])


if __name__ == '__main__': unittest.main()
