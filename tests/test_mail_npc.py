"""Complete-record grading is scoped to one send and cannot mutate source mail."""

import ctypes as C
from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_mail_templates import template_fields
from mail_catalog import parse, templates, verify_registered
from mail_format import format_letter
from mail_grade_model import grade, legacy_grade
from mail_grading import load_prefixes
from mail_record import Field, Record, pack
from mail_reference import assembly_cases
from test_retail import ROM_PATH

CATALOG = ROOT/'build/mail-catalog/catalog.bin'
REL = ROOT/'build/gamecube/files/foresta.rel.szs.decoded'
SYMBOLS = ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt'


class Context(C.Structure):
    _fields_ = [('body',C.c_void_p),('ordinary',C.c_uint),('legacy',C.c_uint),('nonspaces',C.c_int)]


@unittest.skipUnless(CATALOG.is_file() and REL.is_file() and SYMBOLS.is_file()
                     and shutil.which('gcc'),'Registered local catalog, English reference, and host GCC required')
class MailNpcTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = CATALOG.read_bytes()
        verify_registered(cls.catalog)
        cls.banks = parse(cls.catalog)[1]
        cls.prefixes = load_prefixes(REL.read_bytes(),SYMBOLS.read_text())[0]
        cls.temporary = tempfile.TemporaryDirectory()
        directory = Path(cls.temporary.name)
        prefixes = directory/'prefixes.c'
        prefixes.write_text('const unsigned char af_mail_prefixes[1606] = {'+
                            ','.join(map(str,cls.prefixes))+'};\n')
        library = directory/'mail-npc.so'
        run = subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                              '-I'+str(ROOT/'runtime'),
                              *(str(ROOT/'runtime/mail'/name) for name in ('record.c','format.c','catalog.c')),
                              str(ROOT/'runtime/mail_grade.c'),str(ROOT/'runtime/mail_npc.c'),
                              str(ROOT/'overlays/mail_check/grade.c'),
                              *(str(ROOT/'tests'/name) for name in ('mail_catalog_mock.c','mail_grade_mock.c','mail_npc_mock.c')),
                              str(prefixes),'-o',str(library)],capture_output=True,text=True)
        if run.returncode: raise RuntimeError(run.stderr)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_mail_send_npc.argtypes = [C.c_void_p]
        cls.lib.af_mail_grade_native.argtypes = [C.c_void_p]
        cls.lib.af_mail_grade_length.argtypes = [C.c_void_p,C.c_void_p]
        cls.lib.af_mail_word_rate_body.argtypes = [C.c_void_p,C.c_void_p,C.c_uint]

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def integer(self,name): return C.c_uint.in_dll(self.lib,name)

    def setUp(self):
        for name in ('af_npc_allocations','af_npc_releases','af_npc_fail_allocate','af_npc_mock_errors',
                     'af_npc_sends','af_npc_native_lengths','af_npc_depth','af_mail_catalog_reads',
                     'af_mail_catalog_dma_error','af_mail_catalog_fail_read','af_grade_fail_allocate',
                     'af_grade_wrong_overlay','af_grade_fail_at','af_grade_allocated','af_grade_freed','af_grade_loaded','af_grade_invoked'):
            self.integer(name).value = 0
        C.c_void_p.in_dll(self.lib,'af_npc_nested_mail').value = None
        self.context = C.c_void_p.in_dll(self.lib,'af_mail_npc_context')
        self.context.value = None
        self.integer('af_mail_catalog_enabled').value = 1
        self.integer('af_npc_send_result').value = 42
        C.memmove((C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom'),self.catalog,len(self.catalog))

    def record(self,index=0xFD):
        record = Record(2,0,(index,),())
        fields = set().union(*(template_fields(p) for p in templates(self.catalog,record).parts))
        return replace(record,fields=tuple((i,Field(b'hello',4)) for i in sorted(fields)))

    def mail(self,record):
        data = bytearray(164)
        data[:6] = b'READER'
        data[0x12:0x18] = b'WRITER'
        data[0x26:0x2A] = bytes((1,0x80,4,0))
        data[0x2A:] = pack(record)
        return bytes(data)

    def send(self,data,expected_return=42):
        # Unaligned Mail_c proves only the allocated decode workspace needs
        # 16-byte alignment; the wrapper reads record bytes without word casts.
        source = C.create_string_buffer(b'EDGE!'+data+b'EDGE!')
        self.assertEqual(self.lib.af_mail_send_npc(C.byref(source,5)),expected_return)
        self.assertEqual(source.raw,b'EDGE!'+data+b'EDGE!\0')
        self.assertEqual(self.integer('af_npc_mock_errors').value,0)
        self.assertEqual(self.integer('af_mail_catalog_dma_error').value,0)
        return tuple((C.c_int*3).in_dll(self.lib,'af_npc_observed'))

    def test_full_body_scores_reach_both_consumers_before_original_send(self):
        record = self.record()
        body = format_letter(record,templates(self.catalog,record)).body
        self.assertGreater(len(body),96)
        expected = (grade(body,self.prefixes)[-1],*legacy_grade(body,self.prefixes)[:2])
        self.assertEqual(self.send(self.mail(record)),expected)
        self.assertIsNone(self.context.value)
        self.assertEqual([self.integer(n).value for n in
                          ('af_npc_allocations','af_npc_releases','af_npc_sends')],[1,1,1])
        self.assertEqual(self.integer('af_npc_native_lengths').value,0)
        self.assertEqual(self.integer('af_grade_allocated').value,2)
        self.assertEqual(self.integer('af_grade_freed').value,2)

    @unittest.skipUnless(ROM_PATH.is_file(),'Native reply-group reference required')
    def test_all_complete_reference_snapshots_and_both_capital_states(self):
        count = different = 0
        for label,record,_,limitation in assembly_cases(self.banks,ROM_PATH.read_bytes()):
            if record is None: continue
            record = replace(record,catalog=2)
            body = format_letter(record,templates(self.catalog,record)).body
            expected = (grade(body,self.prefixes)[-1],*legacy_grade(body,self.prefixes)[:2])
            with self.subTest(case=label,limitation=limitation):
                self.assertEqual(self.send(self.mail(record)),expected)
                self.assertIsNone(self.context.value)
            different += expected != (grade(body[:96],self.prefixes)[-1],*legacy_grade(body[:96],self.prefixes)[:2])
            count += 1
        self.assertEqual(count,6398)
        self.assertGreater(different,1000)
        self.assertEqual(self.integer('af_npc_allocations').value,self.integer('af_npc_releases').value)

    def test_ordinary_records_bypass_decoding_and_preserve_native_return(self):
        data = bytearray(b' '*164)
        data[0x34:0x94] = b'Hello there!'.ljust(96,b' ')
        self.assertEqual(self.send(bytes(data)),(grade(bytes(data[0x34:0x94]),self.prefixes)[-1],1,123))
        self.assertEqual(self.integer('af_npc_allocations').value,0)
        self.assertEqual(self.integer('af_mail_catalog_reads').value,0)
        self.assertEqual(self.integer('af_npc_native_lengths').value,1)
        self.integer('af_npc_send_result').value = 0
        self.send(bytes(data),0)

    def test_invalid_snapshots_resources_allocations_and_dma_never_send(self):
        valid = self.mail(self.record())
        for offset in (0x26,0x2A,0x2B,0x2C,0x2D,0x2E,0x32,163):
            data = bytearray(valid)
            data[offset] = 255 if offset == 0x26 else data[offset]^1
            self.send(bytes(data),0)
        for flag in ('af_npc_fail_allocate','af_grade_fail_allocate','af_grade_wrong_overlay'):
            self.integer(flag).value = 1
            self.send(valid,0)
            self.integer(flag).value = 0
        self.integer('af_mail_catalog_enabled').value = 0
        self.send(valid,0)
        self.integer('af_mail_catalog_enabled').value = 1
        self.assertEqual(self.integer('af_npc_sends').value,0)
        self.assertIsNone(self.context.value)
        self.integer('af_mail_catalog_reads').value = 0
        self.send(valid)
        reads = self.integer('af_mail_catalog_reads').value
        self.integer('af_npc_sends').value = 0
        for index in range(1,reads+1):
            self.integer('af_mail_catalog_reads').value = 0
            self.integer('af_mail_catalog_fail_read').value = index
            self.send(valid,0)
        self.assertEqual(self.integer('af_npc_sends').value,0)
        self.assertIsNone(self.context.value)

    def test_nested_sends_restore_outer_context_and_pointer_matching_is_exact(self):
        record = self.record()
        nested = C.create_string_buffer(self.mail(self.record(0)))
        C.c_void_p.in_dll(self.lib,'af_npc_nested_mail').value = C.addressof(nested)
        unrelated = C.create_string_buffer(b'Hello.'.ljust(96,b' '))
        outer = Context(C.addressof(unrelated),2,0,777)
        self.context.value = C.addressof(outer)
        self.send(self.mail(record))
        self.assertEqual(self.context.value,C.addressof(outer))
        self.assertEqual(self.integer('af_npc_sends').value,2)
        length = C.c_int(-1)
        self.assertEqual(self.lib.af_mail_grade_native(unrelated),2)
        self.assertEqual(self.lib.af_mail_grade_length(C.byref(length),unrelated),0)
        self.assertEqual(length.value,777)
        other = C.create_string_buffer(b'Hello.'.ljust(96,b' '))
        self.assertEqual(self.lib.af_mail_grade_length(C.byref(length),other),1)
        self.assertEqual(length.value,123)
        bad = bytearray(self.mail(record)); bad[0x2A] ^= 1
        self.send(bytes(bad),0)
        self.assertEqual(self.context.value,C.addressof(outer))
        self.context.value = None

    def test_second_grader_allocation_failure_releases_decode_storage_and_never_sends(self):
        self.integer('af_grade_fail_at').value = 2
        self.send(self.mail(self.record()),0)
        self.assertEqual(self.integer('af_grade_allocated').value,2)
        self.assertEqual(self.integer('af_grade_freed').value,1)
        self.assertEqual(self.integer('af_npc_allocations').value,1)
        self.assertEqual(self.integer('af_npc_releases').value,1)
        self.assertEqual(self.integer('af_npc_sends').value,0)
        self.assertIsNone(self.context.value)

    def test_null_inputs_and_word_loader_failure_do_not_publish(self):
        self.assertEqual(self.lib.af_mail_send_npc(None),0)
        length = C.c_int(-1)
        self.assertEqual(self.lib.af_mail_grade_length(C.byref(length),None),2)
        self.assertEqual(length.value,-1)
        self.assertEqual(self.lib.af_mail_grade_length(None,b'Hi'),2)
        for body,size in ((None,1),(b'Hi',1025)):
            self.assertEqual(self.lib.af_mail_word_rate_body(C.byref(length),body,size),-1)
            self.assertEqual(length.value,-1)
        self.assertEqual(self.integer('af_grade_allocated').value,0)


if __name__ == '__main__': unittest.main()
