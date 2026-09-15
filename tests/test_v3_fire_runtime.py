"""Installed complete fire resources, bounded readers, and deterministic selection."""
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
import zlib

from tests.test_v3_furniture_art import ROOT
from aflib import DMA_START, DMA_END, by_vrom, sha256, n64_checksum
import v3_fire_runtime as r
import v3_fire as fire
import v3_optional_composition as composer
import v3_catalogue as catalogue
import v3_hra as hra
import v3_feng_shui as feng


class FireRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.report = composer.inputs()
        cls.base = (r.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((r.BASE / 'build.json').read_bytes())
        cls.files, cls.old = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.before = cls.files[r.BLOB].extract(cls.image), cls.old[r.BLOB].extract(cls.base)

    def test_complete_fire_assets_code_profiles_and_item_rows(self):
        assets, details = fire.asset_contract((ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        callbacks = json.loads((r.CALLBACKS / 'callbacks.json').read_bytes())
        code = (r.CALLBACKS / 'code/code.bin').read_bytes()
        profiles = fire.profiles(callbacks['proposed_objects_vrom'], code, callbacks['code'])
        at = r.PACKAGE + fire.RAM - r.PACKAGE_RAM
        self.assertEqual(self.blob[at:at + len(code)], code)
        expected = bytearray(self.before[0x20:0xE0])
        for n, (asset, row, (native, table)) in enumerate(zip(assets, details, profiles)):
            item = 0x335C + n * 4; i = r.slot(item)
            at = callbacks['proposed_objects_vrom'][n] - r.BLOB
            self.assertEqual(self.blob[at:at + 0x2000], asset + bytes(0x2000 - len(asset)))
            at = r.PACKAGE + callbacks['vtables_ram'][n] - r.PACKAGE_RAM
            self.assertEqual(self.blob[at:at + 20], table)
            self.assertEqual(self.blob[r.ROWS + i * 80:r.ROWS + (i + 1) * 80],
                struct.pack('>HHI', 1239 + n, item, 1) + native + bytes(4))
            record = struct.pack('>HHHBB', 1239 + n, item, row['price'], 2 if n else 0, 1) + row['name'].encode().ljust(16, b' ') + bytes(8)
            self.assertEqual(self.blob[r.ITEMS + i * 32:r.ITEMS + (i + 1) * 32], record)
            expected[32 + i // 8] |= 1 << (i & 7)
        self.assertEqual(self.blob[0x20:0xE0], expected)
        for at in (r.PACKAGE + 0x10FF0, r.PACKAGE + r.PACKAGE_SIZE - 16):
            self.assertEqual(self.blob[at:at + 16], bytes.fromhex('AFACC0DE') * 4)
        # The tent callback and its complete palette/model remain unchanged.
        at = r.PACKAGE + 0x10400
        self.assertEqual(self.blob[at:at + 0x400], self.before[at:at + 0x400])
        self.assertEqual(self.blob[0x24E000:0x250000], self.before[0x24E000:0x250000])

    def test_current_dma_and_four_cell_bridges(self):
        helper = self.report['furniture']['expanded_tables']
        code = helper['expanded_code']
        self.assertLessEqual(code['bytes'], 2048)
        self.assertEqual(sha256(self.blob[0x5800:0x5800 + code['bytes']]), code['sha256'])
        for row in helper['public_entries']:
            at = row['entry'] - 0x80460000
            self.assertEqual(self.blob[at:at + 8], struct.pack('>II', r.jump(code['symbols'][row['name']]), 0))
        item = self.report['import_storage']['item_code']
        self.assertEqual(item['bytes'], 1020)
        at = r.PACKAGE + 0x10000
        self.assertEqual(sha256(self.blob[at:at + item['bytes']]), item['sha256'])
        extra = self.report['clothing']['save_extension']
        for row in extra['item_dispatch']:
            at = 0xF400 + row['entry'] - 0x8046D000
            self.assertEqual(self.blob[at:at + 8], struct.pack('>II', r.jump(item['symbols'][row['name']]), 0))
        data = self.blob[0xF400:0xF400 + extra['resource_bytes']]
        self.assertEqual(sha256(data), extra['resource_sha256'])
        self.assertEqual(struct.unpack_from('>I', self.blob, 0xE8)[0], zlib.crc32(data))

    def test_scoring_catalogue_and_retained_audio(self):
        for key, tool, width, value in (('hra', hra, 4, 'd4050600'), ('feng_shui', feng, 2, '0000')):
            data = self.files[tool.NEW_VROM].extract(self.image)
            expected = bytearray(self.old[tool.NEW_VROM].extract(self.base))
            for index in (1239, 1240):
                at = self.report[key]['metadata_address'] - tool.RAM + index * width
                expected[at:at + width] = bytes.fromhex(value)
            self.assertEqual(data, expected)
        cat = self.report['catalogue']
        self.assertEqual((cat['total_rows'], cat['clothing']['total_rows']), (472, 248))
        self.assertLessEqual(cat['conservative_pool_required'], cat['pool_reserved'])
        self.assertEqual(cat['pool_reserved'], self.prior['catalogue']['pool_reserved'])
        for item in ('335C', '3360'):
            row = next(r for r in cat['imports'] if r['item_id'] == item)
            self.assertFalse(row['catalogue_orderable'])
            self.assertIsNone(row['ordinary_shop_list'])
            self.assertEqual(row['donor_acquisition_list'], 'ftr_listTent')
            self.assertEqual(row['preview_override'], item == '3360')
        for row in self.report['fire_sound']['resources'].values():
            at, size = row['physical'], row['bytes']
            self.assertEqual(self.image[at:at + size], self.base[at:at + size])
        self.assertEqual(self.report['shops'], self.prior['shops'])
        self.assertFalse(self.report['fire']['acquisition_installed'])

    def test_complete_cartridge_checksums_directory_and_only_intended_changes(self):
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
            (r.BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), 70))
        allowed = {r.BLOB, r.MODULE, r.ROOM, catalogue.VROM, catalogue.RELOC, catalogue.PARENT, hra.NEW_VROM, feng.NEW_VROM}
        restored = bytearray(self.image); restored[16:24] = self.base[16:24]
        for v in allowed:
            entry = self.files[v]; a, b = entry.pstart, entry.pstart + entry.size
            restored[a:b] = self.base[a:b]
            at = DMA_START + entry.index * 16
            restored[at:at + 16] = self.base[at:at + 16]
        self.assertEqual(restored, self.base)

    def test_sanitized_actual_callback_dma_and_catalogue_rules(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-fire-readers-') as folder:
            for name, flags in (('v3_callback_furniture_dma_test', ['AF_V3_FIRE=1']),
                ('v3_clothing_catalogue_test', ['AF_V3_WESTERN_LARGE=1', 'AF_V3_CAMPING_ITEMS=1', 'AF_V3_TENT_MODEL=1', 'AF_V3_FIRE=1'])):
                binary = Path(folder) / name
                result = subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', *['-D' + f for f in flags],
                    str(ROOT / 'tests' / (name + '.c')), '-o', str(binary)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_both_and_individual_fire_composition_retains_complete_behaviour(self):
        catalog = composer.catalogue(self.image, self.report)
        for chosen in (['GAFE01-r0/item/335C'], ['GAFE01-r0/item/3360'],
                       ['GAFE01-r0/item/335C', 'GAFE01-r0/item/3360']):
            selection = composer.resolve(catalog, chosen)
            self.assertEqual(selection['required'], [])
            image, _, blob = composer.compose(self.image, self.report, catalog, selection)
            for key, row in catalog.items():
                self.assertEqual(int.from_bytes(blob[row['enable_offset']:row['enable_offset'] + row['enable_bytes']], 'big'), key in chosen)
            at = r.PACKAGE + fire.RAM - r.PACKAGE_RAM
            self.assertEqual(blob[at:at + fire.LIMIT - fire.RAM], self.blob[at:at + fire.LIMIT - fire.RAM])
            self.assertEqual(image, composer.compose(self.image, self.report, catalog,
                composer.resolve(catalog, list(reversed(chosen))))[0])


if __name__ == '__main__': unittest.main()
