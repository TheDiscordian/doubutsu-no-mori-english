"""Connect every holiday reward to the installed identity/save/inventory path.

The shared actor-service refresh uses this step after motion and dialogue. It
does not activate an event owner, enable unfinished items, or change saves.
"""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,BLOB,compile_part
from v3_furniture_pipeline import Source
from v3_holiday_rewards import discover,encode
from v3_holiday_talk import discover as talk_contract
from v3_import_storage import ROWS,ROWS_RAM,ITEMS
from v3_npc_registry import RAM,SIZE
from v3_registry import furniture_identity,diary_parent_identity
import v3_physical_resources as physical

NATIVE=(
    (0x800B83D4,0x800B8544,'3877e9aac55ee3ec6626275d2408d16f18bbaeb04033ba8654c2dccdf6a9e160'),
    (0x800B8B08,0x800B8BE4,'a0259159d38942b5c904b404c682c47189a2f89774129c1ee325ac74ac559a25'),
)
SOURCES=('tools/v3_holiday_world.py','overlays/v3/holiday_world.c',
    'overlays/v3/holiday_world.h','overlays/v3/holiday_world.ld',
    'overlays/v3/holiday_actor.c','overlays/v3/holiday_actor.h',
    'overlays/v3/holiday_talk.c','overlays/v3/holiday_talk.h',
    'overlays/v3/holiday_rewards.c','overlays/v3/holiday_rewards.h',
    'overlays/v3/diary_calendar.c','tools/v3_registry.py',
    'overlays/v3/holiday_npc.c','overlays/v3/holiday_npc.h','tools/v3_holiday_rewards.py',
    'tools/v3_holiday_dialogue.py','tools/v3_asset_loader.py',
    'tools/v3_furniture_install.py','tools/v3_resource_capacity.py')


def destinations(base,prior,rewards):
    """Bind all candidates, including installed inactive profiles, without promotion."""
    blob=by_vrom(base)[BLOB].extract(base)
    candidates=sorted({int(i,16) for r in rewards['rows'] for i in r['source_items']})
    if len(candidates)!=65:raise ValueError('Changed complete holiday candidate set')
    staged={r['id']:r for r in prior['staged_furniture']['rows']}
    diaries=prior['equipment_resources']['diary_items']
    records=[];packet=bytearray(struct.pack('>4s6H',b'AFHW',1,65,8,536,0,0))
    for donor in candidates:
        diary=0x2B00<=donor<0x2B10
        key=f'GAFE01-r0/item/{donor:04X}'
        if diary:
            style=donor-0x2B00;native=diary_parent_identity(donor);index=1087+style
            row=diaries['profiles'][style];parent=diaries['rows'][style]
            if (parent['id']!=key or parent['item_id']!=f'{native:04X}' or
                    row['parent_item_id']!=f'{native:04X}'):
                raise ValueError('Changed holiday diary parent identity')
        else:
            index,native=furniture_identity(donor);row=staged.get(key)
            if not row or row['item_id']!=f'{native:04X}':
                raise ValueError(f'Holiday reward has no complete installed profile: {key}')
        slot=index-1024;cover=0x3000+slot*4
        profile=blob[ROWS+slot*80:ROWS+(slot+1)*80]
        metadata=blob[ITEMS+slot*32:ITEMS+(slot+1)*32]
        if (row['runtime_index']!=index or row['profile_ram']!=ROWS_RAM+slot*80+8 or
                row['selected'] is not False or
                struct.unpack_from('>HHI',profile)!=(index,cover,0) or
                struct.unpack_from('>HH',metadata)!=(index,cover) or metadata[7] or
                sha256(profile)!=row['profile_record_sha256'] or
                sha256(metadata)!=row['item_record_sha256'] or
                diary and int.from_bytes(metadata[28:30],'big')!=native):
            raise ValueError('Changed installed holiday selection/metadata')
        records.append(dict(id=key,donor_item=donor,item=native,index=index,diary=diary,
            profile_ram=ROWS_RAM+slot*80,profile_sha256=sha256(profile),
            metadata_sha256=sha256(metadata),selected=False))
        packet.extend(struct.pack('>4H',donor,native,index,int(diary)))
    if len(packet)!=536:raise ValueError('Incomplete holiday destination packet')
    return bytes(packet),records


