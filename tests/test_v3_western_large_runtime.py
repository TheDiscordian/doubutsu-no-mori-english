"""Current full-sized Western cartridge, relocated package, and stable dispatch."""
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
from aflib import CODE_RAM, CODE_VROM, DMA_START, by_vrom, n64_checksum, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP
from v3_western_large_runtime import (ABI, ART, BASE, BASE_SHA, ITEMS, ITEMS_RAM,
    PACKAGE, PACKAGE_RAM, PACKAGE_SIZE, ROWS, ROWS_RAM, STATIC_COUNT, TABLE_END, HELPER)
from v3_furniture_art import LARGE_WESTERN_PILOTS, native_profile
from v3_registry import furniture_slot
import v3_catalogue as catalogue
import v3_feng_shui as feng
import v3_hra as hra
import v3_shops as shops

OUTPUT = ROOT / 'build/v3-western-large-runtime-01'


class LargeWesternRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_bytes())
        cls.base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((BASE / 'build.json').read_bytes())
        cls.files, cls.old_files = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.old_blob = cls.files[BLOB].extract(cls.image), cls.old_files[BLOB].extract(cls.base)

    def test_all_new_models_and_complete_relocated_profiles_and_items(self):
        self.assertEqual(self.blob[ROWS:ROWS + 22 * 80], self.old_blob[0x7E500:0x7EBE0])
        self.assertEqual(self.blob[ITEMS:ITEMS + 23 * 32], self.old_blob[0x7EC00:0x7EEE0])
        self.assertEqual(self.blob[ITEMS + 23 * 32:TABLE_END],
            (ROOT / 'build/v3-western-large-items-01/items.bin').read_bytes())
        art = json.loads((ART / 'art.json').read_bytes())
        for slot, (pilot, model, row) in enumerate(zip(LARGE_WESTERN_PILOTS,
                art['objects'], self.report['western_large']['imports'], strict=True), 22):
            index, item, vrom = furniture_slot(pilot.item)
            asset = (ART / model['object_file']).read_bytes()
            self.assertEqual(self.blob[vrom - BLOB:vrom - BLOB + len(asset)], asset)
            profile = native_profile(pilot, len(asset), model['model_offsets'], vrom)
            self.assertEqual(self.blob[ROWS + slot * 80:ROWS + (slot + 1) * 80],
                struct.pack('>HHI', index, item, 1) + profile + bytes(4))
            self.assertEqual(profile[56:58], bytes((3, 1)))
            self.assertEqual(row['footprint'], '1x2')
        for slot, row in enumerate(self.report['furniture']['imports']):
            self.assertEqual(int(row['profile_ram'], 16), ROWS_RAM + slot * 80 + 8)
            self.assertEqual(struct.unpack_from('>I', self.blob, 0x5800 + row['runtime_index'] * 4)[0],
                             int(row['profile_ram'], 16))
        self.assertEqual(STATIC_COUNT, 25)
        self.assertLessEqual(ROWS + STATIC_COUNT * 80, ITEMS)
        self.assertLessEqual(TABLE_END, HELPER)
        self.assertLessEqual(PACKAGE_RAM + PACKAGE_SIZE, self.report['furniture']['bank_pool']['start'])

    def test_startup_descriptors_caches_code_and_retained_save_functions(self):
        package = self.blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
        self.assertEqual(struct.unpack_from('>4I', package), (0x41464133, 1, PACKAGE_SIZE, 20))
        self.assertEqual(package[-16:], bytes.fromhex('AFACC0DE') * 4)
        self.assertEqual(struct.unpack_from('>4I', self.blob, 0xF0),
            (BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM))
        # The old resident code, melodies, and accessory data retain their RAM
        # positions. Only the complete package's size header changes there.
        retained = bytearray(package[:0xF000])
        struct.pack_into('>I', retained, 8, 0xF000)
        self.assertEqual(retained, self.old_blob[0x70000:0x7F000])
        item_code = (OUTPUT / 'items_large/code.bin').read_bytes()
        self.assertEqual(len(item_code), 988)
        self.assertEqual(self.blob[HELPER:HELPER + len(item_code)], item_code)
        extra = bytearray(self.blob[0xF400:0xFFA0])
        for row in self.report['western_large']['item_dispatch']:
            at = row['entry'] - 0x8046D000
            self.assertEqual(extra[at:at + 8].hex(), row['after'])
            self.assertEqual(struct.unpack_from('>2I', extra, at),
                (0x08000000 | (row['target'] >> 2 & 0x3FFFFFF), 0))
            self.assertGreaterEqual(row['target'], 0x80483000)
            self.assertLess(row['target'], 0x80483000 + len(item_code))
            extra[at:at + 8] = bytes.fromhex(row['before'])
        self.assertEqual(extra, self.old_blob[0xF400:0xFFA0])
        self.assertEqual(self.report['clothing']['save_extension']['public_entries'],
                         self.prior['clothing']['save_extension']['public_entries'])
        self.assertEqual(struct.unpack_from('>I', self.blob, 0xE8)[0], zlib.crc32(self.blob[0xF400:0xFFA0]))
        startup = (OUTPUT / 'startup/code.bin').read_bytes()
        module = self.files[MODULE].extract(self.image)
        self.assertEqual(module[STARTUP:STARTUP + len(startup)], startup)
        self.assertLessEqual(len(startup), CONFIG - STARTUP)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
            (BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), ABI))

    def test_stock_catalogue_scoring_and_retained_bank_owner(self):
        cat = self.report['catalogue']
        self.assertEqual((cat['total_rows'], cat['clothing']['total_rows']), (462, 248))
        self.assertEqual((cat['conservative_pool_required'], cat['pool_reserved']), (280128, 280704))
        self.assertEqual(cat['linked_code']['bytes'], 3280)
        self.assertEqual(self.report['furniture']['bank_pool'], self.prior['furniture']['bank_pool'])
        self.assertEqual(self.report['furniture']['expanded_tables']['expanded_code']['symbols'],
                         self.prior['furniture']['expanded_tables']['expanded_code']['symbols'])
        for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
            current = self.files[tool.NEW_VROM].extract(self.image)
            expected = bytearray(self.old_files[tool.NEW_VROM].extract(self.base))
            at = self.report[key]['metadata_address'] - tool.RAM
            for row in self.report['western_large']['imports']:
                start = at + row['runtime_index'] * width
                expected[start:start + width] = bytes.fromhex(row['native_hra_hex'] if width == 4 else row['feng_hex'])
            self.assertEqual(current, expected)
            self.assertEqual(self.files[tool.NEW_RELOC].extract(self.image), self.old_files[tool.NEW_RELOC].extract(self.base))
            if width == 4:
                self.assertEqual(sum(current[at + i * 4] >> 2 == 55 for i in range(2051)), 10)
        new_stock = {r['item_id']: r['group'] for r in self.report['shops']['imports']}
        self.assertEqual({key: new_stock[key] for key in ('32C4', '32D4', '32D8')},
                         {'32C4': 1, '32D4': 5, '32D8': 2})

    def test_exact_cartridge_change_ranges_checksums_and_selected_dependencies(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        self.assertEqual(len(self.blob), 0x1F44F0)
        self.assertLess(len(self.blob), 0x200000)
        self.assertEqual(struct.unpack_from('>2I', self.image, 16), n64_checksum(self.image))
        profile = bytearray(self.old_blob[0x20:0xE0])
        for pilot in LARGE_WESTERN_PILOTS:
            bit = (pilot.item - 0x3000) // 4
            self.assertFalse(profile[32 + bit // 8] & (1 << (bit & 7)))
            profile[32 + bit // 8] |= 1 << (bit & 7)
        self.assertEqual(self.blob[0x20:0xE0], profile)
        regions = [(16, 24), (self.files[BLOB].pstart, self.files[BLOB].pstart + len(self.blob)),
            (self.files[MODULE].pstart, self.files[MODULE].pstart + self.files[MODULE].size),
            (self.files[catalogue.PARENT].pstart + catalogue.OWNER,
             self.files[catalogue.PARENT].pstart + catalogue.OWNER + 32)]
        at = self.files[CODE_VROM].pstart + shops.DESCRIPTOR - CODE_RAM
        regions.append((at, at + 12))
        for vrom in (BLOB, catalogue.VROM, catalogue.RELOC, hra.NEW_VROM, feng.NEW_VROM, shops.VROM):
            at = DMA_START + self.files[vrom].index * 16
            regions.append((at, at + 16))
        restored = bytearray(self.image)
        for start, end in regions: restored[start:end] = self.base[start:end]
        self.assertEqual(restored, self.base)

    def test_sanitized_new_package_startup_checks_and_instruction_cache_range(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-large-startup-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                f'-DAF_V3_ABI={ABI}', '-DAF_V3_WESTERN_LARGE=1',
                f'-DAF_V3_ACCESSORY_VROM={BLOB + PACKAGE}', f'-DAF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_accessory_startup_test.c'), str(ROOT / 'runtime/crc32.c'),
                '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('accessory startup guards, DMA, CRC, caches, and low-memory path pass', result.stdout)


if __name__ == '__main__': unittest.main()
