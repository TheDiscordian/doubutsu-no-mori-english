"""Connect additive surface catalogue lists without growing the submenu pool."""
import copy
import struct
import zlib

from aflib import by_vrom,sha256
from v3_asset_loader import ROOT,compile_part
from v3_catalogue import VROM,RELOC,RAM as CAT_RAM
from v3_import_storage import jump
from v3_npc_clothing import guard_incoming
from v3_npc_draw import relocation_offsets
from v3_surface_items import RAM,BOOT,BOOT_END

CODE=0x3000
TABLES=(('wall',0x808AF7AC,0x808AF254,0x3490),('floor',0x808AF7B4,0x808AF2D4,0x3400))
BIT_SHA='d281e91c4cea05161a214bed028f4929656e6b4ce57ab7a351e6552a167acf13'
SOURCES=('tools/v3_surface_menu.py','overlays/v3/surface_menu.c','overlays/v3/surface_menu.ld')


def patch_catalogue(data,reloc,report,menu):
    """Apply to the current or freshly rebuilt catalogue before its native relocation."""
    result=bytearray(data);fixed=bytearray(reloc)
    count=struct.unpack_from('>I',reloc,16)[0]
    entries=list(struct.unpack_from('>'+str(count)+'I',reloc,20))
    if any(reloc[20+count*4:-4]):raise ValueError('Changed catalogue relocation padding')
    slots={w&0xFFFFFF:w for w in entries}
    entry=report['code']['symbols']['af_v3_catalogue_bit'];at=entry-CAT_RAM
    if sha256(data[at:at+84])!=BIT_SHA:
        raise ValueError('Changed complete catalogue ownership predecessor')
    guard_incoming(data,14048,CAT_RAM,[(at,16)])
    if any(a in slots for a in range(at,at+16,4)):
        raise ValueError('Catalogue ownership bridge overlaps relocations')
    # Pass the actual relocated native function, including its original debug
    # behaviour. Surface bits never enter that native eight-byte array.
    native=0x808A931C;target=menu['code']['symbols']['af_v3_surface_catalogue_bit']
    after=struct.pack('>4I',0x3C060000|((native+0x8000)>>16),
        0x24C60000|(native&65535),jump(target),0)
    result[at:at+16]=after
    entries.extend((0x45000000|at,0x46000000|(at+4)))
    patches=[dict(address=entry,before=data[at:at+16].hex(),after=after.hex())]
    removed=[]
    for row in menu['tables']:
        pos=row['descriptor']-CAT_RAM;table=row['native_table'];n=row['rows']
        if (data[pos:pos+8]!=struct.pack('>2I',table,64) or
                slots.get(pos)!=0x42000000|pos or
                data[table-CAT_RAM:table-CAT_RAM+128]!=struct.pack('>64H',*range(64)) or
                not 64<=n<=69):
            raise ValueError('Changed complete original surface catalogue descriptor/order')
        changed=struct.pack('>2I',row['ram'],n);result[pos:pos+8]=changed
        entries.remove(slots[pos]);removed.append(slots[pos])
        patches.append(dict(address=row['descriptor'],before=data[pos:pos+8].hex(),after=changed.hex()))
    if len(entries)!=count:raise ValueError('Surface catalogue unexpectedly grows relocation storage')
    fixed[20:20+count*4]=struct.pack('>'+str(count)+'I',*entries)
    relocation_offsets(fixed,len(result))
    updated=copy.deepcopy(report)
    updated.update(output_sha256=sha256(result),relocation_sha256=sha256(fixed),
        surface_menu=dict(format='AFV3-SURFACE-CATALOGUE-1',patches=patches,
            removed_relocations=removed,added_relocations=[0x45000000|at,0x46000000|(at+4)],
            predecessor_sha256=BIT_SHA,tables=copy.deepcopy(menu['tables']),
            permanent_code=menu['code']))
    code=updated['code'];start=code['symbols']['af_v3_catalogue_bit']-CAT_RAM
    code.update(compiled_sha256=code.get('compiled_sha256',code['sha256']),
        sha256=sha256(result[start:start+code['bytes']]))
    return bytes(result),bytes(fixed),updated


def retain_catalogue(prior,base,data,reloc,report):
    menu=prior.get('room_surfaces',{}).get('menu')
    if not menu:return data,reloc,report
    from v3_asset_loader import BLOB
    blob=by_vrom(base)[BLOB].extract(base);items=prior['room_surfaces']['items']
    packet=blob[items['blob_offset']:items['blob_offset']+items['bytes']]
    if sha256(packet)!=items['sha256']:raise ValueError('Changed surface menu packet')
    for row in menu['tables']:
        if sha256(packet[row['offset']:row['offset']+row['bytes']])!=row['sha256']:
            raise ValueError('Changed retained surface catalogue table')
    return patch_catalogue(data,reloc,report,menu)


