"""Changed catalogue layout, complete installed tables, and cartridge bounds."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, by_vrom, n64_checksum, sha256
from catalogue_names import APPROVED, Image, PREFIX, START
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP
from v3_catalogue import RAM, VROM, RELOC, TABLE
from v3_catalogue_capacity import CAPACITY, GROWTH, MULTIPLIERS, NAME_OFFSET, PAGE_BYTES, STATE_BYTES, TAIL_GROWTH
from v3_construction_catalogue import BASE, BASE_SHA
from v3_construction_items import PROPERTIES
import v3_hra as hra
import v3_feng_shui as feng
import v3_shops as shops

OUTPUT = ROOT / 'build/v3-construction-catalogue-03'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current construction catalogue required')
class ConstructionCatalogueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.image = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((BASE / 'build.json').read_text())
        cls.files, cls.old_files = by_vrom(cls.image), by_vrom(cls.base)
        cls.cat = cls.report['catalogue']
        cls.data, cls.reloc = (cls.files[v].extract(cls.image) for v in (VROM, RELOC))

    def test_actual_mips_page_arithmetic_and_all_storage_boundaries(self):
        self.assertEqual((CAPACITY, PAGE_BYTES, NAME_OFFSET, STATE_BYTES), (753, 1584, 1514, 18144))
        self.assertEqual(NAME_OFFSET, 8 + CAPACITY * 2)
        self.assertEqual(PAGE_BYTES, NAME_OFFSET + 70)
        self.assertEqual(0xEC8 + 9 * PAGE_BYTES, 0x30C0 + TAIL_GROWTH)
        self.assertLessEqual(0x30C0 + TAIL_GROWTH + 92, STATE_BYTES)
        self.assertEqual(PREFIX + STATE_BYTES, START + GROWTH)
        for source, destination, addresses in MULTIPLIERS:
            for category in range(256):
                registers = [0x13579000 + n for n in range(32)]
                registers[0], registers[source] = 0, category
                before = registers[:]
                for address in addresses:
                    word = struct.unpack_from('>I', self.data, address - RAM)[0]
                    self.assertEqual(word >> 26, 0)
                    rs, rt, rd, shift, op = word >> 21 & 31, word >> 16 & 31, word >> 11 & 31, word >> 6 & 31, word & 63
                    self.assertEqual(rd, destination)
                    if op == 0: registers[rd] = registers[rt] << shift
                    elif op == 33: registers[rd] = registers[rs] + registers[rt]
                    else: self.fail('Unexpected rewritten instruction')
                self.assertEqual(registers[destination], category * PAGE_BYTES)
                registers[destination] = before[destination]
                self.assertEqual(registers, before)
        # The maximum real count now extends beyond the old name offset, while
        # seven complete compatibility fields and the next page remain separate.
        for category in range(9):
            base = 0xEC8 + category * PAGE_BYTES
            self.assertLessEqual(base + 8 + 446 * 2, base + NAME_OFFSET)
            self.assertEqual(base + NAME_OFFSET + 7 * 10, base + PAGE_BYTES)

    def test_complete_furniture_clothing_and_scoring_rows(self):
        cat = self.cat
        self.assertEqual((cat['total_rows'], cat['row_capacity']), (446, 753))
        at = cat['code']['symbols']['af_v3_catalogue_order'] - RAM
        values = list(struct.iter_unpack('>HH', self.data[at:at + 446 * 4]))
        self.assertEqual(values[:436], list(struct.iter_unpack('>HH', self.data[TABLE - RAM:TABLE - RAM + 436 * 4])))
        self.assertEqual([i for i, _ in values[436:]], [r['catalogue_index'] for r in cat['imports']])
        self.assertEqual(len(set(i for i, _ in values)), 446)
        self.assertEqual(sorted(int(r['item_id'], 16) for r in cat['imports']), sorted([0x3224, 0x32B8, 0x3350, *PROPERTIES]))
        self.assertEqual([r['donor_position'] for r in cat['imports']], sorted(r['donor_position'] for r in cat['imports']))
        old_cat = self.old_files[VROM].extract(self.base)
        new_at = cat['clothing']['table_address'] - RAM
        old_at = self.prior['catalogue']['clothing']['table_address'] - RAM
        self.assertEqual(self.data[new_at:new_at + 496], old_cat[old_at:old_at + 496])
        for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
            current = self.files[tool.NEW_VROM].extract(self.image)
            old = bytearray(self.old_files[tool.NEW_VROM].extract(self.base))
            table = self.report[key]['metadata_address'] - tool.RAM
            for item, (_, _, birth, colour) in PROPERTIES.items():
                index = 1024 + (item - 0x3000) // 4
                expected = struct.pack('>I', 0x40050000 | birth << 9) if width == 4 else bytes((colour, 0))
                old[table + index * width:table + (index + 1) * width] = expected
            self.assertEqual(current, old)
            self.assertEqual(self.files[tool.NEW_RELOC].extract(self.image), self.old_files[tool.NEW_RELOC].extract(self.base))
        h = self.files[hra.NEW_VROM].extract(self.image)
        start = self.report['hra']['metadata_address'] - hra.RAM
        self.assertEqual(sum(h[start + i * 4] >> 2 == 16 for i in range(2051)), 28)

    def test_native_relocations_and_menu_allocation(self):
        cap = self.cat['capacity_expansion']
        for destination in (0x801A0010, 0x802F8010, 0x803D0010):
            loaded = relocate_verified_data(Image(RAM, len(self.data), struct.unpack_from('>5I', self.reloc)),
                                            self.data, self.reloc, destination)
            for hook, symbol in ((0x808A9798, 'af_catalog_init'), (0x808A961C, 'af_catalog_load_name'),
                                 (0x808A6C20, 'af_catalog_load_name'), (0x808A8A9C, 'af_catalog_draw')):
                target = destination + APPROVED['symbols'][symbol] + GROWTH
                self.assertEqual(struct.unpack_from('>I', loaded, hook - RAM)[0], 0x0C000000 | (target >> 2 & 0x3FFFFFF))
            self.assertFalse(any(loaded[PREFIX:START + GROWTH]))
            cache = APPROVED['symbols']['af_catalog_init'] + GROWTH
            self.assertEqual(struct.unpack_from('>I', loaded, cache + 32)[0], 0x08000000 | ((destination + 0x32A8) >> 2 & 0x3FFFFFF))
        code = self.files[CODE_VROM].extract(self.image)
        hi, low = (struct.unpack_from('>I', code, address - CODE_RAM)[0] for address in (0x800C4AFC, 0x800C4B10))
        endpoint = ((hi & 65535) << 16) + (low & 65535) - (65536 if low & 32768 else 0)
        self.assertEqual(endpoint, 0x80897620 + 6144)
        self.assertEqual((hi >> 16, low >> 16), (0x3C0E, 0x25CE))
        self.assertEqual(self.cat['pool_reserved'], 280704)
        self.assertLessEqual(self.cat['conservative_pool_required'], self.cat['pool_reserved'])
        self.assertEqual(cap['additional_pool_allocation'], 6144)
        self.assertEqual(len(self.data) % 16, 0)
        self.assertLessEqual(VROM + len(self.data), RELOC)

    def test_whole_cartridge_changes_stock_descriptor_crc_and_save_retention(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        blob, old_blob = self.files[BLOB].extract(self.image), self.old_files[BLOB].extract(self.base)
        self.assertEqual(blob[:4] + blob[8:len(old_blob)], old_blob[:4] + old_blob[8:])
        self.assertEqual(self.report['save_runtime'], self.prior['save_runtime'])
        self.assertEqual(struct.unpack_from('>2I', self.image, 16), n64_checksum(self.image))
        module = self.files[MODULE].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG), (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), 62))
        goods = self.files[shops.VROM].extract(self.image)
        stock = self.report['shops']
        pointers = struct.unpack_from('>12I', goods, stock['table_offset'])
        for item, (_, group, _, _) in PROPERTIES.items():
            first, limit = pointers[group] & 0xFFFFFF, pointers[group + 1] & 0xFFFFFF
            values = list(struct.unpack('>' + str((limit - first) // 2) + 'H', goods[first:limit]))
            self.assertEqual(values.count(item), 1)
            self.assertEqual(values[-1], 0)
        code = self.files[CODE_VROM].extract(self.image)
        self.assertEqual(struct.unpack_from('>3I', code, shops.DESCRIPTOR - CODE_RAM),
                         (shops.VROM, shops.VROM + len(goods), 0x06000000 | stock['table_offset']))
        restored = bytearray(self.image)
        ranges = [(16, 24), (self.files[BLOB].pstart, self.files[BLOB].pstart + len(blob)),
                  (self.files[MODULE].pstart + STARTUP, self.files[MODULE].pstart + CONFIG + 16),
                  (self.files[CODE_VROM].pstart + shops.DESCRIPTOR - CODE_RAM,
                   self.files[CODE_VROM].pstart + shops.DESCRIPTOR - CODE_RAM + 12)]
        for address in (0x800C4AFC, 0x800C4B10):
            at = self.files[CODE_VROM].pstart + address - CODE_RAM
            ranges.append((at, at + 4))
        for vrom in (BLOB, VROM, RELOC, hra.NEW_VROM, feng.NEW_VROM, shops.VROM):
            at = DMA_START + self.files[vrom].index * 16
            ranges.append((at, at + 16))
        parent = self.files[0x7749C0].pstart + 0x2C90
        ranges.append((parent, parent + 32))
        for start, end in ranges: restored[start:end] = self.base[start:end]
        self.assertEqual(restored, self.base)


if __name__ == '__main__': unittest.main()
