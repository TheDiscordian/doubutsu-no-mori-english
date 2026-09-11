"""Focused current-cartridge checks; no replay of old builds or saves."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups, n64_checksum
from map_town_suffix_fix import patch_asset, VROM, START, SIZE, LOAD


class MapTownSuffixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (ROOT/'build/v2-keyboard-06/Animal Forest English V2 Development.z64').read_bytes()
        cls.current = (ROOT/'build/v2-map-suffix-07/Animal Forest English V2.z64').read_bytes()
        cls.old_files, cls.new_files = by_vrom(cls.base), by_vrom(cls.current)

    def test_only_suffix_pixels_change(self):
        old = self.old_files[VROM].extract(self.base)
        new = self.new_files[VROM].extract(self.current)
        self.assertEqual(new, patch_asset(old))
        self.assertEqual(new[START:START+SIZE], bytes(SIZE))
        self.assertEqual((old[:START], old[START+SIZE:]), (new[:START], new[START+SIZE:]))
        self.assertEqual(new[0x1178:0x11B0], LOAD)

    def test_every_other_resource_and_size_retained(self):
        self.assertEqual(len(self.base), len(self.current))
        self.assertEqual(set(self.old_files), set(self.new_files))
        for vrom, before in self.old_files.items():
            after = self.new_files[vrom]
            self.assertEqual((before.index, before.size), (after.index, after.size))
            if vrom not in (VROM, 0x19D40):
                self.assertEqual(before.extract(self.base), after.extract(self.current))

    def test_source_guard(self):
        old = self.old_files[VROM].extract(self.base)
        for bad in (old[:-1], old[:START]+bytes(SIZE)+old[START+SIZE:]):
            with self.assertRaises(ValueError):
                patch_asset(bad)

    def test_checksum_and_original_input_patch(self):
        self.assertEqual(struct.unpack_from('>2I', self.current, 0x10), n64_checksum(self.current))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        patch = (ROOT/'build/v2-map-suffix-07/Animal Forest English V2.ups').read_bytes()
        self.assertEqual(apply_ups(native, patch), self.current)


if __name__ == '__main__':
    unittest.main()
