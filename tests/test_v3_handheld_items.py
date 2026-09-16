"""Complete held-equipment discovery and shared static-art conversion checks."""
from collections import Counter
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from gc_text import decoder_tables
from v3_import_catalog import ITEM_GROUPS,item_rows
import tests.test_v3_furniture_pipeline as furniture_checks
import v3_furniture_pipeline as pipeline
import v3_handheld_items as held

OUTPUT=ROOT/'build/v3-handheld-static-prepared-02'


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.report=held.discover(cls.source)
        cls.rows={r['item_id']:r for r in cls.report['rows']}

    def test_complete_equipment_tables_preserve_categories_and_wear_shapes(self):
        self.assertEqual(len(self.rows),79)
        self.assertEqual(self.report['rejected_item_ids'],[f'{i:04X}' for i in range(0x222C,0x2239)])
        self.assertEqual(Counter(r['category'] for r in self.rows.values()),
                         {'static-held-model':19,'animated-held-model':20,'separate-equipment-owner':40})
        for i in range(8):
            row=self.rows[f'{0x2254+i:04X}']
            self.assertEqual((row['equipment_kind'],row['shape_index'],row['data_type']),(71+i,42+i,0))
            self.assertEqual(row['model_root']['symbol'],f'tol_fan{i+1}_model')
        # Worn axes are one logical parent but retain all three actual shapes.
        self.assertEqual([self.rows[f'{i:04X}']['shape_index'] for i in range(0x223D,0x2244)],
                         [0,1,1,1,2,2,2])
        self.assertEqual(self.rows['223A']['shape_index'],3)
        self.assertEqual(self.rows['223B']['shape_index'],22)
        self.assertTrue(all(not r['selectable'] and not r['runtime_installed'] for r in self.rows.values()))
        self.assertEqual(len({r['shape_index'] for r in self.rows.values() if r.get('data_type')==0}),14)

    def test_changed_complete_selectors_and_invalid_dependencies_reject(self):
        base=self.source.sections[1][0]
        for address,_,size,_,_,_ in held.FUNCTIONS.values():
            for relative in (0,size-1):
                source=copy.copy(self.source);source.rel=bytearray(self.source.rel)
                source.rel[base+address+relative]^=1
                with self.assertRaisesRegex(ValueError,'equipment selector'):held.discover(source)
            source=copy.copy(self.source);source.code_relocations=dict(self.source.code_relocations)
            source.code_relocations[address+0x12]=(6,0,5,0)
            with self.assertRaisesRegex(ValueError,'equipment selector'):held.discover(source)
        for role in ('item_kind','data'):
            at=self.report['tables'][role]['offset']
            for replacement in (None,(1,False,5,0),(1,True,6,0)):
                source=copy.copy(self.source);source.relocations=dict(self.source.relocations)
                if replacement is None:source.relocations.pop(at)
                else:source.relocations[at]=replacement
                with self.assertRaisesRegex(ValueError,'table pointers'):held.discover(source)
        source=copy.copy(self.source);source.rel=bytearray(self.source.rel)
        at=self.source.sections[4][0]+self.report['tables']['shape']['offset']
        source.rel[at]=127
        with self.assertRaisesRegex(ValueError,'escapes resource table'):held.discover(source)

    def test_single_inventory_binds_names_without_enabling_or_duplicating_items(self):
        tables=decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')
        items=[]
        for i,name in enumerate(ITEM_GROUPS):
            items+=item_rows(self.source.raw('itemName_'+name),tables,base=0x2000+i*256,furniture=False)
        before=[r['id'] for r in items]
        held.annotate_inventory(items,self.report);held.annotate_inventory(items,self.report)
        self.assertEqual([r['id'] for r in items],before)
        self.assertEqual(sum('handheld' in r for r in items),79)
        self.assertTrue(all(not r['selectable'] and r['target_item_id'] is None for r in items))
        damaged=copy.deepcopy(items)
        next(r for r in damaged if r['donor_item_id']=='2254')['name_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'complete donor inventory'):
            held.annotate_inventory(damaged,self.report)

    def test_nonstatic_and_unknown_selections_cannot_become_decorative_substitutes(self):
        for row in self.rows.values():
            if row['category']!='static-held-model':
                with self.assertRaises(ValueError):held.descriptor(row)
        with tempfile.TemporaryDirectory(prefix='v3-held-') as temporary:
            output=Path(temporary)/'not-created'
            for selected in (['2200'],['FFFF'],['2254','2244']):
                with self.assertRaisesRegex(ValueError,'Unsupported.*selected'):
                    held.convert(self.source,output,selected)
                self.assertFalse(output.exists())

    def test_cli_refuses_installation_and_ungated_conversion(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='v3-held-cli-') as temporary:
            output=Path(temporary)/'not-created'
            for command in ('import','convert'):
                result=subprocess.run([sys.executable,str(ROOT/'tools/v3_furniture_pipeline.py'),
                    command,'--representation','handheld','--output',str(output)],
                    capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,2)
                self.assertIn('runtime integration is unfinished',result.stderr)
                self.assertFalse(output.exists())

    def test_shape_cannot_select_an_animation_resource(self):
        source=copy.copy(self.source);source.rel=bytearray(self.source.rel)
        at=self.source.sections[4][0]+self.report['tables']['type']['offset']
        source.rel[at]=2
        with self.assertRaisesRegex(ValueError,'shape selects an animation'):
            held.discover(source)


@unittest.skipUnless((OUTPUT/'art.json').is_file(),'Prepared held-model batch required')
class ArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SourceTests.setUpClass()
        cls.source=SourceTests.source
        cls.report=json.loads((OUTPUT/'art.json').read_bytes())
        cls.inventory=json.loads((OUTPUT/'inventory.json').read_bytes())

    def test_all_fourteen_complete_models_and_native_commands(self):
        self.assertEqual(self.report['format'],'AFV3-HANDHELD-PREPARED-ASSETS-1')
        self.assertFalse(self.report['runtime_installed']);self.assertFalse(self.report['selectable'])
        self.assertEqual(self.inventory, json.loads(json.dumps(held.scan(self.source))))
        self.assertEqual(len(self.report['objects']),14)
        self.assertEqual(sum(len(r['parent_item_ids']) for r in self.report['objects']),19)
        by_id={r['item_id']:r for r in self.inventory['rows']}
        for row in self.report['objects']:
            for item in row['parent_item_ids']:
                self.assertEqual(row['profile'],json.loads(json.dumps(held.descriptor(by_id[item]))))
        furniture_checks.DonorTests.check_complete_artwork(self,OUTPUT,self.report,
            prepare=lambda row:pipeline.prepare_models(self.source,row['profile']))

    def test_prepared_held_models_cannot_enter_furniture_installer(self):
        import v3_furniture_install as install
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            install.checked_assets(OUTPUT,self.source,ROOT/'build/item-identity-megasheet.xlsx')

    def test_shared_compiler_retains_current_furniture_output(self):
        import v3_optional_composition as composer
        _,report=composer.inputs()
        art=ROOT/report['automatic_furniture']['art_directory']
        batch=json.loads((art/'art.json').read_bytes())
        # Two different current model-sequence layouts cover the factored
        # compiler. No cartridge rebuild or historical emulator replay.
        for row in batch['objects']:
            with tempfile.TemporaryDirectory(dir=ROOT/'build',prefix='v3-model-emitter-') as temporary:
                result=pipeline.compile_models(Path(temporary),pipeline.prepare(self.source,int(row['item_id'],16)))
                self.assertEqual(result[0],(art/row['object_file']).read_bytes())
                self.assertEqual(result[1],row['model_offsets'])
                self.assertEqual(result[2],row['models'])
                self.assertEqual(result[3],row.get('draw_sequence'))


if __name__=='__main__':unittest.main()
