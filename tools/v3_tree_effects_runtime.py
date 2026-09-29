"""Bind the complete donor tree/leaf/young-tree category to native services.

Generated source remains local. Preparation and installation preserve complete
resources; item admission remains part of the shared carried-item selector.
"""
import json
import copy
from pathlib import Path
import re
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source
from v3_password_policy import function
from v3_scenery import consumers,palettes
from v3_tree_effects import checked

RAM,ART_RAM,END=0x80780000,0x80788000,0x807AC000
PAGE_TABLE=RAM+0x7000
REFERENCES={
    'src/actor/ac_effectbg.c':'28ded65985307a482a31f22e50f3e99b2c1ebb36671b2d957005ca48e0d97782',
    'src/effect/ef_bush_happa.c':'4433ab8f400d060fa617c052fe829355bb6ea19b39758a1b57d2488f1b1e9647',
    'src/effect/ef_young_tree.c':'d507516ba3b25032a5a669eb954a2f598a02507d8bb9cced844a946eba8315ce',
    'include/ac_effectbg.h':'9f070e1b66bcb9bcfbce90aa942a4cd1d9047a7c927d728809eca5a204d595a5'}
SOURCES=('tools/v3_tree_effects.py','tools/v3_tree_effects_runtime.py','tools/v3_furniture_art.py',
    'tools/v3_scenery.py','tools/v3_asset_loader.py','tools/v3_furniture_install.py','tools/v3_room_goods.py',
    'tools/v3_holiday_sky.py','tools/v3_physical_resources.py','tools/v3_room_effects.py',
    'overlays/v3/tree_effects.h','overlays/v3/tree_effects.c','overlays/v3/tree_effects.ld',
    'overlays/v3/paged_resource.h','overlays/v3/resource_dma.h',
    'overlays/v3/effect_loader.c','overlays/v3/surface_bootstrap.c')


def relocate_art_pages(image,records,equipment,first,end,*,excluded_spans=()):
    """Move complete checked art pages that obstruct a growing ROM resource."""
    import v3_physical_resources as physical
    physical.verify(image,records)
    effect=equipment['scenery']['tree_effects'];art=effect['art_packet'];packet=effect['packet']
    pages={r['id']:r for r in art['physical_resources']}
    blockers=[r for r in records if r['physical']<end and first<r['physical']+r['bytes']]
    if not blockers:return image,records,[],[]
    packet_row=next((r for r in records if r['id']==packet['id']),None)
    parent_blocked=packet_row in blockers
    if any(pages.get(r['id'])!=r and r!=packet_row for r in blockers):
        raise ValueError('Resource growth encounters non-page physical ownership')
    if parent_blocked and any(packet_row[k]!=packet[k] for k in ('physical','bytes','sha256')):
        raise ValueError('Changed complete tree startup owner')
    raw=bytearray(image[packet['physical']:packet['physical']+packet['bytes']])
    at=art['directory_ram']-packet['ram'];addresses=art['page_addresses']
    expected=struct.pack('>'+str(5+len(addresses))+'I',0x41465047,art['bytes'],4096,
        len(addresses),*addresses,art['crc32'])
    payload=b''.join(image[a:a+4096] for a in addresses)
    if (sha256(raw)!=packet['sha256'] or raw[at:at+len(expected)]!=expected or
            len(payload)!=art['bytes'] or sha256(payload)!=art['sha256'] or
            zlib.crc32(payload)!=art['crc32']):
        raise ValueError('Changed complete paged artwork or directory')
    staged=bytearray(image);records=copy.deepcopy(records);writes=[];moves=[];remap={}
    original_packet=bytes(raw)
    for old in blockers:
        if old==packet_row:continue
        data=bytes(staged[old['physical']:old['physical']+old['bytes']])
        new=physical.allocate(staged,records,data,old['id']+'-relocation',best_fit=True,
            excluded_spans=(*excluded_spans,(first,end)))
        new['id']=old['id'];records[records.index(old)]=new
        staged[old['physical']:old['physical']+old['bytes']]=bytes(old['bytes'])
        staged[new['physical']:new['physical']+new['bytes']]=data
        writes.append((new,data));moves.append(dict(previous=dict(old),replacement=dict(new)))
        remap[old['physical']]=new['physical'];pages[old['id']]=new
    art['page_addresses']=[remap.get(a,a) for a in addresses]
    art['physical_resources']=[pages[r['id']] for r in art['physical_resources']]
    struct.pack_into('>'+str(len(addresses))+'I',raw,at+16,*art['page_addresses'])
    old_sha=packet['sha256'];packet.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    row=next(r for r in records if r['id']==packet['id'])
    if parent_blocked:
        old=dict(row)
        new=physical.allocate(staged,records,bytes(raw),old['id']+'-relocation',best_fit=True,
            excluded_spans=(*excluded_spans,(first,end)))
        new['id']=old['id'];records[records.index(row)]=new
        edits=[dict(offset=at+16+i*4,before=original_packet[at+16+i*4:at+20+i*4].hex(),
                    after=raw[at+16+i*4:at+20+i*4].hex())
               for i in range(len(addresses)) if addresses[i]!=art['page_addresses'][i]]
        moves.append(dict(previous=old,replacement=dict(new),tree_directory_edits=edits))
        staged[old['physical']:old['physical']+old['bytes']]=bytes(old['bytes'])
        packet['physical']=new['physical'];writes.append((new,bytes(raw)))
    else:
        row['sha256']=packet['sha256'];writes.append((dict(row,previous_sha256=old_sha),bytes(raw)))
    staged[packet['physical']:packet['physical']+packet['bytes']]=raw
    field=equipment.get('carried_items',{}).get('field_creatures')
    if field:
        if field['packet']['id']!=packet['id'] or field['packet']['sha256']!=old_sha:
            raise ValueError('Changed shared field/tree page owner')
        field['packet']=copy.deepcopy(packet)
    if b''.join(staged[a:a+4096] for a in art['page_addresses'])!=payload:
        raise ValueError('Relocation loses complete paged artwork')
    physical.verify(staged,records)
    return staged,records,writes,moves


