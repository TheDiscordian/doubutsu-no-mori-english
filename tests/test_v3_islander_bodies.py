"""Source-complete body layouts with required accessories and native mesh bindings."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from gc_names import symbol_data
from v3_accessory_art import load_objects
from v3_villager_art import (ARTWORK_VILLAGERS, LAYOUTS, build_art, convert_texture,
                             native_body_piece, texture_body_offset)
from v3_villager_mesh import faces
from tests.test_v3_villager_art import source_body, source_texture

OUTPUT = ROOT/'build/v3-islander-bodies-01'
ACCESSORIES = ROOT/'build/v3-accessory-art-03'


def gx_pixel(raw, width, x, y):
    at = ((y//8)*(width//8)+x//8)*32+(y % 8)*4+(x % 8)//2
    return raw[at] >> (0 if x % 2 else 4) & 15


class BodyLayoutSafety(unittest.TestCase):
    def test_edge_rows_are_reconstructed_not_silently_dropped(self):
        for species, layout in LAYOUTS.items():
            body = source_body(layout)
            for offset, (height, mode) in layout.get('edge_rows', {}).items():
                source, _, width, donor_height = next(p for p in layout['parts'] if p[0] == offset)
                piece, actual_height = native_body_piece(body, source, width, donor_height, layout)
                self.assertEqual(actual_height, height)
                self.assertEqual(len(piece), width*height//2)
                changed = bytearray(body)
                # First repeated row, first pixel; top/original rows remain intact.
                at = source+(height//8)*(width//8)*32+(height % 8)*4
                changed[at] ^= 0x10
                with self.subTest(species=species, offset=source, mode=mode):
                    with self.assertRaisesRegex(ValueError, 'unique pixels'):
                        native_body_piece(changed, source, width, donor_height, layout)
        layout = deepcopy(LAYOUTS['lon'])
        layout['edge_rows'][0x300] = (4, 'discard')
        with self.assertRaisesRegex(ValueError, 'Unsupported donor edge'):
            native_body_piece(source_body(LAYOUTS['lon']), 0x300, 32, 8, layout)

    def test_partial_vertex_cache_retains_joint_matrices_and_rejects_unloaded_faces(self):
        commands = [(0xF5400200, 0x00F10040), (0xF2000000, 0x3C03C),
                    (0xDA380003, 0x0D000040), (0x01002004, 0x06000000),
                    (0xDA380003, 0x0D000080), (0x01001006, 0x06000020),
                    (0x05000204, 0), (0xDF000000, 0)]
        raw = b''.join(struct.pack('>II', *words) for words in commands)
        actual = faces(raw, donor=False, vertex_bytes=48)
        self.assertEqual(actual[0][0], ((0, 0x0D000040), (1, 0x0D000040), (2, 0x0D000080)))
        for at, word in ((48, 0x05000206), (40, 0x01021042), (56, 0x00000000)):
            changed = bytearray(raw)
            struct.pack_into('>I', changed, at, word)
            with self.assertRaises(ValueError):
                faces(changed, donor=False, vertex_bytes=48)


@unittest.skipUnless((OUTPUT/'art.json').exists(), 'Complete body component batch required')
class ActualIslanderBodies(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.art, cls.report = build_art(cls.rom, cls.rel, cls.symbols,
            villagers=tuple(ARTWORK_VILLAGERS), accessory_directory=ACCESSORIES)

    def test_nineteen_bodies_keep_fifteen_required_accessories_and_existing_pilots(self):
        self.assertEqual(len(self.report['villagers']), 19)
        self.assertEqual({int(r['id'].split('/')[-1], 16) for r in self.report['villagers']},
                         set(range(216, 236))-{229})
        self.assertEqual(len(self.art), 35)
        self.assertEqual(sum('accessory' in r for r in self.report['villagers']), 15)
        for file, data in self.art.items():
            self.assertEqual(data, (OUTPUT/file).read_bytes())
        for row in self.report['villagers']:
            self.assertFalse(row['selectable'])
            if 'accessory' in row:
                dependency = row['accessory']
                self.assertFalse(dependency['runtime_attached'])
                self.assertEqual(sha256(self.art[dependency['object_file']]), dependency['object_sha256'])
                self.assertEqual(dependency['donor_villager_index'], int(row['id'].split('/')[-1], 16))
                self.assertEqual(row['shared_mesh']['visible_joints'], row['shared_rig']['shown_joints'])
                self.assertTrue(row['shared_mesh']['vertex_indices_and_joint_matrices_match'])
        for key in ('punchy', 'cheri', 'pigleg', 'dobie'):
            file = key+'.n64tex.bin'
            self.assertEqual(self.art[file], (ROOT/'build/v3-islander-art-02'/file).read_bytes())
        self.assertFalse(self.report['installed'])

    def test_every_source_body_pixel_survives_or_is_an_exact_declared_edge_repeat(self):
        checked = 0
        for row in self.report['villagers']:
            layout = LAYOUTS[row['species']]
            source = symbol_data(self.rel, self.symbols.decode(), row['donor_texture_prefix']+'_tmem_txt')
            body_at = texture_body_offset(layout)
            native = self.art[row['texture_file']][body_at:]
            covered = set()
            for part in row['body_parts']:
                offset, target, width, height = (part[k] for k in ('source_offset', 'tmem_offset', 'width', 'height'))
                native_height = part.get('native_height', height)
                tile = source[offset:offset+width*height//2]
                covered.update(range(offset, offset+len(tile)))
                for y in range(height):
                    ny = y if y < native_height else native_height-1-(
                        y-native_height if part['verified_edge_mode'] == 'mirror' else 0)
                    for x in range(width):
                        address = target+ny*(width//2)+(x//2 ^ (4 if ny % 2 else 0))
                        actual = native[address] >> (0 if x % 2 else 4) & 15
                        self.assertEqual(actual, gx_pixel(tile, width, x, y), (row['name'], offset, x, y))
                        checked += 1
            self.assertEqual(len(covered), len(source))
        self.assertGreater(checked, 40000)

    def test_all_actual_expression_frames_and_palette_colours_keep_native_order(self):
        for row in self.report['villagers']:
            layout, prefix = LAYOUTS[row['species']], row['donor_texture_prefix']
            texture = self.art[row['texture_file']]
            eyes = [f'eye{i}' for i in range(1, 9)]
            mouths = [f'mouth{i}' for i in range(1, layout.get('mouth_frames', 6)+1)]
            frames = mouths+eyes if layout.get('mouth_first') else eyes+mouths
            for index, frame in enumerate(frames):
                source = symbol_data(self.rel, self.symbols.decode(), prefix+'_'+frame+'_TA_tex_txt')
                for y in range(16):
                    for x in range(32):
                        pixel = texture[32+index*256+y*16+x//2] >> (0 if x % 2 else 4) & 15
                        self.assertEqual(pixel, gx_pixel(source, 32, x, y))
            palette = symbol_data(self.rel, self.symbols.decode(), prefix+'_pal')
            for (gc,), (native,) in zip(struct.iter_unpack('>H', palette), struct.iter_unpack('>H', texture[:32])):
                if gc & 0x8000:
                    expected = (gc & 0x7FFF)*2+1
                else:
                    self.assertIn(gc >> 12, (0, 7))
                    r, g, b = (((gc >> shift & 15)*17) >> 3 for shift in (8, 4, 0))
                    expected = r << 11 | g << 6 | b << 1 | (gc >> 12 == 7)
                self.assertEqual(native, expected)

    def test_missing_wrong_or_corrupted_accessories_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'accessory needs'):
            build_art(self.rom, self.rel, self.symbols, villagers=('ankha',))
        read_bytes = Path.read_bytes
        for target in ('art.json', 'anrium1.n64obj.bin'):
            def corrupted(path):
                raw = read_bytes(path)
                return raw[:-1]+bytes([raw[-1] ^ 1]) if path.name == target else raw
            with patch.object(Path, 'read_bytes', corrupted):
                with self.assertRaisesRegex(ValueError, 'Accessory dependency'):
                    load_objects(ACCESSORIES, self.rel, self.symbols)


if __name__ == '__main__':
    unittest.main()
