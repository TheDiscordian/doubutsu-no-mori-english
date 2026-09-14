"""Current selected furniture metadata and installed shared item readers."""
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
from v3_asset_loader import BLOB, CONFIG, MODULE, MODULE_RAM, compose
from v3_furniture_items import ABI, BRIDGE, CODE, DATA, ENTRIES, metadata

OUTPUT = ROOT / 'build/v3-furniture-items-01'


class FurnitureItemHostTests(unittest.TestCase):
    def test_sanitized_shared_readers(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-item-tests-') as temp:
            binary = Path(temp) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_furniture_items_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('original fallbacks pass', result.stdout)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current local item-reader build required')
class FurnitureItemCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:32768]

    def test_actual_donor_metadata_and_rejection(self):
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        data, rows = metadata(rel, symbols)
        self.assertEqual(data, self.blob[DATA:DATA + 64])
        self.assertEqual(rows, self.report['furniture_items']['imports'])
        self.assertEqual([(r['name'], r['price'], r['footprint']) for r in rows],
                         [('haz-mat barrel', 830, '1x1'), ('oil drum', 840, '1x1')])
        with self.assertRaises(ValueError):
            metadata(rel[:-1], symbols)
        with self.assertRaises(ValueError):
            metadata(rel, symbols + b' ')

    def test_installed_entries_bridges_and_bounded_code(self):
        symbols = self.report['furniture_items']['code']['symbols']
        for i, (address, size, name, expected, digest) in enumerate(ENTRIES):
            base, vrom = (MODULE_RAM, MODULE) if address >= MODULE_RAM else (CODE_RAM, CODE_VROM)
            at = address - base
            old = self.original[vrom].extract(self.base)
            data = self.files[vrom].extract(self.rom)
            self.assertEqual(sha256(old[at:at + size]), digest)
            self.assertEqual(data[at + 8:at + size], old[at + 8:at + size])
            self.assertEqual(struct.unpack_from('>II', data, at),
                             (0x08000000 | (symbols[name] >> 2 & 0x3FFFFFF), 0))
            self.assertEqual(struct.unpack_from('>4I', self.blob, BRIDGE + i * 16),
                             (*expected, 0x08000000 | ((address + 8) >> 2 & 0x3FFFFFF), 0))
        self.assertLessEqual(CODE + self.report['furniture_items']['code']['bytes'], 0x7FF0)
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, 32768, zlib.crc32(self.blob), ABI))
        self.assertEqual(self.blob[-16:], bytes.fromhex('AF33C0DE') * 4)

    def test_current_composition_and_import_free_retention(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
