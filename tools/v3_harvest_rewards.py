"""Complete Harvest reward owner through the shared source/native adapter.

Preparation preserves all actor functions, twelve reward identities, and full
official dialogue. It does not enable the actor or manufacture acquisition.
"""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source
from v3_holiday_participants import DONOR,generate,dialogue,native_motions

HEADERS=('m_private.h','m_item_name.h','m_player_lib.h','ac_handOverItem.h')
REFERENCES_SHA='2f9bbba4527746a0d0cc1cc318d602634f0337ae8bab268e54995c68a5b556ca'
PRESENT_SHA='e90ae9245e80c9bd88b71d4a8f436558138e478eb25960b8163c54e4618a50f3'
STOCK_SHA='ec5cd3d31e3bc843237705b551cf71ee2aa26f6fc768c82badb3be85eac8d4be'
SOURCES=('tools/v3_harvest_rewards.py','tools/v3_holiday_participants.py',
    'tools/v3_item_destinations.py','tools/v3_keyframes.py','overlays/v3/harvest_event.h',
    'overlays/v3/harvest_state.h','overlays/v3/harvest_state.c',
    'overlays/v3/harvest_dialogue.c','overlays/v3/harvest_world_native.c',
    'overlays/v3/carried_handover.c','overlays/v3/carried_npc.c',
    'overlays/v3/holiday_participants.h','overlays/v3/holiday_participants_registry.c',
    'overlays/v3/holiday_participants_storage.c','overlays/v3/holiday_participants_services.c',
    'overlays/v3/holiday_participants_spawn.S','overlays/v3/holiday_festival_motion.c',
    'overlays/v3/npc_registry.h','overlays/v3/npc_registry_limits.h','tools/v3_registry.py')


def shared_registry(image,prior,source,generated):
    """Extend the active whole registry, retaining every compiled source owner."""
    from v3_registry import SPECIAL_NPCS
    previous=prior['equipment_resources']['carried_items']['quest']['rewards']
    packet=previous['packet'];symbols=previous['code']['symbols']
    raw=image[packet['physical']:packet['physical']+packet['bytes']]
    rows=[dict(row) for row in previous['registry']['rows']]
    if (sha256(raw)!=packet['sha256'] or len(rows)!=27 or
            previous['registry']['resident_count']!=19 or previous['registry']['live_count']!=28):
        raise ValueError('Changed complete active reward registry')
    at=symbols['af_hp_records']-packet['ram'];retained=raw[at:at+20*len(rows)]
    if len(retained)!=20*len(rows):raise ValueError('Truncated whole participant table')
    lines=['#include "harvest_event.h"','extern ACTOR_PROFILE Ev_Turkey_Profile;',
        'const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={']
    for index,row in enumerate(rows):
        record=struct.unpack_from('>4H4B2I',retained,index*20)
        fields=tuple(row[k] for k in ('source','name','profile','event','save','count','part','kind'))
        pointer=symbols[row['donor_profile']]
        if record!=fields+(pointer,row['flags']):
            raise ValueError('Changed retained complete participant: '+row['donor_profile'])
        row['source_pointer']=pointer
        lines.append('{'+','.join(map(str,fields))+f',(const ACTOR_PROFILE *)0x{pointer:X},'+str(row['flags'])+'},')
    identity=SPECIAL_NPCS['GAFE01-r0/npc/ev-turkey']
    profile=source.raw('Ev_Turkey_Profile')
    if len(profile)!=36 or struct.unpack_from('>H',profile)[0]!=identity['donor_profile']:
        raise ValueError('Changed complete Franklin source profile')
    added=dict(source=identity['donor_name'],name=identity['name'],profile=identity['profile'],
        event=108,save=0,count=1,part=3,kind=1,donor_profile='Ev_Turkey_Profile',
        flags=struct.unpack_from('>I',profile,4)[0],donor_profile_sha256=sha256(profile))
    if any(added['profile']==r['profile'] or
            (r['count'] and r['name']<=added['name']<r['name']+r['count']) for r in rows):
        raise ValueError('Franklin overlaps an installed participant')
    rows.append(added)
    lines.append('{'+','.join(str(added[k]) for k in ('source','name','profile','event','save','count','part','kind'))+
        ',&Ev_Turkey_Profile,'+str(added['flags'])+'},')
    profiles={r['name']+i:r['profile'] for r in rows for i in range(r['count'])}
    if sorted(profiles)!=list(range(0xD0A0,0xD0D2)):
        raise ValueError('Incomplete connected participant spawn identities')
    lines+=['};','const s16 af_hp_spawn_profiles[]={'+','.join(str(profiles[n]) for n in sorted(profiles))+'};']
    generated['registry.c']='\n'.join(lines)+'\n'
    names=tuple(previous['registry']['redirects'])+('af_hp_spawn_profile','mEv_get_save_area',
        'mEv_reserve_save_area','af_hp_owner_enabled')
    return dict(rows=rows,owner_count=28,resident_count=19,live_count=29,
        retained_table_sha256=sha256(retained),source_packet_sha256=packet['sha256'],
        redirects={name:symbols[name] for name in names},installed=False)


