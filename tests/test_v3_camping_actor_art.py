"""Complete callback-owned camping assets, including both scrolling I4 layers."""
from copy import deepcopy
import json
import struct
import unittest

from tests import test_v3_furniture_art as static
from aflib import sha256
from gc_names import rel_sections
from v3_camping_actor_art import ACTORS, exact_symbol, finish, identity_evidence, prepare
from v3_furniture_art import SEGMENT, command_source, parse_model
from v3_villager_art import data_pointers

OUTPUT = static.ROOT / 'build/v3-camping-actor-art-01'


class CampingActorArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel = (static.ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (static.ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.report = json.loads((OUTPUT / 'art.json').read_bytes())
        cls.prepared = [prepare(cls.rel, cls.symbols, actor) for actor in ACTORS]
        cls.assets = [(OUTPUT / row['object_file']).read_bytes() for row in cls.report['objects']]

    def test_complete_real_arrays_keep_every_texel_palette_entry_and_vertex(self):
        expected = ((8000, 'c9904baeaf1fcaf903daa9cf14cfeecf5a43d355446d8c49f1206f6ff4b0bf2c'),
            (6032, 'aed67322525e5ece8e17c5be59986a82d1269e4d8421f8985adde0128cd6cfb7'),
            (4288, 'b56aeeb6e542e9742706ca510e054fdb81f87a82e91b9ff684ed669d32c14af7'))
        base = rel_sections(self.rel)[5][0]
        for prepared, asset, report, (size, digest) in zip(self.prepared, self.assets,
                self.report['objects'], expected, strict=True):
            body, resources, *_ = prepared
            self.assertEqual(asset[:len(body)], body)
            self.assertEqual(len(asset), size)
            self.assertEqual(sha256(asset), digest)
            self.assertEqual(report['object_sha256'], digest)
            self.assertFalse(report['runtime_installed'])
            self.assertFalse(report['behaviour_installed'])
            self.assertFalse(report['selectable'])
            for row in resources:
                at, size, dst = (row[k] for k in ('donor_offset', 'bytes', 'native_offset'))
                original, native = self.rel[base + at:base + at + size], asset[dst:dst + size]
                self.assertEqual(sha256(original), row['source_sha256'])
                self.assertEqual(sha256(native), row['output_sha256'])
                if row['kind'] == 'rgba16':
                    for (gc,), (n64,) in zip(struct.iter_unpack('>H', original), struct.iter_unpack('>H', native)):
                        if gc & 0x8000:
                            expected = ((gc & 0x7FFF) << 1) | 1
                        else:
                            self.assertIn(gc >> 12, (0, 7))
                            r, g, b = [((gc >> s & 15) * 17) >> 3 for s in (8, 4, 0)]
                            expected = r << 11 | g << 6 | b << 1 | (gc >> 12 == 7)
                        self.assertEqual(n64, expected)
                elif row['kind'] in ('ci4', 'i4'):
                    w, h = row['width'], row['height']
                    for y in range(h):
                        for x in range(w):
                            gx = ((y // 8) * (w // 8) + x // 8) * 64 + (y % 8) * 8 + x % 8
                            n64 = y * w + x
                            self.assertEqual(original[gx // 2] >> (4 if gx % 2 == 0 else 0) & 15,
                                             native[n64 // 2] >> (4 if n64 % 2 == 0 else 0) & 15)
                elif row['kind'] == 'vertices':
                    for at in range(0, size, 16):
                        self.assertEqual(native[at:at + 6] + native[at + 8:at + 16],
                                         original[at:at + 6] + original[at + 8:at + 16])
                        self.assertEqual(native[at + 6:at + 8], bytes(2))
                else:
                    self.assertEqual(original, native)

    def test_all_compiled_faces_loads_colours_extents_and_pointer_bounds(self):
        for prepared, asset, report in zip(self.prepared, self.assets, self.report['objects'], strict=True):
            body, resources, offsets, models, *_ = prepared
            source, sections = command_source(models, offsets)
            self.assertEqual(sha256(source.encode()), report['command_source_sha256'])
            vertex = next(r for r in resources if r['kind'] == 'vertices')
            for model in report['models']:
                rows = models[model['part']]['rows']
                code = asset[model['native_offset']:model['native_offset'] + model['bytes']]
                self.assertEqual(sha256(code), model['output_sha256'])
                self.assertEqual(len(code), dict(sections)[model['part']])
                faces, loads, shapes, state, calls = [], [], [], [], []
                first, count = 0, 0
                for a, b in struct.iter_unpack('>II', code):
                    op = a >> 24
                    self.assertIn(op, (0xE7, 0xE8, 0xE3, 0xD7, 0xFC, 0xE2, 0xFD, 0xF5,
                        0xE6, 0xF0, 0xF3, 0xF2, 0xFA, 0xFB, 0xD9, 0x01, 0x05, 0x06, 0xDE, 0xDF))
                    if op in (0xFC, 0xE2, 0xFA, 0xFB, 0xD9): state.append((a, b))
                    if op == 0xD7: self.assertEqual((a, b), (0xD7000002, 0xFFFFFFFF))
                    if op == 0xFD:
                        self.assertIn(a, (0xFD100000, 0xFD500000, 0xFD900000))
                        if b == 0x08000000:
                            self.assertEqual((report['item_id'], model['part'], a), ('336C', 'light', 0xFD100000))
                        else:
                            self.assertEqual(b >> 24, 6)
                            self.assertIn(b - SEGMENT, offsets.values())
                        loads.append(b)
                    if op == 0xF2: shapes.append(((b >> 12 & 4095) // 4 + 1, (b & 4095) // 4 + 1))
                    if op == 0xDE:
                        self.assertEqual((a, b), (0xDE000000, 0x09000000))
                        self.assertEqual(model['part'], 'flame')
                        calls.append(b)
                    if op == 0x01:
                        self.assertEqual(b >> 24, 6)
                        count = a >> 12 & 255
                        self.assertTrue(1 <= count <= 32)
                        self.assertTrue(vertex['native_offset'] <= b - SEGMENT <=
                                        vertex['native_offset'] + vertex['bytes'] - count * 16)
                        first = (b - SEGMENT - vertex['native_offset']) // 16
                    if op in (0x05, 0x06):
                        for word in ((a, b) if op == 0x06 else (a,)):
                            indices = tuple(word >> shift & 255 for shift in (16, 8, 0))
                            self.assertTrue(all(i % 2 == 0 and i // 2 < count for i in indices))
                            faces.append(tuple(first + i // 2 for i in indices))
                self.assertEqual(faces, [t for row in rows for t in row.get('global_triangles', [])])
                self.assertEqual(len(faces), model['triangles'])
                self.assertEqual(loads, [r['dynamic_palette'] if 'dynamic_palette' in r else
                    SEGMENT + offsets[r['target']] for r in rows if r['opcode'] in (0xF0, 0xFD)])
                self.assertEqual(state, [r['words'] for r in rows if r['opcode'] in (0xFC, 0xE2, 0xFA, 0xFB, 0xD9)])
                self.assertEqual(shapes, [r['shape'] if r['opcode'] == 0xFD else
                    ((r['words'][1] >> 12 & 4095) // 4 + 1, (r['words'][1] & 4095) // 4 + 1)
                    for r in rows if r['opcode'] in (0xFD, 0xF2)])
                self.assertEqual(calls, [0x09000000] if model['part'] == 'flame' else [])

    def test_two_intensity_tiles_have_separate_native_tmem_and_exact_shifts(self):
        for n in (0, 1):
            row, asset = self.report['objects'][n], self.assets[n]
            model = next(m for m in row['models'] if m['part'] == 'flame')
            commands = list(struct.iter_unpack('>II', asset[model['native_offset']:model['native_offset'] + model['bytes']]))
            self.assertIn((0xE3001001, 0), commands)  # Intensity, not palette mode.
            self.assertFalse(any(a >> 24 == 0xF0 for a, b in commands))
            tiles = [(a, b) for a, b in commands if a >> 24 == 0xF5 and b >> 24 & 7 != 7]
            self.assertEqual(len(tiles), 2)
            for tile, (a, b) in enumerate(tiles):
                width, height = ((32, 64), (32, 32) if n == 0 else (64, 32))[tile]
                self.assertEqual((a >> 21 & 7, a >> 19 & 3, a >> 9 & 511, a & 511),
                                 (4, 0, width // 16, tile * 128))
                shifts = (0, 0) if n == 0 else ((1, 1), (2, 0))[tile]
                self.assertEqual((b >> 24 & 7, b >> 8 & 3, b >> 18 & 3,
                                  b >> 4 & 15, b >> 14 & 15, b & 15, b >> 10 & 15),
                                 (tile, 0, 0, width.bit_length() - 1, height.bit_length() - 1, *shifts))
            self.assertEqual([b >> 12 & 4095 for a, b in commands if a >> 24 == 0xF3],
                             [511, 255 if n == 0 else 511])
            self.assertEqual(row['scroll_velocity'], [[0, -6], [0, 0]] if n == 0 else [[0, -3], [-2, 0]])

    def test_all_rig_pointers_null_tracks_constant_pose_and_display_flags(self):
        for prepared, asset, report in zip(self.prepared, self.assets, self.report['objects'], strict=True):
            body, _, offsets, models, rig, _ = prepared
            compiled = {r['part']: asset[r['native_offset']:r['native_offset'] + r['bytes']] for r in report['models']}
            rebuilt, _, headers, pointers = finish(body, offsets, models, rig, compiled)
            self.assertEqual(rebuilt, asset)
            self.assertEqual(len(pointers), 5 if rig else 0)
            for row in pointers:
                self.assertEqual(struct.unpack_from('>I', asset, row['offset'])[0], SEGMENT + row['target_offset'])
                self.assertTrue(0 <= row['target_offset'] < row['offset'] < len(asset))
            for label, header in headers.items():
                at, size = header['native_offset'], header['bytes']
                raw = bytearray(asset[at:at + size])
                for row in pointers:
                    if at <= row['offset'] < at + size:
                        raw[row['offset'] - at:row['offset'] - at + 4] = bytes(4)
                self.assertEqual(raw, rig[label][1])
            if rig:
                at = headers['animation']['native_offset']
                self.assertEqual(asset[at + 4:at + 12], bytes(8))
                self.assertEqual(asset[at + 16:at + 20], struct.pack('>hh', -1, 101))
                self.assertEqual(report['keyframe_tracks'], 0)
                self.assertEqual(report['constant_components'], 12)
                self.assertEqual(report['joints'], 3)
            with self.assertRaises(ValueError): finish(body + bytes(0x2400), offsets, models, rig, compiled)
            with self.assertRaises(ValueError): finish(body, offsets, models, rig, {})

    def test_tent_keeps_all_four_parts_and_both_complete_palette_endpoints(self):
        row, asset = self.report['objects'][2], self.assets[2]
        self.assertEqual([r['part'] for r in row['models']], ['green', 'body', 'detail', 'light'])
        palettes = {r['symbol']: asset[r['native_offset']:r['native_offset'] + r['bytes']]
                    for r in row['resources'] if r['kind'] == 'rgba16'}
        self.assertEqual(palettes['int_tak_tent_pal'], palettes['int_tak_tent_off_pal'])
        on, off = palettes['int_tak_tent_on_pal'], palettes['int_tak_tent_off_pal']
        self.assertEqual([i for i in range(16) if on[i * 2:i * 2 + 2] != off[i * 2:i * 2 + 2]], [7])
        self.assertEqual((on[14:16].hex(), off[14:16].hex()), ('ffe5', '0001'))
        self.assertEqual(row['dynamic_palette_segment'], '08000000')
        self.assertEqual(row['palette_fade_step'], 0.1)
        self.assertEqual(row['interaction_bits'], '8000')
        self.assertEqual([r['symbol'] for r in row['callbacks']], ['fTTnt_ct', 'fTTnt_mv', 'fTTnt_dw', 'fTTnt_dt'])

    def test_actual_metadata_uses_tent_rewards_and_full_bonfire_footprint(self):
        rows = self.report['objects']
        self.assertEqual([r['name'] for r in rows], ['campfire', 'bonfire', 'tent model'])
        self.assertEqual([r['price'] for r in rows], [1360, 2240, 2550])
        self.assertEqual([r['footprint'] for r in rows], ['1x1', '2x2', '1x1'])
        self.assertTrue(all(r['donor_list'] == 'ftr_listTent' and not r['catalogue_orderable'] for r in rows))
        self.assertEqual(rows[1]['donor_profile_scalar_hex'][16:20], '0505')
        self.assertEqual(rows[1]['preview_mode'], 19)
        self.assertEqual(rows[1]['donor_preview_scalar_hex'], '3f5c28f6c0400000')
        self.assertEqual([r['donor_birth_category'] for r in rows], [37] * 3)
        self.assertEqual([r['donor_loop_sound'] for r in rows[:2]], [0x5D, 0x5C])
        self.assertEqual(len(identity_evidence(static.ROOT / 'build/item-identity-megasheet.xlsx')), 3)
        # Shared local-name resources need exact identity, not first-match lookup.
        with self.assertRaises(ValueError): exact_symbol(self.symbols.decode(), 'int_sum_ayu_pal', 32)
        self.assertEqual(exact_symbol(self.symbols.decode(), 'int_sum_ayu_pal', 32, 0x849D60), 0x849D60)

    def test_unreviewed_dynamic_segments_palettes_shifts_and_materials_fail(self):
        # Keep the real source shapes and pointer inventory; perturb only the
        # reviewed graphics command to prove each extra mode remains bounded.
        for actor, prepared in zip(ACTORS, self.prepared, strict=True):
            _, resources, _, models, *_ = prepared
            label = 'light' if actor.item == 0x336C else 'flame'
            model = models[label]
            at = model['donor_offset']
            size = next(n for key, _, n in actor.models if key == label)
            base = rel_sections(self.rel)[5][0]
            raw = self.rel[base + at:base + at + size]
            pointers = data_pointers(self.rel, at, size)
            vertex = next(r for r in resources if r['kind'] == 'vertices')
            textures = {r['donor_offset']: (r['width'], r['height']) for r in resources
                        if r['kind'] == ('ci4' if actor.item == 0x336C else 'i4')}
            mode = {'tent': True} if actor.item == 0x336C else {'fire_effect': 1 if actor.item == 0x335C else 2}
            args = (at, pointers, resources[0]['donor_offset'], textures, vertex['donor_offset'], vertex['bytes'])
            with self.assertRaises(ValueError): parse_model(raw, *args)
            edits = ((0x1C, 0x08000008), (0x28, 0xD2F0FA00)) if actor.item == 0x336C else (
                (0x4C, 0x08000000), (0x40, 0xD2F1F522), (0x0C, 0xFFFFFFFF))
            for offset, word in edits:
                bad = bytearray(raw); struct.pack_into('>I', bad, offset, word)
                with self.assertRaises(ValueError): parse_model(bad, *args, **mode)
            with self.assertRaises(ValueError): parse_model(raw, *args, camping=True, **mode)
        bad = deepcopy(self.prepared[0][3])
        row = next(r for r in bad['flame']['rows'] if 'fire_tile' in r)
        row['fire_tile'] = 3
        with self.assertRaises(ValueError): command_source(bad, self.prepared[0][2])


if __name__ == '__main__':
    unittest.main()
