"""Checked optional surface metadata, catalogue packing, and resource checksums."""
import copy
import struct
import zlib

from aflib import by_vrom,sha256
from v3_asset_loader import BLOB,MODULE,MODULE_RAM,ROOT,compile_part
from v3_catalogue import VROM as CAT_VROM,RAM as CAT_RAM
from v3_surface_items import RAM,BOOT,BOOT_END

SOURCES=('tools/v3_surface_selection.py','tools/v3_surface_runtime.py',
    'tools/v3_optional_composition.py','tools/v3_browser_composition.py',
    'tools/v3_furniture_install.py','tools/v3_password_acquisition.py','tools/v3_harvest_acquisition.py',
    'overlays/v3/surface_bootstrap.c','overlays/v3/startup.c')


def profile(rows):
    result=bytearray(64)
    for row in rows:
        item=int(row['item_id'],16);kind=(item>>8)-0x26;index=item&255
        if kind not in (0,1) or not 73<=index<78:raise ValueError('Unregistered surface saved identity')
        at=kind*32+(index>>3);mask=1<<(index&7)
        if result[at]&mask:raise ValueError('Duplicate surface saved identity')
        result[at]|=mask
    return bytes(result)


def ready(surface):
    for stage in ('application','save','menu','scoring','sound','stock'):
        if not surface.get(stage):raise ValueError('Surface selection lacks '+stage)
    stock=surface['stock'];result={r['id'] for g in stock['resources'] for r in g['imports']}
    for row in stock.get('passwords',[]):
        if (row['id'] in result or row.get('group')!=16 or
                row.get('ordinary_stock') is not False or
                row.get('catalogue_orderable') is not False or
                not row.get('password_acquisition',{}).get('native_delivery_installed')):
            raise ValueError('Incomplete password-only surface acquisition')
        result.add(row['id'])
    for row in stock.get('harvest',[]):
        acquisition=row.get('harvest_acquisition',{})
        if (row['id'] in result or row.get('group')!=20 or row.get('ordinary_stock') is not False or
                row.get('catalogue_orderable') is not False or not acquisition.get('native_delivery_installed') or
                acquisition.get('destination_item')!=row['item_id'] or not acquisition.get('dependencies')):
            raise ValueError('Incomplete source Harvest surface acquisition')
        result.add(row['id'])
    pending={r['id']:r['dependency'] for r in stock['pending']}
    if (result&pending.keys() or result|pending.keys()!={r['id'] for r in surface['rows']} or
            not stock['selected_only'] or surface['save']['format_version']!=4):
        raise ValueError('Incomplete selected surface dependencies')
    return result,pending


def options(blob,report):
    surface=report.get('room_surfaces',{});selection=surface.get('optional_selection')
    if selection is None:return {}
    enabled,pending=ready(surface);items=surface['items'];start=items['blob_offset']
    packet=blob[start:start+items['bytes']]
    if (selection.get('format')!='AFV3-SURFACE-SELECTION-1' or
            selection.get('web_patcher_enabled') is not False or selection.get('playable_handoff') is not False or
            selection.get('identities')!=sorted(enabled) or selection.get('pending')!=pending or
            sha256(packet)!=items['sha256'] or zlib.crc32(packet)!=items['crc32']):
        raise ValueError('Changed complete optional surface packet/contract')
    source={r['id']:r for r in surface['rows']};result={}
    for row in items['rows']:
        at=row['offset'];record=packet[at:at+24];origin=source[row['id']]
        active=row['id'] in enabled
        if (len(record)!=24 or sha256(record)!=row['record_sha256'] or
                struct.unpack_from('>HHI',record)!=(int(row['item_id'],16),row['price_word'],int(active)) or
                row['enabled']!=active or row['item_id']!=origin['destination_item_id'] or
                record[8:]!=row['name'].encode('ascii').ljust(16,b' ')):
            raise ValueError('Changed complete surface selection binding')
        if active:
            acquisition=next((r['harvest_acquisition'] for r in surface['stock'].get('harvest',[])
                if r['id']==row['id']),None)
            result[row['id']]=dict(id=row['id'],name=row['name'],kind=origin['kind'],
                item_id=row['item_id'],dependencies=acquisition['dependencies'] if acquisition else [],enable_offset=start+at+4,
                enable_bytes=4,enable_ram=RAM+at+4)
    if set(result)!=enabled or profile(result.values()).hex()!=selection['profile_hex']:
        raise ValueError('Incomplete surface selection profile')
    return result


