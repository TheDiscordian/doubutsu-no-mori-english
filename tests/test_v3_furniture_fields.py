"""Current field-grid detours, donor shop rules, and import-free composition."""
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
from v3_furniture_fields import ABI, BLOB_SIZE, BRIDGE, CODE, ENTRIES, WINDOWS, donor_rules, inspect

OUTPUT = ROOT / 'build/v3-furniture-fields-01'


class FurnitureFieldsHostTests(unittest.TestCase):
    def test_sanitized_shop_selection(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-fields-tests-') as temp:
            binary = Path(temp) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_furniture_fields_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('unchanged original dispatch pass', result.stdout)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current local field build required')
class FurnitureFieldsCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.fields = cls.report['furniture_fields']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:BLOB_SIZE]

    def test_exact_functions_donor_rules_and_continuations(self):
        before = self.original[CODE_VROM].extract(self.base)
        code = self.files[CODE_VROM].extract(self.rom)
        self.assertEqual(inspect(before), self.fields['sites'])
        for address, size, digest in ENTRIES:
            at = address - CODE_RAM
            expected = bytearray(before[at:at + size])
            if address == 0x800BEE50:
                struct.pack_into('>II', expected, 0, 0x0811A900, 0)
            else:
                row = next(r for r in self.fields['sites'] if address <= r['start'] < address + size)
                target = self.fields['code']['symbols'][row['symbol']]
                struct.pack_into('>4I', expected, row['start'] - address,
                                 0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0)
            self.assertEqual(code[at:at + size], expected)
            self.assertEqual(sha256(before[at:at + size]), digest)
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        self.assertEqual(donor_rules(rel, symbols), self.fields['donor_rules'])
        with self.assertRaises(ValueError):
            donor_rules(rel[:-1], symbols)
        with self.assertRaises(ValueError):
            inspect(code)

    def test_unchanged_room_queries_and_complete_resident_bounds(self):
        compiled = (OUTPUT / 'fields/code.bin').read_bytes()
        self.assertEqual(self.blob[CODE:CODE + len(compiled)], compiled)
        self.assertLessEqual(CODE + len(compiled), BLOB_SIZE - 16)
        self.assertEqual(self.blob[BRIDGE:BRIDGE + 16], bytes.fromhex('AFA400003084FFFF0802FB9600000000'))
        self.assertEqual(self.report['furniture_room']['code']['bytes'], 4436)
        self.assertEqual(self.fields['code']['symbols']['af_v3_room_query'], 0x804680B8)
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
