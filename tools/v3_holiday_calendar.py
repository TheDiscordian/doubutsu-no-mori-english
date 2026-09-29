"""Connect the shared native/imported calendar and every diary style.

This supplements either choice with GC-only holidays and keeps N64-only dates.
The choice is not exposed until complete event/actor admission is installed.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from apply_translation import write_new
from v3_asset_loader import ROOT, compile_part
from v3_campsite_event import SCHEDULE_SHA
from v3_diary_events import TABLE_SHA
from v3_furniture_pipeline import Source
from v3_import_storage import jump, replace_checked
import v3_physical_resources as physical

# Corresponding rows, not interchangeable event IDs. Native-only celebrations,
# saved shop/visitor dates, and unknown relations are retained. 255 suppresses
# the native August fireworks conversation period in the July 4 calendar.
NATIVE_SOURCES = {
    14:24,15:26,16:27,17:28,18:13,19:32,20:33,23:14,24:53,25:58,
    26:45,28:48,29:34,30:36,31:37,32:38,33:39,34:42,35:41,
    40:60,41:62,42:63,43:70,44:71,45:72,46:64,47:67,48:255,49:66,
    50:90,52:93,53:92,58:81,59:83,60:84,61:85,62:86,63:89,64:88,
    65:96,66:97,67:98,68:99,69:102,70:101,71:107,72:109,73:110,
    74:122,75:123,76:124,77:125,78:126,79:128,80:129,
}
# Calendar counterparts for all relevant donor owners. Shared sports owners
# have spring and autumn rows, resolved from the actual source month below.
DONOR_NATIVE = {1:14,11:29,20:26,35:43,41:58,43:50,64:78,
    80:14,82:29,84:26,87:24,89:25,90:40,92:46,96:58,97:50,99:68,102:71,107:78}
SPORTS_NATIVE = {12:32,13:30,14:33,15:31,16:29}
OBSERVERS = (
    (0x8007FCB8,0x8007FD40,'9418301d9b9e765c96f90f240c4d32e708eba4fd08102e9a643341f177a210a4','af_holiday_calendar_today'),
    (0x8007FD40,0x8007FDA8,'eb5b4e314ceea647d849894d5d1375994c6e8062b857022c2d888527caf472aa','af_holiday_calendar_run_today'),
    (0x8007FF08,0x8007FF8C,'fe7ae84ddd3ab1d4063ddc73d79e195e2d4237962c750616ad10fe15f9c48313','af_holiday_calendar_status'),
)
SOURCES = ('tools/v3_holiday_calendar.py','overlays/v3/holiday_calendar.c',
    'overlays/v3/holiday_calendar.h','overlays/v3/holiday_calendar.ld',
    'overlays/v3/holiday_diary.c','overlays/v3/holiday_events.c','overlays/v3/holiday_events.h',
    'overlays/v3/diary_events.c','overlays/v3/diary_events.h','overlays/v3/diary_native.c',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py')


def data_source(base,source,events):
    core=by_vrom(base)[CODE_VROM].extract(base)
    master=core[0x80104B60-CODE_RAM:0x80104F2C-CODE_RAM]
    schedule=source.raw('event_schedule_data')
    if sha256(master)!=TABLE_SHA or sha256(schedule)!=SCHEDULE_SHA:
        raise ValueError('Changed complete native or donor calendar master')
    rows=[schedule[i:i+12] for i in range(0,len(schedule),12)]
    generated=['const unsigned int af_holiday_calendar_choice=0;\n',
        'const unsigned char af_holiday_calendar_native_sources[81][12]={\n']
    native=[]
    for index,source_index in NATIVE_SOURCES.items():
        raw=bytes([255])+bytes(11) if source_index==255 else rows[source_index]
        if source_index!=255 and (raw[0]&0x10 or raw[4]&0x10 or raw[2] or raw[6]):
            raise ValueError('Calendar relation unexpectedly needs saved-date slots')
        generated.append(f'[{index}]={{'+','.join(str(v) for v in raw)+'},\n')
        native.append(dict(native_row=index,native_type=u32(master,index*12+8),
            source_row=None if source_index==255 else source_index,source_hex=raw.hex()))
    generated.append('};\nconst unsigned char af_holiday_calendar_donor_rows[49]={\n')
    counterparts=[]
    for i,row in enumerate(events['contract']['rows']):
        raw=bytes.fromhex(row['hex']);kind=row['type'];native_index=DONOR_NATIVE.get(kind,255)
        if kind in SPORTS_NATIVE:
            if raw[0] not in (3,9):raise ValueError('Changed sports event source month')
            native_index=SPORTS_NATIVE[kind]+(29 if raw[0]==9 else 0)
        generated.append(str(native_index)+',')
        counterparts.append(dict(row=i,donor_type=kind,native_row=None if native_index==255 else native_index))
    if len(counterparts)!=49:raise ValueError('Incomplete shared calendar owner batch')
    generated.append('\n};\n')
    return ''.join(generated).encode(),dict(native=native,donor=counterparts,
        native_master_sha256=TABLE_SHA,donor_master_sha256=SCHEDULE_SHA,
        additional_calendar_labels=[f'v3/holiday/event/{i:02d}' for i in range(28)],
        native_only_events_preserved=True,gamecube_only_events_in_both_modes=True)


def prepare(base,prior,output):
    e=prior['equipment_resources'];npc=e['npc_extra'];events=npc['events']
    if not e.get('holiday_items',{}).get('controls') or events.get('calendar'):
        raise ValueError('Calendar connection requires installed carried controls and no duplicate module')
    physical.verify(base,prior['physical_resources'])
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    data,contract=data_source(base,source,events)
    directory=output/'holiday-calendar';directory.mkdir();write_new(directory/'data.c',data)
    ui=e['diaries']['ui_compiled'];world=npc['world']['code']['symbols']
    state=e['holiday_state']['code']['symbols'];native=events['native_directory']['code']['symbols']
    storage=e['holiday_items']['controls']['storage']['code']['symbols']
    old=events['sky']['packet'];start=old['ram']+old['bytes']
    bindings=dict(ui['bindings'])
    # Screen/art remain intact. Only the native calendar/entry provider changes.
    bindings['af_diary_screen_open']=ui['symbols']['af_diary_screen_open']
    for name in ('af_diary_event_rules','af_diary_event_labels'):
        bindings[name]=ui['symbols'][name]
    for name in ('af_diary_valid','af_diary_days','af_diary_weekday','af_diary_calendar_event_check'):
        bindings[name]=world[name]
    bindings['af_v3_diary_data']=storage['af_v3_diary_data']
    for name in ('af_holiday_state_dates','af_holiday_state_init'):
        bindings[name]=state[name]
    bindings.update(AF_HCAL_LINK_RAM=start,af_holiday_native_merge=native['af_holiday_native_merge'],
        af_holiday_native_type=native['af_holiday_native_type'],
        af_holiday_native_index=native['af_holiday_native_index'],
        af_holiday_native_days=native['af_holiday_native_days'],
        af_holiday_rtc=0x80136FBC,af_holiday_random_native=0x8002C9AC,
        af_hp_available=events['participants']['code']['symbols']['af_hp_available'])
    # Bind actual packet offsets, not guessed event/registry bases.
    bindings['af_holiday_event_data']=events['native_directory']['code']['symbols']['af_holiday_event_data']
    bindings['af_v3_npc_extras']=npc['code']['symbols']['af_v3_npc_extras']
    bindings['af_holiday_dialogue_data']=npc['dialogue']['code']['symbols']['af_holiday_dialogue_data']
    code,compiled=compile_part('holiday_calendar',directory/'code',defines=('AF_DIARY_HOLIDAYS=1',),
        extra_sources=('overlays/v3/holiday_diary.c','overlays/v3/holiday_events.c',
            'overlays/v3/diary_events.c','overlays/v3/diary_native.c',str((directory/'data.c').relative_to(ROOT))),
        link_symbols=bindings)
    context=u32(code,compiled['symbols']['af_diary_native_context_bytes']-start)
    if context>0x6F0:raise ValueError('Expanded calendar cache exceeds existing native state')
    return code,dict(format='AFV3-HOLIDAY-CALENDAR-1',code=compiled,contract=contract,
        ram=start,context_bytes=context,installed=False,choice_exposed=False,
        actor_admission_bound=False,native_execution_verified=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})


def install(base,prior,blob,core,output):
    del blob
    from v3_console_disk_install import reservations
    from v3_submenu_tables import Owner
    from v3_campsite_manager import VROM,RELOC,RAM as MANAGER_RAM
    code,report=prepare(base,prior,output)
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];events=npc['events']
    old=events['sky']['packet'];start=report['ram'];symbols=report['code']['symbols']
    extra=code+b'AFHC'*4
    if start+len(extra)>0x807DA800 or any(a<start+len(extra) and start<b for a,b in reservations(prior)):
        raise ValueError('Calendar module overlaps retained resident data')
    # Redirect stable entry points inside their checked, startup-loaded owners.
    # The original UI graphics, allocation, and entire prior code stay retained.
    packets={};redirects=[]
    def redirect(packet,address,target):
        record=packets.setdefault(packet['id'],[copy.deepcopy(packet),bytearray(
            base[packet['physical']:packet['physical']+packet['bytes']])])
        p,data=record
        if sha256(base[p['physical']:p['physical']+p['bytes']])!=p['sha256']:
            raise ValueError('Changed public-entry owner')
        offset=address-p['ram'];after=struct.pack('>2I',jump(target),0)
        if not 0<=offset<=len(data)-8:raise ValueError('Calendar redirect outside loaded owner')
        before=bytes(data[offset:offset+8]);data[offset:offset+8]=after
        redirects.append(dict(packet=p['id'],address=address,target=target,before=before.hex(),after=after.hex()))
    diary=e['diaries'];ui=diary['ui_compiled']['symbols']
    for name in ('af_diary_native_selected','af_diary_native_open','af_diary_native_visit',
            'af_diary_native_live_player','af_diary_native_attend'):
        redirect(diary['packets']['ui'],ui[name],symbols[name])
    redirect(npc['packet'],events['native_directory']['code']['symbols']['af_holiday_native_schedule'],
        symbols['af_holiday_calendar_schedule'])
    at=0x8007F428;before=jump(0x80034BF8,link=True);after=jump(symbols['af_holiday_calendar_copy'],link=True)
    replace_checked(core,at-CODE_RAM,struct.pack('>I',before),struct.pack('>I',after))
    observers=[]
    for lo,hi,digest,name in OBSERVERS:
        if sha256(core[lo-CODE_RAM:hi-CODE_RAM])!=digest:
            raise ValueError('Changed complete native event observer: '+name)
        previous=bytes(core[lo-CODE_RAM:lo-CODE_RAM+8])
        replacement=struct.pack('>2I',jump(symbols[name]),0)
        core[lo-CODE_RAM:lo-CODE_RAM+8]=replacement
        observers.append(dict(address=lo,target=symbols[name],before=previous.hex(),
            after=replacement.hex(),function_bytes=hi-lo,function_sha256=digest))
    files=by_vrom(base)
    manager=Owner(files[VROM].extract(base),files[RELOC].extract(base),MANAGER_RAM)
    manager.patch(0x80961308,jump(0x8007FD40,link=True),jump(symbols['af_holiday_calendar_owner_today'],link=True))
    manager_data,manager_reloc,manager_report=manager.finish()
    prefix=base[old['physical']:old['physical']+old['bytes']]
    if sha256(prefix)!=old['sha256']:raise ValueError('Changed combined event prefix')
    combined=prefix+extra;records=copy.deepcopy(prior['physical_resources']);writes=[]
    for p,data in packets.values():
        prior_hash=p['sha256'];p.update(sha256=sha256(data),crc32=zlib.crc32(data))
        replacement={k:p[k] for k in ('id','physical','bytes','sha256')}
        records=[replacement if r['id']==p['id'] else r for r in records]
        writes.append((dict(replacement,previous_sha256=prior_hash),bytes(data)))
        if p['id']==npc['packet']['id']:npc['packet']=p
        elif p['id']==diary['packets']['ui']['id']:diary['packets']['ui']=p
        if p['id']==npc['packet']['id']:
            compiled=events['native_directory']['code']
            offset=compiled['symbols']['af_holiday_native_type']-p['ram']
        else:
            compiled=diary['ui_compiled'];offset=0
        compiled['sha256']=sha256(data[offset:offset+compiled['bytes']])
        compiled['calendar_redirects']=[r for r in redirects if r['packet']==p['id']]
    allocation=physical.grow_backwards(base,prior['physical_resources'],old['id'],combined)
    fresh={k:allocation[k] for k in ('id','physical','bytes','sha256')}
    records=[fresh if r['id']==old['id'] else r for r in records]
    packet=dict(fresh,ram=old['ram'],crc32=zlib.crc32(combined),storage='physical-ROM')
    for family in ('sky','participants','exercise'):events[family]['packet']=copy.deepcopy(packet)
    report.update(installed=True,packet=packet,previous_packet=old,redirects=redirects,
        native_copy_hook=dict(address=at,before=before,after=after),
        observers=observers,manager=manager_report,native_owner_exclusion_bound=True,
        additional_resident_bytes=len(extra),saved_format_changed=False)
    events['calendar']=report
    npc.setdefault('source_batches',[]).append(dict(installed=True,ram=start,bytes=len(extra),
        sha256=sha256(extra),category='shared-holiday-calendar'))
    npc['sources'].update(report['sources'])
    write_new(output/'holiday-calendar/installed.json',(json.dumps(report,indent=2)+'\n').encode())
    manager_state=copy.deepcopy(prior['campsite_manager'])
    manager_state.update(output_sha256=sha256(manager_data),calendar_admission=manager_report)
    return e,{VROM:manager_data,RELOC:manager_reloc},dict(physical_resources=records,
        campsite_manager=manager_state),writes+[(allocation,combined)]
