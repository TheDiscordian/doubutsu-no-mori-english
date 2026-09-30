"""Shared exercise motion, command, and native player integration.

No furniture choice is enabled by installing these dependencies.
"""
import copy
import re
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_equipment_runtime import (PLAYER_CAPACITY, PLAYER_COUNT, PLAYER_FIRST,
    PLAYER_TABLE, PLAYER_VROM, PLAYER_RAM, KIND_TABLE, FACE_TABLE, FACE_DATA,
    FACE_END, player_animation_sources, player_face_sources, store_player_assets)
from v3_resource_capacity import checked_limit

SOURCES=('tools/v3_player_exercise.py','overlays/v3/player_exercise.c',
    'overlays/v3/player_exercise.h','overlays/v3/player_exercise.ld',
    'tools/v3_equipment_runtime.py','overlays/v3/equipment_resources.c')
SOURCES+=('overlays/v3/player_exercise_native.c','overlays/v3/player_exercise_native.h',
    'overlays/v3/player_exercise_native.ld','tools/v3_room_goods.py',
    'overlays/v3/surface_bootstrap.c','tools/v3_asset_loader.py',
    'tools/v3_furniture_reactions.py','tools/v3_room_rig_runtime.py','tools/v3_furniture_install.py')
NATIVE_FUNCTIONS=(
    (0x8005EAFC,0x8005EB74,'06f47a7514046f28056417d7dc9ccc4ec1a09eabb13ff21d923a251484a2c52e'),
    (0x80078D30,0x80078D78,'64caa4eba4dac0d0259e292053a2463d65322310384dd2e790a067ea10da8d77'),
    (0x8007D90C,0x8007D91C,'f36a165b7d65a6ce4b7e25d3a9cc40585f08edd0738b8c924d75b3435c70690a'),
    (0x8007FF08,0x8007FF8C,'4df1b83227b8be1d64d705375c576db58d8fe854291a29c06d57193918913064'),
    (0x80088710,0x80088780,'b210ff697057c37be97eeb9de1db4088a55ab9917f5e12d57852d081959435d8'),
    (0x80089440,0x800894D0,'07344cb8b43778bf17910045b809400f8071bdf413c65ca43e88b5311f729473'),
    (0x800EE050,0x800EE7C4,'e8ad9860db541546d85cc839a35494cd02a6c5066685d7d51b2c11a0990e9c7c'),
    (0x800F5660,0x800F6034,'22a22ddbe01bd668356b5efefaf71464ae7228a77db98d0b8900ce22103c7e72'),
    (0x800F6034,0x800F60F0,'3edbcbaacd51474aa69e5d7b2647aef43d5a4537951adba3db5bbc6960ec4058'),
    (0x800F6140,0x800F6210,'4ae11e9da8ef4b676c8dd5035a9c42770a0b97694bf6c9d09fb2f2baf19cb8b3'),
    (0x800FCAD8,0x800FCE80,'01228029d2dcd19deb2e31b3184c3273f7b6cddfc9796e556e7e70ef855adc31'),
    (0x808B2D50,0x808B2DE4,'2906967329726565873420b3c20a320ea8240c11c6b4347475ca0a3a51c8dc81'),
    (0x808B3010,0x808B30B4,'d52913c08d05bc1c438ee09353a305740977d9d7b2562121aa16f5f76eea218d'),
    (0x808B32C4,0x808B3308,'73dbca69b6bd3dca07428ae27b3d9f1238a5130e0095e2ef11603d2db0b5fc8b'),
    (0x808B3334,0x808B3370,'0d4a8b915d523b0c6bcea7e8c26cb1e38e5d4fffc98209af6d13db02081c6068'),
    (0x808B3648,0x808B36E8,'3b7d669b96713b70f8aba44f0b98d854b08ea996198cd1a149c594e2d2435e00'),
    (0x808B36F4,0x808B37D4,'17bfc9af274efd1bef2eef32b63b19bfa69482bcce99ecdcb08a03aac0bacf28'),
    (0x808B3AF0,0x808B3B08,'b77ae0ded3c1dd5a476da8bac2f471f07622d948d3481913007a1204f988489a'),
    (0x808B3BD0,0x808B3BF0,'8945e8562bd722d10343775638b56a4391be19e767c26ec9dde1c7b24352f2a7'),
    (0x808B3C74,0x808B3C94,'3e86a92e686923b0a8584f32589ec20f8b630da9d90f9090f73b19337fa16bdf'),
    (0x808B48F0,0x808B4924,'305b9f55995ea42f93fc3a36306e4adff4db3468cb793084dd14c3f48d22c4cc'),
    (0x808B4A44,0x808B4B6C,'cf4f3f502e0bc29fa474219bb116f5566cc62dcb4d764686aa3c9bcd7f169650'),
    (0x808B4DAC,0x808B4DE8,'57ee59f746b0f74a5346e1421e5e6d6b853fc70c0415df76c76cd5c16b38dab8'),
    (0x808B5310,0x808B5348,'eaa31c9678d3f5d7ab56cec33e42c99a2370caabc3fde1ce36303ed7fa8251d9'),
    (0x808B5FB0,0x808B5FFC,'a66426054251c28831b3495fb799973b208885c106ec8d17ae01851f586f49f6'),
    (0x808B61E4,0x808B6234,'2da374a85ae8adce8117b3f6a62b26dda7b3d1cb1534024f83b24acbea4c3427'),
    (0x808B8874,0x808B88D4,'d33203657dfe300f88b32a1cd4204f2a751a4c6f2b696b4d0bdb0ec19c16caef'),
    (0x808BBDE8,0x808BBE50,'647c5485d0c1bc0074aee05a9ffcf35489f5b703dbc0f79772b7bf716a1d4f8e'),
    (0x808BD218,0x808BD320,'8bdd6a968f915f0f676b61cfb5b6df602b66489800a2b7ac2b878d66c1c3df55'),
    (0x808BF410,0x808BF494,'3e5bfc3ce6ac9e6b0eacc746204209bec24b325881fcf5d49d135e60e796a55d'),
    (0x808C1064,0x808C10E4,'671817fabfe8142d2de949e4657cd3605892f00b7139015a955430059ca29811'),
    (0x808C1118,0x808C11EC,'b68e5709b312229c1fe343af2d20853448c358633c025c35da0b93697a12abdf'),
    (0x808C1370,0x808C13F0,'41ad4f959ae1e31586a4e44b768a60ddafff11f4a8d7a984ada694c873c99e14'),
)
FUNCTIONS=(
    (0x164A1C,324,'03d551b78a29ea8d1390d487e9ee3c243d4640b5f745fb09ca3a72c45ac1e026'),
    (0x16E944,240,'bcac7896bfd81416edb8e5a088a6d9d888057b237d2cfffd6a5319c12b28a914'),
    (0x16EA34,60,'cd8c2cedbbbf4b142db2c5e9fcbdb779be9ec84dd87a541348a7d7901b416172'),
    (0x16EA70,20,'dbd42b853bf3b4bdac5b86a4933ec513f9d456992a5e7c18b8576f76fa2babf6'),
    (0x16EA84,72,'39342c35f0d41993b0aee97ede38d161ae7a5816ffddefe944810d2b4e1b21fd'),
    (0x16EACC,216,'510ec4c2a7bfd2b3ed7aae6d2eff313db978a57d384549519f951cca1a42d61c'),
    (0x16EBA4,100,'d18902f41915fa3779b2aa138b7e1a0e8703576abb09e13b6b077c2ded027e36'),
    (0x16EC08,292,'8309dfdd9b2908129e15fca7bbd6237425b9d6f5537d057e86d9e64ef2861f83'),
    (0x16ED2C,284,'b2e43f1e39881f8dfa2f25bdca7f2eb15378ab780330c1a5f4f63edc49368a70'),
    (0x16EE48,48,'0cb44ded16568dc65fc6850832b52ca06e620ebd3ca21486d9823262b9cedcdf'),
    (0x175C18,56,'9b640eecf345352be40f0d761ab2c713299acd591bdfdfea223158f6882dfc5c'),
    (0x196950,128,'27e73d96d5a3b62cfc4b2b7806008038c164ebed0efaf682420cd396e5a5ea24'),
    (0x1969D0,208,'39cae77b914cd26f14bd0db443c25081cbaa76d1a7ad6d53778a4a399c3cb410'),
    (0x196AA0,4,'f332ea5b5437103cbb6f1508679da89eec9288ad775c96c439a17fccabe3de8e'),
    (0x196AA4,56,'2f5d63ff7140972bdbd2800366101f619d42d4036f574521023043ea055a19dc'),
    (0x196ADC,40,'c879be2b0d11f75a37ead26e6bb91d270e394b581135cb86ed6f2aafc9a43b85'),
    (0x196B04,328,'6f7228bb4752229d9c8751d69188c78476e8978c58c9bdc5cfbd31a5d6c2372b'),
    (0x196C4C,32,'2d0a79c52c6baae56c6c3532e24f36c6bcf5cb22b5c5af75097c048b8c742d4d'),
    (0x196C6C,32,'2f33dcc160ca754fb8d38a01f3f913adcdcbf3c3b9f8bf2a3c02b5975550bc34'),
    (0x196C8C,320,'8d558c65c6980f2cf3ff1e0f53d4ece6539e1e85dc711a2e731ef1f3191f2b23'),
    (0x196DCC,156,'411457955ee871c3132a197a77dd8c92141eaa024a13f177650edad3ca2ec9fa'),
)


