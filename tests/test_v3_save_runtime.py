"""Actual V3 FlashRAM hook composition and sanitized save/load control flow."""
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
from v3_save_runtime import (ABI, ALLOCATIONS, BLOB_SIZE, BRIDGE, CODE, LIMIT,
                             PREPARE_CALLS, PROFILE_OFFSET, profile_bytes)
from v3_save_warning_smoke import make_seed

OUTPUT = ROOT / 'build/v3-save-runtime-02'


class SaveRuntimeHostTests(unittest.TestCase):
    def test_incompatible_seed_preserves_compatible_bank(self):
        from test_v3_save_codec import fixture, reference_pack
        source_bank, state = fixture()
        bank = bytes(reference_pack(source_bank, state))
        with tempfile.TemporaryDirectory(prefix='v3-warning-fixture-', dir=ROOT / 'build') as directory:
            source = Path(directory) / 'source'
            source.mkdir()
            (source / 'test.flash').write_bytes(bank * 2)
            (source / 'manifest.json').write_text(json.dumps({'flash_sha256': sha256(bank * 2),
                'rom_sha256': 'fixture', 'working_state_hex': state.hex(), 'asynchronous_two_banks_passed': True}))
            output = Path(directory) / 'seed'
            report = make_seed(source, output)
            actual = (output / 'test.flash').read_bytes()
            self.assertEqual(actual[65536:], bank)
            self.assertEqual(actual[:0xF980], bank[:0xF980])
            state[27] |= 4
            self.assertEqual(actual[:65536], reference_pack(bank, state))
            self.assertEqual(report['flash_sha256'], sha256(actual))

    def test_sanitized_save_load_lifecycle_and_failure_order(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-save-runtime-tests-') as directory:
            binary = Path(directory) / 'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_save_runtime_test.c'), '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('failure-before-I/O, retries, and guards pass', result.stdout)

    def test_stable_profile_bits_and_rejection(self):
        villagers = [{'actor_id': 'E0EA', 'registry_version': 1}, {'actor_id': 'E0ED', 'registry_version': 1}]
        furniture = [{'item_id': '3224', 'runtime_index': 1161}, {'item_id': '32B8', 'runtime_index': 1198}]
        value = profile_bytes(villagers, furniture)
        self.assertEqual(value, profile_bytes(villagers[::-1], furniture[::-1]))
        expected = bytearray(160)
        expected[29], expected[49], expected[53] = 0x24, 2, 64
        self.assertEqual(value, expected)
        self.assertEqual(profile_bytes([], []), bytes(160))
        for bad in ({'actor_id': 'E0D9', 'registry_version': 1},
                    {'actor_id': 'E0EE', 'registry_version': 1}, {'actor_id': 'E0EA', 'registry_version': 2}):
            with self.assertRaises(ValueError):
                profile_bytes([bad], furniture)
        for bad in ({'item_id': '3225', 'runtime_index': 1161},
                    {'item_id': '1004', 'runtime_index': 1}, {'item_id': '3224', 'runtime_index': 1}):
            with self.assertRaises(ValueError):
                profile_bytes(villagers, [bad])
        with self.assertRaises(ValueError):
            profile_bytes(villagers * 2, furniture)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current FlashRAM cartridge required')
class SaveRuntimeCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.runtime = cls.report['save_runtime']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:BLOB_SIZE]

    def test_complete_hook_windows_capacities_and_profile(self):
        code, old = self.files[CODE_VROM].extract(self.rom), self.original[CODE_VROM].extract(self.base)
        for patch in self.runtime['patches']:
            at = patch['address'] - CODE_RAM
            before, after = bytes.fromhex(patch['before']), bytes.fromhex(patch['after'])
            self.assertEqual(old[at:at + len(before)], before)
            self.assertEqual(code[at:at + len(after)], after)
        for address in ALLOCATIONS:
            self.assertEqual(struct.unpack_from('>I', code, address - CODE_RAM)[0], 0x3C040001)
        self.assertEqual(struct.unpack_from('>I', code, 0x8008F8D4 - CODE_RAM)[0], 0x26530200)
        self.assertEqual(struct.unpack_from('>I', code, 0x8008F4B8 - CODE_RAM)[0], 0x3C060001)
        for address in (0x8008F9F0, 0x8008FB84, 0x80095820, 0x800961F8):
            self.assertEqual(struct.unpack_from('>I', code, address - CODE_RAM)[0], 0x3406F980)
        for address in PREPARE_CALLS:
            self.assertEqual(struct.unpack_from('>I', code, address - CODE_RAM)[0],
                             0x0C000000 | (self.runtime['code']['symbols']['af_v3_save_prepare'] >> 2 & 0x3FFFFFF))
        self.assertEqual(self.blob[PROFILE_OFFSET:PROFILE_OFFSET + 160],
                         profile_bytes(self.report['npc_draw']['imports'], self.report['furniture']['imports']))
        self.assertEqual(self.blob[BRIDGE:BRIDGE + 8], bytes.fromhex('27bdffc8afb2001c'))
        self.assertEqual(self.blob[BRIDGE + 16:BRIDGE + 24], bytes.fromhex('27bdffe8afbf0014'))
        self.assertTrue(self.runtime['native_save_hooks_enabled'])
        self.assertEqual(self.runtime['native_reader_calls_audited'], 12)

    def test_resident_code_and_state_allocation(self):
        helper = (OUTPUT / 'save_runtime/code.bin').read_bytes()
        self.assertLessEqual(CODE + len(helper), LIMIT)
        self.assertEqual(self.blob[CODE:CODE + len(helper)], helper)
        self.assertEqual(sha256(helper), self.runtime['code']['sha256'])
        self.assertIn('-DAF_V3_SAVE_RUNTIME=1', self.report['startup']['flags'])
        self.assertEqual(self.runtime['state_ram'], 0x8046C000)
        self.assertEqual(self.runtime['state_bytes'], 0x2C0)
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        for offset in (0x7FF0, 0xBFF0):
            self.assertEqual(self.blob[offset:offset + 16], bytes.fromhex('AF33C0DE') * 4)
        for row in self.report['furniture']['imports']:
            offset = int(row['object_vrom'], 16) - BLOB
            model = self.files[BLOB].extract(self.rom)[offset:offset + row['object_bytes']]
            self.assertEqual(sha256(model), row['object_sha256'])

    def test_current_composition_and_import_free_retention(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
