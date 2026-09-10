"""The real English prompt is linear IA8; keep every unrelated v1 resource."""
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups
from title_assets import extract, DATA_BASE
from title_press_start import ASSETS, TEXTURE_OFFSETS
from title_start_fix import source_tiles, build, BASE_SHA, reconstruct


@unittest.skipUnless((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').is_file(),
                     'Supplied native/English inputs required')
class TitleStartFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.base = (ROOT/'build/title-civic-interior-combined-01/animal-forest-title-preview.z64').read_bytes()

    def test_linear_source_not_tiled_or_nibble_swapped(self):
        tiles = source_tiles(self.rel, self.symbols)
        self.assertEqual([sha256(tile) for tile in tiles], [
            '3d1eeece6cdc4781e256c7eade05979bb57ea3206b52a9b5656bbea783cbae95',
            '98b37743e07fb6b472434f5a651bf5948d4e53d8675f159faf25743946ad1fba'])
        legacy = extract(self.rel, self.symbols)[0]
        for at, tile in zip((0x5E5020, 0x5E5420), tiles):
            self.assertEqual(tile, self.rel[DATA_BASE+at:DATA_BASE+at+1024])
            self.assertNotEqual(tile, legacy[f'{at:08X}.ia8.bin'])
            self.assertNotEqual(tile, bytes((v << 4 & 240) | (v >> 4) for v in tile))
        with self.assertRaises(ValueError): source_tiles(self.rel[:-1], self.symbols)
        with self.assertRaises(ValueError): source_tiles(self.rel, self.symbols+b'\n')

    def test_rebuild_installs_complete_tiles_and_preserves_code_and_every_other_owner(self):
        image, patch, report = build(self.native, self.base, self.rel, self.symbols)
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(image), '1898c04ffb844f5cd7ccd0199dae9c41c733e63e8accbe128a1a5933b71a0a08')
        self.assertEqual(apply_ups(self.native, patch), image)
        self.assertEqual(len(image), 32*1024*1024)
        files, old = by_vrom(image), by_vrom(self.base)
        self.assertEqual(set(files), set(old))
        for vrom, entry in files.items():
            self.assertEqual((entry.index, entry.size), (old[vrom].index, old[vrom].size))
            if vrom not in (ASSETS, 0x19D40):
                self.assertEqual(entry.extract(image), old[vrom].extract(self.base), f'{vrom:08X}')
        bank = bytearray(files[ASSETS].extract(image))
        original_bank = old[ASSETS].extract(self.base)
        for at, tile in zip(TEXTURE_OFFSETS, source_tiles(self.rel, self.symbols)+[bytes(1024)]):
            self.assertEqual(bank[at:at+1024], tile)
            bank[at:at+1024] = original_bank[at:at+1024]
        self.assertEqual(bank, original_bank)
        boot = by_vrom(self.native)[0x1060]
        self.assertEqual(image[boot.pstart:boot.pstart+boot.size], files[0x1060].extract(image))
        self.assertFalse(report['code_changed'])
        self.assertFalse(report['allocation_changed'])
        self.assertFalse(report['save_format_changed'])

    def test_changed_predecessor_and_unsafe_repacking_reject(self):
        with self.assertRaisesRegex(ValueError, 'baseline'):
            build(self.native, self.native, self.rel, self.symbols)
        for changes in ({}, {ASSETS: b'bad'}, {0x1060: by_vrom(self.base)[0x1060].extract(self.base)},
                        {0x3FFFFFF: bytes(16)}):
            with self.assertRaises(ValueError): reconstruct(self.native, self.base, changes)


if __name__ == '__main__':
    unittest.main()
