"""Current installed animated resources, shared readers, and expanded ROM storage."""
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
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, u32
from v3_asset_loader import BLOB, CONFIG, MODULE
from v3_speed_bag import ENGINE, validate_calls
from v3_speed_bag_runtime import ABI, END, PROGRAM, ROW, SOUND, VTABLE
from v3_storage import START, END as STORAGE_END, pack

OUTPUT = ROOT/'build/v3-speed-bag-runtime-03'
PREVIOUS = ROOT/'build/v3-speed-bag-sound-03'


class RuntimeHostTests(unittest.TestCase):
    def test_sanitized_actual_animated_loader(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-animated-') as directory:
            binary = Path(directory)/'test'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_speed_bag_runtime_test.c'), '-o', str(binary)],
                check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn('rotations pass', result.stdout)

    def test_ordered_resource_packing_and_overlap_rejection(self):
        resources = {START+0x100: b'A'*16, START+0x80: b'B'*16}
        result = pack(b'C'*32, resources, {})
        self.assertEqual(result, b'C'*32+bytes(96)+b'B'*16+bytes(112)+b'A'*16)
        for resources in ({START+16: b'A'*32}, {STORAGE_END: b'A'*16},
                          {START+32: b'A'*32, START+48: b'B'*16}):
            with self.assertRaises(ValueError): pack(bytes(32), resources, {})
        with self.assertRaises(ValueError):
            pack(bytes(32), {}, {0: SimpleNamespace(vstart=START+0x10000, vend=START+0x10010)})
        for prefix in (b'', bytes(17), bytes(STORAGE_END-START+16)):
            with self.assertRaises(ValueError): pack(prefix, {}, {})
        with self.assertRaises(ValueError): pack(bytes(32), {START+32: bytes(17)}, {})


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current animated cartridge required')
class RuntimeCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.files = by_vrom(cls.rom)
        cls.file = cls.files[BLOB].extract(cls.rom)
        cls.blob = cls.file[:0xC000]

    def test_complete_installed_callbacks_model_metadata_and_disabled_identity(self):
        row = self.report['speed_bag']
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(u32(self.blob, 4), ABI)
        self.assertEqual(struct.unpack_from('>HHI', self.blob, ROW), (1236, 0x3350, 0))
        profile = self.blob[ROW+8:ROW+76]
        self.assertEqual(sha256(profile), row['profile_sha256'])
        self.assertEqual(struct.unpack_from('>4I', profile), (START+0x10000, START+0x10E90, 0x6000000, 0x6000E90))
        self.assertEqual(profile[16:48], bytes(32))
        self.assertEqual(profile[48:64].hex(), row['artwork']['donor_profile_scalar_hex'])
        self.assertEqual(u32(self.blob, 0x5800+1236*4), 0x80460000+ROW+8)
        self.assertEqual(u32(profile, 64), 0x80460000+VTABLE)
        self.assertEqual(struct.unpack_from('>5I', self.blob, VTABLE), (*row['callback_entries'], 0, 0))
        callback = self.blob[PROGRAM:PROGRAM+row['callback_bytes']]
        self.assertEqual(sha256(callback), row['callbacks']['sha256'])
        validate_calls(callback, (OUTPUT/'speed-bag/callbacks/relocations.txt').read_text(),
                       {**ENGINE, 'af_v3_speed_bag_sound': 0x80460000+SOUND})
        self.assertEqual(self.blob[SOUND:SOUND+16].hex(), row['sound_adapter_hex'])
        self.assertEqual(sha256(self.file[0x10000:0x10E90]), row['object_sha256'])
        self.assertEqual(self.blob[0x72E0:0x7300], struct.pack('>HHHBB', 1236, 0x3350, 2990, 0, 1)+b'speed bag       '+bytes(8))
        self.assertFalse(row['enabled'] or row['saved_profile_included'] or row['selectable'])
        # Other furniture records and collection bridges remain untouched.
        old_rom=(PREVIOUS/'animal-forest-v3-asset-loader.z64').read_bytes()
        old=by_vrom(old_rom)[0x03F00000].extract(old_rom)
        for first,last in ((0x6C00,0x6F20),(0x7200,0x7208),(0x7250,0x7258),(0x72A0,0x72E0)):
            self.assertEqual(self.blob[first:last],old[first:last])

    def test_storage_startup_existing_directory_and_save_profile_retention(self):
        self.assertEqual(len(self.file), 0x10E90)
        self.assertEqual(self.report['storage'], {'vrom': START, 'limit': STORAGE_END, 'bytes': len(self.file)})
        config = struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG)
        self.assertEqual(config, (BLOB, 0xC000, zlib.crc32(self.blob), ABI))
        extra_vrom, count, crc, ram = struct.unpack_from('>4I', self.blob, 0xE0)
        self.assertEqual((extra_vrom, ram), (START+0xF400, 0x8046D000))
        self.assertEqual(zlib.crc32(self.file[0xF400:0xF400+count]), crc)
        prior = json.loads((PREVIOUS/'build.json').read_text())
        self.assertEqual(self.report['save_runtime']['profile_hex'], prior['save_runtime']['profile_hex'])
        old_rom=(PREVIOUS/'animal-forest-v3-asset-loader.z64').read_bytes()
        old=by_vrom(old_rom)
        self.assertEqual(set(self.files), set(old)-{0x03F00000}|{START})
        for v, entry in old.items():
            self.assertEqual(self.files[START if v==0x03F00000 else v].index, entry.index)
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
