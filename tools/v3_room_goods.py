"""Prepare source-derived loose-item rotation and complete native drawing hooks."""
import json
import struct
import copy
import zlib
from types import SimpleNamespace

from aflib import by_vrom,sha256,u32
from apply_translation import write_new
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB,ROOT,compile_part
from v3_import_storage import jump
from v3_room_carry import BLOCKS as CARRY_BLOCKS

VROM,RELOC,RAM=0x8576C0,0x858960,0x80962A20
CODE_RAM,CODE_END,STATE_RAM,STATE_BYTES=0x804D9000,0x804DA000,0x804DC000,0x400
SOURCE_SHA='24404e3005c31bfe13bb2f7e721b3d3a200b8487a96d02ce42e658a14ebd2ade'
RELOC_SHA='aad577d021d48de603615f5497a61f15a6e1ed9dea452ba2ddf8fa1a1d75d40e'
TABLE_AT,TABLE_BYTES,TABLE_STRIDE=0x3BC8,0xE38,40
TABLE_SHA='52a1670804799148b43d2da62c7411c6078136a5cb52e63c2a2ce05763f7f28d'
BLOCKS=(
    (0x12DA50,604,'87e4d4283e0d265aa4734d885e3d65da18ca8e5cffe9596eea22d2c6a8e17117','22cbadd25ad3dbe6d5876a84b13fd796df6911105dee36766f894557f8d7ffc8'),
    (0x12DCAC,128,'bb64c3c60ad5e06dcde2c1fe11d3db0d45f7b9a8e34243067077bc80dbc179a9','44bcf134fe73eb97129b6e5962b4e0bc43929dbacb9f0b39947e316463fa1713'),
    (0x12DFE8,592,'ccc2d701aee35a2627ca9dde21b8ed3c378d31b2dc6b0e3fc8dc4a0451a72da3','9968bb14268cd1f14ad0ffc6cdc3f68376df56738bbfacdcc4997d72b2e00164'),
    (0x12D338,548,'14c8df48400f26581cca2b74c75f5dceb5bacb4381dc8d7c51f2e31095fa0655','7cb3c8791e351b447d0da42d665df3529862c32db40b40cb6b068206cd3e2ae6'))
HOOKS=(
    (0x8096344C,'af_v3_goods_ctor_bridge','0c258cf900000000'),
    (0x80963554,'af_v3_goods_destruct','0c258b5600000000'),
    (0x80963214,'af_v3_goods_single_scale_bridge','0c0381078c460008'),
    (0x809636DC,'af_v3_goods_grid_scale_bridge','0c03810746006386'),
    (0x80962BE0,'af_v3_goods_drop_fg_bridge','0c022aa6afa7000c'))
SOURCES=('tools/v3_room_goods.py','tools/v3_room_carry.py',
    'overlays/v3/room_goods.c','overlays/v3/room_goods.h','overlays/v3/room_goods_bridge.S','overlays/v3/room_goods.ld',
    'overlays/v3/room_rigs.h','overlays/v3/surface_bootstrap.c','tools/v3_asset_loader.py',
    'tools/v3_furniture_install.py')


def rotation_contract(source,native):
    if len(native)!=0x12A0 or sha256(native)!=SOURCE_SHA:
        raise ValueError('Changed complete native loose-item owner')
    functions={}
    for at,size,digest,relocations in (*BLOCKS,*CARRY_BLOCKS[-2:]):
        raw,row=source.function(at)
        if (len(raw)!=size or sha256(raw)!=digest or
                sha256(json.dumps(sorted(row['relocations'].items()),separators=(',',':')).encode())!=relocations):
            raise ValueError('Changed complete loose-item drawing dependency: '+row['symbol'])
        functions[row['symbol']]=row
    start,size=source.sections[4]
    raw=source.rel[start+TABLE_AT:start+TABLE_AT+TABLE_BYTES]
    if TABLE_AT+TABLE_BYTES>size or len(raw)!=TABLE_BYTES or sha256(raw)!=TABLE_SHA:
        raise ValueError('Changed complete donor loose-item drawing table')
    donor=[]
    for at in range(0,TABLE_BYTES,TABLE_STRIDE):
        first,last=struct.unpack_from('>HH',raw,at);flags=u32(raw,at+36)
        if (first,last)==(0,0):
            if at+TABLE_STRIDE!=len(raw) or raw[at:]!=bytes(TABLE_STRIDE):
                raise ValueError('Changed donor drawing-table terminator')
            break
        if first>last or flags not in (0,1):raise ValueError('Unknown donor loose-item flags')
        donor.append(dict(index=len(donor),first=first,last=last,rotate=bool(flags)))
    rows=[];mask=0
    for index in range(34):
        first,last=struct.unpack_from('>HH',native,0xFB0+index*20)
        matches=[row for row in donor if first<=row['last'] and row['first']<=last]
        values={row['rotate'] for row in matches}
        if first>last or len(values)>1:raise ValueError('Conflicting source flags in native drawing category')
        rotate=next(iter(values),False)
        if rotate:mask|=1<<index
        rows.append(dict(index=index,first=first,last=last,rotate=rotate,source_rows=[row['index'] for row in matches],
            policy='donor category flag' if matches else 'no generic donor row; retain native orientation'))
    if native[0xFB0+34*20:0xFB0+35*20]!=bytes(20):raise ValueError('Changed native drawing terminator')
    return dict(functions=functions,source_table=dict(section=4,offset=TABLE_AT,bytes=TABLE_BYTES,
        stride=TABLE_STRIDE,sha256=TABLE_SHA),donor_rows=donor,native_rows=rows,
        mask_low=mask&0xFFFFFFFF,mask_high=mask>>32)


