"""Import the complete moon/meteor family through shared effect/model machinery."""
import argparse
import copy
import json
import re
import struct
import zlib
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_furniture_pipeline import Source,prepare_models,compile_models
from v3_password_policy import function

RAM,END=0x80738000,0x8073C000
PACKET_END=END+16
REFERENCES={
    'ef_night13_moon.c':'da00b980d14e9f34410cd207d0729579e9b990b18ca8cea24f7350bfa59db048',
    'ef_shooting_set.c':'b16b72751e8cd2ab2a7658f30cb3053661c040cafb633a8fc49f6162d53a3ae5',
    'ef_shooting.c':'af7bcfa4b6885a2acd76de7ed44b16874287212b62eae1db8f0dfc27a82f6100',
    'ef_shooting_kira.c':'702efa4f881c7854aab085b01b939410110650c621dc860ed4f09c4cceef2ab8'}
FAMILY=(('moon','night13_moon','eNight13Moon'),('set','shooting_set','eShootingSet'),
        ('shooting','shooting','eShooting'),('kira','shooting_kira','eShootingKira'))
SOURCES=('tools/v3_holiday_sky.py','overlays/v3/holiday_sky.h','overlays/v3/holiday_sky.c',
    'overlays/v3/holiday_sky_draw.c','overlays/v3/holiday_sky.ld','tools/v3_furniture_art.py',
    'tools/v3_room_effects.py','tools/v3_room_particles.py','tools/v3_asset_loader.py',
    'overlays/v3/effect_loader.c','tools/v3_room_goods.py','tools/v3_furniture_install.py')


def profile_packet(callbacks,policy_hex,*,code_bounds=(RAM,END)):
    low,high=code_bounds
    if (not 0x80400000<=low<high<=0x80800000 or
            len(callbacks)!=4 or any(type(p)!=int or p&3 or not low<=p<high for p in callbacks) or
            policy_hex not in ('005000ffc47a0cff','ffff00ffc47a0cff','fffe00ffc47a0cff','ffff00ff44480000','fffe00ff44480000')):
        raise ValueError('Invalid complete resident sky-effect profile')
    data=struct.pack('>4I',*callbacks)+bytes.fromhex(policy_hex)
    return data+struct.pack('>2I',zlib.crc32(data),0x41464550)+struct.pack('>5I',0,32,0,0,0)+bytes(8)+struct.pack('>I',32)


