"""Complete source category relationships and split material/geometry artwork."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
import v3_item_categories as category
import v3_furniture_pipeline as pipeline
import tests.test_v3_furniture_pipeline as furniture_checks

OUTPUT=ROOT/os.environ.get('V3_ITEM_CATEGORY_ART','build/v3-item-category-art-02')


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.inventory=category.discover(cls.source)

    def test_all_extra_parent_records_share_source_categories_across_six_owners(self):
        report=self.inventory
        self.assertEqual((report['category_count'],report['parent_record_count']),(9,43))
        self.assertEqual([r['source_category'] for r in report['rows']],[19,33,37,38,39,40,41,42,43])
        self.assertEqual(len(report['tables']),4)
        parents=set()
        for row in report['rows']:
            self.assertEqual([g['category_base'] for g in row['ground_descriptors']],[68,68,68,70])
            self.assertEqual((row['vertices'],row['triangles'],row['object_bytes']),(4,2,816))
            self.assertTrue(row['asset_ready']);self.assertFalse(row['selectable'])
            self.assertFalse(row['runtime_installed'])
            for item in row['parent_item_ids']:
                self.assertNotIn(item,parents);parents.add(item)
            for parent in row['parents']:
                at=parent['name_source_index']*16
                self.assertEqual(sha256(self.source.raw(parent['name_source_symbol'])[at:at+16]),parent['name_sha256'])
        self.assertFalse(report['native_tables_installed']);self.assertEqual(report['logical_imports_added'],0)

    def test_changed_consumers_and_category_bindings_reject(self):
        for at,n,_ in category.FUNCTIONS:
            source=copy.copy(self.source);source.rel=bytearray(self.source.rel)
            source.rel[source.sections[1][0]+at+n-1]^=1
            with self.assertRaisesRegex(ValueError,'complete category consumer'):category.discover(source)
        source=copy.copy(self.source);source.relocations=dict(self.source.relocations)
        at=source.symbol('item1_tableNo$430')[0]+8
        source.relocations[at]=(1,True,5,0)
        with self.assertRaisesRegex(ValueError,'category binding'):category.discover(source)
        source=copy.copy(self.source);source.relocations=dict(self.source.relocations)
        table=self.inventory['tables'][0];at=table['offset']+43*4
        source.relocations[at]=source.relocations[table['offset']+19*4]
        with self.assertRaisesRegex(ValueError,'artwork disagrees'):category.discover(source)

    def test_extra_shadows_callbacks_and_bad_selections_are_not_silently_dropped(self):
        row=self.inventory['rows'][-1];ground=row['ground_descriptors'][0]
        source=copy.copy(self.source);source.data=bytearray(self.source.data)
        source.data[ground['part_offset']+15]=1
        with self.assertRaisesRegex(ValueError,'shadow dependencies'):category.discover(source)
        source=copy.copy(self.source);source.relocations=dict(self.source.relocations)
        source.relocations[ground['list_offset']]=(1,True,1,0)
        with self.assertRaisesRegex(ValueError,'drawing callback'):category.discover(source)
        with tempfile.TemporaryDirectory(prefix='v3-category-selection-') as temp:
            path=Path(temp)/'uncreated'
            with self.assertRaisesRegex(ValueError,'Unknown or original-only'):
                category.convert(self.source,path,['2200'])
            self.assertFalse(path.exists())
        with self.assertRaisesRegex(ValueError,'exactly two'):
            pipeline.prepare_material_pair(self.source,row['models'][:1])
        with self.assertRaises(ValueError):
            pipeline.prepare_material_pair(self.source,list(reversed(row['models'])))


@unittest.skipUnless((OUTPUT/'art.json').is_file(),'Prepared current category artwork required')
class ArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.report=json.loads((OUTPUT/'art.json').read_bytes())

    def test_complete_pixels_colours_vertices_commands_and_independent_split_lists(self):
        self.assertEqual(self.report['format'],'AFV3-ITEM-CATEGORY-PREPARED-ASSETS-1')
        self.assertFalse(self.report['runtime_installed']);self.assertFalse(self.report['selectable'])
        self.assertEqual(json.loads((OUTPUT/'inventory.json').read_bytes()),
                         json.loads(json.dumps(category.discover(self.source))))
        rows=[dict(r,models=r['compiled_models']) for r in self.report['objects']]
        furniture_checks.DonorTests.check_complete_artwork(self,OUTPUT,dict(objects=rows),
            prepare=lambda row:pipeline.prepare_material_pair(self.source,
                [tuple(row['profile']['models'][k]) for k in ('material','geometry')]))
        self.assertEqual(len(rows),9)
        self.assertEqual(sum(r['object_bytes'] for r in rows),7344)
        for row in rows:
            data=(OUTPUT/row['object_file']).read_bytes()
            self.assertEqual(set(row['model_offsets']),{'geometry','material'})
            geometry=next(m for m in row['models'] if m['layer']=='geometry')
            material=next(m for m in row['models'] if m['layer']=='material')
            self.assertEqual(data[geometry['native_offset']],1)
            self.assertEqual(geometry['triangles'],2);self.assertEqual(material['triangles'],0)
            self.assertEqual((geometry['bytes'],material['bytes']),(24,184))
            for resource in row['resources']:
                if resource['kind']!='palette':continue
                at=resource['donor_offset'];out=resource['native_offset']
                for index in range(16):
                    value=struct.unpack_from('>H',self.source.data,at+index*2)[0]
                    if value&0x8000:expected=((value&32767)<<1)|1
                    else:
                        self.assertIn(value>>12,(0,7))
                        red,green,blue=((value>>shift&15)*17>>3 for shift in (8,4,0))
                        expected=red<<11|green<<6|blue<<1|bool(value>>12)
                    self.assertEqual(struct.unpack_from('>H',data,out+index*2)[0],expected)

    def test_split_output_retains_the_complete_shared_model_conversion(self):
        row=self.report['objects'][-1];parts=[tuple(row['profile']['models'][k]) for k in ('material','geometry')]
        descriptor=dict(models={'opaque':parts[0]},callback_adapter=dict(
            category='indexed-model-sequence',model_sequences={'opaque':parts}))
        prepared=pipeline.prepare_models(self.source,descriptor)
        with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='v3-category-full-') as temp:
            full,offsets,models,_=pipeline.compile_models(Path(temp),prepared)
        asset=(OUTPUT/row['object_file']).read_bytes()
        material,geometry=row['compiled_models']
        combined=(asset[material['native_offset']:material['native_offset']+material['bytes']-8]+
                  asset[geometry['native_offset']:geometry['native_offset']+geometry['bytes']])
        self.assertEqual(combined,full[offsets['opaque']:offsets['opaque']+models[0]['bytes']])
        self.assertEqual(asset[:material['native_offset']],full[:offsets['opaque']])

    def test_ordinary_installed_model_emission_remains_unchanged(self):
        lock=json.loads((ROOT/'config/v3-import-build.json').read_bytes())
        current=json.loads((ROOT/lock['directory']/'build.json').read_bytes())
        art=ROOT/current['automatic_furniture']['art_directory']
        batch=json.loads((art/'art.json').read_bytes())
        for row in batch['objects']:
            prepared=pipeline.prepare(self.source,int(row['item_id'],16))
            self.assertEqual(prepared[5],(art/row['item_id']/'commands.c').read_text())
        model=dict(rows=[dict(opcode=0xFD)],inherited_material=True)
        with self.assertRaisesRegex(ValueError,'validated geometry'):
            pipeline.command_source({'invalid':model},{})

    def test_prepared_categories_cannot_enter_furniture_or_held_resource_installers(self):
        import v3_furniture_install as furniture
        import v3_equipment_runtime as held
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            furniture.checked_assets(OUTPUT,self.source,ROOT/'build/item-identity-megasheet.xlsx')
        with self.assertRaisesRegex(ValueError,'Changed handheld artwork source/format'):
            held.prepared_resources(self.source,OUTPUT)


if __name__=='__main__':unittest.main()
