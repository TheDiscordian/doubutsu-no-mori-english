"""Current furniture loader, relocation, bank bounds, and ROM-only asset tail."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import apply_ups, by_vrom, sha256
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
from v3_furniture_runtime import (ABI, BLOB_SIZE, CAPACITY, CODE, CURRENT_SHA, HOOKS, IMPORTS,
                                 INDICES, NATIVE_COUNT, PROFILES, RAM, RELOC, RESIDENT,
                                 SECTIONS, SIZE, VROM, patch_owner)
from v3_registry import furniture_slot

OUTPUT = ROOT / 'build/v3-furniture-loader-03'


class FurnitureRuntimeHostTests(unittest.TestCase):
    def test_sanitized_helpers_and_current_abi_startup(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-furniture-host-') as temp:
            for source, extra, marker in (
                    ('tests/v3_furniture_test.c', [], 'bank ownership'),
                    ('tests/v3_asset_loader_test.c', ['-DAF_V3_ABI=5', '-DAF_V3_BLOB_SIZE=32768',
                                                    str(ROOT / 'runtime/crc32.c')], 'rejection paths pass')):
                binary = Path(temp) / Path(source).stem
                subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', str(ROOT / source),
                    *extra, '-o', str(binary)], check=True, capture_output=True)
                result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
                self.assertIn(marker, result.stdout)

    def test_literal_item_reservations(self):
        self.assertEqual(furniture_slot(0x3224), (1161, 0x3224, 0x03F08000))
        self.assertEqual(furniture_slot(0x32B8), (1198, 0x32B8, 0x03F0A000))
        with self.assertRaises(ValueError):
            furniture_slot(0x3350)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current local furniture build required')
class FurnitureRuntimeCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob_file = cls.files[BLOB].extract(cls.rom)
        cls.blob = cls.blob_file[:BLOB_SIZE]
        cls.furniture = cls.report['furniture']

    def test_bounded_resident_data_and_rom_only_tail(self):
        self.assertEqual(len(self.blob_file), 44176)
        self.assertEqual(struct.unpack_from('>5I', self.blob), (0x41465633, ABI, BLOB_SIZE, 430, 410))
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        self.assertEqual(sha256(self.blob), self.report['blob_sha256'])
        self.assertEqual(self.blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        self.assertEqual(self.blob[INDICES:INDICES + CAPACITY], b'\xFF' * CAPACITY)
        self.assertLessEqual(CODE + self.furniture['code']['bytes'], PROFILES)
        used = {}
        for i, row in enumerate(self.furniture['imports']):
            at = IMPORTS + i * 80
            self.assertEqual(struct.unpack_from('>HHI', self.blob, at),
                             (row['runtime_index'], int(row['item_id'], 16), 1))
            ptr = int(row['profile_ram'], 16)
            used[row['runtime_index']] = ptr
            start, end, segment, limit = struct.unpack_from('>4I', self.blob, at + 8)
            self.assertEqual(start, int(row['object_vrom'], 16))
            self.assertNotIn(start, self.files)
            self.assertEqual((end - start, limit - segment), (row['object_bytes'],) * 2)
            self.assertEqual(sha256(self.blob_file[start - BLOB:end - BLOB]), row['object_sha256'])
            self.assertEqual(sha256(self.blob[at + 8:at + 76]), row['profile_sha256'])
            self.assertFalse(row['playable'])
        for index in range(CAPACITY):
            self.assertEqual(struct.unpack_from('>I', self.blob, PROFILES + index * 4)[0], used.get(index, 0))

    def test_table_retargeting_and_remaining_relocations_at_live_addresses(self):
        before, reloc = (self.original[v].extract(self.base) for v in (VROM, RELOC))
        self.assertEqual(sha256(before), CURRENT_SHA)
        data, fixed, report = patch_owner(before, reloc, self.furniture['code']['symbols'])
        self.assertEqual(data, self.files[VROM].extract(self.rom))
        self.assertEqual(fixed, self.files[RELOC].extract(self.rom))
        self.assertEqual(report, self.furniture['owner'])
        self.assertEqual(report['reference_counts'], {'profile': 57, 'bank': 15})
        self.assertEqual(report['retained_relocations'], 1401)
        spec = SimpleNamespace(ram=RAM, resident_bytes=RESIDENT, sections=struct.unpack_from('>5I', fixed))
        for base in (0x80200000, 0x80368000):
            loaded = relocate_verified_data(spec, data, fixed, base)
            for binding in report['bindings']:
                hi, lo = (struct.unpack_from('>I', loaded, binding[key] - RAM)[0] for key in ('high', 'low'))
                value = ((hi & 65535) << 16) + (lo & 65535) - (65536 if lo & 32768 else 0)
                self.assertEqual(value, binding['target'])
            for address, name, _ in HOOKS:
                self.assertEqual(struct.unpack_from('>II', loaded, address - RAM),
                                 (0x08000000 | (self.furniture['code']['symbols'][name] >> 2 & 0x3FFFFFF), 0))
            self.assertEqual(loaded[SIZE:], bytes(SECTIONS[3]))
        for address in (0x8093931C, 0x80939994):
            at = address - RAM
            self.assertEqual(data[at:at + 36], before[at:at + 36])
        broken = bytearray(before); broken[0] ^= 1
        with self.assertRaises(ValueError):
            patch_owner(broken, reloc, self.furniture['code']['symbols'])

    def test_exact_current_composition_and_import_free_retention(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(len(self.files) - len(self.original), 3)
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