def generate(source):
    """Reuse every complete source init/ctor/move helper, with explicit native APIs."""
    header=(ROOT/'local/ac-decomp/include/ef_effect_control.h').read_bytes()
    if sha256(header)!='8308dd443efa5518826f11b8b529b9acb1aa0119744e53c23b782ea22daa4126':
        raise ValueError('Changed complete source effect identities')
    enum=re.search(r'enum effect_type\s*\{([^}]+)\}',header.decode())[1]
    enum=re.sub(r'/\*.*?\*/|//[^\n]*','',enum,flags=re.S)
    names=[n.strip() for n in enum.split(',') if n.strip()]
    if any(not re.fullmatch(r'eEC_EFFECT_\w+',n) for n in names):
        raise ValueError('Changed implicit source effect identities')
    unique=source.raw('eEC_effect_feature')
    if len(unique)!=names.index('eEC_EFFECT_NUM') or any(v not in (0,1) for v in unique):
        raise ValueError('Incomplete source duplicate policies')
    pieces=['#include "holiday_sky.h"','#pragma GCC diagnostic push',
        '#pragma GCC diagnostic ignored "-Wunused-parameter"'];functions=[];profiles=[]
    for index,(kind,stem,prefix) in enumerate(FAMILY):
        path='ef_'+stem+'.c';raw=(ROOT/'local/ac-decomp/src/effect'/path).read_bytes()
        if sha256(raw)!=REFERENCES[path]:raise ValueError('Changed complete source effect: '+path)
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',raw.decode(),flags=re.S)
        declared=re.findall(r'^static\s+[^\n;{}=]+?\b(e\w+)\([^;{}]*\)\s*\{',text,re.M)
        bodies=[]
        for name in declared:
            matches=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
            if len(matches)!=1:raise ValueError('Missing whole source effect function: '+name)
            functions.append(source.function(matches[0])[1])
            if name.endswith('_dw') or name=='eShooting_GetTwoTileGfx':continue
            bodies.append(function(text,name))
        if not all(prefix+'_'+role in declared for role in ('init','ct','mv','dw')):
            raise ValueError('Incomplete complete effect callback set')
        code='\n\n'.join(bodies)
        replacements={
            'eEC_CLIP->make_effect_proc':'af_sky_create','eEC_CLIP->effect_make_proc':'af_sky_request',
            'eEC_CLIP->set_continious_env_proc':'af_sky_continuous',
            'eEC_CLIP->check_lookat_block_proc':'af_sky_lookat','eEC_CLIP->calc_adjust_proc':'af_sky_adjust',
            'Common_Get(time.rtc_time)':'af_sky_clock()','Common_Get(time).now_sec':'af_sky_seconds()',
            'GET_PLAYER_ACTOR_GAME(game)':'af_sky_player(game)','mEv_CheckTitleDemo()':'af_sky_title_demo()',
            'NPC_CLIP->set_attention_request_proc':'af_sky_attention',
            'static xyz_t scale0':'static const xyz_t scale0'}
        for before,after in replacements.items():code=code.replace(before,after)
        code=re.sub(r'GETREG\(MYKREG,\s*(\d+)\)',r'af_sky_debug(\1)',code)
        code=code.replace('rnd_angle = RANDOM_F(65535.0f);','rnd_angle = (s16)(int)RANDOM_F(65535.0f);')
        if any(token in code for token in ('Common_Get','CLIP','GETREG','GET_PLAYER')):
            raise ValueError('Unbound complete effect source service')
        pieces.append(code)
        target='af_sky_'+kind
        pieces.extend((f'void {target}_init(xyz_t p,int priority,s16 angle,void *g,u16 item,s16 a,s16 b) {{',
            f' if(af_sky_ready(g)){prefix}_init(p,priority,angle,g,item,a,b);}}',
            f'void {target}_ct(RoomEffect *e,void *g,void *arg) {{',
            f' if(af_sky_ready(g)){prefix}_ct(e,g,arg);else e->timer=0;}}',
            f'void {target}_mv(RoomEffect *e,void *g) {{',
            f' if(!af_sky_ready(g)){{e->timer=0;return;}} {prefix}_mv(e,g);',
            f' if(e->timer>1){{--e->timer;{prefix}_mv(e,g);}} }}',
            f'void {target}_dw(RoomEffect *e,void *g) {{'+
                ('(void)e;(void)g;}' if kind=='set' else f'af_sky_{kind}_draw(e,g);}}')))
        symbol='iam_ef_'+stem;at,size=source.symbol(symbol);profile=source.raw(symbol)
        refs={p-at:r for (sec,p),r in source.section_relocations.items() if sec==5 and at<=p<at+size}
        wanted={i*4:(1,1,1,next(r['offset'] for r in functions if r['symbol']==prefix+'_'+role))
            for i,role in enumerate(('init','ct','mv','dw'))}
        tail=('005000ffc47a0cff','ffff00ffc47a0cff','fffe00ffc47a0cff','ffff00ff44480000')[index]
        if profile!=bytes(16)+bytes.fromhex(tail) or refs!=wanted:
            raise ValueError('Changed complete effect profile or death policy')
        donor=names.index('eEC_EFFECT_'+stem.upper())
        profiles.append(dict(kind=kind,source_id=donor,native_id=115+index,source_symbol=symbol,
            offset=at,sha256=sha256(profile),policy_hex=tail,unique=unique[donor],callbacks=wanted))
    pieces.extend(('#pragma GCC diagnostic pop',
        'int af_sky_identity(unsigned int source) {',
        ' static const unsigned short ids[4][2]={'+','.join('{'+str(p['source_id'])+','+str(p['native_id'])+'}' for p in profiles)+'};',
        ' for(unsigned int i=0;i<4;i++){if(ids[i][0]==source)return ids[i][1];}',
        ' return -1;}',''))
    return '\n'.join(pieces),dict(references=REFERENCES,functions=functions,profiles=profiles,
        source_ticks_per_native_update=2,source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()))


