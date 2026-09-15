"""Installed Western models, dedicated bank lifetime, stock, and exact changes."""
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
from v3_furniture_art import WESTERN_PILOTS, native_profile
from v3_western_runtime import (ABI, ART, BASE, BASE_SHA, ITEMS, ITEMS_RAM, PACKAGE,
    PACKAGE_SIZE, ROWS, ROWS_RAM, TABLE_END, STATIC_COUNT, ITEM_COUNT)
from v3_registry import furniture_slot
import v3_furniture_banks as banks
import v3_furniture_runtime as furniture
import v3_catalogue as catalogue
import v3_hra as hra
import v3_hra_mail as mail
import v3_feng_shui as feng
import v3_shops as shops

OUTPUT = ROOT / 'build/v3-western-runtime-02'


class WesternRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((BASE / 'build.json').read_text())
        cls.files, cls.old_files = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.old_blob = cls.files[BLOB].extract(cls.image), cls.old_files[BLOB].extract(cls.base)

    def test_complete_models_profiles_moved_metadata_and_second_opaque_part(self):
        art = json.loads((ART / 'art.json').read_text())
        self.assertEqual(self.blob[ROWS:ROWS + 1200], self.old_blob[ROWS:ROWS + 1200])
        self.assertEqual(self.blob[ITEMS:ITEMS + 512], self.old_blob[0x7EA00:0x7EC00])
        self.assertEqual(self.blob[ITEMS + 512:TABLE_END], (ROOT / 'build/v3-western-items-01/items.bin').read_bytes())
        for slot, (pilot, model, row) in enumerate(zip(WESTERN_PILOTS,
                art['objects'], self.report['western']['imports'], strict=True), 15):
            index, item, vrom = furniture_slot(pilot.item)
            asset = (ART / model['object_file']).read_bytes()
            self.assertEqual(self.blob[vrom - BLOB:vrom - BLOB + len(asset)], asset)
            profile = native_profile(pilot, len(asset), model['model_offsets'], vrom)
            expected = struct.pack('>HHI', index, item, 1) + profile + bytes(4)
            self.assertEqual(self.blob[ROWS + slot * 80:ROWS + (slot + 1) * 80], expected)
            self.assertEqual(int(row['profile_ram'], 16), ROWS_RAM + slot * 80 + 8)
            self.assertEqual(struct.unpack_from('>I', self.blob, 0x5800 + index * 4)[0], int(row['profile_ram'], 16))
            self.assertLessEqual(len(asset), banks.BYTES)
            if item == 0x32BC:
                opaque0, opaque1, translucent0, translucent1 = struct.unpack_from('>4I', profile, 16)
                self.assertTrue(opaque0 and opaque1)
                self.assertNotEqual(opaque0, opaque1)
                self.assertEqual((translucent0, translucent1), (0, 0))
                self.assertGreater(len(asset), 0x1400)
        self.assertLessEqual(ROWS + STATIC_COUNT * 80, ITEMS)
        self.assertEqual((ITEMS_RAM, TABLE_END), (0x80481C00, ITEMS + ITEM_COUNT * 32))
        self.assertLess(TABLE_END, PACKAGE + PACKAGE_SIZE - 16)

    def test_bank_pool_hook_capacity_relocations_and_unchanged_native_teardown(self):
        pool = self.report['furniture']['bank_pool']
        self.assertEqual((pool['data'], pool['bank_bytes'], pool['banks']), (0x80500010, 0x2400, 100))
        self.assertEqual(pool['end'] - pool['start'], 921632)
        self.assertGreaterEqual(pool['start'], 0x80482000)
        self.assertLessEqual(pool['end'], 0x807DA800)
        self.assertEqual((pool['ordinary_heap_growth'], pool['object_arena_growth']), (0, 0))
        current = self.files[furniture.VROM].extract(self.image)
        source = self.old_files[furniture.VROM].extract(self.base)
        at = pool['hook']['address'] - furniture.RAM
        self.assertEqual(source[at:at + 20].hex(), pool['hook']['before'])
        self.assertEqual(current[at:at + 20].hex(), pool['hook']['after'])
        self.assertEqual(current[:at] + source[at:at + 20] + current[at + 20:], source)
        original = self.old_files[furniture.RELOC].extract(self.base)
        reloc = self.files[furniture.RELOC].extract(self.image)
        self.assertEqual((len(reloc), struct.unpack_from('>I', reloc, 16)[0]), (6208, 1397))
        rows = struct.unpack_from('>1401I', original, 20)
        retained = [r for r in rows if r not in pool['removed_relocations']]
        self.assertEqual(list(struct.unpack_from('>1397I', reloc, 20)), retained)
        self.assertEqual(reloc[-4:], original[-4:])
        self.assertLessEqual(self.report['furniture']['expanded_tables']['expanded_code']['bytes'], 2048)

    def test_complete_stock_routes_and_catalogue_capacity(self):
        cat = self.report['catalogue']
        self.assertEqual((cat['total_rows'], cat['clothing']['total_rows']), (459, 248))
        self.assertLessEqual(cat['conservative_pool_required'], cat['pool_reserved'])
        self.assertEqual(cat['pool_reserved'], self.prior['catalogue']['pool_reserved'])
        goods = self.files[shops.VROM].extract(self.image)
        old = self.old_files[shops.VROM].extract(self.base)
        pointers = struct.unpack_from('>12I', goods, self.report['shops']['table_offset'])
        previous_pointers = struct.unpack_from('>12I', old, self.prior['shops']['table_offset'])
        def values(resource, pointer):
            result, at = [], pointer & 0xFFFFFF
            while (item := struct.unpack_from('>H', resource, at)[0]):
                result.append(item); at += 2
                self.assertLess(at, len(resource))
            return result
        additions = {0: [0x32B4, 0x32C0], 1: [0x3328, 0x3330], 2: [0x32B0], 3: [0x32BC, 0x3334]}
        for group in range(11):
            previous = values(old, previous_pointers[group])
            expected = [i for i in previous if i < 0x3000] + sorted(
                [i for i in previous if i >= 0x3000] + additions.get(group, []))
            self.assertEqual(values(goods, pointers[group]), expected)
        rules = {r['item_id']: r for r in cat['imports']}
        for item in ('32BC', '3334'):
            self.assertTrue(rules[item]['catalogue_orderable'])
            self.assertIsNone(rules[item]['ordinary_shop_list'])
            self.assertEqual(rules[item]['donor_acquisition_list'], 'ftr_listEvent')

    def test_complete_scoring_and_letter_name_without_interior_padding(self):
        for key, tool, width, values in (
            ('hra', hra, 4, ('dc050400', 'dc050100', 'dc050600', 'dc050000', 'dc050200', 'dc050200', 'dc050600')),
            ('feng_shui', feng, 2, ('0000', '0000', '0000', '0000', '0400', '0000', '0000'))):
            current = self.files[tool.NEW_VROM].extract(self.image)
            restored = bytearray(self.old_files[tool.NEW_VROM].extract(self.base))
            table = self.report[key]['metadata_address'] - tool.RAM
            for row, value in zip(self.report['western']['imports'], values, strict=True):
                at = table + row['runtime_index'] * width
                restored[at:at + width] = bytes.fromhex(value)
            if key == 'hra':
                series = self.report['hra']['series']
                info, names = series['info_address'] - hra.RAM, series['names_address'] - hra.RAM
                restored[info + 165:info + 168] = bytes.fromhex('0200FF')
                restored[names + 550:names + 560] = b'western   '
            self.assertEqual(current, restored)
            self.assertEqual(self.files[tool.NEW_RELOC].extract(self.image), self.old_files[tool.NEW_RELOC].extract(self.base))
        source = self.old_files[mail.VROM].extract(self.base)
        data = self.files[mail.VROM].extract(self.image)
        table_end = 0xEF10 + 57 * 26
        expected = bytearray(source[:table_end] + b'western   western         ' + bytes(12))
        self.assertEqual(len(expected), 62720)
        for offset in mail.COUNTERS:
            before = struct.unpack_from('>I', source, offset)[0]
            struct.pack_into('>I', expected, offset, before & 0xFFFF0000 | (1520 if offset == 0x25F4 else 58))
        reloc = bytearray(source[62688:]); struct.pack_into('>I', reloc, 0, 62720)
        self.assertEqual(data, expected + reloc)
        self.assertEqual(self.report['hra']['birth_extension'], self.prior['hra']['birth_extension'])

    def test_exact_cartridge_changes_checksums_and_selected_dependencies(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        profile = bytearray(self.old_blob[0x20:0xE0])
        for pilot in WESTERN_PILOTS:
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
        regions = [(16, 24), (self.files[BLOB].pstart, self.files[BLOB].pstart + len(self.blob)),
            (self.files[MODULE].pstart, self.files[MODULE].pstart + self.files[MODULE].size),
            (self.files[catalogue.PARENT].pstart + catalogue.OWNER, self.files[catalogue.PARENT].pstart + catalogue.OWNER + 32)]
        for vrom in (furniture.VROM, furniture.RELOC):
            regions.append((self.files[vrom].pstart, self.files[vrom].pstart + self.files[vrom].size))
        at = self.files[CODE_VROM].pstart + shops.DESCRIPTOR - CODE_RAM
        regions.append((at, at + 12))
        for vrom in (BLOB, catalogue.VROM, catalogue.RELOC, hra.NEW_VROM, feng.NEW_VROM, shops.VROM, mail.VROM):
            at = DMA_START + self.files[vrom].index * 16
            regions.append((at, at + 16))
        restored = bytearray(self.image)
        for start, end in regions: restored[start:end] = self.base[start:end]
        self.assertEqual(restored, self.base)


if __name__ == '__main__': unittest.main()
