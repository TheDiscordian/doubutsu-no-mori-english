"""No bulletin-board sentence, manual blank line, or glyph pair disappears."""

import ctypes as C
from pathlib import Path
import os
import random
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))


class Line(C.Structure):
    _fields_ = [(name, C.c_uint) for name in ('offset', 'length', 'width')]


class Page(C.Structure):
    _fields_ = [('total', C.c_uint), ('count', C.c_uint), ('lines', Line*6)]


class NoticePageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-notice-page-')
        library = Path(cls.temporary.name)/'page.so'
        flags = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                 '-fno-omit-frame-pointer', '-g'] if os.environ.get('AF_NOTICE_SANITIZE') == '1' else []
        compiler_env = dict(os.environ)
        compiler_env.pop('LD_PRELOAD', None)
        subprocess.run(['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        *flags,
                        str(ROOT/'runtime/notice/page.c'), str(ROOT/'runtime/mail/view.c'),
                        str(ROOT/'tests/mail_view_mock.c'), '-o', str(library)],
                       check=True, capture_output=True, env=compiler_env)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_notice_page.argtypes = [C.c_void_p, C.c_void_p, C.c_uint, C.c_uint]
        cls.widths = (C.c_int*256).in_dll(cls.lib, 'af_mail_view_widths')
        cls.widths[:] = [12]*256
        for code in range(32, 127):
            cls.widths[code] = 4 if code in b"iIl'" else 6

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def page(self, text, number=0):
        output = C.create_string_buffer(b'!'*(C.sizeof(Page)+32), C.sizeof(Page)+32)
        self.assertEqual(self.lib.af_notice_page(C.byref(output, 16), text, len(text), number), 1)
        page = Page.from_buffer_copy(output.raw[16:-16])
        self.assertEqual((output.raw[:16], output.raw[-16:]), (b'!'*16, b'!'*16))
        return page.total, [(s.offset, s.length, s.width) for s in page.lines[:page.count]]

    def test_seventh_line_continues_and_trailing_newline_does_not_add_a_page(self):
        self.assertEqual(self.page(b'A\xcd'*6), (1, [(i*2, 1, 6) for i in range(6)]))
        self.assertEqual(self.page(b'A\xcd'*7), (2, [(i*2, 1, 6) for i in range(6)]))
        self.assertEqual(self.page(b'A\xcd'*7, 1), (2, [(12, 1, 6)]))
        self.assertEqual(self.page(b'\xcd'*7, 1), (2, [(6, 0, 0)]))
        self.assertEqual(self.page(b''), (1, []))
        self.assertEqual(self.page(b'  A\xcd\xcd B  '), (1, [(0, 3, 18), (4, 0, 0), (5, 4, 24)]))

    def test_width_boundaries_and_pairs_remain_complete_without_space_cleanup(self):
        self.assertEqual(self.page(b'A'*33), (1, [(0, 32, 192), (32, 1, 6)]))
        self.assertEqual(self.page(b'A'*32+b' '), (1, [(0, 32, 192), (32, 1, 6)]))
        text = b'A'*31+b'\x80\xbf'+b'\xcd'*6+b'\x80\xbf!'
        total = self.page(text)[0]
        collected = []
        for number in range(total):
            for offset, length, width in self.page(text, number)[1]:
                self.assertLessEqual(width, 192)
                span = text[offset:offset+length]
                self.assertFalse(span.endswith(b'\x80'))
                collected.append(span)
        self.assertEqual(b''.join(collected), text.replace(b'\xcd', b''))

    def test_random_whitespace_glyphs_and_maximum_length_are_all_reachable(self):
        rng = random.Random(0xAFB006)
        values = [b'\xcd'*1024, b'A'*1024]
        values += [bytes(rng.choice(b" a iI'\xcd\xa1") for _ in range(rng.randrange(1025))) for _ in range(100)]
        for text in values:
            collected = bytearray()
            total = self.page(text)[0]
            last_end = 0
            for number in range(total):
                count, spans = self.page(text, number)
                self.assertEqual(count, total)
                self.assertLessEqual(len(spans), 6)
                for offset, length, width in spans:
                    self.assertTrue(last_end <= offset <= offset+length <= len(text))
                    self.assertLessEqual(width, 192)
                    collected.extend(text[offset:offset+length])
                    last_end = offset+length
            self.assertEqual(bytes(collected), text.replace(b'\xcd', b''))

    def test_invalid_later_pages_and_inputs_do_not_publish_an_earlier_partial_page(self):
        for text, size, requested in ((None, 1, 0), (b'A', 1025, 0), (b'', 0, 1),
                                      (b'A', 1, 0xFFFFFFFF), (b'\x80', 1, 0),
                                      (b'\x80\x00', 2, 0), (b'A\xcd'*6+b'\x80', 13, 0)):
            output = C.create_string_buffer(b'!'*(C.sizeof(Page)+32), C.sizeof(Page)+32)
            self.assertEqual(self.lib.af_notice_page(C.byref(output, 16), text, size, requested), 0)
            self.assertEqual(output.raw, b'!'*len(output))
        self.assertEqual(self.lib.af_notice_page(None, b'A', 1, 0), 0)

    def test_independent_native_fixture_layout_matches_complete_page_spans(self):
        from notice_native_layout import rows
        rng = random.Random(0xAFB007)
        texts = [b'', b'\xcd'*1024, b'A'*1024, b'A'*32+b'\xcd', b'  A\xcd\xcd B  ']
        alphabet = [b' ', b'A', b"'", b'i', b'\xcd', b'\x80\xbf']
        texts += [b''.join(rng.choice(alphabet) for _ in range(rng.randrange(600))) for _ in range(50)]
        for text in texts:
            expected = rows(text, self.widths)
            spans = []
            total = self.page(text)[0]
            self.assertEqual(total, max(1, (len(expected)+5)//6))
            for number in range(total):
                spans += [(offset, text[offset:offset+length], width)
                          for offset, length, width in self.page(text, number)[1]]
            self.assertEqual(expected, spans)
        for bad in (b'\x80', b'\x80\x00'):
            with self.assertRaises(ValueError): rows(bad, self.widths)

    @unittest.skipUnless((ROOT/'build/mail-glyph-resources/glyph-catalog.bin').is_file(), 'Local references required')
    def test_all_scoped_bodies_and_full_dynamic_fields_retain_complete_text(self):
        from audit_noticeboard import INITIAL_IDS, SCOPED_IDS, initial_body
        from audit_mail_templates import template_fields
        from mail_catalog import parse
        from mail_record import Record, Field
        from mail_format import Templates, format_letter
        data = (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes()
        banks = parse(data)[1]
        for number in SCOPED_IDS:
            parts = tuple(banks[name][number] for name in ('super', 'mail', 'ps'))
            fields = sorted(set().union(*(template_fields(p, extended_glyphs=True) for p in parts)))
            record = Record(4, 0, (number,), tuple((i, Field(b'ABCDEFGHIJKLMNOP', 4)) for i in fields))
            body = initial_body(record, banks) if number in INITIAL_IDS else format_letter(
                record, Templates(4, 0, (number,)*3, parts)).body
            total = self.page(body)[0]
            complete = bytearray()
            for page in range(total):
                for offset, length, width in self.page(body, page)[1]:
                    complete.extend(body[offset:offset+length])
                    self.assertLessEqual(width, 192)
            self.assertEqual(bytes(complete), body.replace(b'\xcd', b''))
            if number in INITIAL_IDS:
                self.assertEqual(total, 1)
            if number == 0x1AE:
                self.assertGreaterEqual(total, 2)

    @unittest.skipUnless((ROOT/'build/mail-glyph-resources/glyph-catalog.bin').is_file(), 'Local references required')
    def test_reviewed_seasonal_bodies_and_full_dates_have_complete_native_page_spans(self):
        from notice_seasonal import audit
        from notice_native_layout import rows
        report = audit((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes())
        for case in report['cases']:
            body = bytes.fromhex(case['body'])
            total = self.page(body)[0]
            spans = []
            for number in range(total):
                spans += [(offset, body[offset:offset+length], width)
                          for offset, length, width in self.page(body, number)[1]]
            self.assertEqual(spans, rows(body, self.widths))
            self.assertEqual(b''.join(text for _, text, _ in spans), body.replace(b'\xcd', b''))


if __name__ == '__main__':
    unittest.main()