def artwork(source,bank,directory):
    from v3_furniture_scroll import evw_scroll
    from v3_room_particles import append_object
    from v3_room_effects import flash_art
    evw,helpers=evw_scroll(source,source.symbol('ef_moon01_01_evw_anime')[0],source.function(0x339C)[1])
    if len(evw['rows'])!=1 or evw['rows'][0]['segment_address']!=0x08000000:
        raise ValueError('Changed full moon material animation')
    objects={}
    for kind,name,scroll in (
        ('moon','ef_moon01_01_modelT',dict(segment=0x08000000,
            dimensions=[[t['width'],t['height']] for t in evw['rows'][0]['tiles']])),
        ('shooting','ef_nagare01_modelT',dict(segment=0x09000000,dimensions=[[8,256],[8,32]]))):
        target=directory/kind;target.mkdir()
        prepared=prepare_models(source,dict(models={'model':source.containing(source.symbol(name)[0],exact=True)},
            callback_adapter=dict(category='actor-model-assets',model_scrolls={'model':scroll})))
        asset,offsets,models,_=compile_models(target,prepared)
        bank,row=append_object(bank,asset,models)
        write_new(target/'object.bin',asset)
        objects[kind]=dict(row,resources=prepared[2],model_records=models,offsets=offsets)
    # Reuse the checked legacy-native sprite converter. Its source texture is
    # already linear, unlike the two GX model families above.
    asset,receipt=flash_art(source);mode=source.raw('ef_takurami01_normal_render_mode')
    if mode.hex()!='e200001cc8104b50df00000000000000':
        raise ValueError('Changed complete source star render state')
    models=[dict(layer='model',native_offset=320,bytes=144,output_sha256=sha256(asset[320:])),
        dict(layer='mode',native_offset=len(asset),bytes=len(mode),output_sha256=sha256(mode))]
    bank,row=append_object(bank,asset+mode,models);objects['kira']=dict(row,source=receipt,model_records=models)
    write_new(directory/'kira-object.bin',asset+mode)
    write_new(directory/'effect-art-bank.bin',bank)
    t=evw['rows'][0]['tiles']
    values=[objects[k]['models']['model'] for k in ('moon','shooting','kira')]+[objects['kira']['models']['mode']]
    code='#include "holiday_sky.h"\nconst AFSkyArt af_sky_art={'+','.join(hex(v) for v in values)+','
    code+=','.join('{'+','.join(str(row[key] if key in ('width','height') else row['rate'][0 if key=='x' else 1])
        for row in t)+'}' for key in ('width','height','x','y'))+'};\n'
    return bank,code,dict(objects=objects,moon_scroll=evw,scroll_functions=helpers)