def checksum_fields(image,report):
    """Read-only CRC words; composition never changes instruction immediates."""
    surface=report.get('room_surfaces',{})
    if not surface.get('optional_selection'):return []
    files=by_vrom(image);blob=files[BLOB];module=files[MODULE]
    items=surface['items'];equipment=report['equipment_resources']
    boot=items['bootstrap']['code'];startup=report['startup']
    ep=blob.pstart+equipment['blob_offset'];sp=blob.pstart+items['blob_offset']
    fields=((ep+boot['symbols']['af_v3_surface_crc_expected']-equipment['ram'],sp,items['bytes']),
        (module.pstart+startup['symbols']['af_v3_equipment_crc_expected']-MODULE_RAM,ep,equipment['bytes']))
    result=[]
    for at,start,size in fields:
        if at&3 or int.from_bytes(image[at:at+4],'big')!=zlib.crc32(image[start:start+size]):
            raise ValueError('Changed optional surface checksum data field')
        result.append(dict(offset=at,before=image[at:at+4].hex(),start=start,length=size))
    return result


def table_writes(image,report,enabled):
    surface=report.get('room_surfaces',{})
    if not surface.get('optional_selection'):return [],{}
    files=by_vrom(image);items=surface['items'];writes=[];receipt={}
    for row in surface['menu']['tables']:
        before=files[BLOB].pstart+items['blob_offset']+row['offset']
        data=image[before:before+row['bytes']];original=row['imports']
        selected=[r for r in original if 'GAFE01-r0/item/'+r['source_item_id'] in enabled]
        expected=struct.pack('>'+str(row['capacity'])+'H',*range(64),
            *(r['index'] for r in original),*([0]*(row['capacity']-64-len(original))))
        if data!=expected or sha256(data)!=row['sha256'] or row['rows']!=64+len(original):
            raise ValueError('Changed complete surface catalogue source table')
        after=struct.pack('>'+str(row['capacity'])+'H',*range(64),
            *(r['index'] for r in selected),*([0]*(row['capacity']-64-len(selected))))
        count=files[CAT_VROM].pstart+row['descriptor']-CAT_RAM+4
        if image[count:count+4]!=struct.pack('>I',row['rows']):raise ValueError('Changed surface catalogue count')
        for at,old,new,purpose in ((before,data,after,'ordering'),
                (count,struct.pack('>I',row['rows']),struct.pack('>I',64+len(selected)),'iteration/completion count')):
            if old!=new:writes.append(dict(offset=at,before=old.hex(),after=new.hex(),purpose='selected '+row['kind']+' '+purpose))
        receipt[row['kind']]=selected
    return writes,receipt


def update_report(image,blob,report,selection,tables):
    surface=report['room_surfaces'];items=surface['items'];equipment=report['equipment_resources']
    packet=blob[items['blob_offset']:items['blob_offset']+items['bytes']]
    ep=blob[equipment['blob_offset']:equipment['blob_offset']+equipment['bytes']]
    items.update(sha256=sha256(packet),crc32=zlib.crc32(packet))
    items['table_sha256']=sha256(packet[items['table_offset']:items['table_offset']+items['table_bytes']])
    for row in items['rows']:
        at=row['offset'];row['enabled']=row['id'] in selection['enabled']
        row['record_sha256']=sha256(packet[at:at+24])
    items['enabled_items']=sum(r['enabled'] for r in items['rows'])
    for row in surface['menu']['tables']:
        row['imports']=tables[row['kind']];row['rows']=64+len(row['imports'])
        row['sha256']=sha256(packet[row['offset']:row['offset']+row['bytes']])
    report['catalogue']['surface_menu']['tables']=copy.deepcopy(surface['menu']['tables'])
    for key in ('profile_hex','profile_sha256'):
        surface['optional_selection'][key]=selection['surface_'+key]
    surface['optional_selection']['selected_identities']=[r['id'] for r in items['rows'] if r['enabled']]
    boot=items['bootstrap'];at=boot['ram']-equipment['ram'];code=boot['code']
    code['sha256']=sha256(ep[at:at+code['bytes']])
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=copy.deepcopy(boot))
    startup=report['startup'];module=by_vrom(image)[MODULE].extract(image)
    at=startup['symbols']['af_v3_startup']-MODULE_RAM
    startup['sha256']=sha256(module[at:at+startup['bytes']])


