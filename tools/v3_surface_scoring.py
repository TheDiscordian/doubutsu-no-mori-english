"""Shared full-index surface weights and source-bound existing HRA themes."""
import copy
import struct
import zlib

from aflib import by_vrom,sha256
from v3_asset_loader import ROOT,compile_part
from v3_npc_clothing import guard_incoming
from v3_npc_draw import relocation_offsets
from v3_surface_items import RAM,BOOT,BOOT_END
import v3_hra as hra

SOURCES=('tools/v3_surface_scoring.py','tools/v3_furniture_install.py','tools/v3_surface_runtime.py')
ENTRY,START,END=0x809274F8,0x80927794,0x809277EC
FUNCTION_SHA='4a44355d60b5b276e18a985f681af7a166f9ad92721e26c1a5aaab1b5b255945'
TABLES=(('floor',0x809295D8,0x3600,'6589569d2c02995617d0b50a634ed2107e1af525da28bbf53f9ce8426f30b725'),
        ('wall',0x80929598,0x3800,'c309f7a72c36c348754f3625bc91de8b16b8e599f55d5a7a8d6daa24df75d52a'))


def tables(data,report,surface,source):
    weights=source.raw('mMkRm_birth_point_table')
    if len(weights)!=38*4 or sha256(weights)!=report['birth_extension']['donor_weights_sha256']:
        raise ValueError('Changed complete donor surface score weights')
    donor=struct.unpack('>38I',weights)
    at=report['birth_extension']['points_address']-hra.RAM
    native=data[at:at+23*4]
    if sha256(native)!=report['birth_extension']['points_sha256']:
        raise ValueError('Changed complete native acquisition weights')
    native=struct.unpack('>23I',native);out=[]
    for kind,address,offset,digest in TABLES:
        original=data[address-hra.RAM:address-hra.RAM+64]
        name='mMkRm_'+kind+'_from';birth=source.raw(name)
        if len(birth)!=67 or sha256(original)!=digest or any(v>=23 for v in original):
            raise ValueError('Changed complete surface birth table')
        # Complete original points are retained, including native lottery weight.
        values=[native[v] for v in original]+[0]*192;rows=[]
        for row in sorted((r for r in surface['rows'] if r['kind']==kind),key=lambda r:r['destination_index']):
            index=row['destination_index'];category=birth[row['source_index']]
            if not 73<=index<78 or category>=len(donor) or donor[category]>65535:
                raise ValueError('Invalid additive surface point record')
            values[index]=donor[category]
            rows.append(dict(item_id=row['destination_item_id'],source_item_id=row['source_item_id'],
                index=index,birth_category=category,points=values[index]))
        if len(rows)!=5:raise ValueError('Incomplete additive surface scoring category')
        table=struct.pack('>256H',*values)
        out.append((table,dict(kind=kind,offset=offset,ram=RAM+offset,bytes=len(table),
            sha256=sha256(table),source_symbol=name,source_sha256=sha256(birth),
            original_sha256=digest,imports=rows)))
    return out


