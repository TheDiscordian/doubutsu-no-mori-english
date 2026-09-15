"""Changed school-desk cartridge paths and independent optional profiles."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, sha256, n64_checksum
from gc_names import symbol_data
from v3_furniture_art import SCHOOL_DESKS, native_profile
import v3_school_desks_runtime as t
import v3_optional_composition as composer
import v3_catalogue as catalogue
import v3_hra as hra
import v3_feng_shui as feng
import v3_shops as shops


class SchoolDeskRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.report = composer.inputs()
        cls.base = (t.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((t.BASE / 'build.json').read_bytes())
        cls.files, cls.old = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob, cls.before = cls.files[t.BLOB].extract(cls.image), cls.old[t.BLOB].extract(cls.base)
        cls.rows = cls.report['school_desks']['imports']

    def test_complete_assets_profiles_only_new_sparse_rows_and_lamp_retained(self):
        art = json.loads((t.ART / 'art.json').read_bytes())
        metadata = (ROOT / 'build/v3-school-desks-items-01/items.bin').read_bytes()
        expected = bytearray(self.before[t.PACKAGE:t.PACKAGE + t.PACKAGE_SIZE])
        profile = bytearray(self.before[0x20:0xE0])
        for n, (pilot, model, row) in enumerate(zip(SCHOOL_DESKS, art['objects'], self.rows, strict=True)):
            index, item, vrom = t.furniture_slot(pilot.item)
            i = t.slot(item)
            asset = (t.ART / model['object_file']).read_bytes()
            self.assertEqual(self.blob[vrom - t.BLOB:vrom - t.BLOB + len(asset)], asset)
            self.assertEqual(self.blob[vrom - t.BLOB + len(asset):vrom - t.BLOB + 0x1000], bytes(0x1000 - len(asset)))
            native = native_profile(pilot, len(asset), model['model_offsets'], vrom)
            self.assertEqual(native[60], int(item != 0x3220))
            at = t.ROWS - t.PACKAGE + i * 80
            self.assertEqual(expected[at:at + 80], bytes(80))
            expected[at:at + 80] = struct.pack('>HHI', index, item, 1) + native + bytes(4)
            at = t.ITEMS - t.PACKAGE + i * 32
            self.assertEqual(expected[at:at + 32], bytes(32))
            expected[at:at + 32] = metadata[n * 32:(n + 1) * 32]
            profile[32 + i // 8] |= 1 << (i & 7)
            self.assertEqual(int(row['profile_ram'], 16), t.ROWS_RAM + i * 80 + 8)
        self.assertEqual(self.blob[t.PACKAGE:t.PACKAGE + t.PACKAGE_SIZE], expected)
        self.assertEqual(self.blob[0x20:0xE0], profile)
        self.assertEqual(self.blob[0x100:0xC000], self.before[0x100:0xC000])
        self.assertEqual(self.blob[0x2A1080:0x2A4080], self.before[0x2A1080:0x2A4080])
        self.assertEqual(self.blob[0xE0:0xF0], self.before[0xE0:0xF0])
        self.assertEqual(self.report['furniture']['expanded_tables'], self.prior['furniture']['expanded_tables'])
        self.assertEqual(self.report['import_storage']['item_code'], self.prior['import_storage']['item_code'])
        self.assertEqual(self.report['furniture_items']['active_metadata_rows'], 39)

    def test_only_three_scoring_rows_change_and_native_school_definition_stays(self):
        for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
            current = self.files[tool.NEW_VROM].extract(self.image)
            expected = bytearray(self.old[tool.NEW_VROM].extract(self.base))
            table = self.report[key]['metadata_address'] - tool.RAM
            for row in self.rows:
                at = table + row['runtime_index'] * width
                self.assertEqual(expected[at:at + width], bytes.fromhex('fc000000') if width == 4 else bytes(2))
                expected[at:at + width] = bytes.fromhex(row['native_hra_hex'] if width == 4 else row['feng_hex'])
            self.assertEqual(current, expected)
            self.assertEqual(sha256(current), self.report[key]['output_sha256'])
        self.assertEqual(self.report['hra']['series'], self.prior['hra']['series'])

    def test_stock_lists_retain_every_prior_item_and_catalogue_uses_official_order(self):
        def groups(files, image, report):
            data = files[shops.VROM].extract(image)
            pointers = struct.unpack_from('>12I', data, report['shops']['table_offset'])
            result = []
            for pointer in pointers[:-1]:
                at, values = pointer & 0xFFFFFF, []
                while int.from_bytes(data[at:at + 2], 'big'):
                    values.append(int.from_bytes(data[at:at + 2], 'big')); at += 2
                result.append(values)
            return result
        old, current = groups(self.old, self.base, self.prior), groups(self.files, self.image, self.report)
        ids = {0x3200, 0x3204, 0x3220}
        self.assertEqual([[i for i in group if i not in ids] for group in current], old)
        self.assertEqual([[i for i in group if i in ids] for group in current],
                         [[0x3200], [0x3204, 0x3220]] + [[] for _ in range(9)])
        cat = self.report['catalogue']
        self.assertEqual((cat['total_rows'], cat['clothing']['total_rows']), (475, 248))
        self.assertLessEqual(cat['conservative_pool_required'], cat['pool_reserved'])
        rows = [r for r in cat['imports'] if int(r['item_id'], 16) in ids]
        self.assertEqual([(r['item_id'], r['donor_position'], r['mode']) for r in rows],
                         [('3200', 237, 0), ('3204', 238, 0), ('3220', 243, 0)])
        self.assertTrue(all(r['catalogue_orderable'] for r in rows))

    def test_single_desk_selection_retains_fixed_id_and_excludes_other_school_scores(self):
        catalog = composer.catalogue(self.image, self.report)
        selection = composer.resolve(catalog, ['GAFE01-r0/item/3204'])
        self.assertEqual(selection['required'], [])
        self.assertEqual(selection['enabled'], ['GAFE01-r0/item/3204'])
        image, _, blob = composer.compose(self.image, self.report, catalog, selection)
        files = by_vrom(image)
        score = files[hra.NEW_VROM].extract(image)
        table = self.report['hra']['metadata_address'] - hra.RAM
        self.assertEqual(sum(score[table + i * 4] >> 2 == 19 for i in range(2051)), 15)
        for row in self.rows:
            item, index = int(row['item_id'], 16), row['runtime_index']
            active = item == 0x3204
            self.assertEqual(int.from_bytes(blob[t.ROWS + t.slot(item) * 80 + 4:t.ROWS + t.slot(item) * 80 + 8], 'big'), active)
            self.assertEqual(score[table + index * 4:table + index * 4 + 4],
                             bytes.fromhex(row['native_hra_hex'] if active else 'fc000000'))
        writes, selected = composer.catalogue_selection(self.image, self.report, set(selection['enabled']))
        self.assertTrue(writes)
        self.assertEqual(selected['total_rows'], 437)

    def test_cartridge_directory_checksums_and_only_reviewed_resource_changes(self):
        self.assertEqual(sha256(self.base), t.BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        self.assertEqual(sha256(self.blob), self.report['blob_sha256'])
        self.assertEqual(struct.unpack_from('>2I', self.image, 16), n64_checksum(self.image))
        self.assertEqual(set(self.files), set(self.old))
        self.assertEqual(len(self.files), 3389)
        self.assertEqual(self.image[DMA_END - 16:DMA_END], bytes(16))
        self.assertEqual(struct.unpack_from('>4I', self.blob, 0xF0),
            (t.BLOB + t.PACKAGE, t.PACKAGE_SIZE, zlib.crc32(self.blob[t.PACKAGE:t.PACKAGE+t.PACKAGE_SIZE]), t.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>4I', self.files[t.MODULE].extract(self.image), t.CONFIG),
            (t.BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), 84))
        allowed = {t.BLOB, t.MODULE, CODE_VROM, catalogue.VROM, catalogue.RELOC,
                   catalogue.PARENT, hra.NEW_VROM, feng.NEW_VROM, shops.VROM}
        ranges = [(16, 24)]
        for vrom in allowed:
            entry = self.files[vrom]
            ranges.append((entry.pstart, entry.pstart + entry.size))
            at = DMA_START + entry.index * 16
            ranges.append((at, at + 16))
        restored = bytearray(self.image)
        for start, end in ranges: restored[start:end] = self.base[start:end]
        self.assertEqual(restored, self.base)
        # Main code changes only the existing stock-resource descriptor.
        code = bytearray(self.files[CODE_VROM].extract(self.image))
        old = self.old[CODE_VROM].extract(self.base); at = shops.DESCRIPTOR - CODE_RAM
        code[at:at + 12] = old[at:at + 12]
        self.assertEqual(code, old)

    def test_native_seat_reader_direction_table_and_all_rotated_two_cell_shapes(self):
        room = self.files[0x82D7F0].extract(self.image); ram = 0x80936710
        self.assertEqual(sha256(room[0x8093FF64-ram:0x80940304-ram]),
                         '890868c570e79ab84c366e24616fadd226b9265cba6f65a6fb4dc5c4794c8ee3')
        self.assertEqual(sha256(room[0x80940378-ram:0x80940498-ram]),
                         'df06bc1e350e243cd781a195123aac4fe81dd1fe99fe59cc6cd77c5c8a2826ac')
        self.assertEqual(sha256(room[0x8094CFF8-ram:0x8094D028-ram]),
                         'f1f6244d7eee9d33c7a892f09e7a035ca2886c3bb64cffc08f8fe5994360232f')
        # Native profile table at 80470010; bit zero selects one direction,
        # whose sole value is 2/front. This is a source-contract check, not sitting.
        self.assertEqual(struct.unpack_from('>I', room, 0x809401E4-ram)[0], 0x9088003C)
        first = struct.unpack_from('>I', room, 0x8094D01C-ram)[0]
        direction, count = struct.unpack_from('>2I', room, first-ram)
        self.assertEqual((room[direction-ram], count), (2, 1))
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
        self.assertEqual(symbol_data(rel, symbols, 'aMR_sit_small_chair1'), bytes([2]))
        code = self.files[CODE_VROM].extract(self.image)
        for address, name in zip((0x8010D28C, 0x8010D2A4, 0x8010D2BC, 0x8010D2D4),
                                 ('south', 'east', 'north', 'west'), strict=True):
            self.assertEqual(code[address-CODE_RAM:address-CODE_RAM+24],
                             symbol_data(rel, symbols, 'mRmTp_size_m_data_' + name))

    def test_three_installed_names_have_single_catalogue_official_credits(self):
        catalogue = json.loads((ROOT / 'translations/provenance.json').read_bytes())
        for row in self.rows:
            entries = [r for r in catalogue['entries'] if r['id'] == row['id'] + '/name']
            self.assertEqual(len(entries), 1)
            text = entries[0]['locales']['en']
            self.assertEqual(text['credit'], 'official')
            self.assertEqual(text['source']['symbol'], 'ftrName2_table')
            self.assertEqual(text['source']['index'], (int(row['item_id'], 16)-0x3000)//4)
            self.assertEqual(text['encoded_sha256'], sha256(row['name'].encode().ljust(16, b' ')))

    def test_generated_subset_receipt_matches_actual_enabled_desk_slots(self):
        path = ROOT / 'build/v3-optional-school-desks-01'
        receipt = json.loads((path / 'profile.json').read_bytes())
        report = json.loads((path / 'build.json').read_bytes())
        image = (path / 'animal-forest-v3-asset-loader.z64').read_bytes()
        self.assertEqual(sha256(image), receipt['output_sha256'])
        self.assertEqual(receipt['requested'], ['GAFE01-r0/item/3204', 'GAFE01-r0/item/3220'])
        self.assertEqual(receipt['required'], [])
        self.assertTrue(report['school_desks']['optional_composition_updated'])
        self.assertNotIn('optional composition', report['school_desks']['pending'])
        blob = by_vrom(image)[t.BLOB].extract(image)
        for row in report['school_desks']['imports']:
            item = int(row['item_id'], 16)
            at = t.ROWS + t.slot(item)*80 + 4
            self.assertEqual(bool(int.from_bytes(blob[at:at+4], 'big')), row['enabled'])
            self.assertEqual(row['enabled'], item != 0x3200)


if __name__ == '__main__': unittest.main()
