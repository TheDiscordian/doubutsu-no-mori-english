"""Construction batch: complete donor assets and explicitly bounded mirror state."""
from dataclasses import replace
import struct
import unittest

import test_v3_furniture_art as static_tests
from v3_furniture_art import (CONSTRUCTION_PILOTS, PILOTS, SEGMENT, command_source,
                             native_profile, parse_model, scalar_profile)


def mirror_fixture():
    raw, pointers = static_tests.fixture()
    raw = bytearray(raw)
    struct.pack_into('>I', raw, 0x20, 0xFD441C0F)  # 16x32 CI4.
    struct.pack_into('>I', raw, 0x28, 0xD2F0F800)  # Mirrored S, clamped T.
    raw[0x30:0x30] = struct.pack('>II', 0xF2000000, 0x0007C07C)
    pointers[0x14C] = pointers.pop(0x144)
    return raw, pointers


class ConstructionArtTests(unittest.TestCase):
    def test_explicit_mirror_mode_and_extent_without_relaxing_other_materials(self):
        raw, pointers = mirror_fixture()

        def parse(data, **kwargs):
            return parse_model(data, 0x100, pointers, 0x500, {0x600: (16, 32)},
                               0x1000, 48, **kwargs)

        with self.assertRaisesRegex(ValueError, 'wrap mode'):
            parse(raw)
        rows = parse(raw, mirrored_s=True)
        self.assertEqual(next(r['wrap_modes'] for r in rows if r['opcode'] == 0xFD), (2, 0))
        source, _ = command_source({'opaque': {'rows': rows}},
                                   {0x500: 0, 0x600: 0x20, 0x1000: 0x120})
        self.assertIn('16, 32, 15, G_TX_MIRROR | G_TX_WRAP, G_TX_CLAMP, 4, 5, 0, 0', source)
        self.assertIn('0xF2000000, 0x0007C07C', source)
        for offset, word in ((0x28, 0xD2F0F900), (0x28, 0xD2F0F000),
                             (0x34, 0x000FC07C), (0x30, 0xF2000001)):
            changed = bytearray(raw)
            struct.pack_into('>I', changed, offset, word)
            with self.subTest(offset=offset, word=word), self.assertRaises(ValueError):
                parse(changed, mirrored_s=True)
        for option in ('speed_bag', 'accessory'):
            with self.assertRaises(ValueError):
                parse(raw, mirrored_s=True, **{option: True})

    def test_opaque_only_profiles_preserve_scalars_and_reject_missing_or_extra_layers(self):
        self.assertEqual(len(PILOTS), 2)
        self.assertEqual(tuple(p.item for p in CONSTRUCTION_PILOTS),
                         (0x31F4, 0x31F8, 0x31FC, 0x320C, 0x3214, 0x3218, 0x322C))
        for pilot in CONSTRUCTION_PILOTS:
            profile = native_profile(pilot, 0x1000, {'opaque': 0xC00}, 0x2300000)
            self.assertEqual(len(profile), 68)
            self.assertEqual(struct.unpack_from('>8I', profile, 16),
                             (SEGMENT + 0xC00, 0, 0, 0, 0, 0, 0, 0))
            self.assertEqual(profile[48:], scalar_profile(pilot) + bytes(4))
            self.assertEqual(profile[59], int(pilot.item == 0x31F8))
            for layers in ({}, {'translucent': 0xC00},
                           {'opaque': 0xC00, 'translucent': 0xE00}):
                with self.assertRaises(ValueError):
                    native_profile(pilot, 0x1000, layers, 0x2300000)
            with self.assertRaises(ValueError):
                native_profile(replace(pilot, lighting_map=7), 0x1000,
                               {'opaque': 0xC00}, 0x2300000)


class ConstructionArtLocalTests(static_tests.FurnitureArtLocalTests):
    output = static_tests.ROOT / 'build/v3-construction-art-02'
    pilots = CONSTRUCTION_PILOTS
    expected_sizes = (2944, 2944, 2944, 2944, 1888, 2672, 3856)
    expected_hashes = (
        '55c284543312f844d820236027758581dfdabae9e442616421f54eae21502302',
        '343624b73303f2dd233c882d9e4998a290a456ff404f79a5913a0d296db74067',
        '3ace8867f47858ab35b3681928052b2f469003d88fa7b3aeb444d12691acc79e',
        'a3b9d4cd2a8e17a49540097cd654ac48cdfdf637eb4e428af6e15745b353f982',
        '0d2ccfa8a6e139d90e7e168efa06b22eadfd8e9690e9ffdf9417a4741b090bb7',
        'b7ad346de5839811f5c68ef61e25d884f50e574632f892af01f0e218d2d9f99d',
        '6e7172d2bdacabfac7a06b6a4507466f04d5422ad9c6d3fd5daa7ae3feb02e32',
    )

    def test_compiled_mirror_masks_extents_and_profiles_fit_native_banks(self):
        mirrored_materials = 0
        for pilot, prepared, report, faces in zip(self.pilots, self.prepared,
                self.report['objects'], (40, 40, 40, 40, 26, 40, 51), strict=True):
            body, resources, offsets, models = prepared
            self.assertEqual(set(models), {'opaque'})
            self.assertEqual(report['models'][0]['triangles'], faces)
            self.assertLessEqual(report['object_bytes'], 0x1400)
            self.assertEqual(resources[-1]['bytes'], pilot.vertex_count * 16)
            asset = (self.output / report['object_file']).read_bytes()
            model = report['models'][0]
            code = asset[model['native_offset']:model['native_offset'] + model['bytes']]
            # Decode real native render-tile fields independently of the
            # converter's macro text. Ignore palette/load-tile descriptor 7.
            tiles = []
            for a, b in struct.iter_unpack('>II', code):
                if a >> 24 == 0xF5 and b >> 24 & 7 == 0:
                    self.assertEqual(b >> 20 & 15, 15)
                    tiles.append((b >> 8 & 3, b >> 18 & 3, b >> 4 & 15,
                                  b >> 14 & 15, b & 15, b >> 10 & 15))
            expected = []
            for row in models['opaque']['rows']:
                if row['opcode'] != 0xFD:
                    continue
                mirrored = row.get('wrap_modes') == (2, 0)
                mirrored_materials += mirrored
                w, h = row['shape']
                expected.append((1 if mirrored else 2, 2,
                                 w.bit_length() - 1, h.bit_length() - 1, 0, 0))
            self.assertEqual(tiles, expected)
            profile = native_profile(pilot, len(asset), report['model_offsets'], 0x2300000)
            self.assertEqual(struct.unpack_from('>I', profile, 16)[0], SEGMENT + model['native_offset'])
            self.assertEqual(profile[20:48], bytes(28))
            self.assertEqual(profile[48:], scalar_profile(pilot) + bytes(4))
        self.assertEqual(mirrored_materials, 2)


if __name__ == '__main__':
    unittest.main()