def read(name):
    data=(ROOT/'local/ac-decomp'/name).read_bytes()
    if sha256(data)!=REFERENCES[name]:raise ValueError('Changed complete tree-effect source: '+name)
    text=re.sub(r'/\*.*?\*/|//[^\n]*','',data.decode(),flags=re.S)
    return re.sub(r'^\s*#include[^\n]*','',text,flags=re.M)


def runtime_art(source,art,data):
    """Bind complete shared graphics/CPU resources without runtime segment-6 use."""
    if len(data)!=art['object']['object_bytes'] or sha256(data)!=art['object']['object_sha256']:
        raise ValueError('Changed complete tree-effect resource binding')
    body=bytearray(data);relocations=[];symbols={'af_tree_art':ART_RAM}
    def fix(at,target,cpu):
        if at&3 or not 0<=at<=len(data)-4 or not 0<=target<len(data) or u32(data,at)!=0x06000000+target:
            raise ValueError('Invalid complete tree-effect resource binding')
        value=ART_RAM+target
        if not cpu:value&=0x1FFFFFFF
        struct.pack_into('>I',body,at,value);relocations.append(dict(offset=at,target=target,cpu=cpu))
    row=art['object']
    for model in row['compiled_models']:
        start=model['native_offset'];stop=start+model['bytes']
        for at in range(start,stop,8):
            a,b=struct.unpack_from('>2I',data,at)
            if a>>24 in (1,0xFD,0xDE,0xDA) and b>>24==6:fix(at+4,b&0xFFFFFF,False)
    for rig in row['rigs']:
        symbols[rig['header']['symbol']]=ART_RAM+rig['header']['native_offset']
        for p in rig['relocations']:fix(p['offset'],p['target_offset'],p['offset']==rig['header']['native_offset']+4)
    animations=row['compiled_animations']
    for p in animations['relocations']:fix(p['offset'],p['target_offset'],True)
    for header in animations['headers']:symbols[header['symbol']]=ART_RAM+header['native_offset']
    for model in row['compiled_models']:symbols[model['symbol']]=(ART_RAM+model['native_offset'])&0x1FFFFFFF
    if len({r['offset'] for r in relocations})!=len(relocations):raise ValueError('Duplicate tree-effect relocation')
    symbols['af_tree_palette_data']=ART_RAM+len(body)
    for family in ('cedar','palm','gold'):
        receipt,pal=palettes(source,consumers(source),family)
        if receipt!=art['palettes'][family]:raise ValueError('Changed complete effect palette family')
        body.extend(pal)
    selectors={tuple(p['term_indices']) for p in art['palettes'].values()}
    if len(selectors)!=1:raise ValueError('Tree palette families need distinct selectors')
    symbols['af_tree_palette_terms']=ART_RAM+len(body);body.extend(bytes(selectors.pop()))
    body.extend(bytes(-len(body)%16))
    if ART_RAM+len(body)>END:raise ValueError('Complete tree-effect data exceeds its reservation')
    return bytes(body),symbols,dict(bytes=len(body),ram=ART_RAM,sha256=sha256(body),
        relocations=relocations,original_art_bytes=len(data),all_palette_frames=42,
        segment_six_rebound=True,art_source_sha256=sha256(data))


