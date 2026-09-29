"""Compile connected donor controllers and participants through one native adapter.

No donor functions are transcribed or discarded. Generated code and complete
source receipts stay local. Preparation does not enable unfinished actors.
"""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import by_vrom,sha256
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT
from v3_furniture_pipeline import Source,prepare_models,compile_models
from v3_registry import PARTICIPANTS,PARTICIPANT_REGISTRY_VERSION

DONOR=ROOT/'local/ac-decomp'
FAMILY=('tokyoso_control','tunahiki_control','hatumode_control',
    'tokyoso_npc0','tokyoso_npc1','tunahiki_npc0','tunahiki_npc1','hatumode_npc0','rope')
CONSTANT_HEADERS=('types.h','ac_npc.h','ac_npc_anim_def.h','m_actor.h','m_event.h',
    'm_name_table.h','m_player.h','m_npc.h','m_npc_personal_id.h','m_choice.h',
    'm_msg.h','m_msg_enum.h','m_demo.h',
    'm_camera2.h','m_collision_bg.h','m_collision_obj.h','c_keyframe.h',
    'm_lib.h','sys_math.h','audio_defs.h','ac_tools.h','ef_effect_control.h')
PREPROCESS=['cc','-E','-P','-dD','-x','c','-','-DVERSION=0',
    '-DVER_GAFE01_00=0','-DVER_GAFU01_00=1']
REFERENCES_SHA='60f93e74b6421a49bdc69c698c561d6bfbc8cfd5fee7e4258553c7ce54b8612a'
NATIVE_PROFILES={
    'tokyoso_control':(0x9378C0,0x80A77620,0x80A78AF0),
    'tunahiki_control':(0x951A70,0x80A91800,0x80A91A10),
    'hatumode_control':(0x94D920,0x80A8D6A0,0x80A8EAE0),
    'tokyoso_npc0':(0x933F00,0x80A73C60,0x80A748C0),
    'tokyoso_npc1':(0x934D50,0x80A74AB0,0x80A75F40),
    'tunahiki_npc0':(0x951D10,0x80A91AA0,0x80A92370),
    'tunahiki_npc1':(0x952730,0x80A924C0,0x80A933B0),
    'hatumode_npc0':(0x948A20,0x80A887A0,0x80A89760),
    'rope':(0x8623E0,0x8096D7A0,0x8096DBA0),
}

# Only unchanged native services with equivalent signatures live here. Donor
# identities, dialogue, effects, and actor creation require explicit adapters.
NATIVE_SERVICES={
    'Actor_delete':0x800567E8,'af_holiday_keyframe_init':0x80052584,
    'af_hp_native_get_save':0x8008033C,'af_hp_native_reserve_save':0x80080080,
    'af_hp_native_dying':0x800814B8,'atans_table':0x800E0008,'bzero':0x8002F4C0,
    'memcpy':0x80034BF8,'mem_copy':0x800998C0,'sin_s':0x80099A94,'cos_s':0x80099A54,
    'none_proc1':0x8009AC74,'fqrand':0x8002C9AC,
    'cKF_FrameControl_stop_proc':0x80051CE8,'cKF_FrameControl_passCheck_now':0x80051C18,
    'mCoBG_GetBgY_OnlyCenter_FromWpos2':0x80071B78,
    'mDemo_Check':0x8007CF00,'mDemo_Request':0x8007CDD8,'mDemo_Get_talk_actor':0x8007B410,
    'mDemo_Start':0x8007CF34,'mDemo_Set_camera':0x8007BA1C,'mDemo_Set_ListenAble':0x8007D098,
    'mDemo_Set_talk_display_name':0x8007B79C,'mDemo_Set_talk_turn':0x8007B908,
    'mDemo_Set_talk_return_demo_wait':0x8007B890,'mDemo_Set_talk_window_color':0x8007B980,
    'mFI_SetOyasiroPos':0x8008E8E0,'mNpc_GetNpcLooks':0x800AD084,
    'mNpc_GetNpcSoundSpec':0x800AD22C,'mNpc_RenewalSetNpc':0x800AB6C8,
    'mPlib_Check_now_handin_item':0x800B5678,
    'mPlib_request_main_demo_wait_type1':0x800B2C3C,
    'mPlib_request_main_demo_walk_type1':0x800B2C80,
    'mPlib_request_main_pray_type1':0x800B2A48,
    'mPlib_request_main_throw_money_type1':0x800B2A04,
    'mPr_GetPossessionItemSumWithCond':0x800B83D4,
    'mPr_GetPossessionItemIdxWithCond':0x800B80B4,'mPr_SetPossessionItem':0x800B8B08,
    'af_hp_native_player_state':0x800B1CBC,
    'af_hp_message_window':0x8009D1F0,'af_hp_message_continue':0x8009E908,
    'af_hp_choice_window':0x80065040,'af_hp_choice_index':0x800654FC,
    'af_hp_native_message':0x8007B5C0,'af_hp_native_continue':0x8009DBA4,
    'af_hp_native_sound':0x800D1D58,'af_hp_native_continuous':0x800D1D08,
    'af_hp_native_find_resident':0x800A7C30,'af_hp_native_free_resident':0x800A7AEC,
    'af_hp_native_make':0x80057E24,'mFI_Wpos2UtCenterWpos':0x800884E0,
    'mCoBG_SetPlussOffset':0x800739FC,'_Matrix_to_Mtx':0x800E139C,
    'osWritebackDCache':0x8002FE00,
    '_texture_z_light_fog_prim_npc':0x800BD5E8,'_texture_z_light_fog_prim_shadow':0x800BD510,
    'af_hp_native_event_status':0x8007FF08,'af_hp_native_event_error':0x8007FDA8,
    'af_hp_native_pool_variant':0x8008930C,'af_hp_native_sex':0x800AD104,
    'af_hp_native_joint_initial':0x800821B0,'af_hp_native_joint_removed':0x800824A4,
    'af_hp_native_joint_refill':0x8008256C,
    'af_hp_native_structure':0x8008D574,
    'xyz_t_add':0x8009A108,'mFI_BlockKind2BkNum':0x80089440,
    'mFI_BkNum2BaseHeight':0x80089114,'Matrix_translate':0x800E0314,
    'Matrix_scale':0x800E041C,'Matrix_RotateX':0x800E0500,
    'Matrix_RotateY':0x800E0698,'Matrix_RotateZ':0x800E0834,
    '_texture_z_light_fog_prim':0x800BD4E8,'_texture_z_light_fog_prim_xlu':0x800BD598,
    'Setpos_HiliteReflect_init':0x800588B8,'Setpos_HiliteReflect_xlu_init':0x80058928,
    'af_coin_native_find':0x80058460,
}
WORLD_READERS={
    'index':0x80081EA0,'active':0x80081EEC,'kind':0x80081F90,'all':0x80081FBC,
    'count':0x80081FE8,'position':0x80082014,'named_position':0x800820B0,
    'initial':0x80082450,'refill':0x800828AC,'name':0x80082BD8,'random':0x80082DA0,
    'lap':0x80082E40,
}


def clean(text):
    return re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)


def preprocess(text):
    # Preserve version branches while avoiding unrelated platform SDK headers.
    text=re.sub(r'^\s*#\s*include[^\n]*','',text,flags=re.M)
    return subprocess.run(PREPROCESS,input=text,text=True,capture_output=True,
        check=True,timeout=20).stdout


def read(path,receipts):
    data=(DONOR/path).read_bytes()
    receipts[path]=dict(bytes=len(data),sha256=sha256(data))
    return data.decode()


def expand(path,receipts):
    text=read(path,receipts)
    def include(match):
        child=match[1]
        if child.startswith('../src/actor/'):
            return expand(child[3:],receipts)
        return ''
    return re.sub(r'^\s*#include "([^"]+)"',include,text,flags=re.M)


def constants(text,receipts,headers=CONSTANT_HEADERS):
    """Select complete source enums/macros, including their dependencies."""
    known={};blocks=[]
    for header in headers:
        raw=preprocess(read('include/'+header,receipts))
        for block in re.findall(r'\b(?:typedef\s+)?enum\b[^;{}]*\{[^{}]*\}\s*(?:\w+)?\s*;',raw,re.S):
            if block.startswith('typedef') and re.search(r'\}\s*;$',block):
                block=block.removeprefix('typedef ')
            body=block[block.index('{')+1:block.rindex('}')]
            names={m[1] for m in re.finditer(r'(?:^|,)\s*(\w+)',body)}
            blocks.append((block,names))
        for match in re.finditer(r'^#define (\w+)([^\n]*)',raw,re.M):
            if match[1].startswith('__'):continue
            known[match[1]]=match[0]
    needed=set(re.findall(r'\b\w+\b',text));chosen=[];definitions={}
    # The furniture macro pastes its argument to _SOUTH. That resulting enum
    # token is absent from the unexpanded source but still a real dependency.
    needed.update(name+'_SOUTH' for name in re.findall(r'\bFTR_START\((\w+)\)',text))
    while True:
        added=[]
        for block,names in blocks:
            if needed&names and block not in chosen:
                chosen.append(block);added.extend(re.findall(r'\b\w+\b',block))
        for name,macro in known.items():
            if name in needed and name not in definitions:
                definitions[name]=macro;added.extend(re.findall(r'\b\w+\b',macro))
        if set(added)<=needed:break
        needed.update(added)
    # Public API shims intentionally replace these pointer-reading macros.
    omit={'CLIP','NPC_CLIP','eEC_CLIP','aSHR_GET_CLIP','mMsg_CHECK_MAINNORMALCONTINUE',
        'mChoice_GET_CHOSENUM','mMsg_SET_CONTINUE_MSG_NUM','NULL'}
    lines=[v for k,v in definitions.items() if k not in omit]
    # Avoid undefined float-to-short narrowing at a full half turn.
    lines=[s.replace('((s16)((deg) * (65536.0f / 360.0f)))',
        '((s16)(int)((deg) * (65536.0f / 360.0f)))') for s in lines]
    return '\n'.join(['#ifndef AF_HP_SOURCE_CONSTANTS','#define AF_HP_SOURCE_CONSTANTS',
        '#define NULL ((void *)0)',*lines,*chosen,'#endif',''])


