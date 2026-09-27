"""Complete nested models and dual-motion lifecycles, without enabling stubs."""
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


if __name__=='__main__':unittest.main()
