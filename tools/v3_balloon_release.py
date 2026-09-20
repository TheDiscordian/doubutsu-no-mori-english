"""Shared release/look/fall consumers for all selected balloon shapes."""
import copy
import re
import struct
import zlib
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import ROOT,compile_part
from v3_equipment_runtime import RAM,PLAYER_RAM,PLAYER_VROM,PLAYER_RELOC
from v3_furniture_pipeline import Source
from v3_import_storage import jump
from v3_npc_draw import relocation_offsets
from v3_npc_clothing import guard_incoming

GROUPS=(('balloon_release',0xE100,0xE800),('balloon_look',0xBAA0,0xBF00),
        ('balloon_fall',0x9BE0,0x9FF0))
SOURCES=('tools/v3_balloon_release.py','overlays/v3/balloon_release.h',
         'overlays/v3/reward_exchange.c','overlays/v3/reward_exchange.ld',
         'overlays/v3/balloon_actor.h','overlays/v3/balloon_actor.ld','overlays/v3/held_rigs.ld')+tuple(
    'overlays/v3/'+name+suffix for name,_,_ in GROUPS for suffix in ('.c','.ld'))


def bindings(source,core,owner,original):
    sources=[]
    for start,end in ((0x18E96C,0x18F58C),(0x177F98,0x178340),(0x1706F0,0x170738),
                      (0x69C10,0x69C84),(0x28781C,0x287B88)):
        at=start
        while at<end:
            data,row=source.function(at);sources.append(row);at+=len(data)
        if at!=end:raise ValueError('Incomplete donor release/get-up function group')
    bounds=[]
    for name in ('symbol_addrs_code.txt','symbol_addrs_overlays.txt'):
        bounds.extend(int(a,16) for a in re.findall(r'= 0x([0-9A-Fa-f]+); // type:func',
            (ROOT/'upstream/af/linker_scripts/jp'/name).read_text()))
    native=[];files=by_vrom(original)
    for at in (0x8007D90C,0x80099A54,0x80099A94,0x8009A974,0x800B1C84,0x800B1F74,
               0x800DADC4,0x800E0008,0x808D71F8,0x808D72E0,0x808D7570,0x808D787C,
               0x808B846C,0x808B4924,0x808B3BD0,0x808C1064,0x808C32F4,0x808C33A0):
        data,ram,vrom=(owner,PLAYER_RAM,PLAYER_VROM) if at>=PLAYER_RAM else (core,CODE_RAM,CODE_VROM)
        end=min(x for x in bounds if x>at);raw=data[at-ram:end-ram]
        if raw!=files[vrom].extract(original)[at-ram:end-ram]:
            raise ValueError(f'Changed native release API {at:08X}')
        native.append(dict(entry=at,end=end,sha256=sha256(raw)))
    return dict(source_functions=sources,native_functions=native,source_steps_per_update=2,
        native_head_tracking_updates=30,native_minimum_release_updates=42,
        continuation_offset=0x13A4,fallen_shape_offset=0x13A8,equipped_offset=0x3EC,
        original_fish_insect_look_retained=True)