def generate(source,*,family=FAMILY,reference_sha=REFERENCES_SHA,extra_headers=()):
    from v3_password_policy import function
    receipts={};modules={};headers=[];contracts=[]
    for stem in family:
        path='src/actor/'+('npc/' if '_npc' in stem else '')+'ac_'+stem+'.c'
        body=clean(expand(path,receipts))
        header=read('include/ac_'+stem+'.h',receipts)
        header=re.sub(r'^\s*#include[^\n]*','',header,flags=re.M)
        headers.append(header)
        # Profiles remain donor-numbered descriptors, never native registrations.
        profiles=re.findall(r'ACTOR_PROFILE\s+(\w+)\s*=\s*\{',body)
        if len(profiles)!=1:raise ValueError('Expected one complete actor owner: '+stem)
        profile=profiles[0]
        profile_at,profile_bytes=source.symbol(profile)
        if profile_bytes!=36:raise ValueError('Changed complete donor actor profile')
        refs={p-profile_at:r for (sec,p),r in source.section_relocations.items()
            if sec==5 and profile_at<=p<profile_at+36}
        if not all(i in refs for i in (16,20,24,28)):
            raise ValueError('Incomplete actor callback directory')
        anchor=refs[16][3]
        names=re.findall(r'^static\s+[^\n;{}=]+?\b(\w+)\([^;{}]*\)\s*\{',body,re.M)
        candidates={n:[at for at,rows in source.functions.items() if any(name==n for name,_ in rows)] for n in names}
        if any(not v for v in candidates.values()):
            raise ValueError('Missing complete actor function: '+stem)
        functions=[]
        for name,matches in candidates.items():
            matches=sorted(matches,key=lambda p:abs(p-anchor))
            if abs(matches[0]-anchor)>=0x10000 or (len(matches)>1 and abs(matches[0]-anchor)==abs(matches[1]-anchor)):
                raise ValueError('Ambiguous complete actor function: '+stem+'/'+name)
            functions.append(source.function(matches[0])[1])
        offsets={f['offset'] for f in functions}
        if offsets!={p for p in source.functions if min(offsets)<=p<=max(offsets)}:
            raise ValueError('Incomplete contiguous source actor function set: '+stem)
        if stem=='rope':
            # Preserve complete collision and deformation code. Only the GX
            # command submission is replaced by bounded native drawing.
            body=body.replace(function(body,'aRP_actor_draw'),
                'static void aRP_actor_draw(ACTOR *a,GAME *g) {af_hp_rope_draw(a,g,aRP_make_vtx);}')
            body=re.sub(r'^extern Gfx [^;]+;', '',body,flags=re.M)
            body=body.replace('i < ARRAY_SIZE(tol_rope_1_v, Vtx)',
                'i < (int)ARRAY_SIZE(tol_rope_1_v, Vtx)')
        body=body.replace('play->game_frame','af_hp_frame(play)')
        body=body.replace('&play->actor_info','af_hp_actor_info(play)')
        # Preserve every implemented function; remove only static prototypes
        # with no definition or reference in their complete source unit.
        for match in list(re.finditer(r'^static void (\w+)\([^;{}]*\);',body,re.M)):
            if len(re.findall(r'\b'+match[1]+r'\b',body))==1:
                body=body.replace(match[0],'')
        modules[stem]=body
        contracts.append(dict(name=stem,profile=profile,functions=functions,
            profile_offset=profile_at,profile_sha256=sha256(source.raw(profile)),
            profile_relocations=refs))
    header='\n'.join(headers)
    source_constants=constants(header+'\n'+'\n'.join(modules.values()),receipts,CONSTANT_HEADERS+extra_headers)
    if sha256(json.dumps(receipts,sort_keys=True,separators=(',',':')).encode())!=reference_sha:
        raise ValueError('Changed complete controller/participant source references')
    prelude=('#include "holiday_participants.h"\n#include "constants.h"\n'
        '#include "actors.h"\n#pragma GCC diagnostic ignored "-Wunused-parameter"\n')
    # Shared clips contain source-generated callbacks but never alias a native
    # clip with a different lifecycle or event record.
    clips=''
    if 'tokyoso_control' in family:clips+='aTKC_clip_c *af_hp_tokyoso_clip;\n'
    if 'hatumode_control' in family:clips+='aHTMD_clip_c *af_hp_hatumode_clip;\n'
    header+='\n'+''.join('extern '+line+'\n' for line in clips.splitlines())
    generated={stem+'.c':prelude+body for stem,body in modules.items()}
    generated.update({'constants.h':source_constants,'actors.h':header})
    # One connected partial link resolves all source-to-source references.
    generated['clips.c']=('#include "holiday_participants.h"\n#include "actors.h"\n'
        +clips)
    return generated,dict(format='AFV3-HOLIDAY-PARTICIPANTS-1',family=contracts,
        references=receipts,source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()),installed=False,
        native_services_bound=False,native_execution_verified=False)


def rope_artwork(source,out,generated,reuse=None):
    """Use the same complete-model converter for the rope and its shadow."""
    vertex,size=source.symbol('tol_rope_1_v')
    if size!=60*16:raise ValueError('Changed complete rope vertex array')
    descriptor=dict(models={label:source.containing(source.symbol(name)[0],exact=True)
        for label,name in (('rope','tol_rope_1T_model'),('shadow','tol_rope_1_shadowT_model'))},
        vertex_bindings={0x08000000:vertex,0x08000200:vertex+512},
        callback_adapter=dict(category='actor-model-assets'))
    prepared=prepare_models(source,descriptor)
    directory=out/'rope-art';directory.mkdir()
    if reuse:
        cached=json.loads((reuse/'prepared.json').read_text())
        receipt=cached['rope'];asset=(reuse/'rope-art.bin').read_bytes()
        if (cached['source_rel_sha256']!=sha256(source.rel) or
                cached['source_symbols_sha256']!=sha256(source.symbols.encode()) or
                sha256(asset)!=receipt['sha256'] or asset[:len(prepared[1])]!=prepared[1] or
                (reuse/'rope-art/commands.c').read_text()!=prepared[5] or
                receipt['resources']!=prepared[2]):
            raise ValueError('Changed complete cached rope resources')
        records=receipt['models'];models={r['layer']:r['native_offset'] for r in records}
        if (set(models)!=set(prepared[4]) or any(sha256(asset[r['native_offset']:
                r['native_offset']+r['bytes']])!=r['output_sha256'] for r in records)):
            raise ValueError('Incomplete cached rope models')
        write_new(directory/'commands.c',prepared[5].encode())
    else:asset,models,records,_=compile_models(directory,prepared)
    offset=prepared[3][vertex]
    generated['rope-art.bin']=asset
    generated['rope-packet.S']=('.section .rodata.af_hp_rope_art,"a",@progbits\n.balign 16\n'
        '.globl af_hp_rope_art\naf_hp_rope_art:\n.incbin "rope-art.bin"\n'
        f'.globl tol_rope_1_v\n.set tol_rope_1_v, af_hp_rope_art+{offset}\n')
    generated['rope-art.c']=('#include "holiday_participants.h"\n'
        'const u32 af_hp_rope_models[2]={'+','.join(hex(0x06000000+models[k]) for k in ('rope','shadow'))+'};\n')
    return dict(bytes=len(asset),sha256=sha256(asset),resources=prepared[2],models=records,
        dynamic_vertex_offset=offset,dynamic_vertex_count=60,
        complete_collision=True,installed=False)


def world(base,prior,source,generated):
    """Bind uniforms and preserve every native shared placement reader body."""
    from aflib import CODE_RAM,CODE_VROM
    from v3_villager_defaults import TEXTURES,PALETTES
    from v3_holiday_maps import REFERENCES
    path='src/game/m_event_map_npc.c';text=(DONOR/path).read_bytes()
    if sha256(text)!=REFERENCES[path]:raise ValueError('Changed shared participant-selection source')
    cloth=prior['clothing']['batch'];prepared=ROOT/cloth['prepared_directory']/'art.json'
    if sha256(prepared.read_bytes())!=cloth['prepared_sha256']:raise ValueError('Changed complete clothing correspondence')
    rows=json.loads(prepared.read_text())['rows'];uniforms=[];files=by_vrom(base)
    textures,palettes=(files[v].extract(base) for v in (TEXTURES,PALETTES))
    for donor in (0x2414,0x2415):
        r=next(r for r in rows if r['donor_item_id']==f'{donor:04X}')
        if r['status']!='native-appearance' or len(r['native_candidates'])!=1:
            raise ValueError('Participant uniform lacks verified native identity')
        target=int(r['native_item_id'],16);index=target-0x2400
        resource=textures[index*512:(index+1)*512]+palettes[index*32:(index+1)*32]
        if sha256(resource)!=r['resource_sha256']:
            raise ValueError('Changed complete installed participant uniform')
        uniforms.append(dict(source=donor,native=target,name=r['name'],sha256=sha256(resource)))
    generated['world-data.c']=('#include "holiday_participants.h"\nint af_hp_uniform(unsigned int source) {\n'
        'switch(source){case 0:return 0;'+''.join(f'case {r["source"]}:return {r["native"]};' for r in uniforms)+
        'default:return -1;}}\n')
    core=files[CODE_VROM].extract(base)
    directory=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt').read_text()
    starts=sorted({int(m[1],16) for m in re.finditer(r'= 0x([0-9A-F]+);[^\n]*type:func',directory)})
    readers=[]
    for name,at in WORLD_READERS.items():
        end=next(p for p in starts if p>at);body=core[at-CODE_RAM:end-CODE_RAM]
        readers.append(dict(name=name,start=at,end=end,sha256=sha256(body),entry_hex=body[:8].hex(),
            replacement='af_hp_world_'+name,previous='af_hp_world_previous_'+name))
    names=('mEvMN_GetNpcIdxRandom','mEvMN_ClearRemoveNpcJoint','mEvMN_SetNpcJointEvRandom')
    functions=[source.function(next(p for p,rs in source.functions.items() if any(n==name for n,_ in rs)))[1]
        for name in names]
    return dict(source_reference=path,source_sha256=sha256(text),uniforms=uniforms,
        native_reader_hooks=readers,selection_functions=functions,native_map_count=15,
        source_map_count=17,original_readers_preserved=True,installed=False)


