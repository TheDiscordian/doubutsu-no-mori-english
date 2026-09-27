"""Shared gesture/action preparation and complete player-animation installation.

Native controls/action registration remain a separate required integration stage.
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
