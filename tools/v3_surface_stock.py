"""Add complete surface stock categories while preserving selected-only goods."""
import copy
import struct
import zlib

from aflib import CODE_RAM,by_vrom,sha256
from v3_asset_loader import BLOB,ROOT,compile_part
from v3_surface_items import RAM,BOOT,BOOT_END
from v3_import_storage import jump

SOURCES=('tools/v3_surface_stock.py','tools/v3_surface_runtime.py','tools/v3_asset_loader.py',
    'tools/v3_furniture_install.py','overlays/v3/surface_stock.c',
    'overlays/v3/surface_stock.S','overlays/v3/surface_stock.ld')
GOODS=(('floor',3,0x11E4000,'24f48de5fe75950e7762069893e2c2508d9051412741e75245c5003945f6de4e'),
    ('wall',4,0x11E7000,'da47a324afaee86cfb8be5d3f5e4fb5ab53271c030c077637370a86a3f9be690'))
CONSUMERS=((0x800BF8E8,200,'840505b8bce6fad24e7363e8622b4fb3ad7324ddb71c966acb41b0d93e3252e3'),
    (0x800C05E0,164,'ffc07760b74ad3b15f3df40341f3214095e08bd5439fe33d664fbe3bedddb97d'),
    (0x800C0490,336,'c27da4d6fc695e19a0d065515278675e9469be8d8f2f398cbd06ea5a22b2dd66'))


def list_items(data,offset):
    values=[]
    while offset+2<=len(data):
        item=struct.unpack_from('>H',data,offset)[0];offset+=2
        if not item:return values
        values.append(item)
    raise ValueError('Unterminated complete surface stock list')


def goods(base,core,surface,source):
    resources=[];pending=[]
    for kind,category,vrom,digest in GOODS:
        old=by_vrom(base)[vrom].extract(base);address=0x8010DAA0+category*12
        if (len(old)!=192 or sha256(old)!=digest or
                struct.unpack_from('>3I',core,address-CODE_RAM)!=(vrom,vrom+192,0x6000094)):
            raise ValueError('Changed complete native surface stock resource/descriptor')
        pointers=struct.unpack_from('>11I',old,0x94);groups={};all_original=[]
        for group,pointer in enumerate(pointers):
            if not pointer:continue
            if pointer>>24!=6 or pointer&0xFFFFFF>=0x94:raise ValueError('Invalid original surface stock pointer')
            values=list_items(old[:0x94],pointer&0xFFFFFF);groups[group]=values;all_original+=values
        base_id=0x2600 if kind=='floor' else 0x2700
        if sorted(all_original)!=list(range(base_id,base_id+64)):
            raise ValueError('Native surface stock does not cover its 64 complete identities')
        imports=[]
        for row in (r for r in surface['rows'] if r['kind']==kind):
            if len(row['acquisition'])!=1:raise ValueError('Ambiguous complete surface acquisition')
            acquire=row['acquisition'][0];group=acquire['table_index'];name=acquire['symbol']
            data=source.raw(name);ids=list_items(data,0);donor=int(row['source_item_id'],16)
            if (len(data)%2 or not data.endswith(bytes(2)) or len(ids)!=len(set(ids)) or
                    ids.count(donor)!=1 or any(v>>8!=base_id>>8 for v in ids)):
                raise ValueError('Changed complete donor surface stock membership')
            item=int(row['destination_item_id'],16)
            record=dict(id=row['id'],item_id=row['destination_item_id'],source_item_id=row['source_item_id'],
                kind=kind,group=group,source_symbol=name,source_sha256=sha256(data))
            if group not in (0,1,2,3):
                record['dependency']='HomePage delivery' if group==16 else 'Harvest rewards' if group==20 else 'unimplemented acquisition category'
                pending.append(record);continue
            if group not in groups or item>>8!=base_id>>8 or not 73<=item&255<78:
                raise ValueError('Unregistered surface stock group/destination')
            imports.append(record)
        result=bytearray(old);lists=[]
        for group in sorted({r['group'] for r in imports}):
            rows=sorted((r for r in imports if r['group']==group),key=lambda r:r['item_id'])
            values=groups[group]+[int(r['item_id'],16) for r in rows];offset=len(result)
            result.extend(struct.pack('>'+str(len(values)+1)+'H',*values,0))
            struct.pack_into('>I',result,0x94+group*4,0x6000000+offset)
            lists.append(dict(group=group,offset=offset,original_items=groups[group],
                added_items=[r['item_id'] for r in rows],count=len(values)))
        result.extend(bytes(-len(result)%16))
        resources.append((bytes(result),dict(kind=kind,category=category,original_vrom=vrom,
            original_bytes=len(old),original_sha256=digest,descriptor=address,table_offset=0x94,
            descriptor_before=core[address-CODE_RAM:address-CODE_RAM+12].hex(),
            bytes=len(result),sha256=sha256(result),imports=imports,lists=lists,
            additional_temporary_bytes=len(result)-len(old))))
    if sum(len(r['imports']) for _,r in resources)!=6 or len(pending)!=4:
        raise ValueError('Incomplete current source acquisition categories')
    return resources,pending