def coin(source,base,prior,out,generated,reuse=None):
    """Prepare the whole offering effect with shared art and sound conversion."""
    from aflib import CODE_RAM,CODE_VROM
    from v3_password_policy import function
    from v3_sound_programs import prepare_triggers,register_triggers,installed_resource
    from v3_villager_audio import read_audio_donor
    from v3_creature_insect_effects import OWNERS as WATER
    path='src/effect/ef_coin.c';raw=(DONOR/path).read_bytes()
    if sha256(raw)!='fea3baecf1240effa5d0591a5f4caf5d50c15d41a884e8cc8e7f9b713edd0acf':
        raise ValueError('Changed complete offering-coin source')
    names=('eCoin_init','eCoin_GetFountainHeight','eCoin_ct','eCoin_mv','eCoin_dw')
    functions=[];pieces=['#include "holiday_coin.h"','#pragma GCC diagnostic ignored "-Wunused-parameter"']
    for name in names:
        matches=[p for p,rs in source.functions.items() if any(n==name for n,_ in rs)]
        if len(matches)!=1:raise ValueError('Missing complete offering function: '+name)
        functions.append(source.function(matches[0])[1])
        if name.endswith('_dw'):continue
        body=clean(function(raw.decode(),name))
        for before,after in (
            ('eEC_CLIP->make_effect_proc','af_coin_create'),
            ('eEC_CLIP->set_continious_env_proc','af_sky_continuous'),('sAdo_OngenTrgStart','af_coin_sound')):
            body=body.replace(before,after)
        # The source truncates then wraps its random 16-bit rotations.
        body=body.replace('= RANDOM_F(65535);','= (s16)(int)RANDOM_F(65535);')
        if name=='eCoin_ct':
            body=body.replace('af_coin_sound(0x466,',
                'if(!af_coin_fit(effect,game)){effect->timer=0;return;}\n    af_coin_sound(0x466,')
        if name=='eCoin_mv':
            # The native shrine is a solid offering box, not the donor's well.
            # Preserve the throw/rotation/fade, but contact only while falling
            # and omit the donor's water-only splash child.
            body=body.replace('if (effect->position.y <= effect->offset.x)',
                'if (effect->velocity.y < 0 && effect->position.y <= effect->offset.x)')
            body=body.replace('xyz_t pos = effect->position;', '').replace('pos.y = effect->offset.x;', '')
            splash=('eEC_CLIP->effect_make_proc(eEC_EFFECT_TURI_MIZU, pos, effect->prio, 0, '
                'game, (u16)effect->item_name, 0, 0);')
            if body.count(splash)!=1:raise ValueError('Changed complete source offering contact')
            body=body.replace(splash,'')
        pieces.append(body)
    pieces.extend((
        'void af_coin_init(xyz_t p,int priority,s16 angle,GAME *g,u16 name,s16 a,s16 b) {',
        ' if(af_sky_ready(g))eCoin_init(p,priority,angle,g,name,a,b);}',
        'void af_coin_ct(RoomEffect *e,GAME *g,void *arg) {',
        ' if(af_sky_ready(g))eCoin_ct(e,g,arg);else e->timer=0;}',
        'void af_coin_mv(RoomEffect *e,GAME *g) {',
        ' if(!af_sky_ready(g)){e->timer=0;return;}',
        ' for(unsigned int i=0,n=af_hp_native_ticks;i<n;i++){',
        '  if(i){if(e->timer<=1)break;--e->timer;} eCoin_mv(e,g);}}',
        'void af_coin_dw(RoomEffect *e,GAME *g) {af_coin_draw(e,g);}',''))
    generated['coin-source.c']='\n\n'.join(pieces)
    at,n=source.symbol('iam_ef_coin');profile=source.raw('iam_ef_coin')
    refs={p-at:r for (section,p),r in source.section_relocations.items() if section==5 and at<=p<at+n}
    expected={i*4:(1,1,1,next(f['offset'] for f in functions if f['symbol']=='eCoin_'+role))
        for i,role in enumerate(('init','ct','mv','dw'))}
    if profile.hex()!='00000000000000000000000000000000fffe00ffc47a0cff' or refs!=expected:
        raise ValueError('Changed complete offering profile')
    # Preserve the actual two palette choices through the material-frame path.
    at,n=source.symbol('eCoin_pal_table');pointers=source.pointers(at,n)
    frames=[]
    for i,name in enumerate(('ef_coin_gold_pal','ef_coin_silver_pal')):
        p,size=source.symbol(name)
        if n!=8 or size!=32 or pointers.get(at+i*4)!=p:raise ValueError('Changed full coin palette table')
        frames.append(dict(symbol=name,donor_offset=p,bytes=size,source_sha256=sha256(source.raw(name))))
    descriptor=dict(models={k:source.containing(source.symbol(name)[0],exact=True)
        for k,name in (('opaque','ef_coin_model'),('translucent','ef_coin_modelT'))},
        callback_adapter=dict(category='actor-model-assets',material_frames=[dict(kind='palette',
            segment_address=0x08000000,frames=frames,selector=dict(input='effect-work',offset=5,mask=1))]))
    prepared=prepare_models(source,descriptor);directory=out/'coin-art';directory.mkdir()
    cached=json.loads((reuse/'prepared.json').read_bytes()) if reuse else {}
    if 'coin' in cached:
        art=cached['coin']['art'];asset=(reuse/'coin-art.bin').read_bytes()
        if (cached['source_rel_sha256']!=sha256(source.rel) or art['resources']!=prepared[2] or
                art['palette_frames']!=frames or sha256(asset)!=art['sha256'] or
                asset[:len(prepared[1])]!=prepared[1] or
                (reuse/'coin-art/commands.c').read_text()!=prepared[5]):
            raise ValueError('Changed complete cached offering artwork')
        model_rows=art['models'];models={r['layer']:r['native_offset'] for r in model_rows}
        if set(models)!=set(prepared[4]) or any(sha256(asset[r['native_offset']:
                r['native_offset']+r['bytes']])!=r['output_sha256'] for r in model_rows):
            raise ValueError('Incomplete cached offering models')
        write_new(directory/'commands.c',prepared[5].encode())
    else:asset,models,model_rows,_=compile_models(directory,prepared)
    generated['coin-art.bin']=asset
    generated['coin-packet.S']=('.section .rodata.af_coin_art,"a",@progbits\n.balign 16\n'
        '.globl af_coin_art\naf_coin_art:\n.incbin "coin-art.bin"\n')
    generated['coin-art.c']=('#include "holiday_coin.h"\nconst u32 af_coin_models[2]={'
        +','.join(hex(0x06000000+models[k]) for k in ('opaque','translucent'))+'};\n'
        'const u32 af_coin_palettes[2]={'+','.join(str(prepared[3][r['donor_offset']]) for r in frames)+'};\n')
    # Retain the existing water receipts, but this solid shrine does not emit
    # the source well's splash. Other native water users remain untouched.
    files=by_vrom(base);water=[]
    for eid,vrom,reloc,ram,digest,rel_digest in WATER[:2]:
        if sha256(files[vrom].extract(base))!=digest or sha256(files[reloc].extract(base))!=rel_digest:
            raise ValueError('Changed complete shared water effect')
        water.append(dict(id=eid,vrom=vrom,reloc=reloc,ram=ram,sha256=digest,relocation_sha256=rel_digest))
    resources,audio=prepare_triggers(base,prior,[0x466,0x467]);core=files[CODE_VROM].extract(base)
    sequence,_,_=installed_resource(base,core,'seq',199)
    previous=prior['equipment_resources']['furniture_audio']
    counts={r['group']:r['previous_count'] for r in previous['tables']}
    dol,_=read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    priority=core[0x80113B84-CODE_RAM:0x80113B84-CODE_RAM+128]
    new_sequence,programs,tables=register_triggers(sequence,audio['programs'],resources['fragments'],counts,
        priority,dol.read(0x800A9A90,128),previous=previous)
    sound_ids={r['source_sound_word']:r['native_sound_word'] for r in programs}
    generated['coin-audio.c']=('#include "holiday_coin.h"\nconst u16 af_coin_sounds[2]={'
        +','.join(str(sound_ids[n]) for n in (0x466,0x467))+'};\n')
    audio_files={'coin-font.bin':resources['font'],'coin-wave.bin':resources['wave'],
        'coin-sequence.bin':new_sequence,**{'coin-'+n:d for n,d in resources['fragments'].items()}}
    generated.update(audio_files)
    audio.update(files={n:dict(bytes=len(d),sha256=sha256(d)) for n,d in audio_files.items()},
        registered_programs=programs,registered_tables=tables,previous_sequence_sha256=sha256(sequence))
    return dict(reference=path,reference_sha256=sha256(raw),functions=functions,
        profile_sha256=sha256(profile),profile_relocations=refs,policy_hex=profile[16:].hex(),
        source_id=118,native_id=119,art=dict(bytes=len(asset),sha256=sha256(asset),
            models=model_rows,resources=prepared[2],palette_frames=frames),water=water,audio=audio,
        installed=False,native_execution_verified=False,
        landing_geometry=shrine_geometry(base),water_subeffect=False,
        platform_adaptations=['Contact the loaded N64 shrine offering box while descending',
            'Retarget horizontal flight to the native box, retaining source vertical acceleration',
            'Omit the wishing-well splash at the solid offering box'])


def shrine_geometry(base):
    """Guard the actual native models and actor that define coin contact."""
    files=by_vrom(base);rows=[]
    for vrom,size,digest in (
        (0xD5E000,611456,'23f68c1a4c9d9bb7ab964a3140aad35f8606ae5ee751dc224839abdeb6cd0d7f'),
        (0xDF4000,752,'a4f33bb4c76cb8c8ebb9df0232e15ccf381ba386b7eed358132b2fb0051a4446'),
        (0x8D8EC0,4320,'e36125d69b517b6507384872e8784a1bfd8ee6e4885f1b643e71a2aab2c2e10d')):
        raw=files[vrom].extract(base)
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed native shrine coin geometry')
        rows.append(dict(vrom=vrom,bytes=size,sha256=digest))
    return dict(native_resources=rows,structure_index=22,profile=0x5C,part=0,
        actor_position_offset=0x28,model_scale=.01,box_x=[-20,20],box_y=[0,17.5],box_z=[42.5,60],
        landing_z=52.5,descending_only=True,actual_loaded_actor_height=True,
        native_execution_verified=False)


def hooks(base,prior,generated,readers):
    """Extend the installed NPC chains and all shared event-map consumers."""
    from aflib import CODE_RAM,CODE_VROM
    from v3_camper_quest import OWNERS as SPAWN_OWNERS
    from v3_import_storage import jump
    from v3_npc_draw import relocation_offsets
    files=by_vrom(base);core=files[CODE_VROM].extract(base)
    links={};rows=[];trampolines=['.set noreorder','.set noat','.set nomacro','.text']
    def exports(symbol):
        found=set()
        def visit(v):
            if isinstance(v,dict):
                if isinstance(v.get('symbols'),dict) and symbol in v['symbols']:
                    found.add(v['symbols'][symbol])
                for child in v.values():visit(child)
            elif isinstance(v,list):
                for child in v:visit(child)
        visit(prior)
        return found
    def chained(vrom,ram,address,replacement,previous,symbol,kind,delay):
        raw=files[vrom].extract(base);offset=address-ram
        word,slot=struct.unpack_from('>2I',raw,offset)
        target=(address+4)&0xF0000000 | (word&0x3FFFFFF)<<2
        if word>>26!=(3 if kind=='call' else 2) or slot!=delay or target not in exports(symbol):
            raise ValueError('Changed installed participant chain: '+symbol)
        if previous in links and links[previous]!=target:
            raise ValueError('NPC controllers disagree on shared profile dispatcher')
        links[previous]=target
        rows.append(dict(vrom=vrom,ram=ram,address=address,kind=kind,
            before=raw[offset:offset+8].hex(),replacement=replacement,previous=previous,
            previous_target=target,previous_export=symbol))
    # Preserve both relocated table-address calculations and their HI/LO
    # relocations. The existing resident camper helper handles every other ID.
    for vrom,reloc,ram,old_hook,bias,*_ in SPAWN_OWNERS[:2]:
        raw=files[vrom].extract(base);rel=files[reloc].extract(base);at=old_hook-ram
        slots=relocation_offsets(rel,len(raw))
        expected=(0x3C090000|((bias+0x8000)>>16),0x01284821,0x25290000|(bias&65535))
        if struct.unpack_from('>3I',raw,at-8)!=expected or at not in slots or at-8 not in slots or at+4 in slots:
            raise ValueError('Changed relocated shared NPC profile lookup')
        chained(vrom,ram,old_hook+4,'af_hp_spawn_profile','af_hp_previous_spawn_profile',
            'af_v3_camper_profile','call',0x27A40044)
        rows[-1].update(relocation_vrom=reloc,relocation_sha256=sha256(rel),
            retained_address_bias=bias,retained_pointer_hex=raw[at-8:at+4].hex())
    profiles={r['name']+i:r['profile'] for r in PARTICIPANTS.values() for i in range(r['count'])}
    if sorted(profiles)!=list(range(0xD0A0,0xD0AE)):
        raise ValueError('Changed complete additional NPC role interval')
    generated['spawn-data.c']=('#include "holiday_participants.h"\nconst s16 af_hp_spawn_profiles[14]={'
        +','.join(str(profiles[n]) for n in sorted(profiles))+'};\n')
    chained(0x8681F0,0x809735B0,0x809749D0,'af_hp_animation','af_hp_previous_animation',
        'af_holiday_motion_animation','entry',0)
    if {0x809749D0-0x809735B0,0x809749D4-0x809735B0}&relocation_offsets(
            files[0x878550].extract(base),files[0x8681F0].size):
        raise ValueError('Participant animation entry requires relocation')
    chained(CODE_VROM,CODE_RAM,0x80057E4C,'af_hp_descriptor','af_hp_previous_descriptor',
        'af_decor_actor_descriptor','call',0x00C02025)
    chained(CODE_VROM,CODE_RAM,0x800583B8,'af_hp_free','af_hp_previous_free',
        'af_v3_npc_extra_free','call',0)
    entries=[dict(r,address=r['start'],kind='entry',vrom=CODE_VROM,ram=CODE_RAM,
        before=r['entry_hex']) for r in readers]
    entries += [dict(address=address,kind='entry',vrom=CODE_VROM,ram=CODE_RAM,
        before=core[address-CODE_RAM:address-CODE_RAM+8].hex(),replacement=replacement,previous=previous)
        for address,replacement,previous in (
            (0x800AA14C,'af_hp_event_lookup','af_hp_previous_event'),
            (0x800AA0B8,'af_hp_event_unregister','af_hp_previous_unregister'),
            (0x800AA124,'af_hp_events_clear','af_hp_previous_clear'))]
    for r in entries:
        words=struct.unpack('>2I',bytes.fromhex(r['before']))
        # These exact prefixes only copy integer registers, form constants, or
        # store the caller frame. No PC-relative operation may be transplanted.
        for word in words:
            if word>>26 not in (0,9,12,15,43) or word>>26==0 and word&63 not in (0,2,3,33,37):
                raise ValueError('Unsafe original participant-reader prologue')
        trampolines.extend(('.balign 4','.globl '+r['previous'],r['previous']+':',
            *(f'.word 0x{w:08X}' for w in words),f'.word 0x{jump(r["address"]+8):08X}','nop'))
        rows.append(r)
    # The complete native manager has the same initial/refill distinction as
    # the donor, but dereferences a failed area-15 allocation. Guard that exact
    # store without preallocating (which would incorrectly select refill).
    vrom,reloc,ram=0x8EA970,0x8ED0E0,0x80A22EB0
    native=files[vrom].extract(base);at=0x80A23C5C-ram
    body=native[0x80A23BDC-ram:0x80A23CD8-ram]
    digest='9b572e9e44fa9b287d28ac186061252d5ebeef0327b17d98e7e726000eab3117'
    if (len(body)!=252 or sha256(body)!=digest or
            {at,at+4}&relocation_offsets(files[reloc].extract(base),len(native))):
        raise ValueError('Changed complete native event allocation/selection function')
    rows.append(dict(vrom=vrom,ram=ram,address=ram+at,kind='call',
        before=native[at:at+8].hex(),replacement='af_hp_manager_alloc',
        native_function=dict(address=0x80A23BDC,bytes=len(body),sha256=digest),
        failure_return=0x80A23CC0,relocation_vrom=reloc,
        relocation_sha256=sha256(files[reloc].extract(base))))
    generated['original-readers.S']='\n'.join(trampolines)+'\n'
    return dict(rows=rows,bindings=links,role_profiles=profiles,
        original_npc_tables_preserved=True,original_relocations_preserved=True,installed=False)


