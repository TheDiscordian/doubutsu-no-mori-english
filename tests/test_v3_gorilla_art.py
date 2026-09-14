"""Complete Yodel geometry, native graphics conversion, and twenty-body bundle."""
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, u32
from gc_names import symbol_data
from v3_gorilla_art import MODEL_LIMIT, convert_commands, load_object, prepare
from v3_villager_art import (LAYOUTS, build_art, data_pointers, normalise_vertex_flags, symbol_span)
from v3_villager_mesh import faces
from tests.test_v3_islander_bodies import gx_pixel

MODEL = ROOT/'build/v3-gorilla-art-02'
BUNDLE = ROOT/'build/v3-all-villager-art-01'
ACCESSORIES = ROOT/'build/v3-accessory-art-03'


def fixture():
    commands = [(0xD7000002, 0), (0xE200001C, 0xC8112078),
                (0xFC127E60, 0xFFFFF3F8), (0xFD44040F, 0x0B000000),
                (0xD2F0F000, 0), (0xFA000080, 0xFFFFFFFF),
                (0xD9000000, 0x230405), (0x01003006, 0),
                (0x0A000000, 0x8200), (0xDF000000, 0)]
    return b''.join(struct.pack('>II', *words) for words in commands), {0x100+56+4: 0x1000}


class GorillaCommandSafety(unittest.TestCase):
    def test_native_scale_wrapping_and_palette_are_explicit(self):
        raw, pointers = fixture()
        values, size, materials, triangles = convert_commands(raw, 0x100, pointers, 0x1000, 48)
        source = '\n'.join(values)
        self.assertIn('gsSPTexture(0xFFFF, 0xFFFF', source)
        self.assertIn('gsSPVertex(0x06000000, 3, 0)', source)
        self.assertIn('gsSP1Triangle(0, 1, 2, 0)', source)
        self.assertEqual(triangles, 1)
        self.assertEqual(size, len(values)*8)
        self.assertEqual(materials[0]['palette'], 15)
        for word in (0xD2F0F200, 0xD2F0F500):
            changed = bytearray(raw)
            struct.pack_into('>I', changed, 32, word)
            text, _, _, _ = convert_commands(changed, 0x100, pointers, 0x1000, 48)
            self.assertIn('G_TX_MIRROR' if word == 0xD2F0F200 else 'G_TX_WRAP', '\n'.join(text))

    def test_unknown_states_palette_texture_cache_and_matrix_are_rejected(self):
        raw, pointers = fixture()
        for at, value in ((32, 0xD2F0E000), (32, 0xD2F0F001), (28, 0x0B000999),
                          (12, 0xC8113078), (44, 0xFFFF0080), (56, 0x01021042),
                          (0, 0xDA380003)):
            changed = bytearray(raw)
            struct.pack_into('>I', changed, at, value)
            with self.assertRaises(ValueError):
                convert_commands(changed, 0x100, pointers, 0x1000, 48)
        with self.assertRaises(ValueError):
            convert_commands(raw, 0x100, {}, 0x1000, 48)


