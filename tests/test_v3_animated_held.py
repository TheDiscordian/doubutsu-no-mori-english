"""Complete shared rig packing, donor artwork, animation bindings, and isolation."""
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
from aflib import by_vrom,sha256
import v3_furniture_pipeline as pipeline
import v3_handheld_items as held
import v3_keyframes as keyframes
from tests import test_v3_furniture_pipeline as furniture_checks

OUTPUT=ROOT/os.environ.get('V3_ANIMATED_HELD_ART','build/v3-handheld-animated-prepared-01')
BASE=ROOT/os.environ.get('V3_ANIMATED_HELD_BASE','build/v3-translation-headers-02')
EXTENDED=ROOT/'build/v3-held-matrix-prepared-02'


class AnimatedHeldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.motion=held.motion(cls.source)
        cls.inventory=held.scan(cls.source)
        cls.rows={r['item_id']:r for r in cls.inventory['rows']}

    def test_shared_scan_exposes_complete_rigs_without_claiming_gameplay(self):
        rows=[r for r in self.rows.values() if r['category']=='animated-held-model']
        self.assertEqual(len(rows),20)
        self.assertTrue(all(r['asset_ready'] for r in rows))
        self.assertEqual(self.inventory['counts']['prepared_model_roots'],34)
        self.assertEqual(self.inventory['counts']['usable_imports'],0)
        for row in rows:
            self.assertFalse(row['selectable']);self.assertFalse(row['runtime_installed'])
            self.assertEqual(row['motion_binding']['shape_index'],row['shape_index'])
            rig=self.motion['skeletons'][row['shape_index']]
            self.assertEqual((row['joints'],row['shown_joints']),(rig['joints'],rig['shown_joints']))

    def test_rig_packing_keeps_every_joint_field_and_checked_model_reference(self):
        for rig in self.motion['skeletons'].values():
            roots=sorted({r['model']['donor_offset'] for r in rig['rows'] if 'model' in r})
            targets={root:i*16 for i,root in enumerate(roots)}
            data,report=keyframes.compile_skeleton(self.source,rig,targets,start=256)
            self.assertEqual(len(data)%16,0)
            n=rig['joint_table']['bytes'];at=rig['joint_table']['donor_offset']
            expected=bytearray(self.source.data[at:at+n])
            pointers=self.source.pointers(at,n)
            for i in range(rig['joints']):
                if at+i*12 in pointers:
                    struct.pack_into('>I',expected,i*12,0x06000000+targets[pointers[at+i*12]])
                else:self.assertEqual(data[i*12:i*12+4],bytes(4))
            self.assertEqual(data[:n],expected)
            self.assertEqual(data[n:n+4],self.source.data[rig['header']['donor_offset']:rig['header']['donor_offset']+4])
            self.assertEqual(struct.unpack_from('>I',data,n+4)[0],0x06000100)
            self.assertEqual(data[n+8:],bytes(len(data)-n-8))
            self.assertEqual(report['header']['native_offset'],256+n)
            self.assertFalse(report['runtime_installed'])
            self.assertEqual(len(report['relocations']),rig['shown_joints']+1)
            for fix in report['relocations']:
                self.assertEqual(struct.unpack_from('>I',data,fix['offset']-256)[0],
                                 0x06000000+fix['target_offset'])

    def test_changed_rigs_unbound_models_and_escaping_offsets_reject(self):
        rig=self.motion['skeletons'][33]
        targets={r['model']['donor_offset']:i*16 for i,r in enumerate(rig['rows']) if 'model' in r}
        bad=copy.deepcopy(rig);bad['rows'][1]['translation'][0]+=1
        with self.assertRaisesRegex(ValueError,'Changed skeleton'):
            keyframes.compile_skeleton(self.source,bad,targets,start=256)
        for change in ('missing','extra','unaligned','tail','negative','duplicate'):
            bad=dict(targets);key=next(iter(bad))
            if change=='missing':bad.pop(key)
            elif change=='extra':bad[0x7FFFFFFF]=128
            else:bad[key]={'unaligned':3,'tail':256,'negative':-8,
                          'duplicate':list(targets.values())[-1]}[change]
            with self.assertRaisesRegex(ValueError,'preceding artwork'):
                keyframes.compile_skeleton(self.source,rig,bad,start=256)
        for start in (-16,3,0x1000000,0xFFFFFFFF):
            with self.assertRaises(ValueError):keyframes.compile_skeleton(self.source,rig,targets,start=start)
        for item in ('2254','2200'):
            with self.assertRaises(ValueError):held.rig_descriptor(self.rows[item],rig)

    def test_category_and_selection_rejections_create_no_partial_output(self):
        with tempfile.TemporaryDirectory(prefix='v3-animated-held-') as directory:
            output=Path(directory)/'not-created'
            for selected in (['2224'],['FFFF'],['2254'],['224C','FFFF']):
                with self.assertRaisesRegex(ValueError,'Unsupported or unknown selected animated'):
                    held.convert(self.source,output,selected,category='animated-held-model')
                self.assertFalse(output.exists())
            with self.assertRaisesRegex(ValueError,'Unsupported or unknown selected handheld'):
                held.convert(self.source,output,['224C'])
            self.assertFalse(output.exists())

    @unittest.skipUnless((EXTENDED/'art.json').is_file(),'Prepared matrix/IA8 category required')
    def test_remaining_rigs_preserve_complete_artwork_and_skeleton_dependencies(self):
        report=json.loads((EXTENDED/'art.json').read_bytes())
        self.assertFalse(report['runtime_installed']);self.assertFalse(report['selectable'])
        installed=json.loads((OUTPUT/'art.json').read_bytes())
        old={r['shape_index'] for r in installed['objects']}
        self.assertEqual({r['shape_index'] for r in report['objects']},set(self.motion['skeletons'])-old)
        self.assertEqual(len(report['objects']),12)
        furniture_checks.DonorTests.check_complete_artwork(self,EXTENDED,report,
            prepare=lambda row:pipeline.prepare_models(self.source,row['profile']))
        for row in report['objects']:
            rig=self.motion['skeletons'][row['shape_index']]
            parent=self.rows[row['parent_item_ids'][0]]
            self.assertEqual(row['profile'],json.loads(json.dumps(held.rig_descriptor(parent,rig))))
            asset=(EXTENDED/row['object_file']).read_bytes()
            roots={root[1]:row['model_offsets'][label] for label,root in row['profile']['models'].items()}
            suffix,description=keyframes.compile_skeleton(self.source,rig,roots,start=row['artwork_bytes'])
            self.assertEqual(asset[row['artwork_bytes']:],suffix)
            self.assertEqual(row['skeleton'],json.loads(json.dumps(description)))
            self.assertEqual(row['maximum_model_animation_bytes'],len(asset)+row['maximum_animation_bytes'])
        self.assertEqual(max(r['maximum_model_animation_bytes'] for r in report['objects']),7168)

    @unittest.skipUnless((EXTENDED/'art.json').is_file(),'Prepared matrix/IA8 category required')
    def test_preparation_does_not_expand_installed_categories_or_joint_capacity(self):
        import v3_equipment_runtime as equipment
        old=json.loads((OUTPUT/'art.json').read_bytes())
        assets,_,_=equipment.prepared_rigs(self.source,OUTPUT)
        self.assertEqual(set(assets),{r['shape_index'] for r in old['objects']})
        with self.assertRaisesRegex(ValueError,'unsupported equipment rig'):
            equipment.prepared_rigs(self.source,EXTENDED)
        report=json.loads((EXTENDED/'art.json').read_bytes())
        parents={p for row in report['objects'] for p in row['parent_item_ids']}
        categories=tuple(sorted({r['item_main'] for r in held.kind_bindings(self.source)['rows']
                                 if r['item_id'] in parents}))
        with self.assertRaisesRegex(ValueError,'work-vector capacity'):
            equipment.prepared_rigs(self.source,EXTENDED,categories=categories)
        assets,_,_=equipment.prepared_rigs(self.source,EXTENDED,categories=categories,joint_work_vectors=8)
        self.assertEqual(set(assets),{r['shape_index'] for r in report['objects']})

    @unittest.skipUnless((OUTPUT/'art.json').is_file(),'Prepared animated category required')
    def test_complete_native_artwork_and_rigs_match_actual_donor(self):
        report=json.loads((OUTPUT/'art.json').read_bytes())
        self.assertEqual(report['format'],'AFV3-ANIMATED-HELD-PREPARED-1')
        self.assertEqual(report['source_rel_sha256'],sha256(self.source.rel))
        self.assertFalse(report['runtime_installed']);self.assertFalse(report['selectable'])
        self.assertEqual(len(report['objects']),8)
        self.assertEqual(sum(r['object_bytes'] for r in report['objects']),26272)
        self.assertEqual(sum(m['triangles'] for r in report['objects'] for m in r['models']),396)
        self.assertEqual(sum(v['bytes']//16 for r in report['objects'] for v in r['resources']
                             if v['kind']=='vertices'),560)
        furniture_checks.DonorTests.check_complete_artwork(self,OUTPUT,report,
            prepare=lambda row:pipeline.prepare_models(self.source,row['profile']))
        for row in report['objects']:
            rig=self.motion['skeletons'][row['shape_index']]
            parent=self.rows[row['parent_item_ids'][0]]
            self.assertEqual(row['profile'],json.loads(json.dumps(held.rig_descriptor(parent,rig))))
            asset=(OUTPUT/row['object_file']).read_bytes();header=row['root_offset']
            self.assertEqual(row['resource_type'],1)
            joints,shown=asset[header:header+2]
            self.assertEqual((joints,shown),(rig['joints'],rig['shown_joints']))
            self.assertEqual(asset[header+2:header+4],bytes(2))
            table=struct.unpack_from('>I',asset,header+4)[0]-0x06000000
            self.assertEqual(table,row['artwork_bytes'])
            bindings={b['joint_index']:b['model_label'] for b in row['profile']['joint_models']}
            pending=[1];seen=0
            for i in range(joints):
                while pending and not pending[-1]:pending.pop()
                self.assertTrue(pending);pending[-1]-=1
                ptr,children,stream,*translation=struct.unpack_from('>IBB3h',asset,table+12*i)
                original=rig['rows'][i]
                self.assertEqual((children,stream,translation),
                                 (original['children'],original['draw_stream'],original['translation']))
                if children:pending.append(children)
                if i in bindings:
                    self.assertEqual(ptr,0x06000000+row['model_offsets'][bindings[i]])
                    seen+=1
                else:self.assertEqual(ptr,0)
            self.assertFalse(any(pending));self.assertEqual(seen,shown)
            roots={root[1]:row['model_offsets'][label] for label,root in row['profile']['models'].items()}
            suffix,compiled=keyframes.compile_skeleton(self.source,rig,roots,start=table)
            self.assertEqual(asset[table:],suffix)
            self.assertEqual(row['skeleton'],json.loads(json.dumps(compiled)))
            for material in row['resources']:
                if material['kind']=='palette':
                    from v3_villager_art import native_palette
                    at,n,out=material['donor_offset'],material['bytes'],material['native_offset']
                    self.assertEqual(asset[out:out+n],native_palette(self.source.data[at:at+n]))
            sizes=[]
            for parent in row['motion_bindings']:
                for index in parent['animation_resources']:
                    desc={k:v for k,v in self.motion['equipment_animations'][index].items() if k!='resource_type'}
                    self.assertEqual(desc['joints'],joints)
                    sizes.append(len(keyframes.compile_animations(self.source,[desc])[0]))
            self.assertEqual(row['maximum_animation_bytes'],max(sizes))
            self.assertEqual(row['maximum_model_animation_bytes'],len(asset)+max(sizes))
        self.assertEqual([r['maximum_model_animation_bytes'] for r in report['objects']],
                         [2896]*6+[5248,4928])

    @unittest.skipUnless((OUTPUT/'art.json').is_file(),'Prepared animated category required')
    def test_prepared_rigs_cannot_enter_static_or_furniture_installer(self):
        import v3_equipment_runtime as equipment
        import v3_furniture_install as furniture
        with self.assertRaisesRegex(ValueError,'artwork source/format'):
            equipment.prepared_resources(self.source,OUTPUT)
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            furniture.checked_assets(OUTPUT,self.source,ROOT/'build/item-identity-megasheet.xlsx')

    @unittest.skipUnless((BASE/'build.json').is_file(),'Current cartridge required')
    def test_static_resource_consumer_retains_all_installed_data(self):
        import v3_equipment_runtime as equipment
        report=json.loads((BASE/'build.json').read_bytes())
        image=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        self.assertEqual(sha256(image),report['output_sha256'])
        blob=by_vrom(image)[equipment.BLOB].extract(image)
        current=report['equipment_resources']
        assets,records,_=equipment.prepared_resources(self.source,ROOT/current['evidence']['art_directory'])
        self.assertEqual(len(assets),30)
        installed={r['source_index']:r for r in current['records']}
        for row in records:
            old=installed[row['source_index']]
            for field in ('index','type','bytes','pointer','sha256'):
                self.assertEqual(row[field],old[field])
            self.assertEqual(assets[row['source_index']],blob[old['blob_offset']:old['blob_offset']+old['bytes']])


if __name__=='__main__':unittest.main()
