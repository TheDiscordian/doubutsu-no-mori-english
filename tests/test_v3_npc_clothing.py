"""NPC queue lifetime, fixed shirt identities, guarded owner edits, and cartridge."""
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
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE
from v3_npc_clothing import ABI, ENTRIES, WINDOWS, guard_incoming, patch_owners
from v3_npc_draw import OWNERS

OUTPUT = ROOT/'build/v3-npc-clothing-01'


class NpcClothingLogic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-npc-clothing-')
        library = Path(cls.temp.name)/'clothing.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
            str(ROOT/'overlays/v3/clothing.c'), str(ROOT/'overlays/v3/npc_clothing.c'),
            str(ROOT/'tests/fixtures/v3_npc_clothing.c'), '-o', str(library)],
            capture_output=True, text=True, check=True)
        cls.api = c.CDLL(str(library))
        for _, name in ENTRIES:
            getattr(cls.api, name).argtypes = (c.c_void_p, c.c_int)
        cls.api.af_v3_clothing_checked_index.argtypes = (c.c_void_p,)

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.row = (c.c_ubyte*32).in_dll(self.api, 'af_v3_clothing')
        self.row[:] = struct.pack('=HHIHBB16sI', 0x34BF, 0x10BF, 0x3F0F000, 380, 1, 0, b'cherry shirt    ', 0)
        self.slot = (c.c_uint*44)()
        self.slot[3], self.slot[24] = 1, 2
        for name in ('async_calls', 'sync_calls', 'create_calls', 'receive_calls', 'invalid_calls'):
            c.c_uint.in_dll(self.api, name).value = 0
        c.c_int.in_dll(self.api, 'receive_result').value = -1
        for name, size in (('texture', 544), ('palette', 64)):
            array = (c.c_ubyte*size).in_dll(self.api, name)
            array[:] = bytes([0xA5])*size

    def test_checked_native_imported_and_missing_ids(self):
        field = (c.c_ubyte*6)(*bytes.fromhex('aaaa0000bbbb'))
        for item, expected in ((0x24BF, 0xBF), (0x2400, 0), (0x24FF, 255), (0x34BF, 0x10BF),
                               (0x3224, 0), (0x34C0, 0), (0, 0), (0xFFFF, 0)):
            field[2:4] = item.to_bytes(2, 'big')
            self.assertEqual(self.api.af_v3_clothing_checked_index(c.byref(field, 2)), expected)
            self.assertEqual(bytes(field[:2]+field[4:]), bytes.fromhex('aaaabbbb'))
            self.assertEqual(bytes(field[2:4]), (item if expected else 0x2400).to_bytes(2, 'big'))
        self.row[10] = 0
        field[2:4] = bytes.fromhex('34bf')
        self.assertEqual(self.api.af_v3_clothing_checked_index(c.byref(field, 2)), 0)
        self.assertEqual(bytes(field[2:4]), bytes.fromhex('2400'))
        self.assertEqual(self.api.af_v3_clothing_checked_index(None), 0)

    def test_async_single_submission_receive_and_exact_bounds(self):
        for _, name in ENTRIES[:2]:
            function = getattr(self.api, name)
            self.assertEqual(function(self.slot, 0x10BF), 0)
            self.assertEqual(function(self.slot, 0x10BF), 0)
        self.assertEqual(c.c_uint.in_dll(self.api, 'async_calls').value, 2)
        self.assertEqual(c.c_uint.in_dll(self.api, 'create_calls').value, 2)
        self.assertEqual(c.c_uint.in_dll(self.api, 'receive_calls').value, 2)
        c.c_int.in_dll(self.api, 'receive_result').value = 0
        for _, name in ENTRIES[:2]: self.assertEqual(getattr(self.api, name)(self.slot, 0x10BF), 1)
        self.assertEqual(list((c.c_uint*4).in_dll(self.api, 'sources'))[:2], [0x3F0F000, 0x3F0F200])
        self.assertEqual(list((c.c_uint*4).in_dll(self.api, 'sizes'))[:2], [512, 32])
        for name, size, vrom in (('texture', 512, 0x3F0F000), ('palette', 32, 0x3F0F200)):
            data = bytes((c.c_ubyte*(size+32)).in_dll(self.api, name))
            self.assertEqual(data, b'\xA5'*16+bytes([(vrom >> 5)&255])*size+b'\xA5'*16)
        self.assertEqual(c.c_uint.in_dll(self.api, 'invalid_calls').value, 0)

    def test_sync_native_and_invalid_no_submission(self):
        for _, name in ENTRIES[2:]: getattr(self.api, name)(self.slot, 0xBF)
        self.assertEqual(c.c_uint.in_dll(self.api, 'sync_calls').value, 2)
        original = bytes((c.c_ubyte*544).in_dll(self.api, 'texture'))
        self.row[10] = 0
        for _, name in ENTRIES:
            function = getattr(self.api, name)
            function(self.slot, 0x10BF)
            function(self.slot, -1)
            function(None, 0xBF)
        self.slot[3] = self.slot[24] = 0
        for _, name in ENTRIES: getattr(self.api, name)(self.slot, 0xBF)
        self.assertEqual(c.c_uint.in_dll(self.api, 'async_calls').value, 0)
        self.assertEqual(c.c_uint.in_dll(self.api, 'sync_calls').value, 2)
        self.assertEqual(bytes((c.c_ubyte*544).in_dll(self.api, 'texture')), original)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current NPC clothing build required')
