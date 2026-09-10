"""Lossless scoped title extraction; no ROM installation is claimed."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from title_assets import CI4, extract, model_texture_shape, pack4, rgb5a3, untile


class TitleTextureTests(unittest.TestCase):
    def test_complete_tiles_preserve_each_row_and_all_four_edges(self):
        for bits, width, height in ((4, 16, 16), (4, 48, 64), (4, 64, 32), (8, 64, 16)):
            mask = (1 << bits)-1
            pixels = bytes((x*3+y*7+(x//8)*5+(y//4)*11) & mask for y in range(height) for x in range(width))
            block_height = 8 if bits == 4 else 4
            tiled = bytearray()
            for top in range(0, height, block_height):
                for left in range(0, width, 8):
                    for y in range(top, top+block_height):
                        tiled.extend(pixels[y*width+left:y*width+left+8])
            packed = pack4(tiled) if bits == 4 else bytes(tiled)
            with self.subTest(bits=bits, width=width, height=height):
                self.assertEqual(untile(packed, width, height, bits), pixels)

    def test_rejects_short_buffers_partial_tiles_and_invalid_samples(self):
        for args in ((b'', 8, 8, 4), (bytes(32), 7, 8, 4), (bytes(32), 8, 7, 4),
                     (bytes(32), True, 8, 4), (bytes(32), 8, 8, 16), (b'', 0, 0, 4)):
            with self.assertRaises(ValueError): untile(*args)
        for samples in (b'\x01', b'\x10\x00'):
            with self.assertRaises(ValueError): pack4(samples)

    def test_exact_rgb5a3_expansion_and_command_dimensions(self):
        for value, expected in ((0xFFFF, 'ffffffff'), (0x8000, '000000ff'),
                                (0, '00000000'), (0x7FFF, 'ffffffff'), (0x3123, '1122336d')):
            self.assertEqual(rgb5a3(value).hex(), expected)
        self.assertEqual(model_texture_shape(bytes.fromhex('FD443C2F00000000DF00000000000000')), (48, 64, 2, 0))
        with self.assertRaises(ValueError): model_texture_shape(bytes(8))


@unittest.skipUnless((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').is_file(), 'Supplied English extraction required')
class TitleSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_complete_scoped_assets_keep_duplicate_local_names_distinct(self):
        files, report = extract(self.rel, self.symbols)
        self.assertEqual(len(report['assets']), 80)
        self.assertEqual(len(report['textures']), 28)
        self.assertEqual(report['output_texture_bytes'], 263680)
        self.assertFalse(report['installed'])
        palettes = [row for row in report['assets'] if row['symbol'] == 'logo_us_pal']
        self.assertEqual(len(palettes), 3)
        self.assertEqual(len({row['source_file'] for row in palettes}), 3)
        self.assertTrue(all(row['source_file'] in files for row in report['assets']))
        for row in report['textures']:
            self.assertEqual(len(files[row['file']]), row['bytes'])

    def test_changed_source_symbol_map_and_equal_area_wrong_shape_reject(self):
        with self.assertRaises(ValueError): extract(self.rel[:-1], self.symbols)
        with self.assertRaises(ValueError): extract(self.rel, self.symbols+b'\n')
        rows = list(CI4); offset, _, _, palette = rows[8]
        rows[8] = (offset, 32, 96, palette)
        with patch('title_assets.CI4', tuple(rows)), self.assertRaisesRegex(ValueError, 'actual display list'):
            extract(self.rel, self.symbols)


if __name__ == '__main__':
    unittest.main()
