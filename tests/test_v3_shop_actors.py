"""Current imported shop interactions preserve translated actors and allocation."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
from v3_shop_actors import ABI, CODE, LIMIT, OWNERS, SHOPS, inspect

OUTPUT = ROOT / 'build/v3-shop-actors-01'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current shop interaction cartridge required')
class ShopActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.actor = cls.report['shop_actors']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:0xC000]

    def test_complete_five_actors_relocations_and_descriptors(self):
        code = self.files[CODE_VROM].extract(self.rom)
        old_code = self.old[CODE_VROM].extract(self.base)
        self.assertEqual(inspect(self.base, code), self.actor['sites'])
        self.assertEqual(len(self.actor['sites']), 20)
        for owner, spec in SHOPS.items():
            expected = bytearray(self.old[spec.vrom].extract(self.base))
            rows = [row for row in self.actor['sites'] if row['owner'] == owner]
            self.assertEqual(len(rows), 4)
            for row in rows:
                target = self.actor['code']['symbols'][row['symbol']]
                struct.pack_into('>II', expected, row['start'] - spec.ram,
                                 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
            self.assertEqual(self.files[spec.vrom].extract(self.rom), expected)
            self.assertEqual(self.files[spec.relocation].extract(self.rom), self.old[spec.relocation].extract(self.base))
            at = OWNERS[owner][1] - CODE_RAM
            self.assertEqual(code[at:at + 32], old_code[at:at + 32])
        damaged = bytearray(code)
        damaged[OWNERS['mame'][1] - CODE_RAM] ^= 1
        with self.assertRaises(ValueError):
            inspect(self.base, damaged)

    def test_compiled_layout_query_and_startup_binding(self):
        helper = (OUTPUT / 'shop_actors/code.bin').read_bytes()
        self.assertEqual(self.blob[CODE:CODE + len(helper)], helper)
        self.assertLessEqual(CODE + len(helper), LIMIT)
        self.assertLessEqual(0x7300 + self.report['furniture_items']['code']['bytes'], CODE)
        self.assertEqual(self.actor['code']['symbols']['af_v3_room_query'], 0x804680B8)
        words = struct.unpack('>' + str(len(helper) // 4) + 'I', helper)
        self.assertEqual(sum(word >> 26 == 63 for word in words), 40)
        self.assertEqual(sum(word >> 26 == 55 for word in words), 40)
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(self.blob), ABI))
        self.assertEqual(self.blob[0x7FF0:0x8000], bytes.fromhex('AF33C0DE') * 4)
        self.assertFalse(self.actor['save_format_changed'])
        self.assertEqual(self.actor['extra_allocation_bytes'], 0)

    def test_current_composition_and_import_free_v2(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        resized = tuple(int(v, 16) for v in self.report['resized_resources'])
        self.assertEqual(compose(self.native, self.base, changes, added, resized=resized), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
