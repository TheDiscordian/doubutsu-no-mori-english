"""Independent clothing-save encoding, migration, ownership, and installation."""
import ctypes as c
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE
from v3_save_clothing import ABI, DESCRIPTOR, PROFILE, RAM, STATE, VROM, install
from tests import test_v3_save_codec as legacy

OUTPUT = ROOT/'build/v3-clothing-save-02'


def fixture():
    bank, old = legacy.fixture()
    state = bytearray(old[:160]+bytes(32)+old[160:]+bytes(128))
    state[160+(0xBF >> 3)] = 0x80
    for player in range(4): state[PROFILE+512+player*32+(0xBF >> 3)] = 0x80
    return bank, state


def reference_pack(source, state):
    bank = bytearray(source)
    bank[4:8] = b'NAF3'
    bank[legacy.PAYLOAD:] = bytes(legacy.CAPSULE)
    struct.pack_into('>4sHHI', bank, legacy.PAYLOAD, b'AFS3', 2, legacy.CAPSULE, 2)
    ext = legacy.PAYLOAD
    bank[ext+0x18:ext+0xB8] = state[:160]
    bank[ext+0xC0:ext+0x2C0] = state[PROFILE:PROFILE+512]
    bank[ext+0x2C0:ext+0x2E0] = state[160:PROFILE]
    bank[ext+0x2E0:ext+0x360] = state[PROFILE+512:]
    payload = bytearray(bank[:ext])
    payload[0x12:0x14] = bytes(2)
    struct.pack_into('>I', bank, ext+12, zlib.crc32(payload))
    legacy.seal_extension(bank)
    legacy.checksum(bank)
    return bank


class ClothingSaveLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-clothing-save-')
        library = Path(cls.temp.name)/'codec.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
            '-DAF_V3_CLOTHING_PROFILE=1', str(ROOT/'overlays/v3/save_codec.c'), '-o', str(library)],
            capture_output=True, text=True, check=True)
        cls.api = c.CDLL(str(library))
        cls.api.af_v3_save_check.argtypes = (c.c_void_p, c.c_uint, c.c_void_p, c.c_void_p)
        cls.api.af_v3_save_pack.argtypes = (c.c_void_p, c.c_uint, c.c_void_p)
        cls.api.af_v3_save_collect.argtypes = (c.c_void_p, c.c_uint, c.c_uint, c.c_uint)
        previous = Path(cls.temp.name)/'previous.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
            str(ROOT/'overlays/v3/save_codec.c'), '-o', str(previous)],
            capture_output=True, text=True, check=True)
        cls.previous = c.CDLL(str(previous))
        cls.previous.af_v3_save_check.argtypes = (c.c_void_p, c.c_uint, c.c_void_p, c.c_void_p)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    @staticmethod
    def buffer(data): return (c.c_ubyte*len(data)).from_buffer_copy(data)

    def check(self, bank, profile, expected, state=None):
        data, current, out = self.buffer(bank), self.buffer(profile), self.buffer(b'\xA5'*STATE)
        self.assertEqual(self.api.af_v3_save_check(data, len(bank), current, out), expected)
        self.assertEqual(bytes(out), bytes(state) if state is not None else b'\xA5'*STATE)
        self.assertEqual(bytes(data), bank)
        return bytes(out)

    def test_complete_independent_encoding_and_legacy_migration(self):
        bank, state = fixture()
        packed = self.buffer(bank)
        self.assertEqual(self.api.af_v3_save_pack(packed, len(bank), self.buffer(state)), 1)
        self.assertEqual(bytes(packed), reference_pack(bank, state))
        self.check(bytes(packed), state[:PROFILE], 1, state)
        unchanged = self.buffer(b'\xA5'*672)
        self.assertEqual(self.previous.af_v3_save_check(packed, len(bank), self.buffer(state[:160]), unchanged), -4)
        self.assertEqual(bytes(unchanged), b'\xA5'*672)
        self.assertEqual(self.api.af_v3_save_pack(packed, len(bank), self.buffer(state)), 1)
        self.assertEqual(bytes(packed), reference_pack(bank, state))
        self.check(bank, state[:PROFILE], 0, state[:PROFILE]+bytes(640))
        old_bank, old_state = legacy.fixture()
        self.check(legacy.reference_pack(old_bank, old_state), state[:PROFILE], 1,
                   state[:PROFILE]+old_state[160:]+bytes(128))

    def test_four_player_clothing_does_not_alias_furniture_rotations(self):
        _, full = fixture()
        raw = full[:PROFILE]+bytes(640)
        state = self.buffer(b'\xA5'*16+raw+b'\xA5'*16)
        pointer = c.byref(state, 16)
        for player in range(4):
            self.assertEqual(self.api.af_v3_save_collect(pointer, player, 0x34BF, 0), 0)
            self.assertEqual(self.api.af_v3_save_collect(pointer, player, 0x34BF, 1), 1)
            self.assertEqual(self.api.af_v3_save_collect(pointer, player, 0x34BF, 0), 1)
            self.assertEqual(self.api.af_v3_save_collect(pointer, player, 0x34BC, 1), -7)
        self.assertEqual(bytes(state[16+PROFILE:16+PROFILE+512]), bytes(512))
        self.assertEqual(bytes(state[16+PROFILE+512:-16]), full[PROFILE+512:])
        self.assertEqual(self.api.af_v3_save_collect(pointer, 0, 0x3225, 1), 1)
        self.assertEqual(self.api.af_v3_save_collect(pointer, 0, 0x3227, 0), 1)
        self.assertEqual(self.api.af_v3_save_collect(pointer, 4, 0x34BF, 1), -1)
        self.assertEqual(self.api.af_v3_save_collect(pointer, 0, 0x24BF, 1), -1)
        self.assertEqual(bytes(state[:16])+bytes(state[-16:]), b'\xA5'*32)

    def test_missing_clothing_corruption_and_overlapping_buffers(self):
        bank, state = fixture()
        packed = reference_pack(bank, state)
        missing = bytearray(state[:PROFILE]); missing[183] = 0
        self.check(packed, missing, -7)
        more = bytearray(state[:PROFILE]); more[182] |= 1
        self.check(packed, more, 1, more+state[PROFILE:])
        for offset, error, reseal in ((0x2E0, -6, False), (0x2E0, -8, True),
                                      (0x360, -4, True), (8, -4, True)):
            damaged = bytearray(packed)
            damaged[legacy.PAYLOAD+offset] ^= 1
            if reseal: legacy.seal_extension(damaged)
            self.check(damaged, state[:PROFILE], error)
        corrupted = bytearray(packed); corrupted[0x400] ^= 1
        legacy.checksum(corrupted)
        self.check(corrupted, state[:PROFILE], -5)
        bad_state = bytearray(state); bad_state[PROFILE+512] |= 1
        dest = self.buffer(bank)
        self.assertEqual(self.api.af_v3_save_pack(dest, len(bank), self.buffer(bad_state)), -8)
        self.assertEqual(bytes(dest), bank)
        self.assertEqual(self.api.af_v3_save_pack(dest, len(bank), c.byref(dest, 0x100)), -1)
        self.assertEqual(self.api.af_v3_save_check(dest, len(bank), self.buffer(state[:PROFILE]), c.byref(dest, 0x200)), -1)
        self.assertEqual(bytes(dest), bank)


