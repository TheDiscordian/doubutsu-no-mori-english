"""Shared surface item readers, with incomplete imports kept unavailable."""
import copy
import struct
import zlib

from aflib import CODE_RAM, sha256
from v3_asset_loader import BLOB, MODULE_RAM, ROOT, compile_part
from v3_import_storage import jump

RAM,SIZE,TABLE,BOOT,BOOT_END=0x804BC000,0x1000,0x800,0x804A8D40,0x804A8FF0
MAGIC,GUARD=0x41465349,0xAF5351DE
SOURCES=('tools/v3_surface_items.py','overlays/v3/surface_items.c',
    'overlays/v3/surface_items.ld','overlays/v3/surface_bootstrap.c',
    'overlays/v3/surface_bootstrap.ld','overlays/v3/startup.c')
HOOKS=(('name',0x801969C8,0x80467300),('type',0x800A5630,0x804AA000),
       ('price',0x800C0194,0x80467574))


def metadata(rows):
    ordered=sorted(rows,key=lambda r:int(r['destination_item_id'],16))
    expected=[base+i for base in (0x2600,0x2700) for i in range(73,78)]
    if [int(r['destination_item_id'],16) for r in ordered]!=expected:
        raise ValueError('Surface metadata requires the complete stable destination category')
    result=bytearray(struct.pack('>4I',MAGIC,1,10,24));records=[]
    for row,item in zip(ordered,expected):
        name=row['name'].encode('ascii').ljust(16,b' ')
        if (len(name)!=16 or sha256(name)!=row['name_sha256'] or
                row['destination_index']!=(item&255) or
                row['kind']!=('floor' if item>>8==0x26 else 'wall') or
                not 0<=row['price_word']<65535):
            raise ValueError('Changed complete surface name, price, or stable identity')
        data=struct.pack('>HHI',item,row['price_word'],0)+name
        records.append(dict(id=row['id'],item_id=f'{item:04X}',name=row['name'],
            price_word=row['price_word'],name_sha256=row['name_sha256'],
            offset=TABLE+len(result),enabled=False,record_sha256=sha256(data)))
        result.extend(data)
    return bytes(result),records


def install(prior,blob,core,module,output):
    surface=copy.deepcopy(prior['room_surfaces'])
    if surface.get('items'):raise ValueError('Surface item readers already installed')
    if not surface.get('secondary_owners'):raise ValueError('Surface items require complete texture consumers')
    equipment=copy.deepcopy(prior['equipment_resources'])
    at=equipment['blob_offset'];size=equipment['bytes'];packet=bytearray(blob[at:at+size])
    if (equipment['ram']!=0x804A3000 or size!=0x12000 or
            sha256(packet)!=equipment['sha256'] or zlib.crc32(packet)!=equipment['crc32']):
        raise ValueError('Changed complete resident equipment packet')
    boot_at=BOOT-equipment['ram'];boot_end=BOOT_END-equipment['ram']
    if any(packet[boot_at:boot_end]) or packet[boot_end:boot_end+16]!=bytes.fromhex('AF48C0DE')*4:
        raise ValueError('Surface bootstrap overlaps parent metadata or its guard')
    category=equipment['item_categories'];compiled=category['code']
    if (compiled['symbols']['af_v3_equipment_category']!=HOOKS[1][2] or
            sha256(packet[category['code_offset']:category['code_offset']+compiled['bytes']])!=compiled['sha256'] or
            any(prior['furniture_items']['code']['symbols']['af_v3_item_'+kind]!=target
                for kind,_,target in (HOOKS[0],HOOKS[2]))):
        raise ValueError('Changed complete predecessor item dispatch')
    # Native floor and wallpaper categories both use 12. Check actual tables,
    # including their pointers and complete bounds, not only source comments.
    pointers=struct.unpack_from('>3I',core,0x8010B334-CODE_RAM+6*4)
    if (pointers[1]-pointers[0],pointers[2]-pointers[1])!=(64,64) or any(
            core[p-CODE_RAM:p-CODE_RAM+64]!=bytes([12])*64 for p in pointers[:2]):
        raise ValueError('Changed complete native surface category tables')
    table,rows=metadata(surface['rows'])
    code,compiled=compile_part('surface_items',output/'surface_items')
    resource=bytearray(SIZE);resource[:len(code)]=code
    resource[TABLE:TABLE+len(table)]=table
    resource[-16:]=struct.pack('>4I',*([GUARD]*4))
    blob.extend(bytes(-len(blob)%16));resource_at=len(blob)
    blob.extend(resource);vrom=BLOB+resource_at;crc=zlib.crc32(resource)
    boot,boot_code=compile_part('surface_bootstrap',output/'surface_bootstrap',defines=(
        f'AF_SURFACE_ITEMS_VROM=0x{vrom:X}u',f'AF_SURFACE_ITEMS_CRC=0x{crc:X}u'))
    if len(boot)>boot_end-boot_at:raise ValueError('Surface loader exceeds checked existing reservation')
    packet[boot_at:boot_at+len(boot)]=boot
    blob[at:at+size]=packet
    hooks=[]
    for kind,address,old in HOOKS:
        owner,base=(module,MODULE_RAM) if address>=MODULE_RAM else (core,CODE_RAM)
        start=address-base;before=struct.pack('>2I',jump(old),0)
        target=compiled['symbols']['af_v3_surface_item_'+kind]
        if owner[start:start+8]!=before or compiled['symbols']['af_surface_prior_'+kind]!=old:
            raise ValueError('Unbound native surface item entry')
        after=struct.pack('>2I',jump(target),0);owner[start:start+8]=after
        hooks.append(dict(kind=kind,address=address,prior=old,target=target,before=before.hex(),after=after.hex()))
    item_report=dict(format='AFV3-SURFACE-ITEMS-1',ram=RAM,bytes=SIZE,blob_offset=resource_at,
        vrom=vrom,crc32=crc,sha256=sha256(resource),code=compiled,rows=rows,
        table_offset=TABLE,table_bytes=len(table),table_sha256=sha256(table),
        bootstrap=dict(ram=BOOT,offset=boot_at,capacity=boot_end-boot_at,code=boot_code),
        hooks=hooks,names_and_prices_installed=True,native_category=12,
        enabled_items=0,additional_resident_bytes=SIZE,additional_scene_bytes=0,
        saved_format_changed=False,saved_profile_changed=False,
        application_and_persistence_installed=False,native_execution_tested=False)
    equipment.update(sha256=sha256(packet),crc32=zlib.crc32(packet),surface_bootstrap=item_report['bootstrap'])
    surface['items']=item_report
    surface['additional_resident_bytes']+=SIZE
    surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return {},dict(room_surfaces=surface,equipment_resources=equipment)
