"""Install shared additive surface resources and native double-buffer readers."""
import struct

from aflib import by_vrom, sha256
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_furniture_pipeline import Source
from v3_npc_clothing import guard_incoming
from v3_npc_draw import relocation_offsets
from v3_room_surfaces import discover, checked_prepared, KINDS

SOURCES = ('tools/v3_surface_runtime.py','tools/v3_room_surfaces.py','tools/v3_registry.py',
    'tools/v3_furniture_install.py','tools/v3_asset_loader.py','overlays/v3/room_surfaces.c',
    'overlays/v3/surface_indoor.ld','overlays/v3/surface_shop.ld')
OWNERS = (
    (0x846860,0x8476A0,0x80951A70,0x154,'surface_indoor',
     ('2d9555a59b7129504a02f0c2c17bbf0011d4d45c4c520d203209d5b63d96b37f',
      '2229c4839bbfe18c03f25e1206abc9274e27071d5152b33c8a1d8fe64da6b503'),
     '5a527530d42df498724ff5df825f73dab3a968c7b816f0cb4add86e58cd72df7',
     (0x450001A0,0x460001AC,0x45000224,0x46000230,0x450002B8,0x460002C4,0x4500033C,0x46000348)),
    (0x84F180,0x8504F0,0x8095A3B0,0x164,'surface_shop',
     ('bdb67ecd8bbfc11ad75a1f9f5adad1600ebf6e8202bc13d2289f8064ebf8bcee',
      '670e94a5896bca9c22b1cb211ab0b17b0d00b68c6ffd91444f28fa08281244a6'),
     'da02472e3673d5592a799e050ecf92709bbe81365b1a932465e8687760c538d9',
     (0x450001B0,0x460001BC,0x45000234,0x46000240,0x450002C8,0x460002D4,0x4500034C,0x46000358)),
)


def patch_owner(data, reloc, owner, code, compiled):
    vrom, rel_vrom, ram, start, part, digests, rel_hash, removed = owner
    windows=[(start,0x118),(start+0x118,0x118)]
    if (sha256(reloc)!=rel_hash or
            [sha256(data[a:a+n]) for a,n in windows]!=list(digests)):
        raise ValueError('Changed complete native surface reader or relocation table')
    locations=relocation_offsets(reloc,len(data))
    guard_incoming(data,struct.unpack_from('>I',reloc)[0],ram,windows)
    expected={'af_v3_surface_floor':ram+start,'af_v3_surface_wall':ram+start+0x118,
        'af_surface_dma':0x80026B44}
    if (compiled['symbols']!=expected or not 0x118<len(code)<=0x230 or
            compiled['bytes']!=len(code) or compiled['sha256']!=sha256(code)):
        raise ValueError('Surface reader escapes original complete function storage')
    # Only the fixed engine DMA target may use an absolute call address.
    # Internal branches remain PC-relative when the actor is relocated.
    for (word,) in struct.iter_unpack('>I',code):
        if word>>26 in (2,3) and ((word&0x3FFFFFF)<<2|0x80000000)!=0x80026B44:
            raise ValueError('Surface copy has an unrelocated absolute call')
    count=struct.unpack_from('>I',reloc,16)[0]
    entries=list(struct.unpack_from('>'+str(count)+'I',reloc,20))
    observed=[w for w in entries if w>>30==1 and start<=(w&0xFFFFFF)<start+0x230]
    if observed!=list(removed) or {w&0xFFFFFF for w in observed}!=locations&set(range(start,start+0x230,4)):
        raise ValueError('Unexpected native surface reader relocations')
    if any(reloc[20+count*4:-4]):raise ValueError('Unexpected native relocation padding')
    keep=[w for w in entries if w not in observed]
    changed=bytearray(data);changed[start:start+0x230]=code+bytes(0x230-len(code))
    fixed=bytearray(reloc);struct.pack_into('>I',fixed,16,len(keep))
    fixed[20:-4]=struct.pack('>'+str(len(keep))+'I',*keep)+bytes(len(fixed)-24-len(keep)*4)
    relocation_offsets(fixed,len(changed))
    return bytes(changed),bytes(fixed),dict(vrom=vrom,relocation_vrom=rel_vrom,ram=ram,
        windows=[dict(offset=a,bytes=n,before_sha256=d) for (a,n),d in zip(windows,digests)],
        previous_sha256=sha256(data),sha256=sha256(changed),
        previous_relocation_sha256=sha256(reloc),relocation_sha256=sha256(fixed),
        removed_relocations=observed,compiled=compiled,buffer_offsets=[0x180,0x188],
        buffer_counts=[2,2],actor_bytes_changed=0,incoming_interiors_checked=True)


def install(base, prior, blob, core, original, output, art_path):
    if prior.get('room_surfaces'):raise ValueError('Surface readers are already installed')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    inventory,assets=discover(source,base)
    prepared=checked_prepared(art_path,inventory,assets)
    if set(prepared)!=set(assets):raise ValueError('Install the complete prepared surface category')
    rows=[];banks=[]
    for kind in KINDS:
        selected=sorted((r for r in inventory['rows'] if r['kind']==kind['kind'] and
            r['source_item_id'] in assets),key=lambda r:r['destination_index'])
        if [r['destination_index'] for r in selected]!=list(range(73,78)):
            raise ValueError('Unsupported noncontiguous additive surface bank')
        blob.extend(bytes(-len(blob)%16));start=len(blob)
        for row in selected:
            data,receipt=prepared[row['source_item_id']];at=len(blob);blob.extend(data)
            rows.append(dict(row,blob_offset=at,vrom=BLOB+at,reused_artwork=receipt,
                room_texture_installed=True))
        banks.append(dict(kind=kind['kind'],first=73,count=len(selected),stride=kind['stride'],
            blob_offset=start,vrom=BLOB+start,bytes=len(blob)-start,sha256=sha256(blob[start:])))
    defines=tuple(f'AF_SURFACE_{b["kind"].upper()}_VROM=0x{b["vrom"]:X}u' for b in banks)
    files=by_vrom(base);changes={};owners=[]
    for owner in OWNERS:
        vrom,rel,_,_,part,*_=owner
        code,compiled=compile_part(part,output/part,primary_source='overlays/v3/room_surfaces.c',defines=defines)
        changes[vrom],changes[rel],receipt=patch_owner(files[vrom].extract(base),files[rel].extract(base),
            owner,code,compiled)
        owners.append(receipt)
    report=dict(format='AFV3-ROOM-SURFACE-READERS-1',registry_version=inventory['registry_version'],
        source_rel_sha256=inventory['source_rel_sha256'],source_symbols_sha256=inventory['source_symbols_sha256'],
        preparation=str(art_path.resolve().relative_to(ROOT)),
        preparation_sha256=sha256((art_path/'surfaces.json').read_bytes()),
        banks=banks,rows=rows,owners=owners,artwork_bytes=sum(b['bytes'] for b in banks),
        additional_resident_bytes=0,additional_scene_bytes=0,saved_format_changed=False,
        selectable=False,room_texture_readers_installed=True,catalogue_texture_reader_installed=False,
        arrange_room_reader_installed=False,application_and_persistence_installed=False,
        native_execution_tested=False,
        pending=['catalogue preview and arranged NPC-room resource readers','item readers and actions',
            'room application and saved identity','acquisition and optional selection','floor sounds and scoring'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    return changes,{'room_surfaces':report}
