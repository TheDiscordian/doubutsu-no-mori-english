"""Gyroid formatting preserves explicit layout and native storage boundaries."""

import ctypes as C
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
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from gc_names import symbol_data
from gyroid_message import (CALLERS, GUARDS, SETTER_SHA256, GC_SETTER_SHA256,
                            GC_SOURCE_SHA256, evidence)
from test_retail import ROM_PATH


def reference(text, length, widths, capacity=68):
    """Reference-style after-glyph threshold, without source or padding trimming."""
    output = bytearray()
    width = rows = 0
    for code in text[:max(0, min(length, capacity))]:
        output.append(code)
        if code == 205:
            width = 0
            rows += 1
        else:
            width += widths[code]
            if len(output) < capacity and width > 186:
                output.append(205)
                width = 0
                rows += 1
        if len(output) >= capacity or rows > 4:
            break
    return bytes(output).ljust(capacity, b' ')


@unittest.skipUnless(shutil.which('gcc'), 'Host GCC required')
class GyroidMessageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temporary.name)
        library = cls.directory/'gyroid.so'
        subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                        str(ROOT/'runtime/gyroid_message.c'), str(ROOT/'tests/gyroid_message_mock.c'),
                        '-o', str(library)], capture_output=True, check=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_set_gyroid_message.argtypes = [C.c_void_p, C.c_int, C.c_void_p, C.c_int]
        cls.lib.af_set_gyroid_message.restype = None

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.widths = (C.c_int*256).in_dll(self.lib, 'af_gyroid_widths')
        self.widths[:] = [12]*256
        for code in range(32, 127):
            self.widths[code] = 4 if code in b"iIl'" else 6

    def run_case(self, text, length=None):
        length = len(text) if length is None else length
        window = C.create_string_buffer(b'!'*(0x132+68+32))
        source = C.create_string_buffer(text)
        self.lib.af_set_gyroid_message(window, 0, source, length)
        self.assertEqual(window.raw[:0x132], b'!'*0x132)
        self.assertEqual(window.raw[-33:], b'!'*32+b'\0')
        self.assertEqual(source.raw, text+b'\0')
        output = window.raw[0x132:0x176]
        self.assertEqual(output, reference(text, length, self.widths))
        return output

    def test_exact_thresholds_spaces_explicit_newlines_and_original_limits(self):
        self.assertEqual(self.run_case(b'a'*32)[:33], b'a'*32+b'\xcd')
        self.assertEqual(self.run_case(b'a'*31)[:32], b'a'*31+b' ')
        self.assertEqual(self.run_case(b'i'*47)[:48], b'i'*47+b'\xcd')
        for text in (b'', b'  a\xcd\xcd  z ', b'\xcd'*64, b'a'*64, b'i'*64,
                     b'\xa1'*64, b"I'i"*22, bytes(range(68)), b'a'*68):
            self.run_case(text)
        self.run_case(b'a'*68, 2147483647)
        for length in (-2147483648, -1, 0):
            self.assertEqual(self.run_case(b'abc', length), b' '*68)

    def test_every_byte_every_source_length_and_random_layout(self):
        for code in range(256):
            self.run_case(bytes([code])*64)
        rng = random.Random(91037)
        for length in range(69):
            for _ in range(12):
                self.run_case(bytes(rng.choice(b" aeiIl'\xcd\xa1!?\0") for _ in range(length)))

    def test_bad_pointers_slots_and_widths_do_not_publish(self):
        window = C.create_string_buffer(b'!'*512)
        source = C.create_string_buffer(b'abc')
        before = window.raw
        for slot in (-2147483648, -1, 1, 2147483647):
            self.lib.af_set_gyroid_message(window, slot, source, 3)
        self.lib.af_set_gyroid_message(None, 0, source, 3)
        self.lib.af_set_gyroid_message(window, 0, None, 3)
        for width in (-1, 0, 13):
            self.widths[ord('b')] = width
            self.lib.af_set_gyroid_message(window, 0, source, 3)
        self.assertEqual(window.raw, before)

    def test_overlapping_source_is_staged_before_writing(self):
        text = b'a'*64
        for shift in (-1, 0, 1, 16):
            value = bytearray(b'!'*512)
            value[0x132+shift:0x132+shift+len(text)] = text
            window = C.create_string_buffer(bytes(value))
            self.lib.af_set_gyroid_message(window, 0, C.byref(window, 0x132+shift), len(text))
            value[0x132:0x176] = reference(text, len(text), self.widths)
            self.assertEqual(window.raw, bytes(value)+b'\0')

    @unittest.skipUnless((ROOT/'local/ac-decomp/src/game/m_msg_ctrl.c_inc').is_file()
                         and (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').is_file(),
                         'Local English source and executable required')
    def test_independent_pinned_english_function_with_native_capacity(self):
        source = (ROOT/'local/ac-decomp/src/game/m_msg_ctrl.c_inc').read_text()
        source = source[source.index('extern void mMsg_Set_mail_str('):
                        source.index('extern void mMsg_Set_continue_msg_num(')]
        self.assertEqual(sha256(source.encode()), GC_SOURCE_SHA256)
        rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
        self.assertEqual(sha256(symbol_data(rel, symbols, 'mMsg_Set_mail_str')), GC_SETTER_SHA256)
        # Only the destination layout/capacity and glyph-width provider differ.
        # The extracted function itself is not modified or committed.
        prefix = '''#include <stddef.h>
typedef unsigned char u8;
#define mMsg_MAIL_STR0 0
#define mMsg_MAIL_STR_NUM 1
#define mMsg_MAIL_STRING_LEN 68
#define CHAR_NEW_LINE 205
#define CHAR_SPACE 32
#define TRUE 1
typedef struct { u8 padding[0x132]; u8 mail_str[1][68]; } mMsg_Window_c;
int widths[256];
int mFont_GetCodeWidth(u8 c, int cut) { (void)cut; return widths[c]; }
'''
        generated = self.directory/'reference.c'
        generated.write_text(prefix+source)
        library = self.directory/'reference.so'
        # The pinned source uses "for (dst; ...)"; keep it unchanged and permit
        # only that known no-effect expression in the independent reference.
        compiled = subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-Wno-unused-value', '-O2', '-shared', '-fPIC',
                                   str(generated), '-o', str(library)], capture_output=True, text=True)
        self.assertEqual(compiled.returncode, 0, compiled.stderr)
        gc = C.CDLL(str(library))
        gc.mMsg_Set_mail_str.argtypes = [C.c_void_p, C.c_int, C.c_void_p, C.c_int]
        gc_widths = (C.c_int*256).in_dll(gc, 'widths')
        rng = random.Random(769)
        for case in range(3000):
            if case % 50 == 0:
                self.widths[:] = [rng.randrange(1, 13) for _ in range(256)]
                gc_widths[:] = self.widths[:]
            text = bytes(rng.choice(b"\xcd\0 aeiIl'\xa1!?z") for _ in range(68))
            length = rng.randrange(-3, 75)
            expected = C.create_string_buffer(b'!'*512)
            gc.mMsg_Set_mail_str(expected, 0, text, length)
            self.assertEqual(self.run_case(text, length), expected.raw[0x132:0x176])


