"""Shared movement rules, complete sounds, and ordinary category activation."""
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
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_room_rig_runtime import bind_profiles
from v3_room_movement import checked_binding,checked_owner,encode,source_contract,BRIDGE,SOURCES
from v3_sound_programs import installed_resource,checked_furniture_loops,trigger_program,register_triggers,read_audio_donor
import v3_optional_composition as composer
import v3_browser_composition as browser

OUT=ROOT/'build/v3-room-movement-imports-01/cartridge'


class MovementTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(OUT/'build-lock.json')
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-contact-floor-runtime-04/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.equipment=cls.report['equipment_resources'];cls.scroll=cls.equipment['room_rigs']['scrolling']
        cls.movement=cls.scroll['movement'];cls.code=by_vrom(cls.image)[CODE_VROM].extract(cls.image)
        cls.catalogue=composer.catalogue(cls.image,cls.report)
    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.pin

    def test_complete_source_dispatch_and_activation_bindings(self):
        bound=checked_binding(self.source,self.image,self.report)
        self.assertEqual(set(bound),{'3018','33A0'});self.assertEqual(bound['33A0']['floors'],[74,48])
        self.assertEqual(bound['3018']['mode'],1);self.assertEqual(bound['33A0']['mode'],2)
        self.assertEqual([r['source_sounds'] for r in self.movement['source']['rows']],[[125,126],[375]])
        self.assertEqual(self.movement['entry'],BRIDGE);checked_owner(self.image,BRIDGE)
        self.assertLessEqual(self.scroll['code']['bytes'],4096)
        self.assertLessEqual(self.equipment['room_rigs']['bootstrap']['bytes'],1536)
        self.assertGreaterEqual(self.equipment['sound_programs']['after_budget']['conservative_spare'],0)
        profiles=bind_profiles(self.source,self.image,self.report)
        self.assertIn('33A0',profiles);self.assertFalse(profiles['33A0']['staged'])
        self.assertNotIn('GAFE01-r0/item/3018',self.catalogue)
        self.assertEqual(len(self.catalogue),148);self.assertIn('GAFE01-r0/item/33A0',self.catalogue)
        for path in SOURCES:self.assertEqual(self.report['sources'][path],sha256((ROOT/path).read_bytes()))
        bad=copy.deepcopy(self.report);bad['equipment_resources']['room_rigs']['scrolling']['movement']['rows'][1]['floors'][0]=26
        with self.assertRaisesRegex(ValueError,'movement installation'):checked_binding(self.source,self.image,bad)
        changed=copy.copy(self.source);changed.rel=bytearray(self.source.rel)
        changed.rel[self.source.sections[1][0]+0x10EBAC+0x10F]^=1
        with self.assertRaisesRegex(ValueError,'source room movement'):source_contract(changed,self.image,self.report)
        old_assets={r['source_item_id']:r for r in self.prior['equipment_resources']['room_rigs']['scrolling']['rows']}
        for row in self.scroll['rows']:
            for key in ('vrom','blob_offset','bytes','sha256','source'):self.assertEqual(row[key],old_assets[row['source_item_id']][key])
        self.assertEqual(self.report['save_codec']['format_version'],4)
        self.assertFalse(self.report['saved_format_changed'])
        before=bytes.fromhex(self.prior['save_runtime']['profile_hex']);after=bytes.fromhex(self.report['save_runtime']['profile_hex'])
        self.assertEqual([(i,a^b) for i,(a,b) in enumerate(zip(before,after)) if a!=b],[(61,1)])
        self.assertEqual(self.report['room_surfaces']['optional_selection'],self.prior['room_surfaces']['optional_selection'])

    def test_complete_audio_and_incremental_category_reuse(self):
        current,_,_=installed_resource(self.image,self.code,'seq',199)
        original,_,_=installed_resource(self.base,by_vrom(self.base)[CODE_VROM].extract(self.base),'seq',199)
        self.assertEqual(len(current)-len(original),320)
        old_table=struct.unpack_from('>H',original,0x188)[0];table=struct.unpack_from('>H',current,0x188)[0]
        self.assertEqual(current[table:table+162],original[old_table:old_table+162])
        old=self.prior['equipment_resources']['furniture_audio'];audio=self.equipment['furniture_audio']
        mapping={r['source_sound_word']:r for r in audio['programs']}
        for row in old['programs']:self.assertEqual(mapping[row['source_sound_word']],row)
        rolling=next(r for r in self.movement['programs'] if r['source_sound_word']==125)
        desc=trigger_program(current,rolling['offset'],rolling['offset']+rolling['bytes'])
        self.assertEqual(desc['duration'],78);self.assertEqual(len(desc['events']),3)
        self.assertEqual([c['opcode'] for c in desc['commands']],[0xC2,0xC4,0xC7,0xC7,0xC7])
        self.assertEqual(desc['commands'],rolling['source_program']['commands'])
        broken=bytearray(current);broken[rolling['offset']+13]=0
        with self.assertRaisesRegex(ValueError,'pitch sweep'):trigger_program(broken,rolling['offset'],rolling['offset']+rolling['bytes'])
        contracts,proof=checked_furniture_loops(self.image,self.code,self.equipment,self.source)
        self.assertEqual(len(contracts),4);self.assertTrue(proof['complete_programs_and_instruments'])
        prepared=json.loads((ROOT/'build/v3-room-movement-prepared-01/audio.json').read_bytes())
        fragments={r['fragment_file']:(ROOT/'build/v3-room-movement-prepared-01'/r['fragment_file']).read_bytes() for r in prepared['programs']}
        dol,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        priority=self.code[0x80113B84-CODE_RAM:0x80113B84-CODE_RAM+128]
        same,rows,tables=register_triggers(current,prepared['programs'],fragments,
            {r['group']:r['previous_count'] for r in audio['tables']},priority,dol.read(0x800A9A90,128),previous=audio)
        self.assertEqual(same,current);self.assertEqual(tables,audio['tables'])
        self.assertEqual(rows,self.movement['programs'])

    def test_actual_dispatcher_under_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-movement-') as temporary:
            directory=Path(temporary);binary=directory/'movement';table=directory/'table.bin'
            table.write_bytes(encode(self.movement['rows']))
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_room_movement_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary),str(table)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr);self.assertIn('unchanged actors pass',run.stdout)

    def test_optional_mower_with_and_without_imported_lawn(self):
        plan=browser.rules(self.image,self.report);cases=[]
        for name,ids in (('none',[]),('all',list(self.catalogue)),('mower',['GAFE01-r0/item/33A0']),
                ('mower-lawn',['GAFE01-r0/item/33A0','GAFE01-r0/item/261A'])):
            selection=composer.resolve(self.catalogue,ids)
            result,_,_=composer.compose(self.image,self.report,self.catalogue,selection)
            cases.append(dict(name=name,requested=ids,selection=selection,sha256=sha256(result)))
            if name=='none':self.assertEqual(sha256(result),self.report['translation_baseline']['sha256'])
            if name=='all':self.assertEqual(result,self.image)
            if name=='mower':self.assertEqual(selection['surface_profile_hex'],'00'*64)
        with tempfile.TemporaryDirectory(prefix='v3-movement-browser-') as temporary:
            path=Path(temporary)/'fixture.json';path.write_bytes(composer.canonical(dict(plan=plan,cases=cases,
                base=str(OUT/'animal-forest-v3-asset-loader.z64'),stable=str(composer.stable_reference(self.report)[0]))))
            run=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(path)],
                capture_output=True,text=True,timeout=60)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(len(json.loads(run.stdout)['passed']),4)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
