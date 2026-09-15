"""Complete camping assets, native graphics states, and source gameplay data."""
from copy import deepcopy
import json
import struct
import unittest

from tests import test_v3_furniture_art as static
from aflib import sha256
from v3_furniture_art import CAMPING_PILOTS, native_profile, parse_model
from v3_camping_items import (BASE, BASE_SHA, REPORT_SHA, TENT, identity_evidence,
                             metadata, score_mapping)
from v3_registry import furniture_slot


class CampingArtTests(static.FurnitureArtLocalTests):
    output = static.ROOT / 'build/v3-camping-art-01'
    pilots = CAMPING_PILOTS
    expected_sizes = (3248, 4384, 2064, 2656, 5632, 2032, 4208)
    expected_hashes = (
        '07d827fbe217faa7eb6a00cd9190ba0537ca301e4eb2831ffd14fcff0c26b360',
        '3c05892a30a6efae29ecb55ac21d604e39f8869a7af22050a2b5dd03aa120643',
        '655c1b8774db92c253d2df16d82014e7793a3ce52ada6f74127a334d998da8fe',
        '03a219644bd47ab6abfd6fbd570eefd1a854d77776c55f2a909382070567fe44',
        '236bc563ad4b2475a4474fe9b265f82a88383b37158d2b935a8379c5e48e5549',
        '2e7fbf0b0135159aefada59f875170151231d7537e2547f82568770e1e6752ab',
        '061382dab493ae69d2a8e70539fedaf28d266793b2158fa8521c75b20da9554d',
    )

    def commands(self, item, layer='opaque'):
        row = self.report['objects'][item]
        model = next(m for m in row['models'] if m['layer'] == layer)
        asset = (self.output / row['object_file']).read_bytes()
        return list(struct.iter_unpack('>II', asset[model['native_offset']:model['native_offset'] + model['bytes']]))

    def test_complete_totals_and_fixed_two_cell_profile_bindings(self):
        self.assertEqual(sum(p.vertex_count for p in self.pilots), 524)
        self.assertEqual(sum(m['triangles'] for row in self.report['objects'] for m in row['models']), 362)
        self.assertEqual(sum(row['object_bytes'] for row in self.report['objects']), 24224)
        ranges = []
        for pilot, row in zip(self.pilots, self.report['objects'], strict=True):
            index, item, vrom = furniture_slot(pilot.item)
            self.assertEqual((index, item), (1024 + (pilot.item - 0x3000) // 4, pilot.item))
            self.assertLessEqual(row['object_bytes'], 0x2000)
            ranges.append((vrom, vrom + 0x2000))
            profile = native_profile(pilot, row['object_bytes'], row['model_offsets'], vrom)
            self.assertEqual(profile[48:64].hex(), row['native_profile_scalar_hex'])
            self.assertEqual(profile[32:48], bytes(16))
            self.assertEqual(profile[64:], bytes(4))
            expected = (3, 1) if pilot.item in (0x3364, 0x33A8, 0x33AC) else (4, 0)
            self.assertEqual(tuple(profile[56:58]), expected)
            self.assertEqual(struct.unpack_from('>4I', profile, 16), tuple(
                0x6000000 + row['model_offsets'][name] if name in row['model_offsets'] else 0
                for name in ('opaque', 'opaque1', 'translucent', 'translucent1')))
        self.assertGreaterEqual(ranges[0][0], 0x242D010)
        self.assertLess(ranges[-1][1], 0x25F0000)
        self.assertTrue(all(a[1] <= b[0] for a, b in zip(ranges, ranges[1:])))
        self.assertEqual(set(self.report['objects'][0]['model_offsets']), {'opaque', 'opaque1'})

    def test_native_mirroring_reset_primitive_tint_and_unlit_lantern(self):
        # Native fields encode clamp=2 and mirror+wrap=1; the GX enum differs.
        def tiles(commands):
            return [(b >> 8 & 3, b >> 18 & 3) for a, b in commands if a >> 24 == 0xF5 and b >> 24 & 7 == 0]
        self.assertIn((1, 1), tiles(self.commands(0, 'opaque1')))
        self.assertIn((1, 1), tiles(self.commands(3)))
        self.assertIn((2, 1), tiles(self.commands(4)))  # Bike saddle mirrors only T.
        backpack = self.commands(1)
        self.assertIn((0xFA000080, 0xFFFDFFFF), backpack)
        self.assertEqual(tiles(backpack)[-1], (2, 2))  # Reset after mirrored base.
        self.assertEqual([b for a, b in backpack if a == 0xF2000000][-1], 0x0003C07C)
        lantern = self.commands(2)
        self.assertEqual([(a, b) for a, b in lantern if a >> 24 == 0xD9],
                         [(0xD9000000, 0x210405), (0xD9000000, 0x210005)])
        self.assertTrue(all(not b & 0x20000 for a, b in lantern if a >> 24 == 0xD9))

    def test_camping_modes_are_explicit_and_unknown_states_still_fail(self):
        raw, pointers = static.fixture()
        changed = bytearray(raw)
        struct.pack_into('>I', changed, 0x28, 0xD2F0FA00)
        with self.assertRaisesRegex(ValueError, 'wrap mode'):
            static.parse(changed, pointers)
        rows = parse_model(changed, 0x100, pointers, 0x500, {0x600: (32, 32)}, 0x1000, 48, camping=True)
        self.assertEqual(next(r['wrap_modes'] for r in rows if r['opcode'] == 0xFD), (2, 2))
        for at, word in ((0x28, 0xD2F0F300), (0x34, 0xFFFFFFFF - 1), (0x3C, 0x270405)):
            bad = bytearray(changed); struct.pack_into('>I', bad, at, word)
            with self.assertRaises(ValueError):
                parse_model(bad, 0x100, pointers, 0x500, {0x600: (32, 32)}, 0x1000, 48, camping=True)
        with self.assertRaises(ValueError):
            parse_model(raw, 0x100, pointers, 0x500, {0x600: (32, 32)}, 0x1000, 48,
                        camping=True, western=True)


class CampingMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (static.ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (static.ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_complete_metadata_keeps_true_reward_route_and_not_for_sale(self):
        records, rows = metadata(self.rel, self.symbols)
        self.assertEqual(sha256(records), 'e9d79e365b85e8f7b77cb8f4831366fb56ba529b8f0d34eac347fddf09b78d7e')
        self.assertEqual([struct.unpack_from('>HHHBB', records, i * 32) for i in range(7)], [
            (1241, 0x3364, 3460, 1, 1), (1244, 0x3370, 1980, 0, 1), (1255, 0x339C, 1180, 0, 1),
            (1257, 0x33A4, 1300, 0, 1), (1258, 0x33A8, 3380, 1, 1), (1259, 0x33AC, 1960, 1, 1),
            (1260, 0x33B0, 1470, 0, 1)])
        self.assertEqual(len(TENT), 11)
        self.assertEqual({row['donor_list'] for row in rows}, {'ftr_listTent'})
        self.assertTrue(all(not row['ordinary_stock'] and not row['catalogue_orderable']
                            and not row['acquisition_installed'] and not row['runtime_installed'] for row in rows))
        self.assertEqual([r['native_hra_hex'] for r in rows], ['d4050600', 'd4050600', 'd4050700',
                         'd4050600', 'd4050600', 'd4050600', 'd4050600'])
        self.assertEqual([r['preview_mode'] for r in rows], [0, 0, 0, 0, 24, 0, 0])
        self.assertEqual(rows[4]['donor_preview_scalar_hex'], '3f59999ac0400000')
        evidence = identity_evidence(static.ROOT / 'build/item-identity-megasheet.xlsx')
        self.assertEqual([r['item_id'] for r in evidence], [f'{p.item:04X}' for p in CAMPING_PILOTS])

    def test_scoring_only_mapping_binds_actual_native_counter_and_preserves_all_other_bits(self):
        image, raw = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes(), (BASE / 'build.json').read_bytes()
        self.assertEqual(sha256(image), BASE_SHA)
        self.assertEqual(sha256(raw), REPORT_SHA)
        report = json.loads(raw)
        mapped = score_mapping(self.rel, self.symbols, image, report)
        self.assertEqual((mapped['donor_category'], mapped['native_scoring_category'], mapped['points']), (37, 3, 412))
        self.assertFalse(mapped['acquisition_category_changed'])
        self.assertEqual(mapped['native_consumers'], [0x809275E0, 0x8092763C, 0x80927680])
        self.assertEqual(mapped['extra_stack_or_counter_memory'], 0)
        for row in metadata(self.rel, self.symbols)[1]:
            donor, native = int(row['donor_hra_hex'], 16), int(row['native_hra_hex'], 16)
            self.assertEqual(donor & 0xFFFFC000, native & 0xFFFFC000)
            self.assertEqual(donor >> 6 & 3, native >> 7 & 3)
            self.assertEqual(native & 127, 0)
        bad = deepcopy(report); bad['hra']['birth_extension']['count'] = 38
        with self.assertRaisesRegex(ValueError, 'equivalence'):
            score_mapping(self.rel, self.symbols, image, bad)
        with self.assertRaisesRegex(ValueError, 'checked'):
            score_mapping(self.rel, self.symbols, image[:-1], report)


if __name__ == '__main__':
    unittest.main()
