"""Subset-aware selection keeps native IDs, population rules, and saved bounds."""
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
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, MODULE, CONFIG, compose
import v3_villager_selection as selection

OUTPUT = ROOT / 'build/v3-villager-selection-01'


class SelectionLogicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = r'''
#include <string.h>
unsigned char af_v3_select_flags[20], af_v3_select_metadata[640], af_v3_select_candidates[32];
unsigned char af_v3_select_animals[0x528*15], af_v3_select_appeared[32];
signed char af_v3_select_growth[224];
int af_v3_select_shuffle[238], af_v3_select_ready = 1;
int draw_size, draw_swaps, resets, sets;
float fraction;
unsigned int af_v3_select_looks(unsigned int npc) { return (npc-0xe000)%6; }
int af_v3_select_seen(int index) { return (af_v3_select_appeared[index/8]>>(index&7))&1; }
void af_v3_select_mark(unsigned int npc) {
    unsigned int index = npc-0xe000; af_v3_select_appeared[index/8] |= 1u << (index&7);
}
int af_v3_select_search(unsigned char *p, unsigned int npc, int n) {
    for (int i = 0; i < n; ++i)
        if ((unsigned int)(p[i*0x528]*256+p[i*0x528+1]) == npc) return i;
    return -1;
}
void af_v3_select_reset(unsigned char *p, unsigned char *animals) {
    ++resets; memset(p, 0, 32);
    for (int i = 0; i < 15; ++i) {
        unsigned int id = animals[i*0x528]*256+animals[i*0x528+1];
        if (id) af_v3_select_mark(id);
    }
}
void af_v3_select_rand(int *p, int count, int swaps) {
    draw_size = count; draw_swaps = swaps;
    for (int i = 0; i < count; ++i) p[i] = count-1-i;
}
float af_v3_select_random(void) { return fraction; }
void af_v3_select_set(unsigned char *p, int index) {
    ++sets; p[0] = 0xe0; p[1] = index; p[11] = index%6;
}
'''
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-selection-')
        library = Path(cls.temp.name) / 'selection.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-Wall', '-Wextra', '-Werror',
                        str(ROOT / 'overlays/v3/villager_selection.c'), '-x', 'c', '-', '-o', str(library)],
                       input=fixture, text=True, check=True, capture_output=True)
        cls.api = c.CDLL(str(library))
        cls.api.af_v3_unseen_personality.argtypes = [c.c_uint]
        cls.api.af_v3_grow_personality.argtypes = [c.c_uint]
        cls.api.af_v3_initial_population.argtypes = [c.c_void_p, c.c_uint, c.c_int]

    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        for symbol, size in (('flags', 20), ('metadata', 640), ('candidates', 32),
                              ('animals', 0x528*15), ('appeared', 32), ('growth', 224)):
            array = (c.c_ubyte*size).in_dll(self.api, 'af_v3_select_'+symbol)
            c.memset(c.addressof(array), 0, size)
            setattr(self, symbol, array)
        for symbol in ('draw_size', 'draw_swaps', 'resets', 'sets'):
            c.c_int.in_dll(self.api, symbol).value = 0
        c.c_int.in_dll(self.api, 'af_v3_select_ready').value = 1
        c.c_float.in_dll(self.api, 'fraction').value = 0
        at = 16*32
        for i, value in enumerate(bytes.fromhex('e0ea2498')+bytes((0, 0, 0, 1))):
            self.metadata[at+i] = value
        self.metadata[at+30:at+32] = bytes.fromhex('2498')

    def test_unseen_counts_disabled_and_complete_dependency_guards(self):
        self.assertEqual(self.api.af_v3_unseen_personality(0), 36)
        self.flags[16] = 1
        self.assertEqual(self.api.af_v3_unseen_personality(0), 37)
        for offset, value in ((7, 0), (30, 0), (6, 1), (1, 0), (4, 6)):
            at = 16*32+offset; previous = self.metadata[at]; self.metadata[at] = value
            self.assertEqual(self.api.af_v3_unseen_personality(0), 36)
            self.metadata[at] = previous
        self.assertEqual(self.api.af_v3_unseen_personality(6), 0)
        self.flags[19] = 1  # No implemented starting outfit or exact metadata.
        self.assertEqual(self.api.af_v3_unseen_personality(3), 36)

    def test_new_candidate_resident_exclusion_and_saved_history(self):
        c.memset(c.addressof(self.appeared), 255, 32)
        self.appeared[234//8] &= ~(1 << (234&7))
        self.assertEqual(self.api.af_v3_grow_personality(0), -1)
        self.flags[16] = 1
        self.assertEqual(self.api.af_v3_grow_personality(0), 234)
        self.assertEqual(bytes(self.candidates), bytes(29)+b'\x04\0\0')
        self.animals[0:2] = bytes.fromhex('e0ea')
        self.assertEqual(self.api.af_v3_grow_personality(0), -1)
        self.assertEqual(self.api.af_v3_grow_personality(6), -1)
        self.animals[0:2] = bytes(2)
        c.c_float.in_dll(self.api, 'fraction').value = 1
        self.assertEqual(self.api.af_v3_grow_personality(0), -1)

    def test_history_reset_considers_only_eligible_imports(self):
        c.memset(c.addressof(self.appeared), 255, 27)
        self.flags[16] = 1
        self.api.af_v3_reset_appeared()
        self.assertEqual(c.c_int.in_dll(self.api, 'resets').value, 0)
        self.appeared[29] |= 4
        self.animals[0:2] = bytes.fromhex('e0ea')
        self.api.af_v3_reset_appeared()
        self.assertEqual(c.c_int.in_dll(self.api, 'resets').value, 1)
        self.assertEqual(bytes(self.appeared), bytes(29)+b'\x04\0\0')

    def test_initial_population_native_draw_and_stable_import_mapping(self):
        self.api.af_v3_initial_population(self.animals, 6, 0)
        self.assertEqual(c.c_int.in_dll(self.api, 'draw_size').value, 216)
        self.assertEqual(c.c_int.in_dll(self.api, 'draw_swaps').value, 216)
        self.assertEqual([self.animals[i*0x528+1] for i in range(6)], list(range(215, 209, -1)))
        c.memset(c.addressof(self.animals), 0, len(self.animals))
        self.flags[16] = 1
        self.api.af_v3_initial_population(self.animals, 6, 1)
        self.assertEqual(c.c_int.in_dll(self.api, 'draw_size').value, 217)
        selected = [self.animals[i*0x528+1] for i in range(6)]
        self.assertEqual(selected, [234, 215, 214, 213, 212, 211])
        self.assertNotIn(216, selected)
        self.assertEqual({self.animals[i*0x528+11] for i in range(6)}, set(range(6)))
        self.assertEqual(bytes(self.animals[6*0x528:]), bytes(9*0x528))


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current selection cartridge required')
class SelectionCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.files = by_vrom(cls.rom)
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.parent = json.loads((ROOT / 'build/v3-villager-readers-01/build.json').read_text())

    def test_native_function_guards_and_owned_memory(self):
        code = bytearray(self.files[CODE_VROM].extract(self.rom))
        native = by_vrom(self.native)[CODE_VROM].extract(self.native)
        for row in self.report['villager_selection']['hooks']:
            at, end = int(row['entry'], 16)-CODE_RAM, int(row['end'], 16)-CODE_RAM
            self.assertEqual(code[at:at+8].hex(), row['after'])
            code[at:at+8] = bytes.fromhex(row['before'])
            self.assertEqual(code[at:end], native[at:end])
        self.assertEqual(sha256(code), self.parent['changed_resources'][f'{CODE_VROM:08X}'])
        blob = bytearray(self.files[BLOB].extract(self.rom)[:0xC000])
        helper = (OUTPUT / 'villager_selection/code.bin').read_bytes()
        self.assertEqual(blob[selection.CODE:selection.CODE+len(helper)], helper)
        self.assertLessEqual(selection.CODE+len(helper), selection.LIMIT)
        self.assertEqual(blob[selection.FLAGS:selection.FLAGS+20], bytes(20))
        self.assertEqual(blob[selection.CANDIDATES:selection.CANDIDATES+32], bytes(32))
        self.assertEqual(blob[selection.SHUFFLE:selection.SHUFFLE+238*4], bytes(238*4))
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob), selection.ABI))
        blob[selection.GROWTH:selection.FLAGS] = bytes(224)
        blob[selection.CODE:selection.CODE+len(helper)] = bytes(len(helper))
        struct.pack_into('>I', blob, 4, 24)
        self.assertEqual(sha256(blob), self.parent['blob_sha256'])

    def test_patch_import_free_and_retained_resources(self):
        base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        self.assertEqual(compose(self.native, base, {}, {}), base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)
        for v, digest in self.parent['changed_resources'].items():
            if int(v, 16) in (CODE_VROM, MODULE): continue
            actual = int(self.report['relocated_resources'].get(v, v), 16)
            self.assertEqual(sha256(self.files[actual].extract(self.rom)), digest)
        self.assertFalse(self.report['new_villager_ids_enabled'])


if __name__ == '__main__': unittest.main()
