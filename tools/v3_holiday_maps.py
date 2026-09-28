"""Convert the complete shared event-layout graph, without guessing native IDs."""
import argparse
import copy
import json
from pathlib import Path
import re
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source
from v3_password_policy import function

REFERENCES={
    'src/game/m_event_map_npc.c':'71ee9c61eab889a596915bdc1640485a47c4dfb06559999a0141758e8bb731a4',
    'src/game/m_event_map_npc_data.c_inc':'d801b90de75593b40629f9e6c9436417ae3abe074f256f8ef8875d43cab869a4',
    'src/actor/ac_event_manager.c':'bb6f890571e68532d6edd8b741acc4975051b192f69b06a3863223552e2efe55',
    'include/m_event.h':'7d479a212f933197a93b1abc80dc356940fd682beaf375503477728c4a2ef2f6',
    'include/m_actor.h':'faf1bfbbfa807f37cad98debad69360071e94c8e149af7f745c4ff5352171412',
    'include/ef_effect_control.h':'8308dd443efa5518826f11b8b529b9acb1aa0119744e53c23b782ea22daa4126',
    'include/m_random_field_h.h':'1927b61d4a190d84c1a219b3a3760690917c1666e9949abeb01cf3068c06d3e1'}
NATIVE_OWNER_GUARDS=(
    (0x8095D280,0x8095D324,'890639c35b8d0e596fe6887c31797b44a5f1b3c247b1776c3a95c86e75032001'),
    (0x8095DA20,0x8095DAD4,'4301d158dde809879c9c88884d63903109582e14cf709ce7f76c2ba06d9412c6'),
    (0x8095DFF0,0x8095E130,'48943d7424156b27d157a6f09de5642d7bc8f2caf3c413957b86c55bc3abc91d'),
    (0x8095E404,0x8095E49C,'de5c4c46ff79f77bae5af3d2cc4f4a591d83e3ac53b4684a7879feecba62f317'),
    (0x8095E49C,0x8095E4CC,'c73ba3fa5f6e6e6c966a8e1f85d1abac16b43b5237da85a046719873c9f87aa5'))
NATIVE_CORE_GUARDS=(
    (0x80087C40,0x80087C64,'d9cdaf5a6030e38e196616f12201c9064e1891854d89d449d909121110a0ab6f'),
    (0x8008930C,0x80089348,'9debc21ff1a4c34dc513d9fd0ce51e2101ca9224fd2a06cea0d1ade00310b59b'),
    (0x80089440,0x80089538,'12d336e1c03fc00a812cdca55cab5d13c5100a0fd96d656c05365ba232eaf4ab'),
    (0x80080F0C,0x8008114C,'f6c5fd68730c842a3c6bed1baff21884096f82fc9e89df5d3b4d5b747740febf'),
    (0x8008D3A4,0x8008D574,'0872ddd9e3b7580158ea1ec937dea0b7dbea7baf784559426c8b86abe33b9cd3'),
    (0x8007FE74,0x8007FEBC,'e47da75362926cd98a3fc9bb1edc50deb7be05810f4dc646bf46bcdc716b6c83'))


