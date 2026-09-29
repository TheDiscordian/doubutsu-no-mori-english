"""Connect hourly event state, native reset lifetime, and dedicated-owner access."""
import copy
import json
import re
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_import_storage import jump,replace_checked
from v3_npc_registry import RAM,SIZE

ADDRESS,COMMON=0x806F3000,0x806F3FE0
NATIVE=(
    ('af_holiday_active_update_original',0x8007EF18,0x8007F1A8,'fe41702b39ca0e90d01fe7207b7887937539dfa148ff2b8c5c4da065ef5bb760'),
    ('af_holiday_active_set',0x8007FE0C,0x8007FE74,'6f9021355b138f87eb5732632c02f35f99050d56245946343314fe8d172490d9'),
    ('af_holiday_active_clear',0x8007FEBC,0x8007FF08,'7b8655bbd956c1e22dfe167071c361461c43af68b9f960516cf383ad03001103'),
    ('af_holiday_native_check_status',0x8007FF08,0x8007FF8C,'fe7ae84ddd3ab1d4063ddc73d79e195e2d4237962c750616ad10fe15f9c48313'),
    ('af_holiday_native_get_place',0x80080D68,0x80080F0C,'1dd70446e8ed063f0d3a554ea1d7f43ee98a5d1313feffcee17bd8bb95bb5c94'),
    ('af_holiday_active_clear_rumours',0x80081424,0x80081434,'619a24a328656142c062043b909e9e7e6a4adabd5345397d633f8fd59a1af8af'),
    ('af_holiday_active_spread_rumour',0x80081434,0x80081460,'5842c290c8750c02dbd6d021229c050900448740d0269d2fc2dcfb286c00307b'),
    ('native_clear_event_info',0x8007D1DC,0x8007D25C,'9a220076bd04cf9175401d50bc52a5570d674b5cd3428b0b7e06f55da0d17a16'),
    ('native_clear_event_save',0x8007D4A0,0x8007D4C4,'16a7513b1f5b8c121acb046d5c4bb3dbf5cb5b5d5ff50ffbfbcde5bbd1cc4040'),
    ('native_common_reset',0x80078A10,0x80078A88,'87f88472b51a023605fdf1f994db14d3b8c510a86f85e910a60c6b1ec1a9ba8d'))
