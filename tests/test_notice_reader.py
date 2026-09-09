"""Board reader ownership, full draws, native-control precedence, and retry."""

import ctypes as C
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from mail_record import Record
from notice_record import pack
from mail_catalog import parse
from audit_noticeboard import initial_body
import test_notice_initial as initial_tests
import test_notice_page as page_tests


class Cache(C.Structure):
    _fields_ = [('source', C.c_void_p), ('status', C.c_uint), ('page', C.c_uint),
                ('saved', C.c_ubyte*96), ('body', initial_tests.NoticeText), ('layout', page_tests.Page)]


class Draw(C.Structure):
    _fields_ = [('length', C.c_uint), ('x', C.c_float), ('y', C.c_float),
                ('colour', C.c_ubyte*4), ('text', C.c_ubyte*128)]


class Label(C.Structure):
    _fields_ = [('length', C.c_uint), ('x', C.c_float), ('y', C.c_float), ('text', C.c_ubyte*32)]


@unittest.skipUnless(initial_tests.CATALOG.is_file(), 'Local immutable catalogue required')
class NoticeReaderTests(unittest.TestCase):
    reader_source = 'overlays/notice/reader.c'
    extra_sources = ()

    @classmethod
    def generated_compile_flags(cls, directory): return []

    @classmethod
    def setUpClass(cls):
        cls.data = initial_tests.CATALOG.read_bytes()
        cls.banks = parse(cls.data)[1]
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-notice-reader-')
        library = Path(cls.temporary.name)/'reader.so'
        sources = ['runtime/mail/record.c', 'runtime/mail/format.c', 'runtime/mail/catalog.c',
                   'runtime/crc32.c', 'runtime/dateformat.c', 'runtime/mail/view.c',
                   'runtime/notice/record.c', 'runtime/notice/initial.c', 'runtime/notice/page.c',
                   cls.reader_source, 'tests/mail_catalog_mock.c', 'tests/mail_view_mock.c',
                   'tests/notice_reader_mock.c', *cls.extra_sources]
        flags = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                 '-fno-omit-frame-pointer', '-g'] if os.environ.get('AF_NOTICE_SANITIZE') == '1' else []
        flags += cls.generated_compile_flags(Path(cls.temporary.name))
        compiler_env = dict(os.environ)
        compiler_env.pop('LD_PRELOAD', None)
        compiled = subprocess.run(['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                                   *flags, *(str(ROOT/name) for name in sources), '-o', str(library)],
                                  capture_output=True, text=True, env=compiler_env)
        if compiled.returncode: raise RuntimeError(compiled.stderr)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_notice_draw_body.argtypes = [C.c_void_p]*3+[C.c_int, C.c_float, C.c_float]+[C.c_void_p]*2
        cls.lib.af_notice_read_control.argtypes = [C.c_void_p]*3
        cls.lib.af_notice_construct.argtypes = [C.c_void_p]
        cls.lib.af_notice_draw_entry.argtypes = [C.c_void_p, C.c_uint, C.c_float, C.c_float]
        cls.lib.af_notice_draw_date.argtypes = [C.c_void_p, C.c_void_p, C.c_float, C.c_float]
        cls.posts = (C.c_ubyte*(15*104)).in_dll(cls.lib, 'af_notice_posts')
        cls.cache = (Cache*2).in_dll(cls.lib, 'af_notice_cache')
        if C.sizeof(Cache) != cls.lib.af_notice_cache_size(): raise ValueError('Host cache ABI mismatch')
        cls.draws = (Draw*9).in_dll(cls.lib, 'af_mail_view_draws')
        cls.labels = (Label*8).in_dll(cls.lib, 'af_notice_labels')
        cls.widths = (C.c_int*256).in_dll(cls.lib, 'af_mail_view_widths')
        cls.widths[:] = [12]*256
        for code in range(32, 127): cls.widths[code] = 4 if code in b"iIl'" else 6
        rom = (C.c_ubyte*0x100000).in_dll(cls.lib, 'af_mail_catalog_rom')
        rom[0xA0000:0xA0000+len(cls.data)] = cls.data

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def number(self, name): return C.c_uint.in_dll(self.lib, name)

    def setUp(self):
        self.lib.af_notice_test_reset()
        self.number('af_mail_catalog_enabled').value = 1
        self.number('af_mail_catalog_reads').value = 0
        self.number('af_mail_catalog_fail_read').value = 0
        self.menu = (C.c_uint*18)()
        self.menu[1] = 1
        self.state = (C.c_ubyte*116)()
        self.state[1], self.state[3], self.state[4] = 8, 15, 4

    def put(self, slot, wire):
        self.posts[slot*104:slot*104+96] = wire
        self.posts[slot*104+96:slot*104+104] = bytes.fromhex('11223304050607d1')

    def draw(self, slot):
        self.number('af_mail_view_calls').value = self.number('af_notice_label_count').value = 0
        x, y = C.c_float(), C.c_float()
        self.lib.af_notice_draw_body(self.menu, 1, C.byref(self.posts, slot*104), 96,
                                     63.0, 63.0, C.byref(x), C.byref(y))
        count = self.number('af_mail_view_calls').value
        self.assertLessEqual(count, 6)
        self.assertEqual(self.number('af_notice_allocation_errors').value, 0)
        return [bytes(row.text[:row.length]) for row in self.draws[:count]]

    def control(self, buttons):
        self.number('af_notice_buttons').value = buttons
        self.lib.af_notice_read_control(1, self.menu, self.state)

    def test_all_initial_bodies_draw_completely_and_repeated_frames_do_not_reload(self):
        for number in range(0x1E, 0x22):
            record = Record(4, 0, (number,), ())
            self.put(4, pack(record))
            saved = bytes(self.posts)
            self.assertEqual(b''.join(self.draw(4)), initial_body(record, self.banks).replace(b'\xcd', b''))
            reads = self.number('af_mail_catalog_reads').value
            self.draw(4)
            self.assertEqual(self.number('af_mail_catalog_reads').value, reads)
            self.assertEqual(bytes(self.posts), saved)
        self.assertEqual((self.number('af_notice_allocations').value, self.number('af_notice_releases').value), (4, 4))

    def test_two_animated_posts_retain_distinct_cached_bodies_and_changed_slots_refresh(self):
        records = (Record(4, 0, (0x1E,), ()), Record(4, 0, (0x1F,), ()))
        for slot, record in zip((4, 5), records): self.put(slot, pack(record))
        for _ in range(3):
            for slot, record in zip((4, 5), records):
                self.assertEqual(b''.join(self.draw(slot)), initial_body(record, self.banks).replace(b'\xcd', b''))
        self.assertEqual(self.number('af_notice_allocations').value, 2)
        self.put(4, b'Manual changed post'.ljust(96, b' '))
        self.assertEqual(self.draw(4), [b'Manual changed post'])
        self.assertEqual(self.number('af_notice_allocations').value, 2)

    def test_extra_pages_use_lr_without_stealing_native_controls(self):
        self.put(4, (b'A\xcd'*7).ljust(96, b' '))
        self.assertEqual(self.draw(4), [b'A']*6)
        self.control(0x10)
        self.assertEqual(self.draw(4), [b'A'])
        self.assertEqual(bytes(self.labels[0].text[:self.labels[0].length]), b'L/R: page 2/2')
        self.control(0x10)
        self.assertEqual(self.draw(4), [b'A'])
        self.control(0x20)
        self.assertEqual(self.draw(4), [b'A']*6)
        for buttons in (0x30, 0x14, 0x18):
            self.control(buttons)
            self.assertEqual(self.draw(4), [b'A']*6)
        self.control(0x12)
        self.assertEqual((self.state[0], self.state[4]), (1, 3))
        self.assertEqual(self.number('af_notice_original_reads').value, 7)

    def test_write_close_and_editor_drawing_keep_native_behaviour(self):
        for buttons in (0x8010, 0x4010, 0x1010):
            self.menu[1], self.state[0], self.state[4] = 1, 0, 4
            self.control(buttons)
            if buttons & 0x8000: self.assertEqual((self.state[0], self.state[4]), (2, 15))
            else: self.assertEqual(self.menu[1], 0)
        self.menu[1] = 2
        self.put(4, pack(Record(4, 0, (0x21,), ())))
        saved = bytes(self.posts)
        x, y = C.c_float(), C.c_float()
        self.lib.af_notice_draw_body(self.menu, 1, C.byref(self.posts, 416), 96, 12.0, 13.0, C.byref(x), C.byref(y))
        self.assertEqual((x.value, y.value), (135.0, 469.0))
        self.assertEqual(self.number('af_notice_original_bodies').value, 1)
        self.assertEqual(self.number('af_notice_allocations').value, 0)
        self.assertEqual(bytes(self.posts), saved)

    def test_bad_or_unavailable_records_show_complete_error_without_leaks_and_reopen_retries(self):
        wire = pack(Record(4, 0, (0x21,), ()))
        error = [b'Unable to read this post.', b'Close and reopen to retry.']
        for changed in (wire[:3]+b'\x02'+wire[4:], b'\x7f?'+wire[2:], wire[:-1]+b'!'):
            self.put(4, changed)
            saved = bytes(self.posts)
            self.assertEqual(self.draw(4), error)
            self.assertEqual(bytes(self.posts), saved)
        self.put(4, wire)
        self.number('af_notice_fail_allocate').value = 1
        self.assertEqual(self.draw(4), error)
        self.number('af_notice_fail_allocate').value = 0
        self.assertEqual(self.draw(4), error)
        self.lib.af_notice_construct(1)
        self.assertEqual(b''.join(self.draw(4)), initial_body(Record(4, 0, (0x21,), ()), self.banks).replace(b'\xcd', b''))
        self.assertEqual(self.number('af_notice_allocations').value, self.number('af_notice_releases').value+1)

    def test_full_dates_and_entry_labels_do_not_mutate_timestamps(self):
        months = ('January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
                  'September', 'October', 'November', 'December')
        for month in range(1, 13):
            for day in (1, 9, 10, 31):
                self.number('af_notice_label_count').value = 0
                rtc = C.create_string_buffer(bytes((5, 4, 3, day, 2, month, 7, 209)), 8)
                before = rtc.raw
                self.lib.af_notice_draw_date(1, rtc, 63.0, 46.0)
                row = self.labels[0]
                expected = f'{months[month-1]} {day}, 2001'.encode()
                self.assertEqual(bytes(row.text[:row.length]), expected)
                self.assertEqual(row.y, 46)
                self.assertAlmostEqual(row.x+sum(self.widths[c] for c in expected)*0.75, 257.0)
                self.assertEqual(rtc.raw, before)
        for entry in range(1, 16):
            self.number('af_notice_label_count').value = 0
            self.lib.af_notice_draw_entry(1, entry, 63.0, 46.0)
            row = self.labels[0]
            self.assertEqual(bytes(row.text[:row.length]), f'entry {entry}'.encode())


if __name__ == '__main__': unittest.main()
