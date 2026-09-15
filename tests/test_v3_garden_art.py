"""Six complete donor decorations, including tall textures and tile changes."""
from dataclasses import replace
import struct
import unittest

from tests import test_v3_furniture_art as static_tests
from v3_furniture_art import (GARDEN_PILOTS, command_source, native_profile,
                             parse_model, scalar_profile)


class GardenParserTests(unittest.TestCase):
    def test_non_power_of_two_clamp_and_explicit_material_update(self):
        raw, pointers = static_tests.fixture()
        raw = bytearray(raw)
        struct.pack_into('>I', raw, 0x20, 0xFD44241F)  # 32x40 CI4.
        raw[0x48:0x48] = struct.pack('>4I', 0xD280F800, 0, 0xF2000000, 0xFC09C)
        args = (0x100, pointers, 0x500, {0x600: (32, 40)}, 0x1000, 48)
        with self.assertRaisesRegex(ValueError, 'standalone'):
            parse_model(raw, *args)
        rows = parse_model(raw, *args, garden=True)
        source, _ = command_source({'opaque': {'rows': rows}},
                                   {0x500: 0, 0x600: 32, 0x1000: 672})
        self.assertIn('32, 40, 15, G_TX_CLAMP, G_TX_CLAMP, 5, 0, 0, 0', source)
        self.assertIn('G_TX_CLAMP, 0, 0, G_TX_MIRROR | G_TX_WRAP, 5, 0', source)
        self.assertIn('gsDPSetTileSize(G_TX_RENDERTILE, 0, 0, 124, 156)', source)
        self.assertNotIn('0xD280', source)
        for at, word in ((0x48, 0xD290F800), (0x48, 0xD280F900),
                         (0x4C, 1), (0x54, 0xFC07C)):
            changed = bytearray(raw)
            struct.pack_into('>I', changed, at, word)
            with self.subTest(at=at, word=word), self.assertRaises(ValueError):
                parse_model(changed, *args, garden=True)
        for mode in ('speed_bag', 'accessory', 'mirrored_s'):
            with self.assertRaises(ValueError):
                parse_model(raw, *args, garden=True, **{mode: True})
        # Never approximate repeat/mirror on a non-power-of-two axis.
        rows[4]['wrap_modes'] = (0, 1)
        with self.assertRaisesRegex(ValueError, 'power-of-two'):
            command_source({'opaque': {'rows': rows}}, {0x500: 0, 0x600: 32})


class GardenArtLocalTests(static_tests.FurnitureArtLocalTests):
    output = static_tests.ROOT / 'build/v3-garden-art-01'
    pilots = GARDEN_PILOTS
    expected_sizes = (4048, 3840, 3680, 3456, 3728, 3680)
    expected_hashes = (
        '39638d65b0e4879e86dfed67bbe9db39a378b1db1b375bd4b91ab3acabee78f1',
        'cab7148b304081f02d313817fa6ffd9c92932bcd9a0460e86c735045eaafc67d',
        '800504a52e055a6a921f184f1615b03d69704caa9475d1c0776d52a3c29ec828',
        'a8c552e2edd1a7cd7b2633a1eab096852d50f783c70c6156711d269049f08398',
        '5bc33d163176bdf5f8c7aa878413d8685ea6ae57918c46185be18a6981e192d2',
        'ef64366aa6428a6adbfc75b2ee2b56a552cd5537c02558d1d2249bc789e1cee2',
    )

    def test_exact_profile_and_compiled_native_tile_fields(self):
        non_power_axes = updates = 0
        for pilot, prepared, report in zip(self.pilots, self.prepared, self.report['objects'], strict=True):
            asset = (self.output / report['object_file']).read_bytes()
            profile = native_profile(pilot, len(asset), report['model_offsets'], 0x2340000)
            self.assertLessEqual(len(asset), 0x1000)
            self.assertEqual(profile[48:], bytes.fromhex('4229b8523c23d70a040000010000000000000000'))
            self.assertEqual(profile[48:64], scalar_profile(pilot))
            self.assertEqual(profile[20:48], bytes(28))
            with self.assertRaises(ValueError):
                native_profile(replace(pilot, height=18), len(asset), report['model_offsets'], 0x2340000)
            model = report['models'][0]
            code = asset[model['native_offset']:model['native_offset'] + model['bytes']]
            actual = [(a >> 9 & 511, b >> 20 & 15, b >> 8 & 3, b >> 18 & 3,
                       b >> 4 & 15, b >> 14 & 15, b & 15, b >> 10 & 15)
                      for a, b in struct.iter_unpack('>II', code) if a >> 24 == 0xF5 and b >> 24 & 7 == 0]
            expected = []
            for row in prepared[3]['opaque']['rows']:
                if row['opcode'] not in (0xFD, 0xD2):
                    continue
                w, h = row['shape']
                masks = tuple(v.bit_length() - 1 if v & (v - 1) == 0 else 0 for v in (w, h))
                non_power_axes += sum(v & (v - 1) != 0 for v in (w, h))
                updates += row['opcode'] == 0xD2
                modes = {0: 2, 1: 0, 2: 1}
                ws, wt = row['wrap_modes']
                expected.append((w // 16, 15, modes[ws], modes[wt], *masks, 0, 0))
            self.assertEqual(actual, expected)
        self.assertEqual(non_power_axes, 8)
        self.assertEqual(updates, 1)


if __name__ == '__main__':
    unittest.main()
