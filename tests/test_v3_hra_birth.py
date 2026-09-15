"""Current extended native acquisition counters, pointers, and cartridge bounds."""
import json
import struct
import unittest
import zlib

from tests.test_v3_furniture_art import ROOT
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, CONFIG, MODULE
from v3_hra_birth import BASE, BASE_SHA, COUNT, ENTRY, STACK, TABLE, extend
import v3_hra as hra

OUTPUT = ROOT / 'build/v3-hra-birth-01'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current acquisition-score build required')
class BirthCounterTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.image = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((BASE / 'build.json').read_text())
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.old_files, cls.files = by_vrom(cls.base), by_vrom(cls.image)
        cls.old = cls.old_files[hra.NEW_VROM].extract(cls.base)
        cls.data = cls.files[hra.NEW_VROM].extract(cls.image)
        cls.reloc = cls.files[hra.NEW_RELOC].extract(cls.image)
        cls.detail = cls.report['hra_birth']

    def test_complete_stack_layout_unrolled_counts_and_original_weights(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual((len(self.data), len(self.reloc), COUNT), (31392, 1184, 23))
        for address, word in STACK.items():
            immediate = word & 65535
            change = -32 if address == ENTRY else 32 if immediate >= 232 else 16 if immediate >= 156 else 0
            self.assertEqual(u32(self.data, address - hra.RAM), word + change)
        # Exact disjoint ranges for 23 occurrence counters and 23 products.
        self.assertEqual(list(range(80, 172, 4)), list(range(80, 80 + COUNT * 4, 4)))
        self.assertEqual(list(range(172, 264, 4)), list(range(172, 172 + COUNT * 4, 4)))
        self.assertEqual(len([172, 176, 180] + [v for n in range(184, 264, 16)
                                              for v in range(n, n + 16, 4)]), COUNT)
        table_at = self.detail['points_address'] - hra.RAM
        weights = struct.unpack_from('>23I', self.data, table_at)
        self.assertEqual(weights[:19], struct.unpack_from('>19I', self.old, TABLE - hra.RAM))
        self.assertEqual(weights[7], 2951)  # Keep N64 lottery balance, not GC 1029.
        self.assertEqual(weights[19:], (1111, 1111, 1111, 412))
        self.assertEqual(table_at, len(self.old) + 4)

    def test_only_reviewed_instructions_and_appended_table_change(self):
        restored = bytearray(self.data[:len(self.old)])
        self.assertEqual(len(self.detail['patches']), 23)
        for row in self.detail['patches']:
            at = row['address'] - hra.RAM
            self.assertEqual(u32(restored, at), row['after'])
            struct.pack_into('>I', restored, at, row['before'])
        self.assertEqual(restored, self.old)
        old_reloc = self.old_files[hra.NEW_RELOC].extract(self.base)
        self.assertEqual(self.reloc[4:], old_reloc[4:])
        self.assertEqual(u32(self.reloc, 0), len(self.data))
        self.assertEqual(self.detail['relocation_destinations_checked'], 3)
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        changed = bytearray(self.old)
        changed[ENTRY - hra.RAM] ^= 1
        with self.assertRaises(ValueError):
            extend(bytes(changed), old_reloc, self.prior['hra'], rel, symbols)

    def test_actual_scheduler_crc_resources_and_save_profile(self):
        self.assertEqual(len(self.image), 0x4000000)
        self.assertEqual(self.report['output_sha256'], sha256(self.image))
        code = bytearray(self.files[CODE_VROM].extract(self.image))
        old_code = self.old_files[CODE_VROM].extract(self.base)
        for row in self.report['hra']['scheduler']:
            at = row['address'] - CODE_RAM
            self.assertEqual(u32(code, at), row['after'])
            struct.pack_into('>I', code, at, row['before'])
        self.assertEqual(code, old_code)
        actual_code = self.files[CODE_VROM].extract(self.image)
        for hi, lo in ((0x8009CED0, 0x8009CED8), (0x8009CF0C, 0x8009CF10)):
            upper, lower = (u32(actual_code, n - CODE_RAM) for n in (hi, lo))
            self.assertEqual(((upper & 65535) << 16) + (lower & 65535) - 65536,
                             hra.RAM + len(self.data))
        self.assertEqual(u32(actual_code, 0x8009CF18 - CODE_RAM) & 65535, len(self.data))
        blob = self.files[BLOB].extract(self.image)
        old_blob = self.old_files[BLOB].extract(self.base)
        self.assertEqual(blob[8:len(old_blob)], old_blob[8:])
        self.assertEqual(blob[0x20:0xE0].hex(), self.prior['save_runtime']['profile_hex'])
        module = self.files[MODULE].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, 49152, zlib.crc32(blob[:49152]), 63))
        self.assertEqual(self.report['hra']['birth_extension']['additional_on_demand_bytes'], 96)
        for row in self.detail['resource_moves']:
            entry = self.files[row['vrom']]
            self.assertEqual(entry.pstart, self.files[BLOB].pstart + row['blob_offset'])
            self.assertEqual(sha256(entry.extract(self.image)), row['sha256'])


if __name__ == '__main__':
    unittest.main()