def native_bindings(base):
    text='\n'.join((ROOT/f'upstream/af/linker_scripts/jp/symbol_addrs_{part}.txt').read_text()
        for part in ('code','boot','libultra'))
    symbols={n:int(a,16) for n,a in re.findall(r'^(\w+) = 0x([0-9A-Fa-f]+);',text,re.M)}
    functions=sorted({int(a,16) for a in re.findall(r'^\w+ = 0x([0-9A-Fa-f]+);[^\n]*type:func',text,re.M)})
    mapping={n:n for n in ('sin_s','cos_s','mFI_BlockKind2BkNum','mFI_BkNum2WposXZ',
        'Matrix_translate','Matrix_scale','Matrix_RotateY','Matrix_RotateZ','Matrix_mult',
        '_Matrix_to_Mtx','osWritebackDCache','_texture_z_light_fog_prim_xlu','Lib_SegmentedToVirtual')}
    mapping.update(af_effect_random='fqrand',af_sky_player='get_player_actor_withoutCheck',
        mFI_BkNum2BaseHeight='func_80089114_jp',af_sky_title_demo='mEv_CheckTitleDemo',memcpy='memcpy')
    core=by_vrom(base)[CODE_VROM].extract(base);link={};receipts=[]
    for name,target in mapping.items():
        lo=symbols[target];hi=next(a for a in functions if a>lo)
        # Low-level RNG/cache/copy routines belong to boot code, not CODE_VROM.
        vrom,ram=(0x1060,0x80025C60) if lo<CODE_RAM else (CODE_VROM,CODE_RAM)
        data=by_vrom(base)[vrom].extract(base)[lo-ram:hi-ram]
        if len(data)!=hi-lo or not data:raise ValueError('Incomplete native sky binding: '+target)
        link[name]=lo;receipts.append(dict(symbol=target,vrom=vrom,ram=ram,address=lo,bytes=len(data),sha256=sha256(data)))
    if link['mFI_BkNum2BaseHeight']!=0x80089114 or link['af_sky_title_demo']!=0x8007D90C:
        raise ValueError('Changed native height/title identities')
    link.update(af_sky_native_clip=0x80136F3C,af_sky_native_rtc=0x80136FBC,
        af_sky_native_debug=0x80138E50,af_sky_native_npc_clip=0x80136EEC)
    return link,receipts


def prepare(output,base,prior):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored preparation')
    output.mkdir(parents=True)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,contract=generate(source)
    effects=prior['equipment_resources']['room_rigs']['effects'];p=effects['bank']
    bank=by_vrom(base)[p['vrom']].extract(base)
    if sha256(bank)!=p['sha256']:raise ValueError('Changed installed complete effect artwork')
    bank,art,resources=artwork(source,bank,output)
    for name,code in (('source.c',generated),('art.c',art)):
        write_new(output/name,code.replace('"holiday_sky.h"','"/source/overlays/v3/holiday_sky.h"').encode())
    bindings,native=native_bindings(base)
    code,compiled=compile_part('holiday_sky',output/'code',extra_sources=(
        'overlays/v3/holiday_sky_draw.c',str((output/'source.c').relative_to(ROOT)),
        str((output/'art.c').relative_to(ROOT))),link_symbols=bindings)
    result=dict(format='AFV3-HOLIDAY-SKY-1',source=contract,artwork=resources,code=compiled,
        native=native,bindings=bindings,bank=dict(previous_sha256=p['sha256'],sha256=sha256(bank),bytes=len(bank)),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},installed=False,native_execution_verified=False)
    write_new(output/'prepared.json',(json.dumps(result,indent=2)+'\n').encode())
    return code,bank,result