def generate(art):
    header=read('include/ac_effectbg.h')
    if header.count('#define EffectBg_JOINT_NUM 4')!=1:raise ValueError('Changed donor joint workspace')
    # Native cKF writes one root translation plus one rotation per joint.
    header=header.replace('#define EffectBg_JOINT_NUM 4','#define EffectBg_JOINT_NUM 6')
    header=header.replace('extern ACTOR_PROFILE Effectbg_Profile;','')
    actor=read('src/actor/ac_effectbg.c')
    actor,n=re.subn(r'ACTOR_PROFILE Effectbg_Profile = \{.*?\};','',actor,count=1,flags=re.S)
    if n!=1:raise ValueError('Missing complete source actor profile')
    actor=actor.replace(function(actor,'EfbgBgitemTreeCheck'),
        'static int EfbgBgitemTreeCheck(xyz_t pos) {return af_tree_collision(pos);}')
    # All source tables remain ordered and complete; only writable qualification
    # changes because callbacks never modify the model/animation directories.
    actor=re.sub(r'(static cKF_(?:Skeleton|Animation)_R_c\*) (\w+_tbl)',r'\1 const \2',actor)
    actor=actor.replace('mFI_GetFieldPal()','af_tree_palettes()')
    actor=actor.replace('play->game_frame','af_tree_frame(play)')
    actor=actor.replace('Common_Get(time).season','af_tree_season()').replace('Common_Get(time).term_idx','af_tree_term()')
    # Retain complete source motion, impact, leaf emissions, and expiry at two
    # donor ticks per 30-Hz native update. Keep its initial cKF play as written.
    actor=actor.replace('EffectBG_object_move(efbg, game);',
        'EffectBG_object_move(efbg, game);\n'
        '            if(efbg->status & EffectBg_STATUS_ACTIVE)EffectBG_object_move(efbg, game);')
    actor+='''
const u32 af_tree_actor_bytes=sizeof(EFFECTBG_ACTOR);
const u32 af_tree_joint_vectors=EffectBg_JOINT_NUM;
void af_tree_actor_ct(ACTOR *a,GAME *g) {
    if(af_tree_resources()){Effectbg_actor_ct(a,g);CLIP(make_effect_bg_proc)=af_tree_make;}
}
void af_tree_actor_dt(ACTOR *a,GAME *g) {
    Effectbg_actor_dt(a,g);efbg_start_p=NULL;CLIP(make_effect_bg_proc)=NULL;
}
void af_tree_actor_mv(ACTOR *a,GAME *g) {if(efbg_start_p)Effectbg_actor_move(a,g);}
void af_tree_actor_dw(ACTOR *a,GAME *g) {
    if(!efbg_start_p || !af_tree_draw_space(g))return;
    mFM_field_pal_c *p=af_tree_palettes();EFFECTBG_ACTOR *e=(EFFECTBG_ACTOR *)a;
    e->tree_pal=p->cedar_tree_pal;e->palm_pal=e->palm_pal2=p->palm_tree_pal;e->gold_pal=p->golden_tree_pal;
    Effectbg_actor_draw(a,g);osWritebackDCache(e->effect,sizeof(e->effect));
}
void af_tree_make(GAME *g,s16 type,s16 variant,xyz_t *pos) {
    if(!pos || !efbg_start_p || (unsigned int)type>=5 || !af_tree_admit(variant))return;
    /* A reused slot must not retain the prior tree's family/impact bits. */
    if(variant==-1 || variant==4 || variant==8 || variant==13) {
        /* Source small-tree leaf creation reads the first slot. Preserve its
           active animation, but supply this request's family temporarily. */
        u8 status=efbg_start_p->status;s16 previous=efbg_start_p->variant;
        efbg_start_p->status=0;efbg_start_p->variant=variant;
        Make_EffectBG(g,type,variant,pos);
        efbg_start_p->status=status;efbg_start_p->variant=previous;
    } else Make_EffectBG(g,type,variant,pos);
}
'''
    # Clear all transient family/impact/angle state on constructor entry, including
    # the full-pool replacement route. Always reset the source impact position.
    marker='    cKF_Skeleton_R_c* skeleton;'
    if actor.count(marker)!=1:raise ValueError('Changed complete tree constructor')
    actor=actor.replace(marker,marker+'\n    efbg->status=0;efbg->add_angle=0;efbg->leaf_angle=0;'
        '\n    efbg->effect_pos=efbg->base_pos;efbg->effect_pos.y+=90.0f;')
    modules={'actor.c':'#include "tree_effects.h"\n'+header+
        '\nvoid af_tree_make(GAME *,s16,s16,xyz_t *);\n'+actor}
    for kind,stem,prefix in (('leaf','bush_happa','eBushHappa'),('young','young_tree','eYoung_Tree')):
        text=read('src/effect/ef_'+stem+'.c')
        text=re.sub(r'eEC_PROFILE_c iam_ef_\w+ = \{.*?\};','',text,flags=re.S)
        text=text.replace('mFI_GetFieldPal()','af_tree_palettes()')
        text=text.replace('Common_Get(time).term_idx','af_tree_term()').replace('Common_Get(time.season)','af_tree_season()')
        if kind=='leaf':
            # Existing shrub callers keep native effect 51. Only tree particles
            # use the additional profile, and its public init enforces arg1>3.
            text=text.replace('extern Gfx ef_s_yabu01_00_modelT[];','')
            text=text.replace('gSPDisplayList(NEXT_POLY_XLU_DISP,ef_s_yabu01_00_modelT);','return;')
            gate='if((b&0x0FFF)<4 || (b&0x0FFF)>7)return;'
        else:
            ct=function(text,'eYoung_Tree_ct')
            ct=ct.replace('GAME_PLAY* play = (GAME_PLAY*)game;','').replace('Camera2* camera = &play->camera;','')
            ct=ct.replace('f32 dist = search_position_distance(&camera->lookat.eye, &camera->lookat.center);','')
            ct=ct.replace('xyz_t_sub(&camera->lookat.eye, &camera->lookat.center, &effect->offset);',
                'af_tree_camera(game,&effect->offset);')
            ct=ct.replace('xyz_t_mult_v(&effect->offset, 1.0f / dist);','')
            text=text.replace(function(text,'eYoung_Tree_ct'),ct)
            gate='if((unsigned int)b>3 || (unsigned int)a>=5)return;'
        text+='\n'+f'''void af_tree_{kind}_init(xyz_t p,int priority,s16 angle,GAME *g,u16 item,s16 a,s16 b) {{
    {gate}
    if(af_tree_ready(g)){prefix}_init(p,priority,angle,g,item,a,b);
}}
void af_tree_{kind}_ct(RoomEffect *e,GAME *g,void *arg) {{
    if(af_tree_ready(g)){prefix}_ct(e,g,arg);else e->timer=0;
}}
void af_tree_{kind}_mv(RoomEffect *e,GAME *g) {{
    if(!af_tree_ready(g)){{e->timer=0;return;}}{prefix}_mv(e,g);
    if(e->timer>1){{--e->timer;{prefix}_mv(e,g);}}
}}
void af_tree_{kind}_dw(RoomEffect *e,GAME *g) {{
    if(af_tree_ready(g) && af_tree_draw_space(g)){prefix}_dw(e,g);
}}
'''
        modules[kind+'.c']='#include "tree_effects.h"\n'+text
    if any(re.search(r'\b(Common_Get|Camera2|ACTOR_PROFILE|eEC_PROFILE_c)\b',text) for text in modules.values()):
        raise ValueError('Unbound tree-effect source service')
    declarations={r['symbol'] for r in art['functions']}
    if len(declarations)!=22 or any(not re.search(r'\b'+name+r'\s*\(',''.join(modules.values())) for name in declarations):
        raise ValueError('Incomplete donor tree-effect callbacks')
    pragma='#pragma GCC diagnostic ignored "-Wunused-parameter"\n'
    return {name:pragma+code for name,code in modules.items()}


