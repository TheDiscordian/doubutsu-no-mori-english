"""Current integrated garden objects, exact changed regions, and scoring rules."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, by_vrom, n64_checksum, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE
from v3_furniture_art import GARDEN_PILOTS, native_profile
from v3_garden_runtime import (ABI, ART, BASE, BASE_SHA, ITEMS, ITEMS_RAM, PACKAGE,
                               PACKAGE_SIZE, ROWS, ROWS_RAM, TABLE_END)
from v3_registry import furniture_slot
import v3_catalogue as catalogue
import v3_hra as hra
import v3_hra_mail as mail
import v3_feng_shui as feng
import v3_shops as shops

OUTPUT = ROOT / 'build/v3-garden-runtime-02'


class GardenRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((BASE / 'build.json').read_text())
        cls.files, cls.old_files = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.old_blob = cls.files[BLOB].extract(cls.image), cls.old_files[BLOB].extract(cls.base)

    def test_actual_models_profiles_fixed_seeds_and_all_item_records(self):
        art = json.loads((ART / 'art.json').read_text())
        self.assertEqual(self.blob[ROWS:ROWS + 720], self.old_blob[ROWS:ROWS + 720])
        self.assertEqual(self.blob[ITEMS:ITEMS + 320], self.old_blob[0x7E800:0x7E940])
        self.assertEqual(self.blob[ITEMS + 320:TABLE_END], (ROOT / 'build/v3-garden-items-01/items.bin').read_bytes())
        for slot, (pilot, model, row) in enumerate(zip(GARDEN_PILOTS,
                art['objects'], self.report['garden']['imports'], strict=True), 9):
            index, item, vrom = furniture_slot(pilot.item)
            data = (ART / model['object_file']).read_bytes()
            self.assertEqual(self.blob[vrom - BLOB:vrom - BLOB + len(data)], data)
            expected = struct.pack('>HHI', index, item, 1) + native_profile(
                pilot, len(data), model['model_offsets'], vrom) + bytes(4)
            self.assertEqual(self.blob[ROWS + slot * 80:ROWS + (slot + 1) * 80], expected)
            self.assertEqual(int(row['profile_ram'], 16), ROWS_RAM + slot * 80 + 8)
            self.assertEqual(struct.unpack_from('>I', self.blob, 0x5800 + index * 4)[0], int(row['profile_ram'], 16))
        self.assertEqual(ROWS + 15 * 80, 0x7E9B0)
        self.assertLessEqual(ROWS + 15 * 80, ITEMS)
        self.assertEqual(ITEMS_RAM, 0x80481A00)
        self.assertEqual(TABLE_END, ITEMS + 16 * 32)
        self.assertLess(TABLE_END, PACKAGE + PACKAGE_SIZE - 16)

    def test_complete_stock_and_catalogue_rules_and_capacity(self):
        cat = self.report['catalogue']
        data = self.files[catalogue.VROM].extract(self.image)
        at = cat['code']['symbols']['af_v3_catalogue_order'] - catalogue.RAM
        table = list(struct.iter_unpack('>HH', data[at:at + 452 * 4]))
        old = self.old_files[catalogue.VROM].extract(self.base)
        old_at = self.prior['catalogue']['code']['symbols']['af_v3_catalogue_order'] - catalogue.RAM
        self.assertEqual(data[at:at + 436 * 4], old[old_at:old_at + 436 * 4])
        self.assertEqual(len(set(i for i, _ in table)), 452)
        self.assertEqual([i for i, _ in table[436:]], [r['catalogue_index'] for r in cat['imports']])
        self.assertEqual(cat['row_capacity'], 753)
        self.assertLessEqual(cat['conservative_pool_required'], cat['pool_reserved'])
        self.assertEqual(cat['pool_reserved'], self.prior['catalogue']['pool_reserved'])
        a, b = cat['clothing']['table_address'] - catalogue.RAM, self.prior['catalogue']['clothing']['table_address'] - catalogue.RAM
        self.assertEqual(data[a:a + 496], old[b:b + 496])
        self.assertEqual(struct.unpack_from('>I', self.files[catalogue.RELOC].extract(self.image))[0], len(data))
        goods = self.files[shops.VROM].extract(self.image)
        old_goods = self.old_files[shops.VROM].extract(self.base)
        pointers = struct.unpack_from('>12I', goods, self.report['shops']['table_offset'])
        old_pointers = struct.unpack_from('>12I', old_goods, self.prior['shops']['table_offset'])
        def values(resource, pointer):
            result, at = [], pointer & 0xFFFFFF
            while (item := struct.unpack_from('>H', resource, at)[0]):
                result.append(item); at += 2
                self.assertLess(at, len(resource))
            return result
        additions = {0: [0x32A4], 1: [0x3268, 0x3290], 2: [0x3284], 5: [0x32A0]}
        for group in range(11):
            previous = values(old_goods, old_pointers[group])
            expected = [i for i in previous if i < 0x3000] + sorted(
                [i for i in previous if i >= 0x3000] + additions.get(group, []))
            self.assertEqual(values(goods, pointers[group]), expected)
        rules = {r['item_id']: r for r in cat['imports']}
        self.assertTrue(rules['32A0']['catalogue_orderable'])
        self.assertFalse(rules['3294']['catalogue_orderable'])
        self.assertFalse(self.report['garden']['post_office_reward_installed'])

    def test_all_scoring_bits_and_complete_letter_extension(self):
        values = ('e0058200', 'e0058400', 'e0050200', 'd405e600', 'e0054f00', 'e0050000')
        colours = ('0000', '0000', '0001', '0500', '0001', '0001')
        for key, tool, width, expected in (('hra', hra, 4, values), ('feng_shui', feng, 2, colours)):
            current = self.files[tool.NEW_VROM].extract(self.image)
            restored = bytearray(self.old_files[tool.NEW_VROM].extract(self.base))
            at = self.report[key]['metadata_address'] - tool.RAM
            for row, value in zip(self.report['garden']['imports'], expected, strict=True):
                index = row['runtime_index']
                restored[at + index * width:at + (index + 1) * width] = bytes.fromhex(value)
            if key == 'hra':
                s = self.report['hra']['series']
                i, n = s['info_address'] - hra.RAM, s['names_address'] - hra.RAM
                restored[i + 56 * 3:i + 57 * 3] = bytes.fromhex('0200FF')
                restored[n + 560:n + 570] = b'backyard  '
            self.assertEqual(current, restored)
            self.assertEqual(self.files[tool.NEW_RELOC].extract(self.image), self.old_files[tool.NEW_RELOC].extract(self.base))
        source = self.old_files[mail.VROM].extract(self.base)
        data = self.files[mail.VROM].extract(self.image)
        expected = bytearray(source[:62656] + b'backyard  backyard        ' + bytes(6))
        for offset in mail.COUNTERS:
            before = struct.unpack_from('>I', source, offset)[0]
            struct.pack_into('>I', expected, offset, before & 0xFFFF0000 | (1488 if offset == 0x25F4 else 57))
        reloc = bytearray(source[62656:]); struct.pack_into('>I', reloc, 0, 62688)
        self.assertEqual(data, expected + reloc)
        self.assertEqual(self.report['hra']['birth_extension'], self.prior['hra']['birth_extension'])

    def test_exact_cartridge_scope_checksums_and_selected_profile(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        profile = bytearray(self.old_blob[0x20:0xE0])
        for pilot in GARDEN_PILOTS:
            bit = (pilot.item - 0x3000) // 4
            self.assertFalse(profile[32 + bit // 8] & (1 << (bit & 7)))
            profile[32 + bit // 8] |= 1 << (bit & 7)
        self.assertEqual(self.blob[0x20:0xE0], profile)
        self.assertEqual(struct.unpack_from('>I', self.blob, 0xF8)[0], zlib.crc32(self.blob[PACKAGE:PACKAGE + PACKAGE_SIZE]))
        self.assertEqual(struct.unpack_from('>I', self.blob, 0xE8)[0], zlib.crc32(self.blob[0xF400:0xFFA0]))
        module = self.files[MODULE].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG), (BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), ABI))
        self.assertEqual(struct.unpack_from('>2I', self.image, 16), n64_checksum(self.image))
        self.assertEqual([i for i in range(0, 2972, 4) if self.blob[0xF400+i:0xF404+i] != self.old_blob[0xF400+i:0xF404+i]], [0x858, 0x860])
        restored = bytearray(self.image)
        regions = [(16, 24), (self.files[BLOB].pstart, self.files[BLOB].pstart + len(self.blob)),
            (self.files[MODULE].pstart, self.files[MODULE].pstart + self.files[MODULE].size),
            (self.files[catalogue.PARENT].pstart + catalogue.OWNER, self.files[catalogue.PARENT].pstart + catalogue.OWNER + 32)]
        at = self.files[CODE_VROM].pstart + shops.DESCRIPTOR - CODE_RAM
        regions.append((at, at + 12))
        for vrom in (BLOB, catalogue.VROM, catalogue.RELOC, hra.NEW_VROM, feng.NEW_VROM, shops.VROM, mail.VROM):
            at = DMA_START + self.files[vrom].index * 16
            regions.append((at, at + 16))
        for start, end in regions: restored[start:end] = self.base[start:end]
        self.assertEqual(restored, self.base)


if __name__ == '__main__': unittest.main()