def shared_motions(image,prior,generated,imported):
    """Add a complete motion without reconverting any retained programme."""
    previous=prior['equipment_resources']['carried_items']['quest']['npc']
    packet=previous['packet'];raw=image[packet['physical']:packet['physical']+packet['bytes']]
    if sha256(raw)!=packet['sha256']:raise ValueError('Changed complete shared motion owner')
    at=previous['code']['symbols']['af_hg_motions']-packet['ram']
    count=struct.unpack_from('>I',raw,at)[0]
    if count!=4:raise ValueError('Changed retained motion category count')
    table=raw[at:at+4+count*8]
    rows=list(struct.iter_unpack('>II',table[4:]))
    if {index for index,pointer in rows}!={328,329,330,382}:
        raise ValueError('Changed retained motion identities')
    new=[row for row in imported if row.get('imported')]
    if len(new)!=1 or new[0]['native']['index']!=385:
        raise ValueError('Changed complete Franklin motion identity')
    assembly=generated['harvest-motions.S']
    before='af_hr_motions:\n.word 1\n'
    if assembly.count(before)!=1:raise ValueError('Changed complete generated motion table')
    assembly=assembly.replace('af_hr_motions','af_hg_motions').replace(
        'af_hg_motions:\n.word 1\n',f'af_hg_motions:\n.word {count+1}\n')
    generated['harvest-motions.S']=assembly+''.join(f'.word {index}, 0x{pointer:X}\n' for index,pointer in rows)
    return dict(retained=[dict(index=index,header=pointer) for index,pointer in rows],
        added=[385],retained_table_sha256=sha256(table),source_packet_sha256=packet['sha256'],
        redirect=previous['code']['symbols']['af_hg_animation'],installed=False)


def rewards(source):
    pattern=r'^aETKY_present_table = \.rodata:0x00008B40;[^\n]*size:0x18 '
    if len(re.findall(pattern,source.symbols,re.M))!=1:
        raise ValueError('Changed complete Harvest reward-table symbol')
    start=source.sections[4][0]+0x8B40;raw=source.rel[start:start+24]
    stock=source.raw('ftr_listHarvest')
    if sha256(raw)!=PRESENT_SHA or sha256(stock)!=STOCK_SHA:
        raise ValueError('Changed complete Harvest reward family')
    values=list(struct.unpack('>12H',raw));members=list(struct.unpack('>11H',stock))
    if (len(set(values))!=12 or members!=values[:10]+[0] or
            [item>>8 for item in values[10:]]!=[0x26,0x27]):
        raise ValueError('Incomplete Harvest furniture/surface category')
    return values,dict(symbol='aETKY_present_table',section=4,offset=0x8B40,
        bytes=len(raw),sha256=PRESENT_SHA,stock_symbol='ftr_listHarvest',stock_sha256=STOCK_SHA)