def install(base,prior,blob,core,output):
    del blob
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra']
    if not npc.get('dialogue') or npc.get('world'):
        raise ValueError('Holiday world requires installed dialogue and no duplicate world')
    physical.verify(base,prior['physical_resources'])
    packet=npc['packet'];data=bytearray(base[packet['physical']:packet['physical']+SIZE])
    if len(data)!=SIZE or sha256(data)!=packet['sha256'] or any(data[0x3A80:0xA000]):
        raise ValueError('Changed NPC packet/world reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    reward_contract=discover(source);rewards=encode(reward_contract)
    mapping,rows=destinations(base,prior,reward_contract)
    conversation=talk_contract(source)
    for start,end,digest in NATIVE:
        if sha256(core[start-CODE_RAM:end-CODE_RAM])!=digest:
            raise ValueError(f'Changed native inventory consumer {start:08X}')
    # The public native entry includes the existing wrapped-present adapter.
    # Calling the unhooked tail would lose that established shared behaviour.
    presents=equipment['wrapped_presents']['code'];files=by_vrom(base)
    prior_blob=files[BLOB].extract(base)
    at=equipment['blob_offset']+equipment['wrapped_presents']['code_offset']
    if sha256(prior_blob[at:at+presents['bytes']])!=presents['sha256']:
        raise ValueError('Changed native insertion/present adapter')
    diary=equipment['diaries']['compiled']['symbols']
    bindings={name:diary[name] for name in ('af_diary_valid','af_v3_diary_data')}
    bindings.update(af_v3_reward_flag=equipment['player_actions']['reward_state']['code']['symbols']['af_v3_reward_flag'],
        af_v3_npc_extra_owned=npc['code']['symbols']['af_v3_npc_extra_owned'])
    directory=output/'holiday-world'
    code,compiled=compile_part('holiday_world',directory/'code',link_symbols=bindings,
        extra_sources=('overlays/v3/holiday_rewards.c','overlays/v3/holiday_talk.c',
                       'overlays/v3/holiday_actor.c','overlays/v3/diary_calendar.c'))
    if len(rewards)!=370 or len(mapping)!=536 or len(code)>0x6000:
        raise ValueError('Holiday world exceeds its existing packet reservation')
    data[0x3B00:0x3B00+len(rewards)]=rewards
    data[0x3C80:0x3C80+len(mapping)]=mapping
    data[0x4000:0x4000+len(code)]=code
    replacement=next(copy.deepcopy(r) for r in prior['physical_resources'] if r['id']==packet['id'])
    previous=packet['sha256'];replacement['sha256']=sha256(data)
    records=[replacement if r['id']==replacement['id'] else copy.deepcopy(r) for r in prior['physical_resources']]
    packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    npc['world']=dict(format='AFV3-HOLIDAY-WORLD-1',installed=True,actor_active=False,
        code=compiled,bindings=bindings,reward_contract=reward_contract,conversation=conversation,
        rewards=dict(offset=0x3B00,ram=RAM+0x3B00,bytes=len(rewards),sha256=sha256(rewards)),
        destinations=dict(offset=0x3C80,ram=RAM+0x3C80,bytes=len(mapping),sha256=sha256(mapping),rows=rows),
        native_inventory=[dict(start=a,end=b,sha256=s) for a,b,s in NATIVE],
        owner_dates_required=True,lighthouse_owner_required=True,additional_resident_bytes=0,
        saved_format_changed=False,native_execution_verified=False)
    npc['pending']=['Event owner/scheduling, actual special dates/vacation state, and cleanup',
        'Separate exercise/card route','Connected native diary gameplay/save verification']
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(directory/'world.json',(json.dumps(npc['world'],indent=2)+'\n').encode())
    write_new(directory/'rewards.bin',rewards);write_new(directory/'destinations.bin',mapping)
    write_new(directory/'packet.bin',data)
    return equipment,{},dict(physical_resources=records),[(dict(replacement,previous_sha256=previous),bytes(data))]