def patch(base,prepared,symbols):
    """Apply the prepared connected hooks without changing overlay lifetimes."""
    from v3_import_storage import jump
    if sha256(base)!=prepared['base_sha256']:raise ValueError('Participant hooks need their exact checked base')
    files=by_vrom(base);changes={};receipts=[]
    for row in prepared['hooks']['rows']:
        vrom=row['vrom'];data=changes.setdefault(vrom,bytearray(files[vrom].extract(base)))
        offset=row['address']-row['ram'];before=bytes.fromhex(row['before'])
        target=symbols[row['replacement']]
        if target&3 or not 0x80400000<=target<0x80800000 or data[offset:offset+len(before)]!=before:
            raise ValueError('Changed participant hook bytes or resident destination')
        after=struct.pack('>I',jump(target,link=row['kind']=='call'))
        if row['kind']=='entry':after+=bytes(4)
        data[offset:offset+len(after)]=after
        receipts.append(dict(row,after=after.hex(),target=target))
    return {v:bytes(data) for v,data in changes.items()},receipts


def native_motions(source,base,generated,*,paired=()):
    """Resolve the whole family's reused animations by complete motion content."""
    from v3_keyframes import _animation,CHANNELS,npc_motion,compile_animations
    files=by_vrom(base);owner=files[0x8681F0].extract(base)
    # The complete native sequence ends before the alternate talking records.
    rows=[struct.unpack_from('>II',owner,0x80981974-0x809735B0+i*8) for i in range(234)]
    if any(p>>24!=6 or index!=i for i,(p,index) in enumerate(rows)):
        raise ValueError('Changed complete native NPC animation directory')
    def native(p,n):
        at=0xE0E000+(p&0xFFFFFF)
        if p>>24!=6:return None
        entry=next((e for e in files.values() if e.vstart<=at and at+n<=e.vend),None)
        return entry.extract(base)[at-entry.vstart:at-entry.vstart+n] if entry else None
    needed=set(re.findall(r'\baNPC_ANIM_\w+','\n'.join(
        code for name,code in generated.items() if name.endswith('.c'))))
    needed.discard('aNPC_ANIM_NUM') # source-only "no animation" sentinel
    needed.discard('aNPC_ANIM_SPEED_TYPE_FREE') # speed mode, not a motion
    # Some source tables select a base motion plus a direction bit. Resolve
    # both complete records and check native adjacency before retaining that
    # arithmetic; replacing only the named base is not sufficient.
    pairs=[]
    if paired:
        enum=clean((DONOR/'include/ac_npc_anim_def.h').read_text())
        blocks=re.findall(r'enum\s*\{([^{}]+)\}',enum,re.S)
        if len(blocks)!=1:raise ValueError('Changed complete NPC animation enum')
        names=[n.strip() for n in blocks[0].split(',') if n.strip()]
        if len(set(names))!=len(names) or any(not re.fullmatch(r'aNPC_ANIM_\w+',n) for n in names):
            raise ValueError('NPC motion arithmetic requires the checked sequential enum')
        for name in sorted(set(paired)):
            index=names.index(name)
            if name not in needed or names[index+1]=='aNPC_ANIM_NUM':
                raise ValueError('Unreferenced or invalid paired NPC motion')
            pair=(name,names[index+1]);pairs.append(pair);needed.update(pair)
    result=[]
    for name in sorted(needed):
        symbol='cKF_ba_r_npc_1_'+name.removeprefix('aNPC_ANIM_').lower()
        at,_=source.symbol(symbol);desc=_animation(source,at,joints=26,record_bytes=64)
        matches=[]
        for p,index in rows:
            raw=native(p,64)
            if not raw or raw[16:36]!=source.data[at+16:at+36]:continue
            for i,label in enumerate(CHANNELS):
                r=desc['arrays'][label];ptr=struct.unpack_from('>I',raw,i*4)[0]
                if bool(ptr)!=bool(r):break
                data=native(ptr,r['bytes']) if r else b''
                if r and (data is None or sha256(data)!=r['source_sha256']):break
            else:matches.append(dict(index=index,address=p,header_sha256=sha256(raw)))
        # WAIT and its talk alias share the same complete resident record. They
        # are not different motions; choose the ordinary, lower directory ID.
        if matches and len({r['address'] for r in matches})==1:
            result.append(dict(name=name,native=matches[0],aliases=matches[1:],source=desc,
                native_face_effect_audio_programme_retained=True))
        elif not matches and name=='aNPC_ANIM_OMAIRI1':
            # The native shrine prayer lasts 91 frames; the complete donor
            # motion lasts 46. Reuse its native identity only with the imported
            # actor's full-motion override, never substitute the native curve.
            p,index=rows[71];raw=native(p,64)
            desc=npc_motion(source,at,joints=26)
            if not raw or raw[36:]!=source.data[at+36:at+64]:
                raise ValueError('Prayer requires additional face/effect/audio conversion')
            data,packed=compile_animations(source,[desc],address_base=0)
            # Relocatable assembler retains every source array and the entire
            # 64-byte control record, without reserving a fixed address early.
            lines=['.section .rodata.af_hp_motion,"a",@progbits','.balign 16',
                '.global af_hp_motion_data','af_hp_motion_data:']
            cursor=0
            for r in packed['relocations']:
                pos=r['offset']
                lines.append(f'.incbin "motion.bin", {cursor}, {pos-cursor}')
                lines.append(f'.word af_hp_motion_data + {r["target_offset"]}')
                cursor=pos+4
            lines.extend([f'.incbin "motion.bin", {cursor}, {len(data)-cursor}',
                '.global af_hp_prayer_motion',
                f'.set af_hp_prayer_motion, af_hp_motion_data + {packed["headers"][0]["native_offset"]}'])
            generated['motion.bin']=data
            generated['motion.S']='\n'.join(lines)+'\n'
            result.append(dict(name=name,native=dict(index=index,address=p,header_sha256=sha256(raw)),
                source=desc,converted=packed,bytes=len(data),sha256=sha256(data),
                native_face_effect_audio_programme_retained=True,override_required=True))
        else:raise ValueError('Missing or ambiguous complete native motion: '+name)
    resolved={r['name']:r for r in result}
    for first,second in pairs:
        if resolved[second]['native']['index']!=resolved[first]['native']['index']+1:
            raise ValueError('Native motion pair needs an explicit mapping: '+first)
        resolved[first]['paired_successor']=second
    for name,code in list(generated.items()):
        if not name.endswith('.c'):continue
        for r in result:
            code=re.sub(r'\b'+r['name']+r'\b',str(r['native']['index']),code)
        generated[name]=code
    return result


def money(source,base,generated):
    """Generate the complete donor wallet/bag payment path with native storage."""
    from v3_password_policy import function,REFERENCES
    raw=(DONOR/'src/game/m_shop.c').read_bytes()
    if sha256(raw)!=REFERENCES['src/game/m_shop.c']:raise ValueError('Changed complete currency source')
    names=('mSP_money_check','mSP_get_sell_price_sub','mSP_get_sell_price')
    bodies=[clean(function(raw.decode(),name)) for name in names]
    tables=[]
    for symbol,fmt in (('mSP_sack_amount','I'),('mSP_itemNo','H')):
        data=source.raw(symbol);values=struct.unpack('>4'+fmt,data)
        tables.append(dict(symbol=symbol,values=values,sha256=sha256(data)))
    # The native offering consumes these same four bags in this same order.
    owner=by_vrom(base)[0x94D920].extract(base)
    values,items=(t['values'] for t in tables)
    if (struct.unpack_from('>4I',owner,0x80A8EB04-0x80A8D6A0)!=values or
            struct.unpack_from('>4H',owner,0x80A8EB14-0x80A8D6A0)!=items):
        raise ValueError('Different native money bags/amounts')
    text='\n'.join(bodies)
    text=text.replace('mSP_money_check','af_hp_source_money_check').replace(
        'mSP_get_sell_price','af_hp_source_get_sell_price')
    generated['money.c']=('#include "holiday_participants.h"\n'
        '#define Common_Get(name) af_hp_private()\n'
        '#define FALSE 0\n#define TRUE 1\n#define MONEY_NUM 4\n'
        '#define mPr_ITEM_COND_NORMAL 0\n#define EMPTY_NO 0\n'
        'static const u32 mSP_sack_amount[4]={'+','.join(map(str,values))+'};\n'
        'static const mActor_name_t mSP_itemNo[4]={'+','.join(map(str,items))+'};\n'+text+'\n')
    return dict(reference_sha256=sha256(raw),functions=[source.function(next(
        p for p,rows in source.functions.items() if any(n==name for n,_ in rows)))[1] for name in names],
        tables=tables,native_wallet_offset=0x38)


