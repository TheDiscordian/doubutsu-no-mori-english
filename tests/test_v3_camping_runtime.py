"""Current camping cartridge, complete sparse rows, and catalogue behaviour."""
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

from tests.test_v3_camping import static
from aflib import DMA_START, DMA_END, by_vrom, sha256, n64_checksum
from v3_asset_loader import BLOB, CONFIG, MODULE
import v3_camping_runtime as c
from v3_furniture_art import CAMPING_PILOTS, native_profile
from v3_registry import furniture_slot
import v3_catalogue as catalogue
import v3_hra as hra
import v3_feng_shui as feng
import v3_shops as shops

OUTPUT = static.ROOT / 'build/v3-camping-runtime-01'


class CampingRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_bytes())
        cls.base = (c.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((c.BASE / 'build.json').read_bytes())
        cls.files, cls.old = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.before = cls.files[BLOB].extract(cls.image), cls.old[BLOB].extract(cls.base)

    def test_complete_art_rows_profile_flags_and_unchanged_resident_code(self):
        art = json.loads((c.ART / 'art.json').read_bytes())
        metadata = (static.ROOT / 'build/v3-camping-items-01/items.bin').read_bytes()
        expected = bytearray(self.before[c.PACKAGE:c.PACKAGE + c.PACKAGE_SIZE])
        profile = bytearray(self.before[0x20:0xE0])
        for n, (pilot, model, row) in enumerate(zip(CAMPING_PILOTS, art['objects'],
                self.report['camping']['imports'], strict=True)):
            index, item, vrom = furniture_slot(pilot.item)
            i = c.slot(item)
            asset = (c.ART / model['object_file']).read_bytes()
            self.assertEqual(self.blob[vrom - BLOB:vrom - BLOB + len(asset)], asset)
            self.assertEqual(self.blob[vrom - BLOB + len(asset):vrom - BLOB + 0x2000], bytes(0x2000 - len(asset)))
            native = native_profile(pilot, len(asset), model['model_offsets'], vrom)
            at = c.ROWS - c.PACKAGE + i * 80
            self.assertEqual(expected[at:at + 80], bytes(80))
            expected[at:at + 80] = struct.pack('>HHI', index, item, 1) + native + bytes(4)
            at = c.ITEMS - c.PACKAGE + i * 32
            self.assertEqual(expected[at:at + 32], bytes(32))
            expected[at:at + 32] = metadata[n * 32:(n + 1) * 32]
            profile[32 + i // 8] |= 1 << (i & 7)
            self.assertEqual(int(row['profile_ram'], 16), c.ROWS_RAM + i * 80 + 8)
            self.assertEqual(self.blob[0x5800 + index * 4:0x5804 + index * 4], bytes(4))
        self.assertEqual(self.blob[c.PACKAGE:c.PACKAGE + c.PACKAGE_SIZE], expected)
        self.assertEqual(self.blob[0x20:0xE0], profile)
        self.assertEqual(self.blob[0x100:0xC000], self.before[0x100:0xC000])
        self.assertEqual(self.blob[0xF400:0xFFA0], self.before[0xF400:0xFFA0])
        self.assertEqual(self.report['furniture']['bank_pool'], self.prior['furniture']['bank_pool'])
        self.assertEqual(self.report['furniture']['expanded_tables'], self.prior['furniture']['expanded_tables'])
        self.assertEqual(len(self.report['furniture']['imports']), 32)
        self.assertEqual(self.report['furniture_items']['active_metadata_rows'], 33)

    def test_exact_scoring_only_changes_and_no_fake_shop_acquisition(self):
        for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
            current = self.files[tool.NEW_VROM].extract(self.image)
            expected = bytearray(self.old[tool.NEW_VROM].extract(self.base))
            table = self.report[key]['metadata_address'] - tool.RAM
            for row in self.report['camping']['imports']:
                at = table + row['runtime_index'] * width
                self.assertEqual(expected[at:at + width], bytes.fromhex('fc000000') if width == 4 else bytes(2))
                expected[at:at + width] = bytes.fromhex(row['native_hra_hex'] if width == 4 else row['feng_hex'])
            self.assertEqual(current, expected)
            self.assertEqual(self.files[tool.NEW_RELOC], self.old[tool.NEW_RELOC])
            self.assertEqual(sha256(current), self.report[key]['output_sha256'])
        self.assertEqual(self.files[shops.VROM].extract(self.image), self.old[shops.VROM].extract(self.base))
        self.assertEqual(self.report['shops'], self.prior['shops'])
        self.assertFalse(self.report['camping']['acquisition_installed'])
        self.assertEqual(self.report['camping']['scoring_mapping']['points'], 412)
        self.assertEqual(self.report['hra']['birth_extension'], self.prior['hra']['birth_extension'])

    def test_full_catalogue_preview_rules_and_actual_memory_bound(self):
        cat = self.report['catalogue']
        self.assertEqual((cat['total_rows'], cat['clothing']['total_rows']), (469, 248))
        self.assertLessEqual(cat['conservative_pool_required'], cat['pool_reserved'])
        self.assertEqual(cat['pool_reserved'], self.prior['catalogue']['pool_reserved'])
        self.assertLessEqual(cat['linked_code']['bytes'], 0xE50)
        rows = {r['item_id']: r for r in cat['imports']}
        for pilot in CAMPING_PILOTS:
            row = rows[f'{pilot.item:04X}']
            self.assertFalse(row['catalogue_orderable'])
            self.assertIsNone(row['ordinary_shop_list'])
            self.assertEqual(row['donor_acquisition_list'], 'ftr_listTent')
            self.assertEqual(row['mode'], 0)
        self.assertEqual(rows['33A8']['donor_preview_mode'], 24)
        self.assertEqual(rows['33A8']['donor_preview_scalar_hex'], '3f59999ac0400000')
        data = self.files[catalogue.VROM].extract(self.image)
        table = cat['code']['symbols']['af_v3_catalogue_order'] - catalogue.RAM
        indices = list(struct.iter_unpack('>HH', data[table:table + 469 * 4]))
        imported = {1024 + furniture_slot(p.item)[0] for p in CAMPING_PILOTS}
        self.assertEqual([r for r in indices if r[0] in imported],
            [(2268, 0), (2281, 0), (2265, 0), (2279, 0), (2282, 0), (2284, 0), (2283, 0)])
        self.assertEqual(sha256(data), cat['output_sha256'])

    def test_cartridge_changes_directory_startup_crc_and_retained_resources(self):
        self.assertEqual(sha256(self.base), c.BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        self.assertEqual(sha256(self.blob), self.report['blob_sha256'])
        self.assertEqual(struct.unpack_from('>2I', self.image, 16), n64_checksum(self.image))
        self.assertEqual(len(self.files), 3389)
        self.assertEqual(set(self.files), set(self.old))
        self.assertEqual(self.image[DMA_END - 16:DMA_END], bytes(16))
        self.assertEqual(struct.unpack_from('>4I', self.blob, 0xF0),
            (BLOB + c.PACKAGE, c.PACKAGE_SIZE, zlib.crc32(self.blob[c.PACKAGE:c.PACKAGE + c.PACKAGE_SIZE]), c.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.image), CONFIG),
            (BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), c.ABI))
        self.assertEqual(self.report['import_storage']['remaining_bytes'], c.END - BLOB - len(self.blob))
        self.assertEqual(self.report['camping']['additional_resident_bytes'], 0)
        allowed = {BLOB, MODULE, catalogue.VROM, catalogue.RELOC, catalogue.PARENT, hra.NEW_VROM, feng.NEW_VROM}
        regions = [(16, 24)]
        for vrom in allowed:
            entry = self.files[vrom]
            regions.append((entry.pstart, entry.pstart + entry.size))
            at = DMA_START + entry.index * 16
            regions.append((at, at + 16))
        restored = bytearray(self.image)
        for start, end in regions:
            restored[start:end] = self.base[start:end]
        self.assertEqual(restored, self.base)
        for vrom, entry in self.files.items():
            if vrom not in allowed and vrom != 0x19D40:
                self.assertEqual(entry, self.old[vrom])
                self.assertEqual(entry.extract(self.image), self.old[vrom].extract(self.base), f'{vrom:08X}')


class CampingCatalogueHost(unittest.TestCase):
    def test_sanitized_current_catalogue_source_and_retained_rules(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-camping-catalogue-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_WESTERN_LARGE=1', '-DAF_V3_CAMPING_ITEMS=1',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(static.ROOT / 'tests/v3_clothing_catalogue_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('Camping exact bike preview', result.stdout)
            self.assertIn('clothing ownership', result.stdout)


if __name__ == '__main__':
    unittest.main()
