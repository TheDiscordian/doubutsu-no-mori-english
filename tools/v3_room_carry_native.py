"""Install shared moving-parent hooks against the actual relocated N64 owner."""
import copy
import json
import struct
from types import SimpleNamespace
import zlib

from aflib import by_vrom,sha256,u32
from apply_translation import write_new
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB,ROOT,compile_part
from v3_import_storage import jump
from v3_room_carry import source_contract

VROM,RELOC,RAM=0x82D7F0,0x844400,0x80936710
CODE_RAM,CODE_END,STATE_RAM,STATE_BYTES=0x804DA000,0x804DC000,0x804DC400,0x400
SOURCE_SHA='a719adbd7209a8ce0bc9778d77da07be0b74cf99faeb7fc55f3d56c8d2f8598b'
RELOC_SHA='c97bc9e48c97a6830145218f5fcdcaa664a7611167b2f013bc93d75f4e493bc5'
HOOKS=(
    (0x8093B6D8,'af_v3_carry_ctor','0c24ed2602002025'),
    (0x8093BB14,'af_v3_carry_destruct','0c24dc5000000000'),
    (0x8093F18C,'af_v3_carry_blocked','0c24f8648fa4007c'),
    (0x8093F598,'af_v3_carry_blocked','0c24f8648fa4006c'),
    (0x80941524,'af_v3_carry_blocked','0c24f8648fa4006c'),
    (0x8093F28C,'af_v3_carry_move_bridge','0c24f2beafa5003c'),
    (0x8093F608,'af_v3_carry_move_bridge','0c24f2beafa5002c'),
    (0x809415EC,'af_v3_carry_permit_rotate_b','0c24fef887a7005c'),
    (0x80941744,'af_v3_carry_permit_rotate_ac','0c24ff4502002025'),
    (0x80944FD0,'af_v3_carry_update_bridge','3c0280948c427568'),
    (0x809471CC,'af_v3_carry_rotation_bridge','0c0381a624050001'),
    (0x809472B4,'af_v3_carry_draw','0c251bd002203825'))
SOURCES=('tools/v3_room_carry_native.py','tools/v3_room_carry.py','tools/v3_room_goods.py',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py','overlays/v3/surface_bootstrap.c',
    'overlays/v3/room_carry.c','overlays/v3/room_carry.h','overlays/v3/room_rigs.h',
    'overlays/v3/furniture_tables.h','overlays/v3/room_goods.h',
    'overlays/v3/room_carry_native.c','overlays/v3/room_carry_native.h',
    'overlays/v3/room_carry_native_bridge.S','overlays/v3/room_carry_native.ld')


def patch_native(native,relocation,symbols):
    if sha256(native)!=SOURCE_SHA or sha256(relocation)!=RELOC_SHA:
        raise ValueError('Changed complete carrying owner/relocation input')
    sections=struct.unpack_from('>5I',relocation)
    if sections!=(0x10E50,0x5BE0,0x1E0,0x22F0,1387):raise ValueError('Changed carrying owner dimensions')
    data=bytearray(native);changed=set();hooks=[];expected_removed={}
    for address,name,expected in HOOKS:
        at=address-RAM;before=bytes.fromhex(expected);target=symbols[name]
        if native[at:at+8]!=before or target&3 or not CODE_RAM<=target<CODE_END:
            raise ValueError('Changed carrying call: '+name)
        count_load=address==0x80944FD0
        after=struct.pack('>I',jump(target,link=True))+(bytes(4) if count_load else before[4:])
        data[at:at+8]=after;changed.update(range(at,at+(8 if count_load else 4)))
        if count_load:expected_removed.update({at:5,at+4:6})
        elif address!=0x809471CC:expected_removed[at]=4
        hooks.append(dict(address=address,symbol=name,target=target,before=before.hex(),after=after.hex()))
    retained=[];removed=[]
    for word in struct.unpack_from('>'+str(sections[4])+'I',relocation,20):
        section,kind,offset=word>>30,word>>24&63,word&0xFFFFFF
        at=sum(sections[:section-1])+offset
        if at in changed:
            if section!=1 or kind!=expected_removed.pop(at,None):
                raise ValueError('Unexpected carrying hook relocation')
            removed.append(word)
        else:retained.append(word)
    if expected_removed:raise ValueError('Missing carrying call/count relocation')
    reloc=bytearray(relocation);struct.pack_into('>I',reloc,16,len(retained))
    reloc[20:-4]=struct.pack('>'+str(len(retained))+'I',*retained)+bytes(len(reloc)-24-len(retained)*4)
    spec=SimpleNamespace(ram=RAM,resident_bytes=0x18F00,sections=sections)
    after_spec=SimpleNamespace(ram=RAM,resident_bytes=0x18F00,sections=(*sections[:4],len(retained)))
    for base in (0x801A0010,0x802F8010,0x803D0010):
        before=relocate_verified_data(spec,native,relocation,base)
        after=relocate_verified_data(after_spec,data,reloc,base)
        if any(a!=b and at not in changed for at,(a,b) in enumerate(zip(before,after,strict=True))):
            raise ValueError('Carrying hooks change unrelated relocated instructions/data')
        for hook in hooks:
            at=hook['address']-RAM
            if after[at:at+8].hex()!=hook['after']:raise ValueError('Carrying hook was relocated incorrectly')
    return bytes(data),bytes(reloc),dict(hooks=hooks,removed_relocations=removed,
        owner_sha256=sha256(data),relocation_sha256=sha256(reloc),saved_format_changed=False,
        actor_allocation_changed=False,stored_item_restrictions_retained=True,installed=False)


