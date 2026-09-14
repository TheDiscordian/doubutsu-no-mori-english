"""Actual islander accessory identity, complete pixels, and native model checks."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from gc_names import rel_sections
from v3_accessory_art import ACCESSORIES, command_records, prepare
from v3_furniture_art import SEGMENT, command_source, parse_model
from tests.test_v3_furniture_art import fixture

OUTPUT = ROOT/'build/v3-accessory-art-03'


class AccessoryParserTests(unittest.TestCase):
    def test_mirrored_tiles_edge_mode_and_shading_are_explicit(self):
        raw, pointers = fixture()
        raw = bytearray(raw)
        for at, value in ((0x14, 0xC8112078), (0x28, 0xD2F0F900), (0x34, 0xB2B2B2FF)):
            struct.pack_into('>I', raw, at, value)
        args = (0x100, pointers, 0x500, {0x600: (32, 32)}, 0x1000, 48)
        with self.assertRaises(ValueError):
            parse_model(raw, *args)
        rows = parse_model(raw, *args, accessory=True)
        self.assertEqual(next(r for r in rows if r['opcode'] == 0xFD)['wrap_modes'], (2, 1))
        source, sections = command_source({'accessory': {'rows': rows}},
                                           {0x500: 0, 0x600: 32, 0x1000: 544})
        self.assertIn('G_TX_MIRROR | G_TX_WRAP, G_TX_WRAP, 5, 5, 0, 0', source)
        self.assertIn('0xC8112078', source)
        self.assertIn('0xB2B2B2FF', source)
        self.assertEqual(sections, (('accessory', 200),))
        for at, value in ((0x28, 0xD2F0FA00), (0x34, 0xB2B2B280), (0x14, 0xC8104DD8)):
            changed = bytearray(raw)
            struct.pack_into('>I', changed, at, value)
            with self.assertRaises(ValueError):
                parse_model(changed, *args, accessory=True)
        with self.assertRaises(ValueError):
            parse_model(raw, *args, accessory=True, speed_bag=True)

    def test_explicit_tile_extents_and_packed_payload_bounds(self):
        raw, pointers = fixture()
        extent = struct.pack('>II', 0xF2000000, 0xFC07C)
        args = (0x100, pointers, 0x500, {0x600: (32, 32)}, 0x1000, 48)
        data = raw[:-8]+extent+raw[-8:]
        rows = parse_model(data, *args, accessory=True)
        self.assertEqual(rows[-2]['words'], (0xF2000000, 0xFC07C))
        with self.assertRaises(ValueError):
            parse_model(data, *args)
        with self.assertRaises(ValueError):
            list(command_records(struct.pack('>II', 0x0AFE0000, 0)))
        with self.assertRaises(ValueError):
            prepare(b'unknown donor', b'unknown symbols')


@unittest.skipUnless((OUTPUT/'art.json').exists(), 'Current accessory conversion required')
class AccessoryActualSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.prepared = prepare(cls.rel, cls.symbols)
        cls.report = json.loads((OUTPUT/'art.json').read_text())

    def test_all_sixteen_bind_real_villagers_profiles_draw_functions_and_objects(self):
        self.assertEqual([r['key'] for r in self.prepared], list(ACCESSORIES))
        self.assertEqual([r['tool'] for r in self.prepared], list(range(52, 68)))
        consumers = [r['consumers'][0]['donor_villager_index'] for r in self.prepared]
        self.assertEqual(set(consumers), set(range(216, 236))-{224, 232, 233, 235})
        for entry, record in zip(self.prepared, self.report['objects']):
            for key in ('key', 'tool', 'consumers', 'profile_id', 'profile_sha256',
                        'draw_function_sha256', 'model_source_sha256', 'resources'):
                self.assertEqual(record[key], entry[key])
            self.assertEqual(sorted(r[1] for r in entry['draw_model_relocations']), [4, 6])
            asset = (OUTPUT/record['object_file']).read_bytes()
            self.assertEqual(len(asset), record['object_bytes'])
            self.assertEqual(sha256(asset), record['object_sha256'])
            self.assertEqual(asset[:len(entry['body'])], entry['body'])
            self.assertFalse(record['runtime_installed'])
            self.assertFalse(record['selectable'])
        self.assertFalse(self.report['runtime_installed'])

    def test_every_texel_palette_and_vertex_is_preserved_in_native_format(self):
        base = rel_sections(self.rel)[5][0]
        for record in self.report['objects']:
            asset = (OUTPUT/record['object_file']).read_bytes()
            for resource in record['resources']:
                at, size, dest = (resource[k] for k in ('donor_offset', 'bytes', 'native_offset'))
                original, native = self.rel[base+at:base+at+size], asset[dest:dest+size]
                self.assertEqual(sha256(native), resource['output_sha256'])
                if resource['kind'] == 'palette':
                    for (gc,), (n64,) in zip(struct.iter_unpack('>H', original), struct.iter_unpack('>H', native)):
                        if gc & 0x8000:
                            expected = (gc & 0x7FFF) << 1 | 1
                        else:
                            channels = [((gc >> shift & 15)*17) >> 3 for shift in (8, 4, 0)]
                            self.assertIn(gc >> 12, (0, 7))
                            expected = channels[0] << 11 | channels[1] << 6 | channels[2] << 1 | (gc >> 12 == 7)
                        self.assertEqual(n64, expected)
                elif resource['kind'] == 'vertices':
                    for pos in range(0, size, 16):
                        self.assertEqual(native[pos:pos+6], original[pos:pos+6])
                        self.assertEqual(native[pos+6:pos+8], bytes(2))
                        self.assertEqual(native[pos+8:pos+16], original[pos+8:pos+16])
                else:
                    width, height = resource['width'], resource['height']
                    for y in range(height):
                        for x in range(width):
                            gx = ((y//8)*(width//8)+x//8)*64+(y%8)*8+x%8
                            n64 = y*width+x
                            self.assertEqual(original[gx//2] >> (4 if gx%2 == 0 else 0) & 15,
                                             native[n64//2] >> (4 if n64%2 == 0 else 0) & 15)

    def test_compiled_lists_preserve_every_face_material_wrap_and_state(self):
        for entry, record in zip(self.prepared, self.report['objects']):
            asset = (OUTPUT/record['object_file']).read_bytes()
            start, size = record['native_model_offset'], record['native_model_bytes']
            code = asset[start:start+size]
            self.assertEqual(sha256(code), record['native_model_sha256'])
            rows = entry['rows']
            expected_faces = [t for row in rows for t in row.get('global_triangles', ())]
            faces, loads, states, shapes, wraps = [], [], [], [], []
            first = count = 0
            vertices = next(r for r in entry['resources'] if r['kind'] == 'vertices')
            for a, b in struct.iter_unpack('>II', code):
                op = a >> 24
                self.assertIn(op, (0xE7, 0xE8, 0xE3, 0xD7, 0xFC, 0xE2, 0xFD, 0xF5,
                                  0xE6, 0xF0, 0xF3, 0xF2, 0xFA, 0xD9, 0x01, 0x05, 0x06, 0xDF))
                if op in (0xFC, 0xE2, 0xFA, 0xD9):
                    states.append((a, b))
                elif op == 0xFD:
                    self.assertIn(a, (0xFD100000, 0xFD500000))
                    self.assertEqual(b >> 24, 6)
                    self.assertIn(b-SEGMENT, entry['offsets'].values())
                    loads.append(b-SEGMENT)
                elif op == 0xF5 and b >> 24 & 7 == 0:
                    wraps.append((b >> 8 & 3, b >> 18 & 3, b >> 4 & 15, b >> 14 & 15))
                elif op == 0xF2:
                    self.assertEqual(a, 0xF2000000)
                    shapes.append(((b >> 12 & 4095)//4+1, (b & 4095)//4+1))
                elif op == 0x01:
                    self.assertEqual(b >> 24, 6)
                    count = a >> 12 & 255
                    self.assertLessEqual(b-SEGMENT+count*16, len(entry['body']))
                    first = (b-SEGMENT-vertices['native_offset'])//16
                elif op in (0x05, 0x06):
                    for word in ((a, b) if op == 0x06 else (a,)):
                        ids = tuple(word >> shift & 255 for shift in (16, 8, 0))
                        self.assertTrue(all(i%2 == 0 and i//2 < count for i in ids))
                        faces.append(tuple(first+i//2 for i in ids))
            self.assertEqual(faces, expected_faces)
            self.assertEqual(len(faces), record['triangles'])
            self.assertEqual(loads, [entry['offsets'][r['target']] for r in rows if r['opcode'] in (0xF0, 0xFD)])
            self.assertEqual(states, [r['words'] for r in rows if r['opcode'] in (0xFC, 0xE2, 0xFA, 0xD9)])
            expected_shapes = []
            for row in rows:
                if row['opcode'] == 0xFD:
                    expected_shapes.append(row['shape'])
                elif row['opcode'] == 0xF2:
                    b = row['words'][1]
                    expected_shapes.append(((b >> 12 & 4095)//4+1, (b & 4095)//4+1))
            self.assertEqual(shapes, expected_shapes)
            native_wrap = {0: 2, 1: 0, 2: 1}
            self.assertEqual(wraps, [(native_wrap[r['wrap_modes'][0]], native_wrap[r['wrap_modes'][1]],
                                     r['shape'][0].bit_length()-1, r['shape'][1].bit_length()-1)
                                    for r in rows if r['opcode'] == 0xFD])
            self.assertEqual(code[-8:], bytes.fromhex('DF00000000000000'))


if __name__ == '__main__':
    unittest.main()
