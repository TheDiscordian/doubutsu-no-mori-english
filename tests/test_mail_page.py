"""Complete letter pages retain every glyph and explicit blank line."""

import ctypes as C
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))


class Span(C.Structure):
    _fields_ = [(name, C.c_uint) for name in ('section', 'offset', 'length', 'y')]


class Page(C.Structure):
    _fields_ = [('total', C.c_uint), ('count', C.c_uint), ('spans', Span*8)]


@unittest.skipUnless(shutil.which('gcc'), 'Host GCC required')
class MailPageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/'mail-page.so'
        subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                        str(ROOT/'runtime/mail/page.c'), str(ROOT/'runtime/mail/view.c'),
                        str(ROOT/'tests/mail_view_mock.c'), '-o', str(library)], check=True, capture_output=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_mail_page.argtypes = [C.c_void_p]*3+[C.c_uint]
        cls.widths = (C.c_int*256).in_dll(cls.lib, 'af_mail_view_widths')
        cls.widths[:] = [12]*256
        for code in range(32, 127):
            cls.widths[code] = 4 if code in b"iIl'" else 6

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def page(self, parts, number=0):
        buffers = [C.create_string_buffer(part) for part in parts]
        sections = (C.c_void_p*3)(*(C.addressof(b) for b in buffers))
        lengths = (C.c_uint*3)(*map(len, parts))
        page = Page()
        self.assertEqual(self.lib.af_mail_page(C.byref(page), sections, lengths, number), 1)
        return page.total, [(s.section, s.offset, s.length, s.y) for s in page.spans[:page.count]]

    def test_native_geometry_continuations_and_footer_room(self):
        parts = (b'To READER', b'a'*192, b'End')
        total, spans = self.page(parts)
        self.assertEqual(total, 1)
        self.assertEqual(spans, [(0,0,9,0)]+[(1,i*32,32,28+i*16) for i in range(6)]+[(2,0,3,136)])
        parts = (parts[0], parts[1], b'f'*33)
        self.assertEqual(self.page(parts)[0], 2)
        self.assertEqual(self.page(parts,1)[1], [(0,0,9,0),(2,0,32,120),(2,32,1,136)])
        parts = (b'H', b'  a\xcd\xcd z', b'  End  ')
        self.assertEqual(self.page(parts)[1], [(0,0,1,0),(1,0,3,28),(1,4,0,44),(1,5,2,60),(2,0,7,136)])

    def test_long_headers_and_footers_remain_complete(self):
        parts = (b'h'*1032, b'b'*1024, b'f'*1024)
        total = self.page(parts)[0]
        collected = [bytearray(), bytearray(), bytearray()]
        for number in range(total):
            count, spans = self.page(parts, number)
            self.assertEqual(count,total)
            self.assertLessEqual(len(spans),8)
            for section, offset, length, y in spans:
                self.assertTrue(0 <= y <= 136)
                collected[section].extend(parts[section][offset:offset+length])
        self.assertEqual(tuple(map(bytes,collected)),parts)

    def test_random_pages_preserve_every_glyph_space_and_blank_line(self):
        rng = random.Random(7199)
        for _ in range(150):
            parts = tuple(bytes(rng.choice(b"a iI'\xcd\xa1") for _ in range(rng.randrange(250))) for _ in range(3))
            first = self.page(parts)
            repeat = bool(parts[0]) and not parts[0].count(b'\xcd') and sum(self.widths[c] for c in parts[0]) <= 192
            # A trailing header newline is also a single repeated line.
            if parts[0].endswith(b'\xcd') and parts[0].count(b'\xcd') == 1:
                repeat = sum(self.widths[c] for c in parts[0][:-1]) <= 192
            collected = [bytearray(), bytearray(), bytearray()]
            blanks = [0,0,0]
            for number in range(first[0]):
                _, spans = self.page(parts, number)
                self.assertLessEqual(len(spans),8)
                for section, offset, length, y in spans:
                    if number and repeat and section == 0:
                        continue
                    text = parts[section][offset:offset+length]
                    self.assertNotIn(205,text)
                    self.assertLessEqual(sum(self.widths[c] for c in text),192)
                    self.assertTrue(0 <= y <= 136)
                    collected[section].extend(text)
                    blanks[section] += not length
            self.assertEqual(tuple(map(bytes,collected)),tuple(part.replace(b'\xcd',b'') for part in parts))
            for section,part in enumerate(parts):
                required = sum(not line for line in part.split(b'\xcd')[:-1])
                self.assertGreaterEqual(blanks[section],required)

    def test_invalid_requests_do_not_publish(self):
        page = Page()
        C.memset(C.byref(page),0xCC,C.sizeof(page))
        before = bytes(page)
        source = C.create_string_buffer(b'H')
        sections = (C.c_void_p*3)(C.addressof(source),0,0)
        lengths = (C.c_uint*3)(1,0,0)
        for out, pointers, sizes, number in ((None,sections,lengths,0),
                (C.byref(page),None,lengths,0),(C.byref(page),sections,None,0),
                (C.byref(page),sections,lengths,1),(C.byref(page),sections,lengths,1030)):
            self.assertEqual(self.lib.af_mail_page(out,pointers,sizes,number),0)
        for values in ((1033,0,0),(1,1025,0),(1,0,1)):
            self.assertEqual(self.lib.af_mail_page(C.byref(page),sections,(C.c_uint*3)(*values),0),0)
        self.assertEqual(bytes(page),before)
        self.assertEqual(self.page((b'',b'',b'')),(1,[]))


if __name__ == '__main__':
    unittest.main()