def bindings(base,prior):
    text='\n'.join((ROOT/f'upstream/af/linker_scripts/jp/symbol_addrs_{part}.txt').read_text()
        for part in ('code','boot','libultra'))
    symbols={n:int(a,16) for n,a in re.findall(r'^(\w+) = 0x([0-9A-Fa-f]+);',text,re.M)}
    starts=sorted({int(a,16) for a in re.findall(r'^\w+ = 0x([0-9A-Fa-f]+);[^\n]*type:func',text,re.M)})
    names=('fqrand','fqrand2','qrand','sqrtf','sin_s','cos_s','xyz_t_add','xyz_t_sub','xyz_t_mult_v',
        'search_position_distance','add_calc_short_angle2','mFI_GetUnitFG','mCoBG_GetBgY_AngleS_FromWpos',
        'mFI_Wpos2UtNum_inBlock','mFI_UtNum2CenterWpos','sAdo_OngenTrgStart','cKF_SkeletonInfo_R_ct',
        'cKF_SkeletonInfo_R_init_standard_stop','cKF_SkeletonInfo_R_play','cKF_Si3_draw_R_SV',
        'Matrix_translate','Matrix_scale','Matrix_Position_VecX','Matrix_RotateVector','suMtxMakeSRT_ZXY',
        '_Matrix_to_Mtx_new','_texture_z_light_fog_prim','_texture_z_light_fog_prim_xlu','osWritebackDCache','memcpy')
    files=by_vrom(base);link={};receipts=[]
    for name in names:
        lo=symbols[name];hi=next(a for a in starts if a>lo)
        vrom,ram=(0x1060,0x80025C60) if lo<CODE_RAM else (CODE_VROM,CODE_RAM)
        data=files[vrom].extract(base)[lo-ram:hi-ram]
        if not data or len(data)!=hi-lo:raise ValueError('Incomplete native tree-effect service: '+name)
        link[name]=lo;receipts.append(dict(symbol=name,vrom=vrom,address=lo,bytes=len(data),sha256=sha256(data)))
    scene=prior['equipment_resources']['scenery'];bootstrap=scene['bootstrap']
    link['af_tree_load']=bootstrap['symbols']['load']
    link['af_v3_tree_player_query']=scene['code']['symbols']['af_v3_tree_player_query']
    link['tree_rule']=scene['code']['symbols']['tree_rule']
    carried=prior['equipment_resources']['carried_items']
    link['af_carried_category']=carried['code']['symbols']['af_carried_category']
    link['af_v3_player_selected_equipment']=prior['equipment_resources']['player_actions']['code']['symbols']['af_v3_player_selected_equipment']
    link.update(af_tree_native_term=0x800CA070,af_tree_native_season=0x80136FAC,
        af_tree_make_clip=0x80136F5C,af_tree_native_owner=0x80101B80,
        af_tree_native_player=0x8010DD1C,af_tree_unit_height=0x80072530,
        af_tree_dma=0x80026B44,af_tree_crc=0x80195938,af_tree_fault=0x80029AB4,
        af_tree_art_pages=PAGE_TABLE,af_tree_art_crc=PAGE_TABLE+160)
    for alias,name in (('ct','cKF_SkeletonInfo_R_ct'),('stop','cKF_SkeletonInfo_R_init_standard_stop'),
            ('play','cKF_SkeletonInfo_R_play'),('draw','cKF_Si3_draw_R_SV')):
        link['af_tree_keyframe_'+alias]=link.pop(name)
    owner=files[0x8E46A0].extract(base);reloc=files[0x8E6640].extract(base)
    if (sha256(owner)!='39c749d2cbcd5d3078a9aade88a5c38c04e8da96fc7f671a8d1bd768af6e3c9b' or
            sha256(reloc)!='6b5606a7f72134e407eca6716994678065db62672b7db756cdd5ca70ddc4be6f'):
        raise ValueError('Changed complete native tree-effect owner')
    core=files[CODE_VROM].extract(base)
    desc=core[0x80101B70-CODE_RAM:0x80101B90-CODE_RAM]
    if desc!=bytes.fromhex('008e46a0008e664080a1cbd080a1eb800000000080a1eaf80000000000000000'):
        raise ValueError('Changed native tree actor descriptor')
    return link,dict(functions=receipts,actor=dict(vrom=0x8E46A0,reloc=0x8E6640,ram=0x80A1CBD0,
        sha256=sha256(owner),reloc_sha256=sha256(reloc),descriptor=desc.hex(),
        descriptor_address=0x80101B70,profile=0x1F28,original_actor_bytes=0xCF0),
        camera_vectors=[0x1A60,0x1A6C],source_ticks_per_native_update=2,
        shared_scene_code_sha256=scene['code']['sha256'],shared_bootstrap_sha256=bootstrap['sha256'])