def patch_owner(data,reloc,report,records,source):
    if sha256(data[ENTRY-hra.RAM:END-hra.RAM+12])!=FUNCTION_SHA:
        raise ValueError('Changed complete current HRA base evaluator')
    if [(r['kind'],r['ram']) for r in records]!=[('floor',0x804BF600),('wall',0x804BF800)]:
        raise ValueError('Surface weights escape fixed resident reservation')
    guard_incoming(data,hra.SECTIONS[0],hra.RAM,[(START-hra.RAM,END-START)])
    count=struct.unpack_from('>I',reloc,16)[0]
    entries=list(struct.unpack_from('>'+str(count)+'I',reloc,20))
    removed=[w for w in entries if START-hra.RAM<=w&0xFFFFFF<END-hra.RAM]
    if removed!=[0x45001DB8,0x45001DBC,0x46001DC4,0x46001DC8,0x45001DD8,0x46001DE0]:
        raise ValueError('Changed surface score pointer relocations')
    # The caller already supplies full home bytes. Bound each index before a
    # direct halfword weight load; keep the accumulated furniture score and
    # original leaf-function RA/stack/epilogue intact. No category-array growth.
    code=struct.pack('>22I',0x8FB80118,0x8FB90114,
        0x2F010100,0x10200005,0x00004025,0x0018C040,0x3C08804C,0x0308C021,0x9708F600,
        0x2F210100,0x10200005,0x00004825,0x0019C840,0x3C09804C,0x0329C821,0x9729F800,
        0x8FAE0108,0x00481021,0x00491021,0x8DCF0000,0x01E2C021,0xADD80000)
    changed=bytearray(data);at=START-hra.RAM;changed[at:at+len(code)]=code
    fixed=bytearray(reloc);keep=[w for w in entries if w not in removed]
    struct.pack_into('>I',fixed,16,len(keep));fixed[20:-4]=struct.pack('>'+str(len(keep))+'I',*keep)+bytes(len(fixed)-24-len(keep)*4)
    relocation_offsets(fixed,len(changed))
    result=copy.deepcopy(report);series=result['series'];begin=series['info_address']-hra.RAM
    original_info=data[begin:begin+series['count']*3];donor=source.raw('mMkRm_series_info')
    if sha256(original_info)!=series['resource_sha256']['af_v3_hra_series_info'] or len(donor)!=180:
        raise ValueError('Changed complete HRA theme definitions')
    mappings=[]
    source_indices={int(r['source_item_id'],16)&255:r['index'] for r in records[0]['imports']}
    if source_indices!={int(r['source_item_id'],16)&255:r['index'] for r in records[1]['imports']}:
        raise ValueError('HRA floor/wall pair reservations disagree')
    for key,adapter in series.items():
        if not isinstance(adapter,dict) or 'donor_wall_floor_index' not in adapter:continue
        idx=adapter['series'];source_index=adapter['donor_wall_floor_index']
        if source_index not in source_indices:continue
        target=source_indices[source_index];pos=begin+idx*3;expected=donor[idx*3:idx*3+3]
        if (adapter['matching_surfaces_installed'] or adapter['native_wall_floor_index']!=255 or
                data[pos:pos+3]!=expected[:2]+b'\xff' or expected[2]!=source_index):
            raise ValueError('Changed installed matching-surface adapter')
        changed[pos+2]=target
        adapter.update(native_wall_floor_index=target,matching_surfaces_installed=True)
        mappings.append(dict(name=key,series=idx,source_index=source_index,index=target,
            offset=pos,before=data[pos:pos+3].hex(),after=changed[pos:pos+3].hex()))
    if len(mappings)!=3:raise ValueError('Incomplete existing theme surface mappings')
    series['resource_sha256']['af_v3_hra_series_info']=sha256(changed[begin:begin+series['count']*3])
    receipt=dict(format='AFV3-SURFACE-SCORING-1',tables=records,themes=mappings,
        window=dict(address=START,bytes=len(code),before=data[at:at+len(code)].hex(),after=code.hex()),
        original_evaluator_sha256=FUNCTION_SHA,evaluator_sha256=sha256(changed[ENTRY-hra.RAM:END-hra.RAM+12]),
        removed_relocations=removed,native_execution_tested=False,saved_format_changed=False,
        additional_resident_bytes=0,additional_owner_bytes=0,
        pending_theme_categories=['complete Harvest furniture series','complete Mario furniture series'])
    result.update(output_sha256=sha256(changed),relocation_sha256=sha256(fixed),surface_scoring=receipt)
    return bytes(changed),bytes(fixed),result,receipt


def install(base,prior,blob,output,source):
    surface=copy.deepcopy(prior['room_surfaces']);items=surface['items']
    if not surface.get('menu') or surface.get('scoring'):
        raise ValueError('Surface scoring requires installed menu support and no previous scoring stage')
    files=by_vrom(base);data=files[hra.NEW_VROM].extract(base);reloc=files[hra.NEW_RELOC].extract(base)
    if sha256(data)!=prior['hra']['output_sha256'] or sha256(reloc)!=prior['hra']['relocation_sha256']:
        raise ValueError('Changed complete installed HRA owner')
    at=items['blob_offset'];packet=bytearray(blob[at:at+items['bytes']])
    if len(packet)!=0x4000 or sha256(packet)!=items['sha256'] or zlib.crc32(packet)!=items['crc32']:
        raise ValueError('Changed complete surface packet')
    resources=tables(data,prior['hra'],surface,source)
    for table,row in resources:
        start=row['offset'];end=start+len(table)
        if end>0x3FF0 or any(packet[start:end]):raise ValueError('Surface weights overlap existing storage')
        packet[start:end]=table
    data,reloc,hr,receipt=patch_owner(data,reloc,prior['hra'],[r for _,r in resources],source)
    equipment=copy.deepcopy(prior['equipment_resources']);ea=equipment['blob_offset']
    ep=bytearray(blob[ea:ea+equipment['bytes']]);ba=BOOT-equipment['ram'];be=BOOT_END-equipment['ram']
    if sha256(ep)!=equipment['sha256'] or zlib.crc32(ep)!=equipment['crc32']:
        raise ValueError('Changed equipment bootstrap packet')
    crc=zlib.crc32(packet)
    boot,bc=compile_part('surface_bootstrap',output/'surface_bootstrap',defines=(
        f'AF_SURFACE_ITEMS_VROM=0x{items["vrom"]:X}u',f'AF_SURFACE_ITEMS_CRC=0x{crc:X}u',
        f'AF_SURFACE_ITEMS_BYTES=0x{len(packet):X}u'))
    if len(boot)>be-ba:raise ValueError('Surface scoring bootstrap exceeds reservation')
    ep[ba:be]=boot+bytes(be-ba-len(boot));blob[ea:ea+len(ep)]=ep;blob[at:at+len(packet)]=packet
    items.update(sha256=sha256(packet),crc32=crc,additional_resident_bytes=0);items['bootstrap']['code']=bc
    equipment.update(sha256=sha256(ep),crc32=zlib.crc32(ep),surface_bootstrap=items['bootstrap'])
    surface['scoring']=receipt;surface['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return {hra.NEW_VROM:data,hra.NEW_RELOC:reloc},dict(room_surfaces=surface,hra=hr,
        equipment_resources=equipment,saved_format_changed=False)
