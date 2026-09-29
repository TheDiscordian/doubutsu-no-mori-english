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


def install_optional(base,prior,blob,core,output):
    """Connect optional rewards in both full controllers, retaining actor assets.

    All existing public calls reach one refreshed world/card context. Reuse the
    festival startup packet instead of adding another loader or actor installer.
    Event/diary admission is a separate remaining consumer, not implied here.
    """
    del blob,core
    from v3_console_disk_install import reservations
    from v3_holiday_participants import optional_card_source
    from v3_import_storage import jump
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];events=npc['events']
    if not events.get('festivals') or npc.get('optional_dialogue'):
        raise ValueError('Optional dialogue requires the complete installed event batch')
    records=copy.deepcopy(prior['physical_resources']);physical.verify(base,records)
    work=output/'holiday-selection';work.mkdir()
    exercise=events['exercise'];prepared=ROOT/exercise['prepared']
    if sha256((prepared/'prepared.json').read_bytes())!=exercise['prepared_sha256']:
        raise ValueError('Changed complete exercise preparation')
    # These retained generated files are the installed complete card controller
    # and its source/native layouts, not another extracted artwork preparation.
    retained={
        'cards.c':'a3bdf1b72cf55e37e279b135df88b41744aa9852c4afda5589ffdd9cf642f01c',
        'actors.h':'c1ba57b6fdaa9d11892c0b5f62a956b6d8092c2a88c86d6e55b02ca5a249603d',
        'constants.h':'1350f05590dd78b23152328d9c6a5247a6be862c0bf0e28218c9a245a5121b2c'}
    for name,digest in retained.items():
        if sha256((prepared/name).read_bytes())!=digest:
            raise ValueError('Changed retained complete exercise source: '+name)
    cards=work/'cards.c';write_new(cards,(optional_card_source((prepared/'cards.c').read_text())+
        '\n_Static_assert(FTR_START(FTR_RADIO_TEST)==0x1FCC,"Complete exercise prize identity");\n').encode())
    world=npc['variants']['modules']['world'];old=events['festivals']['packet']
    start=old['ram']+old['bytes']
    candidates={**exercise['code']['symbols'],**world['code']['symbols']}
    sources=('overlays/v3/holiday_rewards.c','overlays/v3/holiday_talk.c',
        'overlays/v3/holiday_actor.c','overlays/v3/diary_calendar.c',
        'overlays/v3/holiday_exercise_world.c',str(cards.relative_to(ROOT)))
    code,compiled=compile_part('holiday_selection',work/'code',primary_source='overlays/v3/holiday_world.c',
        extra_sources=sources,include_dirs=('overlays/v3',str(prepared.relative_to(ROOT))),
        link_symbols=dict(AF_HS_LINK_RAM=start),symbol_candidates=candidates)
    symbols=compiled['symbols'];end=start+len(code)
    if (symbols['af_hs_end']!=end or code[-16:]!=b'AFHO'*4 or
        not start<symbols['af_hs_code_end']<=symbols['af_hs_state_start']<symbols['af_hs_state_end']<end or
        any(code[symbols['af_hs_state_start']-start:symbols['af_hs_state_end']-start]) or
        any(a<end and start<b for a,b in reservations(prior))):
        raise ValueError('Optional world/card code overlaps retained state')
    prefix_packet=events['sky']['packet']
    prefix=bytearray(base[prefix_packet['physical']:prefix_packet['physical']+prefix_packet['bytes']])
    if sha256(prefix)!=prefix_packet['sha256']:raise ValueError('Changed event prefix')
    # Summer aerobics awards a radio outside the ordinary 28-event gift table.
    # The same checked profile/metadata resolver must cover that real handover.
    np=npc['packet'];npc_data=bytearray(base[np['physical']:np['physical']+np['bytes']])
    mapping,rows=destinations(base,prior,npc['world']['reward_contract'],extra_candidates=(0x1FCC,))
    old_map=npc['world']['destinations'];at=old_map['offset']
    if (sha256(npc_data)!=np['sha256'] or sha256(npc_data[at:at+old_map['bytes']])!=old_map['sha256'] or
        at+len(mapping)>0x4000 or any(npc_data[at+old_map['bytes']:at+len(mapping)])):
        raise ValueError('Expanded source reward map exceeds its existing reservation')
    npc_data[at:at+len(mapping)]=mapping
    old_map.update(bytes=len(mapping),sha256=sha256(mapping),rows=rows)
    npc_previous=np['sha256'];np.update(sha256=sha256(npc_data),crc32=zlib.crc32(npc_data))
    redirects=[]
    for owner,previous,lo in (('world',world['code'],world['ram']),
                             ('exercise',exercise['code'],exercise['loaded_code']['ram'])):
        hi=lo+previous['bytes'];at=lo-prefix_packet['ram']
        if sha256(prefix[at:at+previous['bytes']])!=previous['sha256']:
            raise ValueError('Changed complete optional-dialogue predecessor: '+owner)
        addresses=sorted(set(v for v in previous['symbols'].values() if lo<=v<hi))
        for name,address in previous['symbols'].items():
            if name not in compiled['functions'] or not lo<=address<hi:continue
            following=next((v for v in addresses if v>address),hi)
            if following-address<8:raise ValueError('Optional redirect overlaps next function: '+name)
            offset=address-prefix_packet['ram'];before=bytes(prefix[offset:offset+8])
            target=symbols[name];after=struct.pack('>2I',jump(target),0)
            prefix[offset:offset+8]=after
            redirects.append(dict(owner=owner,name=name,address=address,target=target,
                before=before.hex(),after=after.hex()))
        previous.update(sha256=sha256(prefix[at:at+previous['bytes']]),
            optional_redirects=[r for r in redirects if r['owner']==owner])
        if owner=='world':world['sha256']=previous['sha256']
        else:exercise['loaded_code']['sha256']=previous['sha256']
    required={'af_holiday_world_bind','af_holiday_world_variant','af_holiday_talk_prepare',
        'af_holiday_talk_start','af_holiday_talk_step','af_he_begin','af_he_finish',
        'af_he_item','af_he_forget','mSC_Radio_Set_Talk_Proc','mSC_Radio_Talk_Proc'}
    if not required<={r['name'] for r in redirects}:
        raise ValueError('Incomplete connected optional world/exercise redirects')
    festival=base[old['physical']:old['physical']+old['bytes']]
    if sha256(festival)!=old['sha256']:raise ValueError('Changed complete festival packet')
    combined=festival+code
    # Prefer adjacent space, retaining the same packet identity. A fragmented
    # cartridge may instead need a new complete copy; preserve the old record.
    try:allocation=physical.grow_backwards(base,records,old['id'],combined)
    except ValueError as error:
        if str(error)!='No checked adjacent space for complete physical resource growth':raise
        allocation=physical.allocate(base,records,combined,'holiday-festivals-optional-GAFE01-r0',best_fit=True)
    fresh={k:allocation[k] for k in ('id','physical','bytes','sha256')}
    if fresh['id']==old['id']:records=[fresh if r['id']==old['id'] else r for r in records]
    else:records.append(fresh)
    npc_record=next(r for r in records if r['id']==np['id']);npc_record['sha256']=np['sha256']
    packet=dict(fresh,ram=old['ram'],crc32=zlib.crc32(combined),storage='physical-ROM')
    events['festivals'].update(packet=packet,bytes=len(combined),sha256=sha256(combined),
        optional_dialogue_range=dict(ram=start,bytes=len(code),sha256=sha256(code)))
    previous=prefix_packet['sha256']
    prefix_packet.update(sha256=sha256(prefix),crc32=zlib.crc32(prefix))
    record=next(r for r in records if r['id']==prefix_packet['id']);record['sha256']=prefix_packet['sha256']
    for family in ('sky','participants','exercise','calendar'):events[family]['packet']=copy.deepcopy(prefix_packet)
    # Preserve hashes for the complete loaded ranges, not just the new code.
    for batch in (*npc.get('source_batches',[]),npc['variants']):
        at=batch['ram']-prefix_packet['ram']
        if 0<=at and at+batch['bytes']<=len(prefix):batch['sha256']=sha256(prefix[at:at+batch['bytes']])
    if 'ram' in exercise:
        at=exercise['ram']-prefix_packet['ram'];exercise['sha256']=sha256(prefix[at:at+exercise['bytes']])
    receipt=dict(format='AFV3-OPTIONAL-HOLIDAY-DIALOGUE-1',installed=True,code=compiled,
        ram=start,bytes=len(code),sha256=sha256(code),packet=copy.deepcopy(packet),
        redirects=redirects,retained_source=retained,generated_cards_sha256=sha256(cards.read_bytes()),
        additional_resident_bytes=len(code),saved_format_changed=False,
        event_admission_changed=False,native_execution_verified=False,
        ordinary_greetings=[dict(event=i,source_message=(0x3391 if i==27 else 0x3280+i*10)+(7 if i==25 else 6))
            for i in range(28)],exercise_greeting=0x3429)
    npc['optional_dialogue']=receipt
    separate=[b for b in npc['source_batches'] if b.get('packet_id')==old['id']]
    if len(separate)!=1 or any(separate[0][k]!=old[k] for k in ('ram','bytes','sha256')):
        raise ValueError('Changed complete separately loaded batch')
    separate[0].update(bytes=len(combined),sha256=sha256(combined),packet_id=packet['id'],
        optional_dialogue_range=dict(ram=start,bytes=len(code),sha256=sha256(code)))
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in (*SOURCES,
        'overlays/v3/holiday_selection.ld','overlays/v3/holiday_exercise_world.c',
        'tools/v3_holiday_participants.py')})
    write_new(work/'installed.json',(json.dumps(receipt,indent=2)+'\n').encode())
    return e,{},dict(physical_resources=records),[(allocation,combined),
        (dict(record,previous_sha256=previous),bytes(prefix)),
        (dict(npc_record,previous_sha256=npc_previous),bytes(npc_data))]


def destinations(base,prior,rewards,*,extra_candidates=()):
    """Bind all candidates, including installed inactive profiles, without promotion."""
    blob=by_vrom(base)[BLOB].extract(base)
    candidates=sorted({int(i,16) for r in rewards['rows'] for i in r['source_items']})
    if len(candidates)!=65:raise ValueError('Changed complete holiday candidate set')
    candidates=sorted(set(candidates)|set(extra_candidates))
    if len(candidates)>128:raise ValueError('Source reward map exceeds reader capacity')
    staged={r['id']:r for r in prior['staged_furniture']['rows']}
    diaries=prior['equipment_resources']['diary_items']
    size=16+len(candidates)*8
    records=[];packet=bytearray(struct.pack('>4s6H',b'AFHW',1,len(candidates),8,size,0,0))
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
    if len(packet)!=size:raise ValueError('Incomplete holiday destination packet')
    return bytes(packet),records


def install(base,prior,blob,core,output):
    if prior['equipment_resources']['npc_extra'].get('world'):
        from v3_holiday_events import install as install_events
        return install_events(base,prior,blob,core,output)
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