def patch_native(native,relocation,symbols):
    if sha256(native)!=SOURCE_SHA or sha256(relocation)!=RELOC_SHA:
        raise ValueError('Changed native loose-item patch input')
    sections=struct.unpack_from('>5I',relocation)
    if sections!=(0xFB0,0x2E0,0x10,0x10,54):raise ValueError('Changed loose-item owner dimensions')
    data=bytearray(native);hooks=[];changed=set()
    for address,name,expected in HOOKS:
        at=address-RAM;before=bytes.fromhex(expected);target=symbols[name]
        if (data[at:at+8]!=before or target&3 or not CODE_RAM<=target<CODE_END):
            raise ValueError('Changed loose-item hook: '+name)
        after=struct.pack('>I',jump(target,link=True))
        data[at:at+4]=after;changed.update(range(at,at+4))
        hooks.append(dict(address=address,symbol=name,target=target,before=before.hex(),after=(after+before[4:]).hex()))
    retained=[];removed=[]
    for word in struct.unpack_from('>54I',relocation,20):
        section,kind,offset=word>>30,word>>24&63,word&0xFFFFFF
        at=sum(sections[:section-1])+offset
        if at in changed:
            if section!=1 or kind!=4 or at not in (0xA2C,0xB34):raise ValueError('Unexpected replaced loose-item relocation')
            removed.append(word)
        else:retained.append(word)
    if sorted(removed)!=[0x44000A2C,0x44000B34]:raise ValueError('Missing complete native lifetime relocations')
    reloc=bytearray(relocation);struct.pack_into('>I',reloc,16,len(retained))
    reloc[20:-4]=struct.pack('>'+str(len(retained))+'I',*retained)+bytes(len(reloc)-24-len(retained)*4)
    spec=SimpleNamespace(ram=RAM,resident_bytes=0x12B0,sections=sections)
    target_spec=SimpleNamespace(ram=RAM,resident_bytes=0x12B0,sections=(*sections[:4],len(retained)))
    for base in (0x801A0010,0x802F8010,0x803D0010):
        before=relocate_verified_data(spec,native,relocation,base)
        after=relocate_verified_data(target_spec,data,reloc,base)
        if any(a!=b and at not in changed for at,(a,b) in enumerate(zip(before,after,strict=True))):
            raise ValueError('Loose-item hooks change unrelated relocated instructions/data')
        for hook in hooks:
            if u32(after,hook['address']-RAM)!=jump(hook['target'],link=True):
                raise ValueError('Loose-item hook was incorrectly relocated')
    return bytes(data),bytes(reloc),dict(hooks=hooks,removed_relocations=removed,
        owner_sha256=sha256(data),relocation_sha256=sha256(reloc),saved_format_changed=False,
        caller_delay_slots_retained=True,model_table_retained=True,installed=False)


