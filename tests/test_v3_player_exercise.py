"""Bounded category verification for gestures and complete shared motion banks."""
import copy
import json
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,u32
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_player_exercise import source_contract,pattern_bytes,motions,grow_animation_banks
from v3_equipment_runtime import PLAYER_TABLE,PLAYER_CAPACITY,FACE_TABLE,FACE_DATA,player_face_sources

OUT=ROOT/'build/v3-player-exercise-resources-03'
BASE=ROOT/'build/v3-room-music-imports-04/profile-runtime'


def complete_function(text,name):
    at=text.index(name+'(');start=text.rfind('\n',0,at)+1;begin=text.index('{',at)
    depth=1;end=begin+1
    while depth:
        if text[end]=='{':depth+=1
        elif text[end]=='}':depth-=1
        end+=1
    return text[start:end]


class ExerciseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.contract=source_contract(cls.source)

    def test_complete_source_tables_and_all_animation_channels(self):
        self.assertEqual(len(self.contract['functions']),21)
        self.assertEqual(len(self.contract['patterns']),18)
        self.assertEqual(len(pattern_bytes(self.contract)),288)
        assets,rows,_=motions(self.source,self.contract)
        self.assertEqual(sorted(assets),list(range(144,156)))
        self.assertEqual([r['source']['duration'] for r in rows],[81]*3+[161]+[81]*8)
        self.assertTrue(all(r['source']['joints']==26 for r in rows))
        self.assertEqual(max(map(len,assets.values())),4848)
        self.assertEqual(sum(map(len,assets.values())),23568)
        broken=copy.copy(self.source);raw=bytearray(broken.rel)
        raw[self.source.sections[1][0]+0x196C8C]^=1;broken.rel=bytes(raw)
        with self.assertRaises(ValueError):source_contract(broken)

    def test_core_against_actual_donor_and_extended_readers(self):
        common=(ROOT/'local/ac-decomp/src/game/m_player_common.c_inc').read_text()
        action=(ROOT/'local/ac-decomp/src/game/m_player_main_radio_exercise.c_inc').read_text()
        first=common.index('static int Player_actor_Get_RadioExerciseCommandRingBufferIndex(')
        last=common.index('static void Player_actor_Set_old_sound_frame_counter(',first)
        donor=common[first:last]+'\n'+complete_function(action,'Player_actor_CulcAnimation_Radio_exercise')
        donor+='\n'+complete_function(action,'Player_actor_request_proc_index_fromRadio_exercise')
        rows=[]
        for r in self.contract['patterns']:
            keys=','.join(map(str,r['keys']+[-1]*(8-r['length'])))
            rows.append('{{'+keys+'},'+f'{r["length"]},{r["next"]},{r["animation"]},{r["speed"]}f'+'}')
        with tempfile.TemporaryDirectory(prefix='v3-player-exercise-') as temp:
            directory=Path(temp);binary=directory/'check'
            (directory/'donor_player_exercise.inc').write_text(donor)
            (directory/'exercise_patterns.inc').write_text('static const AFExercisePattern patterns[18]={'+','.join(rows)+'};\n')
            command=['cc','-std=gnu11','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-function',
                '-ffp-contract=off','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-fno-pie','-no-pie','-I'+str(directory),str(ROOT/'tests/v3_player_exercise_test.c'),'-o',str(binary)]
            run=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())
        from tests.test_v3_equipment_runtime import HostTests
        HostTests.sanitized(self,'v3_equipment_resources_test.c',defines=(
            '-DAF_V3_PLAYER_MOTION=1','-DAF_V3_PLAYER_CAPACITY=4848u','-DAF_V3_PLAYER_RESOURCE_END=0x02800000u'))


class InstalledExerciseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=OUT
        cls.image,cls.report=inputs(OUT/'build-lock.json');cls.base,cls.prior=inputs(BASE/'build-lock.json')
        cls.source=ExerciseTests.source if hasattr(ExerciseTests,'source') else Source(
            (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.files=by_vrom(cls.image);cls.before=by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.blob=cls.files[BLOB].extract(cls.image);cls.previous=cls.before[BLOB].extract(cls.base)

    def test_complete_installed_motions_buffers_and_retained_resources(self):
        exercise=self.e['player_motion']['exercise'];contract=source_contract(self.source)
        self.assertEqual(exercise['source'],json.loads(json.dumps(contract)))
        assets,rows,_=motions(self.source,contract);start=self.e['blob_offset']
        module=self.blob[start:start+self.e['bytes']];previous=self.previous[start:start+self.old['bytes']]
        restored=bytearray(module);restored[:self.e['code']['bytes']]=previous[:self.old['code']['bytes']]
        for row in exercise['records']:
            at=row['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],assets[row['source_index']])
            self.assertLessEqual(row['bytes'],4848)
            offset=PLAYER_TABLE+16+row['source_index']*16
            self.assertEqual(struct.unpack_from('>4I',module,offset),(row['vrom'],row['bytes'],row['pointer'],row['type']))
            restored[offset:offset+16]=previous[offset:offset+16]
        self.assertEqual(restored,previous)
        for row in self.old['records']+self.old['player_motion']['records']:
            at=row['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],self.previous[at:at+row['bytes']])
        table,data,faces=player_face_sources(self.source,self.e['player_motion']['records'])
        self.assertEqual(module[FACE_TABLE:FACE_TABLE+len(table)],table)
        self.assertEqual(module[FACE_DATA:FACE_DATA+len(data)],data)
        self.assertEqual(len(data),213)
        self.assertEqual(self.e['code']['symbols'],self.old['code']['symbols'])
        core=bytearray(self.files[CODE_VROM].extract(self.image));old_core=self.before[CODE_VROM].extract(self.base)
        allocation=self.e['player_motion']['allocation'];self.assertEqual(allocation['additional_scene_bytes'],1984)
        for patch in allocation['patches']:
            at=patch['address']-CODE_RAM;self.assertEqual(core[at:at+4].hex(),patch['after'])
            core[at:at+4]=bytes.fromhex(patch['before'])
        self.assertEqual(core,old_core)
        self.assertEqual(self.e['player_actions'],self.old['player_actions'])
        self.assertEqual(self.e['room_rigs'],self.old['room_rigs'])
        self.assertFalse(exercise['action_installed']);self.assertFalse(exercise['prepared_core_installed'])
        self.assertEqual(self.e['bytes'],self.old['bytes'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        rejected=bytearray(old_core);rejected[0x800B121C-CODE_RAM]^=1
        with self.assertRaises(ValueError):grow_animation_banks(original,self.base,self.prior,rejected,4848)
        self.assertEqual(apply_ups(original,(OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_current_private_composition_preserves_choices_and_translation_only(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)