def goods_contract(image,prior):
    from v3_room_goods import CODE_RAM as goods_start,CODE_END as goods_end
    equipment=prior['equipment_resources'];goods=equipment['room_goods'];packet=goods['packet']
    blob=by_vrom(image)[BLOB].extract(image);raw=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
    if (goods.get('format')!='AFV3-ROOM-GOODS-1' or not goods.get('installed') or
            packet['ram']!=goods_start or sha256(raw)!=packet['sha256'] or zlib.crc32(raw)!=packet['crc32']):
        raise ValueError('Missing complete installed loose-item dependency')
    symbols=goods['compiled']['symbols'];exports={key:symbols[key] for key in
        ('af_v3_goods_get','af_v3_goods_set','af_v3_goods_single')}
    if any(at&3 or not goods_start<=at<goods_end for at in exports.values()):
        raise ValueError('Changed loose-item export bounds')
    return dict(packet_sha256=packet['sha256'],exports=exports)


def prepare(source,image,prior,output):
    files=by_vrom(image);native=files[VROM].extract(image);reloc=files[RELOC].extract(image)
    contract=source_contract(source);goods=goods_contract(image,prior);exports=goods['exports']
    output.mkdir(parents=True,exist_ok=False)
    code,compiled=compile_part('room_carry_native',output/'code',
        extra_sources=('overlays/v3/room_carry.c','overlays/v3/room_carry_native_bridge.S'),
        defines=(f'AF_GOODS_GET=0x{exports["af_v3_goods_get"]:X}u',
                 f'AF_GOODS_SET=0x{exports["af_v3_goods_set"]:X}u',
                 f'AF_GOODS_SINGLE=0x{exports["af_v3_goods_single"]:X}u'))
    owner,new_reloc,binding=patch_native(native,reloc,compiled['symbols'])
    write_new(output/'room.bin',owner);write_new(output/'room-reloc.bin',new_reloc)
    result=dict(format='AFV3-ROOM-CARRY-PREPARED-1',source=contract,goods=goods,compiled=compiled,binding=binding,
        state=dict(ram=STATE_RAM,bytes=STATE_BYTES,used=172,mutable=True,saved=False),
        code=dict(ram=CODE_RAM,bytes=len(code),capacity=CODE_END-CODE_RAM,sha256=sha256(code)),
        base_rom_sha256=sha256(image),installed=False,
        sources={path:sha256((ROOT/path).read_bytes()) for path in SOURCES})
    write_new(output/'carrying.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


def install(base,prior,blob,output,directory):
    from v3_furniture_pipeline import Source
    directory=directory.resolve();raw=(directory/'carrying.json').read_bytes();prepared=json.loads(raw)
    if (prepared.get('format')!='AFV3-ROOM-CARRY-PREPARED-1' or prepared.get('installed') is not False or
            prepared.get('sources')!={path:sha256((ROOT/path).read_bytes()) for path in SOURCES}):
        raise ValueError('Stale or incomplete native carrying preparation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if (json.loads(json.dumps(source_contract(source)))!=prepared['source'] or
            goods_contract(base,prior)!=prepared['goods']):raise ValueError('Changed carrying dependencies')
    code=(directory/'code/code.bin').read_bytes();compiled=prepared['compiled']
    if (len(code)!=compiled['bytes'] or sha256(code)!=compiled['sha256'] or
            compiled['symbols']['af_v3_carry_ctor']!=CODE_RAM or len(code)>CODE_END-CODE_RAM):
        raise ValueError('Changed complete native carrying code')
    files=by_vrom(base)
    owner,reloc,binding=patch_native(files[VROM].extract(base),files[RELOC].extract(base),compiled['symbols'])
    if (owner!=(directory/'room.bin').read_bytes() or reloc!=(directory/'room-reloc.bin').read_bytes() or
            binding!=prepared['binding']):raise ValueError('Changed prepared carrying owner')
    result=copy.deepcopy(prior['equipment_resources']);goods=result['room_goods']
    if (result.get('room_carry') or goods['packet']['ram']+goods['packet']['capacity']>CODE_RAM or
            CODE_END>goods['state']['ram'] or goods['state']['ram']+goods['state']['bytes']>STATE_RAM or
            STATE_RAM+STATE_BYTES>prior['furniture']['bank_pool']['start']):
        raise ValueError('Native carrying overlaps an existing reservation')
    packet=code.ljust((len(code)+15)&~15,b'\0');blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(packet)
    binding['installed']=True
    result['room_carry']=dict(format='AFV3-ROOM-CARRY-1',source=prepared['source'],goods=prepared['goods'],
        compiled=compiled,binding=binding,preparation=str(directory.relative_to(ROOT)),preparation_sha256=sha256(raw),
        packet=dict(blob_offset=at,vrom=BLOB+at,ram=CODE_RAM,bytes=len(packet),capacity=CODE_END-CODE_RAM,
                    sha256=sha256(packet),crc32=zlib.crc32(packet)),
        state=dict(ram=STATE_RAM,bytes=STATE_BYTES,used=172,mutable=True,saved=False),
        installed=True,occupied_table_movement_enabled=True,native_execution_tested=False,
        saved_format_changed=False,profile_changed=False)
    goods['occupied_table_movement_enabled']=True
    return result,{VROM:owner,RELOC:reloc}