def actor(source):
    generated,report=generate(source,family=('ev_turkey',),
        reference_sha=REFERENCES_SHA,extra_headers=HEADERS)
    body=generated['ev_turkey.c'];adaptations=[]
    changes=(
        ('#include "holiday_participants.h"','#include "harvest_event.h"',1),
        ('Now_Private','af_cw_private()',4),
        ('gamePT->frame_counter','af_hr_frame()',1),
        ('GET_PLAYER_ACTOR_GAME_ACTOR(game)','af_cw_player_actor(game)',3),
        ('GET_PLAYER_ACTOR_NOW()->Set_force_position_angle_proc(gamePT, NULL, &pl_angle, mPlayer_FORCE_POSITION_ANGLE_ROTY)',
         'af_hr_force_angle(af_hr_game(), NULL, &pl_angle, mPlayer_FORCE_POSITION_ANGLE_ROTY)',1),
        ('CLIP(handOverItem_clip)->master_actor','af_cw_handover_master()',1),
        ('NPC_CLIP->save_proc','af_rw_npc_save',1),
        ('msg_no == 0x3BFD + talk_action','msg_no == af_hr_message(0x3BFD + talk_action)',1),
        ('aETKY_present_table[present_idx]','af_hr_reward(present_idx)',1),
        ('aETKY_present_table[turkey->present_idx]','af_hr_reward(turkey->present_idx)',1),
        ('        bzero(save_p, sizeof(aEv_turkey_save_c));',
         '        if (save_p == NULL) { turkey->ev_save_p = NULL; return; }\n'
         '        bzero(save_p, sizeof(aEv_turkey_save_c));',1),
        ('        turkey->ev_common_p = common_p;\n        common_p->_01 = 0;',
         '        turkey->ev_common_p = common_p;\n'
         '        if (common_p == NULL) return;\n        common_p->_01 = 0;',1),
        ('        aETKY_SetupCommonData(actorx);',
         '        if (turkey->ev_save_p == NULL) { Actor_delete(actorx); return; }\n'
         '        aETKY_SetupCommonData(actorx);\n'
         '        if (turkey->ev_common_p == NULL) { Actor_delete(actorx); return; }',1),
        ('    int dont_have_count = 0;',
         '    u16 eligible = (u16)af_hr_enabled_mask();\n'
         '    if (!given_bitfield || !eligible || (eligible & ~aETKY_ALL_BITS) ||\n'
         '        (*given_bitfield & ~aETKY_ALL_BITS)) return -1;\n'
         '    int dont_have_count = 0;',1),
        ('(*given_bitfield & aETKY_ALL_BITS) == aETKY_ALL_BITS',
         '(*given_bitfield & eligible) == eligible',1),
        ('        *given_bitfield = 0;','        *given_bitfield &= (u16)~eligible;',1),
        ('if (((*given_bitfield >> i) & 1) == 0)',
         'if ((eligible & (1u << i)) && ((*given_bitfield >> i) & 1) == 0)',2),
        ('        turkey->present_idx = aETKY_DecidePresent(&turkey->ev_save_p->given_present_bitfield);',
         '        int selected = aETKY_DecidePresent(&turkey->ev_save_p->given_present_bitfield);\n'
         '        if (selected < 0) { Actor_delete(actorx); return; }\n'
         '        turkey->present_idx = (u8)selected;',1),
        ('        aNPC_DEMO_GIVE_ITEM(present, aHOI_REQUEST_PUTAWAY, FALSE);\n'
         '        mPr_SetFreePossessionItem(af_cw_private(), present, mPr_ITEM_COND_NORMAL);',
         '        if (!af_hr_insert(af_cw_private(), present, mPr_ITEM_COND_NORMAL)) return;\n'
         '        aNPC_DEMO_GIVE_ITEM(present, aHOI_REQUEST_PUTAWAY, FALSE);',1),
        ('        aETKY_ReportPresent(&turkey->ev_save_p->given_present_bitfield, turkey->present_idx);',
         '        aETKY_ReportPresent(&turkey->ev_save_p->given_present_bitfield, turkey->present_idx);\n'
         '        af_hr_report(turkey->present_idx, turkey->ev_save_p->given_present_bitfield);',1),
    )
    for before,after,count in changes:
        if body.count(before)!=count:
            raise ValueError('Changed complete Harvest adaptation: '+repr(before))
        body=body.replace(before,after)
        adaptations.append(dict(source=before,native=after,count=count))
    # Actor-header inclusion precedes source constants; its owned event record
    # uses a complete opaque source identity, not the smaller native Private ID.
    generated['ev_turkey.c']=body
    saved_view='typedef struct {\n    PersonalID_c pid;\n    u16 given_present_bitfield;\n} aEv_turkey_save_c;'
    if generated['actors.h'].count(saved_view)!=1:
        raise ValueError('Changed complete Harvest saved-record view')
    generated['actors.h']=generated['actors.h'].replace(saved_view,
        'typedef AFHarvestSaved aEv_turkey_save_c;')
    constants=generated['constants.h']
    if not constants.endswith('#endif\n'):
        raise ValueError('Changed complete Harvest constant guard')
    generated['constants.h']=constants[:-7]+(
        '#define mEv_get_save_area af_hr_get_save\n'
        '#define mEv_reserve_save_area af_hr_reserve_save\n'
        '#define mEv_get_common_area af_hr_get_common\n'
        '#define mEv_reserve_common_area af_hr_reserve_common\n'
        '#define mEv_set_status af_hr_set_status\n'
        '#define mEv_actor_dying_message af_hr_dying\n'
        '#define mDemo_Set_msg_num af_hr_begin_message\n'
        '#define af_hp_continue_message af_hr_continue_message\n'
        '#define mPr_ClearPersonalID af_hr_clear_personal_id\n#endif\n')
    if re.search(r'\b(?:Common_Get|Save_Get|Now_Private|gamePT|GET_PLAYER_ACTOR_NOW)\b',body):
        raise ValueError('Unmapped Harvest source state')
    report.update(platform_adaptations=adaptations)
    return generated,report


