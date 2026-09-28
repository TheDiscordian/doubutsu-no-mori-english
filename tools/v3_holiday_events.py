"""Shared source calendar/owner conversion for the connected diary category."""
import copy
import json
import re
import struct
import zlib

from aflib import sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source
from v3_npc_registry import RAM,SIZE
from v3_campsite_event import SCHEDULE_SHA
import v3_physical_resources as physical

TYPES=set(range(80,108))|{1,4,5,11,12,13,14,15,16,20,35,37,41,43,56,64}
FUNCTIONS=(
    ('m_weekday2day',0x2B1BC,344,'dbed638cc52c5bd43b86e1c4316401e8eca466bf5edc8d4a64b448fd9844171f'),
    ('decode_date',0x2CB40,336,'e8cba4776b46a72f08f6b7ca82e0048720c7f5e812bc993b82c962285838d9a8'),
    ('update_soncho_event',0x2C2D4,192,'d06a87b2164fccf9baad685a744dc1ff1cc989fca38f77dc7a25471682c44b30'),
    ('update_soncho_event2',0x2C394,116,'40136c03dc2cca7c6852769f6855abfe129404f2fef8350da7aa010e4cf64799'),
    ('update_sports_fair',0x2C408,400,'822b46cbbf2da305f3082a933814665b4b652a20961754e082cce677e0f63811'),
    ('mSC_get_soncho_event',0x7BF98,220,'51d71d1d81eb50129dceea0df9452db139251bcf8d2c48a21049656e4fab0bce'),
    ('mSC_get_soncho_field_event',0x7C074,108,'e9ab65d6ddde891e68ef4034ad680acb62043d3ac201f28adb47806d225ea79e'),
    ('mSC_delete_soncho',0x7C0E0,340,'20e51f598078bf41dd114e89078fd4741f82cd1b64fe09acb00bdafcb5563286'),
    ('add_event_today',0x2B514,372,'3e38d0778016748b6636661620e864efd7bacd446cf180617f97bd147a478df6'),
    ('check_date_range',0x2AFE0,80,'05436a7e4a80b26c6e54a79b178a5f41f7f493e4573570de5acfd2cf376fcfe7'),
    ('soncho_start',728220,132,'0d94a96acdc73a977bd2e31e8a4010e6b214c3e7c9f15f062759b27d1688bc7a'),
    ('soncho_stop',728352,84,'957ceae88c79502fbc7510bbd251f82dedae56f184d370019ff1fafbc3b6b047'),
    ('soncho_in',728436,64,'65db757d7bd971278c9306c1235e30c8f58ec919643363ba8fa2c8c291985550'),
    ('sonchohalloween_start',728500,132,'ff36e64a6f46e1ed20fd93785c8ceaa43f4edae68980e1af576a55c781273f88'),
    ('sonchowandar_start',728632,132,'a113b6aa977bc8d14faa7c913834e37e953073886654ec422582619afeaa108f'),
    ('sonchowandar_stop',728764,100,'459571fdb6dc628fdd1e05b71ffee226a8edf13e128c3b0595889e57fa68194d'),
    ('sonchowandar_in',728864,64,'3b80163318afa888bd751b93df44f1ee2a715accbd47f47e6a67574908fc11b0'),
    ('event_at_oclock',728928,276,'99c25195be1e2b430c4c5e568fd7546a284a36a3cc1ff42735e715d890f493fa'),
    ('event_at_wade',729204,392,'4ed0811bd3703def68cfa1f78d08359a770bcab90110a626928010e2b513d263'),
)
SOURCES=('tools/v3_holiday_events.py','overlays/v3/holiday_events.c',
    'overlays/v3/holiday_events.h','overlays/v3/holiday_events.ld',
    'tools/v3_holiday_world.py','tools/v3_asset_loader.py')


