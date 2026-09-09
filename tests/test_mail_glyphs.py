"""Complete source glyphs, immutable encoding, and atomic letter assembly."""

import ctypes as C
from dataclasses import replace
import json
from pathlib import Path
import shutil
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import test_mail_format as formatter_tests
from mail_catalog import BANKS, COUNTS, identity, parse, resource, valid_part
from mail_format import Templates, format_letter
from mail_glyph_codes import ADVANCES, CAPITALS
from mail_record import Field, Record
from mail_reference import load_reference, assembly_cases
from textbanks import Bank
from textcodec import GLYPHS
from gc_text import decoder_tables

REL = ROOT/'build/gamecube/files/foresta.rel.szs.decoded'
DATA = ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
DECOMP = ROOT/'local/ac-decomp'
CATALOG = ROOT/'build/mail-glyph-catalog/catalog.bin'
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


def fixture(parts,fields=(),capital=False,catalog=4):
    record,templates = formatter_tests.fixture(parts,fields,capital)
    return replace(record,catalog=catalog),replace(templates,catalog=catalog)


@unittest.skipUnless(shutil.which('gcc'),'Host GCC required')
class MailGlyphFormatTests(unittest.TestCase):
    setUpClass = classmethod(formatter_tests.MailFormatTests.setUpClass.__func__)
    tearDownClass = classmethod(formatter_tests.MailFormatTests.tearDownClass.__func__)
    inputs = formatter_tests.MailFormatTests.inputs
    compare = formatter_tests.MailFormatTests.compare
    reject = formatter_tests.MailFormatTests.reject

    def test_every_pair_and_old_catalogues_unknowns_and_saved_literals(self):
        for code in range(256):
            pair = bytes((0x80,code))
            args = fixture((b'\xcd',pair,b''))
            if code in ADVANCES:
                self.compare(*args)
                for catalog in (1,2,3,5,65535):
                    self.reject(*fixture((b'\xcd',pair,b''),catalog=catalog))
                self.reject(*fixture((b'\xcd',b'\x7f\x24',b''),((0,Field(pair)),)))
            else:
                self.reject(*args)

    def test_empty_field_capitalization_and_cross_part_state(self):
        for code in ADVANCES:
            for capital in (False,True):
                for field in (Field(b''),Field(b' '),Field(b'',1),Field(b'word')):
                    pair = bytes((0x80,code))
                    self.compare(*fixture((b'\xcd',b'\x7f\x24'+pair,b''),((0,field),),capital))
                    self.compare(*fixture((b'\xcd',b'\x7f\x24',pair,b'!',b''),((0,field),),capital))
        for code,upper in CAPITALS.items():
            record,parts = fixture((b'\xcd',b'\x7f\x24'+bytes((0x80,code)),b''),((0,Field(b'')),),True)
            self.assertEqual(format_letter(record,parts).body,bytes((0x80,upper)))
        # Existing composite command and capitalization order is retained.
        self.compare(*fixture((b'\xcd',b'\x7f',b'\x75\x7f\x24',b'\x80\x60',b''),((0,Field(b'')),)))

    def test_atomic_output_bounds_and_invalid_part_boundaries(self):
        for code in ADVANCES:
            pair = bytes((0x80,code))
            self.compare(*fixture((b'\xcd',b'x'*1022+pair,b'')))
            self.reject(*fixture((b'H',b'x'*1022+pair,b'')))
            self.reject(*fixture((b'\xcd',b'x\x80',bytes((code,)),b'',b'')))
            self.reject(*fixture((b'\xcd',b'x\x80',b'',bytes((code,)),b'')))
            self.reject(*fixture((b'\x80',b'',pair)))

    @unittest.skipUnless(REL.is_file() and ROM.is_file(),'Supplied English sources remain local')
    def test_all_complete_reference_assembly_cases_match_independent_model(self):
        banks,report = load_reference(DATA,DECOMP,REL,extended_glyphs=True)
        self.assertEqual(sum(bank['converted'] for bank in report['banks'].values()),4866)
        cases = 0
        for label,record,parts,limitation in assembly_cases(banks,ROM.read_bytes()):
            self.assertIsNotNone(record,label)
            with self.subTest(case=label):
                self.compare(replace(record,catalog=4),replace(parts,catalog=4))
            cases += 1
        self.assertEqual(cases,6514)


class MailGlyphCatalogTests(unittest.TestCase):
    def test_encoding_semantics_are_explicit_and_invalid_pairs_rejected(self):
        banks = {name:[b'']*count for name,count in zip(BANKS,COUNTS)}
        for code in ADVANCES:
            pair = bytes((0x80,code))
            self.assertEqual(valid_part(pair+b'\x7f\x3b',catalog=4),1<<15)
            for catalog in (2,3,5):
                with self.assertRaises(ValueError): valid_part(pair,catalog=catalog)
        for code in set(range(256))-ADVANCES.keys():
            with self.assertRaises(ValueError): valid_part(bytes((0x80,code)),catalog=4)
        for part in (b'\x80',b'a\x80',b'\x7f',b'\x7f\x80'):
            with self.assertRaises(ValueError): valid_part(part,catalog=4)
        banks['mail'][0] = b'\x80\x60\x7f\x75\x80\xD0'
        data = resource(banks,4)
        self.assertEqual(parse(data),(4,banks))
        self.assertEqual(identity(data)['semantics'],2)
        bad = bytearray(data);struct.pack_into('>I',bad,12,1)
        with self.assertRaises(ValueError): parse(bytes(bad))

    @unittest.skipUnless(REL.is_file() and CATALOG.is_file(),'Supplied English sources remain local')
    def test_all_source_tokens_and_previous_available_parts_are_preserved(self):
        banks,report = load_reference(DATA,DECOMP,REL,extended_glyphs=True)
        old,_ = load_reference(DATA,DECOMP,REL)
        self.assertEqual(resource(banks,4),CATALOG.read_bytes())
        table = decoder_tables(DECOMP/'tools/msg_tool.py')['CHAR_MAP']
        new_parts = pairs = count = 0
        for name,parts in banks.items():
            source = Bank(name,0,0,(DATA/(name+'_data.bin')).read_bytes(),
                          (DATA/(name+'_data_table.bin')).read_bytes()).entries()
            for number,(raw,converted) in enumerate(zip(source,parts)):
                self.assertIsNotNone(converted,(name,number))
                if old[name][number] is not None:
                    self.assertEqual(converted,old[name][number])
                else:
                    new_parts += 1
                before = after = 0
                while before < len(raw):
                    code = raw[before]
                    if code == 0x7F:
                        self.assertEqual(converted[after:after+2],raw[before:before+2])
                        before += 2;after += 2
                    elif code in ADVANCES:
                        self.assertEqual(converted[after:after+2],bytes((0x80,code)))
                        before += 1;after += 2;pairs += 1
                    else:
                        self.assertEqual(GLYPHS[converted[after]],table[code])
                        before += 1;after += 1
                self.assertEqual(after,len(converted))
                count += 1
        self.assertEqual((count,new_parts,pairs),(4866,59,100))
        self.assertEqual(identity(CATALOG.read_bytes())['sha256'],
                         '76aa61189ccc1043ee4d91f3fd7a2d351b0914b4a932515b47b5bcbe426323bb')


if __name__ == '__main__':
    unittest.main()