def native_contract(image,prior):
    """Pin complete native event services and the real player callback pair."""
    from aflib import CODE_RAM,CODE_VROM,by_vrom,verified_rom
    from v3_holiday_participants import bindings
    direct=dict(af_cw_native_get_save=0x8008033C,af_cw_native_reserve_save=0x80080080,
        af_cw_native_get_common=0x800808E0,af_cw_native_reserve_common=0x800807E0,
        af_hr_native_set_status=0x8007FDA8,mMsg_Get_msg_num=0x8009DBB0,
        mDemo_Check_ListenAble=0x8007D0EC,add_calc=0x8009A570,
        add_calc_short_angle2=0x8009A974,sqrtf=0x80033470)
    _,evidence=bindings(image,prior,extra=direct)
    native=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    installed,retail=by_vrom(image),by_vrom(native)
    bodies=[r for r in evidence if r['name'] in direct]
    directory_moves={
        0x8008009C:(0x3C0E8014,0x3C0E804A),0x800800A4:(0x91CEA098,0x91CE2B00),
        0x800800A8:(0x3C188014,0x3C18806F),0x800800AC:(0x27189F98,0x27181500),
        0x8007FDB4:(0x3C038014,0x3C03804A),0x8007FDBC:(0x9063A098,0x90632B00),
        0x8007FDC0:(0x3C0F8014,0x3C0F806F),0x8007FDC4:(0x25EF9F98,0x25EF1500)}
    for row in bodies:
        raw=bytearray(retail[row['vrom']].extract(native)[row['start']-row['ram']:row['end']-row['ram']])
        moved=[]
        for at,(before,after) in directory_moves.items():
            if not row['start']<=at<row['end']:continue
            if struct.unpack_from('>I',raw,at-row['start'])[0]!=before:
                raise ValueError('Changed original event-directory reader')
            struct.pack_into('>I',raw,at-row['start'],after)
            moved.append(dict(address=at,before=before,after=after))
        if sha256(raw)!=row['sha256']:
            raise ValueError('Changed complete native Harvest service: '+row['name'])
        row['retained_directory_moves']=moved
    owner=installed[0x7AC420].extract(image);original=retail[0x7AC420].extract(native)
    # Constructor stores this native pair at player 123C/1240. The complete
    # setter/getter preserve source masks and queue position/angle at 113C/1148.
    player=[]
    for name,start,end in (('player_force_angle_set',0x808B606C,0x808B612C),
            ('player_force_angle_reset',0x808B612C,0x808B6138),
            ('player_force_angle_get',0x808B6138,0x808B61E4)):
        at,stop=start-0x808B2D50,end-0x808B2D50
        raw=owner[at:stop]
        if raw!=original[at:stop] or len(raw)!=end-start:
            raise ValueError('Changed complete native player angle callback')
        player.append(dict(name=name,start=start,end=end,vrom=0x7AC420,ram=0x808B2D50,
            sha256=sha256(raw),binding='native player-owned relocated callback, not an absolute overlay call'))
    anchors={0x808DD5C8:0x2739606C,0x808DD5CC:0x25086138,
        0x808DD5F0:0xAE19123C,0x808DD5F4:0xAE081240,
        0x808B60F4:0x306B0040,0x808B60FC:0xA44A114A}
    if any(struct.unpack_from('>I',owner,at-0x808B2D50)[0]!=word for at,word in anchors.items()):
        raise ValueError('Changed native player angle callback installation/masks')
    core=installed[CODE_VROM].extract(image)
    event_anchors={0x8008013C:0x28610005,0x80080194:0xA0500018,
        0x80080198:0xA0510019,0x800801A4:0x24440020,0x800801B4:0x24060028,
        0x80080864:0x28410005,0x800808A0:0x24060028}
    if any(struct.unpack_from('>I',core,at-CODE_RAM)[0]!=word for at,word in event_anchors.items()):
        raise ValueError('Changed native event saved/common area capacity')
    direct.update(af_hr_native_game=0x8010EF90,af_holiday_native_days=0x806F1500,
        af_holiday_native_index=0x804A2B00,af_holiday_native_count=0x80104F98)
    return dict(bindings=direct,native_services=bodies,player_callbacks=player,
        player_callback_offset=0x123C,source_y_rotation_mask=32,
        event_areas=dict(saved_slots=5,common_slots=5,stride=48,data_bytes=40,
            saved_data=0x80135D00,common_data=0x80137694,source_saved_bytes=22,source_common_bytes=3),
        installed=False)


