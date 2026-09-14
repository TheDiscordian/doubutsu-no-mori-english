"""Current imported shop-floor branches preserve native delay-entry paths."""
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
from v3_shop_floor import ABI, CODE, LIMIT, POINTER, RAM, RELOC, SITES, VROM, inspect

OUTPUT = ROOT / 'build/v3-shop-floor-01'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current shop floor cartridge required')
class ShopFloorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.floor = cls.report['shop_floor']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:0xC000]

    def test_only_three_branch_words_change(self):
        code = self.files[CODE_VROM].extract(self.rom)
        original = self.old[VROM].extract(self.base)
        self.assertEqual(inspect(self.base, code), self.floor['sites'])
        expected = bytearray(original)
        for address, _, _, delay, _ in SITES:
            target = self.floor['code']['symbols'][f'af_v3_shop_floor_{address:08x}']
            struct.pack_into('>I', expected, address - RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF))
            self.assertEqual(struct.unpack_from('>I', expected, address + 4 - RAM)[0], delay)
        self.assertEqual(self.files[VROM].extract(self.rom), expected)
        self.assertEqual(self.files[RELOC].extract(self.rom), self.old[RELOC].extract(self.base))
        at = POINTER - 16 - CODE_RAM
        self.assertEqual(code[at:at + 32], self.old[CODE_VROM].extract(self.base)[at:at + 32])
        damaged = bytearray(code); damaged[at] ^= 1
        with self.assertRaises(ValueError):
            inspect(self.base, damaged)

    def test_resident_bounds_guards_and_startup_crc(self):
        helper = (OUTPUT / 'shop_floor/code.bin').read_bytes()
        self.assertEqual(self.blob[CODE:CODE + len(helper)], helper)
        self.assertLessEqual(CODE + len(helper), LIMIT)
        self.assertLessEqual(0x7600 + self.report['shop_actors']['code']['bytes'], CODE)
        self.assertEqual(self.floor['code']['symbols']['af_v3_room_query'], 0x804680B8)
        self.assertEqual(self.blob[0x7FF0:0x8000], bytes.fromhex('AF33C0DE') * 4)
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(self.blob), ABI))
        self.assertEqual(self.floor['extra_allocation_bytes'], 0)
        self.assertFalse(self.floor['save_format_changed'])

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
