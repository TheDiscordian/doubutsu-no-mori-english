"""Complete campsite assets, mixed material state, and dynamic bindings."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))

from aflib import sha256
from gc_names import rel_sections
from v3_campsite_art import PARTS, SEGMENT, SHADOW_FLAGS, command_source, exact_symbol, parse_model, prepare
from v3_villager_art import data_pointers, native_palette

OUTPUT = ROOT / 'build/v3-campsite-art-01'


class CampsiteArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.base = rel_sections(cls.rel)[5][0]
        cls.report = json.loads((OUTPUT / 'art.json').read_bytes())
        cls.prepared = [prepare(cls.rel, cls.symbols, part) for part in PARTS]
        cls.assets = [(OUTPUT / row['object_file']).read_bytes() for row in cls.report['objects']]

    def test_complete_resources_and_deterministic_object_identity(self):
        expected = (
            (6960, '6b44fc60069c6909a637a078cb5a463a4056e7d3fd99ca5a2921a883623226bd'),
            (800, '1961620809af4849ae7301e56015ff59571d36ee491961c8a7af82c5919f9a5a'),
            (19872, '34211a356606d7adbf01ef655c847d067bbf9c6e0ee1a146738bf279a15400ce'),
            (3248, '7b920ca7cd74f94554dfd322c2c8af8cc95ea28c4591debf2d8804579b8739dd'))
        for prepared, asset, report, (size, digest) in zip(self.prepared, self.assets,
                self.report['objects'], expected, strict=True):
            body, resources, *_ = prepared
            self.assertEqual(asset[:len(body)], body)
            self.assertEqual((len(asset), sha256(asset)), (size, digest))
            self.assertEqual(report['object_sha256'], digest)
            self.assertFalse(report['runtime_installed'])
            for row in resources:
                at, size, dst = (row[k] for k in ('donor_offset', 'bytes', 'native_offset'))
                raw = self.rel[self.base + at:self.base + at + size]
                native = asset[dst:dst + size]
                self.assertEqual(sha256(raw), row['source_sha256'])
                self.assertEqual(sha256(native), row['output_sha256'])
                if row['kind'] == 'rgba16':
                    self.assertEqual(native, native_palette(raw))
                elif row['kind'] in ('ci4', 'i4'):
                    w, h = row['width'], row['height']
                    for y in range(h):
                        for x in range(w):
                            donor = ((y // 8) * (w // 8) + x // 8) * 64 + y % 8 * 8 + x % 8
                            linear = y * w + x
                            self.assertEqual(raw[donor // 2] >> (4 if donor % 2 == 0 else 0) & 15,
                                             native[linear // 2] >> (4 if linear % 2 == 0 else 0) & 15)
                elif row['kind'] == 'vertices':
                    for n in range(0, size, 16):
                        self.assertEqual(native[n:n + 6] + native[n + 8:n + 16],
                                         raw[n:n + 6] + raw[n + 8:n + 16])
                        self.assertEqual(native[n + 6:n + 8], bytes(2))
                else:
                    self.assertEqual(native, SHADOW_FLAGS)
        self.assertFalse(self.report['runtime_installed'])
        self.assertFalse(self.report['web_patcher_enabled'])

    def test_every_face_pointer_and_material_survives_native_compilation(self):
        for part, prepared, asset, report in zip(PARTS, self.prepared, self.assets,
                self.report['objects'], strict=True):
            _, resources, offsets, model = prepared
            source, sections = command_source(part, offsets, model)
            self.assertEqual(sha256(source.encode()), report['command_source_sha256'])
            desc = report['model']
            code = asset[desc['native_offset']:desc['native_offset'] + desc['bytes']]
            self.assertEqual(len(code), dict(sections)['model'])
            self.assertEqual(sha256(code), desc['output_sha256'])
            vertex = next(r for r in resources if r['kind'] == 'vertices')
            targets = {SEGMENT + r['native_offset']: r for r in resources}
            faces, states, loads, calls, luts = [], [], [], [], []
            count, first, lut = 0, 0, None
            for a, b in struct.iter_unpack('>II', code):
                op = a >> 24
                self.assertIn(op, (0xE7, 0xE8, 0xE3, 0xD7, 0xFC, 0xE2, 0xFD, 0xF5,
                    0xE6, 0xF0, 0xF3, 0xF4, 0xF2, 0xFA, 0xD9, 0x01, 0x05, 0x06, 0xDE, 0xDF))
                if op in (0xFC, 0xE2, 0xFA, 0xD9):
                    states.append((a, b))
                if op == 0xD7:
                    self.assertEqual((a, b), (0xD7000002, 0xFFFFFFFF))
                if op == 0xE3:
                    self.assertEqual(a, 0xE3001001)
                    self.assertIn(b, (0, 0x8000))
                    lut = b
                    luts.append(b)
                if op == 0xFD:
                    self.assertIn(b, targets)
                    resource = targets[b]
                    self.assertEqual(a >> 21 & 7, {'rgba16': 0, 'ci4': 2, 'i4': 4}[resource['kind']])
                    if resource['kind'] != 'rgba16':
                        self.assertEqual(lut, 0 if resource['kind'] == 'i4' else 0x8000)
                    loads.append(b)
                if op == 0xDE:
                    self.assertEqual(part.key, 'exterior')
                    self.assertEqual((a, b), (0xDE000000, 0x08000000))
                    calls.append(b)
                if op == 1:
                    count = a >> 12 & 255
                    if part.key == 'shadow':
                        self.assertEqual((b, count), (0x08000000, 28))
                        first = 0
                    else:
                        self.assertEqual(b >> 24, 6)
                        at = b - SEGMENT - vertex['native_offset']
                        self.assertEqual(at % 16, 0)
                        self.assertTrue(0 <= at <= vertex['bytes'] - count * 16)
                        first = at // 16
                if op in (5, 6):
                    for word in ((a, b) if op == 6 else (a,)):
                        indices = tuple(word >> shift & 255 for shift in (16, 8, 0))
                        self.assertTrue(all(i % 2 == 0 and i // 2 < count for i in indices))
                        faces.append(tuple(first + i // 2 for i in indices))
            self.assertEqual(faces, [t for r in model['rows'] for t in r.get('global_triangles', ())])
            self.assertEqual(len(faces), part.triangles)
            self.assertEqual(states, [r['words'] for r in model['rows'] if r['opcode'] in (0xFC, 0xE2, 0xFA, 0xD9)])
            self.assertEqual(loads, [SEGMENT + offsets[r['target']] for r in model['rows'] if r['opcode'] in (0xF0, 0xFD)])
            self.assertEqual(calls, [0x08000000] if part.key == 'exterior' else [])
            self.assertEqual(luts, [0x8000, 0] if part.key == 'interior' else [0] if part.key == 'shadow' else [0x8000])
            self.assertEqual(code[-8:], struct.pack('>II', 0xDF000000, 0))

    def test_two_lantern_tiles_keep_both_palettes_and_do_not_overlap(self):
        asset, report = self.assets[3], self.report['objects'][3]
        desc = report['model']
        code = asset[desc['native_offset']:desc['native_offset'] + desc['bytes']]
        words = list(struct.iter_unpack('>II', code))
        tiles = [(a, b) for a, b in words if a >> 24 == 0xF5 and b >> 24 & 7 != 7]
        self.assertEqual(len(tiles), 2)
        for i, (a, b) in enumerate(tiles):
            self.assertEqual((a >> 21 & 7, a >> 19 & 3, a >> 9 & 511, a & 511), (2, 0, 2, i * 128))
            self.assertEqual((b >> 24 & 7, b >> 20 & 15, b >> 8 & 3, b >> 18 & 3,
                b >> 4 & 15, b >> 14 & 15, b & 15, b >> 10 & 15), (i, 15 - i, 1, 2, 5, 6, 0, 0))
        pal_loads = [a & 511 for a, b in words if a >> 24 == 0xF5 and b >> 24 & 7 == 7 and a >> 21 & 7 == 0]
        self.assertEqual(pal_loads, [0x100 + 15 * 16, 0x100 + 14 * 16])

    def test_interior_retains_empty_translucent_list_and_not_furniture_bank_limit(self):
        asset, report = self.assets[2], self.report['objects'][2]
        at = report['empty_model_offset']
        self.assertEqual(asset[at:at + 8], struct.pack('>II', 0xDF000000, 0))
        self.assertGreater(len(asset), 0x2400)
        self.assertIsNone(self.report['objects'][0]['empty_model_offset'])

    def test_fail_closed_for_wrong_sources_missing_pointers_and_dynamic_segments(self):
        with self.assertRaisesRegex(ValueError, 'pinned English donor'):
            prepare(self.rel[:-1], self.symbols, PARTS[0])
        for part in PARTS:
            prepared = self.prepared[PARTS.index(part)]
            _, resources, _, _ = prepared
            palettes = tuple(r['donor_offset'] for r in resources if r['kind'] == 'rgba16')
            textures = {r['donor_offset']: (r['width'], r['height'], r['kind'])
                        for r in resources if r['kind'] in ('ci4', 'i4')}
            vertex = next(r['donor_offset'] for r in resources if r['kind'] == 'vertices')
            start = exact_symbol(self.symbols.decode(), part.model, part.model_size)
            raw = self.rel[self.base + start:self.base + start + part.model_size]
            pointers = data_pointers(self.rel, start, part.model_size)
            with self.assertRaisesRegex(ValueError, 'Missing campsite data relocation'):
                parse_model(raw, start, {}, part, palettes, textures, vertex)
            if part.key in ('exterior', 'shadow'):
                raw = raw.replace(bytes.fromhex('08000000'), bytes.fromhex('09000000'))
                with self.assertRaises(ValueError):
                    parse_model(raw, start, pointers, part, palettes, textures, vertex)


if __name__ == '__main__':
    unittest.main()