def prepare(source,directory,art_directory,base,prior):
    from v3_console_disk_install import reservations
    directory=directory.resolve()
    if directory.exists() or not directory.is_relative_to(ROOT/'build'):
        raise ValueError('Use a fresh ignored tree-effect preparation')
    if any(a<END and RAM<b for a,b in reservations(prior)):
        raise ValueError('Tree effects overlap an installed resident allocation')
    art,data,_=checked(source,art_directory)
    data,resources,relocations=runtime_art(source,art,data)
    generated=generate(art);link,native=bindings(base,prior)
    if set(link)&set(resources):raise ValueError('Tree effect resources conflict with native services')
    link.update(resources);directory.mkdir(parents=True)
    sources=[]
    for name,text in generated.items():
        file=directory/name;write_new(file,text.encode());sources.append(str(file.relative_to(ROOT)))
    write_new(directory/'tree-art.bin',data)
    code,receipt=compile_part('tree_effects',directory/'compiled',extra_sources=sources,
        include_dirs=(ROOT/'overlays/v3',),link_symbols=link)
    result=dict(format='AFV3-TREE-EFFECT-RUNTIME-1',references=REFERENCES,
        prepared_art=str(art_directory.relative_to(ROOT)),art=relocations,code=receipt,
        native=native,source_functions=art['functions'],bindings=link,
        generated_sha256={name:sha256(text.encode()) for name,text in generated.items()},
        joint_vectors=6,matrices_per_buffer=6,active_tree_slots=3,new_effect_ids=[120,121],
        debug_offsets='donor normal-play zero values',installed=False,selectable=False,
        sources={name:sha256((ROOT/name).read_bytes()) for name in SOURCES})
    write_new(directory/'prepared.json',(json.dumps(result,indent=2)+'\n').encode())
    return code,data,result


def remove_relocations(data,removed):
    count=u32(data,16);rows=list(struct.unpack_from('>'+str(count)+'I',data,20))
    if len(set(removed))!=len(removed) or any(rows.count(r)!=1 for r in removed):
        raise ValueError('Missing or duplicate original tree-effect relocation')
    rows=[r for r in rows if r not in removed];out=bytearray(data)
    struct.pack_into('>I',out,16,len(rows))
    out[20:-4]=struct.pack('>'+str(len(rows))+'I',*rows)+bytes(len(data)-24-4*len(rows))
    return bytes(out)


