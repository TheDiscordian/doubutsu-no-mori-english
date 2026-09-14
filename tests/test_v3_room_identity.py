"""Current room placement/pickup composition and guarded inverse conversions."""
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
from aflib import apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
import v3_furniture_identity as identity

OUTPUT = ROOT / 'build/v3-room-identity-01'


class IdentityLogicTests(unittest.TestCase):
    def test_selected_and_native_unchecked_fallback(self):
        fixture = r'''
unsigned int enabled = 1;
int af_v3_furniture_import_profile(unsigned int n) {
    return n == 1161 || (n == 1198 && enabled);
}
unsigned int af_v3_furniture_item(unsigned int n, unsigned int r) {
    return (n == 1161 ? 0x3224 : 0x32b8) | (r & 3);
}
'''
        with tempfile.TemporaryDirectory(prefix='v3-identity-') as temporary:
            library = Path(temporary) / 'identity.so'
            subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                            str(ROOT / 'overlays/v3/identity.c'), '-x', 'c', '-', '-o', str(library)],
                           input=fixture, text=True, capture_output=True, check=True)
            api = ctypes.CDLL(str(library))
            api.af_v3_identity_item.argtypes = [ctypes.c_uint, ctypes.c_uint]
            api.af_v3_identity_item.restype = ctypes.c_uint
            for value in (0, 1, 946, 947, 948, 1023, 1161, 1198, 1266, 65535):
                expected = {1161: 0x3224, 1198: 0x32B8}.get(value, value * 4 + 0x1000)
                self.assertEqual(api.af_v3_identity_item(value, 0), expected)
            ctypes.c_uint.in_dll(api, 'enabled').value = 0
            self.assertEqual(api.af_v3_identity_item(1198, 0), 0x22B8)


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current room identity cartridge required')
class RoomIdentityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files = by_vrom(cls.rom)
        cls.parent = json.loads((ROOT / 'build/v3-placement-index-01/build.json').read_text())

    def test_six_words_only_and_guarded_source(self):
        final = self.files[identity.VROM].extract(self.rom)
        reloc = self.files[identity.RELOC].extract(self.rom)
        report = self.report['furniture_identity']
        original = bytearray(final)
        for row in report['sites']:
            target = report['code']['symbols'][row['symbol']]
            self.assertEqual(struct.unpack_from('>2I', final, row['start'] - identity.RAM),
                             (0x08000000 | (target >> 2 & 0x3FFFFFF), 0))
            struct.pack_into('>2I', original, row['start'] - identity.RAM, *row['expected'])
        self.assertEqual(sha256(original), identity.SOURCE_SHA)
        self.assertEqual(identity.inspect(original, reloc), report['sites'])
        self.assertEqual(sha256(final), report['output_sha256'])
        original[report['sites'][0]['start'] - identity.RAM] ^= 1
        with self.assertRaises(ValueError):
            identity.inspect(original, reloc)

    def test_bounds_crc_and_unchanged_dependencies(self):
        blob = self.files[BLOB].extract(self.rom)[:0xC000]
        helper = (OUTPUT / 'identity/code.bin').read_bytes()
        self.assertEqual(blob[identity.CODE:identity.CODE + len(helper)], helper)
        self.assertLessEqual(identity.CODE + len(helper), identity.LIMIT)
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob), identity.ABI))
        self.assertEqual(blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        for name, value in identity.EXPORTS.items():
            self.assertEqual(self.report['furniture']['code']['symbols'][name], value)
            self.assertEqual(self.report['furniture_identity']['code']['symbols'][name], value)
        for vrom, digest in self.parent['changed_resources'].items():
            if int(vrom, 16) in (BLOB, MODULE, identity.VROM):
                continue
            actual = int(self.report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(self.files[actual].extract(self.rom)), digest)
        for part in ('room', 'menu', 'save_runtime', 'hra', 'feng_shui'):
            self.assertEqual(self.report['furniture_menu' if part == 'menu' else
                                         'furniture_room' if part == 'room' else part]['code']['sha256'],
                             self.parent['furniture_menu' if part == 'menu' else
                                         'furniture_room' if part == 'room' else part]['code']['sha256'])

    def test_composition_patch_and_import_free_v2(self):
        native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        moved = {int(v, 16): int(t, 16) for v, t in self.report['relocated_resources'].items()}
        changes = {int(v, 16): self.files[moved.get(int(v, 16), int(v, 16))].extract(self.rom)
                   for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        resized = tuple(int(v, 16) for v in self.report['resized_resources'])
        self.assertEqual(compose(native, self.base, changes, added, resized=resized, relocated=moved), self.rom)
        self.assertEqual(compose(native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])


if __name__ == '__main__':
    unittest.main()