def native_contract(base):
    owner=by_vrom(base)[0x03800000].extract(base);core=by_vrom(base)[CODE_VROM].extract(base)
    for data,ram,guards in ((owner,0x8095B8B0,NATIVE_OWNER_GUARDS),(core,CODE_RAM,NATIVE_CORE_GUARDS)):
        for lo,hi,digest in guards:
            if sha256(data[lo-ram:hi-ram])!=digest:
                raise ValueError(f'Changed complete native event primitive {lo:08X}')
    # Independently check the signed-offset gamePT load in the real spawn path.
    words=struct.unpack_from('>2I',owner,0x8095E0D0-0x8095B8B0)
    if words!=(0x3C048011,0x8C84EF90):raise ValueError('Changed native game-context load')
    address=((words[0]&65535)<<16)+(words[1]&65535)-65536
    symbols=(ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt').read_text()
    if not re.search(r'^gamePT = 0x'+f'{address:08X}'+r';',symbols,re.M):
        raise ValueError('Native source and instructions disagree on gamePT')
    return dict(owner_functions=NATIVE_OWNER_GUARDS,core_functions=NATIVE_CORE_GUARDS,
        game_context=address,game_context_instructions=list(words),
        identity_provider_bound=False,title_transition_provider_bound=False,
        player_wade_lock_provider_bound=False)


def discover(source):
    for path,digest in REFERENCES.items():
        if sha256((ROOT/'local/ac-decomp'/path).read_bytes())!=digest:
            raise ValueError('Changed complete event-layout reference: '+path)
    raw=source.raw('l_event_map_type_table')
    if len(raw)!=68 or sha256(raw)!='3eca540e8c757c3a658f0b0669008b3f078c2af5b62ae9838c23da003f7adbf1':
        raise ValueError('Changed complete source event-map directory')
    types=struct.unpack('>17I',raw);table,size=source.symbol('l_event_set_table')
    if size!=68 or any(source.data[table:table+size]) or len(set(types))!=17:
        raise ValueError('Changed complete source layout pointers')
    checked={};result=[]
    def data(at,n):
        name,start,length=source.containing(at,exact=True)
        if length!=n:raise ValueError('Incomplete layout resource: '+name)
        value=source.data[start:start+length]
        checked[name]=dict(offset=start,bytes=length,sha256=sha256(value))
        return value
    def pointer(at,nullable=False):
        value=source.relocations.get(at)
        if any(source.data[at:at+4]):raise ValueError('Unreviewed nonzero source pointer')
        if value is None and nullable:return None
        if value is None or value[:3]!=(1,True,5):
            raise ValueError('Unresolved event-layout data pointer')
        return value[3]
    data(table,size)
    for index,event in enumerate(types):
        at=pointer(table+index*4,True)
        if at is None:
            result.append(dict(event=event,source_index=index,available=False));continue
        selection,normal,variants,count,_,_,kind=struct.unpack('>4B3I',data(at,16))
        if selection!=0 or not 0<variants<=7 or not 0<count<=16 or normal>count or kind not in (0,4,32768):
            raise ValueError('Unreviewed event-layout category')
        if kind!=32768 and variants!=1:raise ValueError('Only pool layouts select multiple variants')
        info=pointer(at+4);npc=pointer(at+8)
        data(info,variants*4);flags,cloth=struct.unpack('>HH',data(npc,4))
        if flags>>count:raise ValueError('NPC mask exceeds complete layout')
        layouts=[]
        for variant in range(variants):
            record=pointer(info+variant*4);data(record,8)
            names=data(pointer(record),count*2);positions=data(pointer(record+4),count*2)
            actors=[]
            for i in range(count):
                name=struct.unpack_from('>H',names,i*2)[0];x,z=positions[i*2:i*2+2]
                if x>=16 or z>=16:raise ValueError('Layout position exceeds native acre')
                actors.append(dict(source_name=name,x=x,z=z))
            layouts.append(actors)
        result.append(dict(event=event,source_index=index,available=True,selection=selection,
            normal_npcs=normal,variants=variants,count=count,kind=kind,npc_flags=flags,
            source_cloth=cloth,layouts=layouts))
    return dict(format='AFV3-HOLIDAY-MAPS-1',maps=result,resources=checked,references=REFERENCES,
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        native_names_resolved=False,actor_owners_installed=False)


def encode(report):
    rows=report['maps'];data=bytearray(16+len(rows)*20)
    struct.pack_into('>4sHHII',data,0,b'AFHM',1,len(rows),20,0)
    cache={}
    for i,row in enumerate(rows):
        at=16+i*20
        if not row['available']:
            struct.pack_into('>H',data,at,row['event']);continue
        raw=b''.join(struct.pack('>HBB',a['source_name'],a['x'],a['z'])
            for variant in row['layouts'] for a in variant)
        if raw not in cache:cache[raw]=len(data);data.extend(raw)
        struct.pack_into('>H4BHHHII',data,at,row['event'],row['selection'],row['normal_npcs'],
            row['variants'],row['count'],row['npc_flags'],row['source_cloth'],0,row['kind'],cache[raw])
    struct.pack_into('>I',data,12,len(data))
    return bytes(data)


def owner_source(source):
    from v3_holiday_events import discover as events
    owners=[o for o in events(source)['owners'] if o['kind']==4]
    # Source order places shared field-day helpers before their callers.
    names=['field_day_ct','field_day_delete']
    for owner in owners:
        for name in owner['callbacks']:
            if name and name not in names:names.append(name)
    text=(ROOT/'local/ac-decomp/src/actor/ac_event_manager.c').read_text()
    text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
    parts=[function(text,n) for n in names]
    # The only structural adaptation: pass the explicit common-state/primitive
    # context into the source's no-argument shared field-day cleanup helper.
    parts=[p.replace('field_day_delete(void)','field_day_delete(EVENT_MANAGER_ACTOR* evmgr)')
        .replace('field_day_delete();','field_day_delete(evmgr);') for p in parts]
    bodies='\n\n'.join(parts)
    prefixes=('mEv_EVENT_','mEv_STATUS_','mAc_PROFILE_','eEC_EFFECT_')
    needed=set(re.findall(r'\b(?:'+ '|'.join(prefixes)+r')\w+',bodies));enums=[];headers={}
    for path in ('include/m_event.h','include/m_actor.h','include/ef_effect_control.h'):
        raw=(ROOT/'local/ac-decomp'/path).read_bytes();headers[path]=sha256(raw)
        text=re.sub(r'/\*.*?\*/|//[^\n]*','',raw.decode(),flags=re.S)
        for match in re.finditer(r'\benum\b[^;{}]*\{[^{}]*\}\s*;',text,re.S):
            identifiers=set(re.findall(r'\b\w+\b',match[0]))
            if needed&identifiers:enums.append(match[0]);needed-=identifiers
        for match in re.finditer(r'^#define (\w+)\s+[^\n]*',text,re.M):
            if match[1] in needed:enums.append(match[0]);needed.remove(match[1])
    if needed:raise ValueError('Unresolved complete donor enum: '+str(sorted(needed)))
    field='include/m_random_field_h.h';raw=(ROOT/'local/ac-decomp'/field).read_bytes();headers[field]=sha256(raw)
    macros=[]
    for name in sorted(set(re.findall(r'\bmRF_BLOCKKIND_\w+',bodies))):
        matches=re.findall(r'^#define '+name+r'[^\n]*',raw.decode(),re.M)
        if len(matches)!=1:raise ValueError('Unresolved complete donor landmark')
        macros+=matches
    binary=[]
    for name in names:
        matches=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Unresolved complete owner callback: '+name)
        _,receipt=source.function(matches[0]);binary.append(receipt)
    generated=['#include "holiday_dedicated_source.h"',*enums,*macros,
        '#pragma GCC diagnostic push','#pragma GCC diagnostic ignored "-Wunused-parameter"',bodies,
        '#pragma GCC diagnostic pop',
        'int af_holiday_dedicated(AFHolidayDedicated *evmgr,unsigned int donor,unsigned int phase) {',
        ' if(!evmgr || !evmgr->call || !evmgr->common || phase>=5)return -1;',
        ' aEvMgr_event_ctrl_c control={(int)donor};',
        ' switch(donor) {']
    for owner in owners:
        generated+=[' case '+str(owner['type'])+':switch(phase) {']
        generated += [f' case {i}:return {name}(evmgr,&control);' for i,name in enumerate(owner['callbacks']) if name]
        generated+=[' default:return 0;}']
    generated+=[' default:return -1;}','}','']
    return '\n'.join(generated),dict(owners=owners,functions=binary,headers=headers,
        field_day_context_explicit=True,primitive_adapter_bound=False)


def prepare(output,build_lock=None,*,base=None,prior=None):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Use a fresh ignored preparation directory')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    report=discover(source);data=encode(report);generated,owners=owner_source(source)
    output.mkdir(parents=True)
    generated=generated.replace('"holiday_dedicated_source.h"',
        '"/source/overlays/v3/holiday_dedicated_source.h"')
    generated_path=output/'owners.c';write_new(generated_path,generated.encode())
    extra=(str(generated_path.relative_to(ROOT)),);bindings={}
    if build_lock or base is not None:
        from v3_furniture_install import inputs
        from v3_holiday_placement import BINDINGS,contract
        from v3_holiday_scene import prepare as prepare_scene
        from v3_registry import SPECIAL_NPCS
        if build_lock:base,prior=inputs(build_lock)
        npc=prior['equipment_resources']['npc_extra']
        checked=native_contract(base);contract(source,base)
        scene=prepare_scene(base,prior,source,output/'scene')
        checked['player_wade_lock_provider_bound']=True
        place_bindings=dict(npc['events']['placement']['bindings'])
        place_bindings.update(BINDINGS)
        if place_bindings['af_holiday_native_game']!=checked['game_context']:
            raise ValueError('Holiday placement points at the wrong game-context word')
        place_code,place=compile_part('holiday_placement',output/'placement',
            extra_sources=('overlays/v3/holiday_placement_native.c','overlays/v3/holiday_observers.c',
                'overlays/v3/holiday_observers_native.c'),link_symbols=place_bindings,
            defines=(f"AF_HOLIDAY_MIKO_PROFILE={SPECIAL_NPCS['GAFE01-r0/npc/ev-miko']['profile']}",))
        write_new(output/'placement.bin',place_code)
        bindings={name:place_bindings[name] for name in (
            'af_holiday_manager_descriptor','af_holiday_native_field_id','af_holiday_native_get_place',
            'af_holiday_native_reserve_place','af_holiday_native_set_status','af_holiday_native_check_status',
            'af_holiday_native_type','af_holiday_event_owner','af_holiday_event_data')}
        bindings.update(af_holiday_owner_keep=0x806F1B80,
            af_holiday_source_ids=npc['events']['native_directory']['identity_ram']+128,
            af_holiday_native_check_field=0x80087C40,af_holiday_native_pool_variant=0x8008930C,
            af_holiday_native_landmark=0x80089440,af_holiday_native_clear_place=0x80080F0C,
            af_holiday_native_structure=0x8008D3A4,af_holiday_native_clear_status=0x8007FE74,
            af_holiday_native_unable_wade=scene['contract']['wade_setter'],
            af_holiday_placement_native_show_id=place['symbols']['af_holiday_placement_native_show_id'])
        extra+=('overlays/v3/holiday_dedicated_native.c',)
        report['native']=dict(contract=checked,placement=place,placement_bindings=place_bindings,
            bindings=bindings,scene=scene,base_rom_sha256=sha256(base),installed=False,
            placement_callers_to_relink={name:dict(previous=npc['events']['placement']['code']['symbols'][name],
                prepared=place['symbols'][name]) for name in (
                    'af_holiday_placement_native_make','af_holiday_placement_native_show',
                    'af_holiday_placement_native_cull','af_holiday_npc_bind','af_holiday_npc_unregister')},
            remaining_providers=['installed actor/decoration/profile/effect identities',
                'imported fade transition (announcement reader prepared)',
                'imported common-state lifetime and manager dispatch'])
    code,compiled=compile_part('holiday_reserved',output/'code',extra_sources=extra,link_symbols=bindings)
    report.update(packet_bytes=len(data),packet_sha256=sha256(data),code=compiled,
        owners=owners,generated_source_sha256=sha256(generated.encode()),
        sources={p:sha256((ROOT/p).read_bytes()) for p in ('tools/v3_holiday_maps.py',
            'overlays/v3/holiday_reserved.c','overlays/v3/holiday_reserved.h','overlays/v3/holiday_reserved.ld',
            'overlays/v3/holiday_dedicated.h','overlays/v3/holiday_dedicated_source.h',
            'overlays/v3/holiday_dedicated_native.h','overlays/v3/holiday_dedicated_native.c',
            'tools/v3_holiday_placement.py','overlays/v3/holiday_placement.h',
            'overlays/v3/holiday_placement_native.c')})
    write_new(output/'maps.bin',data);write_new(output/'code.bin',code)
    write_new(output/'maps.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def install(base,prior,blob,core,output):
    """Connect prepared shared resources and existing callers without activation."""
    if prior['equipment_resources']['npc_extra']['events'].get('reserved'):
        from v3_holiday_active import install as install_active
        return install_active(base,prior,blob,core,output)
    del blob
    from v3_event_text import patch_bounds
    from v3_import_storage import replace_checked
    from v3_holiday_state import RAM as STATE_RAM,SIZE as STATE_SIZE
    from v3_holiday_placement import RAM as NPC_RAM,SIZE as NPC_SIZE,ADDRESS,OWNER_CODE
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];state=e.get('holiday_state')
    if not state or npc['events'].get('reserved') or prior['save_codec']['format_version']!=12:
        raise ValueError('Reserved event integration requires installed format-twelve state, once')
    prepared=prepare(output/'holiday-reserved',base=base,prior=prior)
    checked=prepared['native'];place=npc['events']['placement'];scene=checked['scene']
    records=copy.deepcopy(prior['physical_resources']);physical.verify(base,records)
    writes=[]
    def packet(p,size):
        raw=base[p['physical']:p['physical']+size]
        if p['bytes']!=size or sha256(raw)!=p['sha256']:
            raise ValueError('Changed complete shared event packet')
        return bytearray(raw)
    def replace_code(data,offset,limit,old,new,compiled,bindings):
        if (offset+old['bytes']>limit or offset+len(new)>limit or
            sha256(data[offset:offset+old['bytes']])!=old['sha256'] or
            any(data[offset+old['bytes']:limit])):
            raise ValueError('Changed event code or occupied expansion tail')
        for name,address in old['symbols'].items():
            if name.startswith('af_') and name not in bindings and compiled['symbols'].get(name)!=address:
                raise ValueError('Relink moved a retained shared entry: '+name)
        data[offset:limit]=new+bytes(limit-offset-len(new))
    def publish(p,data):
        previous=p['sha256'];p.update(sha256=sha256(data),crc32=zlib.crc32(data))
        matches=[r for r in records if r['id']==p['id']]
        if len(matches)!=1:raise ValueError('Ambiguous complete event packet')
        matches[0]['sha256']=p['sha256']
        writes.append((dict(matches[0],previous_sha256=previous),bytes(data)))
    np=npc['packet'];nd=packet(np,NPC_SIZE)
    flag=npc['record']['flags_offset']
    if nd[flag:flag+4]!=bytes(4):raise ValueError('Cannot relink an active unfinished holiday actor')
    # Placement exports may move. All callers are recompiled against their new
    # addresses; exported owner/state entries themselves must remain fixed.
    fresh=checked['placement'];raw=(output/'holiday-reserved/placement.bin').read_bytes()
    off=ADDRESS-NPC_RAM
    if (sha256(nd[off:off+place['code']['bytes']])!=place['code']['sha256'] or
        any(nd[off+place['code']['bytes']:NPC_SIZE-16]) or len(raw)>NPC_SIZE-16-off):
        raise ValueError('Changed placement code/reservation')
    nd[off:NPC_SIZE-16]=raw+bytes(NPC_SIZE-16-off-len(raw))
    owner_bindings=dict(place['owner_bindings'])
    for name,row in checked['placement_callers_to_relink'].items():
        if name in owner_bindings:owner_bindings[name]=row['prepared']
    owner_code,owner=compile_part('holiday_owner',output/'holiday-reserved/owner',link_symbols=owner_bindings)
    replace_code(nd,OWNER_CODE-NPC_RAM,0x9800,place['owner_code'],owner_code,owner,owner_bindings)
    sp=state['packet'];sd=packet(sp,STATE_SIZE);state_bindings=dict(state['bindings'])
    for name in ('af_holiday_npc_bind','af_holiday_npc_unregister'):
        state_bindings[name]=fresh['symbols'][name]
    defines=tuple(f[2:] for f in state['code']['flags'] if f.startswith('-D'))
    state_code,linked=compile_part('holiday_state',output/'holiday-reserved/state',
        defines=defines,link_symbols=state_bindings,extra_sources=('overlays/v3/diary.c',
            'overlays/v3/console_storage.c','overlays/v3/save_compressed.c','overlays/v3/holiday_npc.c'))
    replace_code(sd,0,0x4800,state['code'],state_code,linked,state_bindings)
    # Single bounds/occupancy check for the entire shared payload. Existing
    # dates, guards, saved fields, and resources are not relocated or rewritten.
    additions=((0x4800,0x7200,output/'holiday-reserved/code.bin'),
        (0x7200,0x7700,output/'holiday-reserved/scene/code/code.bin'),
        (0x7700,0x7800,output/'holiday-reserved/scene/titles.bin'),
        (0x7800,0x7F80,output/'holiday-reserved/maps.bin'))
    installed=[]
    for start,end,path in additions:
        data=path.read_bytes()
        if len(data)>end-start or any(sd[start:end]):raise ValueError('Event payload overlaps live services')
        sd[start:start+len(data)]=data
        installed.append(dict(ram=STATE_RAM+start,bytes=len(data),sha256=sha256(data),file=str(path.relative_to(output))))
    hook=scene['native_init_pointer_hook']
    replace_checked(core,hook['address']-CODE_RAM,struct.pack('>I',hook['before']),struct.pack('>I',hook['after']))
    scene['text']['hooks']=patch_bounds(core,scene['text']['first_id'],scene['text']['count'])
    scene.update(installed=True,native_execution_verified=False)
    place.update(code=fresh,bindings=checked['placement_bindings'],owner_code=owner,owner_bindings=owner_bindings)
    state.update(code=linked,bindings=state_bindings)
    npc['lifecycle']['code']=copy.deepcopy(linked)
    reserved=dict(prepared,installed=True,actor_owners_installed=False,resources=installed,
        additional_resident_bytes=0,saved_format_changed=False,native_execution_verified=False)
    reserved['native']['installed']=True
    reserved['owners']['primitive_adapter_bound']=True
    npc['events']['reserved']=reserved
    publish(np,nd);publish(sp,sd)
    sources={p:sha256((ROOT/p).read_bytes()) for p in (*prepared['sources'],
        'tools/v3_holiday_scene.py','overlays/v3/holiday_scene.c','overlays/v3/holiday_scene.h',
        'overlays/v3/holiday_scene.ld','tools/v3_holiday_state.py','tools/v3_holiday_dialogue.py',
        'tools/v3_resource_capacity.py','tools/v3_furniture_install.py','translations/provenance.json')}
    npc['sources'].update(sources);reserved['sources']=sources
    updates=dict(physical_resources=records,save_codec=copy.deepcopy(prior['save_codec']))
    updates['save_codec']['holiday_state_code']=copy.deepcopy(linked)
    write_new(output/'holiday-reserved/installed.json',(json.dumps(reserved,indent=2)+'\n').encode())
    write_new(output/'holiday-reserved/npc-packet.bin',nd)
    write_new(output/'holiday-reserved/state-packet.bin',sd)
    return e,{},updates,writes


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--build-lock',type=Path,help='Prepare checked native bindings against this exact current build')
    args=parser.parse_args();result=prepare(args.output,args.build_lock)
    print(json.dumps(dict(maps=len(result['maps']),variants=sum(r.get('variants',0) for r in result['maps']),
        packet_bytes=result['packet_bytes'],code_bytes=result['code']['bytes']),indent=2))
