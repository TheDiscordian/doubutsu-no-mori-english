"""Connect hourly event state, native reset lifetime, and dedicated-owner access."""
import copy
import json
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
