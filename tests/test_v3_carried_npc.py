"""Focused changed NPC preparation and shared service checks; no old ROM replay."""
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
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source


class CarriedNpcTests(unittest.TestCase):
    def test_global_stationery_policy(self):
        from tests.test_v3_equipment_runtime import HostTests
        for mode in (0,1,2):
            HostTests.sanitized(self,'v3_carried_paper_test.c',defines=(
                '-I'+str(ROOT/'overlays/v3'),'-DAF_V3_PAPER_PACKS=1',
                '-DAF_V3_CARRIED_PROFILE=1','-DAF_V3_CARRIED_QUEST=1',
                '-DAF_V3_EVENT_ITEM_PROFILE=1','-DAF_CARRIED_PAPER_MENUS=47',
                f'-DTEST_PAPER_MODE={mode}'),extra=(
                'overlays/v3/carried_paper.c','overlays/v3/carried_items.c',
                'overlays/v3/carried_collection.c','overlays/v3/holiday_cards.c',
                'overlays/v3/diary.c','overlays/v3/diary_calendar.c','overlays/v3/carried_actions.c'))

    def test_retained_registry_lifecycle(self):
        # This shared source changed; verify its original-family configuration
        # without rebuilding or replaying any previous cartridge.
        with tempfile.TemporaryDirectory(prefix='carried-registry-') as directory:
            binary=Path(directory)/'check'
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-I'+str(ROOT/'overlays/v3'),
                str(ROOT/'tests/v3_holiday_participants_test.c'),
                str(ROOT/'overlays/v3/holiday_participants_registry.c'),'-o',str(binary)]
            result=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)

    def test_changed_registry_and_native_fields(self):
        from tests.test_v3_equipment_runtime import HostTests
        for available in (0,1):
            HostTests.sanitized(self,'v3_carried_npc_test.c',defines=(
                '-I'+str(ROOT/'overlays/v3'),
                '-DAF_HP_EXERCISE_REGISTRY=1','-DAF_HP_FESTIVAL_REGISTRY=1',
                '-DAF_HP_CARRIED_REGISTRY=1',f'-DAF_HP_TEST_AVAILABLE={available}'),
                extra=('overlays/v3/carried_npc.c','overlays/v3/holiday_participants_registry.c'))

    def test_complete_actor_motion_and_official_text(self):
        from v3_keyframes import npc_expression_motion,compile_animations
        from v3_holiday_participants import dialogue,carried_conversation
        from textvalidate import expanded_bound
        from runtime_module import module_command_info
        from textbanks import Bank
        out=ROOT/os.environ.get('V3_CARRIED_NPC','build/v3-carried-npc-connected-08')
        r=json.loads((out/'prepared.json').read_bytes())
        base,prior=inputs(ROOT/'build/v3-carried-field-work-01/quest-manager-03/build-lock.json')
        self.assertEqual(r['base_sha256'],sha256(base))
        for name,digest in r['generated_sha256'].items():self.assertEqual(sha256((out/name).read_bytes()),digest,name)
        self.assertEqual(sha256((out/'carried-npc.o').read_bytes()),r['object']['sha256'])
        for name,digest in r['sources'].items():self.assertEqual(sha256((ROOT/name).read_bytes()),digest,name)
        self.assertTrue(r['unbound_services']);self.assertFalse(r['installed'])
        old=prior['equipment_resources']['npc_extra']['events']['festivals']
        self.assertEqual(r['registry']['rows'][:-1],old['registry']['rows'])
        self.assertEqual(r['registry']['rows'][-1]['profile'],0xF0)
        self.assertEqual(r['registry']['rows'][-1]['event'],114)
        prepared=ROOT/r['source_prepared'];source=(prepared/'ev_ghost.c').read_text()
        body=(out/'ev_ghost.c').read_text()
        self.assertEqual(body,carried_conversation(source.replace('default_animation = 126;', 'default_animation = 382;')
            .replace('aNPC_ANIM_GSTWAIT1','382')))
        generated={};text=dialogue(base,prior,generated,roots=range(0x2ED3,0x2F03),
            map_symbol='af_cw_message',carried_controls=True)
        recorded=copy.deepcopy(r['dialogue'])
        recorded['provenance_entries']=recorded['provenance_entries'][:len(text['provenance_entries'])]
        self.assertEqual(json.loads(json.dumps(text)),recorded)
        self.assertEqual(text['count'],48);self.assertEqual(text['choice_count'],16)
        self.assertEqual(text['branch_added'],[]);self.assertEqual(text['redundant_colours'],{0x2EE4:10})
        messages=Bank('message',0,0,generated['messages.bin'],generated['message-table.bin']).entries()
        self.assertLessEqual(max(expanded_bound(messages[row['id']],module_command_info(base))
            for row in text['rows']),1024)
        self.assertEqual(len(r['strings']),33)
        from v3_holiday_dialogue import check_provenance
        check_provenance(r['dialogue'])
        rel=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        at,_=rel.symbol('cKF_ba_r_npc_1_gstwait1');motion=npc_expression_motion(rel,at,joints=26)
        self.assertEqual(motion['npc_expressions']['eye_type'],1)
        self.assertEqual(motion['npc_expressions']['eye_stop'],-1)
        converted,report=compile_animations(rel,[motion],address_base=0)
        header=report['headers'][0]['native_offset']
        self.assertEqual(converted[header+16:header+64],rel.data[at+16:at+64])
        self.assertEqual(converted,(out/'festival-motions.bin').read_bytes())
        self.assertEqual(len(r['reward_lists']),20)
        for row in r['reward_lists']:
            self.assertEqual(sha256(rel.raw(row['symbol'])),row['source_sha256'])
        mapped=r['reward_destinations']['rows']
        self.assertEqual(len(mapped),1000)
        self.assertEqual(len({row['source_item'] for row in mapped}),1000)
        by_source={row['source_item']:row for row in mapped}
        self.assertEqual((by_source[0x20C0]['item'],by_source[0x20C0]['quantity']),(0x2000,4))
        self.assertEqual((by_source[0x20C3]['item'],by_source[0x20C3]['quantity']),(0x2043,1))
        self.assertTrue(all(row['item']<0x3000 for row in mapped if row['evidence']=='pinned native counterpart'))
        self.assertIn('af_cw_paper_stack',' '.join(r['unbound_services']))
        bad=copy.copy(rel);raw=bytearray(rel.data);struct.pack_into('>h',raw,at+40,0);bad.data=bytes(raw)
        with self.assertRaisesRegex(ValueError,'expression'):npc_expression_motion(bad,at,joints=26)

    def test_complete_reward_and_handover_path(self):
        from tests.test_v3_equipment_runtime import HostTests
        from v3_password_policy import function
        from apply_translation import write_new
        out=ROOT/os.environ.get('V3_CARRIED_NPC','build/v3-carried-npc-connected-08')
        source=(out/'ev_ghost.c').read_text()
        # Test complete actual functions, without retaining the unused actor
        # profile through ASan's global registry or weakening sanitizer checks.
        prefix=source[:source.index('static void aEGH_actor_ct(ACTOR*, GAME*);')]
        arrays=source[source.index('extern mActor_name_t ftr_listA[];'):
            source.index('static mActor_name_t aEGH_not_collect_get()')]
        names=('aEGH_change_talk_proc','aEGH_delete_hitodama','aEGH_get_collect',
            'aEGH_check_collect_num','aEGH_not_collect_get','aEGH_give_me_wait','aEGH_give_you_wait')
        # The reward helper functions precede the array declarations, so each
        # complete function is included once, not copied into a handwritten stub.
        with tempfile.TemporaryDirectory(prefix='carried-conversation-') as directory:
            write_new(Path(directory)/'carried-conversation-under-test.c',
                (prefix+arrays+'\n'+'\n'.join(function(source,n) for n in names)).encode())
            HostTests.sanitized(self,'v3_carried_conversation_test.c',defines=(
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(out),'-I'+directory,
                '-Wno-unused-function','-Wno-unused-variable','-Wno-unused-but-set-variable',
                '-Wno-unused-parameter','-Wno-parentheses'),extra=(
                    'overlays/v3/carried_rewards.c','overlays/v3/carried_dialogue.c',
                    'overlays/v3/carried_handover.c',str(out/'reward-map.c'),
                    str(out/'reward-lists.c'),str(out/'strings.c')))


if __name__=='__main__':unittest.main()
