"""Repair installed paged readers without reconverting their retained artwork."""
import struct
import zlib

from aflib import sha256,u32
from v3_asset_loader import ROOT,compile_part
from v3_import_storage import jump

SOURCES=('tools/v3_paged_dma.py','overlays/v3/paged_dma.c','overlays/v3/paged_dma.ld',
    'overlays/v3/resource_dma.h','overlays/v3/scenery.c','overlays/v3/tree_effects.c')


def install(base,blob,equipment,records,output):
    scene=equipment.get('scenery',{})
    if not scene.get('families') or scene.get('physical_dma'):return []
    start=scene['blob_offset'];size=scene['bytes'];ram=scene['ram']
    code=bytearray(blob[start:start+size]);effects=scene.get('tree_effects')
    if (ram!=0x8077B000 or size!=12596 or sha256(code)!=scene['sha256'] or
            not effects or not effects.get('installed')):
        raise ValueError('Changed complete paged-resource repair inputs')
    reservation=scene['reservations'][0]
    limit=min(scene['additional_fixed_resident_bytes'],
        reservation['blob_offset']+reservation['bytes']-start)
    # Older code remains in the owned cartridge reservation beyond the active
    # image. Preserve it; place the adapter only in a checked zero-filled span.
    at=next((i for i in range((size+15)&~15,limit-255,16)
        if not any(blob[start+i:start+i+256])),None)
    if at is None:raise ValueError('No checked padding for paged DMA adapter')
    adapter,compiled=compile_part('paged_dma',output/'paged_dma',link_symbols={'AF_RESOURCE_DMA_RAM':ram+at})
    end=at+len(adapter)
    if (end>scene['additional_fixed_resident_bytes'] or
            start+end>reservation['blob_offset']+reservation['bytes'] or any(blob[start+at:start+end])):
        raise ValueError('Paged DMA adapter overlaps retained code')
    target=compiled['symbols']['af_v3_paged_dma'];changes=[]
    def bind(data,base_ram,expected):
        found=[i for i in range(0,len(data),4) if u32(data,i)==jump(0x80026B44,link=True)]
        if [base_ram+i for i in found]!=expected:raise ValueError('Changed paged DMA call sites')
        for i in found:
            before=u32(data,i);after=jump(target,link=True);struct.pack_into('>I',data,i,after)
            changes.append(dict(address=base_ram+i,before=before,after=after))
    bind(code,ram,[0x8077B0C8,0x8077B22C,0x8077B248])
    code.extend(blob[start+size:start+at]);code.extend(adapter)
    boot=scene['bootstrap'];flags=[f[2:] for f in boot['flags'] if f.startswith('-D')]
    flags=[f'AF_SCENERY_BYTES={len(code)}u' if f.startswith('AF_SCENERY_BYTES=') else
        f'AF_SCENERY_CRC=0x{zlib.crc32(code):X}u' if f.startswith('AF_SCENERY_CRC=') else f for f in flags]
    raw_boot,new_boot=compile_part('scenery_bootstrap',output/'scenery_dma_bootstrap',defines=tuple(flags))
    boot_at=equipment['blob_offset']+0x804ADC90-equipment['ram']
    # Every caller keeps its original entry address; only transfer length and
    # expected CRC change in the complete existing lazy-loading gate.
    if (len(raw_boot)!=boot['bytes'] or new_boot['symbols']!=boot['symbols'] or
            sha256(blob[boot_at:boot_at+boot['bytes']])!=boot['sha256']):
        raise ValueError('Paged DMA repair changes the existing bootstrap ABI')
    blob[boot_at:boot_at+len(raw_boot)]=raw_boot
    blob[start:start+len(code)]=code
    scene.update(bytes=len(code),sha256=sha256(code),crc32=zlib.crc32(code),bootstrap=new_boot)
    scene['code'].update(bytes=len(code),sha256=sha256(code))
    scene['code']['symbols'].update(af_v3_paged_dma=target,af_scenery_dma=target)
    scene['code'].setdefault('link_symbols',{})['af_scenery_dma']=target
    scene['tree_states']['shared_packet_bytes']=len(code)
    reservation['used_bytes']=start+len(code)-reservation['blob_offset']
    p=effects['packet'];raw=bytearray(base[p['physical']:p['physical']+p['bytes']]);old=p['sha256']
    n=effects['code']['bytes'];part=bytearray(raw[:n])
    if sha256(raw)!=old or sha256(part)!=effects['code']['sha256']:
        raise ValueError('Changed complete paged tree-effect packet')
    bind(part,p['ram'],[0x80780254]);raw[:n]=part
    effects['code'].update(sha256=sha256(part))
    effects['code']['symbols']['af_tree_dma']=target
    effects['code']['link_symbols']['af_tree_dma']=target
    effects['bindings']['af_tree_dma']=target
    p.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    field=equipment.get('carried_items',{}).get('field_creatures')
    if field:
        if field['packet']['sha256']!=old or field['packet']['id']!=p['id']:
            raise ValueError('Changed shared field/tree packet ownership')
        field['packet']=dict(p)
    record=next(r for r in records if r['id']==p['id'])
    if record['sha256']!=old:raise ValueError('Changed paged tree-effect physical ownership')
    record['sha256']=p['sha256']
    scene['physical_dma']=dict(code=compiled,ram=ram+at,patches=changes,
        source_marker=0x80000000,physical_reader=0x80026500,virtual_reader=0x80026B44,
        sources={name:sha256((ROOT/name).read_bytes()) for name in SOURCES})
    a=equipment['blob_offset'];module=blob[a:a+equipment['bytes']]
    equipment.update(sha256=sha256(module),crc32=zlib.crc32(module))
    return [(dict(record,previous_sha256=old),bytes(raw))]
