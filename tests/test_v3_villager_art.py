"""Verify tile conversion, complete expressions, bounds, and donor pointer binding."""

from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import sha256
from title_assets import pack4, untile
from v3_villager_art import (LAYOUTS, NATIVE_BODY_OFFSET, NATIVE_TEXTURE_SIZE,
                             build_art, convert_texture, data_pointers, native_palette,
                             normalise_vertex_flags, symbol_span, texture_body_offset, tmem_rows)


def source_texture():
    palette = struct.pack('>16H', *(0x8000 | i * 0x421 for i in range(16)))
    eyes = [bytes([i * 17]) * 256 for i in range(8)]
    mouths = [bytes([(i + 8) * 17]) * 256 for i in range(6)]
    body = bytes(range(256)) * 4
    return palette, eyes, mouths, body


def fake_rel(records):
    data = bytearray(0x280)
    struct.pack_into('>I', data, 0, 1)
    struct.pack_into('>II', data, 12, 6, 0x48)
    struct.pack_into('>II', data, 0x48 + 5 * 8, 0x100, 0x80)
    struct.pack_into('>II', data, 0x28, 0x80, 8)
    struct.pack_into('>II', data, 0x80, 1, 0x180)
    for i, record in enumerate(records):
        struct.pack_into('>HBBI', data, 0x180 + i * 8, *record)
    return data


