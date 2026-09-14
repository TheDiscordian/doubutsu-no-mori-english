"""House gifts retain native selection rules and full imported item identities."""
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, MODULE, CONFIG, compose
import v3_villager_rewards as rewards

OUTPUT = ROOT/'build/v3-villager-rewards-01'


class RewardLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = r'''
int enabled = 1, draws;
float fraction;
int af_v3_reward_native(unsigned int item) {
    return !(item >= 0x15b0 && item < 0x1d44) && !(item >= 0x1e3c && item < 0x1ea0);
}
int af_v3_reward_imported(unsigned int index) { return enabled && (index == 1161 || index == 1198); }
float af_v3_reward_random(void) { ++draws; return fraction; }
'''
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-rewards-')
        library = Path(cls.temp.name)/'rewards.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        str(ROOT/'overlays/v3/villager_rewards.c'), '-x', 'c', '-', '-o', str(library)],
                       input=fixture, text=True, capture_output=True, check=True)
        cls.api = c.CDLL(str(library))
        cls.api.af_v3_house_reward.argtypes = [c.c_void_p, c.c_void_p, c.c_int]
        cls.api.af_v3_house_reward.restype = c.c_uint

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.layer = (c.c_ubyte*518)()
        self.npc = (c.c_ubyte*56)()
        self.npc[0x30:0x32] = struct.pack('>H', 888)
        self.pointers = (c.c_void_p*498)()
        self.pointers[490] = c.addressof(self.layer)
        c.c_int.in_dll(self.api, 'enabled').value = 1
        c.c_int.in_dll(self.api, 'draws').value = 0
        c.c_float.in_dll(self.api, 'fraction').value = 0

    def place(self, row, column, item):
        offset = 2+(row*16+column)*2
        self.layer[offset:offset+2] = struct.pack('>H', item)

    def select(self, fraction=0):
        c.c_float.in_dll(self.api, 'fraction').value = fraction
        return self.api.af_v3_house_reward(self.pointers, self.npc, 398)

    def test_mixed_rotations_native_exclusions_and_room_bounds(self):
        self.place(0, 0, 0x10b8)
        self.place(1, 1, 0x3227)
        self.place(9, 9, 0x32ba)
        for row, column, item in ((0, 1, 0x17b0), (0, 2, 0x1e3c), (2, 2, 0x3352),
                                   (0, 10, 0x3224), (10, 0, 0x32b8), (9, 10, 0x113f)):
            self.place(row, column, item)
        before = bytes(self.layer), bytes(self.npc)
        self.assertEqual([self.select(f) for f in (0, .4, .9)], [0x10b8, 0x3227, 0x32ba])
        c.c_int.in_dll(self.api, 'enabled').value = 0
        self.assertEqual(self.select(.9), 0x10b8)
        self.assertEqual((bytes(self.layer), bytes(self.npc)), before)

    def test_empty_disabled_and_invalid_data_do_not_draw(self):
        self.place(1, 1, 0x3224)
        c.c_int.in_dll(self.api, 'enabled').value = 0
        self.assertEqual(self.select(), 0)
        self.assertEqual(c.c_int.in_dll(self.api, 'draws').value, 0)
        self.pointers[490] = None
        self.assertEqual(self.select(), 0)
        self.npc[0x30:0x32] = bytes.fromhex('ffff')
        self.assertEqual(self.select(), 0)
        self.assertEqual(self.api.af_v3_house_reward(None, self.npc, 398), 0)
        self.assertEqual(self.api.af_v3_house_reward(self.pointers, None, 398), 0)
        self.assertEqual(c.c_int.in_dll(self.api, 'draws').value, 0)

    def test_negative_layer_difference_retains_first_slot_and_invalid_draw_is_rejected(self):
        self.pointers[0] = c.addressof(self.layer)
        self.npc[0x30:0x32] = bytes(2)
        self.place(0, 0, 0x32b8)
        self.assertEqual(self.select(), 0x32b8)
        for value in (1.0, -.1, float('nan')):
            self.assertEqual(self.select(value), 0)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current reward cartridge required')
class RewardCartridgeTests(unittest.TestCase):
    def test_checked_patch_owned_code_and_unchanged_dependencies(self):
        report = json.loads((OUTPUT/'build.json').read_text())
        parent = json.loads((ROOT/'build/v3-villager-selection-01/build.json').read_text())
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        files = by_vrom(rom)
        code = bytearray(files[CODE_VROM].extract(rom))
        row = report['villager_rewards']
        at = rewards.ENTRY-CODE_RAM
        self.assertEqual(code[at:at+8].hex(), row['after'])
        code[at:at+8] = bytes.fromhex(row['before'])
        self.assertEqual(sha256(code[at:rewards.END-CODE_RAM]), rewards.SOURCE_SHA)
        self.assertEqual(sha256(code), parent['changed_resources'][f'{CODE_VROM:08X}'])
        blob = bytearray(files[BLOB].extract(rom)[:0xC000])
        helper = (OUTPUT/'villager_rewards/code.bin').read_bytes()
        self.assertEqual(blob[rewards.CODE:rewards.CODE+len(helper)], helper)
        self.assertLessEqual(rewards.CODE+len(helper), rewards.LIMIT)
        self.assertEqual(struct.unpack_from('>4I', files[MODULE].extract(rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob), rewards.ABI))
        blob[rewards.CODE:rewards.CODE+len(helper)] = bytes(len(helper))
        struct.pack_into('>I', blob, 4, 25)
        self.assertEqual(sha256(blob), parent['blob_sha256'])
        for v, digest in parent['changed_resources'].items():
            if int(v, 16) in (CODE_VROM, MODULE): continue
            actual = int(report['relocated_resources'].get(v, v), 16)
            self.assertEqual(sha256(files[actual].extract(rom)), digest)
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        self.assertEqual(compose(native, base, {}, {}), base)
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)
        self.assertFalse(report['new_villager_ids_enabled'])


if __name__ == '__main__': unittest.main()
