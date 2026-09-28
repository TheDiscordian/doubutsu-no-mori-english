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


def constants(text,receipts):
    """Select complete source enums/macros, including their dependencies."""
    known={};blocks=[]
    for header in CONSTANT_HEADERS:
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


def generate(source):
    from v3_password_policy import function
    receipts={};modules={};headers=[];contracts=[]
    for stem in FAMILY:
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
        # Three donor files declare a talk_request that has no definition or
        # call; preserve every implemented function and remove only that unused
        # prototype. GCC otherwise diagnoses the original declaration as dead.
        for match in list(re.finditer(r'^static void (\w+_talk_request)\([^;{}]*\);',body,re.M)):
            if len(re.findall(r'\b'+match[1]+r'\b',body))==1:
                body=body.replace(match[0],'')
        modules[stem]=body
        contracts.append(dict(name=stem,profile=profile,functions=functions,
            profile_offset=profile_at,profile_sha256=sha256(source.raw(profile)),
            profile_relocations=refs))
    header='\n'.join(headers)
    source_constants=constants(header+'\n'+'\n'.join(modules.values()),receipts)
    if sha256(json.dumps(receipts,sort_keys=True,separators=(',',':')).encode())!=REFERENCES_SHA:
        raise ValueError('Changed complete controller/participant source references')
    prelude=('#include "holiday_participants.h"\n#include "constants.h"\n'
        '#include "actors.h"\n#pragma GCC diagnostic ignored "-Wunused-parameter"\n')
    # Shared clips contain source-generated callbacks but never alias a native
    # clip with a different lifecycle or event record.
    header+='\nextern aTKC_clip_c *af_hp_tokyoso_clip;\nextern aHTMD_clip_c *af_hp_hatumode_clip;\n'
    generated={stem+'.c':prelude+body for stem,body in modules.items()}
    generated.update({'constants.h':source_constants,'actors.h':header})
    # One connected partial link resolves all source-to-source references.
    generated['clips.c']=('#include "holiday_participants.h"\n#include "actors.h"\n'
        'aTKC_clip_c *af_hp_tokyoso_clip;\naHTMD_clip_c *af_hp_hatumode_clip;\n')
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
            ('eEC_CLIP->make_effect_proc','af_coin_create'),('eEC_CLIP->effect_make_proc','af_coin_request'),
            ('eEC_CLIP->set_continious_env_proc','af_sky_continuous'),('sAdo_OngenTrgStart','af_coin_sound')):
            body=body.replace(before,after)
        # The source truncates then wraps its random 16-bit rotations.
        body=body.replace('= RANDOM_F(65535);','= (s16)(int)RANDOM_F(65535);')
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
    # Water identities are already verified by the complete insect importer.
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
        landing_geometry='Complete source shrine-relative height; native shrine landing needs review')


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


def native_motions(source,base,generated):
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


def dialogue(base,prior,generated):
    """Convert every personality/role, including the full choice/branch closure."""
    from gc_adapter import remove_redundant_article_suppression
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
    roots={*range(6520,6592),*range(6605,6701),*range(7661,7769),4396,4397,4398}
    messages,choices,decoder=donor();info=module_command_info(base)
    pending=set(roots);ready={};selects=set();orders=set();edits={}
    allowed={0,1,2,3,4,5,9,13,15,16,22,25,26,27,28,80,83,84,94}
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
        'int af_hp_message(int source) {\n'
        ' static const u16 map[][2]={'+','.join('{'+str(n)+','+str(v)+'}' for n,v in mapping.items())+'};\n'
        ' unsigned int lo=0,hi=sizeof(map)/sizeof(map[0]);\n'
        ' while(lo<hi){unsigned int m=(lo+hi)/2; if(source<map[m][0])hi=m;'
        'else if(source>map[m][0])lo=m+1;else return map[m][1];}return -1;\n}\n')
    return dict(first_id=first,count=len(extra),first_choice=cf,choice_count=len(new_choices),
        rows=rows,roots=sorted(roots),branch_added=sorted(ready.keys()-roots),mapping=mapping,
        choice_mapping=choice_map,npc_orders=sorted(orders),source_banks=DONOR_FILES,
        provenance_entries=credits,installed=False,max_expanded_bytes=max(r['expanded_bound'] for r in rows),
        resources=[dict(file=name,vrom=vrom,sha256=sha256(data),bytes=len(data),previous_sha256=sha256(previous))
            for name,vrom,data,previous in (('messages.bin',MESSAGE,new_m,mb),('message-table.bin',TABLE,new_t,tb),
                ('choices.bin',cv,new_c,cb),('choice-table.bin',CHOICE_TABLE,new_ct,ct))])


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
    files+=['/source/overlays/v3/holiday_participants_'+part+'.c' for part in ('native','registry','draw','world')]
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
    args=p.parse_args()
    try:
        result=prepare(args.output,args.build_lock,args.reuse)
    except subprocess.CalledProcessError as e:
        print(e.stderr);raise
    print(json.dumps(dict(family=len(result['family']),object=result['object'],
        unbound_services=result['unbound_services']),indent=2))