def install(base,prior,blob,core,output,source):
    surface=copy.deepcopy(prior['room_surfaces']);items=surface['items']
    if not surface.get('sound') or surface.get('stock'):raise ValueError('Invalid surface stock stage')
    resources,pending=goods(base,core,surface,source);contracts=[]
    for address,size,digest in CONSUMERS:
        if sha256(core[address-CODE_RAM:address-CODE_RAM+size])!=digest:
            raise ValueError('Changed complete native surface stock consumer')
        contracts.append(dict(address=address,bytes=size,sha256=digest))
    at=items['blob_offset'];packet=bytearray(blob[at:at+items['bytes']])
    if len(packet)!=0x4000 or sha256(packet)!=items['sha256'] or zlib.crc32(packet)!=items['crc32']:
        raise ValueError('Changed complete resident surface packet')
    if any(packet[0x3E00:0x3FF0]):raise ValueError('Surface stock helper storage occupied')
    code,compiled=compile_part('surface_stock',output/'surface_stock',extra_sources=('overlays/v3/surface_stock.S',))
    if (len(code)>0x1F0 or compiled['symbols']['af_surface_prior_stock_list']!=0x804BFFD0 or
            compiled['symbols']['af_v3_surface_item_type']!=items['code']['symbols']['af_v3_surface_item_type'] or
            compiled['symbols']['af_surface_prior_shop_category']!=prior['shops']['code']['symbols']['af_v3_shop_category'] or
            sha256(blob[0x9C00:0x9C00+prior['shops']['code']['bytes']])!=prior['shops']['code']['sha256']):
        raise ValueError('Changed complete surface stock predecessor/bindings')
    packet[0x3E00:0x3E00+len(code)]=code;patches=[]
    for address,symbol in ((0x800C05E0,'af_v3_surface_shop_category'),(0x800BF8E8,'af_v3_surface_stock_list')):
        pos=address-CODE_RAM;before=bytes(core[pos:pos+8]);target=compiled['symbols'][symbol]
        after=struct.pack('>2I',jump(target),0);core[pos:pos+8]=after
        patches.append(dict(address=address,target=target,before=before.hex(),after=after.hex()))
    records=[]
    for data,row in resources:
        blob.extend(bytes(-len(blob)%16));start=len(blob);blob.extend(data);vrom=BLOB+start
        descriptor=struct.pack('>3I',vrom,vrom+len(data),0x6000000+row['table_offset'])
        core[row['descriptor']-CODE_RAM:row['descriptor']-CODE_RAM+12]=descriptor
        row.update(blob_offset=start,vrom=vrom,descriptor_after=descriptor.hex());records.append(row)
    equipment=copy.deepcopy(prior['equipment_resources']);ea=equipment['blob_offset']
    ep=bytearray(blob[ea:ea+equipment['bytes']]);ba=BOOT-equipment['ram'];be=BOOT_END-equipment['ram']
    if sha256(ep)!=equipment['sha256'] or zlib.crc32(ep)!=equipment['crc32']:
        raise ValueError('Changed complete equipment bootstrap')
    crc=zlib.crc32(packet)
    boot,bc=compile_part('surface_bootstrap',output/'surface_bootstrap',defines=(
        f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',f'AF_SURFACE_ITEMS_CRC=0x{crc:X}u',
        f'AF_SURFACE_ITEMS_BYTES=0x{len(packet):X}u'))
    if len(boot)>be-ba:raise ValueError('Surface stock bootstrap exceeds reservation')
    ep[ba:be]=boot+bytes(be-ba-len(boot));blob[ea:ea+len(ep)]=ep;blob[at:at+len(packet)]=packet
    items.update(sha256=sha256(packet),crc32=crc,additional_resident_bytes=0);items['bootstrap']['code']=bc
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=items['bootstrap'])
    surface['stock']=dict(format='AFV3-SURFACE-STOCK-1',code=compiled,code_offset=0x3E00,
        resources=records,pending=pending,consumer_patches=patches,native_consumers=contracts,
        additional_resident_bytes=0,max_additional_temporary_bytes=max(r['additional_temporary_bytes'] for r in records),
        selected_only=True,native_rng_and_rarity_preserved=True,native_execution_tested=False,
        ordinary_purchase_and_event_delivery_tested=False,saved_format_changed=False)
    surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return {},dict(room_surfaces=surface,equipment_resources=equipment,saved_format_changed=False)
