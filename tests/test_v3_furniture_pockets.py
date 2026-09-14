"""Selected furniture pocket queries and actual current-cartridge installation."""
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
from v3_furniture_pockets import ABI, BLOB_SIZE, BRIDGE, CODE, ENTRIES, PROLOGUE

OUTPUT = ROOT / 'build/v3-furniture-pockets-01'


class FurniturePocketHostTests(unittest.TestCase):
    def test_sanitized_complete_pocket_searches(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-pocket-tests-') as temp:
            binary = Path(temp) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_furniture_pockets_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('original fallbacks pass', result.stdout)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current local pocket build required')
class FurniturePocketCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.pockets = cls.report['furniture_pockets']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:BLOB_SIZE]

    def test_installed_entries_bridges_and_native_bodies(self):
        old, code = self.original[CODE_VROM].extract(self.base), self.files[CODE_VROM].extract(self.rom)
        jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
        for i, (address, size, name, digest) in enumerate(ENTRIES):
            at = address - CODE_RAM
            self.assertEqual(sha256(old[at:at + size]), digest)
            self.assertEqual(struct.unpack_from('>II', code, at), (jump(self.pockets['code']['symbols'][name]), 0))
            self.assertEqual(code[at + 8:at + size], old[at + 8:at + size])
            self.assertEqual(struct.unpack_from('>4I', self.blob, BRIDGE + i * 16),
                             (*PROLOGUE, jump(address + 8), 0))

    def test_code_layout_and_guards(self):
        compiled = (OUTPUT / 'pockets/code.bin').read_bytes()
        self.assertEqual(self.blob[CODE:CODE + len(compiled)], compiled)
        self.assertEqual(self.pockets['code']['symbols']['af_v3_room_value'], 0x80468000)
        self.assertLessEqual(CODE + len(compiled), BLOB_SIZE - 16)
        for part, offset in (('room', 0x8000), ('fields', 0xA400), ('menu', 0xA800), ('icon', 0xAB00), ('ground', 0xAE00)):
            previous = self.report['furniture_' + part]['code']
            self.assertEqual(sha256(self.blob[offset:offset + previous['bytes']]), previous['sha256'])
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        self.assertEqual(self.blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        self.assertEqual(self.blob[0x7FF0:0x8000], self.blob[-16:])

    def test_current_composition_and_import_free_retention(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
