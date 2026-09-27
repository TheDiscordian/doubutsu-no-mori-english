"""Complete field-frame category, shared materials, and retained room artwork."""
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source,PreparedAssets,prepare,prepare_models
import v3_creature_field as field

ASSETS=ROOT/'build/v3-creature-field-prepared-01'


class CreatureFieldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.inventory=field.discover(cls.source)

    def test_complete_category_keeps_distinct_frames_and_repeat_bindings(self):
        report=self.inventory;rows=report['rows']
        self.assertEqual(report['counts'],dict(creatures=17,frames=59,unique_models=43,object_bytes=25504))
        self.assertEqual({r['item_id'] for r in rows},
            {f'{i:04X}' for i in (*range(0x2320,0x2329),*range(0x2D20,0x2D28))})
        for row in rows:
            self.assertFalse(row['runtime_installed']);self.assertFalse(row['selectable'])
            self.assertEqual(set(row['frame_labels']),set(row['descriptor']['models']))
            self.assertEqual(row['native_index'],int(row['item_id'],16)&255)
            if row['category']=='fish':
                self.assertEqual((row['unique_models'],row['frame_count'],len(row['frame_tables'])),(3,3,3))
                self.assertLessEqual(row['object_bytes'],0xA00)
            else:self.assertLessEqual(row['object_bytes'],0xC00)
        snail=next(r for r in rows if r['item_id']=='2D20')
        self.assertEqual(snail['frame_labels'],['frame0']*4)
        bagworm=next(r for r in rows if r['item_id']=='2D23')
        self.assertEqual(bagworm['frame_labels'],['frame0','frame0','frame0','frame1','frame2','frame2'])
        trout=next(r for r in rows if r['item_id']=='2328')
        self.assertEqual((trout['source_item_id'],trout['source_index']),('2301',1))
        # Do not substitute the field selector for the independently authored
        # release selector; their differences are actual source behaviour.
        jellyfish=next(r for r in rows if r['item_id']=='2323')
        self.assertEqual((jellyfish['animation'],jellyfish['release_animation']),(2,1))

    def test_shared_converter_retains_frame_specific_vertices_and_environment_alpha(self):
        fish=self.inventory['rows'][0]
        part=prepare_models(self.source,fish['descriptor'])
        vertices=[r for r in part[2] if r['kind']=='vertices']
        self.assertEqual(len(vertices),3)
        loads=[]
        for model in part[4].values():
            addresses={r['target'] for r in model['rows'] if r['opcode']==1}
            roots={v['donor_offset'] for v in vertices
                   if any(v['donor_offset']<=at<v['donor_offset']+v['bytes'] for at in addresses)}
            self.assertEqual(len(roots),1);loads.extend(roots)
        self.assertEqual(len(set(loads)),3)
        insect=next(r for r in self.inventory['rows'] if r['item_id']=='2D20')
        part=prepare_models(self.source,insect['descriptor'])
        combines=[r for m in part[4].values() for r in m['rows'] if r['opcode']==0xFC]
        self.assertEqual(combines[0]['combine_lerp'][4:8],['TEXEL0','0','ENVIRONMENT','0'])
        self.assertIn('TEXEL0, 0, ENVIRONMENT, 0',part[5])
        with self.assertRaises(ValueError):prepare_models(self.source,dict(models={}))

    def test_incomplete_frame_bindings_and_disagreeing_consumers_reject(self):
        ordinary=self.source.pointers
        row=self.inventory['rows'][0];at=row['frame_tables'][0]['offset']
        def missing(start,size):
            refs=ordinary(start,size)
            if start==at:refs.pop(at)
            return refs
        with patch.object(self.source,'pointers',side_effect=missing):
            with self.assertRaisesRegex(ValueError,'Incomplete creature frame'):
                field.discover(self.source)
        def differing(start,size):
            refs=ordinary(start,size)
            if start==field.FISH_TABLES[1]:
                refs[start+row['source_index']*4]=refs[start+4]
            return refs
        with patch.object(self.source,'pointers',side_effect=differing):
            with self.assertRaisesRegex(ValueError,'consumers disagree'):
                field.discover(self.source)

    @unittest.skipUnless((ASSETS/'art.json').is_file(),'Complete prepared field category required')
    def test_compiled_category_preserves_all_resources_and_frame_command_bounds(self):
        report=json.loads((ASSETS/'art.json').read_bytes())
        self.assertEqual(report['format'],field.FORMAT)
        self.assertEqual(report['source'],json.loads(json.dumps(self.inventory['source'])))
        self.assertEqual([r['item_id'] for r in report['objects']],[r['item_id'] for r in self.inventory['rows']])
        for row,expected in zip(report['objects'],self.inventory['rows'],strict=True):
            part=prepare_models(self.source,expected['descriptor'])
            raw=(ASSETS/row['object_file']).read_bytes()
            self.assertEqual(len(raw),expected['object_bytes']);self.assertEqual(sha256(raw),row['object_sha256'])
            self.assertEqual(raw[:len(part[1])],part[1])
            self.assertEqual(row['resources'],part[2])
            self.assertEqual(row['frame_offsets'],[row['model_offsets'][key] for key in expected['frame_labels']])
            for resource in row['resources']:
                at,n=resource['native_offset'],resource['bytes']
                self.assertEqual(sha256(raw[at:at+n]),resource['output_sha256'])
            for model in row['models']:
                at,n=model['native_offset'],model['bytes'];code=raw[at:at+n]
                self.assertEqual(sha256(code),model['output_sha256'])
                self.assertEqual(code[-8:],struct.pack('>II',0xDF000000,0))
                self.assertEqual([words for words in struct.iter_unpack('>II',code) if words[0]>>24==0xFC],
                    [r['words'] for r in part[4][model['layer']]['rows'] if r['opcode']==0xFC])
                for a,b in struct.iter_unpack('>II',code):
                    if a>>24 not in (1,0xFD):continue
                    self.assertEqual(b>>24,6)
                    offset=b&0xFFFFFF
                    size=(a>>12&255)*16 if a>>24==1 else 1
                    self.assertTrue(any(r['native_offset']<=offset and
                        offset+size<=r['native_offset']+r['bytes'] for r in row['resources']))
                    self.assertLess(offset,len(part[1]))

    def test_existing_room_category_reuses_prepared_art_without_recompiling(self):
        folder=ROOT/'build/v3-creature-profiles-prepared-01'
        if not (folder/'art.json').is_file():self.skipTest('Prepared room category required')
        report=json.loads((folder/'art.json').read_bytes());cache=PreparedAssets(self.source,[folder])
        self.assertEqual(len(report['objects']),17)
        for row in report['objects']:
            part=prepare(self.source,int(row['item_id'],16))
            self.assertIsNotNone(cache.reuse(self.source,row['item_id'],part))


if __name__=='__main__':unittest.main()