class V3VillagerArtTests(unittest.TestCase):
    def test_palette_preserves_opaque_rgb555_and_rejects_partial_alpha(self):
        palette = source_texture()[0]
        expected = b''.join(struct.pack('>H', ((v & 0x7FFF) << 1) | 1)
                            for (v,) in struct.iter_unpack('>H', palette))
        self.assertEqual(native_palette(palette), expected)
        self.assertEqual(native_palette(bytes(32)), bytes(32))
        with self.assertRaisesRegex(ValueError, 'Partial-alpha'):
            native_palette(b'\x30\x00' * 16)
        with self.assertRaises(ValueError):
            native_palette(palette[:-1])

    def test_tmem_swaps_odd_rows_without_crossing_tile_boundaries(self):
        data = bytes(range(32))
        expected = data[:8] + data[12:16] + data[8:12] + data[16:24] + data[28:32] + data[24:28]
        self.assertEqual(tmem_rows(data, 16, 4), expected)
        self.assertEqual(tmem_rows(tmem_rows(data, 16, 4), 16, 4), data)
        for width, height in ((8, 8), (0, 1), (16, 0), (16, 3)):
            with self.assertRaises(ValueError):
                tmem_rows(data, width, height)

    def test_complete_species_objects_keep_frame_order_and_all_pixels(self):
        palette, eyes, mouths, body = source_texture()
        for species, layout in LAYOUTS.items():
            with self.subTest(species=species):
                selected_mouths = mouths[:layout.get('mouth_frames', 6)]
                texture, parts = convert_texture(palette, eyes, selected_mouths,
                                                  body[:layout.get('body_bytes', len(body))], layout)
                body_offset = texture_body_offset(layout)
                self.assertEqual(len(texture), body_offset+2048)
                first = mouths[0] if layout.get('mouth_first') else eyes[0]
                self.assertEqual(texture[32:288], first)
                atlas = texture[body_offset:]
                self.assertEqual(atlas[layout['cloth']:layout['cloth'] + 512], bytes(512))
                for at, count in layout.get('zero_padding', ()):
                    self.assertEqual(atlas[at:at+count], bytes(count))
                frames = [(eyes[0], layout['eye'])]
                if selected_mouths:
                    frames.append((mouths[0], layout['mouth']))
                for frame, at in frames:
                    self.assertEqual(atlas[at:at + 256], tmem_rows(frame, 32, 16))
                for part in parts:
                    at, source, width, height = (part[key] for key in ('tmem_offset', 'source_offset', 'width', 'height'))
                    count = width * height // 2
                    row_major = tmem_rows(atlas[at:at + count], width, height)
                    self.assertEqual(row_major, pack4(untile(body[source:source + count], width, height, 4)))

    def test_refuse_missing_frames_and_unaccounted_or_overlapping_pieces(self):
        source = list(source_texture())
        source[1] = source[1][:-1]
        with self.assertRaisesRegex(ValueError, 'eight eyes'):
            convert_texture(*source, LAYOUTS['cat'])
        for change in ('overlap', 'missing', 'outside'):
            layout = deepcopy(LAYOUTS['cat'])
            if change == 'overlap':
                layout['parts'] += (layout['parts'][0],)
            elif change == 'missing':
                layout['parts'] = layout['parts'][:-1]
            else:
                layout['eye'] = 2048
            with self.assertRaises(ValueError):
                convert_texture(*source_texture(), layout)

    def test_actual_rel_records_resolve_only_in_scope(self):
        rel = fake_rel([(0, 202, 5, 0), (4, 1, 5, 0x20), (4, 1, 5, 0x24), (0, 203, 0, 0)])
        self.assertEqual(data_pointers(rel, 4, 4), {4: 0x20})
        self.assertEqual(data_pointers(rel, 4, 8), {4: 0x20, 8: 0x24})

    def test_relocations_reject_external_duplicate_nonzero_and_outside_targets(self):
        for records in (
                [(0, 202, 5, 0), (4, 1, 5, 0x20), (0, 1, 5, 0x24), (0, 203, 0, 0)],
                [(0, 202, 5, 0), (4, 1, 5, 0x80), (0, 203, 0, 0)],
                [(0, 202, 5, 0), (4, 1, 4, 0x20), (0, 203, 0, 0)],
                [(4, 1, 5, 0x20), (0, 203, 0, 0)]):
            with self.assertRaises(ValueError):
                data_pointers(fake_rel(records), 4, 8)
        good = fake_rel([(0, 202, 5, 0), (4, 1, 5, 0x20), (0, 203, 0, 0)])
        for at in (0x83, 0x104):
            rel = bytearray(good)
            rel[at] = 7
            with self.assertRaises(ValueError):
                data_pointers(rel, 4, 8)

    def test_symbol_identity_is_unique_and_exact(self):
        symbol = 'fixture = .data:0x00000100; // type:object size:0x20 scope:global\n'
        self.assertEqual(symbol_span(symbol, 'fixture'), (256, 32))
        for symbols, name in ((symbol * 2, 'fixture'), (symbol, 'fixtur')):
            with self.assertRaises(ValueError):
                symbol_span(symbols, name)

    def test_vertex_conversion_changes_only_recognised_matrix_flags(self):
        vertices = bytearray(range(32))
        vertices[6:8], vertices[22:24] = b'\0\1', b'\0\0'
        expected = bytearray(vertices)
        expected[6:8] = b'\0\0'
        self.assertEqual(normalise_vertex_flags(vertices), (bytes(expected), 1))
        vertices[7] = 2
        with self.assertRaisesRegex(ValueError, 'matrix flag'):
            normalise_vertex_flags(vertices)
        with self.assertRaises(ValueError):
            normalise_vertex_flags(bytes(15))


class V3VillagerArtLocalTests(unittest.TestCase):
    @unittest.skipUnless((ROOT / 'build/v3-villager-art-02/art.json').exists(), 'Local art batch is not built')
    def test_actual_donor_conversion_recreates_both_artifacts_and_shared_native_reference(self):
        artifacts, report = build_art(
            (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual(set(artifacts), {'punchy.n64tex.bin', 'cheri.n64tex.bin'})
        self.assertEqual(report['shared_bob_roundtrip']['matched_bytes'], 5152)
        for row in report['villagers']:
            expected = artifacts[row['texture_file']]
            self.assertEqual((ROOT / 'build/v3-villager-art-02' / row['texture_file']).read_bytes(), expected)
            self.assertEqual(row['texture_sha256'], sha256(expected))
            self.assertFalse(row['selectable'])
            self.assertEqual(row['shared_rig']['matched_joints'], 26)
            self.assertEqual(row['shared_rig']['matched_vertices'], 323 if row['name'] == 'Punchy' else 346)


if __name__ == '__main__':
    unittest.main()
