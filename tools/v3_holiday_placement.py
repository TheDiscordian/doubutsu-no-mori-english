"""Bind donor holiday placement to actual native field and NPC services."""
import copy
import json
import re
import struct
from types import SimpleNamespace
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT,compile_part
from v3_campsite_manager import RAM as OWNER,VROM,RELOC,METADATA,CONTROL_COUNT,CONTROL_POINTERS
from v3_furniture_pipeline import Source
from v3_npc_registry import RAM,SIZE
from v3_import_storage import replace_checked
from v3_registry import SPECIAL_NPCS,SPECIAL_NPC_REGISTRY_VERSION
import v3_physical_resources as physical

ADDRESS=0x806F1C00
OWNER_CODE,KEEP,NAMES=0x806EC900,0x806F1B80,0x806F1B88
FUNCTIONS=(
    ('search_select_unit_cancel_check',0xAA94C,244,'24288b6a2d964f7cc67d340093c5a24a4c8e35d0b7ee6583a7d16976e0b02cfb'),
    ('search_free_unit_cancel_check',0xAAA40,300,'cd16e748518f014988f3c3698e1113ca5f7f3dd5c24980e033f8e48982c57b27'),
    ('search_free_unit',0xAAB6C,320,'b36120dbc5981ddf143a6edae1a3537bdb8b491827329ee6e206f4efbc81deaa'),
    ('search_select_unit',0xAACAC,208,'ae55d32ff7280921caba4234184aa3157d37a6bc906a5d8e0bf3e1c6f5166cbb'),
    ('make_actor_in_free_block',0xABDEC,248,'8d9affc7982df8b3fd288ba0bb5cac11b3546d861fa2727a0628c492ddf994a3'),
    ('make_actor_in_select_block',0xABEE4,244,'9fca0ddf922e5b19d20311f807aa0c049778f0f449dbdfd6b87a719004d6d200'),
    ('show_actor_at_wade_checkfgcol',0xACB24,436,'a450540f39da0edefc0cf09516f6071735a6eaf5d8bccf02d613a04e4b1add10'),
    ('mNpc_CheckNpcSet_height',0x62FF8,168,'620359ee79bb60ab48594070853ddf554cddc10468a225a13738943319290a15'),
    ('mNpc_GetMakeUtNuminBlock33',0x630A0,280,'a36f566a190eee981264d24373f217079807c7b113326b0825c1858963570831'),
    ('wait_culling',0xADC58,48,'512f5b15c608f8b5bb861ca7ed4da62bfc93ca4be924c3d38d9f4cef7734d95f'),
    ('get_forward_block',0xA92F8,188,'4adec4404857c710c6d95b13ae689c66509f6216dc7565347e8ab29329038801'),
    ('be_flat_unit',0xAAFE0,308,'8661fd90f5492654ed440c75895ddf2f544161153388c037a6c7b3f94304575a'),
    ('mCoBG_ExistHeightGap_KeepAndNow',0x20928,80,'5393cd7ff7d3ebdcc1aa1f8d1a123b707d754678f1711675d1e0e5338dc1f1b5'),
)
CORE_GUARDS=(
    (0x80072BE8,0x80072CC4,'dc75e149459ba9c1313a295e6a58a32fc8c03e410bc55df0aae7c770fe2a93b1'),
    (0x8008114C,0x80081360,'a2017ac5eacfc79550ba0181a472d3701b2fe139e7620ebcab17cab8297f26db'),
    (0x80088BFC,0x80088C74,'3beea0903cd1ef9ff4cabf6c8e70ba6ef918892e712e2fe3b5c6c1bb3384fea4'),
    (0x80088F94,0x80089054,'3064cf8a9a82f60ed9e31fac6e5c99463234d97bc80842863bac110b3725944e'),
    (0x800ADC8C,0x800ADD20,'eb654e519600fb5e452e1df13eb64b50a449fc89a816dbda4a93cfe71faa89dc'),
    (0x800AE110,0x800AE140,'178a257899573e62d83d4ad6539b35a5ca203ec07937ad7f09fc0ec234b59da8'),
    (0x80080C68,0x80080D68,'d7a0eefd1171cb5bfdb8a006f21ccae4c4eff525224a56f070bdaa1a5e607ccc'),
    (0x80080D68,0x80080F0C,'1dd70446e8ed063f0d3a554ea1d7f43ee98a5d1313feffcee17bd8bb95bb5c94'),
)
OWNER_GUARDS=(
    (0x8095B8B0,0x8095B96C,'d2d9a6857f4a85bf7b9c0be2aa3b1a1c5509d3ecb8364bf616678ff0bba0d549'),
    (0x8095C6C8,0x8095C994,'3ee103af185db35b16376f4eb892614254f4ad17fa708db9c28b622a6a2ac0f9'),
    (0x8095CC88,0x8095CD98,'ed2a75754677295fbed172c264b4fd0b8da444a00ec01d1e673602f027611cbf'),
    (0x8095D608,0x8095D6F4,'e5443595adb84c8ca1d512b4552710deb7fae23f41ac335e2cbf7a523f491482'),
    (0x8095DDE8,0x8095DFF0,'571a71591b022e61e78838f04d686fff48659e851e15eaf81d2749b6ba64d853'),
    (0x8095EDE4,0x8095EE1C,'f21ba8a15429534501dacae3290cfb3796bc299a0d8dda843320ba517cab4edd'),
    (0x80961768,0x809618A4,'ccefd6f339bbfad84da3612dd7e708a992e2aa5eb771fe168832ab8e96637e3a'),
)
BINDINGS=dict(
    af_holiday_manager_descriptor=0x80101310,af_holiday_native_rtc=0x80136FBC,
    af_holiday_native_clip=0x80136EEC,af_holiday_native_game=0x8011EF90,
    af_holiday_native_field_id=0x80087C88,af_holiday_native_bg_busy=0x80088F94,
    af_holiday_native_other=0x8008114C,af_holiday_native_unit=0x800AE110,
    af_holiday_native_collision=0x80089538,af_holiday_native_foreground=0x8008A33C,
    af_holiday_native_fg_allowed=0x800ADBE4,af_holiday_native_position=0x80088BFC,
    af_holiday_native_height_gap=0x80072C60,af_holiday_native_get_place=0x80080D68,
    af_holiday_native_reserve_place=0x80080C68,af_holiday_native_set_status=0x8007FDA8,
    af_holiday_native_check_status=0x8007FF08,af_holiday_event_data=RAM+0x9800)