def source_contract(source):
    functions={}
    for at,size,digest in FUNCTIONS:
        raw,row=source.function(at)
        if len(raw)!=size or sha256(raw)!=digest:
            raise ValueError('Changed complete exercise dependency: '+row['symbol'])
        functions[row['symbol']]=row
    raw,recognize=source.function(0x16EC08)
    base=recognize['relocations'].get(0x16)
    if (base!=(6,1,5,0x51080) or recognize['relocations'].get(0x1E)!=(4,1,5,base[3])
            or tuple(u32(raw,p) for p in (0x2C,0x30,0x38))!=(0x3B3D0224,0x3B1D026C,0x387D02B4)):
        raise ValueError('Changed exercise command-table addressing')
    tables={}
    def data(at,n,role):
        name,start,size=source.containing(at,exact=True)
        if start!=at or size!=n:raise ValueError('Incomplete exercise '+role)
        raw=source.data[at:at+n]
        tables[role]=dict(symbol=name,section=5,offset=at,bytes=n,sha256=sha256(raw),
                          pointers=source.pointers(at,n))
        return raw
    first=base[3]+0x224
    pointer_bytes=data(first,72,'commands')
    if pointer_bytes!=bytes(72) or set(source.pointers(first,72))!={first+i*4 for i in range(18)}:
        raise ValueError('Incomplete exercise command pointers')
    lengths=struct.unpack('>18I',data(base[3]+0x26C,72,'lengths'))
    following=struct.unpack('>18b',data(base[3]+0x2B4,18,'continuations'))
    _,setup=source.function(0x1969D0)
    target=setup['relocations'].get(0x5A)
    if target!=(6,1,4,0x7428) or setup['relocations'].get(0x6E)!=(4,1,4,target[3]):
        raise ValueError('Changed exercise animation selector')
    at=target[3];begin=source.sections[4][0]+at;animations=list(source.rel[begin:begin+18])
    names=re.findall(r'^(\S+) = \.rodata:0x%08X;[^\n]* size:0x([\dA-Fa-f]+) ' % at,source.symbols,re.M)
    if len(names)!=1 or int(names[0][1],16)!=18 or sorted(set(animations))!=list(range(144,156)):
        raise ValueError('Incomplete exercise animation table')
    tables['animations']=dict(symbol=names[0][0],section=4,offset=at,bytes=18,sha256=sha256(bytes(animations)))
    _,calc=source.function(0x196B04)
    target=calc['relocations'].get(0xE2)
    if target!=(6,1,5,0x513CC) or calc['relocations'].get(0xF2)!=(4,1,5,target[3]):
        raise ValueError('Changed exercise speed selector')
    speeds=struct.unpack('>18f',data(target[3],72,'speeds'));rows=[]
    pointers=source.pointers(first,72)
    for i,(n,next_index,animation,speed) in enumerate(zip(lengths,following,animations,speeds,strict=True)):
        if not 1<=n<=8 or not -1<=next_index<18 or speed not in (.25,.5):
            raise ValueError('Unsupported complete gesture record')
        keys=list(data(pointers[first+i*4],n,f'pattern_{i}'))
        if max(keys)>8 or tables[f'pattern_{i}']['pointers']:raise ValueError('Invalid exercise direction')
        rows.append(dict(keys=keys,length=n,next=next_index,source_animation=animation,
                         animation=PLAYER_FIRST+animation,speed=speed))
    return dict(functions=functions,tables=tables,patterns=rows,
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        input_adaptation='N64 C-button directions and diagonals replace the GameCube C-stick',
        runtime_installed=False)


