"""Focused V3 object-loader ownership and current-cartridge checks."""
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
from v3_asset_loader import (BASE_SHA, BLOB, BLOB_SIZE, CAPACITY, CONFIG, MODULE,
    MODULE_RAM, OBJECT_COUNT, OBJECT_TABLE, STARTUP, STARTUP_CALL, STARTUP_END,
    TABLE_OFFSET, compose, texture_slot)


class LoaderHostTests(unittest.TestCase):
    def test_sanitized_startup_and_native_object_status_contract(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-assets-host-') as temp:
            binary = Path(temp) / 'check'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_asset_loader_test.c'), str(ROOT / 'runtime/crc32.c'),
                '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('rejection paths pass', result.stdout)

    def test_reserved_texture_slots_do_not_depend_on_selection_order(self):
        self.assertEqual(texture_slot(235), (429, 0x03F36000))
        self.assertEqual(texture_slot(232), (426, 0x03F30000))
        self.assertEqual(len({texture_slot(i) for i in range(216, 236)}), 20)
        for invalid in (0, 215, 236, 237, 255):
            with self.assertRaises(ValueError):
                texture_slot(invalid)


@unittest.skipUnless((ROOT / 'build/v3-asset-loader-02/build.json').is_file(), 'Local V3 asset batch required')
class CurrentCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.output = ROOT / 'build/v3-asset-loader-02'
        cls.report = json.loads((cls.output / 'build.json').read_text())
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.image = (cls.output / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.old, cls.new = by_vrom(cls.base), by_vrom(cls.image)

    def test_only_owned_startup_bytes_change_and_original_dma_indices_survive(self):
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.image), self.report['output_sha256'])
        for vrom, old in self.old.items():
            before, after = old.extract(self.base), self.new[vrom].extract(self.image)
            self.assertEqual(old.index, self.new[vrom].index)
            if vrom == 0x19D40:
                self.assertEqual(before[:16], after[:16])
                continue
            allowed = (range(STARTUP, STARTUP_END) if vrom == MODULE else
                       range(STARTUP_CALL - CODE_RAM, STARTUP_CALL - CODE_RAM + 4) if vrom == CODE_VROM else ())
            self.assertEqual(len(before), len(after))
            self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(before, after))), hex(vrom))
        module = self.new[MODULE].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.new[BLOB].extract(self.image)), 1))
        call = struct.unpack_from('>I', self.new[CODE_VROM].extract(self.image), STARTUP_CALL - CODE_RAM)[0]
        self.assertEqual(call, 0x0C000000 | (((MODULE_RAM + STARTUP) >> 2) & 0x3FFFFFF))

    def test_native_table_and_new_texture_bounds_are_complete(self):
        blob = self.new[BLOB].extract(self.image)
        before = self.old[CODE_VROM].extract(self.base)
        at = OBJECT_TABLE - CODE_RAM
        self.assertEqual(blob[TABLE_OFFSET:TABLE_OFFSET + OBJECT_COUNT * 8], before[at:at + OBJECT_COUNT * 8])
        used = set()
        for row in self.report['imports']:
            bank, vrom = row['object_bank'], int(row['texture_vrom'], 16)
            texture = self.new[vrom].extract(self.image)
            self.assertEqual(struct.unpack_from('>II', blob, TABLE_OFFSET + bank * 8), (vrom, vrom + len(texture)))
            self.assertEqual(sha256(texture), row['texture_sha256'])
            self.assertEqual(len(texture), 5664)
            self.assertFalse(row['playable'])
            self.assertFalse(row['draw_record_installed'])
            used.add(bank)
        self.assertEqual(used, {426, 429})
        for bank in set(range(OBJECT_COUNT, CAPACITY)) - used:
            self.assertEqual(blob[TABLE_OFFSET + bank * 8:TABLE_OFFSET + (bank + 1) * 8], bytes(8))
        self.assertEqual(struct.unpack_from('>4I', blob, len(blob) - 16), (0xAF33C0DE,) * 4)

    def test_no_import_baseline_and_complete_patch_reconstruction(self):
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (self.output / 'asset-loader.ups').read_bytes()), self.image)
        with self.assertRaises(ValueError):
            compose(self.native, self.native, {}, {})
        with self.assertRaises(ValueError):
            compose(self.native, self.base, {}, {MODULE: bytes(16)})
        with self.assertRaises(ValueError):
            compose(self.native, self.base, {MODULE: bytes(16)}, {})


if __name__ == '__main__':
    unittest.main()