SOURCES=('tools/v3_holiday_placement.py','overlays/v3/holiday_placement.h',
    'overlays/v3/holiday_placement.c','overlays/v3/holiday_placement_native.c',
    'overlays/v3/holiday_placement.ld','overlays/v3/holiday_owner.c','overlays/v3/holiday_owner.h',
    'overlays/v3/holiday_owner.ld','tools/v3_holiday_native.py','tools/v3_asset_loader.py',
    'tools/v3_furniture_install.py','tools/v3_registry.py','overlays/v3/holiday_observers.h',
    'overlays/v3/holiday_observers.c','overlays/v3/holiday_observers_native.c')

OBSERVER_GUARDS=(
    (0x8008E8E0,0x8008E9C4,'463b3e1be9378d1d109589fef6802e392a11a098648945ead553aee15f098e70'),
    (0x8008033C,0x800804AC,'e3f773780ce82da3b43a46975c07e1c0c37815fbc95bca00f3b00ce8869adec3'),
    (0x80058460,0x800584AC,'27b66e9064b9e9d3efdb4cabe6d1b0e787845ab758a9f765c8767b46d4e1b6b2'),
    (0x800567E8,0x80056800,'d0772f05c1eea44df9220576f516b75782baa311d11196db4f5867de06305647'),
)


