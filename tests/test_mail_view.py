"""Read-mode mail uses measured widths without changing manual newlines or saves."""

import ctypes as C
import json
from pathlib import Path
import random
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256
from mail_view_patch import RELOC_VROM, RELOC_SHA256, CALLS, SNAPSHOT_CALLS, remove_call_relocations, install
from mail_viewer import RAM, VROM
from test_retail import ROM_PATH


class Line(C.Structure):
    _fields_ = [('consumed', C.c_uint), ('drawn', C.c_uint), ('width', C.c_uint), ('newline', C.c_uint)]


class Draw(C.Structure):
    _fields_ = [('length', C.c_uint), ('x', C.c_float), ('y', C.c_float),
                ('colour', C.c_ubyte*4), ('text', C.c_ubyte*128)]


@unittest.skipUnless(shutil.which('gcc'), 'Host GCC required')
class MailViewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/'mail-view.so'
        subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                        str(ROOT/'runtime/mail/view.c'), str(ROOT/'tests/mail_view_mock.c'), '-o', str(library)],
                       capture_output=True, check=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_mail_next_line.argtypes = [C.c_void_p, C.c_void_p, C.c_uint]
        cls.lib.af_mail_read_body.argtypes = [C.c_void_p, C.c_void_p, C.c_void_p, C.c_float,
                                             C.c_void_p, C.c_void_p, C.c_void_p, C.c_void_p]
        cls.lib.af_mail_read_footer.argtypes = [C.c_void_p, C.c_void_p, C.c_float, C.c_float, C.c_void_p]

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.widths = (C.c_int*256).in_dll(self.lib, 'af_mail_view_widths')
        self.widths[:] = [12]*256
        for code in range(32, 127):
            self.widths[code] = 4 if code in b"iIl'" else 6
        self.board = (C.c_ubyte*192).in_dll(self.lib, 'af_mail_view_board')
        self.board[:] = b'!'*192
        self.calls = C.c_uint.in_dll(self.lib, 'af_mail_view_calls')
        self.calls.value = 0
        self.draws = (Draw*6).in_dll(self.lib, 'af_mail_view_draws')
        self.colour = C.create_string_buffer(bytes([70,40,50,255]), 4)

    def scan(self, text):
        line = Line(999,999,999,999)
        source = C.create_string_buffer(text)
        self.assertEqual(self.lib.af_mail_next_line(C.byref(line), source, len(text)), 1)
        return tuple(getattr(line, name) for name, _ in Line._fields_)

    def test_pixels_newlines_exact_edges_and_unmodified_spaces(self):
        for text, expected in ((b'', (0,0,0,0)), (b'\xcdabc', (1,0,0,1)),
                               (b'i'*48+b'a', (48,48,192,0)), (b'a'*32+b'\xcd', (33,32,192,1)),
                               (b'  a\xcd  z', (4,3,18,1)), (b'\xa1'*17, (16,16,192,0))):
            self.assertEqual(self.scan(text), expected)
        rng = random.Random(731)
        for _ in range(1000):
            text = bytes(rng.choice(b"a iIl'\xcd\xa1") for _ in range(rng.randrange(97)))
            used = drawn = pixels = newline = 0
            for code in text:
                if code == 205:
                    used += 1
                    newline = 1
                    break
                if pixels+self.widths[code] > 192:
                    break
                pixels += self.widths[code]
                used += 1
                drawn += 1
            self.assertEqual(self.scan(text), (used,drawn,pixels,newline))

    def test_invalid_line_inputs_do_not_publish(self):
        line = Line(1,2,3,4)
        source = C.create_string_buffer(b'abc')
        for out, text, size in ((None,source,3), (C.byref(line),None,3), (C.byref(line),source,1025)):
            self.assertEqual(self.lib.af_mail_next_line(out,text,size), 0)
        for width in (0,-1,193):
            self.widths[ord('b')] = width
            self.assertEqual(self.lib.af_mail_next_line(C.byref(line),source,3), 0)
        self.assertEqual(tuple(getattr(line,n) for n,_ in Line._fields_), (1,2,3,4))

    def test_complete_glyph_pairs_keep_exact_advances_and_byte_boundaries(self):
        from mail_glyph_codes import ADVANCES
        for code in range(256):
            pair = bytes((0x80,code))
            if code in ADVANCES:
                width = ADVANCES[code]
                self.assertEqual(self.scan(pair+b'\xcd'),(3,2,width,1))
                self.assertEqual(self.scan(b'a'*31+pair),
                                 (33,33,186+width,0) if width <= 6 else (31,31,186,0))
                count = 192//width
                self.assertEqual(self.scan(pair*(count+1)),(count*2,count*2,192,0))
            else:
                line = Line(1,2,3,4)
                self.assertEqual(self.lib.af_mail_next_line(C.byref(line),pair,len(pair)),0)
                self.assertEqual(tuple(getattr(line,n) for n,_ in Line._fields_),(1,2,3,4))
        line = Line(1,2,3,4)
        self.assertEqual(self.lib.af_mail_next_line(C.byref(line),b'a\x80',2),0)
        self.assertEqual(tuple(getattr(line,n) for n,_ in Line._fields_),(1,2,3,4))
        text = b'i\x80\xd0\x80\xbf'
        self.board[7] = len(text)
        self.board[0x9C:0x9C+len(text)] = text
        self.lib.af_mail_read_footer(1,1,64,172,self.colour)
        d = self.draws[0]
        self.assertEqual((self.calls.value,d.length,d.x),(1,len(text),256-19))
        self.assertEqual(bytes(d.text[:d.length]),text)

    def body(self, text):
        self.board[6] = len(text)
        self.board[0x3C:0x9C] = text.ljust(96,b' ')
        original = bytes(self.board)
        y, ex, ey = C.c_float(64), C.c_float(-96), C.c_float(56)
        self.lib.af_mail_read_body(1,1,1,64,C.byref(y),C.byref(ex),C.byref(ey),self.colour)
        self.assertEqual(bytes(self.board), original)
        return y.value,ex.value,ey.value

    def test_read_body_draws_complete_measured_spans_and_keeps_source(self):
        self.assertEqual(self.body(b'a'*32+b'\xcd'+b'i'*48), (160,-95,24))
        self.assertEqual(self.calls.value,2)
        self.assertEqual([(d.length,d.x,d.y) for d in self.draws[:2]], [(32,64,64),(48,64,80)])
        self.assertEqual([bytes(d.text[:d.length]) for d in self.draws[:2]], [b'a'*32,b'i'*48])
        self.assertTrue(all(bytes(d.colour)==bytes([70,40,50,255]) for d in self.draws[:2]))
        self.calls.value = 0
        self.body(b'\xa1'*96)
        self.assertEqual([(d.length,d.y) for d in self.draws], [(16,64+i*16) for i in range(6)])
        self.calls.value = 0
        self.body(b'\xcd\xcd a \xcdz')
        self.assertEqual([(d.length,d.y) for d in self.draws[:self.calls.value]], [(3,96),(1,112)])

    def test_footer_right_edge_and_rejection_are_read_only(self):
        text = b"iI'hello"
        self.board[7] = len(text)
        self.board[0x9C:0xAC] = text.ljust(16,b' ')
        original = bytes(self.board)
        self.lib.af_mail_read_footer(1,1,64,172,self.colour)
        d = self.draws[0]
        self.assertEqual((self.calls.value,d.length,d.x,d.y), (1,len(text),256-sum(self.widths[c] for c in text),172))
        self.assertEqual(bytes(d.text[:d.length]), text)
        self.assertEqual(bytes(self.board), original)
        self.calls.value = 0
        self.board[7] = 17
        self.lib.af_mail_read_footer(1,1,64,172,self.colour)
        self.assertEqual(self.calls.value, 0)
        self.widths[ord('a')] = 0
        self.assertEqual(self.body(b'a'), (64,-96,56))
        self.assertEqual(self.calls.value, 0)