class ClothingStartup(unittest.TestCase):
    def test_sanitized_secondary_code_loading_and_rejection(self):
        with tempfile.TemporaryDirectory(prefix='v3-clothing-startup-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/fixtures/v3_clothing_startup.c'), str(ROOT/'runtime/crc32.c'),
                '-o', str(binary)], capture_output=True, text=True, check=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True, check=True, timeout=20)
            self.assertIn('rejection checks pass', result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current clothing-save build required')
class ClothingSaveCartridge(unittest.TestCase):
    def test_extension_code_descriptor_dispatch_and_runtime(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        parent = json.loads((ROOT/'build/v3-player-clothing-01/build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        files = by_vrom(rom)
        blob = files[BLOB].extract(rom)
        ext = report['clothing']['save_extension']
        resource = blob[VROM-BLOB:]
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(sha256(resource), ext['resource_sha256'])
        self.assertEqual(struct.unpack_from('>4I', blob, DESCRIPTOR), (VROM, len(resource), zlib.crc32(resource), RAM))
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        self.assertLessEqual(len(blob), 0x10000)
        self.assertEqual(report['save_runtime']['state_bytes'], 864)
        self.assertEqual(report['save_codec']['format_version'], 2)
        self.assertEqual(report['save_codec']['registry_version'], 2)
        self.assertEqual(report['save_codec']['work_state_bytes'], STATE)
        profile = bytes.fromhex(report['save_runtime']['profile_hex'])
        self.assertEqual(len(profile), PROFILE)
        self.assertEqual(profile[:160].hex(), parent['save_runtime']['profile_hex'])
        self.assertEqual(profile[160:], bytes(23)+b'\x80'+bytes(8))
        self.assertEqual(blob[0x20:0xE0], profile)
        codec = bytearray(blob[0xB400:0xB400+report['save_codec']['code']['bytes']])
        for hook in ext['public_entries']:
            at = int(hook['entry'], 16)-0x8046B400
            self.assertEqual(codec[at:at+8].hex(), hook['after'])
            codec[at:at+8] = bytes.fromhex(hook['before'])
        self.assertEqual(sha256(codec), parent['save_codec']['code']['sha256'])
        staging = bytearray(blob[:0xC000])
        staging[DESCRIPTOR:DESCRIPTOR+16] = bytes(16)
        staging[0xB400:0xB400+len(codec)] = codec
        helper = resource[:ext['code']['bytes']]
        rebuilt, _ = install(staging, helper, ext['code'], report['save_codec']['code'], report['save_runtime'])
        self.assertEqual(rebuilt, resource)
        self.assertEqual(staging, blob[:0xC000])
        staging[DESCRIPTOR:DESCRIPTOR+16] = bytes(16)
        staging[0xB400:0xB400+len(codec)] = codec
        staging[0xB450] ^= 1
        with self.assertRaises(ValueError):
            install(staging, helper, ext['code'], report['save_codec']['code'], report['save_runtime'])
        for field in ('npc_draw', 'villager_audio', 'villager_text', 'asset'):
            self.assertEqual(report[field], parent[field])
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