def prepare(output,lock):
    from v3_furniture_install import inputs
    from v3_item_destinations import destinations
    out=output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'build'):
        raise ValueError('Use a fresh ignored connected Harvest preparation')
    image,prior=inputs(lock)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (DONOR/'config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,report=actor(source);items,table=rewards(source)
    report['native_contract']=native_contract(image,prior)
    report['motions']=native_motions(source,image,generated,import_missing=True)
    if 'festival-motions.S' in generated:
        generated['harvest-motions.S']=generated.pop('festival-motions.S').replace(
            'af_hg_','af_hr_').replace('festival-motions.bin','harvest-motions.bin')
        generated['harvest-motions.bin']=generated.pop('festival-motions.bin')
    report['shared_motions']=shared_motions(image,prior,generated,report['motions'])
    report['registry']=shared_registry(image,prior,source,generated)
    mapped=destinations(image,prior,items,lock=lock)
    by_source={row['source_item']:row for row in mapped}
    ordered=[dict(by_source[item],index=index) for index,item in enumerate(items)]
    generated['reward-map.c']=('#include "harvest_event.h"\n'
        'const u16 af_hr_reward_items[12]={'+','.join(str(r['item']) for r in ordered)+'};\n'
        'const u16 af_hr_source_items[12]={'+','.join(map(str,items))+'};\n')
    generated['layout.c']=('#include "harvest_event.h"\n#include "constants.h"\n#include "actors.h"\n'
        '_Static_assert(sizeof(aEv_turkey_save_c)==22,"Complete source Harvest saved area");\n'
        'const u32 af_hr_layout[]={sizeof(EV_TURKEY_ACTOR),sizeof(aEv_turkey_save_c),'
        'sizeof(aEv_turkey_common_c),mEv_EVENT_HARVEST_FESTIVAL_FRANKLIN,'
        'mAc_PROFILE_EV_TURKEY,aNPC_ANIM_TKYKYORO1,mPlayer_FORCE_POSITION_ANGLE_ROTY};\n')
    text=dialogue(image,prior,generated,roots=set(range(0x3BFE,0x3C22)),
        map_symbol='af_hr_message',carried_controls=True,reward_controls=True,festival_controls=True)
    out.mkdir(parents=True)
    for name,data in generated.items():
        write_new(out/name,data if isinstance(data,bytes) else data.encode())
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
        '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
        '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror',
        '-Wno-unused-variable','-Wno-unused-but-set-variable','-Wno-parentheses',
        '-I/source/overlays/v3','-I/out',
        '-DAF_HP_HARVEST_REGISTRY=1','-DAF_HP_REWARD_REGISTRY=1',
        '-DAF_HP_CARRIED_REGISTRY=1','-DAF_HP_EXERCISE_REGISTRY=1']
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
        return result.stdout
    units=['ev_turkey.c','dialogue.c','reward-map.c','layout.c','registry.c',
        '/source/overlays/v3/harvest_state.c','/source/overlays/v3/harvest_dialogue.c',
        '/source/overlays/v3/harvest_world_native.c',
        '/source/overlays/v3/carried_handover.c',
        '/source/overlays/v3/carried_npc.c',
        '/source/overlays/v3/holiday_participants_registry.c',
        '/source/overlays/v3/holiday_participants_storage.c',
        '/source/overlays/v3/holiday_participants_services.c',
        '/source/overlays/v3/holiday_participants_spawn.S',
        '/source/overlays/v3/holiday_festival_motion.c']
    if 'harvest-motions.S' in generated:units.append('harvest-motions.S')
    run('gcc',*flags,*units)
    run('objcopy','-O','binary','--only-section=.rodata.af_hr_layout','layout.o','layout.bin')
    layout_values=struct.unpack('>7I',(out/'layout.bin').read_bytes())
    report['native_layout']=dict(zip(('actor_bytes','saved_bytes','common_bytes','source_event',
        'source_profile','source_special_motion','source_y_rotation_mask'),layout_values))
    run('ld','-EB','-r',*(Path(n).stem+'.o' for n in units),'-o','harvest-unbound.o')
    report.update(format='AFV3-HARVEST-REWARDS-1',base_abi=prior['runtime_abi'],
        base_sha256=sha256(image),rewards=ordered,source_reward_table=table,dialogue=text,
        generated_sha256={n:sha256(v if isinstance(v,bytes) else v.encode()) for n,v in generated.items()},
        unbound_services=run('nm','--undefined-only','harvest-unbound.o').strip().splitlines(),
        object=dict(sha256=sha256((out/'harvest-unbound.o').read_bytes()),compiler=IMAGE,
            flags=flags,size=run('size','harvest-unbound.o'),linked=False),
        acquisition_installed=False,saved_format_changed=False,
        pending=['complete native world/selection/state bindings and persistent reward record',
            'complete Franklin art, voice, motions, and shared registry admission',
            'source free-block hiding, arrival, and after-conversation relocation',
            'ordinary furniture/surface admission and current gameplay/save verification'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(out/'prepared.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();result=prepare(args.output,args.base_lock)
    print(json.dumps(dict(functions=len(result['family'][0]['functions']),
        rewards=len(result['rewards']),messages=len(result['dialogue']['rows']),
        unbound=len(result['unbound_services']),installed=False)))


if __name__=='__main__':main()
