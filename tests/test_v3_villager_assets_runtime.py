"""Focused current build: fixed banks, retained resources, memory, and native code."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import DMA_START, apply_ups, by_vrom, n64_checksum, sha256
from v3_villager_assets_runtime import (ABI, ART, BASE, BASE_SHA, BLOB, CAPACITY,
    CONFIG, FLAGS, GROWTH, MODULE, RESIDENT, accessory_slot, compose, install_art,
    load_art, model_slot, replace_constants, texture_slot)

OUTPUT = ROOT/'build/v3-complete-villager-assets-01'


class RuntimeGuards(unittest.TestCase):
    def test_fixed_bank_ids_and_invalid_identity_rejection(self):
        self.assertEqual(texture_slot(235), (429, 0x03F36000))
        self.assertEqual(texture_slot(232), (426, 0x03F30000))
        self.assertEqual(texture_slot(216), (410, BLOB+0x40000))
        self.assertEqual(model_slot(233), (430, BLOB+0x12000))
        self.assertEqual(model_slot(229), (431, BLOB+0x14000))
        self.assertEqual(accessory_slot(67), (447, BLOB+0x36000))
        for function, args in ((texture_slot, (215, 236)), (model_slot, (216, 235)),
                               (accessory_slot, (51, 68))):
            for value in args:
                with self.assertRaises(ValueError): function(value)

    def test_retained_code_may_change_only_reviewed_immediates(self):
        a, b = bytes.fromhex('2c6201ae'), bytes.fromhex('2c6201c0')
        self.assertEqual(len(replace_constants(a, b, {(430, 448)})), 1)
        for changed in (a, b+b, bytes.fromhex('2c6301c0'), bytes.fromhex('2c6201c1')):
            with self.assertRaises(ValueError): replace_constants(a, changed, {(430, 448)})

    def test_sanitized_current_capacity_and_boundaries(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-expanded-assets-') as temp:
            binary = Path(temp)/'check'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_expanded_assets_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('ownership pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current full-asset implementation build required')
class CurrentCartridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.image = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.old, cls.new = by_vrom(cls.base), by_vrom(cls.image)
        cls.blob = cls.new[BLOB].extract(cls.image)
        cls.records, cls.resources = load_art(ART)

    def test_all_art_and_fixed_bank_rows_are_installed_without_changing_original_banks(self):
        original = self.old[BLOB].extract(self.base)
        self.assertEqual(self.blob[0x1000:0x1000+410*8], original[0x1000:0x1000+410*8])
        self.assertEqual(len(self.records), 38)
        for row in self.records:
            start, end = struct.unpack_from('>II', self.blob, 0x1000+row['bank']*8)
            self.assertEqual((start, end), (int(row['vrom'], 16), int(row['vrom'], 16)+row['bytes']))
            e = next(e for e in self.new.values() if e.vstart <= start < end <= e.vend)
            self.assertEqual(e.extract(self.image)[start-e.vstart:end-e.vstart], self.resources[row['bank']])
        self.assertEqual(next(r for r in self.records if r['bank'] == 431)['skeleton'], '06002770')
        self.assertEqual(self.blob[GROWTH:GROWTH+224], self.old[0xE0D000].extract(self.base))
        self.assertEqual(self.blob[FLAGS:FLAGS+20], bytes(20))
        self.assertEqual(self.report['villager_assets']['move_in_enabled'], [])

    def test_resident_changes_are_exact_and_profile_is_retained(self):
        before = bytearray(self.old[BLOB].extract(self.base))
        allowed = [(0, 20), (0x100, 0x100+self.report['asset']['bytes']),
                   (0x1000+410*8, 0x1E60), (GROWTH, GROWTH+224),
                   (0x3400, 0x3400+self.report['villager_selection']['code']['bytes'])]
        after = bytearray(self.blob[:len(before)])
        for start, end in allowed:
            before[start:end] = after[start:end]
        self.assertEqual(before, after)
        self.assertEqual(struct.unpack_from('>5I', self.blob), (0x41465633, ABI, RESIDENT, CAPACITY, 410))
        module = self.new[MODULE].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, RESIDENT, zlib.crc32(self.blob[:RESIDENT]), ABI))
        self.assertEqual(self.blob[RESIDENT-16:RESIDENT], bytes.fromhex('AF33C0DE')*4)
        for part in ('asset', 'startup'):
            self.assertTrue(self.report[part]['instruction_changes'])
        self.assertTrue(self.report['villager_selection']['code']['instruction_changes'])

    def test_only_one_directory_row_changes_and_all_audio_physical_locations_are_retained(self):
        self.assertEqual(set(self.old), set(self.new))
        self.assertEqual(len(self.image), 32*1024*1024)
        for v, e in self.old.items():
            if v != BLOB:
                self.assertEqual(e, self.new[v], hex(v))
            if v not in (BLOB, MODULE, 0x19D40):
                self.assertEqual(e.extract(self.base), self.new[v].extract(self.image), hex(v))
        # Full physical comparison catches stale startup copies and unlisted writes.
        expected = bytearray(self.base)
        entry = self.new[BLOB]
        expected[entry.pstart:entry.pstart+entry.size] = self.blob
        module = self.new[MODULE]
        expected[module.pstart:module.pstart+module.size] = module.extract(self.image)
        row = DMA_START+entry.index*16
        expected[row:row+16] = self.image[row:row+16]
        expected[0x10:0x18] = self.image[0x10:0x18]
        self.assertEqual(expected, self.image)

    def test_bad_source_bundle_and_reconstruction(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        self.assertEqual(n64_checksum(self.image), struct.unpack_from('>II', self.image, 0x10))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), self.image)
        with self.assertRaises(ValueError): compose(bytes(len(self.base)), self.blob, bytes(0x8000))
        with self.assertRaises(ValueError):
            install_art(bytes(len(self.blob)), self.records, self.resources, self.old, self.base)
        with tempfile.TemporaryDirectory(prefix='af-v3-bad-art-') as temp:
            with self.assertRaises(FileNotFoundError): load_art(Path(temp))


if __name__ == '__main__':
    unittest.main()