def install(base,prior,blob,output):
    if prior['room_surfaces'].get('optional_selection'):
        route='harvest' if prior['room_surfaces']['stock'].get('passwords') else 'passwords'
        return promote_acquisition(base,prior,blob,output,route=route)
    surface=copy.deepcopy(prior['room_surfaces']);enabled,pending=ready(surface)
    if surface.get('optional_selection'):raise ValueError('Surface optional selections already installed')
    files=by_vrom(base);items=surface['items'];start=items['blob_offset']
    packet=bytearray(blob[start:start+items['bytes']])
    if sha256(packet)!=items['sha256'] or zlib.crc32(packet)!=items['crc32']:
        raise ValueError('Changed surface packet before optional selection')
    for row in items['rows']:
        at=row['offset']
        if row['enabled'] or sha256(packet[at:at+24])!=row['record_sha256']:
            raise ValueError('Changed disabled surface metadata')
        row['enabled']=row['id'] in enabled;struct.pack_into('>I',packet,at+4,int(row['enabled']))
        row['record_sha256']=sha256(packet[at:at+24])
    cat=copy.deepcopy(prior['catalogue']);data=bytearray(files[CAT_VROM].extract(base))
    if sha256(data)!=cat['output_sha256']:raise ValueError('Changed catalogue before surface selections')
    for row in surface['menu']['tables']:
        at=row['offset'];pos=row['descriptor']-CAT_RAM
        if sha256(packet[at:at+row['bytes']])!=row['sha256'] or struct.unpack_from('>2I',data,pos)!=(row['ram'],64):
            raise ValueError('Changed surface catalogue predecessor')
        row['available_imports']=copy.deepcopy(row['imports'])
        row['imports']=[r for r in row['imports'] if 'GAFE01-r0/item/'+r['source_item_id'] in enabled]
        values=list(range(64))+[r['index'] for r in row['imports']];row['rows']=len(values)
        packed=struct.pack('>'+str(row['capacity'])+'H',*values,*([0]*(row['capacity']-len(values))))
        packet[at:at+len(packed)]=packed;row['sha256']=sha256(packed)
        struct.pack_into('>I',data,pos+4,row['rows'])
    cat['surface_menu']['tables']=copy.deepcopy(surface['menu']['tables']);cat['output_sha256']=sha256(data)
    equipment=copy.deepcopy(prior['equipment_resources']);ea=equipment['blob_offset']
    ep=bytearray(blob[ea:ea+equipment['bytes']]);ba=BOOT-equipment['ram'];be=BOOT_END-equipment['ram']
    if sha256(ep)!=equipment['sha256']:raise ValueError('Changed complete equipment startup packet')
    crc=zlib.crc32(packet)
    code,compiled=compile_part('surface_bootstrap',output/'surface_bootstrap',defines=(
        'AF_V3_EDITABLE_CHECKSUMS=1',f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',
        f'AF_SURFACE_ITEMS_CRC=0x{crc:X}u',f'AF_SURFACE_ITEMS_BYTES=0x{items["bytes"]:X}u'))
    field=compiled['symbols']['af_v3_surface_crc_expected']-BOOT
    if len(code)>be-ba or field<0 or struct.unpack_from('>I',code,field)[0]!=crc:
        raise ValueError('Invalid editable surface startup CRC')
    ep[ba:be]=code+bytes(be-ba-len(code));blob[ea:ea+len(ep)]=ep;blob[start:start+len(packet)]=packet
    items.update(sha256=sha256(packet),crc32=crc,enabled_items=len(enabled),additional_resident_bytes=0,
        table_sha256=sha256(packet[items['table_offset']:items['table_offset']+items['table_bytes']]))
    items['bootstrap']['code']=compiled
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=items['bootstrap'])
    selected=[r for r in items['rows'] if r['enabled']];bits=profile(selected)
    surface['optional_selection']=dict(format='AFV3-SURFACE-SELECTION-1',identities=sorted(enabled),
        pending=pending,profile_hex=bits.hex(),profile_sha256=sha256(bits),experimental=True,
        web_patcher_enabled=False,playable_handoff=False)
    surface['menu']['surface_options_enabled']=surface['save']['surface_options_enabled']=True
    surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return {CAT_VROM:bytes(data)},dict(room_surfaces=surface,catalogue=cat,equipment_resources=equipment,
        saved_format_changed=False)