class NpcClothingCartridge(unittest.TestCase):
    def test_exact_hooks_relocation_guards_and_retained_resources(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        parent = json.loads((ROOT/'build/v3-clothing-resources-01/build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        files, original = by_vrom(rom), by_vrom(native)
        self.assertEqual(sha256(rom), report['output_sha256'])
        blob = files[BLOB].extract(rom)
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI))
        restored = {}
        for row in report['clothing']['owners']:
            vrom, ram = int(row['vrom'], 16), int(row['link_address'], 16)
            data = bytearray(files[vrom].extract(rom))
            self.assertEqual(sha256(data), row['patched_sha256'])
            for hook in row['hooks']:
                at, before, after = int(hook['address'], 16)-ram, bytes.fromhex(hook['before']), bytes.fromhex(hook['after'])
                self.assertEqual(data[at:at+len(after)], after)
                data[at:at+len(before)] = before
            self.assertEqual(sha256(data), parent['changed_resources'][row['vrom']])
            restored[vrom] = bytes(data)
        for vrom, reloc, *_ in OWNERS:
            self.assertEqual(files[reloc].extract(rom), original[reloc].extract(native))
        symbols = report['asset']['symbols']
        patched, _ = patch_owners(native, restored, symbols)
        for vrom, data in patched.items(): self.assertEqual(data, files[vrom].extract(rom))
        broken = dict(restored)
        altered = bytearray(broken[OWNERS[0][0]])
        altered[0x100] ^= 1
        broken[OWNERS[0][0]] = bytes(altered)
        with self.assertRaises(ValueError): patch_owners(native, broken, symbols)
        with self.assertRaises(ValueError):
            guard_incoming(struct.pack('>4I', 0x10000001, 0, 0, 0), 16, 0x80000000, [(4, 8)])
        excluded = {MODULE} | {row[0] for row in OWNERS}
        for vrom, digest in parent['changed_resources'].items():
            if int(vrom, 16) in excluded: continue
            actual = int(report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(files[actual].extract(rom)), digest, vrom)
        self.assertEqual(report['save_runtime']['profile_hex'], parent['save_runtime']['profile_hex'])
        self.assertEqual(report['clothing']['imports'], parent['clothing']['imports'])
        self.assertFalse(report['clothing']['punchy_defaults_enabled'])
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)


if __name__ == '__main__': unittest.main()
