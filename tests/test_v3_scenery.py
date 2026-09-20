"""Complete seasonal scenery conversion and explicit inherited render state."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
import v3_furniture_pipeline as pipeline
import v3_scenery as scenery
import tests.test_v3_furniture_pipeline as furniture_checks

OUTPUT = ROOT/os.environ.get('V3_SCENERY_ART', 'build/v3-scenery-gold-tree-01')


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.inventory = scenery.discover(cls.source)

    def test_complete_seasons_states_parts_shadows_and_deduplication(self):
        report = self.inventory
        self.assertEqual(report['counts'], dict(seasons=4, foreground_ids=14,
                                               descriptors=40, model_pairs=37, object_bytes=65632))
        self.assertEqual(len(report['bindings']), 56)
        expected = {f'{i:04X}' for i in (*range(0x7B, 0x82), *range(0x863, 0x86A))}
        for season in scenery.SEASONS:
            self.assertEqual({r['foreground_id'] for r in report['bindings'] if r['season']==season}, expected)
        self.assertEqual(sum(len(r['body']) for r in report['descriptors']), 52)
        self.assertEqual(sum(r['shadow'] is not None for r in report['descriptors']), 24)
        self.assertEqual(sum('external_vertices' in r['render_context'] for r in report['objects']), 6)
        pairs = {r['key'] for r in report['objects']}; used = set()
        for row in report['descriptors']:
            for draw in row['body'] + ([row['shadow']['draw']] if row['shadow'] else []):
                used.add(draw['object'])
        self.assertEqual(used, pairs)
        self.assertFalse(report['runtime_installed']); self.assertFalse(report['selectable'])
        self.assertEqual(report['logical_imports_added'], 0)

    def test_inherited_context_is_explicit_and_cannot_hide_missing_resources(self):
        body = next(r for r in self.inventory['objects'] if 'palette_slot' in r['render_context'])
        shadow = next(r for r in self.inventory['objects'] if 'external_vertices' in r['render_context'])
        for row in (body, shadow):
            with self.assertRaises(ValueError): pipeline.prepare_material_pair(self.source, row['models'])
        for slot in (-1, 16, True, 7, None):
            with self.subTest(slot=slot), self.assertRaises(ValueError):
                pipeline.prepare_material_pair(self.source, body['models'], render_context={'palette_slot':slot})
        external = shadow['render_context']['external_vertices']
        for vertices in ((external[0], external[1], 48), ('wrong', external[1], external[2])):
            with self.assertRaisesRegex(ValueError, 'inherited vertex'):
                pipeline.prepare_material_pair(self.source, shadow['models'], render_context={'external_vertices':vertices})
        with self.assertRaisesRegex(ValueError, 'overwrites its inherited vertex'):
            pipeline.prepare_material_pair(self.source, body['models'],
                render_context=dict(palette_slot=8, external_vertices=external))
        with self.assertRaisesRegex(ValueError, 'Unused or conflicting'):
            pipeline.prepare_material_pair(self.source, shadow['models'],
                render_context=dict(shadow['render_context'], palette_slot=8))
        with self.assertRaisesRegex(ValueError, 'Unknown inherited'):
            pipeline.prepare_material_pair(self.source, body['models'], render_context={'ignore_missing':True})

    def test_changed_consumers_callbacks_shadow_dependencies_and_palette_reject(self):
        source = copy.copy(self.source); source.rel = bytearray(source.rel)
        function = self.inventory['functions']['bg_item_common_s_draw_loop_type1'][0]
        source.rel[source.sections[1][0]+function['offset']] ^= 1
        with self.assertRaisesRegex(ValueError, 'complete scenery consumer'): scenery.discover(source)
        descriptor = next(r for r in self.inventory['descriptors'] if r['shadow'])
        source = copy.copy(self.source); source.relocations = dict(source.relocations)
        source.relocations[descriptor['shadow']['draw']['donor_offset']] = (1, True, 1, 0)
        with self.assertRaisesRegex(ValueError, 'drawing callback'): scenery.discover(source)
        for offset in (descriptor['descriptor']['donor_offset']+15,
                       descriptor['shadow']['fix']['donor_offset'],
                       self.inventory['palettes']['bank']['donor_offset'],
                       self.inventory['palettes']['selector']['donor_offset']):
            source = copy.copy(self.source); source.data = bytearray(source.data)
            source.data[offset] ^= 0x80
            with self.subTest(offset=offset), self.assertRaises(ValueError): scenery.discover(source)
        with tempfile.TemporaryDirectory(prefix='v3-scenery-rejected-') as temp:
            output = Path(temp)/'uncreated'
            with self.assertRaisesRegex(ValueError, 'not selectable'):
                scenery.convert(self.source, output, ['223B'])
            self.assertFalse(output.exists())
            with self.assertRaisesRegex(ValueError, 'Unsupported scenery'):
                scenery.convert(self.source, output, category='unknown')
            self.assertFalse(output.exists())


@unittest.skipUnless((OUTPUT/'art.json').is_file(), 'Prepared scenery artwork required')
class ArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.report = json.loads((OUTPUT/'art.json').read_bytes())

    def test_every_pixel_vertex_triangle_and_native_material_against_donor(self):
        report = self.report
        self.assertEqual(report['format'], 'AFV3-SCENERY-PREPARED-ASSETS-1')
        self.assertEqual(json.loads((OUTPUT/'inventory.json').read_bytes()),
                         json.loads(json.dumps(scenery.discover(self.source))))
        rows = [dict(r, models=r['compiled_models']) for r in report['objects']]
        furniture_checks.DonorTests.check_complete_artwork(self, OUTPUT, dict(objects=rows), prepare=lambda row:
            pipeline.prepare_material_pair(self.source,
                [tuple(row['profile']['models'][k]) for k in ('material', 'geometry')],
                render_context=row['render_context']))
        for row in rows:
            asset = (OUTPUT/row['object_file']).read_bytes()
            models = {m['layer']:m for m in row['compiled_models']}
            material, geometry = models['material'], models['geometry']
            shadow = 'external_vertices' in row['render_context']
            self.assertEqual(asset[geometry['native_offset']], 6 if shadow else 1)
            words = list(struct.iter_unpack('>II', asset[material['native_offset']:
                                                        material['native_offset']+material['bytes']]))
            self.assertFalse(any(a>>24 == 0xF0 for a,b in words))
            self.assertEqual([b>>20&15 for a,b in words if a>>24==0xF5 and b>>24&7==0],
                             [0 if shadow else 8])

    def test_all_palette_colours_and_term_mapping(self):
        palette = self.report['palettes']; native = (OUTPUT/palette['object_file']).read_bytes()
        bank = palette['bank']; start, n = bank['donor_offset'], bank['bytes']
        self.assertEqual(n, 448); self.assertEqual(len(native), n)
        self.assertEqual(sha256(native), palette['output_sha256'])
        donor = self.source.data[start:start+n]
        for index, (value,) in enumerate(struct.iter_unpack('>H', donor)):
            if value&0x8000: expected = (value&0x7FFF)<<1|1
            else:
                self.assertIn(value>>12, (0,7))
                r,g,b = ((value>>shift&15)*17>>3 for shift in (8,4,0))
                expected = r<<11|g<<6|b<<1|bool(value>>12)
            self.assertEqual(struct.unpack_from('>H', native, index*2)[0], expected)
        self.assertEqual(palette['term_indices'], [10,12,13,0,1,2,2,3,3,4,5,6,7,8,9,10,11,10])
        self.assertEqual(palette['palette_slot'], 8)

    def test_prepared_dependencies_cannot_install_as_furniture_or_equipment(self):
        import v3_furniture_install as furniture
        import v3_equipment_runtime as held
        with self.assertRaisesRegex(ValueError, 'Unknown converter/source revision'):
            furniture.checked_assets(OUTPUT, self.source, ROOT/'build/item-identity-megasheet.xlsx')
        with self.assertRaisesRegex(ValueError, 'Changed handheld artwork source/format'):
            held.prepared_resources(self.source, OUTPUT)


if __name__ == '__main__': unittest.main()