def discover(source):
    schedule=source.raw('event_schedule_data')
    if len(schedule)!=1608 or sha256(schedule)!=SCHEDULE_SHA:
        raise ValueError('Changed complete source holiday schedule')
    functions=[]
    for name,at,n,digest in FUNCTIONS:
        code,receipt=source.function(at)
        if (len(code)!=n or sha256(code)!=digest or
                not re.search(r'^'+name+rf' = .text:0x{at:08X};',source.symbols,re.M|re.I)):
            raise ValueError('Changed complete event function: '+name)
        functions.append(dict(name=name,**receipt))
    rows=[dict(source_index=i//12,type=int.from_bytes(schedule[i+10:i+12],'big'),hex=schedule[i:i+12].hex())
        for i in range(0,len(schedule),12) if int.from_bytes(schedule[i+10:i+12],'big') in TYPES]
    if len(rows)!=49 or {r['type'] for r in rows}!=TYPES:
        raise ValueError('Incomplete connected holiday schedule')
    for row in rows:
        raw=bytes.fromhex(row['hex'])
        if raw[2] or raw[6] or raw[8:10]!=b'\0\0' or any(raw[i]&0x10 for i in (0,4)) or any(raw[i]&0x20 for i in (3,7)):
            raise ValueError('Unbound holiday saved-date dependency')
    table=source.raw('event_table')
    if sha256(table)!='a166d30f03dd45dfe223f04c1dfe8c3ccf6c6bad27731cebe2f79cd285e49136':
        raise ValueError('Changed holiday actor priority table')
    control=source.raw('schedule_event');at,n=source.symbol('schedule_event')
    if sha256(control)!='557830a3d7f0022201a9b96b2554373d37e3d9bacd231ebe7fccf86dd82bd1e5':
        raise ValueError('Changed source event-manager directory')
    names={int(v,16):k for k,v in re.findall(r'^(\w+) = .text:0x([0-9A-Fa-f]+);',source.symbols,re.M)}
    owners=[]
    for offset in range(0,n,32):
        event=int.from_bytes(control[offset:offset+4],'big')
        if event not in TYPES:continue
        callbacks=[];targets=[]
        for slot in (4,8,12,16,20):
            binding=source.relocations.get(at+offset+slot)
            if binding:
                if binding[:3]!=(1,True,1) or binding[3] not in names:
                    raise ValueError('Unresolved holiday owner callback')
                callbacks.append(names[binding[3]]);targets.append(binding[3])
            else:
                if any(control[offset+slot:offset+slot+4]):raise ValueError('Unrelocated owner callback')
                callbacks.append(None);targets.append(None)
        kind={None:0,'soncho_start':1,'sonchowandar_start':2,'sonchohalloween_start':3}.get(callbacks[0],4)
        if kind in (1,2,3):
            expected=['sonchowandar_start','sonchowandar_stop','sonchowandar_in','wait_culling',None] if kind==2 else [
                'sonchohalloween_start' if kind==3 else 'soncho_start','soncho_stop','soncho_in','wait_culling',None]
            if callbacks!=expected:raise ValueError('Changed complete shared holiday owner')
        elif kind==0 and any(callbacks):raise ValueError('Unexpected partial shared owner')
        owners.append(dict(type=event,kind=kind,callbacks=callbacks,targets=targets))
    if len(owners)!=44 or {o['type'] for o in owners}!=TYPES:
        raise ValueError('Incomplete holiday ownership directory')
    return dict(format='AFV3-HOLIDAY-EVENTS-1',rows=rows,owners=owners,priority=list(table),
        functions=functions,source_schedule_sha256=sha256(schedule),source_owners_sha256=sha256(control),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        native_adapter_bound=False,actor_active=False)


def encode(contract):
    data=bytearray(struct.pack('>4s6H',b'AFHE',1,49,44,12,4,0))
    data.extend(bytes(contract['priority'])+bytes(4))
    for row in contract['rows']:data.extend(bytes.fromhex(row['hex']))
    for owner in contract['owners']:
        mask=sum(1<<i for i,callback in enumerate(owner['callbacks']) if callback)
        data.extend(bytes((owner['type'],owner['kind'],mask,0)))
    if len(data)!=812:raise ValueError('Incomplete event packet')
    return bytes(data)


def install(base,prior,blob,core,output):
    if prior['equipment_resources']['npc_extra'].get('events'):
        from v3_holiday_native import install as install_native
        return install_native(base,prior,blob,core,output)
    del blob,core
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra']
    if not npc.get('world') or npc.get('events'):
        raise ValueError('Event connection requires installed world and no duplicate events')
    physical.verify(base,prior['physical_resources'])
    packet=npc['packet'];data=bytearray(base[packet['physical']:packet['physical']+SIZE])
    if (len(data)!=SIZE or sha256(data)!=packet['sha256'] or
            0x4000+npc['world']['code']['bytes']>0x7400 or any(data[0x7400:0xA000])):
        raise ValueError('Changed holiday event reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    contract=discover(source);event_data=encode(contract)
    available=npc['world']['code']['symbols']
    bindings={name:available[name] for name in ('af_diary_days','af_diary_weekday')}
    directory=output/'holiday-events'
    code,compiled=compile_part('holiday_events',directory/'code',link_symbols=bindings)
    if len(code)>0x2400 or len(event_data)>0x800:raise ValueError('Holiday events exceed existing packet')
    data[0x7400:0x7400+len(code)]=code;data[0x9800:0x9800+len(event_data)]=event_data
    replacement=next(copy.deepcopy(r) for r in prior['physical_resources'] if r['id']==packet['id'])
    previous=packet['sha256'];replacement['sha256']=sha256(data)
    records=[replacement if r['id']==replacement['id'] else copy.deepcopy(r) for r in prior['physical_resources']]
    packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    npc['events']=dict(contract=contract,code=compiled,bindings=bindings,installed=True,
        data=dict(offset=0x9800,ram=RAM+0x9800,bytes=len(event_data),sha256=sha256(event_data)),
        native_adapter_bound=False,actor_active=False,additional_resident_bytes=0,
        saved_format_changed=False,native_execution_verified=False)
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(directory/'events.json',(json.dumps(npc['events'],indent=2)+'\n').encode())
    write_new(directory/'events.bin',event_data);write_new(directory/'packet.bin',data)
    return equipment,{},dict(physical_resources=records),[(dict(replacement,previous_sha256=previous),bytes(data))]
