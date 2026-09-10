"""Exact intensity inspection preserves every sample and rejects wrong formats."""
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from texture_preview import decode

class TexturePreviewTests(unittest.TestCase):
    def test_native_i8_is_eight_bit_intensity_without_nibble_swap(self):
        samples=bytes(range(256))
        expected=b''.join(bytes((v,v,v,255)) for v in samples)
        self.assertEqual(decode(samples,16,16,'i8'),expected)

    def test_gc_i8_tile_order(self):
        # Two horizontal 8x4 tiles; GC's I8 layout is not row-major.
        encoded=bytes(range(32))+bytes(range(100,132))
        values=b''.join(encoded[y*8:y*8+8]+encoded[32+y*8:40+y*8] for y in range(4))
        expected=b''.join(bytes((v,v,v,255)) for v in values)
        self.assertEqual(decode(encoded,16,4,'i8',gamecube=True),expected)

    def test_existing_intensity_formats_and_invalid_inputs(self):
        self.assertEqual(decode(b'\x1f',2,1,'i4'),bytes((17,17,17,255,255,255,255,255)))
        self.assertEqual(decode(b'\x1f',1,1,'ia8'),bytes((17,17,17,255)))
        for args in ((b'\x00',2,1,'i8'),(b'\x00',0,1,'i8'),(b'\x00',1,1,'rgba32')):
            with self.assertRaises(ValueError):decode(*args)
        with self.assertRaises(ValueError):decode(b'\x00',1,1,'i8',bytes(32))

if __name__=='__main__':unittest.main()