@unittest.skipUnless(ROM_PATH.is_file(), 'Local original ROM required')
class GyroidEvidenceTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'build/notice-seasonal-runtime/module.json').is_file(), 'Build current resident module first')
    def test_native_scenario_requires_both_installed_entry_and_original_insertion(self):
        from aflib import replace_dma
        from font import make_halfwidth
        from gyroid_message_test_scenario import scenario
        from runtime_module import add_runtime_module
        rom = ROM_PATH.read_bytes()
        replacements, _ = make_halfwidth(rom)
        additions, module = add_runtime_module(rom, replacements, ROOT/'build/notice-seasonal-runtime')
        built = replace_dma(rom, replacements, additions=additions)
        actions = scenario(built, module)
        self.assertEqual(sum('call' in a for a in actions), 47)
        self.assertEqual(sum('expect' in a for a in actions), 165)
        self.assertEqual(actions[-4:-1], [{'load_state': True}, {'resume': True}, {'wait': 2}])
        for address, error in ((0x8009DA94, 'installed entry'), (0x8009F670, 'unchanged native dialogue')):
            files = by_vrom(built)
            code = bytearray(files[CODE_VROM].extract(built))
            code[address-CODE_RAM+3] ^= 1
            damaged = replace_dma(built, {CODE_VROM: bytes(code)})
            with self.assertRaisesRegex(ValueError, error):
                scenario(damaged, module)

    def test_source_destination_and_caller_guards(self):
        rom = ROM_PATH.read_bytes()
        report = evidence(rom)
        self.assertEqual((report['destination_offset'], report['destination_bytes'], report['saved_source_bytes']),
                         (0x132, 68, 64))
        self.assertEqual([c['call_ram'] for c in report['callers']], ['809340EC', '8096B368'])
        files = by_vrom(rom)
        data = bytearray(files[CODE_VROM].extract(rom))
        class Entry:
            def extract(self, ignored): return data
        files[CODE_VROM] = Entry()
        with patch('gyroid_message.by_vrom', return_value=files):
            for address in GUARDS:
                data[address-CODE_RAM+3] ^= 1
                with self.assertRaises(ValueError): evidence(rom)
                with patch('gyroid_message.sha256', return_value=SETTER_SHA256):
                    with self.assertRaisesRegex(ValueError, 'instruction guard'): evidence(rom)
                data[address-CODE_RAM+3] ^= 1
        for vrom, ram, digest, start, words, _, _ in CALLERS:
            files = by_vrom(rom)
            data = bytearray(files[vrom].extract(rom))
            files[vrom] = Entry()
            with patch('gyroid_message.by_vrom', return_value=files):
                for i in range(len(words)):
                    data[start-ram+i*4+3] ^= 1
                    with self.assertRaises(ValueError): evidence(rom)
                    with patch('gyroid_message.sha256', side_effect=lambda b: digest if len(b) == len(data) else sha256(b)):
                        with self.assertRaisesRegex(ValueError, 'caller instruction guard'): evidence(rom)
                    data[start-ram+i*4+3] ^= 1


if __name__ == '__main__':
    unittest.main()
