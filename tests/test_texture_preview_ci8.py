"""Synthetic CI8 inspection checks; no game, old candidate, or build execution."""
from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from texture_preview import decode


class CI8PreviewTests(unittest.TestCase):
    def test_native_indices_and_alpha(self):
        palette = struct.pack('>256H', *(i << 8 | i for i in range(256)))
        actual = decode(bytes(range(256)), 16, 16, 'ci8', palette)
        expected = bytearray()
        for i in range(256):
            value = i << 8 | i
            channels = [(value >> shift) & 31 for shift in (11, 6, 1)]
            expected.extend(channel*8+channel//4 for channel in channels)
            expected.append(255*(value & 1))
        self.assertEqual(actual, expected)

    def test_gamecube_two_tile_rows_and_palette(self):
        # CI8 GC tiles are 8x4, not a linear 16x8 image.
        linear = bytes(range(128))
        tiled = bytes(linear[y*16+x] for ty in (0, 4) for tx in (0, 8)
                      for y in range(ty, ty+4) for x in range(tx, tx+8))
        values = [0x8000 | (i//32)<<10 | (i%32)<<5 | (31-i%32) for i in range(256)]
        values[127] = 0  # Also check GC's transparent RGB5A3 palette mode.
        palette = struct.pack('>256H', *values)
        expected = bytearray()
        for i in linear:
            if i == 127:
                expected.extend(b'\0\0\0\0')
            else:
                expected.extend(c*8+c//4 for c in (i//32, i%32, 31-i%32))
                expected.append(255)
        self.assertEqual(decode(tiled, 16, 8, 'ci8', palette, gamecube=True),
                         expected)

    def test_rejects_incomplete_data_or_palette(self):
        for data, palette in ((b'\0'*255, b'\0'*512), (b'\0'*256, None),
                              (b'\0'*256, b'\0'*32), (b'\0'*256, b'\0'*514)):
            with self.subTest(bytes=len(data), palette=None if palette is None else len(palette)):
                with self.assertRaises(ValueError):
                    decode(data, 16, 16, 'ci8', palette)


if __name__ == '__main__':
    unittest.main()