def observer_contract(source,base):
    from v3_holiday_actor import REFERENCES as actor_references
    from v3_holiday_talk import REFERENCES as talk_references
    references={**actor_references,**talk_references}
    for path,digest in references.items():
        if sha256((ROOT/'local/ac-decomp'/path).read_bytes())!=digest:
            raise ValueError('Changed complete holiday observation reference: '+path)
    functions=[]
    for name,at,size,digest in (
        ('mFI_SetOyasiroPos',0x3AE58,236,'e134515a898734c793f753a91184db5d8bf4e0f38eb6d620a5dded30b5c9ad1e'),
        ('aES2_look_runner',0x1B4F30,104,'1e9c5d955fc19e42fe7c171213b73fdef0f090dfc8f7d14f104cca90cdf47674'),
        ('aES2_talk_end_chk',0x1B4CAC,172,'041d802ef8313165f280198b76e8ec5fc472612439338d85c1926fa9168b6bc8')):
        code,row=source.function(at)
        if row['symbol']!=name or len(code)!=size or sha256(code)!=digest:
            raise ValueError('Changed complete holiday observation: '+name)
        functions.append(row)
    files=by_vrom(base);core=files[CODE_VROM].extract(base);npc=files[0x8681F0].extract(base)
    for lo,hi,digest in OBSERVER_GUARDS:
        if sha256(core[lo-CODE_RAM:hi-CODE_RAM])!=digest:
            raise ValueError(f'Changed native holiday observer {lo:08X}')
    if sha256(npc[0x80980D74-0x809735B0:0x80981018-0x809735B0])!=\
            'd87ca4b8d4e1c2ffde698675544a37acb43fb3da28f4eb1b1db64a28c6636c1e':
        raise ValueError('Changed complete outdoor clip constructor')
    descriptor=struct.unpack_from('>8I',core,0x80101090-CODE_RAM)
    if descriptor!=(0x8681F0,0x878550,0x809735B0,0x80994880,0,0x8098194C,0,0):
        raise ValueError('Changed outdoor NPC overlay descriptor')
    return dict(functions=functions,references=references,native_functions=OBSERVER_GUARDS,
        native_descriptor=list(descriptor),clip_linked=0x80983A80,clip_bytes=0x11C,
        shrine_landmark_offset=0x22C,runner_donor_type=15,runner_saved_id=8,
        runner_active_flag=0x400,runner_position_offsets=[10,12],
        melody_nonzero_assignments=0,registry_version=SPECIAL_NPC_REGISTRY_VERSION,
        miko_reservation=SPECIAL_NPCS['GAFE01-r0/npc/ev-miko'],miko_actor_installed=False)


def patch_reset(core):
    """Retain the complete native common-data reset and clear additive flags.

    Inline stores are safe even before packet code is loaded. Do not jump into
    the startup-loaded packet from this early reset or assume unknown native
    common-data padding is an expandable array.
    """
    at=0x80078A10-CODE_RAM;before=bytes(core[at:at+120])
    if sha256(before)!='ffb68a5c21b6f9a85848d27fdab7cc1bd2debcf4aef607a5737309708154d6fb':
        raise ValueError('Changed complete common-data reset')
    words=(0x27BDFFE0,0x3C028013,0x904E7950,0xAFBF0014,0x3C048012,0x3C050001,
        0x34A50AB8,0x24846EA0,0x0C00BD30,0xA3AE001F,0x3C028013,0x93A9001F,
        0x24180001,0x2419FFFF,0x240800C9,0xA0596FEB,0xA0586EA0,0xAC596EA4,
        0xA4487656,0xA0497950,0x3C048012,0x3C08806F,0xAD001B80,0xAD001B84,
        0x0C023BE5,0x24846EA0,0x8FBF0014,0x03E00008,0x27BD0020,0)
    after=struct.pack('>30I',*words);replace_checked(core,at,before,after)
    return dict(address=0x80078A10,bytes=120,before_sha256=sha256(before),sha256=sha256(after),
        cleared_ram=KEEP,cleared_bytes=8,early_packet_code_call=False)