def install(base,prior,blob,output):
    surface=copy.deepcopy(prior['room_surfaces']);items=surface['items']
    if not surface.get('save') or surface.get('menu'):
        raise ValueError('Surface menus require format-4 persistence and no installed menu stage')
    at=items['blob_offset'];packet=bytearray(blob[at:at+items['bytes']])
    if (len(packet)!=0x4000 or sha256(packet)!=items['sha256'] or
            zlib.crc32(packet)!=items['crc32'] or any(packet[CODE:0x3FF0])):
        raise ValueError('Changed surface packet or occupied menu reservation')
    files=by_vrom(base);data=files[VROM].extract(base);reloc=files[RELOC].extract(base)
    cat=prior['catalogue']
    if sha256(data)!=cat['output_sha256'] or sha256(reloc)!=cat['relocation_sha256']:
        raise ValueError('Changed complete current catalogue')
    code,compiled=compile_part('surface_menu',output/'surface_menu')
    if (compiled['symbols']!={'af_v3_surface_catalogue_bit':RAM+CODE,'af_v3_catalogue_owned':0x80469AD4}
            or len(code)>0x400):raise ValueError('Changed surface menu bindings/bounds')
    packet[CODE:CODE+len(code)]=code
    rows=[]
    for kind,descriptor,old,offset in TABLES:
        candidates=sorted((r for r in surface['rows'] if r['kind']==kind),key=lambda r:r['catalogue_position'])
        ids=[int(r['destination_item_id'],16)&255 for r in candidates]
        if len(ids)!=5 or len(set(ids))!=5:raise ValueError('Incomplete surface catalogue category')
        # Inactive imports remain outside the counted list. The reserved tail
        # provides canonical rows for the private composer's later selections.
        enabled=[r for r in candidates if any(i['item_id']==r['destination_item_id'] and
            struct.unpack_from('>I',packet,i['offset']+4)[0]==1 for i in items['rows'])]
        if enabled:raise ValueError('Initial surface menu stage requires disabled import records')
        table=struct.pack('>69H',*range(64),*ids);packet[offset:offset+len(table)]=table
        rows.append(dict(kind=kind,descriptor=descriptor,native_table=old,ram=RAM+offset,
            offset=offset,bytes=len(table),sha256=sha256(table),rows=64,capacity=69,
            native_rows=64,imports=[dict(source_item_id=r['source_item_id'],
                item_id=r['destination_item_id'],index=int(r['destination_item_id'],16)&255,
                donor_position=r['catalogue_position']) for r in candidates]))
    menu=dict(format='AFV3-SURFACE-MENU-1',code=compiled,tables=rows,
        additional_resident_bytes=0,additional_menu_bytes=0,native_execution_tested=False,
        ordinary_inventory_tested=False,surface_options_enabled=False)
    data,reloc,cat=patch_catalogue(data,reloc,cat,menu)
    equipment=copy.deepcopy(prior['equipment_resources']);ea=equipment['blob_offset']
    ep=bytearray(blob[ea:ea+equipment['bytes']]);ba=BOOT-equipment['ram'];be=BOOT_END-equipment['ram']
    oldboot=items['bootstrap']['code']
    if (sha256(ep)!=equipment['sha256'] or zlib.crc32(ep)!=equipment['crc32'] or
            sha256(ep[ba:ba+oldboot['bytes']])!=oldboot['sha256'] or any(ep[ba+oldboot['bytes']:be])):
        raise ValueError('Changed surface startup predecessor')
    crc=zlib.crc32(packet)
    boot,bc=compile_part('surface_bootstrap',output/'surface_bootstrap',defines=(
        f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',f'AF_SURFACE_ITEMS_CRC=0x{crc:X}u',
        f'AF_SURFACE_ITEMS_BYTES=0x{len(packet):X}u'))
    if len(boot)>be-ba:raise ValueError('Surface menu bootstrap exceeds reservation')
    ep[ba:be]=boot+bytes(be-ba-len(boot));blob[ea:ea+len(ep)]=ep;blob[at:at+len(packet)]=packet
    items.update(sha256=sha256(packet),crc32=crc,additional_resident_bytes=0)
    items['bootstrap']['code']=bc
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=items['bootstrap'])
    surface['menu']=menu;surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return {VROM:data,RELOC:reloc},dict(room_surfaces=surface,catalogue=cat,
        equipment_resources=equipment,saved_format_changed=False)
