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
    def test_deferred_field_reward(self):
        from tests.test_v3_equipment_runtime import HostTests
        HostTests.sanitized(self,'v3_carried_world_test.c',defines=(
            '-I'+str(ROOT/'overlays/v3'),'-DAF_V3_EVENT_ITEM_PROFILE=1',
            '-DAF_V3_CARRIED_PROFILE=1','-DAF_V3_CARRIED_QUEST=1',
            '-DAF_V3_PAPER_PACKS=1','-DAF_V3_CARRIED_NPC=1'),extra=(
                'overlays/v3/carried_world.c','overlays/v3/holiday_cards.c',
                'overlays/v3/diary_calendar.c','overlays/v3/diary.c'))

    def test_voice_lifetime_and_mapped_system_sounds(self):
        from tests.test_v3_equipment_runtime import HostTests
        HostTests.sanitized(self,'v3_carried_voice_test.c',defines=(
            '-I'+str(ROOT/'overlays/v3'),),extra=('overlays/v3/carried_voice.c',))

    def test_complete_sound_batch_preserves_other_groups_and_programs(self):
        from aflib import CODE_RAM,CODE_VROM,by_vrom
        import v3_sound_programs as sounds
        out=ROOT/os.environ.get('V3_CARRIED_NPC','build/v3-carried-npc-connected-10')
        prepared=json.loads((out/'prepared.json').read_bytes());audio=prepared['audio']
        base,prior=inputs(ROOT/'build/v3-paper-quantities-installed-08/build-lock.json')
        core=by_vrom(base)[CODE_VROM].extract(base)
        original,_,_=sounds.installed_resource(base,core,'seq',199)
        sequence=(out/'carried-sequence.bin').read_bytes()
        priority=bytearray(core[0x80113B84-CODE_RAM:0x80113B84-CODE_RAM+128])
        old=prior['equipment_resources']['furniture_audio'];rows=audio['registered_programs']
        self.assertEqual([r['source_sound_word'] for r in rows],[0x6B,0x16C])
        self.assertEqual(len(rows[0]['source_program']['layers']),2)
        self.assertEqual([r['trigger_priority'] for r in rows],[70,70])
        self.assertEqual(audio['priority_changes'],[dict(address=0x80113BF9,before='28',after='46')])
        for patch in audio['priority_changes']:
            index=patch['address']-0x80113B84
            self.assertGreaterEqual(index,max(73,*(r['previous_count'] for r in old['tables'])))
            self.assertNotIn(index,[r['native_sound_word']&255 for r in old['programs']])
            priority[index]=int(patch['after'],16)
        for row in old['programs']:
            self.assertEqual(sequence[row['offset']:row['offset']+row['bytes']],
                original[row['offset']:row['offset']+row['bytes']])
        for group,at in ((2,0x2ED8),(3,0x2F6A)):
            self.assertEqual(sequence[0x188+group*2:0x18A+group*2],original[0x188+group*2:0x18A+group*2])
            self.assertEqual(sequence[at:at+146],original[at:at+146])
        combined=dict(old,programs=old['programs']+rows,tables=audio['registered_tables'])
        again,added,tables=sounds.register_triggers(sequence,[],{},
            {r['group']:r['previous_count'] for r in old['tables']},priority,bytes(128),previous=combined)
        self.assertEqual(again,sequence);self.assertEqual(added,[])
        self.assertEqual(tables,audio['registered_tables'])
        for name,row in audio['files'].items():
            data=(out/name).read_bytes()
            self.assertEqual((len(data),sha256(data)),(row['bytes'],row['sha256']))
        for row in rows:
            actual=sounds.trigger_program(sequence,row['offset'],row['offset']+row['bytes'])
            self.assertEqual(actual['events'],row['source_program']['events'])
            self.assertEqual(actual.get('layers'),row['source_program'].get('layers'))

    def test_stationery_native_consumer_preparation(self):
        from aflib import by_vrom,CODE_VROM
        from v3_carried_runtime import paper_quantity_catalogue,paper_quantity_letter,paper_quantity_supply
        from v3_submenu_tables import Owner
        out=ROOT/os.environ.get('V3_PAPER_QUANTITIES','build/v3-paper-quantities-prepared-10')
        prepared=json.loads((out/'prepared.json').read_bytes())
        image,r=inputs(ROOT/'build/v3-carried-field-work-01/quest-manager-03/build-lock.json')
        self.assertEqual(prepared['base_sha256'],sha256(image))
        self.assertEqual(prepared['base_abi'],r['runtime_abi'])
        self.assertFalse(prepared['installed'])
        for path,digest in prepared['sources'].items():
            self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        files=by_vrom(image);core=bytearray(files[CODE_VROM].extract(image))
        symbols=prepared['code']['symbols']
        bridges,supply=paper_quantity_supply(core,symbols,prepared['ram']+0x2800)
        self.assertEqual(bridges,(out/'supply-bridges.bin').read_bytes())
        self.assertEqual(supply,prepared['supply'])
        self.assertEqual(len(supply['core_patches']),5)
        self.assertEqual(supply['background_only'],[0x800A90EC,0x800A938C])
        with self.assertRaisesRegex(ValueError,'Changed paper caller'):
            paper_quantity_supply(core,symbols,prepared['ram']+0x2800)
        for name,vrom,reloc,ram,adapt in (
                ('letter',0x3B60000,0x3B70000,0x80888E90,paper_quantity_letter),
                ('catalogue',0x3970000,0x3980000,0x808A6100,
                    lambda owner:paper_quantity_catalogue(owner,symbols))):
            owner=Owner(files[vrom].extract(image),files[reloc].extract(image),ram)
            adapt(owner);data,rel,receipt=owner.finish()
            self.assertEqual(data,(out/(name+'.bin')).read_bytes())
            self.assertEqual(rel,(out/(name+'-reloc.bin')).read_bytes())
            self.assertEqual(receipt,prepared[name]['owner'])
        self.assertEqual(prepared['choice']['default'],'N64')
        self.assertEqual(prepared['choice']['values'],{'N64':0,'GameCube':1})
        self.assertEqual((prepared['save_format'],prepared['wire_version']),(18,5))
        import v3_paper_consumers as consumers
        from shop_units import SHOPS,PRICE_BIASES
        self.assertEqual(len(prepared['native_consumers']),8)
        for row in prepared['native_consumers']:
            vrom=row['vrom'];name=row['name']
            owner=consumers.native_owner(files[vrom].extract(image),files[row['reloc']].extract(image),row['ram'],
                address_constants=(PRICE_BIASES[vrom],) if vrom in PRICE_BIASES else ())
            if name=='shop-floor':actual=consumers.shop_floor(owner)
            elif name=='room-goods':actual=consumers.room_drawing(owner)
            elif name=='first-job':actual=consumers.first_job(owner,symbols)
            else:actual=consumers.shop_counter(owner,SHOPS[name[5:]])
            self.assertEqual(actual,row['hooks'])
            data,rel,receipt=owner.finish()
            self.assertEqual(data,(out/(name+'.bin')).read_bytes())
            self.assertEqual(rel,(out/(name+'-reloc.bin')).read_bytes())
            self.assertEqual(receipt,row['owner'])

    def test_stationery_temporary_lookup_registers(self):
        from v3_paper_consumers import normalize
        from tests.test_v3_house_markers import run_leaf
        for register in (2,3,4):
            words=normalize(register)+[0x03E00008,0]
            for item in (*range(0x2000,0x2045),*range(0x2E3F,0x2F01),0,0x2400,0x2E00,0x2E01,0xFFFF):
                seed=[0]+[0xABCDEF123400+i for i in range(1,32)]
                seed[register]=item;seed[31]=0x12345678
                expected=0x2000 if 0x2040<=item<0x2044 or 0x2E40<=item<0x2F00 else item
                actual=run_leaf(words,0,seed)
                self.assertEqual(actual[register],expected)
                self.assertEqual([v for i,v in enumerate(actual) if i not in (1,register)],
                    [v for i,v in enumerate(seed) if i not in (1,register)])

    def test_global_stationery_policy(self):
        from tests.test_v3_equipment_runtime import HostTests
        for mode in (0,1,2):
            HostTests.sanitized(self,'v3_carried_paper_test.c',defines=(
                '-I'+str(ROOT/'overlays/v3'),'-DAF_V3_PAPER_PACKS=1',
                '-DAF_V3_CARRIED_PROFILE=1','-DAF_V3_CARRIED_QUEST=1',
                '-DAF_V3_EVENT_ITEM_PROFILE=1','-DAF_CARRIED_PAPER_MENUS=47',
                f'-DTEST_PAPER_MODE={mode}'),extra=(
                'overlays/v3/carried_paper.c','overlays/v3/carried_items.c',
                'overlays/v3/carried_paper_supply.c',
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
        out=ROOT/os.environ.get('V3_CARRIED_NPC','build/v3-carried-npc-connected-10')
        r=json.loads((out/'prepared.json').read_bytes())
        base,prior=inputs(ROOT/'build/v3-paper-quantities-installed-08/build-lock.json')
        self.assertEqual(r['base_sha256'],sha256(base))
        for name,digest in r['generated_sha256'].items():self.assertEqual(sha256((out/name).read_bytes()),digest,name)
        self.assertEqual(sha256((out/'carried-npc.o').read_bytes()),r['object']['sha256'])
        for name,digest in r['sources'].items():self.assertEqual(sha256((ROOT/name).read_bytes()),digest,name)
        self.assertFalse(r['unbound_services']);self.assertFalse(r['installed'])
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
        self.assertEqual(r['unbound_services'],[])
        self.assertEqual((r['save_format'],r['wire_version']),(19,6))
        self.assertEqual(sha256((out/'storage/code.bin').read_bytes()),r['storage']['sha256'])
        self.assertEqual(r['bindings']['af_cw_paper_stack'],prior['equipment_resources']['carried_items'][
            'paper']['quantities']['code']['symbols']['af_cw_paper_stack'])
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
