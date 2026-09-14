"""Independent CRC/encoding, save-profile rejection, bounds, and cartridge checks."""
import ctypes
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
from v3_save_codec import ABI, BANK, BLOB_SIZE, CAPSULE, CODE, PAYLOAD, PROFILE, STATE, install

OUTPUT = ROOT / 'build/v3-save-codec-01'


def checksum(bank):
    bank[0x12:0x14] = bytes(2)
    total = sum(struct.unpack('>' + 'H' * (PAYLOAD // 2), bank[:PAYLOAD]))
    struct.pack_into('>H', bank, 0x12, -total & 0xFFFF)


def fixture():
    bank = bytearray((i * 37 + 11) & 255 for i in range(BANK))
    bank[4:8] = b'NAFJ'
    bank[8:10] = bank[0x2F68:0x2F6A] = b'\x30\x12'
    checksum(bank)
    state = bytearray(STATE)
    for actor in (234, 237):
        state[actor >> 3] |= 1 << (actor & 7)
    for index in (137, 174):
        state[32 + (index >> 3)] |= 1 << (index & 7)
    for player, index in ((0, 137), (1, 174), (2, 137), (2, 174), (3, 174)):
        state[PROFILE + player * 128 + (index >> 3)] |= 1 << (index & 7)
    return bank, state


def seal_extension(bank):
    at = PAYLOAD + 0x10
    bank[at:at + 4] = bytes(4)
    struct.pack_into('>I', bank, at, zlib.crc32(bank[PAYLOAD:]))


def reference_pack(source, state):
    bank = bytearray(source)
    bank[4:8] = b'NAF3'
    bank[PAYLOAD:] = bytes(CAPSULE)
    struct.pack_into('>4sHHI', bank, PAYLOAD, b'AFS3', 1, CAPSULE, 1)
    bank[PAYLOAD + 0x18:PAYLOAD + 0xB8] = state[:PROFILE]
    bank[PAYLOAD + 0xC0:PAYLOAD + 0x2C0] = state[PROFILE:]
    payload = bytearray(bank[:PAYLOAD])
    payload[0x12:0x14] = bytes(2)
    struct.pack_into('>I', bank, PAYLOAD + 12, zlib.crc32(payload))
    seal_extension(bank)
    checksum(bank)
    return bank


class SaveCodecHostTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='af-v3-save-tests-')
        binary = Path(cls.temp.name) / 'codec.so'
        subprocess.run(['gcc', '-std=c11', '-O2', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
            str(ROOT / 'overlays/v3/save_codec.c'), '-o', str(binary)], check=True, capture_output=True)
        cls.codec = ctypes.CDLL(str(binary))
        ptr = ctypes.POINTER(ctypes.c_ubyte)
        cls.codec.af_v3_save_check.argtypes = (ptr, ctypes.c_uint, ptr, ptr)
        cls.codec.af_v3_save_pack.argtypes = (ptr, ctypes.c_uint, ptr)
        cls.codec.af_v3_save_collect.argtypes = (ptr, ctypes.c_uint, ctypes.c_uint, ctypes.c_uint)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def buffer(self, value):
        return (ctypes.c_ubyte * len(value)).from_buffer_copy(value)

    def checked(self, bank, current, expected):
        src, profile, out = self.buffer(bank), self.buffer(current), self.buffer(b'\xA5' * STATE)
        result = self.codec.af_v3_save_check(src, len(bank), profile, out)
        self.assertEqual(result, expected)
        self.assertEqual(bytes(src), bank)
        self.assertEqual(bytes(profile), current)
        if expected < 0:
            self.assertEqual(bytes(out), b'\xA5' * STATE)
        return bytes(out)

    def test_independent_complete_encoding_and_determinism(self):
        source, state = fixture()
        src, data = self.buffer(source), self.buffer(state)
        self.assertEqual(self.codec.af_v3_save_pack(src, BANK, data), 1)
        expected = reference_pack(source, state)
        self.assertEqual(bytes(src), expected)
        self.assertEqual(bytes(data), state)
        self.assertEqual(self.checked(expected, state[:PROFILE], 1), state)
        self.assertEqual(self.codec.af_v3_save_pack(src, BANK, data), 1)
        self.assertEqual(bytes(src), expected)
        for i, (before, after) in enumerate(zip(source[:PAYLOAD], expected)):
            if i not in (*range(4, 8), 0x12, 0x13):
                self.assertEqual(before, after)

    def test_legacy_ignores_uninitialised_padding_and_additions(self):
        source, state = fixture()
        out = self.checked(source, state[:PROFILE], 0)
        self.assertEqual(out, state[:PROFILE] + bytes(512))
        source[PAYLOAD:] = b'\xFF' * CAPSULE
        self.assertEqual(self.checked(source, state[:PROFILE], 0), out)
        bank = reference_pack(source, state)
        profile = bytearray(state[:PROFILE])
        profile[31] |= 0x80
        profile[-1] |= 0x80
        self.assertEqual(self.checked(bank, profile, 1), profile + state[PROFILE:])
        for offset in (29, 32 + (137 >> 3), 32 + (174 >> 3)):
            profile = bytearray(state[:PROFILE])
            profile[offset] = 0
            self.checked(bank, profile, -7)

    def test_corruption_torn_binding_and_unknown_formats(self):
        source, state = fixture()
        bank = reference_pack(source, state)
        mutations = ((4, -2), (8, -2), (0x2F68, -2), (0x12, -3), (0x800, -3),
                     (PAYLOAD, -4), (PAYLOAD + 4, -4), (PAYLOAD + 7, -4),
                     (PAYLOAD + 8, -4), (PAYLOAD + 0x14, -4), (PAYLOAD + 0xB8, -4),
                     (PAYLOAD + 0x2C0, -4), (BANK - 1, -4),
                     (PAYLOAD + 0x18, -6), (PAYLOAD + 0xC0, -6), (PAYLOAD + 0x10, -6))
        for at, expected in mutations:
            with self.subTest(at=hex(at)):
                changed = bytearray(bank)
                changed[at] ^= 1
                self.checked(changed, state[:PROFILE], expected)
        changed = bytearray(bank)
        changed[0x800] ^= 1
        checksum(changed)  # Native checksum now passes; paired extension must not.
        self.checked(changed, state[:PROFILE], -5)
        different = bytearray(source)
        different[0x900] ^= 1
        other = reference_pack(different, state)
        changed = bytearray(bank[:PAYLOAD] + other[PAYLOAD:])
        self.checked(changed, state[:PROFILE], -5)
        changed = bytearray(bank)
        changed[PAYLOAD + 0xC0] |= 1  # Owned furniture is not in the saved profile.
        seal_extension(changed)
        self.checked(changed, state[:PROFILE], -8)
        bad_state = bytearray(state)
        bad_state[PROFILE] |= 1
        src = self.buffer(source)
        self.assertEqual(self.codec.af_v3_save_pack(src, BANK, self.buffer(bad_state)), -8)
        self.assertEqual(bytes(src), source)

    def test_sanitized_full_catalogue_capacity_and_buffer_guards(self):
        binary = Path(self.temp.name) / 'sanitized'
        subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
            str(ROOT / 'tests/v3_save_codec_test.c'), '-o', str(binary)], check=True, capture_output=True)
        result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
        self.assertIn('guards pass', result.stdout)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current save-codec cartridge required')
class SaveCodecCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)[:BLOB_SIZE]

    def test_code_guards_and_native_save_paths_unchanged(self):
        report = self.report['save_codec']
        compiled = (OUTPUT / 'save_codec/code.bin').read_bytes()
        self.assertEqual(self.blob[CODE:CODE + len(compiled)], compiled)
        self.assertEqual(sha256(compiled), report['helper_sha256'])
        for start, end in ((0x8008ECA0, 0x80090120), (0x800CDB10, 0x800CE120)):
            a, b = start - CODE_RAM, end - CODE_RAM
            self.assertEqual(self.files[CODE_VROM].extract(self.rom)[a:b],
                             self.original[CODE_VROM].extract(self.base)[a:b])
        self.assertFalse(report['native_save_hooks_enabled'])
        self.assertFalse(report['native_catalogue_hooks_enabled'])
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(self.blob), ABI))
        self.assertEqual(self.blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        for at in (CODE, BLOB_SIZE - 20):
            changed = bytearray(self.blob)
            changed[CODE:-16] = bytes(BLOB_SIZE - CODE - 16)
            changed[at] = 1
            with self.assertRaises(ValueError):
                install(changed, compiled, report['code']['symbols'], self.report['furniture_pockets']['code'])

    def test_current_composition_and_import_free_output(self):
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        changes = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        self.assertEqual(compose(self.native, self.base, changes, added), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
