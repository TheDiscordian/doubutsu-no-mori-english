"""Current room integration, complete register saves, and cartridge composition."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, BLOB_RAM, CONFIG, MODULE, compose
from v3_furniture_room import ABI, BLOB_SIZE, CODE, RAM, RELOC, VROM, inspect

OUTPUT = ROOT / 'build/v3-furniture-room-02'


class FurnitureRoomHostTests(unittest.TestCase):
    def test_sanitized_value_queries(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-room-tests-') as temp:
            binary = Path(temp) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_furniture_room_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('original room arithmetic pass', result.stdout)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current local room build required')
class FurnitureRoomCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.room = cls.report['furniture_room']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:BLOB_SIZE]

    def test_complete_bound_inventory_and_preserved_owner(self):
        data = self.files[VROM].extract(self.rom)
        unchanged = bytearray(data)
        native_windows = self.original[VROM].extract(self.base)
        for row in self.room['sites']:
            start, end = row['start'] - RAM, row['end'] - RAM
            unchanged[start:end] = native_windows[start:end]
            target = self.room['code']['symbols'][row['symbol']]
            self.assertEqual(data[start:end], struct.pack('>I', 0x08000000 | (target >> 2 & 0x3FFFFFF))
                             + bytes(end - start - 4))
        reloc = self.files[RELOC].extract(self.rom)
        self.assertEqual(inspect(bytes(unchanged), reloc), self.room['sites'])
        self.assertEqual(sha256(data), self.room['output_sha256'])
        self.assertEqual(len(self.room['sites']), 27)
        self.assertEqual(sum(r.get('paired', False) for r in self.room['sites']), 17)
        with self.assertRaises(ValueError):
            inspect(bytes(unchanged[:-1]), reloc)
        with self.assertRaises(ValueError):
            inspect(bytes(unchanged), reloc[:-1])

    def test_actual_register_saves_and_resident_model_bounds(self):
        code = (OUTPUT / 'room/code.bin').read_bytes()
        self.assertEqual(self.blob[CODE:CODE + len(code)], code)
        self.assertLessEqual(CODE + len(code), BLOB_SIZE - 16)
        symbols = self.room['code']['symbols']
        start = symbols['af_v3_room_query'] - BLOB_RAM - CODE
        end = symbols[self.room['sites'][0]['symbol']] - BLOB_RAM - CODE
        words = [n for n, in struct.iter_unpack('>I', code[start:end])]
        # Under o32, SD/LD can silently expand into paired 32-bit macros without
        # .set gp=64. Require actual opcodes and every preserved register here.
        saves = {(w >> 16 & 31, w & 65535) for w in words if w >> 26 == 63}
        loads = {(w >> 16 & 31, w & 65535) for w in words if w >> 26 == 55}
        self.assertEqual(len(saves), 30)
        self.assertEqual(saves, loads)
        self.assertTrue(set(range(1, 26)) | {28, 30, 31} <= {r for r, _ in saves})
        self.assertNotIn(17, [w >> 26 for w, in struct.iter_unpack('>I', code)])
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        self.assertEqual(struct.unpack_from('>3I', self.blob), (0x41465633, ABI, BLOB_SIZE))
        self.assertEqual(self.blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        self.assertEqual(self.blob[0x7FF0:0x8000], self.blob[-16:])
        model_file = self.files[BLOB].extract(self.rom)
        for row, expected in zip(self.report['furniture']['imports'], (0x03F0C000, 0x03F0E000)):
            start, size = int(row['object_vrom'], 16), row['object_bytes']
            self.assertEqual(start, expected)
            self.assertGreaterEqual(start - BLOB, BLOB_SIZE)
            self.assertLessEqual(start + size, 0x03F10000)
            self.assertEqual(sha256(model_file[start - BLOB:start - BLOB + size]), row['object_sha256'])
            profile = int(row['profile_ram'], 16) - BLOB_RAM
            self.assertEqual(struct.unpack_from('>2I', self.blob, profile), (start, start + size))

    def test_current_composition_and_import_free_retention(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
