"""Install saved holiday state and link the complete prepared NPC lifecycle."""
import copy
import json
import re
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_console_disk_install import reservations
from v3_diaries import LAYOUT
from v3_furniture_pipeline import Source
from v3_import_storage import jump,replace_checked
from v3_npc_registry import RAM as NPC_RAM,SIZE as NPC_SIZE,TABLE as NPC_TABLE
import v3_physical_resources as physical

RAM,SIZE,TABLE=0x806F4000,0x8000,0x7F80
GUARD=bytes.fromhex('41464853')*4
CALENDAR_SHA='2afd25eb770d0e92ba33df4e079af38cbbe3c7c1cf81d33e8957c3c6559b87ec'
WARNING=('Format-12 experimental saves require this or a newer compatible build. '
    'Compatible older saves migrate forward, retaining diary pages and existing progress. '
    'V2 and format-11-or-earlier V3 builds cannot load new saves. Preserve backups. '
    'Native diary/holiday gameplay and save/reload remain unverified.')
REFERENCES={
    'src/game/m_soncho.c':'86925ff50163654cf795045563d93fa9da6859e81c6c5cf5d4e42fcc9bf8bf11',
    'src/lb_reki.c':'a10a18671f43387c9aef040abff56cbf9ad7abd03553e23347348a570dcae4b1',
    'src/game/m_start_data_init.c':'d3b07718ee603aa50527a1523c626966026281af58b533d60ab2ef2628325d32'}
SOURCES=('tools/v3_holiday_state.py','tools/v3_holiday_placement.py','tools/v3_room_goods.py',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py','overlays/v3/surface_bootstrap.c',
    'overlays/v3/holiday_state.c','overlays/v3/holiday_state.h','overlays/v3/holiday_state.ld',
    'overlays/v3/holiday_npc.c','overlays/v3/holiday_npc.h','overlays/v3/holiday_native.h',
    'overlays/v3/npc_registry.h','overlays/v3/diary.c',
    'overlays/v3/diary.h','overlays/v3/console_storage.c','overlays/v3/console_storage.h',
    'overlays/v3/save_compressed.c','overlays/v3/save_compressed.h')


def contract(source):
    for path,digest in REFERENCES.items():
        if sha256((ROOT/'local/ac-decomp'/path).read_bytes())!=digest:
            raise ValueError('Changed complete holiday state reference: '+path)
    functions=[]
    for match in re.finditer(r'^(mSC_LightHouse_\w+|lbRk_(?:VernalEquinoxDay|AutumnalEquinoxDay|HarvestMoonDay)) = \.text:0x([0-9A-Fa-f]+);',source.symbols,re.M):
        code,row=source.function(int(match[2],16));functions.append(dict(row,sha256=sha256(code)))
    data=source.raw('ev_day$400')
    if len(data)!=58 or sha256(data)!='b9674c5e99839c59b259304ae33272084457bb4ad3c1f4991bed0d162ad0e347':
        raise ValueError('Changed complete donor harvest dates')
    return data,dict(references=REFERENCES,functions=functions,harvest_symbol='ev_day$400',
        harvest_sha256=sha256(data),harvest_years=[2002,2030],native_lunar_bounds=[2000,2032],
        town_day_random_bound=30,town_day_excludes=4,quest_days=17,working_days=7,
        completion_check_after_flag=True)


