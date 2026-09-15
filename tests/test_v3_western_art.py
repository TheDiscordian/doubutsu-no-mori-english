"""Complete Western geometry and explicitly reviewed native material changes."""
import struct
import unittest

from tests import test_v3_furniture_art as static_tests
from v3_furniture_art import WESTERN_PILOTS, command_source, native_profile, parse_model


class WesternParserTests(unittest.TestCase):
    def test_double_mirror_is_explicit_and_keeps_both_axis_extents(self):
        raw, pointers = static_tests.fixture()
        raw = bytearray(raw)
        struct.pack_into('>I', raw, 0x20, 0xFD440C0F)  # 16x16 CI4.
        struct.pack_into('>I', raw, 0x28, 0xD2F0FA00)
        raw[0x48:0x48] = struct.pack('>II', 0xF2000000, 0x7C07C)
        args = (0x100, pointers, 0x500, {0x600: (16, 16)}, 0x1000, 48)
        rows = parse_model(raw, *args, western=True)
        source, _ = command_source({'opaque': {'rows': rows}},
                                   {0x500: 0, 0x600: 32, 0x1000: 160})
        self.assertIn('16, 16, 15, G_TX_MIRROR | G_TX_WRAP, G_TX_MIRROR | G_TX_WRAP, 4, 4', source)
        self.assertIn('0x0007C07C', source)
        self.assertNotIn('0xD2F0', source)
        for mode in ({}, {'garden': True}, {'mirrored_s': True},
                     {'western': True, 'garden': True}):
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                parse_model(raw, *args, **mode)
        for at, value in ((0x28, 0xD2F0F900), (0x2C, 1), (0x4C, 0xFC07C)):
            changed = bytearray(raw)
            struct.pack_into('>I', changed, at, value)
            with self.subTest(at=at), self.assertRaises(ValueError):
                parse_model(changed, *args, western=True)


class WesternArtLocalTests(static_tests.FurnitureArtLocalTests):
    output = static_tests.ROOT / 'build/v3-western-art-01'
    pilots = WESTERN_PILOTS
    expected_sizes = (3296, 3632, 5216, 1920, 2320, 2720, 5088)
    expected_hashes = (
        '26d9cc3626020cce04694799a5ee780e0e9cc1be4ea8af32c750f30b3c6b2e94',
        'd373c14b5a24afe7130013c5a66c3827fc5b18f448ddfd81bd267cd9361b5c12',
        '46edc82db7109e3202ba07d048331e72ac0812cbc18040965d2b9e9db1682ebb',
        'c5a93917a460a6acdba32ab3f24b572dba888a9f445b6ebb3faf80f70fb716aa',
        'f10bba41b5a6409af894f1717f865aebec038ab5ed1af0e2d10861b9d7683430',
        'dc196724077633a328183e570711318939ef95ffdcb2e3c86e8403ab92a798cc',
        'bce7d9549cece143b1fc3fbc5f8f3838eb73e7e57b6b9de0e5435259f627af34',
    )

    def test_second_opaque_slot_and_compiled_mirrors_preserve_source_routing(self):
        mirrors = []
        for pilot, prepared, report in zip(self.pilots, self.prepared, self.report['objects'], strict=True):
            profile = native_profile(pilot, report['object_bytes'], report['model_offsets'], 0x2364000)
            expected = [0] * 8
            for label, _, slot, _ in pilot.models:
                expected[slot // 4] = 0x6000000 + report['model_offsets'][label]
            self.assertEqual(struct.unpack_from('>8I', profile, 16), tuple(expected))
            self.assertEqual(profile[56:68], bytes.fromhex('040000000000000000000000'))
            asset = (self.output / report['object_file']).read_bytes()
            for model in report['models']:
                code = asset[model['native_offset']:model['native_offset'] + model['bytes']]
                actual = [(b >> 8 & 3, b >> 18 & 3, b >> 4 & 15, b >> 14 & 15)
                          for a, b in struct.iter_unpack('>II', code)
                          if a >> 24 == 0xF5 and b >> 24 & 7 == 0]
                expected_tiles = []
                for row in prepared[3][model['layer']]['rows']:
                    if row['opcode'] != 0xFD:
                        continue
                    w, h = row['shape']
                    ws, wt = row.get('wrap_modes', (0, 0))
                    modes = {0: 2, 1: 0, 2: 1}
                    expected_tiles.append((modes[ws], modes[wt], w.bit_length() - 1, h.bit_length() - 1))
                    if (ws, wt) == (2, 2):
                        mirrors.append(pilot.key)
                self.assertEqual(actual, expected_tiles)
        self.assertEqual(mirrors, ['well'] * 3)
        self.assertEqual(sum(p.vertex_count for p in self.pilots), 463)
        # Keep the known capacity dependency explicit; do not truncate this model.
        self.assertEqual(self.expected_sizes[2] - 0x1400, 96)


if __name__ == '__main__':
    unittest.main()
