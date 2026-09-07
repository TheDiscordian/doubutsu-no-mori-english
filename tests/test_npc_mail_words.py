"""Lossless reply-word mapping, canonical resource, and source mutation checks."""

from copy import deepcopy
from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from gc_text import decoder_tables
from mail_record import Record,pack,unpack
from mail_reference import transcode
from npc_mail_words import (Word,COUNT,RESOURCE_BYTES,HEADER_BYTES,ROW_BYTES,
    WORD_BASES,REFERENCE_BASES,identity,pack_words,unpack_words,lookup,prepare)
from textbanks import Bank,banks
from test_retail import ROM_PATH

LEGACY = ROOT/'build/inspect/legacy.z64'
REFERENCE = ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
DECODER = ROOT/'local/ac-decomp/tools/msg_tool.py'


class NpcMailWordResourceTests(unittest.TestCase):
    def setUp(self):
        self.rows = tuple(Word(*identity(i),(b'word with spaces')[:i%16+1]) for i in range(COUNT))
        self.data = pack_words(self.rows)

    def test_all_rows_lookup_and_wire_fields_retain_complete_values(self):
        self.assertEqual(len(self.data),RESOURCE_BYTES)
        decoded = unpack_words(self.data,sha256(self.data))
        self.assertEqual(decoded,self.rows)
        for row in self.rows:
            field = lookup(decoded,row.slot,row.native_id)
            self.assertEqual(field,row.field())
            self.assertEqual(field.article,0)
            record = Record(2,0,(0,),((row.slot,field),))
            self.assertEqual(unpack(pack(record),expected_catalog=2),record)

    def test_padding_order_ids_article_and_glyphs_are_strict(self):
        for changes in ({'text':b''},{'text':b'x'*17},{'text':b'\x7f'},
                        {'text':b'\x80'},{'text':b'\xcd'},{'text':'text'},
                        {'article':1},{'article':False},{'slot':14},
                        {'native_id':0},{'reference_id':0}):
            rows = list(self.rows);rows[0] = replace(rows[0],**changes)
            with self.subTest(changes=changes),self.assertRaises(ValueError): pack_words(rows)
        rows = list(self.rows);rows[0],rows[1] = rows[1],rows[0]
        with self.assertRaises(ValueError): pack_words(rows)
        with self.assertRaises(ValueError): pack_words(self.rows[:-1])
        for relative in (0,2,4,5,6,7,9,24,31):
            data = bytearray(self.data);data[HEADER_BYTES+relative] ^= 1
            data[32:64] = bytes.fromhex(sha256(data[64:]))
            with self.subTest(offset=relative),self.assertRaises(ValueError): unpack_words(data)

    def test_header_payload_changes_and_bound_content_hash_are_rejected(self):
        for offset in range(HEADER_BYTES):
            data = bytearray(self.data);data[offset] ^= 1
            with self.assertRaises(ValueError): unpack_words(data)
        for data in (b'',self.data[:-1],self.data+b'\0'):
            with self.assertRaises(ValueError): unpack_words(data)
        data = bytearray(self.data);data[HEADER_BYTES+8] = ord('x')
        with self.assertRaises(ValueError): unpack_words(data)
        # A recomputed embedded digest proves structure, not approved content.
        data[32:64] = bytes.fromhex(sha256(data[64:]))
        self.assertNotEqual(unpack_words(data)[0].text,self.rows[0].text)
        with self.assertRaises(ValueError): unpack_words(data,sha256(self.data))

    def test_source_slot_and_native_family_boundaries_never_shift_or_reroll(self):
        for slot,base in enumerate(WORD_BASES,3):
            for index in (base-1,base+32,-1,True,0.0):
                with self.assertRaises(ValueError): lookup(self.rows,slot,index)
            self.assertEqual(lookup(self.rows,slot,base).text,self.rows[(slot-3)*32].text)
            self.assertEqual(lookup(self.rows,slot,base+31).text,self.rows[(slot-3)*32+31].text)
        for slot in (2,14,-1,True,3.0):
            with self.assertRaises(ValueError): lookup(self.rows,slot,WORD_BASES[0])
        for index in (-1,COUNT,True,0.0):
            with self.assertRaises(ValueError): identity(index)
        with self.assertRaises(ValueError): lookup(self.rows[:-1],3,WORD_BASES[0])
        rows = list(self.rows);rows[0] = replace(rows[0],native_id=0)
        with self.assertRaises(ValueError): lookup(rows,3,WORD_BASES[0])


@unittest.skipUnless(ROM_PATH.is_file() and LEGACY.is_file() and DECODER.is_file()
                     and (REFERENCE/'string_data.bin').is_file(),'Local native/legacy/English word banks required')
class RetailNpcMailWordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = [next(bank for bank in banks(path.read_bytes(),legacy=old) if bank.name == 'string')
                       for path,old in ((ROM_PATH,False),(LEGACY,True))]
        cls.sources.append(Bank('string',0,0,(REFERENCE/'string_data.bin').read_bytes(),
                                (REFERENCE/'string_data_table.bin').read_bytes()))
        cls.tables = decoder_tables(DECODER)

    def test_every_full_word_matches_both_sources_and_preserves_native_identity(self):
        data,report = prepare(*self.sources,self.tables)
        rows = unpack_words(data,report['resource_sha256'])
        self.assertEqual(report['resource_sha256'],'698e26d21c20eddcc25766317aa52024949f4eba51db99d73d58d46f6c5a12c1')
        self.assertEqual((report['word_count'],report['words_exceeding_native_ten_bytes'],report['maximum_word_bytes']),
                         (352,83,16))
        old,reference = self.sources[1].entries(),self.sources[2].entries()
        for row,entry in zip(rows,report['rows']):
            self.assertEqual(row.text,old[row.native_id])
            self.assertEqual(row.text,transcode(reference[row.reference_id],self.tables))
            self.assertEqual(lookup(rows,row.slot,row.native_id).text,row.text)
            self.assertEqual(entry['captured_sha256'],sha256(row.text))
        for slot in (6,7):
            family = rows[(slot-3)*32:(slot-2)*32]
            self.assertEqual([row.reference_id for row in family],list(range(REFERENCE_BASES[slot-3],REFERENCE_BASES[slot-3]+32)))

    def test_all_three_source_banks_and_tables_are_hash_guarded(self):
        for source in range(3):
            for part in ('data','table'):
                bank = self.sources[source]
                changed = bytes([getattr(bank,part)[0]^1])+getattr(bank,part)[1:]
                sources = list(self.sources);sources[source] = replace(bank,**{part:changed})
                with self.subTest(source=source,part=part),self.assertRaises(ValueError):
                    prepare(*sources,self.tables)

    def test_changed_decoder_cannot_supply_a_different_word(self):
        tables = deepcopy(self.tables)
        tables['CHAR_MAP'][ord('f')] = 'x'
        with self.assertRaisesRegex(ValueError,'not confirmed'):
            prepare(*self.sources,tables)


if __name__ == '__main__': unittest.main()