def registry(base,report,generated):
    """Generate the entire family's native profiles, not per-resident scripts."""
    from v3_password_policy import function
    if set(PARTICIPANTS)!=set(FAMILY):raise ValueError('Incomplete participant registry')
    files=by_vrom(base);code=['#include "holiday_participants.h"','#include "actors.h"'];rows=[]
    constants=generated['constants.h'];mapping={};timing=[];overrides=[]
    for row in report['family']:
        stem=row['name'];r=PARTICIPANTS[stem]
        vrom,ram,at=NATIVE_PROFILES[stem];image=files[vrom].extract(base)
        raw=image[at-ram:at-ram+36]
        profile,part,flags,name,bank,size=struct.unpack_from('>HHIHHI',raw)
        expected_part=4 if stem=='rope' else 3 if r['count'] else 7
        expected_bank=394 if stem=='rope' else 3
        if len(raw)!=36 or bank!=expected_bank or part!=expected_part<<8 or size>2400:
            raise ValueError('Changed native participant profile/pool contract: '+stem)
        code.append(f'_Static_assert(sizeof({stem.upper()}_ACTOR)<=2400,"Native participant pool bound");')
        rows.append(dict(r,stem=stem,donor_profile=row['profile'],native_vrom=vrom,native_ram=ram,
            original_profile=profile,original_name=name,original_bytes=size,part=part>>8,
            flags=flags,native_profile=at,native_profile_sha256=sha256(raw)))
        if r['count']:
            for i in range(r['count']):mapping[r['source']+i]=r['name']+i
    # Replace only the source role-name macros. Every source arithmetic reader
    # sees the same contiguous role sequence at its fixed additive destination.
    for match in re.finditer(r'^#define (SP_NPC_EV_(?:TOKYOSO|TUNAHIKI|HATUMODE)_\d+) \(SP_NPC_START \+ (\d+)\)',constants,re.M):
        n=0xD000+int(match[2])
        if n in mapping:overrides.append(f'#undef {match[1]}\n#define {match[1]} 0x{mapping[n]:04X}')
    if not constants.endswith('#endif\n'):raise ValueError('Changed generated constant guard')
    generated['constants.h']=constants[:-7]+'\n'.join(overrides)+'\n#endif\n'
    code.append('const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={')
    for r in rows:
        code.append('{'+','.join(str(r[k]) for k in ('source','name','profile','event','save','count','part'))+
            ',0,&'+r['donor_profile']+','+str(r['flags'])+'},')
    code.extend(('};','/* Installation supplies the real dependency/selection gate. */',
        'const u32 af_hp_available=0;',''))
    generated['registry.c']='\n'.join(code)
    # The source assumes the shared event area outlives every participant. A
    # cancelled native event can retire its storage before actor teardown.
    for file,fn,before,after in (
        ('hatumode_npc0.c','aHN0_actor_dt','if (actorx->npc_id == SP_NPC_EV_HATUMODE_0) {',
         'if (hatumode_p != NULL && actorx->npc_id == SP_NPC_EV_HATUMODE_0) {'),
        ('tunahiki_npc1.c','aTNN1_actor_dt','tunahiki->flag |= aTNC_NPCIDX2DELETEFLG(actorx->npc_id);',
         'if (tunahiki != NULL) tunahiki->flag |= aTNC_NPCIDX2DELETEFLG(actorx->npc_id);')):
        body=function(generated[file],fn)
        if body.count(before)!=1:raise ValueError('Changed event teardown assumption: '+file)
        generated[file]=generated[file].replace(body,body.replace(before,after))
    # All eight elapsed-time decrements across four modules use the native
    # update interval. State callbacks, physics, and audio still run once.
    expected={'tokyoso_control.c':4,'tokyoso_npc0.c':1,'tokyoso_npc1.c':2,'hatumode_npc0.c':1}
    for name,count in expected.items():
        code,n=re.subn(r'\b((?:actor|h_npc)->(?:run_)?timer)--;',r'\1 = af_hp_countdown(\1);',generated[name])
        if n!=count:raise ValueError('Changed complete event timer readers: '+name)
        generated[name]=code;timing.append(dict(file=name,timer_readers=n))
    # This controller only advances shared rope state: it does not advance NPC
    # physics, talk, animations, or sounds. Run its complete source update for
    # each elapsed tick, including the odd-length counter wrap at 65 -> 2.
    name='tunahiki_control.c';code=generated[name]
    before='    aTNC_actor_move,\n'
    if code.count(before)!=1 or code.count('af_hp_frame(play)')!=1:
        raise ValueError('Changed complete tug controller cadence')
    code=code.replace(before,'    af_hp_tug_step,\n').replace('af_hp_frame(play)','af_hp_tug_frame')
    code=code.replace('static void aTNC_actor_ct(',
        'static void af_hp_tug_step(ACTOR*,GAME*);\nstatic u32 af_hp_tug_frame;\nstatic void aTNC_actor_ct(',1)
    code+='\nstatic void af_hp_tug_step(ACTOR *a,GAME *g) {\n'
    code+=' for(unsigned int i=0,n=af_hp_elapsed();i<n;i++){aTNC_actor_move(a,g);++af_hp_tug_frame;}\n}\n'
    generated[name]=code
    return dict(version=PARTICIPANT_REGISTRY_VERSION,rows=rows,name_mapping=mapping,
        uses_native_npc_pool=True,native_pool_bytes=2400,enabled=False,
        countdowns=timing,tug_elapsed_ticks=True,repeat_npc_physics=False,
        timing_native_execution_verified=False)


def bindings(base,prior):
    """Resolve the shared native services without pretending missing ones exist."""
    from aflib import CODE_RAM,CODE_VROM
    # Every service body is retained in the preparation receipt, using complete
    # function boundaries from the pinned N64 symbol directory.
    directory='\n'.join((ROOT/'upstream/af/linker_scripts/jp'/name).read_text() for name in (
        'symbol_addrs_code.txt','symbol_addrs_libultra.txt','symbol_addrs_boot.txt'))
    starts=sorted({int(m[1],16) for m in re.finditer(r'= 0x([0-9A-F]+);[^\n]*type:func',directory)})
    names={n:int(a,16) for n,a in re.findall(r'^(\w+) = 0x([0-9A-F]+);',directory,re.M)}
    files=by_vrom(base);rows=[]
    for name,at in NATIVE_SERVICES.items():
        if at not in starts:raise ValueError('Native service lacks exact symbol boundary: '+name)
        if name in names and names[name]!=at:raise ValueError('Native service symbol disagrees with binding: '+name)
        end=next(p for p in starts if p>at)
        vrom,ram=(0x1060,0x80025C60) if at<CODE_RAM else (CODE_VROM,CODE_RAM)
        raw=files[vrom].extract(base)[at-ram:end-ram]
        if len(raw)!=end-at or end-at<8:raise ValueError('Incomplete native service body: '+name)
        rows.append(dict(name=name,start=at,end=end,vrom=vrom,ram=ram,sha256=sha256(raw)))
    result=dict(NATIVE_SERVICES,af_hp_native_npc_clip=0x80136EEC,
        af_hp_native_shrine=0x80136F70,af_hp_players=0x80126EC0,
        af_hp_native_tools=0x80136F40,af_hp_native_effects=0x80136F3C,
        af_hp_native_animals=0x80130DB8,af_hp_native_ticks=0x80145048,
        af_hp_native_segments=0x801458A0,
        af_hp_native_events=0x801375B0,
        af_hp_visitor=0x801439A0,af_hp_active=0x80136FD8,af_hp_player_index=0x80136EA3)
    npc=prior['equipment_resources']['npc_extra']
    # Runtime exports remain tied to their installed packet, not hardcoded
    # guessed addresses. Locate each exact export once across existing owners.
    for symbol in ('af_holiday_native_type','af_holiday_observers_clip',
                   'af_holiday_transition_maps','af_holiday_map_get','af_decor_actor_resolve',
                   'af_sky_ready','af_sky_continuous','af_sky_adjust'):
        found=set()
        def visit(v):
            if isinstance(v,dict):
                if 'symbols' in v and symbol in v['symbols']:found.add(v['symbols'][symbol])
                for x in v.values():visit(x)
            elif isinstance(v,list):
                for x in v:visit(x)
        visit(npc)
        if len(found)!=1:raise ValueError('Missing or conflicting installed participant service: '+symbol)
        result[symbol]=found.pop()
    result.update(af_sky_native_clip=0x80136F3C,af_effect_random=NATIVE_SERVICES['fqrand'])
    return result,rows


