"""Focused native-adapter and installed-action checks; no hardware claim."""
import copy
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_VROM,CODE_RAM,sha256,apply_ups,u32
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_player_exercise import checked_native
from tests.test_v3_player_exercise import complete_function


class NativeExerciseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_EXERCISE_BUILD','build/v3-player-exercise-imports-01/player-exercise-native')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.e=cls.report['equipment_resources'];cls.exercise=cls.e['player_motion']['exercise']

    def test_adapter_with_actual_source_eligibility(self):
        common=(ROOT/'local/ac-decomp/src/game/m_player_common.c_inc').read_text()
        donor='\n'.join(complete_function(common,name) for name in
            ('Player_actor_Check_InBlockRadioExercise','Player_actor_Check_AbleRadioExercise'))
        patterns=[]
        for r in self.exercise['source']['patterns']:
            keys=','.join(map(str,r['keys']+[-1]*(8-r['length'])))
            patterns.append('{{'+keys+'},'+f'{r["length"]},{r["next"]},{r["animation"]},{r["speed"]}f'+'}')
        with tempfile.TemporaryDirectory(prefix='v3-exercise-native-') as temp:
            directory=Path(temp);binary=directory/'check'
            (directory/'donor_player_exercise_native.inc').write_text(donor)
            (directory/'exercise_patterns.inc').write_text('const AFExercisePattern af_v3_exercise_patterns[18]={'+','.join(patterns)+'};\n')
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                '-fno-omit-frame-pointer','-fno-pie','-no-pie','-DAF_EXERCISE_PRIOR_INIT=0x804AC8ACu',
                '-I'+str(directory),str(ROOT/'tests/v3_player_exercise_native_test.c'),
                str(ROOT/'overlays/v3/player_exercise_native.c'),str(ROOT/'overlays/v3/player_exercise.c'),'-o',str(binary)]
            result=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('256 donor eligibility comparisons',result.stdout)

    def test_installed_complete_callbacks_and_preserved_resources(self):
        self.assertTrue(checked_native(self.image,self.report))
        files,old=by_vrom(self.image),by_vrom(self.base)
        blob,previous=files[BLOB].extract(self.image),old[BLOB].extract(self.base)
        native=self.exercise['native'];packet=native['packet']
        raw=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
        symbols=native['code']['symbols'];at=symbols['af_v3_exercise_patterns']-packet['ram']
        self.assertEqual(raw[at:at+288].hex(),self.exercise['pattern_hex'])
        for row in self.e['player_motion']['records']:
            at=row['vrom']-BLOB
            self.assertEqual(blob[at:at+row['bytes']],previous[at:at+row['bytes']])
        self.assertEqual(self.e['room_rigs'],self.prior['equipment_resources']['room_rigs'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['automatic_furniture']['imports'],self.prior['automatic_furniture']['imports'])
        self.assertEqual(self.e['player_actions']['enabled_imported_actions'],[109,111,118,119,120])
        self.assertEqual(len(native['removed_relocations']),4)
        core=files[CODE_VROM].extract(self.image);before=old[CODE_VROM].extract(self.base)
        allowed={p['address']-CODE_RAM+i for p in native['core_patches'] for i in range(4)}
        allowed.update(native['player_allocation_address']-CODE_RAM+i for i in range(4))
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(core,before,strict=True))))
        self.assertEqual(u32(core,native['player_allocation_address']-CODE_RAM),0x13E0)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(self.out/'asset-loader.ups').read_bytes()),self.image)
        self.assertFalse(native['native_execution_tested'])

    def test_checked_preload_success_and_rejection(self):
        with tempfile.TemporaryDirectory(prefix='v3-exercise-startup-') as temp:
            binary=Path(temp)/'check'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                str(ROOT/'tests/v3_player_exercise_startup_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('all eight DMA/checksum rejection paths pass',result.stdout)

    def test_current_private_compositions(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)

    def test_shared_profile_binding_recognizes_installed_interaction(self):
        from v3_furniture_pipeline import Source,rig_import_plan
        from v3_room_rig_runtime import bind_profiles
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        bindings=bind_profiles(source,self.image,self.report)
        self.assertTrue(bindings['1FCC']['indoor_aerobics_installed'])
        self.assertTrue(bindings['1FCC']['staged'])
        art=next(r['source'] for r in self.e['room_rigs']['rows'] if r.get('mode')==12)
        row=dict(art,asset_ready=True,installed=False,room_alias=False)
        for missing,expected in ((None,[]),('native',['native']),('all',['motions','native'])):
            report=copy.deepcopy(self.report)
            motion=report['equipment_resources']['player_motion']
            if missing=='native':motion['exercise']['action_installed']=False
            elif missing=='all':del motion['exercise']
            plan=rig_import_plan({'rows':[row]},report,bindings,source=source)
            self.assertEqual(plan.get('player_exercise',[]),expected)
            self.assertFalse(plan['resources'] or plan['profiles'])


if __name__=='__main__':unittest.main()
