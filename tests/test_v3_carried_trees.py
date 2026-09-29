"""Complete palm/cedar preparation and shared seasonal loading, not gameplay."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256,u32
from v3_furniture_pipeline import Source,prepare_material_pair
import v3_scenery as scenery
import v3_scenery_runtime as runtime
import tests.test_v3_equipment_runtime as host_helper
import tests.test_v3_furniture_pipeline as art_helper

ART=ROOT/'build/v3-carried-trees-prepared-02'
BANKS=ROOT/'build/v3-carried-runtime-work-01/tree-banks-01'


class HostTests(unittest.TestCase):
    sanitized=host_helper.HostTests.sanitized
    def test_shared_palettes_light_callback_selection_and_rejection(self):
        self.sanitized('v3_tree_families_test.c')


class TreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.inventory=scenery.discover(cls.source,'carried-trees')

    def test_complete_family_graphs_flags_palettes_and_aliases(self):
        inv=self.inventory
        self.assertEqual(inv['counts'],dict(seasons=4,foreground_ids=27,descriptors=85,
                                           model_pairs=67,object_bytes=124160))
        expected={f'{n:04X}' for n in (*range(0x70,0x7B),0x82,*range(0x854,0x863))}
        for season,(table,_) in zip(scenery.SEASONS,sorted(self.source.names['draw_part_table_a']),strict=True):
            rows=[r for r in inv['descriptors'] if r['season']==season]
            self.assertEqual(len(rows),22 if season=='xmas' else 21)
            self.assertEqual({b['foreground_id'] for b in inv['bindings'] if b['season']==season},expected)
            for row in rows:
                self.assertEqual(row['flags'],u32(self.source.data,table+row['table_index']*8+4))
        lights=[d for r in inv['descriptors'] for d in r['body'] if d['callback_kind']=='coloured-lights']
        self.assertEqual(len(lights),1)
        self.assertEqual([inv['palettes'][f]['palette_slot'] for f in ('cedar','palm')],[6,7])
        self.assertEqual(len(inv['model_aliases']),4)
        for row in inv['model_aliases']:
            alias=row['source'];target=scenery.resource(self.source,row['target'],pointers=True)
            self.assertEqual((alias['sha256'],alias['bytes']),(target['sha256'],target['bytes']))
            self.assertEqual({p-alias['donor_offset']:v for p,v in alias['pointers'].items()},
                             {p-target['donor_offset']:v for p,v in target['pointers'].items()})
        cedar_shadows=[r for r in inv['objects'] if r['models'][0][0]=='obj_cedar3_shadowT_mat_model']
        self.assertEqual(len(cedar_shadows),3)
        self.assertEqual(len({r['render_context']['external_vertices'][1] for r in cedar_shadows}),3)

    def test_changed_light_function_alias_and_palette_cannot_disappear(self):
        source=copy.copy(self.source);source.rel=bytearray(source.rel)
        fn=self.inventory['functions']['bXI_draw_loop_type1_xtree'][0]
        source.rel[source.sections[1][0]+fn['offset']]^=1
        with self.assertRaisesRegex(ValueError,'drawing callback'):scenery.discover(source,'carried-trees')
        source=copy.copy(self.source);source.data=bytearray(source.data)
        source.data[self.inventory['model_aliases'][0]['source']['donor_offset']]^=1
        with self.assertRaisesRegex(ValueError,'Unconsumed'):scenery.discover(source,'carried-trees')
        for family in ('palm','cedar'):
            source=copy.copy(self.source);source.data=bytearray(source.data)
            source.data[self.inventory['palettes'][family]['bank']['donor_offset']]^=1
            with self.assertRaisesRegex(ValueError,'palette bank'):scenery.discover(source,'carried-trees')

    @unittest.skipUnless((ART/'art.json').is_file(),'Prepared carried-tree resources required')
    def test_complete_art_and_packing_preserve_all_dependencies(self):
        bundle=runtime.prepared(self.source,ART)
        art,assets,palettes,_=bundle
        rows=[dict(r,models=r['compiled_models']) for r in art['objects']]
        art_helper.DonorTests.check_complete_artwork(self,ART,dict(objects=rows),prepare=lambda row:
            prepare_material_pair(self.source,[tuple(row['profile']['models'][k]) for k in ('material','geometry')],
                                  render_context=row['render_context']))
        for family,data in palettes.items():
            self.assertEqual(len(data),448);self.assertEqual(sha256(data),art['palettes'][family]['output_sha256'])
        mixed,models,pals=runtime.merge_categories([runtime.prepared(self.source,ROOT/'build/v3-scenery-gold-tree-01'),bundle])
        wrappers={n:(BANKS/'palette'/('palette.bin' if n==8 else f'palette{n}.bin')).read_bytes() for n in (6,7,8)}
        for season in scenery.SEASONS:
            data,report=runtime.pack_bank(mixed,models,pals,season,wrappers,
                light_loop=runtime.LIGHT_OFFSET if season=='xmas' else 0)
            self.assertEqual(data,(BANKS/(season+'.bin')).read_bytes())
            self.assertEqual(len(data),106640 if season=='xmas' else 105216)
            h=struct.unpack_from('>32I',data)
            self.assertEqual((h[1],h[11],h[13],h[19]),(2,32 if season=='xmas' else 31,41,3))
            self.assertEqual({p['slot'] for p in report['palettes']},{6,7,8})
            self.assertEqual(set(report['selected_items']),{0x223B,0x2807,0x290A})
            kinds=[u32(data,h[8]+i*8+4) for i in range(h[9])]
            self.assertEqual(kinds.count(2),int(season=='xmas'))
            used=set()
            for table,count,stride in ((h[4],h[5],4),(h[6],h[7],4),(h[8],h[9],8)):
                for i in range(count):
                    at=u32(data,table+i*stride);self.assertNotIn(at,used);used.add(at)
                    self.assertEqual(at%4,0);self.assertTrue(128<=at<=len(data)-4)
                    if stride==4:self.assertTrue(128<=u32(data,at)<len(data))
            # Every full descriptor's original flags survive packing, including palms.
            descriptors=[r for r in mixed['descriptors'] if r['season']==season]
            for i,row in enumerate(descriptors):self.assertEqual(u32(data,h[10]+i*8+4),row['flags'])
        with self.assertRaisesRegex(ValueError,'callback'):
            runtime.pack_bank(mixed,models,pals,'xmas',wrappers)


if __name__=='__main__':unittest.main()