def install(base,prior,blob,core,output):
    del blob
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];d=e['diaries']
    if e.get('holiday_state') or prior['save_codec']['format_version']!=11:
        raise ValueError('Holiday state requires the installed format-eleven diary path')
    if any(a<RAM+SIZE and RAM<b for a,b in reservations(prior)):
        raise ValueError('Holiday services overlap a retained RAM allocation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    dates,checked=contract(source)
    native=by_vrom(base)[CODE_VROM].extract(base)
    if sha256(native[0x8007F358-CODE_RAM:0x8007F6A0-CODE_RAM])!=CALENDAR_SHA:
        raise ValueError('Changed complete native calendar caller/job gate/cleanup')
    old=d['compiled'];symbols=old['symbols']
    bindings={n:symbols[n] for n in ('af_diary_days','af_v3_require_save_state','af_v3_save_halt',
        'af_v3_save_check_extended','af_v3_save_pack_extended','af_v3_creature_player_clear')}
    for section,names in (
        (npc['world'],('af_holiday_world_bind','af_holiday_world_resources','af_holiday_npc_resources',
            'af_holiday_actor_construct','af_holiday_actor_think_init','af_holiday_actor_think_elapsed',
            'af_holiday_actor_request','af_holiday_actor_prepare','af_holiday_actor_start','af_holiday_actor_talk')),
        (npc['motion'],('af_holiday_motion_bind','af_holiday_motion_resources')),
        (npc['dialogue'],('af_holiday_dialogue_bind','af_holiday_npc_continue')),
        (npc['events']['placement'],('af_holiday_npc_bind','af_holiday_npc_unregister'))):
        bindings.update({n:section['code']['symbols'][n] for n in names})
    bindings.update(af_v3_npc_extras=NPC_RAM+NPC_TABLE,
        af_holiday_native_schedule=npc['events']['native_directory']['code']['symbols']['af_holiday_native_schedule'],
        af_holiday_calendar_previous=prior['campsite_calendar']['code']['symbols']['af_v3_campsite_before_cleanup'])
    defines=tuple(f[2:] for f in old['flags'] if f.startswith('-D'))+('AF_V3_HOLIDAY_STORAGE=1',)
    directory=output/'holiday-state'
    code,compiled=compile_part('holiday_state',directory/'code',defines=defines,link_symbols=bindings,
        extra_sources=('overlays/v3/diary.c','overlays/v3/console_storage.c',
            'overlays/v3/save_compressed.c','overlays/v3/holiday_npc.c'))
    data=code.ljust(TABLE,b'\0')+dates
    data=data.ljust(SIZE-16,b'\0')+GUARD
    if len(data)!=SIZE or len(code)>TABLE:raise ValueError('Holiday services exceed checked packet')
    records=copy.deepcopy(prior['physical_resources']);physical.verify(base,records)
    new=physical.allocate(base,records,data,'holiday-state-GAFE01-r0')
    records.append(new);writes=[(new,data)]
    # Install the actual native caller and every prepared actor profile callback
    # together. Selection flags remain zero; no incomplete event is enabled.
    call=0x8007F630
    hook_before=struct.pack('>2I',jump(bindings['af_holiday_calendar_previous'],link=True),0)
    hook_after=struct.pack('>2I',jump(compiled['symbols']['af_holiday_calendar_before_cleanup'],link=True),0)
    replace_checked(core,call-CODE_RAM,hook_before,hook_after)
    np=npc['packet'];npcdata=bytearray(base[np['physical']:np['physical']+NPC_SIZE])
    if len(npcdata)!=NPC_SIZE or sha256(npcdata)!=np['sha256']:
        raise ValueError('Changed complete NPC packet before lifecycle binding')
    if npcdata[npc['record']['flags_offset']:npc['record']['flags_offset']+4]!=bytes(4):
        raise ValueError('Cannot bind lifecycle over an active or changed NPC selection')
    fixups=[]
    for row in npc['record']['profile_fixups']:
        at=row['offset'];target=compiled['symbols'][row['symbol']]
        replace_checked(npcdata,at,bytes(4),struct.pack('>I',target))
        fixups.append(dict(row,target=target))
    previous=np['sha256'];np.update(sha256=sha256(npcdata),crc32=zlib.crc32(npcdata))
    records=[dict(r,sha256=np['sha256']) if r['id']==np['id'] else r for r in records]
    writes.append((dict(next(r for r in records if r['id']==np['id']),previous_sha256=previous),bytes(npcdata)))
    packet=d['packets']['storage'];before=base[packet['physical']:packet['physical']+packet['bytes']]
    if sha256(before)!=packet['sha256'] or sha256(before[:old['bytes']])!=old['sha256']:
        raise ValueError('Changed complete prior diary/save code')
    patched=bytearray(before);redirects=[]
    # Keep every existing caller and function pointer valid. Redirect all public
    # functions defined in the changed modules, leaving private old code intact.
    addresses=sorted(set(v for v in symbols.values() if LAYOUT['code']['ram']<=v<LAYOUT['code']['ram']+old['bytes']))
    for name,target in compiled['symbols'].items():
        if name in bindings or not name.startswith('af_') or name not in symbols or not RAM<=target<RAM+len(code):continue
        address=symbols[name];at=address-LAYOUT['code']['ram']
        if not 0<=at<old['bytes']:raise ValueError('Holiday redirect escapes old code')
        following=next((v for v in addresses if v>address),LAYOUT['code']['ram']+old['bytes'])
        if following-address<8:raise ValueError('Holiday redirect overlaps next symbol: '+name)
        original=bytes(patched[at:at+8]);replacement=struct.pack('>2I',jump(target),0)
        patched[at:at+8]=replacement
        redirects.append(dict(name=name,address=address,target=target,before=original.hex(),after=replacement.hex()))
    required={'af_diary_reset','af_diary_valid','af_diary_player_clear','af_v3_save_check','af_v3_save_pack',
        'af_v3_console_storage_reset','af_v3_console_storage_valid','af_v3_console_storage_commit',
        'af_v3_save_expand_diary','af_v3_save_compress_diary','af_v3_diary_measure','af_v3_diary_data'}
    if not required<={r['name'] for r in redirects}:raise ValueError('Incomplete shared holiday/save redirects')
    previous=packet['sha256'];packet.update(sha256=sha256(patched),crc32=zlib.crc32(patched))
    records=[dict(r,sha256=packet['sha256']) if r['id']==packet['id'] else r for r in records]
    writes.append((dict(next(r for r in records if r['id']==packet['id']),previous_sha256=previous),bytes(patched)))
    old.update(sha256=sha256(patched[:old['bytes']]),holiday_redirects=redirects)
    e['console_storage'].update(diary_runtime=copy.deepcopy(old),save_format=12)
    state=dict(format='AFV3-HOLIDAY-STATE-1',code=compiled,bindings=bindings,contract=checked,
        packet=dict(new,ram=RAM,crc32=zlib.crc32(data),storage='physical-ROM',guard=GUARD.hex()),
        installed=True,lifecycle_linked=True,actor_active=False,native_schedule_caller_bound=True,
        calendar_hook=dict(address=call,before=hook_before.hex(),after=hook_after.hex(),
            predecessor_function_sha256=CALENDAR_SHA,original_job_gate_retained=True,
            camper_and_native_cleanup_retained=True),profile_fixups=fixups,
        save_format=12,diary_format=2,serialized_bytes_unchanged=True,additional_resident_bytes=SIZE,
        saved_profile_changed=False,saved_format_changed=True,native_execution_verified=False,
        redirects=redirects,sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    e['holiday_state']=state
    npc['events']['placement']['observers']['event_world_bound']=True
    npc['lifecycle']=dict(code=compiled,linked=True,callbacks_installed=True,active=False)
    npc['events']['native_directory']['native_schedule_caller_bound']=True
    npc['pending']=['Complete dedicated/costume/exercise owners and calendar behaviour choice',
        'Separate exercise/card route','Actor activation and connected diary gameplay/save verification']
    npc['sources'].update(state['sources']);d['sources'].update(state['sources'])
    updates={k:copy.deepcopy(prior[k]) for k in ('save_runtime','save_codec','clothing','room_surfaces')}
    updates['save_runtime']['diary_runtime_code']=copy.deepcopy(old)
    updates['save_codec'].update(format_version=12,active_storage_code=copy.deepcopy(old),holiday_state_code=compiled)
    updates['clothing']['save_extension'].update(format_version=12,active_storage_code=copy.deepcopy(old))
    updates['clothing']['save_extension']['legacy_formats_read']=list(dict.fromkeys(
        [*updates['clothing']['save_extension']['legacy_formats_read'],'AFS3-v11']))
    updates['room_surfaces']['save']['disk_format_version']=12
    updates.update(physical_resources=records,saved_format_changed=True,save_warning=WARNING)
    write_new(directory/'state.json',(json.dumps(state,indent=2)+'\n').encode())
    write_new(directory/'packet.bin',data);write_new(directory/'diary-storage.bin',patched)
    write_new(directory/'npc-packet.bin',npcdata)
    return e,{},updates,writes
