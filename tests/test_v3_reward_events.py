"""Complete source-family conversion and shared handover transition checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
OUT=ROOT/os.environ.get('V3_REWARD_EVENTS','build/v3-reward-events-prepared-17')


class RewardEventTests(unittest.TestCase):
    def test_birthday_giver_uses_verified_native_memory_layout(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-birthday-') as temp:
            target=Path(temp)/'check'
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-Wno-unused-variable','-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(OUT),'-Ioverlays/v3',
                'tests/v3_reward_birthday_test.c','-o',str(target)]
            for cmd in (command,[str(target)]):
                run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
        report=json.loads((OUT/'prepared.json').read_text())
        self.assertEqual(len(report['birthday']['functions']),3)
        self.assertEqual(report['birthday']['item']['item'],0x1D30)
        self.assertIn('present = AF_RW_BIRTHDAY_ITEM;',(OUT/'present_demo.c').read_text())

    def test_shrine_assessment_spawning_cleanup_and_loaded_owner(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-shrine-') as temp:
            for name in ('v3_reward_shrine_test','v3_reward_shrine_owner_test'):
                target=Path(temp)/name
                command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(OUT),'-Ioverlays/v3',
                    'tests/'+name+'.c','-o',str(target)]
                for cmd in (command,[str(target)]):
                    run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                    self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_birthday_masks_and_static_mayor_use_distinct_native_paths(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-masks-') as temp:
            target=Path(temp)/'check'
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(OUT),'-Ioverlays/v3',
                '-DAF_HP_REWARD_REGISTRY=1','-DAF_HP_CARRIED_REGISTRY=1',
                'tests/v3_reward_masks_test.c','-o',str(target)]
            for cmd in (command,[str(target)]):
                run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_reward_registry_preserves_calendar_and_real_resident_admission(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-registry-') as temp:
            target=Path(temp)/'check'
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-Ioverlays/v3',
                '-DAF_HP_REWARD_REGISTRY=1','-DAF_HP_CARRIED_REGISTRY=1',
                '-DAF_HP_EXERCISE_REGISTRY=1','tests/v3_reward_registry_test.c','-o',str(target)]
            for cmd in (command,[str(target)]):
                run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_native_world_fields_and_player_event_services(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-world-') as temp:
            target=Path(temp)/'check'
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(OUT),'-Ioverlays/v3',
                'tests/v3_reward_native_world_test.c','-o',str(target)]
            for cmd in (command,[str(target)]):
                run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                if run.stdout:print(run.stdout.strip())

    def test_native_reward_state_and_insertion_providers(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-state-') as temp:
            target=Path(temp)/'check'
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-Ioverlays/v3','-I'+str(OUT),
                *('-D'+name+'=1' for name in ('AF_V3_CARRIED_PROFILE','AF_V3_CARRIED_QUEST',
                    'AF_V3_PAPER_PACKS','AF_V3_CARRIED_NPC','AF_V3_GOLDEN_REWARD_STORAGE',
                    'AF_V3_EVENT_ITEM_PROFILE'))]
            for cmd in (['cc',*flags,'tests/v3_reward_native_state_test.c',
                'overlays/v3/holiday_cards.c','overlays/v3/diary.c',
                'overlays/v3/diary_calendar.c','-o',str(target)],[str(target)]):
                run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                if run.stdout:print(run.stdout.strip())

    def test_reward_fields_use_the_actual_save_transaction_and_migrate(self):
        from tests.test_v3_carried_storage import CarriedStorageTests
        for mode in (0,1):
            CarriedStorageTests.save_transaction(self,True,mode,rewards=True,golden_rewards=True)

    def test_complete_family_and_explicit_unbound_services(self):
        report=json.loads((OUT/'prepared.json').read_text())
        self.assertEqual([r['name'] for r in report['family']],['present_demo','present_npc','npc_hem'])
        self.assertFalse(report['installed'])
        self.assertFalse(report['native_services_bound'])
        self.assertFalse(report['object']['linked'])
        self.assertTrue(report['unbound_services'])
        for name,digest in report['generated_sha256'].items():
            self.assertEqual(sha256((OUT/name).read_bytes()),digest,name)
        for family in report['family']:
            body=(OUT/(family['name']+'.c')).read_text()
            for function in family['functions']:
                self.assertIn(function['symbol']+'(',body)
        self.assertEqual(sha256((OUT/'reward-events.o').read_bytes()),report['object']['sha256'])
        state=report['native_state'];storage=state['storage']
        self.assertEqual((state['storage_wire'],state['save_format'],state['retained_state_bytes'],
            state['state_bytes'],state['retained_scratch_bytes'],state['scratch_bytes']),
            (7,20,48,64,120352,120368))
        self.assertEqual(sha256((OUT/'storage/code.bin').read_bytes()),storage['sha256'])
        self.assertLessEqual(storage['bytes'],state['storage_bounds'][1]-state['storage_bounds'][0])
        self.assertEqual(storage['symbols']['AF_HI_STORAGE_RAM'],state['storage_bounds'][0])
        self.assertEqual(storage['symbols']['af_v3_card_state'],state['state_ram'])
        self.assertNotEqual(state['storage_bounds'][0],state['retained_storage_bounds'][0])
        for name in ('af_reward_first_present','af_reward_mark_first_present',
                     'af_reward_birthday_get','af_reward_birthday_set',
                     'af_reward_good_field_get','af_reward_good_field_set'):
            self.assertIn(name,storage['symbols'])
        self.assertEqual(len(report['perfect_field']['functions']),4)
        self.assertEqual(len(report['perfect_field']['clock_reference_functions']),3)
        from v3_furniture_install import inputs
        _,prior=inputs(ROOT/'build/v3-golden-tools-selection-03/build-lock.json')
        old=prior['equipment_resources']['carried_items']['quest']['npc']['registry']
        from v3_reward_bindings import layout
        self.assertEqual(report['memory'],layout(prior))
        import copy
        bad=copy.deepcopy(prior);bad['overlap']={'ram':state['state_ram'],'bytes':16}
        with self.assertRaisesRegex(ValueError,'overlaps'):layout(bad)
        bad=copy.deepcopy(prior);bad['overlap']={'ram':0x8069F620,'bytes':16}
        with self.assertRaisesRegex(ValueError,'scratch'):layout(bad)
        registry=report['registry']
        self.assertEqual(registry['rows'][:23],old['rows'])
        self.assertEqual((registry['owner_count'],registry['resident_count'],registry['live_count']),(27,19,28))
        self.assertEqual([(r['profile'],r['name'],r['kind']) for r in registry['rows'][23:]],
            [(0xF1,0,4),(0xF2,0xD0CE,4),(0xF3,0xD0CF,5),(0xF4,0xD0D0,5)])
        self.assertTrue(registry['redirects'])
        bound=report['bindings'];pending={r.split()[-1] for r in report['unbound_services']}
        self.assertNotIn('mDemo_Set_msg_num',bound)
        self.assertIn('mDemo_Set_msg_num',pending)
        self.assertNotIn('af_hp_admit',bound)
        self.assertNotIn('af_hp_event_lookup',bound)
        self.assertFalse(any(n.startswith('mSC_LightHouse_') for n in pending))
        self.assertTrue({'af_rw_owner_active','af_rw_owner_enabled','af_rw_continue_message'}<=pending)
        self.assertNotIn('af_rw_shrine',pending)
        self.assertFalse(any(n.startswith('af_rw_native_shrine_') for n in bound))
        for n in ('lbRTC_IsOverTime','lbRTC_GetIntervalDays','lbRTC_TimeCopy',
                  'af_rw_native_rank_set','af_rw_native_rank_condition'):
            self.assertIn(n,bound)
            self.assertTrue(any(r['name']==n and r['end']>r['start'] for r in report['native_bindings']))

    def test_shared_gift_handover_is_a_single_transaction(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-events-') as temp:
            target=Path(temp)/'check'
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-unused-variable','-Wno-unused-but-set-variable',
                '-Wno-unused-function','-Wno-parentheses','-Wno-cast-function-type',
                '-ffunction-sections','-fdata-sections','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(OUT),'-Ioverlays/v3','-Wl,--gc-sections']
            for command in (['cc',*flags,'tests/v3_reward_event_test.c','-o',str(target)], [str(target)]):
                run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                if run.stdout:print(run.stdout.strip())


class RewardEffectTests(unittest.TestCase):
    def test_all_installed_and_reward_callback_packets_have_separate_bounds(self):
        from v3_holiday_sky import profile_packet
        import zlib
        import struct
        low,high=0x807C9000,0x807CA800
        for policy in ('fffe00ffc47a0cff','00c300ffc47a0cff'):
            body=profile_packet([low+4*i for i in range(4)],policy,code_bounds=(low,high))
            self.assertEqual(len(body),64)
            self.assertEqual(struct.unpack_from('>I',body,24)[0],zlib.crc32(body[:24]))
        for callbacks,policy in (([low-4]*4,'00c300ffc47a0cff'),
                                ([high]*4,'00c300ffc47a0cff'),
                                ([low+1]*4,'00c300ffc47a0cff'),
                                ([low]*4,'00c200ffc47a0cff')):
            with self.assertRaises(ValueError):profile_packet(callbacks,policy,code_bounds=(low,high))
        defines=dict(AF_EFFECT_COUNT='14u',AF_EFFECT_ROOM_COUNT='4u',AF_EFFECT_SKY_COUNT='4u',
            AF_EFFECT_PARTICIPANT_COUNT='1u',AF_EFFECT_TREE_COUNT='2u',AF_EFFECT_REWARD_COUNT='3u',
            AF_EFFECT_SKY_START='0x80738000u',AF_EFFECT_SKY_END='0x8073C000u',
            AF_EFFECT_PARTICIPANT_START='0x80750000u',AF_EFFECT_PARTICIPANT_END='0x80751000u',
            AF_EFFECT_TREE_START='0x80780000u',AF_EFFECT_TREE_END='0x80783420u',
            AF_EFFECT_REWARD_START=hex(low)+'u',AF_EFFECT_REWARD_END=hex(high)+'u')
        with tempfile.TemporaryDirectory(prefix='v3-reward-loader-') as temp:
            target=Path(temp)/'check'
            cmd=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-Ioverlays/v3',
                *('-D'+key+'='+value for key,value in defines.items()),
                'tests/v3_effect_loader_test.c','-o',str(target)]
            for command in (cmd,[str(target)]):
                run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                if run.stdout:print(run.stdout.strip())

    def test_complete_artwork_audio_and_retained_native_effect_bank(self):
        from aflib import by_vrom
        from v3_furniture_install import inputs
        from v3_furniture_pipeline import Source, prepare_models
        from tests.test_v3_furniture_pipeline import DonorTests
        out=ROOT/os.environ.get('V3_REWARD_EFFECTS','build/v3-reward-effects-prepared-05')
        report=json.loads((out/'prepared.json').read_bytes())
        self.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        base,prior=inputs(ROOT/'build/v3-golden-tools-selection-03/build-lock.json')
        old=prior['equipment_resources']['room_rigs']['effects']['bank']
        bank=(out/'effect-art-bank.bin').read_bytes()
        self.assertEqual(bank[:old['bytes']],by_vrom(base)[old['vrom']].extract(base))
        self.assertEqual(sha256(bank),report['bank']['sha256'])
        names={'sphere':'ef_sphere_light_model','light':'ef_circle_light_model'}
        for kind,name in names.items():
            asset=(out/kind/'object.bin').read_bytes()
            row=report['artwork'][kind]
            prepared=lambda _:prepare_models(self.source,dict(
                models={'model':self.source.containing(self.source.symbol(name)[0],exact=True)},
                callback_adapter=dict(category='actor-model-assets')))
            DonorTests.check_complete_artwork(self,out/kind,dict(objects=[dict(
                object_file='object.bin',object_sha256=sha256(asset),models=row['models_compiled'])]),prepared)
            self.assertEqual(asset,(ROOT/report['reused_artwork']/kind/'object.bin').read_bytes())
        self.assertEqual(len(report['audio']['programs']),2)
        for name,digest in report['generated_sha256'].items():
            self.assertEqual(sha256((out/name).read_bytes()),digest)
        self.assertEqual(sha256((out/'reward-effects.o').read_bytes()),report['object']['sha256'])
        self.assertFalse(report['installed'])

    def test_source_family_and_native_service_lifetimes(self):
        from v3_reward_effects import generate
        from v3_furniture_pipeline import Source
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        generated,contract=generate(source)
        self.assertEqual(len(contract['functions']),12)
        self.assertEqual([(r['source_id'],r['native_id'],r['unique']) for r in contract['profiles']],
            [(123,122,1),(124,123,0),(125,124,1)])
        with tempfile.TemporaryDirectory(prefix='v3-reward-effects-') as temp:
            from apply_translation import write_new
            out=Path(temp);write_new(out/'source.c',generated.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-misleading-indentation','-fno-pie','-no-pie',
                '-fsanitize=address,undefined,float-cast-overflow','-fno-omit-frame-pointer',
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(out),
                'tests/v3_reward_effects_test.c','-lm','-o',str(out/'check')]
            for cmd in (command,[str(out/'check')]):
                run=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                if run.stdout:print(run.stdout.strip())


if __name__=='__main__':unittest.main()
