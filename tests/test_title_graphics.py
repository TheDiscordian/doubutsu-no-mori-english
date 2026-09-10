"""English title strip continuity, native storage, and exact source retention."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from title_assets import DATA_BASE, extract, scoped_symbols
from title_graphics import HEADER_BYTES, SEGMENT, TMEM_BYTES, load_tile, package, slices


@unittest.skipUnless((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').is_file(),
                     'Supplied English title extraction required')
class TitleGraphicsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.blob, cls.report = package(cls.rel, cls.symbols)

    def test_complete_texture_values_and_source_animation_arrays(self):
        files, assets = extract(self.rel, self.symbols)
        textures = {row['offset']: row for row in assets['textures']}
        for model in self.report['models']:
            row = textures[model['texture']]
            start = model['texture_offset']
            self.assertEqual(self.blob[start:start+row['bytes']], files[row['file']])
        entries = scoped_symbols(self.symbols)
        for skeleton in self.report['skeletons']:
            for source, output in zip(skeleton['animation_arrays'], skeleton['array_package_offsets']):
                source = int(source, 16); size = entries[source]['bytes']
                self.assertEqual(self.blob[output:output+size], self.rel[DATA_BASE+source:DATA_BASE+source+size])

    def test_all_edges_join_and_filtering_keeps_adjacent_rows(self):
        self.assertEqual((len(self.blob), self.report['strips'], self.report['max_tmem_bytes']),
                         (280224, 107, TMEM_BYTES))
        self.assertFalse(self.report['installed'])
        for model in self.report['models']:
            _, t0, _, t1 = model['texture_bounds']
            self.assertEqual(model['strips'][0]['draw_rows'][0]*32, t0)
            self.assertEqual(model['strips'][-1]['draw_rows'][1]*32, t1)
            for a, b in zip(model['strips'], model['strips'][1:]):
                row = a['draw_rows'][1]
                self.assertEqual(row, b['draw_rows'][0])
                self.assertEqual({tuple(v) for v in a['vertices'] if v[5] == row*32},
                                 {tuple(v) for v in b['vertices'] if v[5] == row*32})
                self.assertGreater(a['load_rows'][1], row)
                self.assertLess(b['load_rows'][0], row)
            for band in model['strips']:
                self.assertLessEqual(band['tmem_bytes'], TMEM_BYTES)
                at = band['vertex_offset']
                self.assertEqual(self.blob[at:at+64], b''.join(struct.pack('>hhhHhh4B', *v) for v in band['vertices']))
            for vertex in model['vertices']:
                edge = model['strips'][0 if vertex[5] == t0 else -1]
                self.assertIn(vertex[:3]+[0]+vertex[4:], edge['vertices'])

    def test_segment_pointers_resolve_within_the_native_package(self):
        header = struct.unpack_from('>20I', self.blob)
        self.assertEqual(header[:6], (0x41465447, 1, len(self.blob), SEGMENT, 23, 3))
        pointers = [header[i] for i in (6, 7, 9, 10, 12, 13, 15, 16, 17, 18, 19)]
        model_addresses = {SEGMENT << 24 | m['package_offset'] for m in self.report['models']}
        for skeleton in self.report['skeletons']:
            skel, anim, joints = (skeleton[k] for k in ('skeleton_package_offset', 'animation_package_offset', 'joint_package_offset'))
            pointers.append(struct.unpack_from('>I', self.blob, skel+4)[0])
            pointers.extend(struct.unpack_from('>4I', self.blob, anim))
            for i, joint in enumerate(skeleton['joints']):
                shape = struct.unpack_from('>I', self.blob, joints+i*12)[0]
                if joint['model']:
                    self.assertIn(shape, model_addresses)
                    pointers.append(shape)
                else:
                    self.assertEqual(shape, 0)
        for pointer in pointers:
            self.assertEqual(pointer >> 24, SEGMENT)
            self.assertTrue(HEADER_BYTES <= (pointer & 0xFFFFFF) < len(self.blob))
            self.assertEqual(pointer & 15, 0)

    def test_oversize_tmem_and_non_affine_geometry_reject(self):
        with self.assertRaisesRegex(ValueError, 'TMEM'):
            load_tile(0x0B000060, 64, 64, 0, 17, True)
        with self.assertRaises(ValueError):
            load_tile(0x0B000060, 64, 64, 0, 65, True)
        model = deepcopy(self.report['models'][0]); model['vertices'][0][0] += 1
        with self.assertRaisesRegex(ValueError, 'affine'):
            slices(model)


if __name__ == '__main__':
    unittest.main()