@unittest.skipUnless(ROM_PATH.is_file(), 'Local native ROM required')
class MailViewPatchTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'build/runtime-module/module.json').is_file(), 'Build resident module first')
    def test_snapshot_option_changes_only_five_calls_and_three_relocations(self):
        from runtime_module import MODULE_VROM
        rom = ROM_PATH.read_bytes()
        files = by_vrom(rom)
        module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
        additions = {MODULE_VROM:(ROOT/'build/runtime-module/module.bin').read_bytes()}
        replacements = {}
        report = install(rom,replacements,additions,module,snapshots=True)
        self.assertTrue(report['snapshot_reader'])
        restored = bytearray(replacements[VROM])
        for address,old,symbol in CALLS+SNAPSHOT_CALLS:
            target = int(module['symbols'][symbol],16)
            self.assertEqual(struct.unpack_from('>I',restored,address-RAM)[0],0x0C000000|((target&0x0FFFFFFF)>>2))
            struct.pack_into('>I',restored,address-RAM,0x0C000000|((old&0x0FFFFFFF)>>2))
        self.assertEqual(restored,files[VROM].extract(rom))
        before = files[RELOC_VROM].extract(rom)
        after = replacements[RELOC_VROM]
        self.assertEqual(struct.unpack_from('>I',after,16)[0],49)
        self.assertEqual(list(struct.unpack_from('>49I',after,20)),
                         [v for v in struct.unpack_from('>52I',before,20) if v not in (0x440011A4,0x44001210,0x44001244)])
        self.assertEqual((len(after),after[:16],after[-4:]),(len(before),before[:16],before[-4:]))

    def test_relocation_removes_only_two_calls_and_rejects_mutations(self):
        data = by_vrom(ROM_PATH.read_bytes())[RELOC_VROM].extract(ROM_PATH.read_bytes())
        changed = remove_call_relocations(data)
        before = list(struct.unpack_from('>52I',data,20))
        after = list(struct.unpack_from('>50I',changed,20))
        self.assertEqual(after,[r for r in before if r not in (0x44001210,0x44001244)])
        self.assertEqual((len(changed),changed[:16],changed[-4:]), (len(data),data[:16],data[-4:]))
        for offset in (0,16,20):
            invalid = bytearray(data)
            invalid[offset] ^= 1
            with self.assertRaises(ValueError):
                remove_call_relocations(bytes(invalid))
        # The exact relocation checks must also work independently of the hash.
        invalid = bytearray(data)
        offset = 20+before.index(0x44001210)*4
        invalid[offset+3] ^= 1
        with patch('mail_view_patch.sha256',return_value=RELOC_SHA256), self.assertRaisesRegex(ValueError,'Missing'):
            remove_call_relocations(bytes(invalid))

    @unittest.skipUnless((ROOT/'build/runtime-module/module.json').is_file(), 'Build resident module first')
    def test_installer_binds_targets_and_preserves_every_other_overlay_byte(self):
        from runtime_module import MODULE_VROM
        rom = ROM_PATH.read_bytes()
        files = by_vrom(rom)
        module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
        additions = {MODULE_VROM:(ROOT/'build/runtime-module/module.bin').read_bytes()}
        replacements = {}
        report = install(rom,replacements,additions,module)
        self.assertEqual(report['read_mode'],1)
        self.assertFalse(report['saved_format_changed'])
        restored = bytearray(replacements[VROM])
        for address, old, symbol in CALLS:
            offset = address-RAM
            target = int(module['symbols'][symbol],16)
            self.assertEqual(struct.unpack_from('>I',restored,offset)[0],0x0C000000|((target&0x0FFFFFFF)>>2))
            struct.pack_into('>I',restored,offset,0x0C000000|((old&0x0FFFFFFF)>>2))
        self.assertEqual(restored,files[VROM].extract(rom))
        self.assertEqual(report['viewer_sha256'],sha256(replacements[VROM]))
        for repl,add,meta in ((replacements,additions,module), ({},{},module), ({},additions,None),
                              ({},additions,{**module,'symbols':{}})):
            with self.assertRaises(ValueError):
                install(rom,repl,add,meta)


if __name__ == '__main__':
    unittest.main()
