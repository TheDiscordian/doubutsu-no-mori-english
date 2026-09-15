"""Complete installed tent wiring, retained resources, and optional selection."""
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
from aflib import DMA_START, DMA_END, by_vrom, sha256, n64_checksum
import v3_tent_model_runtime as r
import v3_tent_model as tent
import v3_optional_composition as composer
import v3_catalogue as catalogue
import v3_hra as hra
import v3_feng_shui as feng


class TentRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        output = ROOT / 'build/v3-tent-model-runtime-01'
        cls.image = (output / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((output / 'build.json').read_bytes())
        cls.base = (r.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((r.BASE / 'build.json').read_bytes())
        cls.files, cls.old = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.before = cls.files[r.BLOB].extract(cls.image), cls.old[r.BLOB].extract(cls.base)

    def test_complete_asset_callbacks_profile_item_and_selected_dependency(self):
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        asset, row, record, code, native, vtable, _ = r.prepared(rel, symbols)
        expected = bytearray(self.before[r.PACKAGE:r.PACKAGE + r.PACKAGE_SIZE])
        for at, data in ((tent.RAM - r.PACKAGE_RAM, code), (tent.VTABLE - r.PACKAGE_RAM, vtable),
                (r.ROWS - r.PACKAGE + r.slot(0x336C) * 80, struct.pack('>HHI', 1243, 0x336C, 1) + native + bytes(4)),
                (r.ITEMS - r.PACKAGE + r.slot(0x336C) * 32, record)):
            self.assertFalse(any(expected[at:at + len(data)]))
            expected[at:at + len(data)] = data
        self.assertEqual(self.blob[r.PACKAGE:r.PACKAGE + r.PACKAGE_SIZE], expected)
        self.assertEqual(self.blob[0x24E000:0x250000], asset + bytes(0x2000 - len(asset)))
        selected = bytearray(self.before[0x20:0xE0])
        selected[32 + r.slot(0x336C) // 8] |= 1 << (r.slot(0x336C) & 7)
        self.assertEqual(self.blob[0x20:0xE0], selected)
        self.assertEqual(self.blob[0x100:0xC000], self.before[0x100:0xC000])
        self.assertEqual(native[0x28:0x30], bytes(8))
        self.assertEqual(native[0x40:], struct.pack('>I', tent.VTABLE))
        self.assertTrue(self.report['tent_model']['imports'][0]['behaviour_installed'])
        self.assertEqual(self.report['furniture']['bank_pool'], self.prior['furniture']['bank_pool'])
        self.assertEqual(self.report['furniture_items']['active_metadata_rows'], 34)
        self.assertEqual(row['price'], 2550)

    def test_scoring_and_catalogue_without_invented_acquisition(self):
        for key, tool, width, value in (('hra', hra, 4, 'd4050600'), ('feng_shui', feng, 2, '0100')):
            data = self.files[tool.NEW_VROM].extract(self.image)
            expected = bytearray(self.old[tool.NEW_VROM].extract(self.base))
            at = self.report[key]['metadata_address'] - tool.RAM + 1243 * width
            self.assertEqual(expected[at:at + width], bytes.fromhex('fc000000') if width == 4 else bytes(2))
            expected[at:at + width] = bytes.fromhex(value)
            self.assertEqual(data, expected)
            self.assertEqual(sha256(data), self.report[key]['output_sha256'])
        cat = self.report['catalogue']
        self.assertEqual((cat['total_rows'], cat['clothing']['total_rows']), (470, 248))
        self.assertLessEqual(cat['conservative_pool_required'], cat['pool_reserved'])
        self.assertEqual(cat['pool_reserved'], self.prior['catalogue']['pool_reserved'])
        self.assertLessEqual(cat['linked_code']['bytes'], 0xE50)
        row = next(row for row in cat['imports'] if row['item_id'] == '336C')
        self.assertFalse(row['catalogue_orderable'])
        self.assertIsNone(row['ordinary_shop_list'])
        self.assertEqual(row['donor_acquisition_list'], 'ftr_listTent')
        self.assertEqual(row['donor_preview_scalar_hex'], '3f666666c0400000')
        self.assertFalse(row['preview_override'])
        self.assertIn('-DAF_V3_TENT_MODEL=1', cat['linked_code']['flags'])
        self.assertFalse(self.report['tent_model']['acquisition_installed'])
        self.assertEqual(self.report['shops'], self.prior['shops'])

    def test_rom_directory_checksums_and_only_intended_resources_change(self):
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        self.assertEqual(sha256(self.blob), self.report['blob_sha256'])
        self.assertEqual(struct.unpack_from('>2I', self.image, 16), n64_checksum(self.image))
        self.assertEqual(len(self.files), 3389)
        self.assertEqual(set(self.files), set(self.old))
        self.assertEqual(self.image[DMA_END - 16:DMA_END], bytes(16))
        self.assertEqual(struct.unpack_from('>4I', self.blob, 0xF0),
            (r.BLOB + r.PACKAGE, r.PACKAGE_SIZE,
             zlib.crc32(self.blob[r.PACKAGE:r.PACKAGE + r.PACKAGE_SIZE]), r.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>4I', self.files[r.MODULE].extract(self.image), r.CONFIG),
            (r.BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), 69))
        self.assertEqual(self.report['import_storage']['remaining_bytes'], r.END - r.BLOB - len(self.blob))
        self.assertEqual(self.report['tent_model']['additional_resident_bytes'], 0)
        allowed = {r.BLOB, r.MODULE, catalogue.VROM, catalogue.RELOC, catalogue.PARENT, hra.NEW_VROM, feng.NEW_VROM}
        restored = bytearray(self.image)
        restored[16:24] = self.base[16:24]
        for v in allowed:
            entry = self.files[v]
            a, b = entry.pstart, entry.pstart + entry.size
            restored[a:b] = self.base[a:b]
            at = DMA_START + entry.index * 16
            restored[at:at + 16] = self.base[at:at + 16]
        self.assertEqual(restored, self.base)
        for v, entry in self.files.items():
            if v not in allowed and v != 0x19D40:
                self.assertEqual(entry, self.old[v])
                self.assertEqual(entry.extract(self.image), self.old[v].extract(self.base), f'{v:08X}')

    def test_tent_only_composition_keeps_complete_behaviour_and_removes_other_imports(self):
        current, report = composer.inputs()
        catalog = composer.catalogue(current, report)
        key = 'GAFE01-r0/item/336C'
        selected = composer.resolve(catalog, [key])
        self.assertEqual(selected['required'], [])
        image, _, blob = composer.compose(current, report, catalog, selected)
        for k, row in catalog.items():
            self.assertEqual(int.from_bytes(blob[row['enable_offset']:row['enable_offset'] + row['enable_bytes']], 'big'), k == key)
        at = r.PACKAGE + tent.RAM - r.PACKAGE_RAM
        self.assertEqual(blob[at:at + tent.LIMIT - tent.RAM], self.blob[at:at + tent.LIMIT - tent.RAM])
        data = by_vrom(image)[catalogue.VROM].extract(image)
        at = self.report['catalogue']['code']['symbols']['af_v3_catalogue_order'] - catalogue.RAM
        self.assertEqual(data[at + 436 * 4:at + 437 * 4], struct.pack('>HH', 2267, 0))
        self.assertEqual(data[at + 437 * 4:at + 470 * 4], bytes(33 * 4))
        self.assertEqual(image, composer.compose(current, report, catalog,
                         composer.resolve(catalog, [key, key]))[0])


class TentCatalogueHost(unittest.TestCase):
    def test_sanitized_catalogue_reward_rule_rotations_and_neighbours(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-tent-catalogue-') as folder:
            binary = Path(folder) / 'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-DAF_V3_WESTERN_LARGE=1', '-DAF_V3_CAMPING_ITEMS=1', '-DAF_V3_TENT_MODEL=1',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_clothing_catalogue_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('non-orderable rewards, neighbouring IDs, and rotations pass', result.stdout)


if __name__ == '__main__':
    unittest.main()
