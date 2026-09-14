"""Current donor house installation preserves native resources and stable IDs."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_VROM, apply_ups, by_vrom, sha256
from v3_asset_loader import BLOB, CONFIG, MODULE, compose
from v3_registry import villager_house_layers
import v3_villager_houses as houses

OUTPUT = ROOT / 'build/v3-house-layout-01'


class HouseIdentityTests(unittest.TestCase):
    def test_subset_independent_layer_reservations(self):
        self.assertEqual(villager_house_layers(232), (888, 889))
        self.assertEqual(villager_house_layers(235), (894, 895))
        slots = [slot for donor in range(216, 236) for slot in villager_house_layers(donor)]
        self.assertEqual(slots, list(range(856, 896)))
        with self.assertRaises(ValueError):
            villager_house_layers(215)
        with self.assertRaises(ValueError):
            houses.layers(bytes(519))
        with self.assertRaises(ValueError):
            houses.layers(bytes(2 * houses.STRIDE))


@unittest.skipUnless((OUTPUT / 'build.json').exists(), 'Current house cartridge required')
class HouseCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT / 'build.json').read_text())
        cls.houses = cls.report['villager_houses']
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.native)
        cls.parent = json.loads((ROOT / 'build/v3-room-identity-01/build.json').read_text())

    def test_complete_house_and_layer_preservation(self):
        table = self.files[houses.HOUSE].extract(self.rom)
        original = self.original[houses.HOUSE].extract(self.native)
        self.assertEqual(table[:len(original)], original)
        self.assertEqual(table[234 * 8:235 * 8], bytes.fromhex('00003f2103780379'))
        self.assertEqual(table[len(original):234 * 8], bytes((234 - 218) * 8))
        self.assertEqual(table[235 * 8:], bytes(3 * 8))
        fg = self.files[houses.FOREGROUND].extract(self.rom)
        original_fg = self.original[houses.FOREGROUND].extract(self.native)
        self.assertEqual(fg[:len(original_fg)], original_fg)
        self.assertEqual(fg[-4:], bytes(4))
        source = ROOT / 'build/gamecube/files/forest_2nd.arc.unpacked/data/fgnpcdata.bin'
        raw = source.read_bytes()
        self.assertEqual(sha256(raw), houses.DONOR_FG_SHA)
        donor_layers = houses.layers(raw)
        for i, (source_id, target_id) in enumerate(((514, 888), (515, 889))):
            at = len(original_fg) + i * houses.STRIDE
            self.assertEqual(fg[at:at + houses.STRIDE], struct.pack('>H', target_id) + donor_layers[source_id][2:])
        self.assertEqual(sha256(fg), self.houses['output_fg_sha256'])
        self.assertEqual(len(fg), 224816)
        self.assertLessEqual(houses.FOREGROUND + len(fg), 0x11E2000)
        self.assertFalse(self.report['new_villager_ids_enabled'])

    def test_exact_native_surfaces_and_complete_dependencies(self):
        for house, wall, floor in zip(self.houses['houses'], (63, 39), (33, 20)):
            self.assertEqual([row['index'] for row in house['wall']['native_matches']], [wall])
            self.assertEqual([row['index'] for row in house['floor']['native_matches']], [floor])
            for name in ('wall', 'floor'):
                self.assertEqual(house[name]['converted_sha256'], house[name]['native_matches'][0]['record_sha256'])
        cheri, punchy = self.houses['houses']
        self.assertTrue(cheri['installed'])
        self.assertFalse(punchy['installed'])
        self.assertEqual({row['donor_item'] for row in cheri['dependencies'] if row['imported_item']}, {'3224', '32B8'})
        self.assertTrue(all(row['status'] in ('existing_identity', 'import_dependency') for row in cheri['dependencies']))
        self.assertEqual([row['donor_item'] for row in punchy['dependencies']
                          if row['status'] == 'identity_or_content_work_required'], ['3352'])

    def test_loader_words_crc_retained_prefix_and_resources(self):
        code = bytearray(self.files[CODE_VROM].extract(self.rom))
        for at, before, after in houses.WINDOWS:
            self.assertEqual(struct.unpack_from('>I', code, at - houses.CODE_RAM)[0], after)
            struct.pack_into('>I', code, at - houses.CODE_RAM, before)
        self.assertEqual(sha256(code), self.parent['changed_resources'][f'{CODE_VROM:08X}'])
        blob = self.files[BLOB].extract(self.rom)[:0xC000]
        self.assertEqual(struct.unpack_from('>I', blob, 4)[0], houses.ABI)
        previous_header = bytearray(blob)
        struct.pack_into('>I', previous_header, 4, 22)
        self.assertEqual(sha256(previous_header), self.parent['blob_sha256'])
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob), houses.ABI))
        for vrom, digest in self.parent['changed_resources'].items():
            if int(vrom, 16) in (CODE_VROM, MODULE):
                continue
            actual = int(self.report['relocated_resources'].get(vrom, vrom), 16)
            self.assertEqual(sha256(self.files[actual].extract(self.rom)), digest)
        for vrom in (houses.HOUSE, houses.FOREGROUND):
            self.assertEqual(self.files[vrom].index, self.original[vrom].index)

    def test_current_composition_patch_and_import_free_v2(self):
        moved = {int(v, 16): int(t, 16) for v, t in self.report['relocated_resources'].items()}
        changes = {int(v, 16): self.files[moved.get(int(v, 16), int(v, 16))].extract(self.rom)
                   for v in self.report['changed_resources']}
        added = {int(v, 16): self.files[int(v, 16)].extract(self.rom) for v in self.report['added_resources']}
        resized = tuple(int(v, 16) for v in self.report['resized_resources'])
        self.assertEqual(compose(self.native, self.base, changes, added, resized=resized, relocated=moved), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)
        self.assertEqual(apply_ups(self.native, (OUTPUT / 'asset-loader.ups').read_bytes()), self.rom)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])


if __name__ == '__main__':
    unittest.main()