def dialogue(base,prior,generated,*,roots=None,map_symbol='af_hp_message',exercise_controls=False):
    """Convert every personality/role, including the full choice/branch closure."""
    from gc_adapter import remove_redundant_article_suppression,expand_random_message_ranges
    from gc_text import decode_gc
    from runtime_module import module_command_info
    from textcodec import encode,tokenize,LATIN
    from textvalidate import expanded_bound
    from textbanks import Bank
    from v3_camper_text import donor,DONOR_FILES,extend_bank
    from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE
    from v3_holiday_dialogue import credit
    # Complete personality strides from all five NPC ctor base-message tables.
    # Source receipts above pin those tables and every arithmetic selector.
    if roots is None:roots={*range(6520,6592),*range(6605,6701),*range(7661,7769),4396,4397,4398}
    roots=set(roots)
    if not re.fullmatch(r'af_[a-z_]+',map_symbol):raise ValueError('Invalid dialogue export')
    messages,choices,decoder=donor();info=module_command_info(base)
    pending=set(roots);ready={};selects=set();orders=set();edits={};ranges={}
    allowed={0,1,2,3,4,5,9,13,15,16,19,20,21,22,25,26,27,28,80,83,84,94,103}
    # Adapt the actual N64 location, not the idiom "Well, ...". Exact source
    # substrings keep deliberate breaks and every command in place.
    shrine={
        0x112C:('wishing well','shrine'),0x1E09:('wishing well','shrine'),
        0x1E18:('the well','the shrine'),0x1E1E:('the well','the shrine'),
        0x1E27:('That well','That shrine'),0x1E28:('the well','the shrine'),
        0x1E2B:('Wishing Well','Shrine'),0x1E3B:('a well','a shrine'),
        0x1E3E:('wishing well','shrine'),0x1E3F:('the well','the shrine'),
        0x1E4F:('the well','the shrine'),0x1E52:('the well','the shrine'),
    }
    while pending:
        n=min(pending);pending.remove(n)
        if not 0<=n<len(messages):raise ValueError('Participant branch escapes donor bank')
        text,edits[n]=remove_redundant_article_suppression(decode_gc(messages[n],decoder))
        text,ranges[n]=expand_random_message_ranges(text)
        if exercise_controls and 0x3A2A<=n<0x3A32:
            # The imported player controller recognises N64 C-button patterns,
            # not a stick. Keep the complete official instruction and timing;
            # change only the platform nouns/verbs and coloured span length.
            if text.count('C Stick')!=1:raise ValueError('Changed official exercise control wording')
            text=re.sub(r'\{cmd:7F50C3821E0[78]\}C Sticks?',
                '{cmd:7F50C3821E09}C Buttons',text)
            for before,after in (('Tilt that','Press those'),('Tilt your','Press your'),
                    ('tilt that','press those'),('Work that','Work those'),('Lift it up','Press up')):
                text=text.replace(before,after)
            if 'C Stick' in text:raise ValueError('Unadapted exercise controller reference')
        if n in shrine:
            before,after=shrine[n]
            if text.count(before)!=1:raise ValueError('Changed official shrine-location adaptation')
            text=text.replace(before,after)
        data=encode(text,info);tokens=list(tokenize(data,info))
        unknown={t.data[1] for t in tokens if t.kind=='cmd'}-allowed
        if (not tokens or tokens[-1].data not in (b'\x7f\0',b'\x7f\1') or
                sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1 or unknown or
                any(t.kind!='cmd' and (t.kind!='text' or t.data[0] not in LATIN|{0xCD}) for t in tokens) or
                expanded_bound(data,info)>1024):
            raise ValueError(f'Unreviewed participant text/control/buffer: {n:04X}, operations {unknown}')
        ready[n]=data
        for t in tokens:
            if t.kind!='cmd':continue
            op=t.data[1]
            if op==9:
                index,value=t.data[2],int.from_bytes(t.data[3:],'big')
                if not (index==0 and value in {*range(1,24),255} or index==1 and value in (2,10,14) or index==9 and value==1):
                    raise ValueError(f'Unreviewed participant NPC order: {n:04X} / {index}:{value}')
                orders.add((index,value))
            if 14<=op<=24:
                refs=struct.unpack('>'+'H'*((len(t.data)-2)//2),t.data[2:])
                if op<=21:pending.update(set(refs)-ready.keys())
                else:selects.update(refs)
    files=by_vrom(base);cv=prior['import_storage']['choice_vrom']
    mb,tb,cb,ct=(files[p].extract(base) for p in (MESSAGE,TABLE,cv,CHOICE_TABLE))
    first=len(Bank('message',0,0,mb,tb).entries());cf=len(Bank('select',0,0,cb,ct).entries())
    mapping={n:first+i for i,n in enumerate(sorted(ready))}
    choice_map={n:cf+i for i,n in enumerate(sorted(selects))}
    extra=[];new_choices=[];rows=[];credits=[]
    for n,data in sorted(ready.items()):
        out=bytearray(data)
        for t in tokenize(data,info):
            if t.kind=='cmd' and 14<=t.data[1]<=24:
                refs=mapping if t.data[1]<=21 else choice_map
                for at in range(2,len(t.data),2):
                    struct.pack_into('>H',out,t.offset+at,refs[int.from_bytes(t.data[at:at+2],'big')])
        out=bytes(out);extra.append(out)
        adaptations=['Native encoding; retain official wording, line/page breaks, pauses, and demo orders',
            'Remap the complete participant message/choice graph to additive native IDs']
        if edits[n]:adaptations.append('Remove redundant article-suppression flags before native insertions')
        if ranges[n]:adaptations.append('Expand inclusive random-message ranges to equivalent native random branches; retain every target')
        if exercise_controls and 0x3A2A<=n<0x3A32:
            adaptations.append('Assistant platform adaptation: N64 C Buttons replace C Stick; adapt press/work verbs and coloured span while preserving original directions, pauses, and page breaks')
        if n in shrine:adaptations.append('Assistant platform adaptation: '+repr(shrine[n][0])+
            ' → '+repr(shrine[n][1])+'; preserve the N64 shrine identity')
        row=credit(f'message:{mapping[n]:04X}',f'message:{n:04X}',messages[n],out,adaptations)
        row['locales']['en']['locator'][0]='tools/v3_holiday_participants.py:dialogue';credits.append(row)
        rows.append(dict(donor_id=n,id=mapping[n],sha256=sha256(out),bytes=len(out),
            expanded_bound=expanded_bound(out,info)))
    for n,target in choice_map.items():
        data=encode(decode_gc(choices[n],decoder),info)
        if not 1<=len(data)<=20 or any(c not in LATIN for c in data):raise ValueError('Invalid participant choice')
        new_choices.append(data)
        row=credit(f'select:{target:04X}',f'select:{n:04X}',choices[n],data,['Native encoding; unchanged official choice'])
        row['locales']['en']['locator'][0]='tools/v3_holiday_participants.py:dialogue';credits.append(row)
    new_m,new_t=extend_bank(mb,tb,extra,first);new_c,new_ct=extend_bank(cb,ct,new_choices,cf)
    generated.update({'messages.bin':new_m,'message-table.bin':new_t,'choices.bin':new_c,'choice-table.bin':new_ct})
    generated['dialogue.c']=('#include "holiday_participants.h"\n'
        f'int {map_symbol}(int source) {{\n'
        ' static const u16 map[][2]={'+','.join('{'+str(n)+','+str(v)+'}' for n,v in mapping.items())+'};\n'
        ' unsigned int lo=0,hi=sizeof(map)/sizeof(map[0]);\n'
        ' while(lo<hi){unsigned int m=(lo+hi)/2; if(source<map[m][0])hi=m;'
        'else if(source>map[m][0])lo=m+1;else return map[m][1];}return -1;\n}\n')
    return dict(first_id=first,count=len(extra),first_choice=cf,choice_count=len(new_choices),
        rows=rows,roots=sorted(roots),branch_added=sorted(ready.keys()-roots),mapping=mapping,
        choice_mapping=choice_map,npc_orders=sorted(orders),source_banks=DONOR_FILES,
        random_ranges={n:r for n,r in ranges.items() if r},
        provenance_entries=credits,installed=False,max_expanded_bytes=max(r['expanded_bound'] for r in rows),
        resources=[dict(file=name,vrom=vrom,sha256=sha256(data),bytes=len(data),previous_sha256=sha256(previous))
            for name,vrom,data,previous in (('messages.bin',MESSAGE,new_m,mb),('message-table.bin',TABLE,new_t,tb),
                ('choices.bin',cv,new_c,cb),('choice-table.bin',CHOICE_TABLE,new_ct,ct))])


def exercise_registry(base,prior,generated):
    """Extend the existing complete registry, retaining installed controllers.

    Residents and special characters share lifetime/callback services. Only
    allocation/artwork differ, as declared by the shared row kind.
    """
    from v3_registry import EXERCISE_PARTICIPANTS
    old=prior['equipment_resources']['npc_extra']['events']['participants']
    rows=old['registry']['rows']
    if len(rows)!=9 or {r['stem'] for r in rows}!=set(PARTICIPANTS):
        raise ValueError('Changed complete retained participant registry')
    image=by_vrom(base)[0x8C6D80].extract(base)
    raw=image[0x809E4708-0x809E35B0:0x809E4708-0x809E35B0+36]
    profile,part,flags,name,bank,size=struct.unpack_from('>HHIHHI',raw)
    if (profile,part,bank,size)!=(0x93,3<<8,3,0x950):raise ValueError('Changed complete native exercise profile')
    code=['#include "holiday_exercise.h"','#include "actors.h"','#include "constants.h"']
    links={r['donor_profile']:old['code']['symbols'][r['donor_profile']] for r in rows}
    code.extend('extern const ACTOR_PROFILE '+n+';' for n in links)
    code.append('const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={')
    for r in rows:
        code.append('{'+','.join(str(r[k]) for k in ('source','name','profile','event','save','count','part'))+
            ',0,&'+r['donor_profile']+','+str(r['flags'])+'},')
    for r in EXERCISE_PARTICIPANTS:
        code.append('{'+','.join(str(r[k]) for k in ('source','name','profile'))+
            ',mEv_EVENT_MORNING_AEROBICS,mEv_EVENT_SPORTS_FAIR_AEROBICS,'+
            f'{r["count"]},3,{r["kind"]},&Taisou_Npc0_Profile,{flags}'+'},')
    code.append('};')
    links['af_hp_available']=old['code']['symbols']['af_hp_available']
    generated['registry.c']='\n'.join(code)+'\n'
    mapping={r['source']+i:r['name']+i for r in EXERCISE_PARTICIPANTS for i in range(r['count'])}
    constants=generated['constants.h'];overrides=[]
    for match in re.finditer(r'^#define (SP_NPC_EV_TAISOU_\d+|SP_NPC_SONCHO_D078) \(SP_NPC_START \+ (\d+)\)',constants,re.M):
        source=0xD000+int(match[2])
        if source in mapping:overrides.append(f'#undef {match[1]}\n#define {match[1]} 0x{mapping[source]:04X}')
    if len(overrides)!=3 or not constants.endswith('#endif\n'):
        raise ValueError('Incomplete exercise name arithmetic/attendance identity remapping')
    generated['constants.h']=constants[:-7]+'\n'.join(overrides)+'\n#endif\n'
    profiles={r['name']+i:r['profile'] for r in (*rows,*EXERCISE_PARTICIPANTS) for i in range(r['count'])}
    if sorted(profiles)!=list(range(0xD0A0,0xD0B4)):raise ValueError('Noncontiguous complete participant spawn directory')
    generated['spawn-data.c']=('#include "holiday_participants.h"\nconst s16 af_hp_spawn_profiles[20]={'
        +','.join(str(profiles[n]) for n in sorted(profiles))+'};\n')
    return dict(records=list(EXERCISE_PARTICIPANTS),name_mapping=mapping,retained_profiles=links,
        original_profile=profile,native_profile_sha256=sha256(raw),native_flags=flags,
        owner_count=12,resident_count=18,live_count=24,enabled=False),links


def prepare_exercise(output,lock):
    """Compile the whole dancer/card family through the shared source importer.

    Native services stay explicit unresolved symbols until their actual owners
    are connected. No partial conversation, fake inventory, or native-number
    event fallback is generated. Prepared donor code remains local.
    """
    from v3_password_policy import function
    from v3_furniture_install import inputs
    out=output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored preparation')
    base,prior=inputs(lock)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (DONOR/'config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,report=generate(source,family=('taisou_npc0',),
        reference_sha='01c6e63a77a521b137be01f568ee6f76e74e5c4739439dfbde7106058d5d88f1',
        extra_headers=('m_soncho.h','lb_rtc.h'))
    raw=read('src/game/m_soncho.c',report['references'])
    if sha256(raw.encode())!='86925ff50163654cf795045563d93fa9da6859e81c6c5cf5d4e42fcc9bf8bf11':
        raise ValueError('Changed complete card conversation source')
    names=re.findall(r'^(?:static|extern)\s+[^\n;{}=]+?\b(mSC_Radio_\w+|mSCR_talk_\w+)\([^;{}]*\)\s*\{',raw,re.M)
    names.append('mSC_set_free_str_number')
    functions=[];bodies=[]
    for name in names:
        matches=[p for p,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Ambiguous complete exercise dependency: '+name)
        functions.append(source.function(matches[0])[1]);bodies.append(clean(function(raw,name)))
    generated['cards.c']='\n\n'.join(bodies)
    font=read('src/game/m_font.c',report['references'])
    if sha256(font.encode())!='89f63d09c6c6b5c71b9ec2b51ffe3cba9ef89ea89714cec9ad8bef015c2316de':
        raise ValueError('Changed complete number formatter source')
    number_functions=[];pieces=['#include "holiday_exercise.h"',
        '#define CHAR_ZERO 48\n#define CHAR_SPACE 32\n#define CHAR_COMMA 44\n#define TRUE 1\n#define FALSE 0',
        'static const u8 mFont_suji_data[10]="0123456789";']
    for name in ('mMsg_CutLeftSpace','mFont_suji_check','mFont_UnintToString'):
        matches=[p for p,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Ambiguous complete number formatter: '+name)
        number_functions.append(source.function(matches[0])[1]);pieces.append(clean(function(font,name)))
    generated['numbers.c']='\n'.join(pieces)+'\n'
    report['number_functions']=number_functions
    # Constants are selected across both complete owners so actor and card
    # arithmetic retain the same enum values and contiguous source item IDs.
    extra=('m_soncho.h','lb_rtc.h','m_private.h','m_item_name.h','ac_handOverItem.h','m_field_info.h')
    adapter='\n'.join((ROOT/f'overlays/v3/holiday_exercise_{part}.c').read_text()
        for part in ('native','dialogue','world','handover'))
    adapter+='\n'+(ROOT/'overlays/v3/holiday_participants_services.c').read_text()
    generated['constants.h']=constants('\n'.join(generated.values())+'\n'+adapter,
        report['references'],CONSTANT_HEADERS+extra)
    prelude=('#include "holiday_exercise.h"\n#include "constants.h"\n#include "actors.h"\n#include <limits.h>\n'
        '#pragma GCC diagnostic ignored "-Wunused-parameter"\n'
        '#pragma GCC diagnostic ignored "-Wunused-variable"\n'
        'typedef void (*mSCR_TALK_PROC)(TAISOU_NPC0_ACTOR *,GAME_PLAY *);\n'
        'int mSC_Radio_Set_Talk_Proc(TAISOU_NPC0_ACTOR *);\n'
        'void mSC_Radio_Talk_Proc(TAISOU_NPC0_ACTOR *,GAME_PLAY *);\n')
    substitutions=(
        ('Common_Get(now_private)','af_he_private()'),
        ('Common_Get(player_no)','af_he_player()'),
        ('Common_GetPointer(time.rtc_time)','af_he_clock()'),
        ('Common_Get(time.rtc_time)','(*af_he_clock())'),
        ('Common_Get(time.rtc_time.year)','af_he_clock()->year'),
        ('Common_Get(time.rtc_time.month)','af_he_clock()->month'),
        ('Common_Get(time.rtc_time.day)','af_he_clock()->day'),
        ('Common_Get(clip).handOverItem_clip->master_actor','af_he_handover_master()'),
        ('Common_Get(clip).handOverItem_clip->request_mode','af_he_handover_mode()'),
        ('Common_Get(clip).handOverItem_clip->player_after_mode = 8;','af_he_handover_after(8);'),
        ('play->game.frame_counter','af_he_frame(play)'),
        ('play->block_table.block_x','af_he_block_x(play)'),
        ('play->block_table.block_z','af_he_block_z(play)'),
        ('NPC_CLIP->save_proc','af_he_npc_save'),
        # Make the source's implicit unsigned conversion explicit for GCC.
        ('diff < INT_MIN','diff < (u32)INT_MIN'),
        ('mMsg_Get_msg_num(msg_win) == 0x342B','mMsg_Get_msg_num(msg_win) == af_he_message(0x342B)'),
        ('mMsg_Get_msg_num(msg_win) == 0x3428','mMsg_Get_msg_num(msg_win) == af_he_message(0x3428)'),
    )
    for name in ('taisou_npc0.c','cards.c'):
        body=re.sub(r'^#(?:include|pragma)[^\n]*\n','',generated[name],flags=re.M)
        for before,after in substitutions:body=body.replace(before,after)
        if 'Common_Get' in body or 'play->' in body:raise ValueError('Unadapted complete exercise context')
        generated[name]=prelude+body+'\n'
    # Wrap whole callbacks, not individual source statements. A native player
    # cannot change halfway through a borrowed GC Private view; its card record
    # is decoded/committed at each complete callback boundary.
    body=generated['taisou_npc0.c']
    callbacks=(('aTS0_set_talk_info','void','ACTOR *a','a','1','0'),
        ('aTS0_talk_init','int','ACTOR *a,GAME *g','a,g','0','0'),
        ('aTS0_talk_end_chk','int','ACTOR *a,GAME *g','a,g','0','result'))
    for name,ret,args,call,first,end in callbacks:
        original=function(body,name);renamed=original.replace(name+'(',name+'_source(',1)
        wrapper=f'\nstatic {ret} {name}({args}) {{\n'
        wrapper+=f' if(!af_he_begin(a,{first}))return'+(';' if ret=='void' else ' 0;')+'\n'
        if ret=='void':wrapper+=f' {name}_source({call});(void)af_he_finish({end});\n'
        else:wrapper+=f' int result={name}_source({call});return af_he_finish({end})?result:0;\n'
        wrapper+='}\n';body=body.replace(original,renamed+wrapper)
    generated['taisou_npc0.c']=body
    # A rejected native request is retryable. The donor ignores its declared
    # return value, but advancing orders on rejection would wait forever for a
    # handover that never started. Keep each complete source callback intact.
    for mode in (7,8):
        call=f'mPlib_request_main_give_type1((GAME*)play, ITM_EXCERCISE_CARD00, {mode}, FALSE, FALSE)'
        if generated['cards.c'].count(call+';')!=1:raise ValueError('Changed complete card handover request')
        generated['cards.c']=generated['cards.c'].replace(call+';',f'if (!{call}) return;')
    destructor=function(generated['taisou_npc0.c'],'aTS0_actor_dt')
    marker='af_he_forget(actorx);'
    replacement=destructor[:destructor.rfind('}')]+marker+'\n}'
    generated['taisou_npc0.c']=generated['taisou_npc0.c'].replace(destructor,replacement)
    for before,after,count in (
        ('actor->delay_cnt--;','actor->delay_cnt = af_hp_countdown(actor->delay_cnt);',1),
        ('nactorx->draw.frame_speed = 0.5f;',
         'nactorx->draw.frame_speed = 0.5f * (f32)af_hp_elapsed();',1),
        ('NPC_CLIP->move_proc(actorx, game);',
         '((NPC_ACTOR *)actorx)->draw.frame_speed = 0.5f * (f32)af_hp_elapsed();\n        NPC_CLIP->move_proc(actorx, game);',1)):
        if generated['taisou_npc0.c'].count(before)!=count:raise ValueError('Changed exercise elapsed-tick consumer')
        generated['taisou_npc0.c']=generated['taisou_npc0.c'].replace(before,after)
    report['timing']=dict(counter_offset=0xA0,animation_speed_per_tick=.5,
        delay_uses_elapsed_ticks=True,npc_physics_once_per_update=True,native_execution_verified=False)
    generated['clips.c']='#include "holiday_exercise.h"\n#include "actors.h"\n'
    generated['layout.c']=('#include "holiday_exercise.h"\n#include "actors.h"\n#include "holiday_cards.h"\n'
        '_Static_assert(sizeof(TAISOU_NPC0_ACTOR)<=2400,"Complete exercise native pool bound");\n'
        'const unsigned int af_he_actor_bytes=sizeof(TAISOU_NPC0_ACTOR);\n'
        'u8 af_v3_card_state[AF_HC_BYTES];\n')
    sequence=re.search(r'static int animeSeqNo\[\]\s*=\s*\{([^{}]+)\}',generated['taisou_npc0.c'])
    if not sequence:raise ValueError('Missing complete exercise animation table')
    paired=re.findall(r'\baNPC_ANIM_\w+',sequence[1])
    if len(paired)!=13:raise ValueError('Changed complete exercise action count')
    report['motions']=native_motions(source,base,generated,paired=paired)
    report['registry'],retained_profiles=exercise_registry(base,prior,generated)
    # Both exercise schedules, all six personalities, all four resident roles,
    # and Copper. The separate complete Tortimer/card bank is already installed;
    # preserve and reuse it instead of allocating another copy.
    msg_table=re.search(r'static int msg_base\[\]\[mNpc_LOOKS_NUM\]\s*=\s*\{(.*?)\};',
        generated['taisou_npc0.c'],re.S)
    bases=[int(n,16) for n in re.findall(r'0x[0-9A-Fa-f]+',msg_table[1])] if msg_table else []
    if len(bases)!=12:raise ValueError('Changed complete exercise personality table')
    roots={n for start in bases for n in range(start+3,start+15)}|set(range(0x2665,0x266B))
    report['dialogue']=dialogue(base,prior,generated,roots=roots,map_symbol='af_he_participant_message',exercise_controls=True)
    # Only genuine complete-function bindings are resolved here. The remaining
    # card/world/actor providers stay visible in the link report.
    links,native_functions=bindings(base,prior)
    direct={name:links[name] for name in ('Actor_delete','fqrand','none_proc1',
        'mDemo_Check','mDemo_Request','mDemo_Set_ListenAble','mNpc_GetNpcLooks')}
    direct.update(af_he_native_radio=0x800D21CC,af_he_native_status=0x8007FF08,
        af_he_native_message=0x8007B5C0,af_he_native_continue=0x8009DBA4,
        af_he_native_order=0x8007B44C,mDemo_Get_OrderValue=0x8007B49C,
        mMsg_Get_base_window_p=0x8009D1F0,mMsg_Check_MainNormalContinue=0x8009E908,
        mMsg_Get_msg_num=0x8009DBB0,mMsg_Set_LockContinue=0x8009E9E8,
        mMsg_Unset_LockContinue=0x8009E9F8,lbRTC_IsEqualDate=0x800D5164,
        af_he_native_item_string=0x8009D88C,af_he_native_town=0x800950D8,
        af_he_native_sum=0x800B83D4,af_he_native_find=0x800B80B4,
        af_he_native_set=0x800B8B08,af_he_native_give=0x800B8B8C,
        af_he_native_player=0x800B1C84,af_he_native_request_give=0x800B25F4,
        memcpy=0x80034BF8)
    from aflib import CODE_RAM,CODE_VROM
    directory=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt').read_text()
    starts=sorted({int(a,16) for a in re.findall(r'= 0x([0-9A-F]+);[^\n]*type:func',directory)})
    core=by_vrom(base)[CODE_VROM].extract(base);service_rows=[]
    for name,address in direct.items():
        if address<CODE_RAM:
            service_rows.append(next(r for r in native_functions if r['name']==name));continue
        if address not in starts:raise ValueError('Exercise service has no complete native boundary: '+name)
        end=next(a for a in starts if a>address);body=core[address-CODE_RAM:end-CODE_RAM]
        service_rows.append(dict(name=name,start=address,end=end,sha256=sha256(body)))
    direct.update(af_hp_native_npc_clip=links['af_hp_native_npc_clip'],
        af_hp_player_index=links['af_hp_player_index'],af_he_native_rtc=0x80136FBC,
        af_he_native_handover=0x80136F34,
        # Existing installed text/name reader entries, not their old bodies.
        af_he_native_free_string=0x8009D6D0,af_he_native_item_name=0x801969C8)
    for symbol in ('af_hp_private',
            'af_holiday_native_type','af_holiday_native_notify','af_holiday_observers_clip',
            'af_holiday_message','af_holiday_dialogue_data','af_v3_npc_extra_owned'):
        found=set()
        def collect(value):
            if isinstance(value,dict):
                if 'symbols' in value and symbol in value['symbols']:found.add(value['symbols'][symbol])
                for v in value.values():collect(v)
            elif isinstance(value,list):
                for v in value:collect(v)
        collect(prior['equipment_resources']['npc_extra'])
        if len(found)!=1:raise ValueError('Exercise requires one installed provider: '+symbol)
        direct[symbol]=found.pop()
    previous=prior['equipment_resources']['npc_extra']['events']['participants']
    for name,address in previous['code']['symbols'].items():
        if (name.startswith('af_hp_previous_') or name.startswith('af_hp_world_previous_') or
                name in ('af_hp_native_resident_index','af_hp_native_resident_valid','af_hp_uniform',
                    'af_decor_actor_resolve','af_holiday_map_get')):
            direct[name]=address
    for name in ('af_hp_native_events','af_hp_native_ticks','af_hp_native_animals','af_holiday_transition_maps'):
        direct[name]=previous['code']['symbols'][name]
    direct.update({name:address for name,address in NATIVE_SERVICES.items() if name in (
        'af_hp_native_get_save','af_hp_native_reserve_save','af_hp_native_event_status',
        'af_hp_native_event_error','af_hp_native_pool_variant','af_hp_native_sex',
        'af_hp_native_joint_initial','af_hp_native_joint_removed','af_hp_native_joint_refill',
        'af_hp_native_structure')})
    direct.update(retained_profiles)
    equipment=prior['equipment_resources'];npc=equipment['npc_extra']
    world=npc.get('variants',{}).get('modules',{}).get('world',npc['world'])['code']['symbols']
    for name in ('af_diary_calendar_event','af_diary_calendar_event_check','af_holiday_reward_data',
            'af_holiday_world_resolve','af_v3_holiday_count','af_diary_days',
            'af_v3_holiday_select','af_v3_reward_flag'):
        direct[name]=world[name]
    direct['af_holiday_item_display']=equipment['holiday_items']['code']['symbols']['af_holiday_item_display']
    direct['af_holiday_state_dates']=equipment['holiday_state']['code']['symbols']['af_holiday_state_dates']
    direct['af_holiday_native_current']=npc['events']['native_directory']['code']['symbols']['af_holiday_native_current']
    holiday=equipment['holiday_state'];fishing=equipment['holiday_fishing']
    direct.update({n:holiday['code']['symbols'][n] for n in
        ('af_diary_reset','af_diary_valid','af_diary_upgrade','af_diary_player_clear')})
    direct.update({n:holiday['bindings'][n] for n in ('af_v3_require_save_state',
        'af_v3_save_halt','af_v3_save_check_extended','af_v3_save_pack_extended','af_v3_creature_player_clear')})
    direct.update({n:fishing['code']['symbols'][n] for n in
        ('af_holiday_fish_wire_clear_person','af_holiday_fish_wire_reset','af_holiday_fish_wire_valid')})
    direct['af_v3_fishing_state']=fishing['bindings']['af_v3_fishing_state']
    direct['mMsg_Set_free_str']=direct['af_he_native_free_string']
    # Exact native exercise loads/stores establish every new sparse NPC field.
    native=by_vrom(base)[0x8C6D80].extract(base);native_ram=0x809E35B0
    fields=((0x809E3E98,0x8C880188),(0x809E4000,0xE60001B8),
        (0x809E3EEC,0xA48A072C),(0x809E3EF4,0xA48B072E),
        (0x809E392C,0xA08E07C9),(0x809E41C0,0xAC8E07D0),
        (0x809E4274,0xA088072A),(0x809E4278,0xE490073C),
        (0x809E404C,0x8DC300A0),(0x809E427C,0x8CAB00A0),
        (0x809E3658,0x8DD900C8),(0x809E402C,0x0C034873))
    if any(struct.unpack_from('>I',native,at-native_ram)[0]!=word for at,word in fields):
        raise ValueError('Changed exercise NPC native field reader')
    handover=by_vrom(base)[0x858A50].extract(base)
    handover_fields=((0x80964080,0x8C426F34),(0x80964088,0x8C4E0010),
        (0x80964094,0xA045000C),(0x80963F80,0xAD190014),
        (0x80963F9C,0xA58B000E),(0x80963FA8,0x24010007),
        (0x80963FB0,0x24010008),(0x80963FC4,0xA1B0000D),
        (0x8096411C,0xADE4001C))
    if any(struct.unpack_from('>I',handover,at-0x80963DC0)[0]!=word for at,word in handover_fields):
        raise ValueError('Changed native card handover layout or supported modes')
    give_fields=((0x800B2614,0x8C470CF0),(0x800B2618,0x24010040),
        (0x800B2628,0x8C450D10),(0x800B2670,0x8C5911D4))
    if any(struct.unpack_from('>I',core,at-CODE_RAM)[0]!=word for at,word in give_fields):
        raise ValueError('Changed native give request player context')
    out.mkdir(parents=True)
    for name,body in generated.items():write_new(out/name,body if isinstance(body,bytes) else body.encode())
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            text=True,capture_output=True,check=True,timeout=60).stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
        '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
        '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror',
        '-I/source/overlays/v3','-I/out','-DAF_HP_EXERCISE_REGISTRY=1']
    modules=[name for name in generated if name.endswith('.c')]
    modules.append('/source/overlays/v3/holiday_exercise_native.c')
    modules.append('/source/overlays/v3/holiday_exercise_dialogue.c')
    modules.append('/source/overlays/v3/holiday_exercise_world.c')
    modules.append('/source/overlays/v3/holiday_exercise_handover.c')
    modules.extend('/source/overlays/v3/holiday_participants_'+part+'.c'
        for part in ('registry','services','storage','world'))
    modules.append('/source/overlays/v3/holiday_participants_spawn.S')
    run('gcc',*flags,*modules)
    objects=[Path(name).stem+'.o' for name in modules]
    run('ld','-EB','-r',*(f'--defsym={n}=0x{v:X}' for n,v in direct.items()),*objects,'-o','exercise.o')
    storage_defines=[f for f in prior['equipment_resources']['diaries']['compiled']['flags'] if f.startswith('-D')]
    storage_defines+=['-DAF_V3_HOLIDAY_STORAGE=1','-DAF_V3_FISHING_STORAGE=1','-DAF_V3_CARD_STORAGE=1']
    storage=['holiday_cards','save_compressed','console_storage']
    run('gcc',*flags,*storage_defines,*(f'/source/overlays/v3/{name}.c' for name in storage))
    run('ld','-EB','-r',*(name+'.o' for name in storage),'-o','card-storage.o')
    # One connected object supplies the actual card-state getter, codec, and
    # runtime. Final installation must redirect every existing save caller and
    # extend scratch before this format can be used.
    run('ld','-EB','-r',*(f'--defsym={n}=0x{v:X}' for n,v in direct.items()),
        *objects,'card-storage.o','-o','exercise.o')
    report.update(category='complete-exercise-card',card_functions=functions,
        base_sha256=sha256(base),base_abi=prior['runtime_abi'],native_field_readers=fields,
        native_field_owner_sha256=sha256(native),
        handover=dict(native_sha256=sha256(handover),native_field_readers=handover_fields,
            give_field_readers=give_fields,retry_rejected_request=True,native_execution_verified=False),
        bindings=direct,native_services=service_rows,
        storage=dict(save_format=14,serialized_bytes=48,installed=False,
            sha256=sha256((out/'card-storage.o').read_bytes()),size=run('size','card-storage.o'),
            defines=storage_defines,unbound_services=run('nm','--undefined-only','card-storage.o').strip().splitlines()),
        unbound_services=run('nm','--undefined-only','exercise.o').strip().splitlines(),
        object=dict(sha256=sha256((out/'exercise.o').read_bytes()),compiler=IMAGE,flags=flags,
            size=run('size','exercise.o'),linked=False),
        sources={p:sha256((ROOT/p).read_bytes()) for p in ('tools/v3_holiday_participants.py',
            'overlays/v3/holiday_participants.h','overlays/v3/holiday_exercise.h',
            'overlays/v3/holiday_exercise_native.c','overlays/v3/holiday_exercise_dialogue.c',
            'overlays/v3/holiday_exercise_world.c',
            'overlays/v3/holiday_exercise_handover.c',
            'overlays/v3/holiday_participants_registry.c','overlays/v3/holiday_participants_services.c',
            'overlays/v3/holiday_participants_storage.c','overlays/v3/holiday_participants_world.c',
            'overlays/v3/holiday_participants_spawn.S','tools/v3_registry.py',
            'overlays/v3/holiday_cards.c','overlays/v3/holiday_cards.h',
            'overlays/v3/console_storage.c','overlays/v3/console_storage.h',
            'overlays/v3/save_compressed.c','overlays/v3/save_compressed.h','tools/gc_adapter.py')})
    write_new(out/'prepared.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def prepare(output,lock,reuse=None):
    out=output.resolve()
    if out.exists() or not out.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored preparation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (DONOR/'config/GAFE01_00/foresta/symbols.txt').read_bytes())
    from v3_furniture_install import inputs
    generated,report=generate(source);base,prior=inputs(lock)
    out.mkdir(parents=True)
    report['rope']=rope_artwork(source,out,generated,reuse)
    report['motions']=native_motions(source,base,generated)
    report['currency']=money(source,base,generated)
    report['dialogue']=dialogue(base,prior,generated)
    report['registry']=registry(base,report,generated)
    report['world']=world(base,prior,source,generated)
    report['hooks']=hooks(base,prior,generated,report['world']['native_reader_hooks'])
    report['coin']=coin(source,base,prior,out,generated,reuse)
    links,report['native_functions']=bindings(base,prior)
    links.update(report['hooks']['bindings'])
    report['bindings']=links
    report['base_sha256']=sha256(base);report['base_abi']=prior['runtime_abi']
    for name,body in generated.items():write_new(out/name,body if isinstance(body,bytes) else body.encode())
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            text=True,capture_output=True,check=True,timeout=60).stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
        '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
        '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror',
        '-I/source/overlays/v3']
    files=[name for name in generated if name.endswith(('.c','.S'))]
    files+=['/source/overlays/v3/holiday_participants_'+part+'.c'
        for part in ('native','registry','services','storage','draw','world')]
    files+=['/source/overlays/v3/holiday_participants_spawn.S']
    files+=['/source/overlays/v3/holiday_coin.c']
    objects=[Path(name).stem+'.o' for name in files]
    if len(set(objects))!=len(objects):raise ValueError('Colliding connected compile units')
    run('gcc',*flags,'-I/out',*files)
    run('ld','-EB','-r',*(f'--defsym={n}=0x{v:X}' for n,v in links.items()),*objects,'-o','participants.o')
    report['unbound_services']=run('nm','--undefined-only','participants.o').strip().splitlines()
    report['object']=dict(sha256=sha256((out/'participants.o').read_bytes()),
        compiler=IMAGE,flags=flags,size=run('size','participants.o'),linked=False)
    report['sources']={p:sha256((ROOT/p).read_bytes()) for p in (
        'tools/v3_holiday_participants.py','overlays/v3/holiday_participants.h',
        'overlays/v3/holiday_participants_native.c','overlays/v3/holiday_participants_registry.c',
        'overlays/v3/holiday_participants_services.c','overlays/v3/holiday_participants_storage.c',
        'overlays/v3/holiday_participants_draw.c','tools/v3_registry.py',
        'overlays/v3/holiday_participants_world.c',
        'overlays/v3/holiday_participants_spawn.S',
        'overlays/v3/holiday_coin.h','overlays/v3/holiday_coin.c',
        'tools/v3_sound_programs.py','tools/v3_villager_audio.py','tools/v3_furniture_materials.py',
        'tools/v3_furniture_art.py','tools/v3_furniture_pipeline.py')}
    write_new(out/'prepared.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--build-lock',type=Path,required=True)
    p.add_argument('--reuse',type=Path,help='Reuse identical complete rope conversion from a prior preparation')
    p.add_argument('--exercise',action='store_true',help='Prepare the complete exercise actor/card family using the same source importer')
    args=p.parse_args()
    try:
        result=prepare_exercise(args.output,args.build_lock) if args.exercise else prepare(args.output,args.build_lock,args.reuse)
    except subprocess.CalledProcessError as e:
        print(e.stderr);raise
    print(json.dumps(dict(family=len(result['family']),object=result['object'],
        unbound_services=result['unbound_services']),indent=2))
