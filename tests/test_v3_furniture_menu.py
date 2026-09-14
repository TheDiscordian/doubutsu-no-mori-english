"""Current installed inventory menu dispatch and unchanged surrounding resources."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
from v3_furniture_menu import ABI, BLOB_SIZE, CODE, RAM, RELOC, ROOT_VROM, SITES, VROM, inspect

OUTPUT = ROOT / 'build/v3-furniture-menu-01'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current local menu build required')
class FurnitureMenuCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.menu = cls.report['furniture_menu']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:BLOB_SIZE]

    def test_exact_tag_windows_parent_and_relocations(self):
        old = self.original[VROM].extract(self.base)
        root = self.original[ROOT_VROM].extract(self.base)
        reloc = self.original[RELOC].extract(self.base)
        native_code = self.files[CODE_VROM].extract(self.rom)
        self.assertEqual(inspect(native_code, root, old, reloc), self.menu['sites'])
        expected = bytearray(old)
        for row in self.menu['sites']:
            target = self.menu['code']['symbols'][row['symbol']]
            struct.pack_into('>II', expected, row['start'] - RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        self.assertEqual(self.files[VROM].extract(self.rom), expected)
        self.assertEqual(self.files[RELOC].extract(self.rom), reloc)
        self.assertEqual(self.files[ROOT_VROM].extract(self.rom), root)
        with self.assertRaises(ValueError):
            inspect(native_code, root, bytes(expected), reloc)
        with self.assertRaises(ValueError):
            inspect(native_code, root[:-1], old, reloc)

    def test_resident_code_guards_and_query_binding(self):
        compiled = (OUTPUT / 'menu/code.bin').read_bytes()
        self.assertEqual(self.blob[CODE:CODE + len(compiled)], compiled)
        self.assertLessEqual(CODE + len(compiled), BLOB_SIZE - 16)
        self.assertEqual(self.menu['code']['symbols']['af_v3_room_query'], 0x804680B8)
        self.assertEqual(self.report['furniture_room']['code']['bytes'], 4436)
        self.assertEqual(self.report['furniture_fields']['code']['bytes'], 252)
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        self.assertEqual(self.blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        self.assertEqual(self.blob[0x7FF0:0x8000], self.blob[-16:])
        words = [w for w, in struct.iter_unpack('>I', compiled)]
        self.assertEqual(sum(w >> 26 == 63 for w in words), 6)
        self.assertEqual(sum(w >> 26 == 55 for w in words), 6)

    def test_current_composition_and_import_free_retention(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
