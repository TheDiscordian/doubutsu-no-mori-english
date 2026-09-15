"""Installed construction assets, scoped writes, retained code, and save profiles."""
import ctypes as c
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import DMA_START, by_vrom, n64_checksum, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP
from v3_construction_runtime import (ART, BASE, BASE_SHA, ITEMS, ITEMS_RAM, PACKAGE,
                                     PACKAGE_SIZE, ROWS, ROWS_RAM, TABLE_END)
from v3_furniture_art import CONSTRUCTION_PILOTS, native_profile
from v3_registry import furniture_slot
from v3_save_clothing import PROFILE, STATE
from tests.test_v3_save_clothing import reference_pack
import v3_optional_composition as composer

OUTPUT = ROOT / 'build/v3-construction-runtime-02'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current construction cartridge required')
class ConstructionRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((BASE / 'build.json').read_text())
        cls.files, cls.old_files = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.old_blob = (files[BLOB].extract(image) for files, image in
                                  ((cls.files, cls.image), (cls.old_files, cls.base)))
        cls.art = json.loads((ART / 'art.json').read_text())

    def test_all_models_profiles_metadata_and_fixed_seeds(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        for slot, row in enumerate(self.prior['furniture']['imports']):
            old = int(row['profile_ram'], 16) - 0x80460000 - 8
            self.assertEqual(self.blob[ROWS + slot * 80:ROWS + (slot + 1) * 80],
                             self.old_blob[old:old + 80])
        for slot, (pilot, model, row) in enumerate(zip(CONSTRUCTION_PILOTS,
                self.art['objects'], self.report['construction']['imports'], strict=True), 2):
            index, item, vrom = furniture_slot(pilot.item)
            source = (ART / model['object_file']).read_bytes()
            self.assertEqual(self.blob[vrom - BLOB:vrom - BLOB + len(source)], source)
            self.assertEqual(row['object_sha256'], sha256(source))
            self.assertEqual(row['profile_ram'], f'{ROWS_RAM + slot * 80 + 8:08X}')
            expected = struct.pack('>HHI', index, item, 1) + native_profile(
                pilot, len(source), model['model_offsets'], vrom) + bytes(4)
            self.assertEqual(self.blob[ROWS + slot * 80:ROWS + (slot + 1) * 80], expected)
            self.assertEqual(struct.unpack_from('>I', self.blob, 0x5800 + index * 4)[0],
                             ROWS_RAM + slot * 80 + 8)
        self.assertEqual(self.blob[ITEMS:ITEMS + 96], self.old_blob[0x72A0:0x7300])
        prepared = (ROOT / 'build/v3-construction-items-01/items.bin').read_bytes()
        self.assertEqual(self.blob[ITEMS + 96:TABLE_END], prepared)
        self.assertEqual(len(self.blob[ITEMS:TABLE_END]), 320)
        self.assertFalse(self.report['construction']['catalogue_installed'])
        self.assertFalse(self.report['construction']['ordinary_stock_installed'])

    def test_exact_changed_regions_crc_and_all_existing_clothing_fixes(self):
        restored = bytearray(self.blob[:len(self.old_blob)])
        regions = [(4, 8), (0x20, 0xE0), (0xE8, 0xEC), (0xF8, 0xFC),
                   (0x5800, 0x6000), (0xF400, 0xF400 + 2976), (ROWS, TABLE_END)]
        for row in self.report['furniture']['imports']:
            at = 0x5800 + row['runtime_index'] * 4
            regions.append((at, at + 4))
        for row in self.report['furniture']['expanded_tables']['public_entries']:
            at = row['entry'] - 0x80460000
            regions.append((at, at + 8))
            self.assertEqual(self.blob[at:at + 8].hex(), row['after'])
        for start, end in regions:
            restored[start:end] = self.old_blob[start:end]
        self.assertEqual(restored, self.old_blob)
        # Exact actual-code difference: table high/low address and end pointer.
        before, after = self.old_blob[0xF400:0xFFC0], self.blob[0xF400:0xFFC0]
        changed = [i for i in range(0, len(before), 4) if before[i:i + 4] != after[i:i + 4]]
        self.assertEqual(changed, [0x838, 0x858, 0x860])
        for row in self.prior['aloha_outfits']['reader_fixes']:
            at = row['blob_offset']
            self.assertEqual(self.blob[at:at + 4].hex(), row['after'])
        self.assertEqual(struct.unpack_from('>I', self.blob, 0xE8)[0],
                         zlib.crc32(self.blob[0xF400:0xF400 + 2976]))
        self.assertEqual(struct.unpack_from('>I', self.blob, 0xF8)[0],
                         zlib.crc32(self.blob[PACKAGE:PACKAGE + PACKAGE_SIZE]))
        module = self.files[MODULE].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), 61))
        self.assertEqual(struct.unpack_from('>2I', self.image, 0x10), n64_checksum(self.image))
        restored_rom = bytearray(self.image)
        ranges = [(0x10, 0x18),
            (DMA_START + self.files[BLOB].index * 16 + 4, DMA_START + self.files[BLOB].index * 16 + 8),
            (self.files[BLOB].pstart, self.files[BLOB].pstart + len(self.blob)),
            (self.files[MODULE].pstart + STARTUP, self.files[MODULE].pstart + CONFIG + 16)]
        for start, end in ranges:
            restored_rom[start:end] = self.base[start:end]
        self.assertEqual(restored_rom, self.base)

    def test_actual_codec_accepts_existing_profile_and_rejects_new_saves_in_older_profile(self):
        before, after = self.old_blob[0x20:0xE0], self.blob[0x20:0xE0]
        expected = bytearray(before)
        for pilot in CONSTRUCTION_PILOTS:
            bit = (pilot.item - 0x3000) // 4
            self.assertFalse(expected[32 + bit // 8] & (1 << (bit & 7)))
            expected[32 + bit // 8] |= 1 << (bit & 7)
        self.assertEqual(after, expected)
        source = (ROOT / 'local/rc2-save-report-g3O4lU/test.flash').read_bytes()[:65536]
        with tempfile.TemporaryDirectory(prefix='v3-construction-codec-') as directory:
            library = Path(directory) / 'codec.so'
            subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_CLOTHING_PROFILE=1', str(ROOT / 'overlays/v3/save_codec.c'), '-o', str(library)],
                check=True, capture_output=True, text=True)
            codec = c.CDLL(str(library))
            codec.af_v3_save_check.argtypes = (c.c_void_p, c.c_uint, c.c_void_p, c.c_void_p)
            buffer = lambda data: (c.c_ubyte * len(data)).from_buffer_copy(data)
            for saved, wanted, result in ((before, after, 1), (after, after, 1), (after, before, -7)):
                packed = bytes(reference_pack(source, saved + bytes(STATE - PROFILE)))
                bank, profile, out = buffer(packed), buffer(wanted), buffer(b'\xA5' * STATE)
                self.assertEqual(codec.af_v3_save_check(bank, len(packed), profile, out), result)
                self.assertEqual(bytes(bank), packed)
                self.assertEqual(bytes(profile), wanted)
                self.assertEqual(bytes(out), wanted + bytes(STATE - PROFILE) if result == 1 else b'\xA5' * STATE)

    def test_later_registry_reservations_do_not_enable_missing_prior_cartridge_content(self):
        # The current composer must reject the old cartridge entirely; its
        # newer installed catalogue cannot authorise writes into an old build.
        with self.assertRaisesRegex(ValueError, 'pinned installed cartridge'):
            composer.catalogue(self.base, self.prior)


if __name__ == '__main__':
    unittest.main()
