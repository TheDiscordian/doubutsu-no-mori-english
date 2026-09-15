"""Focused static-furniture conversion checks, without original game assets."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import sha256
from gc_names import rel_sections
from v3_furniture_art import (PILOTS, SEGMENT, command_source, native_profile,
                             parse_model, prepare, scalar_profile, verify_sources)

OUTPUT = ROOT / 'build/v3-furniture-art-01'


def fixture():
    words = [(0xD7000002, 0), (0xFC127E60, 0xFFFFF3F8),
             (0xE200001C, 0xC8113078), (0xF08F4010, 0),
             (0xFD441C1F, 0), (0xD2F0F000, 0), (0xFA000080, 0xFFFFFFFF),
             (0xD9000000, 0x230405), (0x01003006, 0),
             (0x0A000000, (1 << 5 | 2 << 10) << 4), (0xDF000000, 0)]
    raw = b''.join(struct.pack('>II', *w) for w in words)
    pointers = {0x11C: 0x500, 0x124: 0x600, 0x144: 0x1000}
    return raw, pointers


def parse(raw, pointers):
    return parse_model(raw, 0x100, pointers, 0x500, {0x600: (32, 32)}, 0x1000, 48)


class FurnitureArtTests(unittest.TestCase):
    def test_static_commands_and_absolute_triangle_indices(self):
        raw, pointers = fixture()
        rows = parse(raw, pointers)
        self.assertEqual([r['triangles'] for r in rows if 'triangles' in r], [[(0, 1, 2)]])
        self.assertEqual([r['global_triangles'] for r in rows if 'triangles' in r], [[(0, 1, 2)]])
        self.assertNotIn(0xD2, [r['opcode'] for r in rows])
        self.assertEqual([r['shape'] for r in rows if 'shape' in r], [(32, 32)])

    def test_reject_unsupported_state_pointers_and_command_bounds(self):
        raw, pointers = fixture()
        for offset, value in ((0, 0xDE000000), (0x28, 0xD2F0FA00),
                              (0x10, 0xE3000000), (0x40, 0x01004008),
                              (0x4C, (1 << 5 | 3 << 10) << 4), (0x18, 0xF08F4011)):
            changed = bytearray(raw)
            struct.pack_into('>I', changed, offset, value)
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                parse(changed, pointers)
        for changed in (raw[:-8], raw + bytes(8), raw[:-1]):
            with self.assertRaises(ValueError):
                parse(changed, pointers)
        for changed in ({**pointers, 0x144: 0x1010}, {**pointers, 0x104: 0x500},
                        {k: v for k, v in pointers.items() if k != 0x11C}):
            with self.assertRaises(ValueError):
                parse(raw, changed)

    def test_native_compiler_input_replaces_every_dolphin_operation(self):
        rows = parse(*fixture())
        models = {'opaque': {'rows': rows}}
        source, sections = command_source(models, {0x500: 0, 0x600: 0x20, 0x1000: 0x220})
        self.assertIn('gsSPTexture(0xFFFF, 0xFFFF', source)
        self.assertIn('gsDPLoadTLUT_pal16(15, 0x06000000)', source)
        self.assertIn('gsSPVertex(0x06000220, 3, 0)', source)
        self.assertIn('gsSP1Triangle(0, 1, 2, 0)', source)
        for forbidden in ('0xF08F', '0xFD44', '0xD2F0', '0x0A00'):
            self.assertNotIn(forbidden, source)
        self.assertEqual(sections, (('opaque', 25 * 8),))
        changed = deepcopy(models)
        changed['opaque']['rows'][0] = {'opcode': 0xDE, 'words': (0xDE000000, 0x80000000)}
        with self.assertRaises(ValueError):
            command_source(changed, {})

    def test_native_profile_preserves_both_layers_and_exact_scalar_fields(self):
        for pilot in PILOTS:
            result = native_profile(pilot, 0xC90, {'opaque': 0xA60, 'translucent': 0xBB0}, 0x3E00000)
            self.assertEqual(len(result), 0x44)
            self.assertEqual(struct.unpack_from('>4I', result), (0x3E00000, 0x3E00C90, SEGMENT, SEGMENT + 0xC90))
            self.assertEqual(struct.unpack_from('>8I', result, 16), (0x6000A60, 0, 0x6000BB0, 0, 0, 0, 0, 0))
            self.assertEqual(result[0x30:0x40], scalar_profile(pilot))
            self.assertEqual(result[0x40:], bytes(4))
        for size, models, vrom in ((0xC90, {'opaque': 0xA60}, 0x3E00000),
                                  (0xC90, {'opaque': 0xC90, 'translucent': 0xBB0}, 0x3E00000),
                                  (0xC90, {'opaque': 0xA61, 'translucent': 0xBB0}, 0x3E00000),
                                  (0xC91, {'opaque': 0xA60, 'translucent': 0xBB0}, 0x3E00000),
                                  (0xC90, {'opaque': 0xA60, 'translucent': 0xBB0}, 0x3FFFFF0)):
            with self.assertRaises(ValueError):
                native_profile(PILOTS[0], size, models, vrom)

    def test_unsupported_source_revision_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'pinned English donor'):
            verify_sources(b'not the supplied donor', b'not the pinned symbols')


class FurnitureArtLocalTests(unittest.TestCase):
    output = OUTPUT
    pilots = PILOTS
    expected_hashes = ('27693e1512114e3091a7675b228e0e60643ec6114ceb55e59cb5a09c8316a42a',
                       '0c5e51be4d6bda888fd52b5f5c25ca1dc5e5b93e9b2ada16b3aef2198845d2f2')
    expected_sizes = (3216, 3216)

    @classmethod
    def setUpClass(cls):
        if not (cls.output / 'art.json').exists():
            raise unittest.SkipTest('Local furniture asset conversion is not built')
        cls.rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.report = json.loads((cls.output / 'art.json').read_text())
        cls.prepared = [prepare(cls.rel, cls.symbols, pilot) for pilot in cls.pilots]

    def test_complete_assets_preserve_texels_palette_and_geometry(self):
        base = rel_sections(self.rel)[5][0]
        self.assertEqual(len(self.report['objects']), len(self.pilots))
        for pilot, prepared, report, digest, size in zip(
                self.pilots, self.prepared, self.report['objects'], self.expected_hashes,
                self.expected_sizes, strict=True):
            body, resources, offsets, models = prepared
            asset = (self.output / report['object_file']).read_bytes()
            self.assertEqual(asset[:len(body)], body)
            self.assertEqual(len(asset), size)
            self.assertEqual(sha256(asset), digest)
            self.assertEqual(report['object_sha256'], digest)
            self.assertFalse(report['selectable'])
            self.assertIsNone(report['target_item_id'])
            for resource in resources:
                at, size, dst = (resource[k] for k in ('donor_offset', 'bytes', 'native_offset'))
                original, native = self.rel[base + at:base + at + size], asset[dst:dst + size]
                self.assertEqual(sha256(native), resource['output_sha256'])
                if resource['symbol'].endswith('_pal'):
                    for (gc,), (n64,) in zip(struct.iter_unpack('>H', original), struct.iter_unpack('>H', native)):
                        if gc & 0x8000:
                            expected = (gc & 0x7FFF) << 1 | 1
                        else:
                            colours = [((gc >> shift & 15) * 17) >> 3 for shift in (8, 4, 0)]
                            self.assertIn(gc >> 12, (0, 7))
                            expected = colours[0] << 11 | colours[1] << 6 | colours[2] << 1 | (gc >> 12 == 7)
                        self.assertEqual(n64, expected)
                elif resource['symbol'].endswith('_v'):
                    for start in range(0, size, 16):
                        self.assertEqual(native[start:start + 6], original[start:start + 6])
                        self.assertEqual(native[start + 6:start + 8], bytes(2))
                        self.assertEqual(native[start + 8:start + 16], original[start + 8:start + 16])
                else:
                    suffix = resource['symbol'][len(pilot.stem) + 1:-len('_tex_txt')]
                    w, h = next((w, h) for name, w, h in pilot.textures if name == suffix)
                    # Independent GX 8x8 block addressing, compared to every
                    # native row-major nibble. No shared untile implementation.
                    for y in range(h):
                        for x in range(w):
                            gx = ((y // 8) * (w // 8) + x // 8) * 64 + (y % 8) * 8 + x % 8
                            n64 = y * w + x
                            self.assertEqual(original[gx // 2] >> (4 if gx % 2 == 0 else 0) & 15,
                                             native[n64 // 2] >> (4 if n64 % 2 == 0 else 0) & 15)

    def test_actual_compiled_lists_keep_faces_materials_and_native_load_bounds(self):
        for prepared, report in zip(self.prepared, self.report['objects']):
            body, resources, offsets, models = prepared
            asset = (self.output / report['object_file']).read_bytes()
            source, sections = command_source(models, offsets)
            self.assertEqual(sha256(source.encode()), report['command_source_sha256'])
            for model_report in report['models']:
                layer = model_report['layer']
                at, size = model_report['native_offset'], model_report['bytes']
                code = asset[at:at + size]
                self.assertEqual(size, dict(sections)[layer])
                self.assertEqual(sha256(code), model_report['output_sha256'])
                donor = models[layer]['rows']
                expected = [t for row in donor for t in row.get('global_triangles', [])]
                faces, loads, state, shapes = [], [], [], []
                first, count = 0, 0
                for a, b in struct.iter_unpack('>II', code):
                    op = a >> 24
                    self.assertIn(op, (0xE7, 0xE8, 0xE3, 0xD7, 0xFC, 0xE2, 0xFD, 0xF5,
                                       0xE6, 0xF0, 0xF3, 0xF2, 0xFA, 0xD9, 0x01, 0x05, 0x06, 0xDF))
                    if op in (0xFC, 0xE2, 0xFA, 0xD9):
                        state.append((a, b))
                    if op == 0xF0:
                        self.assertEqual((a, b), (0xF0000000, 0x0703C000))
                    if op == 0xFD:
                        self.assertIn(a, (0xFD100000, 0xFD500000))
                        self.assertEqual(b >> 24, 6)
                        self.assertIn(b - SEGMENT, offsets.values())
                        loads.append(b - SEGMENT)
                    if op == 0xD7:
                        self.assertEqual((a, b), (0xD7000002, 0xFFFFFFFF))
                    if op == 0xF2:
                        shapes.append(((b >> 12 & 4095) // 4 + 1, (b & 4095) // 4 + 1))
                    if op == 0x01:
                        self.assertEqual(b >> 24, 6)
                        count = a >> 12 & 255
                        self.assertLessEqual(b - SEGMENT + count * 16, len(body))
                        first = (b - SEGMENT - resources[-1]['native_offset']) // 16
                    if op in (0x05, 0x06):
                        for word in ((a, b) if op == 0x06 else (a,)):
                            indices = tuple(word >> shift & 255 for shift in (16, 8, 0))
                            self.assertTrue(all(i % 2 == 0 and i // 2 < count for i in indices))
                            faces.append(tuple(first + i // 2 for i in indices))
                self.assertEqual(faces, expected)
                self.assertEqual(len(faces), model_report['triangles'])
                self.assertEqual(loads, [offsets[r['target']] for r in donor if r['opcode'] in (0xF0, 0xFD)])
                expected_shapes = []
                for row in donor:
                    if row['opcode'] in (0xFD, 0xD2):
                        expected_shapes.append(row['shape'])
                    elif row['opcode'] == 0xF2:
                        b = row['words'][1]
                        expected_shapes.append(((b >> 12 & 4095) // 4 + 1, (b & 4095) // 4 + 1))
                self.assertEqual(shapes, expected_shapes)
                self.assertEqual(state, [r['words'] for r in donor if r['opcode'] in (0xFC, 0xE2, 0xFA, 0xD9)])
                self.assertEqual(code[-8:], struct.pack('>II', 0xDF000000, 0))
        self.assertFalse(self.report['runtime_installed'])


if __name__ == '__main__':
    unittest.main()