SOURCES=('tools/v3_holiday_active.py','overlays/v3/holiday_active.c',
    'overlays/v3/holiday_active.h','overlays/v3/holiday_active.ld','tools/v3_holiday_maps.py',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py','tools/v3_room_goods.py')
TRANSITION_PREPARED=ROOT/'build/v3-diary-category-work-01/transition-native-06'
TRANSITION_RAM,TRANSITION_PACKET_END=0x806FC000,0x80700000
DISPATCH_SOURCES=('overlays/v3/holiday_dispatch.c','overlays/v3/holiday_dispatch.h',
    'overlays/v3/holiday_dispatch_native.c','overlays/v3/holiday_dedicated_native.c')


def owner_requirements(maps,owners,generated,*,include_collision_positions=False):
    """Derive the entire admission list from source layouts and callback calls."""
    from v3_password_policy import function
    rows=[];requirements=[]
    for owner in owners['owners']:
        donor=owner['type'];needed=set();collision_only=[]
        local={r['symbol'] for r in owners['functions']}
        todo={n for n in owner['callbacks'] if n};seen=set();bodies=[]
        while todo:
            name=todo.pop();seen.add(name);body=function(generated,name);bodies.append(body)
            todo.update(set(re.findall(r'\b(\w+)\s*\(',body))&local-seen)
        reserved=[]
        for body in bodies:
            reserved.extend(re.findall(r'\bmake_(?:actor|FG)_in_reserved_block\(\s*evmgr\s*,\s*ctrl\s*,\s*([^,]+),',body))
        for row in maps['maps']:
            if row['event']==donor:
                for variant_index,variant in enumerate(row.get('layouts',[])):
                    for slot,actor in enumerate(variant):
                        # A resident-labelled collision position beyond the
                        # actual resident count is not an actor to spawn. The
                        # source callback must independently prove that no
                        # reserved-actor/foreground call uses that slot.
                        unused=(slot>=row['normal_npcs'] and row['npc_flags']&(1<<slot)
                            and actor['source_name']>>12==13 and reserved and
                            all(re.fullmatch(r'\d+',a.strip()) for a in reserved) and
                            slot not in {int(a) for a in reserved})
                        if unused:
                            collision_only.append(dict(variant=variant_index,slot=slot,
                                source_name=actor['source_name'],source_resident_count=row['normal_npcs']))
                        if include_collision_positions or not unused:
                            needed.add((0,str(actor['source_name'])))
        for name in owner['callbacks']:
            if not name:continue
            text=function(generated,name)
            for callee,kind in (('make_control_actor_without_indoor',1),('make_effect',2),('delete_effect',2)):
                for arg in re.findall(r'\b'+callee+r'\(([^()]*)\)',text):
                    arg=arg.strip()
                    if not re.fullmatch(r'(?:mAc_PROFILE_|eEC_EFFECT_)\w+',arg):
                        raise ValueError('Unresolved complete owner identity expression: '+arg)
                    needed.add((kind,arg))
        entries=sorted(needed);start=len(requirements);requirements.extend(entries)
        rows.append(dict(donor=donor,first=start,count=len(entries),
            phases=sum(1<<i for i,n in enumerate(owner['callbacks']) if n),requirements=entries))
        if collision_only and not include_collision_positions:rows[-1]['collision_only']=collision_only
    if len(rows)!=14 or len({r['donor'] for r in rows})!=14:
        raise ValueError('Incomplete dedicated owner admission directory')
    # The compiler evaluates the very same checked enums as the complete owner
    # bodies. No independently maintained numeric profile/effect aliases.
    enums=generated.split('#pragma GCC diagnostic push',1)[0].split('\n',1)[1]
    code='#include "holiday_dispatch.h"\n'+enums
    code+='const AFHolidayNeeds af_holiday_owner_needs[14]={\n'+''.join(
        '{'+','.join(str(r[k]) for k in ('donor','first','count','phases'))+'},\n' for r in rows)+'};\n'
    code+='const AFHolidayNeed af_holiday_identity_needs[]={\n'+''.join(
        '{'+str(kind)+','+value+'},\n' for kind,value in requirements)+'};\n'
    code+='const unsigned int af_holiday_identity_need_count='+str(len(requirements))+';\n'
    return code,rows


def refresh_dispatch(base,npc,records,directory,bindings,defines):
    """Bind installed provider categories without replacing event owners/art."""
    from v3_furniture_pipeline import Source
    from v3_holiday_maps import owner_source,discover
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,owners=owner_source(source)
    maps=discover(source)
    dependencies,requirements=owner_requirements(maps,owners,generated)
    events=npc['events'];active=events['active']
    if sha256(dependencies.encode())!=events['dispatch']['generated_requirements_sha256']:
        legacy,_=owner_requirements(maps,owners,generated,include_collision_positions=True)
        if sha256(legacy.encode())!=events['dispatch']['generated_requirements_sha256']:
            raise ValueError('Changed complete owner dependency graph')
    directory.mkdir()
    path=directory/'requirements.c'
    write_new(path,dependencies.replace('"holiday_dispatch.h"',
        '"/source/overlays/v3/holiday_dispatch.h"').encode())
    links=dict(active['bindings'],**bindings)
    code,compiled=compile_part('holiday_active',directory/'code',link_symbols=links,
        defines=defines,extra_sources=('overlays/v3/holiday_dispatch.c',
            'overlays/v3/holiday_dispatch_native.c',str(path.relative_to(ROOT))))
    for name in ('af_holiday_active_update','af_holiday_dedicated_current',
            *('af_holiday_dedicated_'+phase for phase in ('start','stop','in','out','behind'))):
        if compiled['symbols'][name]!=active['code']['symbols'][name]:
            raise ValueError('Moved retained active event dispatcher entry: '+name)
    packet=npc['packet'];data=bytearray(base[packet['physical']:packet['physical']+packet['bytes']])
    at,limit=ADDRESS-packet['ram'],COMMON-packet['ram'];old=active['code']
    if (sha256(data)!=packet['sha256'] or not 0<=at<limit<=len(data) or
            sha256(data[at:at+old['bytes']])!=old['sha256'] or
            any(data[at+old['bytes']:limit]) or len(code)>limit-at):
        raise ValueError('Changed shared owner code reservation')
    data[at:limit]=code+bytes(limit-at-len(code));previous=packet['sha256']
    packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    matches=[r for r in records if r['id']==packet['id']]
    if len(matches)!=1:raise ValueError('Ambiguous shared owner physical packet')
    matches[0]['sha256']=packet['sha256']
    active.update(code=compiled,bindings=links)
    events['dispatch'].update(code=compiled,bindings=links,provider_defines=list(defines),
        requirements=requirements,generated_requirements_sha256=sha256(dependencies.encode()))
    return (dict(matches[0],previous_sha256=previous),bytes(data))


def install_dispatch(base,prior,blob,core,output):
    """Connect all actual owner entries, guarding complete dependencies first."""
    del blob,core
    from v3_furniture_pipeline import Source
    from v3_holiday_maps import owner_source,discover
    from v3_campsite_manager import VROM,RELOC,RAM as OWNER
    from v3_decoration_actor import SERVICES
    from v3_registry import SPECIAL_NPCS
    import v3_physical_resources as physical
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra'];events=npc['events']
    if not events['transition'].get('native_scene_services_bound') or events.get('dispatch'):
        raise ValueError('Dedicated dispatch requires complete live transitions, once')
    if [(SPECIAL_NPCS[key]['donor_name'],SPECIAL_NPCS[key]['name']) for key in
            ('GAFE01-r0/npc/ev-soncho2','GAFE01-r0/npc/ev-miko')]!=[(0xD074,0xD090),(0xD03D,0xD091)]:
        raise ValueError('Changed fixed dedicated actor identities')
    physical.verify(base,prior['physical_resources'])
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,owners=owner_source(source);maps=discover(source)
    dependencies,requirements=owner_requirements(maps,owners,generated)
    directory=output/'holiday-dispatch';directory.mkdir(parents=True)
    for name,text,header in (('owners.c',generated,'holiday_dedicated_source.h'),
            ('requirements.c',dependencies,'holiday_dispatch.h')):
        write_new(directory/name,text.replace('"'+header+'"','"/source/overlays/v3/'+header+'"').encode())
    reserved=events['reserved'];bindings=dict(reserved['native']['bindings'])
    # Placement may have been refreshed since initial layout installation.
    bindings['af_holiday_placement_native_show_id']=events['placement']['code']['symbols']['af_holiday_placement_native_show_id']
    reserved_code,reserved_compiled=compile_part('holiday_reserved',directory/'reserved',
        extra_sources=(str((directory/'owners.c').relative_to(ROOT)),
            'overlays/v3/holiday_dedicated_native.c'),link_symbols=bindings)
    old_reserved=copy.deepcopy(reserved['code'])
    if reserved_compiled['symbols']['af_holiday_map_get']!=old_reserved['symbols']['af_holiday_map_get']:
        raise ValueError('Moved retained shared layout entry')
    active=events['active'];active_bindings=dict(active['bindings'])
    active_bindings.update(af_holiday_dedicated_native=reserved_compiled['symbols']['af_holiday_dedicated_native'],
        af_holiday_native_type=events['native_directory']['code']['symbols']['af_holiday_native_type'],
        af_holiday_native_set_status=0x8007FDA8,
        af_holiday_transition_live_fade=events['transition']['code']['symbols']['af_holiday_transition_live_fade'],
        af_holiday_transition_maps=0x806FB800,
        af_decor_actor_records=events['decorations']['controllers']['code']['symbols']['af_decor_actor_records'],
        af_holiday_decoration_ready=SERVICES,af_v3_npc_extras=RAM+0xA000)
    code,compiled=compile_part('holiday_active',directory/'code',link_symbols=active_bindings,
        extra_sources=('overlays/v3/holiday_dispatch.c','overlays/v3/holiday_dispatch_native.c',
            str((directory/'requirements.c').relative_to(ROOT))))
    for name in ('af_holiday_active_update','af_holiday_dedicated_current'):
        if compiled['symbols'][name]!=active['code']['symbols'][name]:
            raise ValueError('Moved retained event-state entry: '+name)
    records=copy.deepcopy(prior['physical_resources']);writes=[]
    def replace_code(packet,address,limit,old,new):
        data=bytearray(base[packet['physical']:packet['physical']+packet['bytes']]);start=address-packet['ram'];stop=limit-packet['ram']
        if (sha256(data)!=packet['sha256'] or not 0<=start<stop<=len(data) or
            old['bytes']>stop-start or len(new)>stop-start or
            sha256(data[start:start+old['bytes']])!=old['sha256'] or any(data[start+old['bytes']:stop])):
            raise ValueError('Changed or occupied shared owner code reservation')
        data[start:stop]=new+bytes(stop-start-len(new));previous=packet['sha256']
        packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
        matches=[r for r in records if r['id']==packet['id']]
        if len(matches)!=1:raise ValueError('Ambiguous shared owner physical packet')
        matches[0]['sha256']=packet['sha256'];writes.append((dict(matches[0],previous_sha256=previous),bytes(data)))
        return data
    p=equipment['holiday_state']['packet']
    state=replace_code(p,0x806F8800,0x806FB200,old_reserved,reserved_code)
    equipment['holiday_fishing']['packet']=copy.deepcopy(p)
    npc_data=replace_code(npc['packet'],ADDRESS,COMMON,active['code'],code)
    if npc_data[npc['record']['flags_offset']:npc['record']['flags_offset']+4]!=bytes(4):
        raise ValueError('Cannot connect incomplete owners after activation')
    # Retain all 29 original/camper rows and every null callback. Existing
    # imported callback words are resident and must have no overlay relocation.
    files=by_vrom(base);manager=copy.deepcopy(prior['campsite_manager'])
    before=files[VROM].extract(base);rel=files[RELOC].extract(base);image=bytearray(before)
    if sha256(before)!=manager['output_sha256'] or sha256(rel)!=manager['relocation_sha256']:
        raise ValueError('Changed complete event manager')
    relocation_words=set(struct.unpack_from('>'+str(struct.unpack_from('>I',rel,16)[0])+'I',rel,20))
    rows=manager['holiday_owners']['rows'];hooks=[]
    if len(rows)!=44 or manager['control_count']!=73:raise ValueError('Changed full owner directory')
    names=('start','stop','in','out','behind')
    for index,row in enumerate(rows):
        offset=manager['table']-OWNER+(29+index)*32
        current=list(struct.unpack_from('>8I',image,offset))
        if current!=[row['native'],*row['callbacks'],0,0]:raise ValueError('Changed actual owner callback row')
        if row['kind']!=4:continue
        for phase,old in enumerate(row['callbacks']):
            if not old:continue
            at=offset+4+phase*4
            if old!=events['placement']['owner_code']['symbols']['af_holiday_owner_unbound'] or (0x42000000|at) in relocation_words:
                raise ValueError('Unexpected dedicated owner target or relocation')
            new=compiled['symbols']['af_holiday_dedicated_'+names[phase]]
            replace_checked(image,at,struct.pack('>I',old),struct.pack('>I',new))
            row['callbacks'][phase]=new;hooks.append(dict(donor=row['donor'],phase=phase,address=OWNER+at,before=old,after=new))
        row['dedicated_callbacks_bound']=True
    manager['output_sha256']=sha256(image)
    manager['holiday_owners']['all_dedicated_callbacks_bound']=True
    active.update(code=compiled,bindings=active_bindings,owner_dispatch_bound=True,
        owner_services_bound=False)
    reserved.update(code=reserved_compiled,actor_owners_installed=False)
    reserved['native']['bindings']=bindings
    reserved['native']['remaining_providers']=['participant/controller/effect lifecycle bindings and calendar choice']
    # Refresh the existing code receipt, not its independent graphics/resources.
    loaded=dict(ram=0x806F8800,bytes=len(reserved_code),sha256=sha256(reserved_code))
    for row in reserved['resources']:
        if row['ram']==loaded['ram']:row.update(loaded)
    events['decorations']['controllers']['preserved'].append(loaded)
    sources={p:sha256((ROOT/p).read_bytes()) for p in (*SOURCES,*DISPATCH_SOURCES)}
    reserved['sources'].update(sources)
    report=dict(installed=True,callbacks_bound=hooks,requirements=requirements,
        code=compiled,reserved_code=reserved_compiled,bindings=active_bindings,
        generated_requirements_sha256=sha256(dependencies.encode()),
        complete_dependency_preflight=True,negative_transition_is_failure=True,
        actor_active=False,native_execution_verified=False,additional_resident_bytes=0,
        saved_format_changed=False,sources=sources,
        pending=['participant/controller/effect lifecycle bindings','calendar behaviour choice','actor and diary admission'])
    events['dispatch']=report;events['placement']['dedicated_callbacks_bound']=True
    npc['sources'].update(sources)
    for name,data in (('npc-packet.bin',npc_data),('state-packet.bin',state)):
        write_new(directory/name,data)
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return equipment,{VROM:bytes(image)},dict(physical_resources=records,campsite_manager=manager),writes


def donor_update(source):
    from v3_password_policy import function
    path=ROOT/'local/ac-decomp/src/game/m_event.c';text=path.read_text()
    if sha256(path.read_bytes())!='82a0d9ebdc4915357f5dd4217b49a978e6c680687dd4d7850e281a5a3a5741ef':
        raise ValueError('Changed complete source event lifecycle')
    records={}
    for name in ('mEv_ClearEventInfo','update_active'):
        offsets=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(offsets)!=1:raise ValueError('Ambiguous complete donor event function: '+name)
        _,records[name]=source.function(offsets[0])
    body=function(text,'update_active')
    return body,dict(functions=records,source_sha256=sha256(path.read_bytes()),
        update_source_sha256=sha256(body.encode()),sports_event_ids=[12,13,14,15,16],
        common_state_bytes=4,initial_value=-1)


def patch_core(core,entry):
    for name,lo,hi,digest in NATIVE:
        if sha256(core[lo-CODE_RAM:hi-CODE_RAM])!=digest:
            raise ValueError('Changed complete native event dependency: '+name)
    hooks=[]
    def patch(address,after):
        before=bytes(core[address-CODE_RAM:address-CODE_RAM+len(after)])
        replace_checked(core,address-CODE_RAM,before,after)
        row=dict(address=address,bytes=len(after),before=before.hex(),after=after.hex(),
            before_sha256=sha256(before),sha256=sha256(after))
        hooks.append(row);return row
    patch(0x8007EF18,struct.pack('>2I',jump(entry),0))
    # Preserve native saved initialization and additive keep-flag clearing.
    # t9 still holds -1 and t0 is already 806F0000; there is one trailing NOP.
    old=list(struct.unpack_from('>30I',core,0x80078A10-CODE_RAM))
    if old[22:24]!=[0xAD001B80,0xAD001B84] or old[-1]!=0:
        raise ValueError('Changed native common reset insertion point')
    common=patch(0x80078A10,struct.pack('>30I',*(old[:24]+[0xAD193FE0]+old[24:-1])))
    # Compress seven original zero stores into the checked native memset.
    # ClearEventInfo may run before packet load, so it never calls packet code.
    words=(0x27BDFFE8,0xAFBF0014,0x3C048014,0x2484A0E0,0x00002825,
        jump(0x8003B9B0,link=True),0x2406001C,jump(0x8007D4A0,link=True),0,
        0x3C08806F,0x2419FFFF,0xAD193FE0,0,0)
    patch(0x8007D1DC,struct.pack('>14I',*words))
    return hooks,common


def install(base,prior,blob,core,output):
    if prior['equipment_resources']['npc_extra']['events'].get('transition'):
        from v3_holiday_structures import install as install_decorations
        return install_decorations(base,prior,output)
    if prior['equipment_resources']['npc_extra']['events'].get('active'):
        return install_transition(base,prior,output)
    del blob
    from v3_furniture_pipeline import Source
    from v3_holiday_transition import MEMORY_NATIVE
    from v3_holiday_native import identities
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];events=npc['events']
    if not events.get('reserved') or events.get('active') or prior['save_codec']['format_version']!=12:
        raise ValueError('Hourly connection requires installed shared owners and format twelve, once')
    for name,vrom,ram,at,size,digest in MEMORY_NATIVE:
        if name!='memset':continue
        raw=by_vrom(base)[vrom].extract(base)
        if sha256(raw[at-ram:at-ram+size])!=digest:raise ValueError('Changed complete native reset memset')
    packet=npc['packet'];data=bytearray(base[packet['physical']:packet['physical']+SIZE])
    if packet['ram']!=RAM or packet['bytes']!=SIZE or sha256(data)!=packet['sha256']:
        raise ValueError('Changed complete NPC event packet')
    start=ADDRESS-RAM;stop=SIZE-16
    if any(data[start:stop]) or data[-16:]!=bytes.fromhex('41464E58')*4:
        raise ValueError('Occupied hourly state/code range or changed NPC guard')
    registry=events['native_directory'];ids,_=identities();id_offset=registry['identity_ram']-RAM
    if (registry['days_ram']!=0x806F1500 or registry['day_capacity']!=64 or
        data[id_offset:id_offset+256]!=ids or
        data[npc['record']['flags_offset']:npc['record']['flags_offset']+4]!=bytes(4)):
        raise ValueError('Changed identity/storage contract or active unfinished owner')
    directory=output/'holiday-active';directory.mkdir(parents=True)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    _,donor=donor_update(source)
    bindings={name:lo for name,lo,_,_ in NATIVE[1:7]}
    bindings.update(af_holiday_native_days=registry['days_ram'],af_holiday_native_index=0x804A2B00,
        af_holiday_source_ids=registry['identity_ram']+128,af_holiday_dedicated_common=COMMON,
        af_holiday_active_hour=0x80136FBE,af_holiday_active_too_short=0x8013777C,
        af_holiday_active_delete=0x80135DEC,af_holiday_active_rumour_count=0x80104F90,
        af_holiday_active_rumours=0x80104F2C,
        af_holiday_dedicated_native=events['reserved']['code']['symbols']['af_holiday_dedicated_native'])
    code,compiled=compile_part('holiday_active',directory/'code',link_symbols=bindings)
    if len(code)>COMMON-ADDRESS:raise ValueError('Hourly code overlaps common event state')
    hooks,reset=patch_core(core,compiled['symbols']['af_holiday_active_update'])
    data[start:start+len(code)]=code
    struct.pack_into('>hh',data,COMMON-RAM,-1,-1)
    before=packet['sha256'];packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    records=copy.deepcopy(prior['physical_resources']);physical.verify(base,records)
    matches=[r for r in records if r['id']==packet['id']]
    if len(matches)!=1:raise ValueError('Ambiguous NPC physical resource')
    matches[0]['sha256']=packet['sha256']
    # Update the same reset receipt used by later placement refreshes.
    events['placement']['keep_reset'].update(sha256=reset['sha256'],
        imported_common_ram=COMMON,imported_common_bytes=4,imported_common_initial=-1)
    report=dict(code=compiled,bindings=bindings,donor=donor,native_functions=NATIVE,
        hooks=hooks,common=dict(ram=COMMON,bytes=4,initial_hex='ffffffff',saved=False,
            reset_callers=[0x80078A10,0x8007D1DC],survives_scene_changes=True),
        installed=True,additional_resident_bytes=0,saved_format_changed=False,
        owner_services_bound=False,native_execution_verified=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    events['active']=report;npc['sources'].update(report['sources'])
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(directory/'npc-packet.bin',data)
    return e,{},dict(physical_resources=records),[(dict(matches[0],previous_sha256=before),bytes(data))]


def install_transition(base,prior,output):
    """Load the unchanged prepared module through the existing startup owner.

    Inactive providers remain inactive; loading checked code is not activation.
    Keep the previous physical allocation intact in the new ROM as well.
    """
    from v3_console_disk_install import reservations
    from v3_holiday_state import RAM as STATE_RAM,SIZE as STATE_SIZE,GUARD
    from v3_holiday_transition import NATIVE as GEOMETRY,SCENE_NATIVE,MEMORY_NATIVE
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];events=npc['events'];s=e['holiday_state']
    if not events.get('active') or events.get('transition'):
        raise ValueError('Scene packet requires connected hourly/common state, once')
    if any(a<TRANSITION_PACKET_END and TRANSITION_RAM<b for a,b in reservations(prior)):
        raise ValueError('Scene packet overlaps an existing RAM reservation')
    prepared=json.loads((TRANSITION_PREPARED/'transition.json').read_bytes())
    code=(TRANSITION_PREPARED/'code.bin').read_bytes()
    if (len(code)!=prepared['code']['bytes'] or sha256(code)!=prepared['code']['sha256'] or
        not 0<len(code)<=0x3000 or prepared['planned_code_range']!=[TRANSITION_RAM,0x806FF000] or
        prepared['code']['symbols']['af_holiday_transition_run']!=TRANSITION_RAM or
        prepared['installed'] or not prepared['native_scene_bridge_compiled']):
        raise ValueError('Changed complete prepared scene-transition module')
    for path,digest in prepared['sources'].items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Stale prepared transition: '+path)
    if sha256((TRANSITION_PREPARED/'source.c').read_bytes())!=prepared['generated_sha256']:
        raise ValueError('Changed complete generated scene source')
    files=by_vrom(base);core=files[CODE_VROM].extract(base)
    for name,lo,hi,digest in (*GEOMETRY,*SCENE_NATIVE):
        if sha256(core[lo-CODE_RAM:hi-CODE_RAM])!=digest:
            raise ValueError('Changed complete scene primitive: '+name)
    for name,vrom,ram,at,size,digest in MEMORY_NATIVE:
        raw=files[vrom].extract(base)
        if sha256(raw[at-ram:at-ram+size])!=digest:raise ValueError('Changed complete scene memory helper: '+name)
    owner=files[0x03800000].extract(base)
    if (sha256(owner[0x8095EC24-0x8095B8B0:0x8095EDE4-0x8095B8B0])!=prepared['native_fade_sha256'] or
        core[0x800B1C84-CODE_RAM:0x800B1C90-CODE_RAM]!=bytes.fromhex('8c821c9003e0000800000000')):
        raise ValueError('Changed native scene/player layout contract')
    bindings={f'af_holiday_transition_{n}':lo for n,lo,_,_ in (*GEOMETRY,*SCENE_NATIVE)}
    bindings.update(af_holiday_map_get=events['reserved']['code']['symbols']['af_holiday_map_get'],
        af_holiday_native_type=events['native_directory']['code']['symbols']['af_holiday_native_type'],
        af_holiday_native_game=0x8010EF90,af_holiday_transition_common=0x80136EA0,
        af_holiday_transition_scene=0x80126EB4,af_holiday_transition_player=0x800B1C84)
    bindings.update({name:at for name,_,_,at,_,_ in MEMORY_NATIVE})
    if bindings!=prepared['bindings'] or bindings!=prepared['code']['link_symbols']:
        raise ValueError('Prepared scene module has stale caller bindings')
    old=s['packet'];prefix=base[old['physical']:old['physical']+old['bytes']]
    if (old['ram']!=STATE_RAM or old['bytes']!=STATE_SIZE or sha256(prefix)!=old['sha256'] or
        prefix[-16:]!=GUARD or STATE_RAM+STATE_SIZE!=TRANSITION_RAM):
        raise ValueError('Changed complete holiday-state prefix')
    data=prefix+code+bytes(TRANSITION_PACKET_END-TRANSITION_RAM-16-len(code))+GUARD
    records=copy.deepcopy(prior['physical_resources'])
    new=physical.allocate(base,records,data,'holiday-transition-GAFE01-r0');records.append(new)
    s['packet']=dict(new,ram=STATE_RAM,crc32=zlib.crc32(data),storage='physical-ROM',guard=GUARD.hex())
    stage=dict(prepared,installed=True,native_scene_services_bound=False,
        prepared_directory=str(TRANSITION_PREPARED.relative_to(ROOT)),input_rom_sha256=sha256(base),
        packet_ram=STATE_RAM,packet_bytes=len(data),additional_resident_bytes=0x4000,
        loaded_code=dict(ram=TRANSITION_RAM,bytes=len(code),sha256=sha256(code)),
        preserved_prefix_sha256=sha256(prefix),preserved_prefix_bytes=len(prefix),
        original_packet=copy.deepcopy(old),native_execution_verified=False,
        pending=[p for p in prepared['pending'] if not p.startswith('Common-state lifetime')]+[
            'Live dedicated-owner dispatch with complete scene providers',
            'Costume/exercise/Miko/race actors and explicit calendar behaviour choice'])
    events['transition']=stage
    sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}
    npc['sources'].update(sources);stage['installation_sources']=sources
    directory=output/'holiday-transition';directory.mkdir(parents=True)
    write_new(directory/'installed.json',(json.dumps(stage,indent=2)+'\n').encode())
    write_new(directory/'state-packet.bin',data)
    return e,{},dict(physical_resources=records),[(new,data)]
