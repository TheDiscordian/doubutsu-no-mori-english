"""Complete-letter creation stages captures and validates before publication."""

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
from mail_catalog import parse,templates,verify_registered
from mail_record import Record,Field,pack,unpack
from mail_reference import assembly_cases
from test_mail_format import CField,CText,inplace_reference
from test_retail import ROM_PATH

CATALOG_PATH = ROOT/'build/mail-catalog/catalog.bin'


class Capture(C.Structure):
    _fields_ = [('valid',C.c_uint),('capital',C.c_uint),('fields',CField*20)]


class Selection(C.Structure):
    _fields_ = [('catalog',C.c_ushort),('kind',C.c_ubyte),('reserved',C.c_ubyte),
               ('templates',C.c_ushort*5)]


@unittest.skipUnless(shutil.which('gcc'),'Host GCC required')
class MailGenerateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-mail-generation-')
        output = Path(cls.temporary.name)/'generate.so'
        sources = ['overlays/mail_generation/generate.c','runtime/mail/record.c',
                   'runtime/mail/format.c','runtime/mail/catalog.c',
                   'tests/mail_catalog_mock.c','tests/mail_generate_mock.c']
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                        *(str(ROOT/path) for path in sources),'-o',str(output)],
                       check=True,capture_output=True)
        cls.lib = C.CDLL(str(output))
        cls.lib.af_mail_capture_reset.argtypes = [C.c_void_p]
        cls.lib.af_mail_capture_set.argtypes = [C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint]
        cls.lib.af_mail_generate.argtypes = [C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p]
        cls.work_size = cls.lib.af_mail_generate_work_size()
        cls.text_offset = cls.lib.af_mail_generate_text_offset()

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def setUp(self):
        self.rom = (C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom')
        self.enabled = C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled')
        self.reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads')
        self.errors = C.c_uint.in_dll(self.lib,'af_mail_catalog_dma_error')
        self.fail_at = C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read')
        self.enabled.value,self.reads.value,self.errors.value,self.fail_at.value = 1,0,0,0

    def catalog(self):
        if not CATALOG_PATH.is_file(): self.skipTest('Registered local mail catalog required')
        self.data = CATALOG_PATH.read_bytes()
        verify_registered(self.data)
        C.memmove(self.rom,self.data,len(self.data))
        return parse(self.data)[1]

    def capture(self,record,extra=False):
        value = Capture()
        self.lib.af_mail_capture_reset(C.byref(value))
        if extra:
            for slot in range(20):
                self.assertEqual(self.lib.af_mail_capture_set(C.byref(value),slot,b'UNUSED VALUE    ',16,4),1)
        for slot,field in record.fields:
            self.assertEqual(self.lib.af_mail_capture_set(C.byref(value),slot,field.text,len(field.text),field.article),1)
        value.capital = int(record.initial_capital)
        return value

    def fixture(self,record,extra=False):
        capture = self.capture(record,extra)
        selection = Selection(2,record.kind,0,(C.c_ushort*5)(*record.templates))
        mail = C.create_string_buffer(b'!'*16+bytes(range(164))+b'!'*16,196)
        workspace = C.create_string_buffer(b'!'*(self.work_size+64),self.work_size+64)
        work = (C.addressof(workspace)+31)&~15
        return mail,capture,selection,workspace,work

    def call(self,record,success=True,extra=False,fixture=None,parts=None):
        mail,capture,selection,workspace,work = fixture or self.fixture(record,extra)
        before_mail,before_capture,before_selection = mail.raw,bytes(capture),bytes(selection)
        result = self.lib.af_mail_generate(C.byref(mail,16),164,C.byref(capture),C.byref(selection),work)
        self.assertEqual(result,int(success))
        lead = work-C.addressof(workspace)
        self.assertEqual(workspace.raw[:lead]+workspace.raw[lead+self.work_size:],b'!'*64)
        self.assertEqual(bytes(selection),before_selection)
        self.assertEqual(self.errors.value,0)
        if not success:
            self.assertEqual(mail.raw,before_mail)
            self.assertEqual(bytes(capture),before_capture)
            return
        expected = bytearray(before_mail)
        expected[16+39] = 128
        expected[16+42:16+164] = pack(record)
        self.assertEqual(mail.raw,bytes(expected))
        self.assertEqual(unpack(mail.raw[58:180],expected_catalog=2),record)
        text = CText.from_address(work+self.text_offset)
        reference = inplace_reference(record,parts or templates(self.data,record))
        self.assertEqual(tuple(bytes(text.text[o:o+n]) for o,n in zip(text.offsets,text.lengths)),
                         (reference.header,reference.body,reference.footer))
        self.assertEqual(text.split,reference.header_split)
        self.assertEqual(bool(capture.capital),reference.final_capital)
        old_capture = Capture.from_buffer_copy(before_capture)
        old_capture.capital = capture.capital
        self.assertEqual(bytes(capture),bytes(old_capture))
        self.assertEqual(text.reserved,0)
        self.assertFalse(any(text.text[sum(text.lengths):]))
        return mail,capture,selection,workspace,work

    def test_capture_all_slots_lengths_articles_padding_aliases_and_invalid_replacement(self):
        self.assertEqual(self.lib.af_mail_capture_size(),C.sizeof(Capture))
        self.assertEqual(self.lib.af_mail_selection_size(),C.sizeof(Selection))
        state = Capture()
        for slot in range(20):
            for size in range(17):
                for article in range(5):
                    value = (b'letters with gap'[:size]).ljust(size,b' ')
                    self.assertEqual(self.lib.af_mail_capture_set(C.byref(state),slot,value,size,article),1)
                    self.assertEqual((state.fields[slot].length,state.fields[slot].article),(size,article))
                    self.assertEqual(bytes(state.fields[slot].text),value.ljust(16,b'\0'))
                    self.assertTrue(state.valid & (1<<slot))
            # A substring of the field itself is captured before publication.
            at = C.addressof(state)+Capture.fields.offset+slot*C.sizeof(CField)+2
            expected = C.string_at(at+3,8)
            self.assertEqual(self.lib.af_mail_capture_set(C.byref(state),slot,at+3,8,2),1)
            self.assertEqual(bytes(state.fields[slot].text),expected.ljust(16,b'\0'))
            for value,size,article in ((None,1,0),(b'x'*17,17,0),(b'x',1,5),
                                       (b'\x7f',1,0),(b'\x80',1,0)):
                before = Capture.from_buffer_copy(state)
                self.assertEqual(self.lib.af_mail_capture_set(C.byref(state),slot,value,size,article),0)
                before.valid &= ~(1<<slot)
                self.assertEqual(bytes(state),bytes(before))
            self.assertEqual(self.lib.af_mail_capture_set(C.byref(state),slot,None,0,0),1)
        before = bytes(state)
        self.assertEqual(self.lib.af_mail_capture_set(C.byref(state),20,b'x',1,0),0)
        self.assertEqual(bytes(state),before)
        self.assertEqual(self.lib.af_mail_capture_set(None,0,b'x',1,0),0)
        self.lib.af_mail_capture_reset(C.byref(state))
        self.assertEqual(bytes(state),bytes(C.sizeof(state)))

    @unittest.skipUnless(ROM_PATH.is_file(),'Original ROM required for reference combinations')
    def test_all_reference_cases_and_unused_fields_are_pruned(self):
        banks = self.catalog()
        count = skipped = 0
        for label,record,parts,limitation in assembly_cases(banks,ROM_PATH.read_bytes()):
            if record is None:
                skipped += 1
                continue
            record = replace(record,catalog=2)
            with self.subTest(case=label,limitation=limitation):
                self.call(record,extra=True,parts=replace(parts,catalog=2))
            count += 1
        self.assertEqual((count,skipped),(6398,58))

    def test_missing_required_fields_overflow_and_unavailable_parts_are_atomic(self):
        banks = self.catalog()
        record = Record(2,0,(2,),())
        used = set().union(*(template_fields(p) for p in templates(self.data,record).parts))
        self.assertTrue(used)
        good = replace(record,fields=tuple((i,Field(b'complete')) for i in sorted(used)))
        self.call(good)
        for slot in used:
            self.call(replace(good,fields=tuple(row for row in good.fields if row[0] != slot)),success=False)
        fixture = self.fixture(good)
        slot = min(used)
        self.assertEqual(self.lib.af_mail_capture_set(C.byref(fixture[1]),slot,b'\x7f',1,0),0)
        self.call(good,success=False,fixture=fixture)
        overflow = Record(2,0,(1,),tuple((i,Field(b'x'*16)) for i in range(10,20)))
        self.assertEqual(set().union(*(template_fields(p) for p in templates(self.data,overflow).parts)),set(range(10,20)))
        with self.assertRaisesRegex(ValueError,'exceeds'): pack(overflow)
        self.call(overflow,success=False)
        unavailable = [i for i in range(982) if any(banks[name][i] is None for name in ('super','mail','ps'))]
        self.assertTrue(unavailable)
        for index in unavailable: self.call(Record(2,0,(index,),()),success=False,extra=True)
        for kind,ids in ((0,(982,)),(1,(0,0,384,0,0))):
            self.call(Record(2,kind,ids,()),success=False,extra=True)

    def test_each_dma_failure_and_corrupt_selected_metadata_preserves_mail_and_capture(self):
        self.catalog()
        record = Record(2,0,(0,),())
        used = set().union(*(template_fields(p) for p in templates(self.data,record).parts))
        record = replace(record,fields=tuple((i,Field(b'complete',i%5)) for i in sorted(used)))
        self.call(record)
        total = self.reads.value
        for read in range(1,total+1):
            self.reads.value,self.fail_at.value = 0,read
            self.call(record,success=False)
        self.fail_at.value = 0
        for offset in (*range(0,128,4),128,132,136,140,256,260,262,264,268):
            self.rom[offset] ^= 1
            self.call(record,success=False)
            self.rom[offset] ^= 1
        self.enabled.value,self.reads.value = 0,0
        self.call(record,success=False)
        self.assertEqual(self.reads.value,0)

    def test_sticky_capitalization_is_committed_only_with_a_complete_letter(self):
        banks = self.catalog()
        selected = next(i for i in range(982) if all(banks[name][i] is not None for name in ('super','mail','ps'))
                        and any(b'\x7f\x75' in banks[name][i] for name in ('super','mail','ps')))
        base = Record(2,0,(selected,),())
        used = set().union(*(template_fields(p) for p in templates(self.data,base).parts))
        record = replace(base,fields=tuple((i,Field(b'friend')) for i in sorted(used)))
        fixture = self.call(record)
        self.assertEqual(fixture[1].capital,1)
        total = self.reads.value
        self.reads.value,self.fail_at.value = 0,total
        self.call(record,success=False)
        self.fail_at.value = 0
        self.call(replace(record,initial_capital=True),fixture=fixture)
        self.reads.value,self.fail_at.value = 0,1
        self.call(replace(record,initial_capital=True),success=False,fixture=fixture)

    def test_invalid_configuration_sizes_alignment_and_overlaps_fail_before_dma(self):
        self.catalog()
        record = Record(2,0,(0,),())
        fixture = self.fixture(record,extra=True)
        mail,capture,selection,workspace,work = fixture
        for target,field,value in ((capture,'capital',2),(capture,'valid',1<<20),
                                   (selection,'catalog',3),(selection,'kind',2),(selection,'reserved',1)):
            old = getattr(target,field);setattr(target,field,value)
            self.call(record,success=False,fixture=fixture)
            setattr(target,field,old)
        selection.templates[1] = 1
        self.call(record,success=False,fixture=fixture)
        selection.templates[1] = 0
        original = (mail.raw,bytes(capture),bytes(selection),workspace.raw)
        args = (C.addressof(mail)+16,164,C.addressof(capture),C.addressof(selection),work)
        invalid = [(None,*args[1:]),(args[0],163,*args[2:]),
                   (*args[:2],None,*args[3:]),(*args[:3],None,args[4]),(*args[:4],None),
                   (*args[:4],work+1),(work,*args[1:]),
                   (*args[:2],work,*args[3:]),(*args[:3],work,args[4]),
                   (args[2],*args[1:]),(args[3],*args[1:]),
                   (*args[:3],args[2],args[4])]
        for bad in invalid:
            self.assertEqual(self.lib.af_mail_generate(*bad),0)
            self.assertEqual((mail.raw,bytes(capture),bytes(selection),workspace.raw),original)
        self.assertEqual(self.reads.value,0)


if __name__ == '__main__': unittest.main()