def patch_manager(base,prior,events,symbols,core):
    files=by_vrom(base);old=files[VROM].extract(base);oldrel=files[RELOC].extract(base)
    if sha256(old)!='1025b5016e5297fe5bd7c2bdf06ee147769006577f5838f81224785a3bdf5903' or sha256(oldrel)!=\
            'b2a952198cfc61dbbb72ab9da44659a9523fdabd0db4c8b14f71b81ae202bbc1':
        raise ValueError('Changed complete native-directory manager')
    report=copy.deepcopy(prior['campsite_manager']);oldtable=report['table']
    head=struct.unpack_from('>5I',oldrel);relocs=list(struct.unpack_from('>'+str(head[4])+'I',oldrel,20))
    if head[:4]!=(len(old),0,0,0) or report['control_count']!=29:
        raise ValueError('Changed native/camper directory layout')
    data=bytearray(old);table=OWNER+len(data);originals=old[oldtable-OWNER:oldtable-OWNER+29*32]
    data.extend(originals);added=[];rows=[];mapping={r['donor_type']:r['native_type'] for r in events['native_directory']['identities']}
    for index in range(29):
        for field in range(1,6):
            oldpos=oldtable-OWNER+index*32+field*4
            if struct.unpack_from('>I',old,oldpos)[0]:
                if relocs.count(0x42000000|oldpos)!=1:raise ValueError('Missing retained callback relocation')
                added.append(0x42000000|(len(old)+index*32+field*4))
    callback_names=('start','stop','in','out')
    for owner in events['contract']['owners']:
        callbacks=[]
        for i,source in enumerate(owner['callbacks']):
            if source is None:callbacks.append(0)
            elif owner['kind']==4:callbacks.append(symbols['af_holiday_owner_unbound'])
            elif i<4:callbacks.append(symbols['af_holiday_owner_'+callback_names[i]])
            else:raise ValueError('Unbound shared behind callback')
        native=mapping[owner['type']]
        data.extend(struct.pack('>8I',native,*callbacks,0,0))
        rows.append(dict(donor=owner['type'],native=native,kind=owner['kind'],callbacks=callbacks,
            dedicated_callbacks_bound=owner['kind']!=4,costume_actor_bound=owner['kind']!=3))
    if len(rows)!=44 or len(data)!=len(old)+73*32:raise ValueError('Incomplete native holiday owner set')
    hooks=[]
    for hi,lo,reg in CONTROL_POINTERS:
        for address,oldword,newword in (
            (hi,0x3C000000|reg<<16|(oldtable+0x8000)>>16,0x3C000000|reg<<16|(table+0x8000)>>16),
            (lo,0x24000000|reg<<21|reg<<16|oldtable&65535,0x24000000|reg<<21|reg<<16|table&65535)):
            replace_checked(data,address-OWNER,struct.pack('>I',oldword),struct.pack('>I',newword))
            hooks.append(dict(address=address,before=oldword,after=newword))
    replace_checked(data,CONTROL_COUNT-OWNER,struct.pack('>I',29),struct.pack('>I',73))
    hooks.append(dict(address=CONTROL_COUNT,before=29,after=73))
    relocs+=added;length=(24+len(relocs)*4+15)&~15
    reloc=(struct.pack('>5I',len(data),0,0,0,len(relocs))+struct.pack('>'+str(len(relocs))+'I',*relocs)
        +bytes(length-24-len(relocs)*4)+struct.pack('>I',length))
    if len(data)+length>0xC000 or OWNER+len(data)>0x809670B0 or VROM+len(data)>RELOC:
        raise ValueError('Holiday directory exceeds event-owner allocation')
    allowed={p for h in hooks for p in range(h['address']-OWNER,h['address']-OWNER+4)}
    for address in (0x801A0010,0x802F8010):
        a=relocate_verified_data(SimpleNamespace(ram=OWNER,resident_bytes=len(old),sections=head),old,oldrel,address)
        b=relocate_verified_data(SimpleNamespace(ram=OWNER,resident_bytes=len(data),
            sections=(len(data),0,0,0,len(relocs))),bytes(data),reloc,address)
        if any(x!=y and i not in allowed for i,(x,y) in enumerate(zip(a,b))):
            raise ValueError('Holiday owner changes unrelated relocated code')
        if b[len(old):len(old)+len(originals)]!=a[oldtable-OWNER:oldtable-OWNER+len(originals)]:
            raise ValueError('Holiday directory changes relocated native/camper callbacks')
        # All new functions are resident; they must NOT move with the owner.
        if b[len(old)+len(originals):]!=data[len(old)+len(originals):]:
            raise ValueError('Resident holiday callbacks were relocated')
    before=struct.pack('>4I',VROM,VROM+len(old),OWNER,OWNER+len(old))
    after=struct.pack('>4I',VROM,VROM+len(data),OWNER,OWNER+len(data))
    replace_checked(core,METADATA-CODE_RAM,before,after)
    sizes=[dict(vrom=vrom,previous_bytes=len(before),previous_sha256=sha256(before),bytes=len(after),sha256=sha256(after))
        for vrom,before,after in ((VROM,old,data),(RELOC,oldrel,reloc))]
    report.update(table=table,table_bytes=73*32,control_count=73,bytes=len(data),
        relocation_bytes=len(reloc),relocation_count=len(relocs),output_sha256=sha256(data),
        relocation_sha256=sha256(reloc),on_demand_growth=report['on_demand_growth']+len(data)-len(old))
    report['holiday_owners']=dict(rows=rows,hooks=hooks,retained_controls=29,
        copied_callback_relocations=len(added),all_dedicated_callbacks_bound=False,
        actor_active=False,native_execution_verified=False)
    return {VROM:bytes(data),RELOC:reloc},report,sizes


