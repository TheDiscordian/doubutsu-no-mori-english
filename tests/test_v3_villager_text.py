"""Focused shared-reader/default-reference checks on the current V3 cartridge."""
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
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, apply_ups
from v3_asset_loader import BLOB, MODULE, MODULE_RAM, CONFIG, compose
from v3_villager_text import ABI, BLOB_SIZE, DATA, STRIDE, CODE, BRIDGES, jump


class HostTests(unittest.TestCase):
    def test_text_and_borrowed_reference_contract(self):
        self.sanitized('v3_villager_text_test.c', [], 'guards pass')

    def test_abi_four_startup_and_complete_code_cache_range(self):
        self.sanitized('v3_asset_loader_test.c', ['-DAF_V3_ABI=4', '-DAF_V3_BLOB_SIZE=32768',
            str(ROOT / 'runtime/crc32.c')], 'rejection paths pass')

    def sanitized(self, file, args, message):
        with tempfile.TemporaryDirectory(prefix='af-v3-text-') as temp:
            binary = Path(temp) / 'check'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests' / file), *args, '-o', str(binary)], check=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn(message, result.stdout)


@unittest.skipUnless((ROOT / 'build/v3-villager-text-02/build.json').exists(), 'Current local V3 text build required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT / 'build/v3-villager-text-02'
        cls.report = json.loads((cls.out / 'build.json').read_text())
        cls.rom = (cls.out / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.files = by_vrom(cls.rom)
        cls.blob = cls.files[BLOB].extract(cls.rom)
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()

    def test_complete_owned_metadata_and_programs(self):
        self.assertEqual(len(self.blob), BLOB_SIZE)
        self.assertEqual(struct.unpack_from('>5I', self.blob), (0x41465633, ABI, BLOB_SIZE, 430, 410))
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        self.assertEqual(self.blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        text = self.report['villager_text']
        self.assertEqual(sha256(self.blob[CODE:CODE + text['code']['bytes']]), text['code']['sha256'])
        slots = set()
        for row in text['imports']:
            actor = int(row['actor_id'], 16); slot = actor - 0xE0DA; slots.add(slot)
            data = self.blob[DATA + slot * STRIDE:DATA + (slot + 1) * STRIDE]
            self.assertEqual(sha256(data), row['record_sha256'])
            self.assertEqual(struct.unpack_from('>HH4B', data),
                             (actor, int(row['donor_clothing_id'], 16), row['personality'], row['donor_umbrella'], 0, 1))
            self.assertEqual(data[8:16], row['name'].encode().ljust(8, b' '))
            self.assertEqual(data[16:26], row['catchphrase'].encode().ljust(10, b' '))
            self.assertEqual(data[26:30], bytes.fromhex(row['saved_default_key']))
            self.assertEqual(data[30:], bytes(2))
        self.assertEqual(slots, {16, 19})
        for slot in set(range(20)) - slots:
            self.assertEqual(self.blob[DATA + slot * STRIDE:DATA + (slot + 1) * STRIDE], bytes(STRIDE))

    def test_real_hook_destinations_and_original_return_bridges(self):
        syms = self.report['villager_text']['code']['symbols']
        for address, bridge, helper, expected in BRIDGES:
            vrom, base = (MODULE, MODULE_RAM) if address >= MODULE_RAM else (CODE_VROM, CODE_RAM)
            data = self.files[vrom].extract(self.rom)
            self.assertEqual(struct.unpack_from('>II', data, address - base), (jump(syms[helper]), 0))
            self.assertEqual(struct.unpack_from('>4I', self.blob, bridge), (*expected, jump(address + 8), 0))
        self.assertEqual(struct.unpack_from('>II', self.files[MODULE].extract(self.rom), 0x80195D20 - MODULE_RAM),
                         (jump(syms['af_v3_actor_name']), 0))
        # Original name and catchphrase resources retain their native ownership.
        before = by_vrom(self.base)
        for vrom in (0xE04000, 0xE03000, 0xE02000, 0x2C00000, 0x2E00000):
            self.assertEqual(self.files[vrom].extract(self.rom), before[vrom].extract(self.base))

    def test_sources_reconstruction_and_translation_only_retention(self):
        self.assertTrue(self.report['saved_format_changed'])
        self.assertFalse(self.report['saved_layout_changed'])
        self.assertIn('do not load those saves in V2', self.report['save_warning'])
        for path, digest in self.report['sources'].items():
            self.assertEqual(sha256((ROOT / path).read_bytes()), digest, path)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (self.out / 'asset-loader.ups').read_bytes()), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)


if __name__ == '__main__': unittest.main()
