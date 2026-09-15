"""Current campsite scene/field integration; no historical cartridge replays."""
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
from aflib import CODE_VROM, CODE_RAM, by_vrom, sha256, n64_checksum, DMA_START, DMA_END
from v3_asset_loader import BLOB, MODULE, CONFIG
import v3_campsite_scene as scene
import v3_campsite_runtime as runtime

OUTPUT = ROOT / 'build/v3-campsite-runtime-03'


class CampsiteRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_bytes())
        cls.base = scene.BASE.read_bytes()
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob, cls.previous = cls.files[BLOB].extract(cls.rom), cls.old[BLOB].extract(cls.base)

    def test_sanitized_callbacks_and_expanded_startup_caches(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-campsite-') as directory:
            for test, extras, args in (
                ('v3_campsite_scene_test.c', [], [str(runtime.SCENE_BUILD / 'packet.bin')]),
                ('v3_accessory_startup_test.c', ['-DAF_V3_ABI=71', '-DAF_V3_ACCESSORY_BYTES=192528',
                    '-DAF_V3_ACCESSORY_VROM=0x02400000', '-DAF_V3_WESTERN_LARGE=1', '-DAF_V3_CAMPSITE=1',
                    str(ROOT / 'runtime/crc32.c')], [])):
                binary = Path(directory) / test
                subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                    str(ROOT / 'tests' / test), *extras, '-o', str(binary)], check=True, capture_output=True)
                result = subprocess.run([str(binary), *args], check=True, capture_output=True, timeout=20)
                self.assertIn(b'pass', result.stdout)

    def test_complete_packet_fields_assets_and_startup(self):
        package = self.blob[runtime.PACKAGE:runtime.PACKAGE + runtime.PACKAGE_SIZE]
        self.assertEqual(struct.unpack_from('>4I', self.blob, 0xF0),
                         (BLOB + runtime.PACKAGE, runtime.PACKAGE_SIZE, zlib.crc32(package), runtime.PACKAGE_RAM))
        self.assertEqual(sha256(package), self.report['campsite']['package_sha256'])
        self.assertEqual(package[8:12], struct.pack('>I', runtime.PACKAGE_SIZE))
        self.assertEqual(package[-16:], bytes.fromhex('AFACC0DE') * 4)
        self.assertEqual(package[0x2D000:0x2D010], bytes.fromhex('AFACC0DE') * 4)
        self.assertEqual(package[0x2E000:0x2F000], (runtime.SCENE_BUILD / 'packet.bin').read_bytes())
        for row in self.report['campsite']['resources']:
            offset = row['vrom'] - BLOB
            self.assertEqual(sha256(self.blob[offset:offset + row['bytes']]), row['sha256'])
        at = scene.FIELD_VROM - BLOB
        original = self.old[scene.NATIVE_FIELDS].extract(self.base)
        self.assertEqual(self.blob[at:at + 35 * 0x88], original[:35 * 0x88])
        self.assertEqual(struct.unpack_from('>HH', self.blob, at + 35 * 0x88), (0x3012, 0x0101))
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(self.blob[:0xC000]), 71))
        self.assertLess(runtime.PACKAGE_RAM + runtime.PACKAGE_SIZE, self.report['furniture']['bank_pool']['start'])
        self.assertEqual(self.blob[0x20:0xE0], self.previous[0x20:0xE0])

    def test_only_reviewed_owners_change_and_relocations_remain_bounded(self):
        changed = {v for v in self.files if self.files[v].extract(self.rom) != self.old[v].extract(self.base)}
        self.assertEqual(changed, {0x19D40, BLOB, MODULE, CODE_VROM, runtime.PLAY, runtime.PLAY_RELOC})
        directory = bytearray(self.files[0x19D40].extract(self.rom))
        old_directory = self.old[0x19D40].extract(self.base)
        for vrom in (BLOB, runtime.PLAY, runtime.PLAY_RELOC):
            at = DMA_START - 0x19D40 + self.files[vrom].index * 16
            directory[at:at + 16] = old_directory[at:at + 16]
        self.assertEqual(directory, old_directory)
        for hook in self.report['campsite']['hooks']:
            address = hook['address']
            vrom, ram = (runtime.PLAY, runtime.PLAY_RAM) if address >= runtime.PLAY_RAM else (CODE_VROM, CODE_RAM)
            data = self.files[vrom].extract(self.rom)
            self.assertEqual(data[address - ram:address - ram + len(bytes.fromhex(hook['after']))].hex(), hook['after'])
        moved = self.report['campsite']['resource_moves']
        self.assertEqual([r['vrom'] for r in moved], [runtime.PLAY, runtime.PLAY_RELOC])
        for row in moved:
            entry = self.files[row['vrom']]
            self.assertEqual((entry.index, entry.vstart, entry.vend),
                             (self.old[row['vrom']].index, row['vrom'], row['vrom'] + row['bytes']))
            self.assertEqual(entry.pend, 0)
            self.assertEqual(sha256(entry.extract(self.rom)), row['sha256'])
        reloc = self.files[runtime.PLAY_RELOC].extract(self.rom)
        self.assertEqual(struct.unpack_from('>5I', reloc), (0x1840, 0xA0, 0xC0, 0xF0, 127))
        self.assertEqual(self.report['campsite']['removed_play_relocations'], [0x44001818])
        self.assertEqual(len(self.files), 3389)
        self.assertEqual(self.rom[DMA_END - 16:DMA_END], bytes(16))
        self.assertEqual(struct.unpack_from('>II', self.rom, 0x10), n64_checksum(self.rom))
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertFalse(self.report['campsite']['acquisition_installed'])
        self.assertFalse(self.report['campsite']['web_patcher_enabled'])


if __name__ == '__main__':
    unittest.main()