def prepare(source,image,output):
    files=by_vrom(image);native=files[VROM].extract(image);reloc=files[RELOC].extract(image)
    source_contract=rotation_contract(source,native)
    output.mkdir(parents=True,exist_ok=False)
    code,compiled=compile_part('room_goods',output/'code',extra_sources=('overlays/v3/room_goods_bridge.S',),
        defines=(f'AF_GOODS_ROTATE_LOW=0x{source_contract["mask_low"]:X}u',
                 f'AF_GOODS_ROTATE_HIGH=0x{source_contract["mask_high"]:X}u'))
    owner,new_reloc,binding=patch_native(native,reloc,compiled['symbols'])
    write_new(output/'shop.bin',owner);write_new(output/'shop-reloc.bin',new_reloc)
    result=dict(format='AFV3-ROOM-GOODS-PREPARED-1',source=source_contract,compiled=compiled,binding=binding,
        state=dict(ram=STATE_RAM,bytes=STATE_BYTES,used=524,mutable=True,saved=False),
        code=dict(ram=CODE_RAM,bytes=len(code),capacity=CODE_END-CODE_RAM,sha256=sha256(code)),
        base_rom_sha256=sha256(image),installed=False,
        sources={path:sha256((ROOT/path).read_bytes()) for path in SOURCES},
        pending=['checked startup loading and fixed-memory reservation',
                 'install the owner and relocation through the shared runtime builder',
                 'native bridge execution and GPU appearance'])
    write_new(output/'goods.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


def install(base,prior,blob,output,directory):
    from v3_furniture_pipeline import Source
    from v3_room_rig_runtime import packet_layout
    directory=directory.resolve()
    raw=(directory/'goods.json').read_bytes();prepared=json.loads(raw)
    if (prepared.get('format')!='AFV3-ROOM-GOODS-PREPARED-1' or prepared.get('installed') is not False or
            prepared.get('sources')!={path:sha256((ROOT/path).read_bytes()) for path in SOURCES}):
        raise ValueError('Stale or incomplete loose-item preparation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    files=by_vrom(base);native=files[VROM].extract(base);reloc=files[RELOC].extract(base)
    contract=rotation_contract(source,native)
    if json.loads(json.dumps(contract))!=prepared['source']:raise ValueError('Changed loose-item source contract')
    code=(directory/'code/code.bin').read_bytes();compiled=prepared['compiled']
    if (len(code)!=compiled['bytes'] or sha256(code)!=compiled['sha256'] or
            compiled['symbols']['af_v3_goods_ctor']!=CODE_RAM or len(code)>CODE_END-CODE_RAM):
        raise ValueError('Changed complete loose-item native code')
    owner,new_reloc,binding=patch_native(native,reloc,compiled['symbols'])
    if ((directory/'shop.bin').read_bytes()!=owner or (directory/'shop-reloc.bin').read_bytes()!=new_reloc or
            binding!=prepared['binding']):raise ValueError('Changed complete prepared loose-item owner')
    result=copy.deepcopy(prior['equipment_resources'])
    ram,_,size=packet_layout(result['room_rigs'])
    if result.get('room_goods') or ram+size>CODE_RAM or CODE_END>STATE_RAM or STATE_RAM+STATE_BYTES>prior['furniture']['bank_pool']['start']:
        raise ValueError('Loose-item code/state overlaps an existing reservation')
    packet=code.ljust((len(code)+15)&~15,b'\0')
    blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(packet)
    binding['installed']=True
    result['room_goods']=dict(format='AFV3-ROOM-GOODS-1',source=contract,compiled=compiled,binding=binding,
        preparation=str(directory.relative_to(ROOT)),preparation_sha256=sha256(raw),
        packet=dict(blob_offset=at,vrom=BLOB+at,ram=CODE_RAM,bytes=len(packet),capacity=CODE_END-CODE_RAM,
                    sha256=sha256(packet),crc32=zlib.crc32(packet)),
        state=dict(ram=STATE_RAM,bytes=STATE_BYTES,used=524,mutable=True,saved=False),
        saved_format_changed=False,profile_changed=False,installed=True,native_execution_tested=False,
        occupied_table_movement_enabled=False)
    return result,{VROM:owner,RELOC:new_reloc}


def publish_bootstrap(equipment,blob,surface,output):
    """Retain the goods preload whenever another shared stage rebuilds startup."""
    from v3_surface_items import BOOT,BOOT_END
    goods=equipment['room_goods'];packet=goods['packet'];items=surface['items']
    code=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
    if sha256(code)!=packet['sha256'] or zlib.crc32(code)!=packet['crc32']:
        raise ValueError('Changed resident loose-item packet')
    at=equipment['blob_offset'];module=bytearray(blob[at:at+equipment['bytes']])
    if sha256(module)!=equipment['sha256']:raise ValueError('Changed equipment before goods startup')
    carrying=equipment.get('room_carry');extra=()
    if carrying:
        p=carrying['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32']:
            raise ValueError('Changed resident carrying packet')
        extra=(f'AF_ROOM_CARRY_VROM=0x{p["vrom"]:X}u',f'AF_ROOM_CARRY_CRC=0x{p["crc32"]:X}u',
               f'AF_ROOM_CARRY_BYTES=0x{p["bytes"]:X}u')
    exercise=equipment.get('player_motion',{}).get('exercise',{}).get('native')
    if exercise:
        p=exercise['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                p['ram']!=0x804CE000 or p['bytes']>0x2000):
            raise ValueError('Changed resident player-exercise packet')
        extra+=(f'AF_PLAYER_EXERCISE_VROM=0x{p["vrom"]:X}u',f'AF_PLAYER_EXERCISE_CRC=0x{p["crc32"]:X}u',
                f'AF_PLAYER_EXERCISE_BYTES=0x{p["bytes"]:X}u')
    console=equipment.get('console_storage')
    if console:
        p=console['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                p['ram']!=0x804DE200 or p['bytes']!=0x4E00):
            raise ValueError('Changed resident console-storage packet')
        extra+=(f'AF_CONSOLE_STORAGE_VROM=0x{p["vrom"]:X}u',f'AF_CONSOLE_STORAGE_CRC=0x{p["crc32"]:X}u',
                f'AF_CONSOLE_STORAGE_BYTES=0x{p["bytes"]:X}u')
    images=equipment.get('console_images')
    if images:
        p=images['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                p['ram']!=0x804F9020 or p['bytes']!=0x5800):
            raise ValueError('Changed complete console image-loader packet')
        extra+=(f'AF_CONSOLE_IMAGES_VROM=0x{p["vrom"]:X}u',f'AF_CONSOLE_IMAGES_CRC=0x{p["crc32"]:X}u',
                f'AF_CONSOLE_IMAGES_BYTES=0x{p["bytes"]:X}u')
    disk=equipment.get('console_disk')
    if disk:
        from v3_console_disk_install import RAM,END,LAYOUT
        p=disk['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                p['ram']!=RAM or p['bytes']!=END-RAM or disk['layout']!=LAYOUT):
            raise ValueError('Changed complete resident disk module')
        extra+=(f'AF_CONSOLE_DISK_VROM=0x{p["vrom"]:X}u',f'AF_CONSOLE_DISK_CRC=0x{p["crc32"]:X}u',
                f'AF_CONSOLE_DISK_BYTES=0x{p["bytes"]:X}u')
    creatures=equipment.get('creature_items')
    if creatures:
        from v3_creature_items import RAM as CREATURE_RAM,SIZE as CREATURE_SIZE
        p=creatures['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                p['ram']!=CREATURE_RAM or p['bytes']!=CREATURE_SIZE):
            raise ValueError('Changed complete creature item packet')
        extra+=(f'AF_CREATURE_ITEMS_VROM=0x{p["vrom"]:X}u',f'AF_CREATURE_ITEMS_CRC=0x{p["crc32"]:X}u',
                f'AF_CREATURE_ITEMS_BYTES=0x{p["bytes"]:X}u')
    field=equipment.get('creature_field')
    if field:
        from v3_creature_field_native import RAM as FIELD_RAM,SIZE as FIELD_SIZE
        p=field['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                p['ram']!=FIELD_RAM or p['bytes']!=FIELD_SIZE):
            raise ValueError('Changed complete creature field packet')
        extra+=(f'AF_CREATURE_FIELD_VROM=0x{p["vrom"]:X}u',f'AF_CREATURE_FIELD_CRC=0x{p["crc32"]:X}u',
                f'AF_CREATURE_FIELD_BYTES=0x{p["bytes"]:X}u')
    fish_world=equipment.get('creature_fish',{}).get('world')
    if fish_world:
        from v3_creature_fish import WORLD_RAM,WORLD_SIZE
        p=fish_world['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                p['ram']!=WORLD_RAM or p['bytes'] not in (WORLD_SIZE,0xB000,0xC000)):
            raise ValueError('Changed complete fish world packet')
        extra+=(f'AF_FISH_WORLD_VROM=0x{p["vrom"]:X}u',f'AF_FISH_WORLD_CRC=0x{p["crc32"]:X}u',
                f'AF_FISH_WORLD_BYTES=0x{p["bytes"]:X}u')
    insects=equipment.get('creature_insects')
    if insects:
        p=insects['packet'];compiled=insects['compiled']
        if (p['ram']!=compiled['ram'] or p['bytes']!=compiled['bytes']+16 or
                p['bytes']&15 or p['physical']&15 or not 0x100000<=p['physical']<0x4000000-p['bytes'] or
                p['ram']!=0x80656000 or p['ram']+p['bytes']>0x807DA800 or
                p['sha256']!=insects['physical_resource']['sha256'] or
                p['physical']!=insects['physical_resource']['physical']):
            raise ValueError('Changed complete insect startup packet')
        extra+=(f'AF_INSECT_PHYSICAL=0x{p["physical"]:X}u',f'AF_INSECT_CRC=0x{p["crc32"]:X}u',
                f'AF_INSECT_BYTES=0x{p["bytes"]:X}u',f'AF_INSECT_RAM=0x{p["ram"]:X}u')
    clothing=equipment.get('clothing_batch')
    if clothing:
        p=clothing['packet'];raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        if (p['ram']!=0x8066E000 or p['bytes']!=0x1000 or sha256(raw)!=p['sha256']
                or zlib.crc32(raw)!=p['crc32']):
            raise ValueError('Changed complete clothing startup packet')
        extra+=(f'AF_CLOTHING_VROM=0x{p["vrom"]:X}u',f'AF_CLOTHING_CRC=0x{p["crc32"]:X}u',
                f'AF_CLOTHING_BYTES=0x{p["bytes"]:X}u',f'AF_CLOTHING_RAM=0x{p["ram"]:X}u')
    diaries=equipment.get('diaries')
    if diaries:
        from v3_diary_install import LAYOUT,MEMORY
        expected={'storage':(LAYOUT['code']['ram'],LAYOUT['code']['bytes']),
            'ui':(MEMORY['code'][0],MEMORY['code'][1]+MEMORY['state'][1]),'art':MEMORY['art']}
        if set(diaries['packets'])!=set(expected):raise ValueError('Incomplete diary startup packets')
        for name,(ram,size) in expected.items():
            p=diaries['packets'][name]
            if (p['ram']!=ram or p['bytes']!=size or p['physical']&15 or
                    not 0x100000<=p['physical']<p['physical']+size<=0x4000000 or
                    p['storage']!='physical-ROM'):
                raise ValueError('Changed complete diary startup packet: '+name)
            prefix='AF_DIARY_'+name.upper()
            extra+=tuple(f'{prefix}_{label}=0x{p[key]:X}u' for label,key in
                (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
    diary_items=equipment.get('diary_items')
    if diary_items:
        p=diary_items['packet']
        if (not diaries or p['ram']!=0x806E0000 or p['bytes']!=0x4000 or p['physical']&15 or
                p['storage']!='physical-ROM' or not 0x100000<=p['physical']<p['physical']+p['bytes']<=0x4000000):
            raise ValueError('Changed complete diary item startup packet')
        extra+=tuple(f'AF_DIARY_ITEMS_{label}=0x{p[key]:X}u' for label,key in
            (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
    npc_extra=equipment.get('npc_extra')
    if npc_extra:
        from v3_npc_registry import RAM as NPC_RAM,SIZE as NPC_SIZE
        p=npc_extra['packet']
        if (p['ram']!=NPC_RAM or p['bytes']!=NPC_SIZE or p['physical']&15 or
                p['storage']!='physical-ROM' or not 0x100000<=p['physical']<p['physical']+p['bytes']<=0x4000000):
            raise ValueError('Changed complete additional NPC startup packet')
        extra+=tuple(f'AF_NPC_EXTRA_{label}=0x{p[key]:X}u' for label,key in
            (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
        extra+=(f'AF_NPC_EXTRA_INIT=0x{npc_extra["code"]["symbols"]["af_v3_npc_dma_init"]:X}u',)
    holiday_state=equipment.get('holiday_state')
    fishing=equipment.get('holiday_fishing')
    if holiday_state:
        from v3_holiday_state import RAM as HOLIDAY_RAM,SIZE as HOLIDAY_SIZE
        p=holiday_state['packet']
        transition=npc_extra.get('events',{}).get('transition') if npc_extra else None
        sky=npc_extra.get('events',{}).get('sky') if npc_extra else None
        size=HOLIDAY_SIZE
        if transition:
            if (not transition.get('installed') or transition['packet_ram']!=HOLIDAY_RAM or
                transition['packet_bytes']!=0xC000 or transition['loaded_code']['ram']!=0x806FC000 or
                not 0<transition['loaded_code']['bytes']<=0x3000 or
                transition['preserved_prefix_bytes']!=HOLIDAY_SIZE):
                raise ValueError('Changed complete scene-transition packet contract')
            size=transition['packet_bytes']
            renderer=npc_extra['events'].get('decorations',{}).get('renderer')
            controllers=npc_extra['events'].get('decorations',{}).get('controllers')
            if renderer:
                from v3_decoration_draw import RAM as DRAW_RAM,ART as DRAW_ART,END as DRAW_END
                if (not renderer['installed'] or renderer['packet_ram']!=HOLIDAY_RAM or
                    renderer['packet_bytes']!=DRAW_END-HOLIDAY_RAM or
                    renderer['preserved_prefix_bytes']!=size or
                    renderer['loaded_code']['ram']!=DRAW_RAM or
                    not 0<renderer['loaded_code']['bytes']<=0x4000 or
                    renderer['artwork']['ram']!=DRAW_ART or
                    DRAW_ART+renderer['artwork']['bytes']>DRAW_END-16 or
                    (not controllers and p['id']!='holiday-decoration-runtime-GAFE01-r0')):
                    raise ValueError('Changed complete decoration loading contract')
                size=renderer['packet_bytes']
                if controllers:
                    from v3_decoration_actor import RAM as ACTOR_RAM,END as ACTOR_END,CONTEXT,DATA_END
                    if (not controllers['installed'] or controllers['packet_ram']!=HOLIDAY_RAM or
                        controllers['packet_bytes']!=ACTOR_END-HOLIDAY_RAM or
                        controllers['loaded_code']['ram']!=ACTOR_RAM or
                        not 0<controllers['loaded_code']['bytes']<=ACTOR_END-ACTOR_RAM-16 or
                        controllers['data']['ram']!=CONTEXT or controllers['data']['bytes']!=DATA_END-CONTEXT or
                        ACTOR_RAM!=DRAW_END or controllers['original_packet']['bytes']!=size or
                        p['id']!=('holiday-fishing-GAFE01-r0' if fishing else 'holiday-decoration-actors-GAFE01-r0')):
                        raise ValueError('Changed complete decoration controller loading contract')
                    size=controllers['packet_bytes']
            elif p['id']!='holiday-transition-GAFE01-r0':
                raise ValueError('Changed scene-transition physical identity')
        if fishing:
            from v3_holiday_fishing import RAM as FISHING_RAM,SIZE as FISHING_SIZE
            if (not fishing.get('storage_installed') or fishing['packet']!=p or
                    fishing['preserved_prefix_bytes']!=size or HOLIDAY_RAM+size!=FISHING_RAM or
                    p['bytes']!=size+FISHING_SIZE or fishing['loaded_code']['ram']!=FISHING_RAM):
                raise ValueError('Changed combined fishing startup packet')
            size+=FISHING_SIZE
        if sky:
            from v3_holiday_sky import RAM as SKY_RAM,END as SKY_END,PACKET_END
            sp=sky['packet']
            participants=npc_extra['events'].get('participants')
            sky_bytes=PACKET_END-SKY_RAM
            if participants:
                pc=participants['loaded_code']
                if (not participants['installed'] or participants['packet']!=sp or pc['ram']!=PACKET_END or
                        participants['preserved_prefix_bytes']!=sky_bytes or
                        participants['preserved_sky_packet']['bytes']!=sky_bytes or
                        pc['ram']+pc['bytes']>0x807DA800):
                    raise ValueError('Changed connected participant startup packet')
                sky_bytes+=pc['bytes']
            variants=npc_extra.get('variants')
            if variants:
                if (not variants['installed'] or variants['ram']!=SKY_RAM+sky_bytes or
                        variants['ram']+variants['bytes']>0x807DA800 or variants['bytes']&15):
                    raise ValueError('Changed shared character-variant startup reservation')
                sky_bytes+=variants['bytes']
            for batch in npc_extra.get('native_batches',[]):
                if (not batch['installed'] or batch['ram']!=SKY_RAM+sky_bytes or
                        batch['ram']+batch['bytes']>0x807DA800 or batch['bytes']&15):
                    raise ValueError('Changed shared native-character startup reservation')
                sky_bytes+=batch['bytes']
            for batch in npc_extra.get('source_batches',[]):
                if batch.get('packet_id'):
                    separate=npc_extra['events'].get('festivals')
                    carried=equipment.get('carried_items')
                    source_packet=carried['previous_packet'] if carried else separate['packet'] if separate else {}
                    if (not separate or batch['packet_id']!=source_packet['id'] or
                            any(batch[k]!=source_packet[k] for k in ('ram','bytes','sha256'))):
                        raise ValueError('Changed separately loaded source-character batch')
                    continue
                if (not batch['installed'] or batch['ram']!=SKY_RAM+sky_bytes or
                        batch['ram']+batch['bytes']>0x807DA800 or batch['bytes']&15):
                    raise ValueError('Changed complete source-character startup reservation')
                sky_bytes+=batch['bytes']
            if (not sky.get('installed') or sp['ram']!=SKY_RAM or sp['bytes']!=sky_bytes or
                    sp['physical']&15 or sp['storage']!='physical-ROM' or
                    sky['loaded_code']['ram']!=SKY_RAM or not 0<sky['loaded_code']['bytes']<=SKY_END-SKY_RAM or
                    sky['guard_ram']!=SKY_END):
                raise ValueError('Changed complete sky-effect startup packet')
            extra+=tuple(f'AF_HOLIDAY_SKY_{label}=0x{sp[key]:X}u' for label,key in
                (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
            festivals=npc_extra['events'].get('festivals')
            if festivals:
                fp=festivals['packet']
                expected_bytes=festivals['bytes']
                carried=equipment.get('carried_items')
                if carried:
                    extension=festivals.get('carried_packet_extension',{})
                    storage=carried.get('storage')
                    carried_end=0x80778000
                    if storage:
                        if storage['ram']!=carried_end or storage['bytes']!=storage['code']['bytes']:
                            raise ValueError('Changed carried save owner reservation')
                        carried_end+=storage['bytes']+16
                    if (carried['packet']!=fp or extension.get('previous_bytes')!=expected_bytes or
                            extension.get('end')!=carried_end or fp['ram']+fp['bytes']!=extension['end'] or
                            carried['ram']!=0x80771000 or carried['table_ram']!=0x80773800 or
                            carried['state_count']!=26 or carried['parent_count']!=7):
                        raise ValueError('Changed carried-item extension of the shared startup packet')
                    expected_bytes+=extension['bytes']
                if (not festivals['installed'] or fp['ram']!=SKY_RAM+sky_bytes or
                        fp['bytes']!=expected_bytes or fp['ram']+fp['bytes']>0x807DA800 or
                        fp['physical']&15 or fp['bytes']&15 or fp['storage']!='physical-ROM' or
                        not 0x100000<=fp['physical']<fp['physical']+fp['bytes']<=0x4000000):
                    raise ValueError('Changed separately loaded complete festival packet')
                extra+=tuple(f'AF_HOLIDAY_FESTIVALS_{label}=0x{fp[key]:X}u' for label,key in
                    (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
        if (not npc_extra or p['ram']!=HOLIDAY_RAM or p['bytes']!=size or p['physical']&15 or
                p['storage']!='physical-ROM' or not 0x100000<=p['physical']<p['physical']+p['bytes']<=0x4000000):
            raise ValueError('Changed complete holiday-state startup packet')
        extra+=tuple(f'AF_HOLIDAY_STATE_{label}=0x{p[key]:X}u' for label,key in
            (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
    tree_effects=equipment.get('scenery',{}).get('tree_effects')
    if tree_effects:
        from v3_tree_effects_runtime import RAM as TREE_RAM,ART_RAM as TREE_END
        p=tree_effects['packet']
        if (not tree_effects['installed'] or p['ram']!=TREE_RAM or p['bytes']!=TREE_END-TREE_RAM or
                p['physical']&15 or p['storage']!='physical-ROM' or
                not 0x100000<=p['physical']<p['physical']+p['bytes']<=0x4000000):
            raise ValueError('Changed complete tree-effect startup packet')
        extra+=tuple(f'AF_TREE_EFFECTS_{label}=0x{p[key]:X}u' for label,key in
            (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
    carried_field=equipment.get('carried_items',{}).get('field_creatures')
    if carried_field and (not tree_effects or not carried_field['installed'] or
            carried_field['packet']!=tree_effects['packet'] or carried_field['ram']!=0x80784000 or
            carried_field['bytes']!=0x3000 or carried_field['additional_resident_bytes']):
        raise ValueError('Changed shared carried field/tree startup packet')
    carried_quest=equipment.get('carried_items',{}).get('spawning')
    if carried_quest:
        p=carried_quest['packet']
        quest=equipment['carried_items'].get('quest')
        if (quest and quest['packet']!=p):raise ValueError('Quest owner must reuse the spirit startup packet')
        paper=equipment['carried_items'].get('paper',{}).get('quantities')
        expected=0x8000 if quest else 0x2000
        if paper:
            if (not paper['installed'] or not quest or paper['packet']!=p or
                    paper['ram']!=0x807B4000 or paper['end']!=0x807BB000 or
                    paper['save_format']!=18 or paper['wire_version']!=5):
                raise ValueError('Changed global stationery startup extension')
            expected+=0x7000
        npc=quest.get('npc') if quest else None
        if npc:
            if (not npc['installed'] or npc['packet']!=p or npc['ram']!=0x807BF000 or
                    npc['save_format']!=19 or npc['wire_version']!=6 or npc['end']>0x807DA800):
                raise ValueError('Changed complete carried NPC startup extension')
            expected=npc['end']-p['ram']
        rewards=quest.get('rewards') if quest else None
        if rewards:
            from v3_reward_bindings import LAYOUT
            reward_end=LAYOUT['pools']['ram']+LAYOUT['pools']['bytes']
            if (not npc or not rewards['installed'] or rewards['packet']!=p or
                    rewards['ram']!=LAYOUT['state']['ram'] or rewards['end']!=reward_end or
                    rewards['save_format']!=20 or rewards['wire_version']!=7 or
                    rewards['storage']['symbols']['af_v3_card_state']!=LAYOUT['state']['ram'] or
                    rewards['storage']['symbols']['AF_HI_STORAGE_RAM']!=LAYOUT['storage']['ram'] or
                    equipment['diaries']['memory']['scratch']['bytes']!=120368):
                raise ValueError('Changed complete golden reward startup extension')
            expected=reward_end-p['ram']
        if (not carried_quest['installed'] or p['ram']!=0x807AC000 or p['bytes']!=expected or
                p['physical']&15 or p['storage']!='physical-ROM' or
                not 0x100000<=p['physical']<p['physical']+p['bytes']<=0x4000000):
            raise ValueError('Changed complete carried-quest startup packet')
        extra+=tuple(f'AF_CARRIED_QUEST_{label}=0x{p[key]:X}u' for label,key in
            (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
    harvest=equipment.get('harvest')
    if harvest:
        from v3_harvest_install import RAM as HARVEST_RAM,END as HARVEST_END
        p=harvest['packet']
        if (not harvest['installed'] or p['ram']!=HARVEST_RAM or
                p['bytes']!=HARVEST_END-HARVEST_RAM or p['physical']&15 or
                p['storage']!='physical-ROM' or
                not 0x100000<=p['physical']<p['physical']+p['bytes']<=0x4000000):
            raise ValueError('Changed complete Harvest startup packet')
        extra+=tuple(f'AF_HARVEST_{label}=0x{p[key]:X}u' for label,key in
            (('PHYSICAL','physical'),('CRC','crc32'),('BYTES','bytes'),('RAM','ram')))
    boot,compiled=compile_part('surface_bootstrap',output/'goods_surface_bootstrap',defines=(
        'AF_V3_EDITABLE_CHECKSUMS=1',f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',
        f'AF_SURFACE_ITEMS_CRC=0x{items["crc32"]:X}u',f'AF_SURFACE_ITEMS_BYTES=0x{items["bytes"]:X}u',
        f'AF_ROOM_GOODS_VROM=0x{packet["vrom"]:X}u',f'AF_ROOM_GOODS_CRC=0x{packet["crc32"]:X}u',
        f'AF_ROOM_GOODS_BYTES=0x{packet["bytes"]:X}u',*extra),link_symbols=(
            {'af_surface_npc_init':npc_extra['code']['symbols']['af_v3_npc_dma_init']} if npc_extra else None))
    if len(boot)>BOOT_END-BOOT:raise ValueError('Combined surface/goods startup exceeds its reservation')
    compiled['packet_stride']=16
    compiled['packet_count']=2+sum(name.endswith('_BYTES') for name in
        (define.split('=',1)[0] for define in extra))
    begin,end=BOOT-equipment['ram'],BOOT_END-equipment['ram']
    previous=items['bootstrap']['code']
    if (sha256(module[begin:begin+previous['bytes']])!=previous['sha256'] or
            any(module[begin+previous['bytes']:end])):raise ValueError('Changed complete prior surface bootstrap')
    module[begin:end]=boot.ljust(end-begin,b'\0');blob[at:at+len(module)]=module
    items['bootstrap']['code']=compiled
    equipment.update(sha256=sha256(module),crc32=zlib.crc32(module),surface_bootstrap=copy.deepcopy(items['bootstrap']))
    goods['startup']=dict(ram=BOOT,bytes=len(boot),capacity=BOOT_END-BOOT,sha256=sha256(boot))
    if carrying:carrying['startup']=copy.deepcopy(goods['startup'])
    if exercise:exercise['startup']=copy.deepcopy(goods['startup'])
    if console:console['startup']=copy.deepcopy(goods['startup'])
    if images:images['startup']=copy.deepcopy(goods['startup'])
    if disk:disk['startup']=copy.deepcopy(goods['startup'])
    if creatures:creatures['startup']=copy.deepcopy(goods['startup'])
    if field:field['startup']=copy.deepcopy(goods['startup'])
    if fish_world:fish_world['startup']=copy.deepcopy(goods['startup'])
    if clothing:clothing['startup']=copy.deepcopy(goods['startup'])
    if insects:insects['startup']=copy.deepcopy(goods['startup'])
    if diaries:diaries['startup']=copy.deepcopy(goods['startup'])
    if npc_extra:npc_extra['startup']=copy.deepcopy(goods['startup'])
    if holiday_state:holiday_state['startup']=copy.deepcopy(goods['startup'])
    if fishing:fishing['startup']=copy.deepcopy(goods['startup'])