def contract(source,base):
    functions=[]
    for name,at,size,digest in FUNCTIONS:
        code,receipt=source.function(at)
        if len(code)!=size or sha256(code)!=digest or not re.search(
                r'^'+name+rf' = .text:0x{at:08X};',source.symbols,re.M|re.I):
            raise ValueError('Changed complete holiday placement function: '+name)
        functions.append(dict(name=name,**receipt))
    files=by_vrom(base);core=files[CODE_VROM].extract(base);owner=files[VROM].extract(base)
    for data,ram,ranges in ((core,CODE_RAM,CORE_GUARDS),(owner,OWNER,OWNER_GUARDS)):
        for lo,hi,digest in ranges:
            if sha256(data[lo-ram:hi-ram])!=digest:
                raise ValueError(f'Changed native holiday placement dependency {lo:08X}')
    return dict(functions=functions,core_ranges=CORE_GUARDS,owner_ranges=OWNER_GUARDS,
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        native_coordinate_order='z,x',native_landmarks=4,donor_landmarks=5,
        adaptation='N64 has no island dock; exclude its four actual landmarks.')


def install(base,prior,blob,core,output):
    del blob
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra'];events=npc['events']
    if not events.get('native_directory'):
        raise ValueError('Placement requires native directory')
    existing=events.get('placement')
    if existing and existing.get('observers'):
        raise ValueError('Current observation providers already installed')
    physical.verify(base,prior['physical_resources'])
    p=npc['packet'];data=bytearray(base[p['physical']:p['physical']+SIZE]);offset=ADDRESS-RAM
    if len(data)!=SIZE or sha256(data)!=p['sha256']:
        raise ValueError('Changed holiday placement reservation')
    old_data=bytes(data)
    if existing:
        for start,stop,record in ((offset,SIZE-16,existing['code']),
                (OWNER_CODE-RAM,0x9800,existing['owner_code'])):
            end=start+record['bytes']
            if end>stop or sha256(data[start:end])!=record['sha256'] or any(data[end:stop]):
                raise ValueError('Changed installed holiday code or free tail')
            data[start:end]=bytes(end-start)
        reset=existing['keep_reset'];at=reset['address']-CODE_RAM
        if (sha256(core[at:at+reset['bytes']])!=reset['sha256'] or
                data[KEEP-RAM:NAMES-RAM+4]!=bytes.fromhex('0000000000000000d0900000')):
            raise ValueError('Changed native common reset or owner identity/state')
    elif any(data[offset:SIZE-16]) or any(data[OWNER_CODE-RAM:0x9800]) or any(data[KEEP-RAM:NAMES-RAM+4]):
        raise ValueError('Occupied holiday placement reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    checked=contract(source,base);observers=observer_contract(source,base);bindings=dict(BINDINGS)
    bindings['af_holiday_native_type']=events['native_directory']['code']['symbols']['af_holiday_native_type']
    bindings['af_holiday_event_owner']=events['code']['symbols']['af_holiday_event_owner']
    bindings.update({name:events['native_directory']['code']['symbols'][name] for name in (
        'af_holiday_native_current','af_holiday_native_field','af_holiday_native_cleanup','af_holiday_native_notify')})
    bindings.update(af_holiday_npc_descriptor=0x80101090,af_holiday_observers_shrine=0x8008E8E0,
        af_holiday_observers_save=0x8008033C,af_holiday_native_find=0x80058460,
        af_holiday_observers_delete=0x800567E8,
        af_holiday_world_resources=npc['world']['code']['symbols']['af_holiday_world_resources'])
    directory=output/'holiday-placement'
    code,compiled=compile_part('holiday_placement',directory/'code',
        extra_sources=('overlays/v3/holiday_placement_native.c','overlays/v3/holiday_observers.c',
            'overlays/v3/holiday_observers_native.c'),link_symbols=bindings,
        defines=(f"AF_HOLIDAY_MIKO_PROFILE={SPECIAL_NPCS['GAFE01-r0/npc/ev-miko']['profile']}",))
    if len(code)>SIZE-16-offset:raise ValueError('Holiday placement exceeds checked packet')
    data[offset:offset+len(code)]=code
    owner_bindings={name:compiled['symbols'][name] for name in (
        'af_holiday_placement_native_make','af_holiday_placement_native_show','af_holiday_placement_native_cull')}
    owner_bindings.update(af_holiday_native_type=bindings['af_holiday_native_type'],
        af_holiday_event_owner=bindings['af_holiday_event_owner'],af_holiday_event_data=RAM+0x9800,
        af_holiday_source_ids=events['native_directory']['identity_ram']+128,
        af_holiday_owner_keep=KEEP,af_holiday_owner_names=NAMES,
        af_holiday_native_set_status=BINDINGS['af_holiday_native_set_status'],
        af_v3_npc_extras=npc['code']['symbols']['af_v3_npc_extras'])
    owner_code,owner_compiled=compile_part('holiday_owner',directory/'owner',link_symbols=owner_bindings)
    if len(owner_code)>0x9800-(OWNER_CODE-RAM):raise ValueError('Holiday owner code exceeds packet')
    data[OWNER_CODE-RAM:OWNER_CODE-RAM+len(owner_code)]=owner_code
    struct.pack_into('>2H',data,NAMES-RAM,0xD090,0) # Costume identity is not an ordinary Tortimer alias.
    if existing:
        # Only link targets inside the refreshed code change. Preserve the real
        # manager, callback addresses/relocations, allocation, and reset hook.
        for name,value in existing['owner_code']['symbols'].items():
            if name.startswith('af_holiday_owner_') and owner_compiled['symbols'][name]!=value:
                raise ValueError('Refreshed owner moved an installed callback')
        manager=copy.deepcopy(prior['campsite_manager']);owners={};resizes=[]
        for vrom,key in ((VROM,'output_sha256'),(RELOC,'relocation_sha256')):
            if sha256(by_vrom(base)[vrom].extract(base))!=manager[key]:
                raise ValueError('Changed retained event manager')
        allowed=set(range(offset,SIZE-16))|set(range(OWNER_CODE-RAM,0x9800))
        if any(x!=y and i not in allowed for i,(x,y) in enumerate(zip(old_data,data))):
            raise ValueError('Observation refresh changes unrelated NPC packet data')
    else:
        reset=patch_reset(core)
        owners,manager,resizes=patch_manager(base,prior,events,owner_compiled['symbols'],core)
    replacement=next(copy.deepcopy(r) for r in prior['physical_resources'] if r['id']==p['id'])
    previous=p['sha256'];replacement['sha256']=sha256(data)
    records=[replacement if r['id']==replacement['id'] else copy.deepcopy(r) for r in prior['physical_resources']]
    p.update(sha256=sha256(data),crc32=zlib.crc32(data))
    events['placement']=dict(code=compiled,bindings=bindings,contract=checked,
        owner_code=owner_compiled,owner_bindings=owner_bindings,keep_reset=reset,
        installed=True,native_primitives_bound=True,owner_callbacks_bound=True,
        dedicated_callbacks_bound=False,costume_actor_bound=False,actor_active=False,
        native_execution_verified=False,saved_format_changed=False,additional_resident_bytes=0)
    events['placement']['observers']=dict(contract=observers,bind_installed=True,unregister_installed=True,
        event_world_bound=False,miko_actor_installed=False,runner_owner_installed=False,
        native_execution_verified=False)
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(directory/'placement.json',(json.dumps(events['placement'],indent=2)+'\n').encode())
    write_new(directory/'packet.bin',data)
    return equipment,owners,dict(physical_resources=records,campsite_manager=manager,
        runtime_owner_resizes=resizes),[(dict(replacement,previous_sha256=previous),bytes(data))]