def install(base,prior,blob,core,original,output):
    old=prior['equipment_resources'];actions=old['player_actions'];files=by_vrom(base)
    start=old['blob_offset'];module=bytearray(blob[start:start+old['bytes']])
    owner=bytearray(files[PLAYER_VROM].extract(base));rel=files[PLAYER_RELOC].extract(base)
    if (not actions.get('balloon_actor') or actions.get('balloon_release') or old['bytes']!=0x12000
            or sha256(module)!=old['sha256'] or sha256(owner)!=actions['owner_sha256']
            or sha256(rel)!=actions['relocation_sha256']):
        raise ValueError('Balloon release requires the checked complete flying actor')
    flying=actions['balloon_actor'];rig=old['held_rig_actions']
    if (flying['offset']+flying['code']['bytes']>0x9BE0 or flying['player_bytes']!=0x13B0 or
            flying['packet_offset']+flying['packet_bytes']!=0xBAA0 or
            rig['code_offset']+rig['code']['bytes']>0xE100):
        raise ValueError('Balloon consumers overlap retained code/state')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    evidence=bindings(source,core,owner,original);codes={};symbols={}
    dependencies={k:v for part in (flying['code'],actions['tool_motion']['code'],actions['code'],
        actions['reward_actions']['requests'],actions['reward_exchange']['codes']['reward_deferred']['code'])
        for k,v in part['symbols'].items()}
    for name,at,end in GROUPS:
        if any(module[at:end]):raise ValueError('Balloon consumer storage is occupied')
        data,compiled=compile_part(name,output/name)
        if len(data)>end-at:raise ValueError('Balloon consumer exceeds checked reservation')
        for key,value in compiled['symbols'].items():
            if key in dependencies and dependencies[key]!=value:raise ValueError('Changed shared dependency: '+key)
            if key in symbols and symbols[key]!=value:raise ValueError('Inconsistent balloon consumer symbol: '+key)
            symbols[key]=value
        module[at:at+len(data)]=data;codes[name]=dict(offset=at,end=end,code=compiled)
    previous_exchange=actions['reward_exchange']['codes']['reward_exchange']
    at,n,end=previous_exchange['offset'],previous_exchange['code']['bytes'],previous_exchange['end']
    if sha256(module[at:at+n])!=previous_exchange['code']['sha256'] or any(module[at+n:end]):
        raise ValueError('Changed complete prior exchange code or occupied suffix')
    code,compiled=compile_part('reward_exchange',output/'reward_exchange',defines=('AF_V3_BALLOON_RELEASE',))
    if at+len(code)>end:raise ValueError('Balloon exchange exceeds checked category reservation')
    for key,value in compiled['symbols'].items():
        if not key.startswith('af_v3_'):continue
        prior_value=symbols.get(key,previous_exchange['code']['symbols'].get(key))
        if prior_value is not None and prior_value!=value:raise ValueError('Changed exchange public dependency: '+key)
    module[at:end]=code+bytes(end-at-len(code))
    codes['reward_exchange']=dict(offset=at,end=end,code=compiled)
    prior_deferred=actions['reward_exchange']['codes']['reward_deferred']['code']['symbols']
    prior_recovery=actions['tool_motion']['code']['symbols']
    plans=((0x808D78D0,(jump(0x808D7570,link=True),),(jump(symbols['af_v3_balloon_look'],link=True),)),
           (0x808D7814,(jump(prior_deferred['af_v3_reward_release_transition']),0),
                        (jump(symbols['af_v3_balloon_release_transition']),0)),
           (0x808C320C,(jump(prior_recovery['af_v3_tool_getup']),0),(jump(symbols['af_v3_balloon_getup']),0)),
           (0x808C33A0,(0x27BDFFE8,0xAFBF0014),(jump(symbols['af_v3_balloon_getup_transition']),0)))
    guard_incoming(owner,u32(rel,0),PLAYER_RAM,[(a-PLAYER_RAM,4*len(b)) for a,b,_ in plans])
    slots=relocation_offsets(rel,len(owner));patches=[]
    removed=[0x44000000|(0x808D78D0-PLAYER_RAM)]
    for at,before,after in plans:
        off=at-PLAYER_RAM;n=4*len(before)
        if struct.unpack_from('>'+str(len(before))+'I',owner,off)!=before:
            raise ValueError('Changed native balloon consumer hook')
        expected={off} if at==0x808D78D0 else set()
        if slots&set(range(off,off+n,4))!=expected:raise ValueError('Unexpected balloon consumer relocation')
        data=struct.pack('>'+str(len(after))+'I',*after)
        patches.append(dict(vrom=PLAYER_VROM,ram=PLAYER_RAM,address=at,before=owner[off:off+n].hex(),after=data.hex()))
        owner[off:off+n]=data
    count=u32(rel,16);rows=list(struct.unpack_from('>'+str(count)+'I',rel,20))
    if any(rows.count(r)!=1 for r in removed):raise ValueError('Missing unique balloon Look relocation')
    kept=[r for r in rows if r not in removed];updated=bytearray(rel)
    struct.pack_into('>I',updated,16,len(kept))
    updated[20:20+count*4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(4*len(removed))
    report=copy.deepcopy(old);current=report['player_actions'];callbacks=[]
    mappings={0x808DD874:('af_v3_reward_release_submenu','af_v3_balloon_submenu'),
              0x808DDA18:('af_v3_reward_release_setup','af_v3_balloon_release_setup')}
    for row in current['tables']:
        if row['native_entry'] not in mappings:continue
        at,n=row['offset'],row['bytes'];before,name=mappings[row['native_entry']];slot=at+4*81
        if sha256(module[at:at+n])!=row['sha256'] or u32(module,slot)!=prior_deferred[before]:
            raise ValueError('Changed shared creature callback table')
        callbacks.append(dict(action=81,consumer=row['native_entry'],offset=slot,before=u32(module,slot),after=symbols[name]))
        struct.pack_into('>I',module,slot,symbols[name]);row['sha256']=sha256(module[at:at+n])
    if len(callbacks)!=2:raise ValueError('Incomplete balloon action registration')
    current.update(owner_sha256=sha256(owner),relocation_sha256=sha256(updated),
                   removed_relocations=current['removed_relocations']+len(removed))
    current['balloon_release']=dict(codes=codes,bindings=evidence,patches=patches,callbacks=callbacks,
        removed_relocations=removed,release_action_installed=True,tumble_loss_installed=True,
        ordinary_menu_release_installed=False,exchange_release_installed=True,
        saved_format_changed=False,additional_scene_bytes=0,ordinary_gameplay_tested=False)
    current['balloon_actor']['tumble_loss_installed']=True
    current['reward_exchange']['codes']['reward_exchange']=copy.deepcopy(codes['reward_exchange'])
    current['reward_exchange']['balloon_release_installed']=True
    report['player_motion'].update(owner_sha256=sha256(owner),reloc_sha256=sha256(updated))
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    blob[start:start+len(module)]=module
    return report,{PLAYER_VROM:bytes(owner),PLAYER_RELOC:bytes(updated)}