@unittest.skipUnless((MODEL/'art.json').exists() and (BUNDLE/'art.json').exists(), 'Current Yodel model/body required')
class ActualGorillaConversion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.prepared = prepare(cls.rom, cls.rel, cls.symbols)
        cls.model, cls.report = load_object(MODEL, cls.rom, cls.rel, cls.symbols)
        cls.art, cls.body = build_art(cls.rom, cls.rel, cls.symbols, villagers=('yodel',),
            accessory_directory=ACCESSORIES, model_directory=MODEL)

    def test_all_vertices_joints_and_model_storage_are_complete(self):
        source = symbol_data(self.rel, self.symbols.decode(), 'gor_1_v')
        vertices, flags = normalise_vertex_flags(source)
        self.assertEqual(len(vertices)//16, 429)
        self.assertEqual(self.model[:len(vertices)], vertices)
        self.assertEqual(flags, 358)
        self.assertEqual(len(self.model), 10112)
        self.assertEqual(MODEL_LIMIT-len(self.model), 128)
        self.assertEqual(self.report['triangles'], 284)
        skeleton = int(self.report['skeleton'], 16) & 0xFFFFFF
        self.assertEqual(self.model[skeleton:skeleton+4], bytes.fromhex('1a0c0000'))
        joints = u32(self.model, skeleton+4) & 0xFFFFFF
        donor_joints = symbol_data(self.rel, self.symbols.decode(), 'cKF_je_r_gor_1_tbl')
        pointers = self.prepared['joint_pointers']
        offsets = {r['donor_offset']: r['native_offset'] for r in self.report['models']}
        for i in range(26):
            actual = self.model[joints+12*i:joints+12*(i+1)]
            self.assertEqual(actual[4:], donor_joints[12*i+4:12*(i+1)])
            pointer = pointers.get(self.prepared['joint_at']+12*i)
            self.assertEqual(u32(actual, 0), 0x06000000+offsets[pointer] if pointer else 0)
        self.assertEqual(self.model[skeleton+8:], bytes(len(self.model)-skeleton-8))
        self.assertFalse(self.report['runtime_installed'])

    def test_compiled_faces_keep_actual_partial_caches_matrices_and_render_states(self):
        symbols = self.symbols.decode()
        vertex, vertex_bytes = symbol_span(symbols, 'gor_1_v')
        self.assertEqual(sha256(self.prepared['source'].encode()), self.report['command_source_sha256'])
        for entry in self.report['models']:
            raw = symbol_data(self.rel, symbols, entry['symbol'])
            donor = faces(raw, donor=True, vertex_start=vertex, vertex_bytes=vertex_bytes,
                start=entry['donor_offset'], pointers=data_pointers(self.rel, entry['donor_offset'], len(raw)))
            start = entry['native_offset']
            native = self.model[start:start+entry['native_bytes']]
            actual = faces(native, donor=False, vertex_bytes=vertex_bytes)
            self.assertEqual([t for t, _ in actual], [t for t, _ in donor])
            self.assertEqual(sha256(native), entry['native_sha256'])
            states = list(struct.iter_unpack('>II', native))
            self.assertEqual(states[0], (0xE7000000, 0))
            for command in ((0xD7000002, 0xFFFFFFFF), (0xE200001C, 0xC8112078),
                            (0xFC127E60, 0xFFFFF3F8), (0xFA000080, 0xFFFFFFFF),
                            (0xD9000000, 0x230405)):
                self.assertEqual(states.count(command), 1)
            self.assertFalse({a >> 24 for a, _ in states} & {0xFD, 0xD2, 0x0A})
            tiles = [(a, b) for a, b in states if a >> 24 == 0xF5]
            extents = [(a, b) for a, b in states if a >> 24 == 0xF2]
            self.assertEqual(len(tiles), len(entry['materials']))
            self.assertEqual(len(extents), len(tiles))
            for (a, b), (_, extent), material in zip(tiles, extents, entry['materials']):
                native_wrap = {0: 2, 1: 0, 2: 1}
                self.assertEqual((a & 511)*8, material['tmem'])
                self.assertEqual((a >> 9 & 511)*8, material['width']//2)
                self.assertEqual(b >> 20 & 15, material['palette'])
                self.assertEqual((b >> 8 & 3, b >> 18 & 3), tuple(native_wrap[w] for w in material['wrap']))
                self.assertEqual((b >> 4 & 15, b >> 14 & 15),
                    (material['width'].bit_length()-1, material['height'].bit_length()-1))
                self.assertEqual((extent >> 12 & 4095, extent & 4095), tuple(material['extent']))

    def test_twenty_body_bundle_retains_every_previous_component_and_yodel_dependencies(self):
        bundle = json.loads((BUNDLE/'art.json').read_text())
        self.assertEqual(len(bundle['villagers']), 20)
        self.assertEqual({int(r['id'].split('/')[-1], 16) for r in bundle['villagers']}, set(range(216, 236)))
        previous = ROOT/'build/v3-islander-bodies-01'
        for file in previous.glob('*.bin'):
            self.assertEqual((BUNDLE/file.name).read_bytes(), file.read_bytes())
        row = self.body['villagers'][0]
        self.assertEqual(row, next(r for r in bundle['villagers'] if r['name'] == 'Yodel'))
        for file, content in self.art.items():
            self.assertEqual(content, (BUNDLE/file).read_bytes())
        self.assertEqual(row['accessory']['key'], 'bag1')
        self.assertEqual(row['accessory']['joint'], 13)
        self.assertEqual(row['converted_skeleton'], '06002770')
        self.assertEqual(row['shared_rig']['matched_vertices'], 429)
        self.assertEqual(row['shared_mesh']['ordered_triangles'], 284)
        self.assertEqual(row['shared_mesh']['comparison_model'], 'converted_native_model')
        self.assertFalse(row['selectable'])
        self.assertIsNone(row['target_model_bank'])

    def test_yodel_body_and_expressions_retain_every_actual_source_pixel(self):
        row, layout = self.body['villagers'][0], LAYOUTS['gor']
        texture = self.art[row['texture_file']]
        self.assertEqual(len(texture), 5664)
        source = symbol_data(self.rel, self.symbols.decode(), 'gor_5_tmem_txt')
        for at, target, width, height in layout['parts']:
            part = source[at:at+width*height//2]
            for y in range(height):
                for x in range(width):
                    offset = 0xE20+target+y*width//2+(x//2 ^ (4 if y % 2 else 0))
                    self.assertEqual(texture[offset] >> (0 if x % 2 else 4) & 15,
                                     gx_pixel(part, width, x, y))
        for index, name in enumerate([*(f'eye{i}' for i in range(1, 9)), *(f'mouth{i}' for i in range(1, 7))]):
            part = symbol_data(self.rel, self.symbols.decode(), f'gor_5_{name}_TA_tex_txt')
            for y in range(16):
                for x in range(32):
                    self.assertEqual(texture[32+index*256+y*16+x//2] >> (0 if x % 2 else 4) & 15,
                                     gx_pixel(part, 32, x, y))

    def test_missing_or_corrupted_model_cannot_fall_back_to_native_gorilla(self):
        with self.assertRaisesRegex(ValueError, 'complete converted gorilla'):
            build_art(self.rom, self.rel, self.symbols, villagers=('yodel',), accessory_directory=ACCESSORIES)
        read_bytes = Path.read_bytes
        for target in ('art.json', 'yodel.n64model.bin'):
            def corrupted(path):
                raw = read_bytes(path)
                return raw[:-1]+bytes([raw[-1] ^ 1]) if path.name == target else raw
            with patch.object(Path, 'read_bytes', corrupted):
                with self.assertRaisesRegex(ValueError, 'Gorilla model'):
                    load_object(MODEL, self.rom, self.rel, self.symbols)


if __name__ == '__main__':
    unittest.main()
