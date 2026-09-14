"""Current ground-item hooks and unchanged surrounding cartridge data."""
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
from v3_furniture_ground import ABI, BLOB_SIZE, CODE, RAM, RELOC, SITES, VROM, inspect

OUTPUT = ROOT / 'build/v3-furniture-ground-01'


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current local ground build required')
class FurnitureGroundCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.ground = cls.report['furniture_ground']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:BLOB_SIZE]

    def test_exact_windows_and_retained_resources(self):
        old, reloc = (self.original[v].extract(self.base) for v in (VROM, RELOC))
        code = self.files[CODE_VROM].extract(self.rom)
        inspect(code, old, reloc)
        expected = bytearray(old)
        for start, *_ in SITES:
            target = self.ground['code']['symbols'][f'af_v3_ground_type_{start:08x}']
            struct.pack_into('>II', expected, start - RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        self.assertEqual(self.files[VROM].extract(self.rom), expected)
        self.assertEqual(self.files[RELOC].extract(self.rom), reloc)
        for v in (0x858A50, 0x85A180):
            self.assertEqual(self.files[v].extract(self.rom), self.original[v].extract(self.base))
        with self.assertRaises(ValueError):
            inspect(code, bytes(expected), reloc)
        with self.assertRaises(ValueError):
            inspect(code, old, reloc[:-1])

    def test_resident_code_query_and_guards(self):
        compiled = (OUTPUT / 'ground/code.bin').read_bytes()
        self.assertEqual(self.blob[CODE:CODE + len(compiled)], compiled)
        self.assertEqual(self.ground['code']['symbols']['af_v3_room_query'], 0x804680B8)
        self.assertLessEqual(CODE + len(compiled), BLOB_SIZE - 16)
        for part, offset in (('room', 0x8000), ('fields', 0xA400), ('menu', 0xA800), ('icon', 0xAB00)):
            previous = self.report['furniture_' + part]['code']
            self.assertEqual(sha256(self.blob[offset:offset + previous['bytes']]), previous['sha256'])
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        self.assertEqual(self.blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        self.assertEqual(self.blob[0x7FF0:0x8000], self.blob[-16:])
        words = [w for w, in struct.iter_unpack('>I', compiled)]
        self.assertEqual(sum(w >> 26 == 63 for w in words), 7)
        self.assertEqual(sum(w >> 26 == 55 for w in words), 7)

    def test_current_composition_and_import_free_retention(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
