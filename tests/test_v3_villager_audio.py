"""Focused melody conversion, source/operand bounds, and runtime checks."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import by_vrom, sha256, CODE_RAM, CODE_VROM, apply_ups
from v3_villager_audio import Dol, sequence_programs, program_shape, instrument
from v3_audio_runtime import TABLE, STATE, WIDE_PATCHES
from v3_asset_loader import BLOB, compose


class HostTests(unittest.TestCase):
    def test_runtime_protocol_and_full_voice_ids_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-melody-') as temp:
            binary = Path(temp) / 'check'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_melody_test.c'), '-o', str(binary)], check=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('guards pass', result.stdout)

    def test_dol_sections_are_address_mapped_and_bounded(self):
        data = bytearray(288)
        struct.pack_into('>I', data, 0, 256)
        struct.pack_into('>I', data, 0x48, 0x80010000)
        struct.pack_into('>I', data, 0x90, 32)
        data[256:] = bytes(range(32))
        dol = Dol(bytes(data))
        self.assertEqual(dol.read(0x80010008, 4), bytes(range(8, 12)))
        for address, size in ((0x80010000, 0), (0x8001001C, 8), (256, 4)):
            with self.assertRaises(ValueError): dol.read(address, size)
        struct.pack_into('>I', data, 4, 256)
        struct.pack_into('>I', data, 0x4C, 0x80020000)
        struct.pack_into('>I', data, 0x94, 32)
        with self.assertRaises(ValueError): Dol(bytes(data))

    def test_melody_offsets_terminators_and_native_slot_bounds(self):
        program = bytes.fromhex('EB0300780001FF402034FF')
        data = bytearray(256)
        struct.pack_into('>19H', data, 4, *(42 + i * len(program) for i in range(19)))
        for i in range(19): data[42 + i * len(program):42 + (i + 1) * len(program)] = program
        self.assertEqual(len(sequence_programs(bytes(data))), 19)
        for at, value in ((4, 255), (42, 254), (47, 2), (52, 0), (255, 99)):
            changed = data.copy(); changed[at] = value
            with self.assertRaises((ValueError, IndexError)): sequence_programs(bytes(changed))
        with self.assertRaises(ValueError): sequence_programs(bytes(0x610))


@unittest.skipUnless((ROOT / 'build/v3-audio-runtime-02/build.json').exists(), 'Current local V3 audio build required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT / 'build/v3-audio-runtime-02'
        cls.report = json.loads((cls.out / 'build.json').read_text())
        cls.rom = (cls.out / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files = by_vrom(cls.rom)

    def test_installed_assets_and_shared_sample_dependencies(self):
        blob = self.files[BLOB].extract(self.rom)
        report = self.report['villager_audio']
        self.assertEqual(struct.unpack_from('>I', blob, 4)[0], 3)
        self.assertEqual(blob[STATE:STATE + 32], b'\xff' * 32)
        self.assertEqual(set(report['conversion']['instruments']), {'0', '1', '48', '49'})
        for row in report['imports']:
            pointer, size = struct.unpack_from('>II', blob, TABLE + (row['voice'] - 256) * 8)
            self.assertEqual((pointer, size), (int(row['ram'], 16), row['bytes']))
            data = blob[pointer - 0x80460000:pointer - 0x80460000 + size]
            self.assertEqual(sha256(data), row['sha256'])
            self.assertEqual(len(sequence_programs(data)), 19)
        for voice in set(range(256, 299)) - {285, 286}:
            self.assertEqual(blob[TABLE + (voice - 256) * 8:TABLE + (voice - 255) * 8], bytes(8))
        self.assertEqual(blob[-16:], bytes.fromhex('AF33C0DE') * 4)

    def test_wide_calls_native_resources_and_patch_reconstruction(self):
        code = self.files[CODE_VROM].extract(self.rom)
        sizes = struct.unpack_from('>256I', code, 0x80119240 - CODE_RAM)
        offsets = struct.unpack_from('>256I', code, 0x80119640 - CODE_RAM)
        for size, offset in zip(sizes, offsets):
            self.assertTrue(42 <= size <= 0x600 and size % 16 == 0)
            self.assertTrue(0 <= offset <= 0x18D10 - size)
        for address, (_, expected) in WIDE_PATCHES.items():
            self.assertEqual(struct.unpack_from('>I', code, address - CODE_RAM)[0], expected)
        for address, name in ((0x800FCEEC, 'af_v3_melody_start'), (0x800FD0D4, 'af_v3_melody_count')):
            target = self.report['asset']['symbols'][name]
            self.assertEqual(struct.unpack_from('>II', code, address - CODE_RAM), (0x08000000 | target >> 2 & 0x3FFFFFF, 0))
        native_files = by_vrom(self.native)
        for vrom in (0x27130, 0xE4D10, 0x13D9A0):
            self.assertEqual(self.files[vrom].extract(self.rom), native_files[vrom].extract(self.native))
        for path, digest in self.report['sources'].items():
            self.assertEqual(sha256((ROOT / path).read_bytes()), digest, path)
        self.assertEqual(apply_ups(self.native, (self.out / 'asset-loader.ups').read_bytes()), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)


if __name__ == '__main__': unittest.main()