def pattern_bytes(contract):
    return b''.join(struct.pack('>8bBbHf',*(r['keys']+[-1]*(8-r['length'])),
        r['length'],r['next'],r['animation'],r['speed']) for r in contract['patterns'])


def motions(source,contract):
    # Preparation allows complete larger motions; installation grows the actual
    # bank and containing scene arena before publishing any larger record.
    return player_animation_sources(source,[r['source_animation'] for r in contract['patterns']],capacity=65520)


def grow_animation_banks(original,base,prior,core,capacity):
    native=by_vrom(original)[CODE_VROM].extract(original);files=by_vrom(base)
    if not PLAYER_CAPACITY<capacity<32768 or capacity%16:
        raise ValueError('Invalid complete animation-bank capacity')
    maximum=bytes(core[0x800B11F8-CODE_RAM:0x800B1264-CODE_RAM])
    if (maximum!=native[0x800B11F8-CODE_RAM:0x800B1264-CODE_RAM] or
            sha256(maximum)!='f0f0ebf4c4a74deba763b3cf33a385f55b7f02b772dde7a88ceda2d4707d3dd0' or
            core[0x8010BF2C-CODE_RAM:0x8010BF30-CODE_RAM]!=bytes(4)):
        raise ValueError('Changed complete native animation maximum/cache')
    evidence=[]
    for start,end in ((0x800B1838,0x800B1944),(0x800C5C30,0x800C5CC4),(0x800B1D94,0x800B1DE8)):
        raw=bytes(core[start-CODE_RAM:end-CODE_RAM])
        if raw!=native[start-CODE_RAM:end-CODE_RAM]:raise ValueError('Changed animation allocation/transfer consumer')
        evidence.append(dict(start=start,end=end,sha256=sha256(raw)))
    owner=files[PLAYER_VROM].extract(base);old_owner=by_vrom(original)[PLAYER_VROM].extract(original)
    at=0x808B46C4-PLAYER_RAM;end=0x808B47F8-PLAYER_RAM
    if owner[at:end]!=old_owner[at:end]:raise ValueError('Changed complete player animation cache-copy consumer')
    # The two real banks are registered by the two calls in mSc's player loader.
    if any(u32(core,p-CODE_RAM)!=0x0C02C643 for p in (0x800C5C48,0x800C5C50)):
        raise ValueError('Changed two-bank animation registration')
    previous_arena=prior['equipment_resources']['animated_rigs']['allocation']['scene_arena_bytes']
    growth=2*(capacity-((PLAYER_CAPACITY+15)&~15));arena=previous_arena+growth
    if arena>>16!=9:raise ValueError('Animation arena exceeds checked immediate pair')
    patches=[]
    for address,before,after in (
            (0x800B121C,0x24120082,0x24120000|PLAYER_FIRST+PLAYER_COUNT),
            (0x800C6618,0x34A50000|(previous_arena&65535),0x34A50000|(arena&65535)),
            (0x800C6628,0x34210000|(previous_arena&65535),0x34210000|(arena&65535))):
        offset=address-CODE_RAM
        if u32(core,offset)!=before:raise ValueError('Changed animation bank/arena patch')
        struct.pack_into('>I',core,offset,after)
        patches.append(dict(address=address,before=f'{before:08x}',after=f'{after:08x}'))
    return dict(previous_bank_bytes=PLAYER_CAPACITY,bank_bytes=capacity,banks=2,
        additional_scene_bytes=growth,previous_scene_arena_bytes=previous_arena,scene_arena_bytes=arena,
        maximum_entry=0x800B11F8,maximum_source_sha256=sha256(maximum),patches=patches,
        native_consumers=evidence,copy_consumer_sha256=sha256(owner[at:end]),
        native_execution_tested=False,saved_format_changed=False)