def actor_and_player(source,base,equipment,code,compiled):
    from v3_player_actions import native_references
    from v3_import_storage import jump
    from v3_npc_clothing import guard_incoming
    files=by_vrom(base);symbols=compiled['symbols'];ram=0x80A1CBD0
    actor=bytearray(files[0x8E46A0].extract(base));reloc=files[0x8E6640].extract(base)
    _,absolute,_,locations,_=native_references(actor,reloc,expected_sections=struct.unpack_from('>4I',reloc))
    profile=0x1F28
    size=u32(code,symbols['af_tree_actor_bytes']-RAM)
    if u32(actor,profile+12)!=0xCF0 or not 0xCF0+72<=size<=0xE00:raise ValueError('Invalid resized tree actor workspace')
    struct.pack_into('>I',actor,profile+12,size);removed=[];pointers=[]
    for i,(role,offset) in enumerate((('ct',0x13C),('dt',0x1E8),('mv',0x1008),('dw',0x1A34))):
        at=profile+16+4*i
        if absolute.get(at)!=ram+offset or u32(actor,at)!=ram+offset or at not in locations:
            raise ValueError('Changed native actor callback set')
        target=symbols['af_tree_actor_'+role];struct.pack_into('>I',actor,at,target)
        removed.append(locations[at]);pointers.append(dict(offset=at,before=ram+offset,after=target))
    fixed=remove_relocations(reloc,removed)
    native_references(actor,fixed,expected_sections=struct.unpack_from('>4I',fixed))
    actors=dict(vrom=0x8E46A0,reloc=0x8E6640,ram=ram,actor_bytes=size,additional_actor_bytes=size-0xCF0,
        previous_sha256=sha256(files[0x8E46A0].extract(base)),previous_reloc_sha256=sha256(reloc),
        sha256=sha256(actor),reloc_sha256=sha256(fixed),callbacks=pointers,removed_relocations=removed,
        native_heap_art_bytes_removed=[12448,12448,14016])
    source_raw,source_fn=source.function(0x16B2D0)
    if sha256(source_raw)!='0aab899a1af261256153d2374eccaa4ed81816c2ad039693984fe28f7b881b99':
        raise ValueError('Changed complete donor tree-effect player dispatcher')
    vrom,reloc_vrom,ram=0x7AC420,0x7D9BA0,0x808B2D50
    player=bytearray(files[vrom].extract(base));rel=files[reloc_vrom].extract(base)
    prior=equipment['player_actions']
    if sha256(player)!=prior['owner_sha256'] or sha256(rel)!=prior['relocation_sha256']:
        raise ValueError('Changed current complete player owner')
    entry,end=0x808B96F8,0x808B996C
    if sha256(player[entry-ram:end-ram])!='86367e103fc29fda00bd70fda5dd81f42055994da3a7709f189ff85af0d8dedb':
        raise ValueError('Changed complete native player effect dispatcher')
    groups,absolute,_,locations,_=native_references(player,rel,expected_sections=struct.unpack_from('>4I',rel))
    sites=[p for p in range(0,u32(rel,0),4) if u32(player,p) in (jump(entry),jump(entry,link=True))]
    if ([ram+p for p in sites]!=[0x808BA290,0x808BA344,0x808CA610,0x808D188C] or
            entry in absolute.values() or any(t==entry for rows in groups.values() for _,t in rows)):
        raise ValueError('Changed complete native tree-effect call set')
    guard_incoming(player,u32(rel,0),ram,[(p,4) for p in sites])
    patches=[];removed=[]
    for at in sites:
        before=u32(player,at);after=jump(symbols['af_tree_player_effect'],link=True)
        if before!=jump(entry,link=True) or at not in locations:raise ValueError('Changed player effect call relocation')
        removed.append(locations[at]);patches.append(dict(offset=at,before=before,after=after))
        struct.pack_into('>I',player,at,after)
    player_rel=remove_relocations(rel,removed)
    native_references(player,player_rel,expected_sections=struct.unpack_from('>4I',player_rel))
    player_info=dict(vrom=vrom,reloc=reloc_vrom,ram=ram,source=source_fn,
        previous_sha256=prior['owner_sha256'],previous_reloc_sha256=prior['relocation_sha256'],
        sha256=sha256(player),reloc_sha256=sha256(player_rel),patches=patches,removed_relocations=removed,
        original_dispatcher_preserved=True,native_dispatcher_offset=entry-ram)
    # Keep all shared owners' current identity receipts synchronized. No existing
    # instruction, animation, query hook, or saved player field is removed.
    prior.update(owner_sha256=sha256(player),relocation_sha256=sha256(player_rel))
    equipment['player_motion'].update(owner_sha256=sha256(player),reloc_sha256=sha256(player_rel))
    equipment['scenery']['player_queries'].update(sha256=sha256(player),reloc_sha256=sha256(player_rel))
    changes={0x8E46A0:bytes(actor),0x8E6640:fixed,vrom:bytes(player),reloc_vrom:player_rel}
    return changes,actors,player_info


