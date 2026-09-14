"""Pigleg/Dobie component conversion without enabling a roster or replacing art."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256
from gc_names import symbol_data
from v3_villager_art import (LAYOUTS, build_art, convert_texture, native_species,
                             normalise_vertex_flags, texture_body_offset)
from tests.test_v3_villager_art import source_texture

OUTPUT = ROOT/'build/v3-islander-art-01'


class IslanderTextureBounds(unittest.TestCase):
    def test_distinct_body_sizes_mouth_frames_and_padding_are_required(self):
        palette, eyes, mouths, body = source_texture()
        with self.assertRaisesRegex(ValueError, 'body texture size'):
            convert_texture(palette, eyes, mouths, body, LAYOUTS['pig'])
        with self.assertRaisesRegex(ValueError, 'mouth frames'):
            convert_texture(palette, eyes, mouths, body, LAYOUTS['wol'])
        layout = {**LAYOUTS['wol'], 'zero_padding': ((0x600, 256),)}
        with self.assertRaisesRegex(ValueError, 'Overlapping'):
            convert_texture(palette, eyes, [], body, layout)
        self.assertEqual(texture_body_offset(LAYOUTS['wol']), 0x820)
        self.assertEqual(texture_body_offset(LAYOUTS['pig']), 0xE20)


@unittest.skipUnless((OUTPUT/'art.json').exists(), 'Local islander artwork required')
class IslanderActualSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.art, cls.report = build_art(cls.rom, cls.rel, cls.symbols,
                                        villagers=('dobie', 'pigleg', 'cheri', 'punchy'))

    def test_complete_outputs_and_pilot_retention(self):
        self.assertEqual(set(self.art), {'punchy.n64tex.bin', 'cheri.n64tex.bin',
            'pigleg.n64tex.bin', 'pigleg.n64model.bin', 'dobie.n64tex.bin'})
        for name, content in self.art.items():
            self.assertEqual(content, (OUTPUT/name).read_bytes())
        for name in ('punchy.n64tex.bin', 'cheri.n64tex.bin'):
            self.assertEqual(self.art[name], (ROOT/'build/v3-villager-art-02'/name).read_bytes())
        self.assertEqual(self.report['shared_pig_roundtrip']['matched_bytes'], 5152)
        self.assertEqual(self.report['shared_wol_roundtrip']['matched_bytes'], 3616)
        self.assertFalse(self.report['installed'])
        self.assertTrue(all(not r['selectable'] for r in self.report['villagers']))

    def test_pigleg_imports_actual_head_coordinates_without_other_model_changes(self):
        row = next(r for r in self.report['villagers'] if r['name'] == 'Pigleg')
        native = by_vrom(self.rom)[int(row['native_model_vrom'], 16)].extract(self.rom)
        result = self.art[row['model_file']]
        vertices, _ = normalise_vertex_flags(symbol_data(self.rel, self.symbols.decode(), 'pig_1_v'))
        self.assertEqual(len(result), len(native))
        self.assertEqual(result[:len(vertices)], vertices)
        self.assertEqual(result[len(vertices):], native[len(vertices):])
        changed = []
        for at in range(0, len(vertices), 16):
            self.assertEqual(result[at+6:at+16], native[at+6:at+16])
            if result[at:at+6] != native[at:at+6]:
                changed.append(at//16)
        self.assertEqual(changed, list(range(67)))
        self.assertEqual(row['shared_rig']['matched_vertices'], 319)
        self.assertEqual(row['shared_rig']['matched_joints'], 26)
        self.assertEqual(row['shared_rig']['comparison_model'], 'converted_native_model')
        self.assertEqual(row['model_sha256'], sha256(result))
        self.assertIsNone(row['target_model_bank'])

    def test_dobie_keeps_native_mouthless_layout_and_rig(self):
        row = next(r for r in self.report['villagers'] if r['name'] == 'Dobie')
        native_row, _, _ = native_species(self.rom, 'wol')
        self.assertEqual(native_row[48:72], bytes(24))
        self.assertEqual(struct.unpack_from('>I', native_row, 8)[0], 0x06000820)
        self.assertEqual(len(self.art[row['texture_file']]), 4128)
        self.assertEqual(row['expression_frames'], {'eye': 8, 'mouth': 0})
        self.assertEqual(row['shared_rig']['matched_vertices'], 374)
        self.assertEqual(row['shared_rig']['matched_joints'], 26)
        self.assertNotIn('model_file', row)
        self.assertEqual(self.art[row['texture_file']][-256:], bytes(256))


if __name__ == '__main__':
    unittest.main()