def promote_passwords(base,prior,blob,output):
    """Admit every prepared HomePage surface without fabricating shop stock."""
    return promote_acquisition(base,prior,blob,output,route='passwords')


def promote_acquisition(base,prior,blob,output,*,route):
    """Admit a complete source reward category using unchanged surface readers."""
    del output # Existing code and complete artwork are unchanged.
    from v3_furniture_pipeline import Source
    from v3_surface_stock import list_items
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    if route=='passwords':
        from v3_password_acquisition import checked
        group=16
    elif route=='harvest':
        from v3_harvest_acquisition import checked
        group=20
    else:raise ValueError('Unsupported source surface admission category')
    binding=checked(source,base,prior)
    if binding is None:raise ValueError('Surface admission requires complete installed '+route+' delivery')
    options(blob,prior)
    surface=copy.deepcopy(prior['room_surfaces']);stock=surface['stock']
    if stock.get(route):raise ValueError('Source surface category is already admitted')
    origins={r['id']:r for r in surface['rows']};admitted=[];pending=[]
    for row in stock['pending']:
        if row['group']!=group:pending.append(row);continue
        origin=origins[row['id']];donor=int(row['source_item_id'],16)
        data=source.raw(row['source_symbol']);ids=list_items(data,0)
        acquire=origin['acquisition']
        if (len(acquire)!=1 or acquire[0]['table_index']!=group or
                acquire[0]['symbol']!=row['source_symbol'] or len(data)%2 or
                not data.endswith(bytes(2)) or len(set(ids))!=len(ids) or ids.count(donor)!=1 or
                any(i>>8!=donor>>8 for i in ids) or sha256(data)!=row['source_sha256'] or
                row['item_id']!=origin['destination_item_id']):
            raise ValueError('Changed complete donor source surface acquisition')
        record=dict(row);record.pop('dependency')
        record.update(ordinary_stock=False,catalogue_orderable=False)
        if route=='passwords':
            if not binding['matrix'][donor]&4:raise ValueError('Missing source HomePage password permission')
            record['password_acquisition']=dict(route='homepage-surface',permission_mask=binding['matrix'][donor],
                native_delivery_installed=True,ordinary_gameplay_tested=False)
        else:
            from v3_harvest_acquisition import acquisition
            record['harvest_acquisition']=acquisition(binding,donor,row['source_symbol'])
            if record['harvest_acquisition']['destination_item']!=row['item_id']:
                raise ValueError('Source Harvest reward uses an unrelated surface identity')
        admitted.append(record)
    if len(admitted)!=2 or {r['kind'] for r in admitted}!={'floor','wall'}:
        raise ValueError('Incomplete donor source surface category')
    stock[route]=admitted;stock['pending']=pending
    enabled,remaining=ready(surface)
    files=by_vrom(base);items=surface['items'];start=items['blob_offset']
    packet=bytearray(blob[start:start+items['bytes']])
    for row in items['rows']:
        row['enabled']=row['id'] in enabled;struct.pack_into('>I',packet,row['offset']+4,int(row['enabled']))
        row['record_sha256']=sha256(packet[row['offset']:row['offset']+24])
    cat=copy.deepcopy(prior['catalogue']);data=bytearray(files[CAT_VROM].extract(base))
    if sha256(data)!=cat['output_sha256']:raise ValueError('Changed retained surface catalogue')
    for row in surface['menu']['tables']:
        at=row['offset'];pos=row['descriptor']-CAT_RAM
        if (sha256(packet[at:at+row['bytes']])!=row['sha256'] or
                struct.unpack_from('>2I',data,pos)!=(row['ram'],row['rows'])):
            raise ValueError('Changed retained surface catalogue table/count')
        row['imports']=[r for r in row['available_imports'] if 'GAFE01-r0/item/'+r['source_item_id'] in enabled]
        values=list(range(64))+[r['index'] for r in row['imports']];row['rows']=len(values)
        if len(values)>row['capacity']:raise ValueError('Source surfaces exceed their catalogue reservation')
        table=struct.pack('>'+str(row['capacity'])+'H',*values,*([0]*(row['capacity']-len(values))))
        packet[at:at+len(table)]=table;row['sha256']=sha256(table)
        struct.pack_into('>I',data,pos+4,row['rows'])
    cat['surface_menu']['tables']=copy.deepcopy(surface['menu']['tables']);cat['output_sha256']=sha256(data)
    equipment=copy.deepcopy(prior['equipment_resources']);ea=equipment['blob_offset']
    ep=bytearray(blob[ea:ea+equipment['bytes']]);boot=items['bootstrap'];code=boot['code']
    if sha256(ep)!=equipment['sha256']:raise ValueError('Changed retained surface startup packet')
    at=code['symbols']['af_v3_surface_crc_expected']-equipment['ram']
    if struct.unpack_from('>I',ep,at)[0]!=items['crc32']:
        raise ValueError('Changed retained surface startup CRC field')
    struct.pack_into('>I',ep,at,zlib.crc32(packet))
    offset=boot['ram']-equipment['ram'];code['sha256']=sha256(ep[offset:offset+code['bytes']])
    blob[ea:ea+len(ep)]=ep;blob[start:start+len(packet)]=packet
    items.update(sha256=sha256(packet),crc32=zlib.crc32(packet),enabled_items=len(enabled),
        table_sha256=sha256(packet[items['table_offset']:items['table_offset']+items['table_bytes']]))
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=copy.deepcopy(boot))
    if route=='harvest':
        h=equipment['harvest'];imports={r['id']:r for r in prior['furniture']['imports']}
        expected={'GAFE01-r0/item/'+f'{item:04X}' for item in binding['lists']['ftr_listHarvest']['items']}
        if not expected<=imports.keys() or any(not imports[key].get('harvest_acquisition') for key in expected):
            raise ValueError('Source Harvest admission requires all ten ordinary furniture records')
        h.update(reward_selection_installed=True,selectable=True,
            reward_choices=sorted(expected|{r['id'] for r in admitted}),dependencies=binding['dependencies'],
            pending=['ordinary conversation, hiding/arrival, reward delivery, and save/restart'])
    bits=profile([r for r in items['rows'] if r['enabled']])
    surface['optional_selection'].update(identities=sorted(enabled),pending=remaining,
        profile_hex=bits.hex(),profile_sha256=sha256(bits),
        ordinary_password_delivery_tested=False,ordinary_save_reload_tested=False)
    surface['optional_selection']['ordinary_'+route+'_delivery_tested']=False
    surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    updates=dict(room_surfaces=surface,catalogue=cat,equipment_resources=equipment,saved_format_changed=False)
    options(blob,dict(prior,**updates))
    return {CAT_VROM:bytes(data)},updates