def install(base,prior,blob,core,output,art_directory):
    from v3_asset_loader import BLOB
    from v3_furniture_install import relocate_resource_plan
    from v3_resource_capacity import checked_limit
    from v3_room_effects import restore_controller,extend_controller,RAM as OWNER_RAM
    from v3_holiday_sky import profile_packet
    import v3_physical_resources as physical
    equipment=copy.deepcopy(prior['equipment_resources']);scene=equipment['scenery']
    if scene.get('tree_effects'):raise ValueError('Tree effects are already installed')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    directory=output/'tree-effects'
    code,data,report=prepare(source,directory,art_directory.resolve(),base,prior)
    if len(code)>PAGE_TABLE-RAM:raise ValueError('Tree code overlaps complete page directory')
    packet=bytearray(ART_RAM-RAM);packet[:len(code)]=code;packet[-16:]=b'AFTE'*4
    physical.verify(base,prior['physical_resources']);records=copy.deepcopy(prior['physical_resources'])
    allocated=physical.allocate(base,records,packet,'tree-effects-GAFE01-r0',best_fit=True);records.append(allocated)
    changes,actor,player=actor_and_player(source,base,equipment,code,report['code'])
    report.update(actor=actor,player=player)
    files=by_vrom(base);effects=equipment['room_rigs']['effects'];old=effects['controller']
    if old['count']!=120 or [r['id'] for r in effects['profiles']]!=list(range(111,120)):
        raise ValueError('Changed complete native/additive effect identities')
    native,rel=restore_controller(files[old['vrom']].extract(base),files[old['reloc']].extract(base),old)
    start=(len(blob)+15)&~15;count=11
    if BLOB+start+64*count>checked_limit(base,prior):raise ValueError('Tree effect profiles exceed cartridge storage')
    blob.extend(bytes(start+64*count-len(blob)));rows=[];additions=[]
    for i in range(count):
        at=start+64*i
        if i<9:
            row=copy.deepcopy(effects['profiles'][i]);where=row['blob_offset'];payload=bytes(blob[where:where+64])
            if sha256(payload)!=row['sha256']:raise ValueError('Changed retained complete effect profile')
            addition=copy.deepcopy(old['additions'][i])
        else:
            kind=('leaf','young')[i-9]
            callbacks=[report['code']['symbols']['af_tree_'+kind+'_'+phase] for phase in ('init','ct','mv','dw')]
            source_name='iam_ef_'+('bush_happa' if kind=='leaf' else 'young_tree')
            source_profile=source.raw(source_name);source_at,source_size=source.symbol(source_name)
            refs={p-source_at:r for (sec,p),r in source.section_relocations.items()
                if sec==5 and source_at<=p<source_at+source_size}
            prefix='eBushHappa' if kind=='leaf' else 'eYoung_Tree'
            wanted={i*4:(1,1,1,next(r['offset'] for r in report['source_functions'] if r['symbol']==prefix+'_'+phase))
                for i,phase in enumerate(('init','ct','mv','dw'))}
            source_id=51 if kind=='leaf' else 77
            unique=source.raw('eEC_effect_feature')[source_id]
            if (len(source_profile)!=24 or source_profile!=bytes(16)+bytes.fromhex('fffe00ff44480000') or
                    refs!=wanted or unique not in (0,1)):
                raise ValueError('Changed complete tree-particle profile policy')
            payload=profile_packet(callbacks,source_profile[16:].hex(),code_bounds=(RAM,RAM+len(code)))
            row=dict(id=111+i,kind='tree-'+kind,callbacks=callbacks,callback_owner='tree-effects',
                policy_hex=source_profile[16:].hex(),source_symbol=source_name,source_id=source_id,
                source_sha256=sha256(source_profile),source_callbacks=wanted)
            # Complete graphics live in the startup packet, not a truncated
            # 3584-byte effect scratch bank. Native effect slots are unchanged.
            addition=dict(id=111+i,graphics=[0,0],unique=unique)
        row.update(blob_offset=at,vrom=BLOB+at,bytes=64,sha256=sha256(payload));rows.append(row)
        blob[at:at+64]=payload;logical=0x80700000+i*0x100
        addition['overlay']=[BLOB+at,BLOB+at+32,logical,logical+32,logical];additions.append(addition)
    defines=[f[2:] for f in old['loader']['flags'] if f.startswith('-D') and
             not f.startswith(('-DAF_EFFECT_PROFILES=','-DAF_EFFECT_COUNT='))]
    defines.extend((f'AF_EFFECT_PROFILES=0x{BLOB+start:X}u',f'AF_EFFECT_COUNT={count}u',
        'AF_EFFECT_PARTICIPANT_COUNT=1u',f'AF_EFFECT_TREE_START=0x{RAM:X}u',f'AF_EFFECT_TREE_END=0x{RAM+len(code):X}u'))
    loader=compile_part('effect_loader',directory/'effect-loader',defines=tuple(defines))
    owner,newrel,controller=extend_controller(native,rel,additions,loader=loader,graphics_vrom=effects['bank']['vrom'])
    offset=0x801010B0-CODE_RAM;before=bytes.fromhex(old['descriptor']['after'])
    if core[offset:offset+32]!=before:raise ValueError('Changed live effect-controller descriptor')
    after=struct.pack('>8I',old['vrom'],old['vrom']+len(owner),OWNER_RAM,OWNER_RAM+len(owner),0,OWNER_RAM+0x36A0,0,0)
    core[offset:offset+32]=after
    controller.update(installed=True,vrom=old['vrom'],reloc=old['reloc'],ram=OWNER_RAM,
        descriptor=dict(address=0x801010B0,before=before.hex(),after=after.hex()))
    changes.update({old['vrom']:owner,old['reloc']:newrel});growth=[]
    for vrom,payload in changes.items():
        if len(payload)==files[vrom].size and not files[vrom].pend:continue
        _,row=relocate_resource_plan(base,files,vrom,payload,minimum_physical=0x100000,
            reservations=records+growth,append_only=False,allow_compressed=True,
            excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),))
        if row['physical']<files[BLOB].pstart+len(blob) and files[BLOB].pstart<row['physical']+row['bytes']:
            raise ValueError('Tree effect owner overlaps the expanded import blob')
        growth.append(row)
    # Reserve the complete contiguous owners first, then use fragmented free
    # cartridge space for full shared 4-KiB art pages. No resource is truncated.
    art_packet=bytearray(END-ART_RAM);art_packet[:len(data)]=data;art_packet[-16:]=b'AFTE'*4
    staged=bytearray(base);staged[allocated['physical']:allocated['physical']+len(packet)]=packet
    writes=[];pages={};addresses=[]
    reservations=records+[{k:r[k] for k in ('physical','bytes','sha256')}|
        {'id':f"tree-effects-owner-{r['vrom']:X}"} for r in growth]
    for r in growth:staged[r['physical']:r['physical']+r['bytes']]=changes[r['vrom']]
    for at in range(0,len(art_packet),4096):
        page=bytes(art_packet[at:at+4096])
        if page not in pages:
            row=physical.allocate(staged,reservations,page,f'tree-effects-page-{len(pages):02d}',best_fit=True,
                excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),))
            pages[page]=row['physical'];writes.append((row,page));records.append(row);reservations.append(row)
            staged[row['physical']:row['physical']+row['bytes']]=page
        addresses.append(pages[page])
    directory_words=[0x41465047,len(art_packet),4096,len(addresses),*addresses]
    if len(directory_words)!=40:raise ValueError('Changed complete tree-effect page count')
    struct.pack_into('>41I',packet,PAGE_TABLE-RAM,*directory_words,zlib.crc32(art_packet))
    allocated['sha256']=sha256(packet)
    if physical.overlaps([allocated,*[r for r,_ in writes]],files[BLOB].pstart,files[BLOB].pstart+len(blob)):
        raise ValueError('Tree effect packet overlaps the expanded import blob')
    report.update(packet=dict(allocated,ram=RAM,storage='physical-ROM',crc32=zlib.crc32(packet)),
        art_packet=dict(ram=ART_RAM,bytes=len(art_packet),sha256=sha256(art_packet),crc32=zlib.crc32(art_packet),
            directory_ram=PAGE_TABLE,page_addresses=addresses,physical_resources=[r for r,_ in writes],
            loaded_before_actor_construction=True),
        installed=True,native_execution_verified=False,ordinary_gameplay_verified=False,
        saved_format_changed=False,additional_resident_bytes=END-RAM,guard_ram=END-16)
    report.update(profiles=rows[9:],previous_profiles=copy.deepcopy(effects['profiles']),
        effect_controller_previous_sha256=old['sha256'],effect_controller_sha256=sha256(owner),
        additional_scene_bytes=actor['additional_actor_bytes']+len(owner)-old['bytes'],resource_growth=growth)
    effects.update(profiles=rows,controller=controller,additional_scene_bytes=controller['additional_scene_bytes'])
    effects['sources'].update(report['sources']);effects['tree_effects']=dict(profiles=[120,121],code=report['code'])
    scene.update(tree_effects=report,additional_fixed_resident_bytes=scene['additional_fixed_resident_bytes']+END-RAM,
        additional_scene_resident_bytes=scene['additional_scene_resident_bytes']+report['additional_scene_bytes'])
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return equipment,changes,dict(physical_resources=records,resource_growth=growth),[(allocated,bytes(packet)),*writes]


if __name__=='__main__':
    import argparse
    from v3_furniture_install import inputs
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',required=True,type=Path)
    parser.add_argument('--art',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();base,prior=inputs(args.base_lock)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    _,_,report=prepare(source,args.output,args.art.resolve(),base,prior)
    print(json.dumps(dict(code_bytes=report['code']['bytes'],art_bytes=report['art']['bytes'],installed=False)))
