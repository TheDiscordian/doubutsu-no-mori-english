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
    boot,compiled=compile_part('surface_bootstrap',output/'goods_surface_bootstrap',defines=(
        'AF_V3_EDITABLE_CHECKSUMS=1',f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',
        f'AF_SURFACE_ITEMS_CRC=0x{items["crc32"]:X}u',f'AF_SURFACE_ITEMS_BYTES=0x{items["bytes"]:X}u',
        f'AF_ROOM_GOODS_VROM=0x{packet["vrom"]:X}u',f'AF_ROOM_GOODS_CRC=0x{packet["crc32"]:X}u',
        f'AF_ROOM_GOODS_BYTES=0x{packet["bytes"]:X}u',*extra))
    if len(boot)>BOOT_END-BOOT:raise ValueError('Combined surface/goods startup exceeds its reservation')
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
