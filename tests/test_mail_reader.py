"""Snapshot viewing decodes once, keeps source records, and never renders wire bytes."""

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
from mail_catalog import templates, verify_registered, parse
from mail_record import Record, Field, pack
from mail_format import format_letter
from audit_mail_templates import template_fields
from mail_reference import assembly_cases
from test_retail import ROM_PATH
from test_mail_page import Page
from test_mail_view import Draw

CATALOG = ROOT/'build/mail-catalog/catalog.bin'


class Reader(C.Structure):
    _fields_ = [('owner',C.c_void_p),('status',C.c_uint),('page',C.c_uint),('total',C.c_uint),
                ('lengths',C.c_uint*3),('layout',Page),('header',C.c_ubyte*1030)]


@unittest.skipUnless(CATALOG.is_file() and shutil.which('gcc'), 'Registered local catalog and host GCC required')
class MailReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = CATALOG.read_bytes()
        verify_registered(cls.catalog)
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/'mail-reader.so'
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                        *(str(ROOT/'runtime/mail'/name) for name in ('record.c','format.c','catalog.c','view.c','page.c','reader.c')),
                        *(str(ROOT/'tests'/name) for name in ('mail_catalog_mock.c','mail_view_mock.c','mail_reader_mock.c')),
                        '-o',str(library)],capture_output=True,check=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_mail_reader_copy.argtypes = [C.c_void_p]*3
        cls.lib.af_mail_reader_trigger.argtypes = [C.c_void_p]*2
        cls.lib.af_mail_snapshot_header.argtypes = [C.c_void_p]*3+[C.c_float,C.c_float,C.c_void_p]
        cls.lib.af_mail_snapshot_body.argtypes = [C.c_void_p]*3+[C.c_float]+[C.c_void_p]*4
        cls.lib.af_mail_snapshot_footer.argtypes = [C.c_void_p]*2+[C.c_float,C.c_float,C.c_void_p]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.lib.af_mail_reader_test_reset()
        self.state = Reader.in_dll(self.lib,'af_mail_reader')
        self.board = (C.c_ubyte*192).in_dll(self.lib,'af_mail_view_board')
        self.board[:] = b'!'*192
        self.menu = (C.c_uint*18)()
        self.menu[14] = 1
        self.colour = C.create_string_buffer(bytes([70,40,50,255]))
        self.calls = C.c_uint.in_dll(self.lib,'af_mail_view_calls')
        self.draws = (Draw*9).in_dll(self.lib,'af_mail_view_draws')
        self.buttons = C.c_uint.in_dll(self.lib,'af_mail_reader_buttons')
        self.reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads')
        self.reads.value = 0
        C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1
        rom = (C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom')
        C.memmove(rom,self.catalog,len(self.catalog))
        self.widths = (C.c_int*256).in_dll(self.lib,'af_mail_view_widths')
        self.widths[:] = [12]*256
        for code in range(32,127): self.widths[code] = 4 if code in b"iIl'" else 6

    def record(self,index):
        record = Record(2,0,(index,),())
        parts = templates(self.catalog,record)
        mask = set().union(*(template_fields(part) for part in parts.parts))
        return replace(record,fields=tuple((i,Field(b'x'*16,4)) for i in sorted(mask)))

    def open(self,record,*,wire=None,marker=0x80,kind=4):
        source = bytearray(164)
        source[:6] = b'READER'
        source[0x12:0x18] = b'WRITER'
        source[0x26:0x2A] = bytes([0,marker,kind,0])
        source[0x2A:] = pack(record) if wire is None else wire
        buffer = C.create_string_buffer(bytes(source),164)
        self.lib.af_mail_reader_copy(C.byref(self.board,8),buffer,self.menu)
        self.assertEqual(buffer.raw,bytes(source))
        self.assertEqual(bytes(self.board[:8])+bytes(self.board[172:]),b'!'*28)
        if marker == 128:
            self.assertEqual(bytes(self.board[0x32:172]),b' '*122)
            self.assertEqual(self.board[0x2F],0)
            self.assertEqual(self.state.owner,C.addressof(self.board))
        else:
            self.assertEqual(bytes(self.board[8:172]),bytes(source))
        return source

    def draw(self):
        self.calls.value = 0
        self.lib.af_mail_snapshot_header(1,1,self.menu,64,36,self.colour)
        self.assertLessEqual(self.calls.value,9)
        return [(bytes(d.text[:d.length]),d.x,d.y) for d in self.draws[:self.calls.value]]

    def test_full_header_body_footer_all_pages_and_no_repeated_dma(self):
        record = self.record(0xFD)
        letter = format_letter(record,templates(self.catalog,record))
        self.open(record)
        self.assertEqual(self.state.status,1)
        expected_header = letter.header[:letter.header_split]+b'READER'+letter.header[letter.header_split:]
        self.assertEqual(bytes(self.state.header[:self.state.lengths[0]]),expected_header)
        self.assertEqual(tuple(self.state.lengths),(len(expected_header),len(letter.body),len(letter.footer)))
        self.assertGreater(self.state.total,1)
        reads = self.reads.value
        before = bytes(self.board)
        collected = [bytearray(),bytearray()]
        for page in range(self.state.total):
            self.assertEqual(self.state.page,page)
            drawings = self.draw()
            visible = [(s.section,s.length,s.y) for s in self.state.layout.spans[:self.state.layout.count] if s.length]
            self.assertEqual(len(drawings),len(visible)+1)
            for (section,length,y),(text,x,actual_y) in zip(visible,drawings):
                self.assertEqual(actual_y,36+y)
                self.assertEqual(x,256-sum(self.widths[c] for c in text) if section == 2 else 64)
                if section: collected[section-1].extend(text)
            self.assertEqual(drawings[-1][0],f'Left/Right: {page+1}/{self.state.total}'.encode())
            y,ex,ey = C.c_float(64),C.c_float(-96),C.c_float(56)
            self.lib.af_mail_snapshot_body(1,self.menu,1,64,C.byref(y),C.byref(ex),C.byref(ey),self.colour)
            self.lib.af_mail_snapshot_footer(1,1,64,172,self.colour)
            self.assertEqual(y.value,160)
            self.assertEqual(self.calls.value,len(drawings))
            self.buttons.value = 0x100
            self.assertEqual(self.lib.af_mail_reader_trigger(1,self.menu),0x100)
        self.assertEqual(tuple(map(bytes,collected)),(letter.body.replace(b'\xcd',b''),letter.footer.replace(b'\xcd',b'')))
        self.assertEqual(self.reads.value,reads)
        self.assertEqual(bytes(self.board),before)
        self.assertEqual(self.state.page,self.state.total-1)
        for button in (0x8000,0x4000,0x1000,0x8100,0xD300):
            self.buttons.value = button
            self.assertEqual(self.lib.af_mail_reader_trigger(1,self.menu),button)
            self.assertEqual(self.state.page,self.state.total-1)
        self.buttons.value = 0x200
        self.lib.af_mail_reader_trigger(1,self.menu)
        self.assertEqual(self.state.page,self.state.total-2)
        self.buttons.value = 0x100
        self.menu[14] = 0
        self.lib.af_mail_reader_trigger(1,self.menu)
        self.assertEqual(self.state.page,self.state.total-2)
        self.menu[14] = 1
        self.state.owner = C.addressof(self.board)+4
        self.lib.af_mail_reader_trigger(1,self.menu)
        self.assertEqual(self.state.page,self.state.total-2)

    def test_invalid_wire_and_disabled_catalog_show_error_without_native_text(self):
        record = self.record(0)
        wire = bytearray(pack(record))
        wire[8] ^= 1
        for data,enabled in ((bytes(wire),1),(pack(record),0)):
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = enabled
            self.menu[14] = 2
            self.open(record,wire=data)
            self.assertEqual((self.state.status,self.state.page,self.state.total),(2,0,1))
            self.assertEqual(self.menu[14],1)
            self.assertEqual(self.draw(),[(b'Unable to read this letter.',64,64)])

    def test_ordinary_records_clear_cache_and_keep_copy_and_editor_mode(self):
        record = self.record(0)
        self.open(record)
        self.menu[14] = 3
        self.open(record,wire=b' '*122,marker=3)
        self.assertEqual((self.state.status,self.state.owner,self.menu[14]),(0,None,3))
        self.board[3],self.board[5],self.board[0x2F] = 6,3,3
        self.board[0x32:0x35] = b'To '
        self.assertEqual(self.draw(),[(b'To READER',64,36)])

    def test_special_header_types_do_not_insert_recipient(self):
        record = self.record(0)
        letter = format_letter(record,templates(self.catalog,record))
        for kind in (2,3,5):
            self.open(record,kind=kind)
            self.assertEqual(bytes(self.state.header[:self.state.lengths[0]]),letter.header)

    @unittest.skipUnless(ROM_PATH.is_file(), 'Native reply-group evidence required')
    def test_all_reference_probes_retain_complete_body_and_footer_across_pages(self):
        count = 0
        for label,record,parts,limitation in assembly_cases(parse(self.catalog)[1],ROM_PATH.read_bytes()):
            if record is None:
                continue
            record,parts = replace(record,catalog=2),replace(parts,catalog=2)
            expected = format_letter(record,parts)
            with self.subTest(reference=label,limitation=limitation):
                self.open(record)
                self.assertEqual(self.state.status,1)
                header = expected.header[:expected.header_split]+b'READER'+expected.header[expected.header_split:]
                self.assertEqual(bytes(self.state.header[:self.state.lengths[0]]),header)
                reads = self.reads.value
                collected = [bytearray(),bytearray()]
                for page in range(self.state.total):
                    drawings = iter(self.draw())
                    for span in self.state.layout.spans[:self.state.layout.count]:
                        if span.length:
                            text,_,_ = next(drawings)
                            if span.section: collected[span.section-1].extend(text)
                    self.buttons.value = 0x100
                    self.lib.af_mail_reader_trigger(1,self.menu)
                self.assertEqual(tuple(map(bytes,collected)),
                                 (expected.body.replace(b'\xcd',b''),expected.footer.replace(b'\xcd',b'')))
                self.assertEqual(self.reads.value,reads)
            count += 1
        self.assertEqual(count,6398)


if __name__ == '__main__':
    unittest.main()
