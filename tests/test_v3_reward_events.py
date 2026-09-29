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
OUT=ROOT/os.environ.get('V3_REWARD_EVENTS','build/v3-reward-events-prepared-06')


class RewardEventTests(unittest.TestCase):
    def test_native_reward_state_and_insertion_providers(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-state-') as temp:
            target=Path(temp)/'check'
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-Ioverlays/v3',
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
        self.assertEqual((state['storage_wire'],state['save_format'],state['unchanged_state_bytes'],
            state['unchanged_scratch_bytes']),(7,20,48,120352))
        self.assertEqual(sha256((OUT/'storage/code.bin').read_bytes()),storage['sha256'])
        self.assertLessEqual(storage['bytes'],state['retained_storage_bounds'][1]-state['retained_storage_bounds'][0])
        for name in ('af_reward_first_present','af_reward_mark_first_present',
                     'af_reward_birthday_get','af_reward_birthday_set'):
            self.assertIn(name,storage['symbols'])

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