def install_resources(base,prior,blob,core,original,output):
    from v3_furniture_pipeline import Source
    old=prior['equipment_resources'];start=old['blob_offset'];module=bytearray(blob[start:start+old['bytes']])
    motion=old['player_motion'];source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if (sha256(module)!=old['sha256'] or motion.get('exercise') or not motion.get('faces')
            or not old['room_rigs'].get('music',{}).get('installed')):
        raise ValueError('Exercise resources require complete installed music/player dependencies')
    contract=source_contract(source);assets,rows,evidence=motions(source,contract)
    if {r['source_index'] for r in rows}&{r['source_index'] for r in motion['records']}:
        raise ValueError('Exercise would overwrite an existing animation')
    capacity=max(PLAYER_CAPACITY,*(r['bytes'] for r in rows),*(r['bytes'] for r in motion['records']))
    allocation=grow_animation_banks(original,base,prior,core,capacity)
    limit=checked_limit(base,prior)
    storage=store_player_assets(base,old,blob,core,assets,rows,limit=limit)
    report=copy.deepcopy(old);new_motion=report['player_motion'];new_motion['records']+=rows
    new_motion['records'].sort(key=lambda r:r['source_index'])
    for row in rows:
        at=PLAYER_TABLE+16+row['source_index']*16
        if any(module[at:at+16]):raise ValueError('Exercise motion slot is occupied')
        struct.pack_into('>4I',module,at,row['vrom'],row['bytes'],row['pointer'],row['type'])
    # Validate the installed face data before expanding its complete source table.
    previous_table,previous_data,_=player_face_sources(source,motion['records'])
    if (module[FACE_TABLE:FACE_TABLE+len(previous_table)]!=previous_table or
            module[FACE_DATA:FACE_DATA+len(previous_data)]!=previous_data):
        raise ValueError('Changed installed face timelines')
    table,data,faces=player_face_sources(source,new_motion['records'])
    if len(data)>len(previous_data) and any(module[FACE_DATA+len(previous_data):FACE_DATA+len(data)]):
        raise ValueError('Expanded face timelines would overwrite another runtime')
    module[FACE_TABLE:FACE_TABLE+len(table)]=table
    module[FACE_DATA:FACE_DATA+len(data)]=data
    new_motion['faces'].update(faces)
    flags=tuple(f[2:] for f in old['code']['flags'] if f.startswith('-D'))
    flags+=(f'AF_V3_PLAYER_CAPACITY={capacity}u',f'AF_V3_PLAYER_RESOURCE_END=0x{limit:X}u')
    code,compiled=compile_part('equipment_resources',output/'equipment_resources',defines=flags,
        extra_sources=('overlays/v3/equipment_resources.S',))
    if (len(code)>KIND_TABLE or compiled['symbols']!=old['code']['symbols'] or
            len(code)!=old['code']['bytes'] or sha256(module[:len(code)])!=old['code']['sha256']):
        raise ValueError('Exercise resource reader moves installed entry points')
    module[:KIND_TABLE]=code+bytes(KIND_TABLE-len(code))
    prepared,prepared_code=compile_part('player_exercise',output/'player_exercise')
    new_motion.update(animation_buffer_bytes_changed=True,allocation=allocation)
    new_motion['exercise']=dict(source=contract,motion_source=evidence,records=rows,storage=storage,
        animation_bytes=sum(map(len,assets.values())),pattern_hex=pattern_bytes(contract).hex(),
        prepared_core=prepared_code,prepared_core_installed=False,action_installed=False,
        saved_format_changed=False)
    blob[start:start+len(module)]=module
    report.update(code=compiled,sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    return report,{}


def native_contract(core,owner):
    functions=[]
    for address,end,digest in NATIVE_FUNCTIONS:
        data,origin=(owner,PLAYER_RAM) if address>=PLAYER_RAM else (core,CODE_RAM)
        raw=data[address-origin:end-origin]
        if sha256(raw)!=digest:raise ValueError(f'Changed complete exercise native dependency {address:08X}')
        functions.append(dict(address=address,end=end,sha256=digest))
    calendars=[]
    for address,expected,donor,native in (
            (0x80104D64,'07190086081f008600000010',35,16),
            (0x80104E24,'0a9100090a91000a00000008',13,8)):
        if core[address-CODE_RAM:address-CODE_RAM+12].hex()!=expected:
            raise ValueError('Changed native aerobics calendar identity')
        calendars.append(dict(address=address,hex=expected,source_event=donor,native_event=native))
    return dict(functions=functions,event_calendars=calendars,field_type=0x80136EA1,
        audio=dict(context=0x801494E0,clock=0x8014BDA0,handle=0x80113848,
            group_count=0x8014BD60,groups=0x8014CB90,stride=0x160,sequence_offset=4,
            tempo_offset=8,tempo_divisor=48,sequence=181),
        source_steps_per_update=2,physics_steps_per_update=1,
        source_event_first_condition_retained=True,saved_format_changed=False)


def checked_native(image,report):
    equipment=report['equipment_resources'];exercise=equipment.get('player_motion',{}).get('exercise',{})
    if not exercise.get('action_installed'):return False
    native=exercise['native'];packet=native['packet'];files=by_vrom(image)
    blob=files[BLOB].extract(image);core=files[CODE_VROM].extract(image);owner=files[PLAYER_VROM].extract(image)
    events=equipment.get('npc_extra',{}).get('events',{})
    calendar=events.get('calendar',{})
    if calendar.get('installed'):
        core=bytearray(core)
        observer=next(r for r in calendar['observers'] if r['address']==0x8007FF08)
        target=calendar['code']['symbols']['af_holiday_calendar_status']
        p=calendar['packet'];at=observer['address']-CODE_RAM
        after=struct.pack('>2I',0x08000000|(target>>2 & 0x3FFFFFF),0)
        if (observer['target']!=target or observer['after']!=after.hex() or
                core[at:at+8]!=after or observer['before']!='afa5000400052c00' or
                sha256(image[p['physical']:p['physical']+p['bytes']])!=p['sha256']):
            raise ValueError('Changed exercise shared-calendar observer')
        core[at:at+8]=bytes.fromhex(observer['before'])
        if sha256(core[at:at+132])!=observer['function_sha256']:
            raise ValueError('Changed complete exercise calendar dependency')
        directory=events['native_directory'];days=directory['days_ram']
        for address,before,after in ((0x8007FF20,0x3C0F8014,0x3C0F0000|((days+32768)>>16)),
                (0x8007FF24,0x25EF9F98,0x25EF0000|(days&65535))):
            patch=next(r for r in directory['core_hooks'] if r['address']==address)
            if patch['before']!=before or patch['after']!=after or u32(core,address-CODE_RAM)!=after:
                raise ValueError('Changed exercise shared event-storage pointer')
            struct.pack_into('>I',core,address-CODE_RAM,before)
    raw=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
    module=blob[equipment['blob_offset']:equipment['blob_offset']+equipment['bytes']]
    if (sha256(raw)!=packet['sha256'] or zlib.crc32(raw)!=packet['crc32'] or
            sha256(raw[:native['code']['bytes']])!=native['code']['sha256'] or
            native['binding']!=native_contract(core,owner) or
            sha256(module)!=equipment['sha256'] or not exercise['prepared_core_installed']):
        raise ValueError('Changed installed player exercise dependencies')
    if u32(core,native['player_allocation_address']-CODE_RAM)!=native['player_bytes']:
        raise ValueError('Player exercise state exceeds the actual actor allocation')
    for row in native['owner_hooks']:
        if u32(owner,row['address']-PLAYER_RAM)!=row['after']:
            raise ValueError('Missing player exercise hook')
    for row in native['callback_patches']:
        if u32(module,row['offset'])!=row['after']:raise ValueError('Missing exercise/WAIT callback')
    flags=equipment['surface_bootstrap']['code']['flags']
    for name,key in (('VROM','vrom'),('CRC','crc32'),('BYTES','bytes')):
        if f'-DAF_PLAYER_EXERCISE_{name}=0x{packet[key]:X}u' not in flags:
            raise ValueError('Missing checked player exercise preload')
    return True


def install_native(base,prior,blob,core,original,output):
    from apply_translation import write_new
    from types import SimpleNamespace
    from npc_mail_show import relocate_verified_data
    from v3_player_actions import native_references
    from v3_import_storage import jump
    from v3_room_rig_runtime import packet_layout
    from v3_furniture_pipeline import Source
    files=by_vrom(base);old=prior['equipment_resources'];start=old['blob_offset']
    module=bytearray(blob[start:start+old['bytes']]);owner=bytearray(files[PLAYER_VROM].extract(base))
    reloc=files[0x7D9BA0].extract(base);actions=old['player_actions'];exercise=old['player_motion']['exercise']
    if (sha256(module)!=old['sha256'] or sha256(owner)!=actions['owner_sha256'] or
            sha256(reloc)!=actions['relocation_sha256'] or exercise.get('action_installed') or
            not old['room_rigs']['music']['installed'] or not old.get('room_carry')):
        raise ValueError('Incomplete or changed player exercise installation input')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    contract=source_contract(source);patterns=pattern_bytes(contract)
    if patterns.hex()!=exercise['pattern_hex'] or len(exercise['records'])!=12:
        raise ValueError('Changed installed complete exercise resources')
    binding=native_contract(core,owner)
    # Separate immutable code uses the gap after reaction/colour state and before
    # the current room packet. It never borrows the occupied tool-action region.
    ram,_,_=packet_layout(old['room_rigs']);code_ram,code_end=0x804CE000,0x804D0000
    if (ram!=code_end or old['ram']+old['bytes']>0x804C0000 or
            old['room_rigs']['colours']['state']['ram']+old['room_rigs']['colours']['state']['bytes']>code_ram):
        raise ValueError('Player exercise code overlaps resident resources')
    assembly=output/'exercise-patterns.S'
    write_new(assembly,('.section .rodata\n.balign 4\n.global af_v3_exercise_patterns\n'
        'af_v3_exercise_patterns:\n.byte '+','.join(map(str,patterns))+'\n').encode())
    init=actions['balloon_actor']['code']['symbols']['af_v3_balloon_player_init']
    code,compiled=compile_part('player_exercise_native',output/'player_exercise_native',
        extra_sources=('overlays/v3/player_exercise.c',str(assembly.relative_to(ROOT))),
        defines=(f'AF_EXERCISE_PRIOR_INIT=0x{init:X}u',))
    symbols=compiled['symbols'];pattern_at=symbols['af_v3_exercise_patterns']-code_ram
    if (len(code)>code_end-code_ram or code[pattern_at:pattern_at+len(patterns)]!=patterns or
            not 0<=pattern_at<len(code)):
        raise ValueError('Incomplete compiled exercise packet')
    packet=code.ljust((len(code)+15)&~15,b'\0')
    blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(packet)
    if BLOB+len(blob)>checked_limit(base,prior):raise ValueError('Exercise packet exceeds checked resource storage')
    groups,absolute,rows,locations,slots=native_references(owner,reloc)
    patches=[];removed=set()
    def patch(address,before,after,remove=False):
        offset=address-PLAYER_RAM
        if u32(owner,offset)!=before:raise ValueError(f'Changed player exercise hook {address:08X}')
        struct.pack_into('>I',owner,offset,after)
        patches.append(dict(address=address,before=before,after=after))
        if remove:
            if offset not in slots:raise ValueError('Missing native exercise-hook relocation')
            removed.add(locations[offset])
        elif offset in slots:raise ValueError('Unexpected exercise-hook relocation')
    for address,before,name,remove in (
            (0x808DD79C,init,'init',False),
            (0x808DDBBC,0x808BD218,'after',True),
            (0x808BBE60,0x808BBDE8,'camera',True)):
        patch(address,jump(before,link=True),jump(symbols['af_v3_exercise_native_'+name],link=True),remove)
    matches=[(hi,lo) for hi,consumers in groups.items() for lo,target in consumers if target==0x808BBDE8]
    if matches!=[(0x2A958,0x2A980)] or any(v==0x808BBDE8 for v in absolute.values()):
        raise ValueError('Changed complete player camera callback references')
    target=symbols['af_v3_exercise_native_camera']
    for offset,value in ((matches[0][0],(target+0x8000)>>16),(matches[0][1],target&65535)):
        before=u32(owner,offset);patch(PLAYER_RAM+offset,before,before&0xFFFF0000|value,True)
    kept=[r for r in rows if r not in removed];new_reloc=bytearray(reloc)
    struct.pack_into('>I',new_reloc,16,len(kept))
    new_reloc[20:20+len(rows)*4]=struct.pack('>'+str(len(kept))+'I',*kept)+bytes(4*len(removed))
    sections=struct.unpack_from('>5I',reloc);changed={p['address']-PLAYER_RAM+i for p in patches for i in range(4)}
    original_owner=files[PLAYER_VROM].extract(base)
    old_spec=SimpleNamespace(ram=PLAYER_RAM,resident_bytes=sum(sections[:4]),sections=sections)
    new_spec=SimpleNamespace(ram=PLAYER_RAM,resident_bytes=sum(sections[:4]),sections=(*sections[:4],len(kept)))
    for loaded in (0x801A0010,0x802F8010,0x803B0010):
        before=relocate_verified_data(old_spec,original_owner,reloc,loaded)
        after=relocate_verified_data(new_spec,owner,new_reloc,loaded)
        if any(a!=b and i not in changed for i,(a,b) in enumerate(zip(before,after,strict=True))):
            raise ValueError('Exercise hooks change unrelated relocated player code')
        if any(u32(after,p['address']-PLAYER_RAM)!=p['after'] for p in patches):
            raise ValueError('Exercise hook was incorrectly relocated')
    report=copy.deepcopy(old);current=report['player_actions'];table_patches=[]
    callbacks={0x808BE620:0x808BE140,0x808DD874:0,0x808DD9B4:0,
        0x808DDA18:symbols['af_v3_exercise_native_setup'],0x808DDB5C:symbols['af_v3_exercise_native_main']}
    for table in current['tables']:
        if table['width']!=4:continue
        offset,size=table['offset'],table['bytes']
        if sha256(module[offset:offset+size])!=table['sha256']:raise ValueError('Changed complete player dispatch table')
        edits=[(111,0,callbacks[table['native_entry']])]
        if table['native_entry']==0x808DDA18:edits.append((7,0x808C1118,symbols['af_v3_exercise_native_wait_setup']))
        if table['native_entry']==0x808DDB5C:edits.append((7,0x808C1370,symbols['af_v3_exercise_native_wait']))
        for index,before,after in edits:
            p=offset+index*4
            if u32(module,p)!=before:raise ValueError('Changed exercise/WAIT callback')
            struct.pack_into('>I',module,p,after)
            table_patches.append(dict(offset=p,index=index,before=before,after=after))
        table['sha256']=sha256(module[offset:offset+size])
    allocation=report['held_rig_actions']['player_allocation'];address=allocation['address']
    if allocation['bytes']!=0x13B0 or u32(core,address-CODE_RAM)!=0x13B0:
        raise ValueError('Changed transient player extension allocation')
    struct.pack_into('>I',core,address-CODE_RAM,0x13E0);allocation['bytes']=0x13E0
    arena=old['player_motion']['allocation']['scene_arena_bytes'];core_patches=[]
    for addr,prefix in ((0x800C6618,0x34A50000),(0x800C6628,0x34210000)):
        before=prefix|(arena&65535);after=prefix|((arena+48)&65535)
        if arena>>16!=(arena+48)>>16 or u32(core,addr-CODE_RAM)!=before:
            raise ValueError('Changed scene arena before transient exercise state')
        struct.pack_into('>I',core,addr-CODE_RAM,after)
        core_patches.append(dict(address=addr,before=before,after=after))
    current.update(owner_sha256=sha256(owner),relocation_sha256=sha256(new_reloc),
        removed_relocations=current['removed_relocations']+len(removed))
    current['enabled_imported_actions']=sorted(current['enabled_imported_actions']+[111])
    current['disabled_indices'].remove(111)
    motion=report['player_motion'];motion.update(owner_sha256=sha256(owner),reloc_sha256=sha256(new_reloc))
    motion['exercise'].update(action_installed=True,prepared_core_installed=True,native=dict(
        code=compiled,binding=binding,packet=dict(ram=code_ram,capacity=code_end-code_ram,
            blob_offset=at,vrom=BLOB+at,bytes=len(packet),sha256=sha256(packet),crc32=zlib.crc32(packet)),
        player_bytes=0x13E0,state_offset=0x13B0,state_bytes=44,additional_scene_bytes=48,
        previous_scene_arena_bytes=arena,scene_arena_bytes=arena+48,core_patches=core_patches,
        player_allocation_address=address,owner_hooks=patches,callback_patches=table_patches,
        removed_relocations=sorted(removed),native_execution_tested=False,saved_format_changed=False))
    blob[start:start+len(module)]=module
    report.update(sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=len(packet))
    return report,{PLAYER_VROM:bytes(owner),0x7D9BA0:bytes(new_reloc)}
