"""Pure default-message selection cannot overwrite custom or saved contents."""

import ctypes as C
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import verified_rom, sha256
from textbanks import banks

NATIVE = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


@unittest.skipUnless(shutil.which('gcc') and NATIVE.is_file(), 'Host GCC and supplied cartridge required')
class GyroidDefaultSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = verified_rom(NATIVE.read_bytes())
        cls.original = next(b for b in banks(rom) if b.name == 'string').entries()[0x55C]
        if len(cls.original) != 64 or sha256(cls.original) != 'b3c40cd00dd3610400c2ff42cd922c63b7130720690e8abf30c16048a8eb7900':
            raise ValueError('Changed original saved gyroid default')
        cls.temp = tempfile.TemporaryDirectory(); path = Path(cls.temp.name)
        source = path/'native.c'
        source.write_text('const unsigned char af_gyroid_native_default[64] = {'+
                          ','.join(str(b) for b in cls.original)+'};\n')
        library = path/'default.so'
        subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                        str(ROOT/'overlays/gyroid_default/default.c'), str(source), '-o', str(library)],
                       capture_output=True, text=True, check=True)
        cls.lib = C.CDLL(str(library))
        cls.select = cls.lib.af_gyroid_default_select
        cls.select.argtypes = [C.c_uint, C.c_void_p]; cls.select.restype = C.c_uint

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def test_only_exact_complete_default_and_original_owner_message_are_selected(self):
        original = C.create_string_buffer(self.original)
        self.assertEqual(self.select(0x0928, original), 0x2AE7)
        for requested in (0, 0x0934, 0x0935, 0x0925, 0x092E, 0x0929, 0x2AE7, 0x10000928, 0xFFFFFFFF):
            self.assertEqual(self.select(requested, original), requested)
            self.assertEqual(self.select(requested, None), requested)
        self.assertEqual(self.select(0x0928, None), 0x0928)
        self.assertEqual(original.raw, self.original+b'\0')

    def test_every_single_byte_customisation_including_padding_remains_custom(self):
        source = C.create_string_buffer(self.original)
        for offset, initial in enumerate(self.original):
            for replacement in range(256):
                if replacement == initial: continue
                value = bytearray(self.original); value[offset] = replacement
                source.raw = bytes(value)+b'\0'
                self.assertEqual(self.select(0x0928, source), 0x0928, (offset, replacement))
                self.assertEqual(source.raw, bytes(value)+b'\0')

    def test_unaligned_saved_source_and_surrounding_bytes_are_unchanged(self):
        for prefix in (1, 2, 3, 16):
            raw = b'L'*prefix+self.original+b'R'*16
            source = C.create_string_buffer(raw)
            self.assertEqual(self.select(0x0928, C.byref(source, prefix)), 0x2AE7)
            self.assertEqual(source.raw, raw+b'\0')


if __name__ == '__main__': unittest.main()
