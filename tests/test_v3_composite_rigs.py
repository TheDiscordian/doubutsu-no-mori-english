"""Complete nested models and dual-motion lifecycles, without enabling stubs."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source,prepare,PreparedAssets,ReviewRequired
from v3_furniture_composite import ROTATED_CATEGORY,DUAL_CATEGORY
ART=ROOT/'build/v3-composite-rigs-prepared-01'


class CompositeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_resources_and_pending_profiles(self):
        from tests.test_v3_furniture_pipeline import DonorTests
        from v3_furniture_rigs import suffix
        from v3_furniture_install import profile
        art=json.loads((ART/'art.json').read_bytes())
        self.assertEqual([r['item_id'] for r in art['objects']],['1FCC','31B0'])
        DonorTests.check_complete_artwork(self,ART,art)
        for row in art['objects']:
            prepared=prepare(self.source,int(row['item_id'],16));descriptor=prepared[0]
            self.assertEqual(PreparedAssets(self.source,[ART]).reuse(self.source,row['item_id'],prepared)[1]['object_sha256'],row['object_sha256'])
            self.assertFalse(row['import_ready'])
            with self.assertRaises(ValueError):profile(row,0x02500000)
            adapter=descriptor['callback_adapter']
            for receipt in adapter['functions'].values():
                changed=copy.copy(self.source);data=bytearray(changed.rel)
                data[changed.sections[1][0]+receipt['offset']]^=1;changed.rel=bytes(data)
                with self.subTest(function=receipt['symbol']),self.assertRaises(ValueError):prepare(changed,int(row['item_id'],16))
            if adapter['category']==ROTATED_CATEGORY:
                self.assertEqual((adapter['rotation_y'],row['object_bytes']),(-0x7000,5152))
                self.assertEqual(adapter['emitter']['source_period'],36)
                self.assertIn('room-music-ownership',adapter['pending_callbacks'])
                self.assertEqual(sum(m['triangles'] for m in row['models']),24)
            else:
                self.assertEqual(adapter['category'],DUAL_CATEGORY)
                self.assertEqual((adapter['skeleton']['joints'],adapter['skeleton']['shown_joints']),(6,5))
                self.assertEqual([m['duration'] for m in adapter['animations']],[51,51])
                self.assertEqual(sum(m['triangles'] for m in row['models']),150)
                start=(len(prepared[1])+sum(n for _,n in prepared[6])+15)&~15
                packed,receipt=suffix(self.source,descriptor,row['model_offsets'],start=start,resources=row['resources'])
                blob=(ART/row['object_file']).read_bytes();self.assertEqual(blob[start:],packed)
                self.assertEqual(receipt['motion_offsets'],[8632,8652])
                self.assertNotEqual(blob[8632:8652],blob[8652:8672])
                for resource in receipt['animations']['arrays']:
                    at,n,dst=(resource[k] for k in ('donor_offset','bytes','native_offset'))
                    self.assertEqual(blob[dst:dst+n],self.source.data[at:at+n])

    def test_nested_graph_preserves_caller_and_callee_order_and_relocations(self):
        source=self.source;root=source.containing(5743832,exact=True)
        data,pointers,parts=source.model_graph(root)
        a,b=source.containing(5743680,exact=True),source.containing(5743744,exact=True)
        expected=source.data[root[1]:root[1]+40]+source.data[a[1]:a[1]+a[2]-8]+source.data[b[1]:b[1]+b[2]-8]+struct.pack('>II',0xDF000000,0)
        self.assertEqual(data,expected)
        expected_refs={}
        for at,n,joined in ((root[1],40,0),(a[1],a[2]-8,40),(b[1],b[2]-8,96)):
            expected_refs.update({joined+loc-at:target for loc,target in source.pointers(at,n).items()})
        self.assertEqual(pointers,expected_refs)
        self.assertEqual([p['donor_offset'] for p in parts],[root[1],a[1],b[1]])
        for part in parts:
            at,n=part['donor_offset'],part['bytes'];self.assertEqual(part['sha256'],sha256(source.data[at:at+n]))
        changed=copy.copy(source);changed.relocations=source.relocations.copy()
        ref=changed.relocations[root[1]+44];changed.relocations[root[1]+44]=(*ref[:3],root[1])
        with self.assertRaisesRegex(ReviewRequired,'recursive'):changed.model_graph(root)
        changed=copy.copy(source);raw=bytearray(source.data);struct.pack_into('>I',raw,root[1]+40,0xDE010000);changed.data=bytes(raw)
        with self.assertRaisesRegex(ReviewRequired,'branch'):changed.model_graph(root)
        # A direct model remains in the established absolute-address convention.
        self.assertEqual(source.model_graph(a),(source.data[a[1]:a[1]+a[2]],source.pointers(a[1],a[2]),None))

    def test_dual_motion_against_actual_us_donor_under_sanitizers(self):
        text=(ROOT/'local/ac-decomp/src/furniture/ac_ike_island_hako01.c').read_text();functions=[]
        for name,prefix,after in (('fIIH_ct','static void ',0),('fIIH_mv','void ',text.index('#else')),('fIIH_dt','void ',0)):
            start=text.index('\n'+prefix+name+'(',after)+1
            # The constructor's earlier prototype is not a function body.
            if text.index(';',start)<text.index('{',start):start=text.index('\n'+prefix+name+'(',start)+1
            functions.append(text[start:text.index('\n}',start)+2])
        with tempfile.TemporaryDirectory(prefix='v3-dual-motion-') as d:
            directory=Path(d);binary=directory/'check'
            (directory/'donor_dual_motion.inc').write_text('\n\n'.join(functions))
            run=subprocess.run(['cc','-std=gnu11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I'+str(directory),str(ROOT/'tests/v3_dual_motion_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('9612 donor comparisons; 4800 draw frames',run.stdout)

    def test_complete_dual_motion_audio_dependencies(self):
        from v3_sound_programs import prepare_triggers,furniture_trigger,furniture_trigger_words,furniture_level,trigger_program
        from v3_furniture_install import inputs
        directory=ROOT/'build/v3-dual-motion-audio-01'
        receipt=json.loads((directory/'triggers/audio.json').read_bytes())
        image,report=inputs(ROOT/'build/v3-effect-rig-imports-01/cartridge/build-lock.json')
        profile=self.source.profile(0x31B0);trigger=furniture_trigger(self.source,profile)
        self.assertEqual(furniture_trigger_words([trigger]),[0x16A,0x16B])
        self.assertEqual(furniture_level(self.source,profile)['source_sound_id'],0x52)
        resources,actual=prepare_triggers(image,report,[0x16A,0x16B])
        self.assertEqual(receipt['programs'],json.loads(json.dumps(actual['programs'])))
        for name,data in dict(resources['fragments'],**{'font.bin':resources['font'],'wave.bin':resources['wave']}).items():
            self.assertEqual((directory/'triggers'/name).read_bytes(),data)
        for row,size,indices in zip(actual['programs'],[32,20],[[5,74],[73]],strict=True):
            self.assertEqual(row['bytes'],size)
            self.assertEqual([p['source_instrument'] for p in row['layer_instruments']],indices)
            self.assertEqual({p['source_instrument'] for p in actual['layout']['imports']} & set(indices),set(indices))
            raw=resources['fragments'][row['fragment_file']];origin=row['fragment_origin']
            parsed=trigger_program(bytes(origin)+raw,origin,origin+len(raw))
            self.assertEqual(parsed['events'],row['source_program']['events'])
            mapping={p['source_instrument']:p['native_instrument'] for p in row['layer_instruments']}
            self.assertEqual([p['instrument'] for p in parsed['commands'] if p['opcode']==0xC6],
                [mapping[p['instrument']] for p in row['source_program']['commands'] if p['opcode']==0xC6])
        from aflib import by_vrom,CODE_RAM,CODE_VROM
        from v3_sound_programs import register_triggers,installed_resource,read_audio_donor
        code=by_vrom(image)[CODE_VROM].extract(image);prior=report['equipment_resources']['furniture_audio']
        sequence,_,_=installed_resource(image,code,'seq',199)
        dol,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        registered,programs,tables=register_triggers(sequence,actual['programs'],resources['fragments'],
            {r['group']:r['previous_count'] for r in prior['tables']},
            code[0x80113B84-CODE_RAM:0x80113B84-CODE_RAM+128],dol.read(0x800A9A90,128),previous=prior)
        self.assertEqual(len(programs),2)
        for old in prior['programs']:
            self.assertEqual(registered[old['offset']:old['offset']+old['bytes']],sequence[old['offset']:old['offset']+old['bytes']])
        for prepared,installed in zip(actual['programs'],programs,strict=True):
            self.assertEqual(installed['layer_instruments'],prepared['layer_instruments'])
            table=next(r for r in tables if r['group']==1)
            self.assertEqual(struct.unpack_from('>H',registered,table['offset']+2*(installed['native_sound_word']&255))[0],installed['offset'])
        loop=json.loads((directory/'loop/audio.json').read_bytes())
        self.assertEqual([r['source_sound_id'] for r in loop['programs']],[0x52])
        data=(directory/'loop/sequence.bin').read_bytes()
        self.assertEqual(sha256(data),loop['sequence']['sha256'])
        for row in loop['programs']:
            self.assertEqual(sha256(data[row['offset']:row['offset']+row['bytes']]),row['sha256'])

    def test_dual_motion_shared_dispatch_and_native_save_capture(self):
        from v3_room_rig_runtime import prepared_categories,encode_packet
        bundle=ROOT/'build/v3-dual-motion-imports-01/prepared'
        row=json.loads((bundle/'art.json').read_bytes())['objects'][0]
        with tempfile.TemporaryDirectory(prefix='v3-dual-dispatch-',dir=ROOT/'build') as d:
            directory=Path(d)
            rows,_,_=prepared_categories(self.source,[bundle])
            self.assertEqual((rows[0]['mode'],rows[0]['first'],rows[0]['last'],rows[0]['loop']),
                (11,0x06000000+8652,0,0x52))
            rows[0]['last']=0x016A016B
            table=directory/'table';table.write_bytes(encode_packet(rows));binary=directory/'check'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-DAF_V3_ROOM_DUAL_MOTION','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-fno-pie','-no-pie',str(ROOT/'tests/v3_reversible_dispatch_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary),str(table),str(ART/row['object_file'])],
                capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('2880 dual-motion dispatch frames',run.stdout)


class InstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from v3_furniture_install import inputs
        from aflib import by_vrom
        from v3_asset_loader import BLOB
        cls.batch=ROOT/os.environ.get('V3_DUAL_MOTION_BATCH','build/v3-dual-motion-imports-01')
        pipeline=json.loads((cls.batch/'pipeline.json').read_bytes())
        cls.out=(ROOT/pipeline['final_lock']).parent
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-effect-rig-imports-01/cartridge/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)

    def test_complete_installed_motion_sound_contexts_save_bindings_and_retention(self):
        from aflib import by_vrom,apply_ups,CODE_VROM
        from v3_asset_loader import BLOB
        from v3_furniture_composite import dual_native_contract,dual_sound_words,checked_dual_binding
        from v3_sound_programs import checked_furniture_loops,installed_resource
        from v3_room_rig_runtime import bind_profiles,encode_packet
        from v3_furniture_pipeline import scan,rig_import_plan
        from v3_villager_audio import instrument
        e=self.report['equipment_resources'];room=e['room_rigs']
        bindings=bind_profiles(self.source,self.image,self.report)
        row=next(r for r in room['rows'] if r['source_item_id']=='31B0')
        self.assertTrue(bindings['31B0']['staged']);self.assertTrue(row['profile_installed'])
        self.assertFalse(row['parent_selectable']);self.assertEqual((row['mode'],row['joints'],row['shown']),(11,6,5))
        self.assertEqual((row['animation'],row['first'],row['loop']),(0x06000000+8632,0x06000000+8652,0x52))
        self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']],(ART/'31B0.n64obj.bin').read_bytes())
        self.assertEqual(room['dual_contract'],dual_native_contract(self.image,self.report))
        words=dual_sound_words(self.source,self.source.profile(0x31B0),self.image,self.report)
        self.assertEqual(row['last'],words[0]<<16|words[1]);self.assertNotEqual(words[0],words[1])
        core=by_vrom(self.image)[CODE_VROM].extract(self.image)
        contracts,_=checked_furniture_loops(self.image,core,e,self.source)
        for key,value in (('last',0),('first',row['animation']),('loop',0),('dual_lifecycle',None)):
            bad=copy.deepcopy(row);bad[key]=value
            with self.assertRaises(ValueError):checked_dual_binding(self.source,self.source.profile(0x31B0),bad,contracts,e)
        packet=encode_packet(room['rows'],room['sound_rows'],room['material_rows'])
        at=room['packet']['blob_offset']+0x8000
        self.assertEqual(self.blob[at:at+len(packet)],packet)
        audio=e['furniture_audio'];font,header,_=installed_resource(self.image,core,'bank',140)
        wave,_,_=installed_resource(self.image,core,'wave',header[10])
        for r in audio['layout']['imports']:
            self.assertEqual(instrument(font,wave,r['native_instrument'],header[12],extended=True),r['identity'])
        source_audio=json.loads((self.batch/'audio/audio.json').read_bytes())
        imported={r['source_instrument'] for r in source_audio['layout']['imports']}
        self.assertTrue({4,5,73,74}<=imported)
        old=self.prior['equipment_resources'];blob=by_vrom(self.base)[BLOB].extract(self.base)
        for key in ('rows','sound_rows','material_rows'):
            for previous in old['room_rigs'][key]:
                kept=next(r for r in room[key] if r['source_item_id']==previous['source_item_id'])
                self.assertEqual(kept,previous)
                if 'blob_offset' in previous:
                    at=previous['blob_offset'];n=previous['bytes'];self.assertEqual(self.blob[at:at+n],blob[at:at+n])
        for key in ('room_goods','room_carry'):self.assertEqual(e[key],old[key])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['31B0'])
        self.assertTrue(all(not v for v in rig_import_plan(inventory,self.report,bindings,source=self.source).values()))
        self.assertEqual(inventory['rows'][0]['reason'],'acquisition needs an adapter: ftr_listIsland')
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)
        self.assertLessEqual(room['code']['bytes'],32768);self.assertLessEqual(room['bootstrap']['bytes'],1536)

    def test_private_browser_compositions_keep_unavailable_acquisition_disabled(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        self.assertNotIn('31B0',{r.get('donor_item_id') for r in self.rows})
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
