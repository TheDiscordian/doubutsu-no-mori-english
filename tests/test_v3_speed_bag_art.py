"""Speed-bag source binding, complete conversion, and native rig layout."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from gc_names import rel_sections
from v3_furniture_art import command_source, parse_model
from v3_speed_bag_art import SEGMENT, STEM, TEXTURES, finish, prepare, validate_animation
from v3_villager_art import data_pointers
from tests.test_v3_furniture_art import fixture as static_fixture

OUTPUT = ROOT/'build/v3-speed-bag-art-01'


class SpeedBagArtTests(unittest.TestCase):
    def test_environment_map_is_explicit_and_unknown_settings_fail(self):
        raw, pointers = static_fixture()
        raw = bytearray(raw)
        for at, word in ((4, 0x0FA00FA0), (0x20, 0xFD440C0F),
                         (0x28, 0xD2F0F522), (0x3C, 0x270405)):
            struct.pack_into('>I', raw, at, word)
        args = (0x100, pointers, 0x500, {0x600: (16, 16)}, 0x1000, 48)
        with self.assertRaises(ValueError): parse_model(raw, *args)
        rows = parse_model(raw, *args, speed_bag=True)
        source, sections = command_source({'ball': {'rows': rows}}, {0x500: 0, 0x600: 32, 0x1000: 160})
        self.assertIn('gsSPTexture(4000, 4000', source)
        self.assertIn('G_TX_WRAP, G_TX_WRAP, 4, 4, 2, 2', source)
        self.assertIn('0x00270405', source)
        self.assertEqual(sections, (('ball', 200),))
        for at, word in ((4, 0x0FA10FA0), (0x28, 0xD2F0F523), (0x3C, 0x270005)):
            changed = bytearray(raw); struct.pack_into('>I', changed, at, word)
            with self.assertRaises(ValueError): parse_model(changed, *args, speed_bag=True)
        rows[0]['texture_scale'] = (4001, 4000)
        with self.assertRaises(ValueError): command_source({'ball': {'rows': rows}}, {})

    def test_animation_track_bounds_and_pointer_target_sections(self):
        counts = struct.pack('>3h', 2, 11, 11)
        frames = [1, 7, 13, 19, 25, 31, 37, 43, 49, 57, 69]
        keys = b''.join(struct.pack('>3h', frame, 0, 0) for frame in [1, 69]+frames+frames)
        self.assertEqual(len(validate_animation(bytes((0, 7)), counts, bytes(12), keys)), 3)
        for values in ((bytes((0, 6)), counts, bytes(12), keys),
                       (bytes((0, 7)), counts, bytes(12), keys[:-2]),
                       (bytes((0, 7)), counts, bytes(12), b'\0\0'+keys[2:])):
            with self.assertRaises(ValueError): validate_animation(*values)
        # Synthetic REL: data slot zero points into the same module's text.
        rel = bytearray(0x140)
        struct.pack_into('>I', rel, 0, 7)
        struct.pack_into('>II', rel, 12, 6, 0x48)
        struct.pack_into('>II', rel, 0x50, 0x80, 16)
        struct.pack_into('>II', rel, 0x70, 0x90, 16)
        struct.pack_into('>II', rel, 0x28, 0xA0, 8)
        struct.pack_into('>II', rel, 0xA0, 7, 0xB0)
        struct.pack_into('>HBBIHBBIHBBI', rel, 0xB0, 0, 202, 5, 0, 0, 1, 1, 4, 0, 203, 0, 0)
        self.assertEqual(data_pointers(rel, 0, 4, expected_section=1), {0: 4})
        with self.assertRaises(ValueError): data_pointers(rel, 0, 4)
        for at, value in ((0xBC, 16), (0xA0, 8)):
            changed = bytearray(rel); struct.pack_into('>I', changed, at, value)
            with self.assertRaises(ValueError): data_pointers(changed, 0, 4, expected_section=1)
        with self.assertRaises(ValueError): data_pointers(rel, 0, 4, expected_section=6)

    def test_unsupported_source_is_rejected(self):
        with self.assertRaises(ValueError): prepare(b'wrong donor', b'wrong symbols')


@unittest.skipUnless((OUTPUT/'art.json').exists(), 'Current speed-bag conversion required')
class SpeedBagLocalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.report = json.loads((OUTPUT/'art.json').read_text())
        cls.asset = (OUTPUT/'speed-bag.n64obj.bin').read_bytes()
        cls.prepared = prepare(cls.rel, cls.symbols)

    def test_complete_texels_palettes_vertices_and_animation_arrays(self):
        body, resources, offsets, models, rig, details = self.prepared
        self.assertEqual(self.asset[:len(body)], body)
        self.assertEqual(len(self.asset), 3728)
        self.assertEqual(sha256(self.asset), '3b10054b80021c00a5a12d98aeb4afcd76b7201ad68f55c1ac77c1b3a7844893')
        self.assertEqual(sha256(self.asset), self.report['object_sha256'])
        self.assertFalse(self.report['runtime_installed'])
        self.assertFalse(self.report['behaviour_installed'])
        self.assertFalse(self.report['selectable'])
        self.assertIsNone(self.report['target_item_id'])
        base = rel_sections(self.rel)[5][0]
        for resource in resources:
            at, size, dst = (resource[k] for k in ('donor_offset', 'bytes', 'native_offset'))
            original = self.rel[base+at:base+at+size]
            actual = self.asset[dst:dst+size]
            self.assertEqual(sha256(original), resource['source_sha256'])
            self.assertEqual(sha256(actual), resource['output_sha256'])
            name = resource['symbol']
            if name.endswith('_pal'):
                for (gc,), (n64,) in zip(struct.iter_unpack('>H', original), struct.iter_unpack('>H', actual)):
                    if gc & 0x8000:
                        expected = ((gc & 0x7FFF) << 1) | 1
                    else:
                        self.assertIn(gc >> 12, (0, 7))
                        r, g, b = [((gc >> s & 15)*17) >> 3 for s in (8, 4, 0)]
                        expected = r << 11 | g << 6 | b << 1 | (gc >> 12 == 7)
                    self.assertEqual(n64, expected)
            elif name.endswith('_tex_txt'):
                suffix = name[len(STEM)+1:-8]
                width, height = next((w, h) for label, w, h in TEXTURES if label == suffix)
                for y in range(height):
                    for x in range(width):
                        gx = ((y//8)*(width//8)+x//8)*64+(y%8)*8+x%8
                        n64 = y*width+x
                        self.assertEqual(original[gx//2] >> (4 if gx%2 == 0 else 0) & 15,
                                         actual[n64//2] >> (4 if n64%2 == 0 else 0) & 15)
            elif name.endswith('_v'):
                for at in range(0, size, 16):
                    self.assertEqual(actual[at:at+6]+actual[at+8:at+16],
                                     original[at:at+6]+original[at+8:at+16])
                    self.assertEqual(actual[at+6:at+8], bytes(2))
            else:
                self.assertEqual(actual, original)
        self.assertEqual([r['symbol'] for r in details['callbacks']], ['fIPPnch_ct', 'fIPPnch_mv', 'fIPPnch_dw'])

    def test_compiled_faces_materials_and_environment_map(self):
        body, resources, offsets, models, *_ = self.prepared
        source, sections = command_source(models, offsets)
        self.assertEqual(sha256(source.encode()), self.report['command_source_sha256'])
        vertex = next(r['native_offset'] for r in resources if r['symbol'].endswith('_v'))
        for model in self.report['models']:
            rows = models[model['part']]['rows']
            code = self.asset[model['native_offset']:model['native_offset']+model['bytes']]
            self.assertEqual(sha256(code), model['output_sha256'])
            self.assertEqual(len(code), dict(sections)[model['part']])
            faces, loads, shapes, modes, scales, tiles = [], [], [], [], [], []
            first, count = 0, 0
            for a, b in struct.iter_unpack('>II', code):
                op = a >> 24
                self.assertIn(op, (0xE7, 0xE8, 0xE3, 0xD7, 0xFC, 0xE2, 0xFD, 0xF5,
                                   0xE6, 0xF0, 0xF3, 0xF2, 0xFA, 0xD9, 0x01, 0x05, 0x06, 0xDF))
                if op in (0xFC, 0xE2, 0xFA, 0xD9): modes.append((a, b))
                if op == 0xD7: scales.append(b)
                if op == 0xFD:
                    self.assertIn(a, (0xFD100000, 0xFD500000))
                    self.assertIn(b-SEGMENT, offsets.values())
                    loads.append(b-SEGMENT)
                if op == 0xF2: shapes.append(((b >> 12 & 4095)//4+1, (b & 4095)//4+1))
                if op == 0xF5 and b >> 24 == 0:
                    tiles.append((b >> 8 & 3, b >> 18 & 3, b & 15, b >> 10 & 15))
                if op == 0x01:
                    self.assertEqual(b >> 24, 6)
                    count = a >> 12 & 255
                    self.assertTrue(1 <= count <= 32)
                    self.assertTrue(vertex <= b-SEGMENT <= vertex+992-count*16)
                    first = (b-SEGMENT-vertex)//16
                if op in (0x05, 0x06):
                    for word in ((a, b) if op == 0x06 else (a,)):
                        indices = tuple(word >> shift & 255 for shift in (16, 8, 0))
                        self.assertTrue(all(i%2 == 0 and i//2 < count for i in indices))
                        faces.append(tuple(first+i//2 for i in indices))
            self.assertEqual(faces, [t for row in rows for t in row.get('global_triangles', [])])
            self.assertEqual(len(faces), model['triangles'])
            self.assertEqual(loads, [offsets[r['target']] for r in rows if r['opcode'] in (0xF0, 0xFD)])
            self.assertEqual(shapes, [r['shape'] for r in rows if r['opcode'] == 0xFD])
            self.assertEqual(modes, [r['words'] for r in rows if r['opcode'] in (0xFC, 0xE2, 0xFA, 0xD9)])
            ball = model['part'] == 'ball'
            self.assertEqual(scales, [0x0FA00FA0 if ball else 0xFFFFFFFF])
            self.assertEqual(tiles, [(0, 0, 2, 2)] if ball else [(2, 2, 0, 0)]*8)

    def test_all_seven_native_rig_pointers_and_bank_bounds(self):
        body, resources, offsets, models, rig, _ = self.prepared
        compiled = {r['part']: self.asset[r['native_offset']:r['native_offset']+r['bytes']]
                    for r in self.report['models']}
        asset, _, headers, pointers = finish(body, offsets, models, rig, compiled)
        self.assertEqual(asset, self.asset)
        self.assertEqual(len(pointers), 7)
        for row in pointers:
            self.assertEqual(struct.unpack_from('>I', asset, row['offset'])[0], SEGMENT+row['target_offset'])
            self.assertTrue(0 <= row['target_offset'] < row['offset'] < len(asset))
        for label in ('animation', 'joints', 'skeleton'):
            start = headers[label]['native_offset']
            data = bytearray(asset[start:start+headers[label]['bytes']])
            for row in pointers:
                if start <= row['offset'] < start+len(data):
                    data[row['offset']-start:row['offset']-start+4] = bytes(4)
            self.assertEqual(data, rig[label][1])
        with self.assertRaises(ValueError): finish(body+bytes(5120), offsets, models, rig, compiled)
        with self.assertRaises(ValueError): finish(body, {}, models, rig, compiled)
        with self.assertRaises(ValueError): finish(body, offsets, models, rig, {'ball': compiled['ball']})


if __name__ == '__main__': unittest.main()