def install(base,prior,blob,core,output):
    from v3_console_disk_install import reservations
    from v3_holiday_state import RAM as STATE_RAM
    from v3_furniture_install import relocate_resource_plan
    from v3_resource_capacity import checked_limit
    from v3_room_effects import restore_controller,extend_controller,RAM as OWNER_RAM
    from v3_room_rig_runtime import packet_layout
    from v3_holiday_active import owner_requirements,ADDRESS,COMMON
    from v3_holiday_maps import owner_source,discover
    import v3_physical_resources as physical
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra'];events=npc['events']
    if not events.get('dispatch') or events.get('sky'):
        raise ValueError('Sky effects require live dedicated owners and a fresh installation')
    if PACKET_END>0x807DA800 or any(a<PACKET_END and RAM<b for a,b in reservations(prior)):
        raise ValueError('Sky effect code overlaps retained resident memory')
    physical.verify(base,prior['physical_resources'])
    directory=output/'holiday-sky';code,bank,report=prepare(directory,base,prior)
    files=by_vrom(base);room=equipment['room_rigs'];effects=room['effects'];old=effects['controller']
    if [p['id'] for p in effects['profiles']]!=[111,112,113,114] or old['count']!=115:
        raise ValueError('Changed complete additive effect directory')
    native_owner,reloc=restore_controller(files[old['vrom']].extract(base),files[old['reloc']].extract(base),old)
    # Preserve the existing holiday packet. A separate small startup packet
    # fits verified free ROM space without duplicating the whole holiday bank.
    packet=equipment['holiday_state']['packet'];start=packet['physical'];n=packet['bytes']
    raw=base[start:start+n]
    if packet['ram']!=STATE_RAM or STATE_RAM+n!=RAM or sha256(raw)!=packet['sha256']:
        raise ValueError('Changed complete shared holiday packet')
    data=code+bytes(END-RAM-len(code))+b'AFSK'*4
    records=copy.deepcopy(prior['physical_resources'])
    fresh=physical.allocate(base,records,data,'holiday-sky-GAFE01-r0');records.append(fresh)
    installed=dict(fresh,ram=RAM,crc32=zlib.crc32(data),storage='physical-ROM')
    writes=[(fresh,data)]
    report.update(installed=True,packet=installed,preserved_holiday_packet=copy.deepcopy(packet),
        loaded_code=dict(ram=RAM,bytes=len(code),sha256=sha256(code)),
        guard_ram=END,additional_resident_bytes=PACKET_END-RAM,events_active=False,saved_format_changed=False)
    # Repack all imported profiles contiguously for the checked native loader.
    # The four room callback words/policies stay exactly as installed.
    profile_start=(len(blob)+15)&~15
    if BLOB+profile_start+512>checked_limit(base,prior):raise ValueError('Effect profiles exceed import storage')
    blob.extend(bytes(profile_start+512-len(blob)));previous_profiles=copy.deepcopy(effects['profiles'])
    rows=[];additions=[]
    for i in range(8):
        at=profile_start+64*i
        if i<4:
            row=copy.deepcopy(previous_profiles[i]);p=row['blob_offset']
            payload=bytes(blob[p:p+64])
            if sha256(payload)!=row['sha256']:raise ValueError('Changed retained room effect profile')
            graphics=old['additions'][i]['graphics'];unique=old['additions'][i]['unique']
        else:
            source=report['source']['profiles'][i-4];kind=source['kind']
            callbacks=[report['code']['symbols']['af_sky_'+kind+'_'+role] for role in ('init','ct','mv','dw')]
            payload=profile_packet(callbacks,source['policy_hex'])
            row=dict(id=source['native_id'],kind=kind,callbacks=callbacks,callback_owner='holiday-sky',policy_hex=source['policy_hex'])
            graphics=[0,0] if kind=='set' else report['artwork']['objects'][kind]['graphics'];unique=source['unique']
        row.update(blob_offset=at,vrom=BLOB+at,bytes=64,sha256=sha256(payload));rows.append(row)
        blob[at:at+64]=payload
        ram=0x80700000+i*0x100
        additions.append(dict(id=111+i,overlay=[BLOB+at,BLOB+at+32,ram,ram+32,ram],graphics=graphics,unique=unique))
    effects['profiles']=rows
    room_start,room_end,_=packet_layout(room)
    loader=compile_part('effect_loader',directory/'effect-loader',defines=(
        f'AF_EFFECT_PROFILES=0x{BLOB+profile_start:X}u','AF_EFFECT_COUNT=8u','AF_EFFECT_ROOM_COUNT=4u',
        f'AF_EFFECT_CODE_START=0x{room_start:X}u',f'AF_EFFECT_CODE_END=0x{room_end:X}u',
        f'AF_EFFECT_SKY_START=0x{RAM:X}u',f'AF_EFFECT_SKY_END=0x{RAM+len(code):X}u'))
    owner,fixed,controller=extend_controller(native_owner,reloc,additions,loader=loader,graphics_vrom=effects['bank']['vrom'])
    at=0x801010B0-CODE_RAM;before=bytes.fromhex(old['descriptor']['after'])
    if core[at:at+32]!=before or files[old['reloc']].index!=files[old['vrom']].index+1:
        raise ValueError('Changed complete scene effect owner descriptor')
    after=struct.pack('>8I',old['vrom'],old['vrom']+len(owner),OWNER_RAM,OWNER_RAM+len(owner),0,OWNER_RAM+0x36A0,0,0)
    core[at:at+32]=after
    controller.update(installed=True,vrom=old['vrom'],reloc=old['reloc'],ram=OWNER_RAM,
        descriptor=dict(address=0x801010B0,before=before.hex(),after=after.hex()))
    bank_vrom=effects['bank']['vrom'];changes={old['vrom']:owner,old['reloc']:fixed,bank_vrom:bank}
    growth=[]
    for vrom,payload in changes.items():
        _,row=relocate_resource_plan(base,files,vrom,payload,
            minimum_physical=files[BLOB].pstart+len(blob),reservations=records+growth,
            append_only=vrom==bank_vrom)
        growth.append(row)
    effects['bank'].update(bytes=len(bank),sha256=sha256(bank),
        additional_rom_bytes=effects['bank']['additional_rom_bytes']+len(bank)-files[bank_vrom].size)
    effects.update(controller=controller,additional_scene_bytes=controller['additional_scene_bytes'],resource_growth=growth,
        sky=dict(installed=True,profiles=[r['id'] for r in rows[4:]],code=report['code']))
    effects['sources'].update(report['sources'])
    report.update(previous_profiles=previous_profiles,profiles=rows[4:],resource_growth=growth,
        loader_room_bounds=[room_start,room_end],loader_sky_bounds=[RAM,RAM+len(code)],
        native_effect_prefix_preserved=True)
    # Publish real effect identities to the existing owner preflight. Keep
    # its public entries and all participant/controller admission gates intact.
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,owners=owner_source(source);deps,needs=owner_requirements(discover(source),owners,generated)
    if sha256(deps.encode())!=events['dispatch']['generated_requirements_sha256']:
        raise ValueError('Changed complete owner dependency graph')
    write_new(directory/'requirements.c',deps.replace('"holiday_dispatch.h"','"/source/overlays/v3/holiday_dispatch.h"').encode())
    active=events['active'];bindings=dict(active['bindings'],af_sky_identity=report['code']['symbols']['af_sky_identity'])
    active_code,compiled=compile_part('holiday_active',directory/'owner-dispatch',link_symbols=bindings,
        defines=('AF_HOLIDAY_SKY',),extra_sources=('overlays/v3/holiday_dispatch.c',
            'overlays/v3/holiday_dispatch_native.c',str((directory/'requirements.c').relative_to(ROOT))))
    for name in ('af_holiday_active_update','af_holiday_dedicated_current',
            *('af_holiday_dedicated_'+phase for phase in ('start','stop','in','out','behind'))):
        if compiled['symbols'][name]!=active['code']['symbols'][name]:
            raise ValueError('Moved retained active event dispatcher entry: '+name)
    p=npc['packet'];npc_data=bytearray(base[p['physical']:p['physical']+p['bytes']]);at=ADDRESS-p['ram'];limit=COMMON-p['ram']
    if (sha256(npc_data)!=p['sha256'] or sha256(npc_data[at:at+active['code']['bytes']])!=active['code']['sha256'] or
            any(npc_data[at+active['code']['bytes']:limit]) or len(active_code)>limit-at):
        raise ValueError('Changed shared owner code reservation')
    npc_data[at:limit]=active_code+bytes(limit-at-len(active_code));previous=p['sha256']
    p.update(sha256=sha256(npc_data),crc32=zlib.crc32(npc_data))
    row=next(r for r in records if r['id']==p['id']);row['sha256']=p['sha256']
    writes.append((dict(row,previous_sha256=previous),bytes(npc_data)))
    active.update(code=compiled,bindings=bindings);events['dispatch'].update(code=compiled,bindings=bindings,effects_bound=True)
    events['sky']=report;npc['sources'].update(report['sources'])
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return equipment,changes,dict(physical_resources=records,resource_growth=growth),writes


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    from v3_furniture_install import inputs
    base,prior=inputs(args.base_lock)
    _,_,report=prepare(args.output,base,prior)
    print(json.dumps(dict(code_bytes=report['code']['bytes'],effects=report['source']['profiles']),indent=2))
