"""Complete joint-callback resource category, without claiming native gameplay."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source, prepare, PreparedAssets, metadata, identity_rows
from v3_furniture_install import profile
from v3_furniture_joint_rigs import CATEGORY
from v3_furniture_rigs import suffix
from v3_furniture_scroll import bindings


class JointRigResourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        cls.art=ROOT/os.environ.get('V3_JOINT_RIG_ART','build/v3-joint-callback-rigs-prepared-01')
        cls.report=json.loads((cls.art/'art.json').read_bytes())
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_all_complete_art_and_keyframes_in_one_compiler_batch(self):
        from tests.test_v3_furniture_pipeline import DonorTests
        DonorTests.check_complete_artwork(self,self.art,self.report)
        rows=self.report['objects']
        self.assertEqual([r['item_id'] for r in rows],['3064','3070','309C','31AC'])
        self.assertEqual(self.report['batch'],dict(objects=4,compiled=4,reused=0,compiler_containers=1))
        self.assertEqual([r['object_bytes'] for r in rows],[3008,4576,3600,5296])
        self.assertEqual(sum(m['triangles'] for r in rows for m in r['models']),290)
        for r in rows:
            descriptor=prepare(self.source,int(r['item_id'],16))[0]
            end=max(m['native_offset']+m['bytes'] for m in r['models']);start=(end+15)&~15
            complete,receipt=suffix(self.source,descriptor,r['model_offsets'],start=start)
            asset=(self.art/r['object_file']).read_bytes()
            self.assertEqual(asset[start:],complete)
            self.assertEqual(json.loads(json.dumps(receipt)),r['rig'])
            # Each original motion array survives in full, at its relocated offset.
            for array in r['rig']['animations']['arrays']:
                at,n,dst=array['donor_offset'],array['bytes'],array['native_offset']
                self.assertEqual(asset[dst:dst+n],self.source.data[at:at+n])
            self.assertEqual(r['profile']['skeleton']['shown_joints'],len(r['profile']['joint_models']))

    def test_callbacks_retained_and_incomplete_gameplay_cannot_install(self):
        identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',include_unmapped_legacy=True)
        for row in self.report['objects']:
            item=int(row['item_id'],16);descriptor=self.source.profile(item);adapter=descriptor['callback_adapter']
            self.assertEqual(adapter['category'],CATEGORY)
            self.assertEqual(adapter['pending_callbacks'],['create','move','draw'])
            self.assertFalse(row['import_ready'] or adapter['runtime_installed'])
            self.assertIn('lifecycle and joint behaviour',row['pending_reason'])
            with self.assertRaisesRegex(ValueError,'lifecycle and joint behaviour'):
                metadata(self.source,item,descriptor,identities[item])
            with self.assertRaisesRegex(ValueError,'native lifecycle'):
                profile(row,0x02600000,model_capacity=12288)
            for receipt in [adapter['functions']['create'],adapter['functions']['draw'],*adapter['joint_callbacks']]:
                changed=copy.copy(self.source);changed.rel=bytearray(self.source.rel)
                changed.rel[self.source.sections[1][0]+receipt['offset']]^=1
                with self.assertRaises(ValueError,msg=(row['item_id'],receipt['symbol'])):changed.profile(item)
        cache=PreparedAssets(self.source,[self.art])
        for row in self.report['objects']:
            reused=cache.reuse(self.source,row['item_id'],prepare(self.source,int(row['item_id'],16)))
            self.assertEqual(reused[1]['object_sha256'],row['object_sha256'])

    def test_donor_intensity_format_and_distinct_scroll_window(self):
        from v3_villager_audio import read_audio_donor
        dol,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        table=dol.read(0x800AAFC0,64)
        self.assertEqual(sha256(table),'7ae4019ff69d72ee09dd42b8b1c5a4c7a3a236d07aa238e2acdb93c97302fe30')
        self.assertEqual(struct.unpack_from('>H',table,(4*4+1)*2)[0],1)
        row=next(r for r in self.report['objects'] if r['item_id']=='3070')
        resource,=[r for r in row['resources'] if r.get('format')=='I8']
        self.assertEqual((resource['width'],resource['height'],resource['bytes']),(8,16,128))
        adapter=self.source.profile(0x31AC)['callback_adapter'];scroll=adapter['scrolling']
        self.assertEqual(scroll['texture_dimensions'],[[16,32]])
        self.assertEqual([[t['width'],t['height']] for t in scroll['tiles']],[[8,32],[8,32]])
        self.assertEqual([t['rate'] for t in scroll['tiles']],[[0,8],[0,0]])
        self.assertEqual(bindings(adapter),{scroll['model']:dict(segment=0x09000000,dimensions=[[16,32]])})
        for field,value in [('texture_dimensions',[[8,32]]),('segment_address',0x08000000)]:
            bad=copy.deepcopy(adapter);bad['scrolling'][field]=value
            with self.assertRaisesRegex(ValueError,'scroll window'):bindings(bad)
        from v3_furniture_art import command_source
        parts=prepare(self.source,0x3070)
        model=next(m for m in parts[4].values() if any(r.get('i8') for r in m['rows']))
        bad=copy.deepcopy(model);texture=next(r for r in bad['rows'] if r.get('i8'));texture['intensity']=False
        with self.assertRaisesRegex(ValueError,'conflicting formats'):command_source({'model':bad},parts[3])

    def test_joint_redraws_retain_every_source_model_and_render_parameter(self):
        for item,hidden,colour in ((0x3070,[3,7],'primitive-lod'),(0x31AC,[3,4],'primitive-alpha')):
            parts=prepare(self.source,item);a=parts[0]['callback_adapter']
            self.assertEqual(a['joint_features'],dict(mode='translucent-joints',joints=hidden,colour=colour))
            for joint in hidden:
                label=next(r['model_label'] for r in a['joint_models'] if r['joint_index']==joint)
                self.assertIn(label,parts[4])
            post=next(r for r in a['joint_callbacks'] if r['role']=='after')
            changed=copy.copy(self.source);changed.code_relocations=dict(self.source.code_relocations)
            # Redirecting only a high binding cannot silently substitute a joint model.
            p=next(p for p,ref in post['relocations'].items() if ref[:3]==(6,1,5))
            target=post['relocations'][p]
            changed.code_relocations[post['offset']+p]=(*target[:3],target[3]+8)
            with self.assertRaises(ValueError):changed.profile(item)
