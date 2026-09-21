"""Install shared additive surface resources and native double-buffer readers."""
import copy
import struct

from aflib import by_vrom, sha256
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_furniture_pipeline import Source
from v3_npc_clothing import guard_incoming
from v3_npc_draw import relocation_offsets
from v3_room_surfaces import discover, checked_prepared, KINDS

SOURCES = ('tools/v3_surface_runtime.py','tools/v3_room_surfaces.py','tools/v3_registry.py',
    'tools/v3_furniture_install.py','tools/v3_asset_loader.py','overlays/v3/room_surfaces.c',
    'overlays/v3/surface_indoor.ld','overlays/v3/surface_shop.ld',
    'overlays/v3/surface_single.c','overlays/v3/surface_transfer.h','overlays/v3/surface_arrange.ld',
    'overlays/v3/surface_preview.c','overlays/v3/surface_preview.ld','tools/v3_garden_runtime.py')
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
SECONDARY = (
    (0x845C40,0x8463A0,0x80950E50,0x78,'surface_arrange',
     ('c8f99e77e8b76f3117965deeaa811b349ec9a684c60e70588dd7acd3d499b88c',
      'aa189bf14678568c753a7ad36acf4c803939a87414701c7477cd77e22107ae10'),
     '9e35cfd3560271dbcbdef5ec8eafdc2edb0c118bbd56fe2693a452b8cbdc43b5',
     (0x450000A0,0x460000AC,0x450000F4,0x46000100)),
    (0x3970000,0x3980000,0x808A6100,0x754,'surface_preview',
     ('fd8411cd9ff5fcd8fadc3be1b357ffd583b5b7ec0da441c36c64770b0e8e02a3',
      '20d9008d9a258ebb1125b993dd8447ddc1c9e9368ed62bac6946542ea64e3cb0'),
     '86957955ad986eb0732715934be18cb79bb337a620bad081df8b7a371c613a64',
     (0x450007B4,0x460007C8,0x450008AC,0x460008C0)),
)


def reader_layout(owner):
    """Owner interfaces, not item-specific behaviour categories."""
    vrom,_,ram,start,part,*_=owner
    if part=='surface_arrange':stride,names,buffers=0x54,('af_v3_single_wall','af_v3_single_floor'),[]
    elif part=='surface_preview':stride,names,buffers=0xF8,('af_v3_preview_wall','af_v3_preview_floor'),[0x744]
    else:stride,names,buffers=0x118,('af_v3_surface_floor','af_v3_surface_wall'),[0x180,0x188]
    symbols={names[0]:ram+start,names[1]:ram+start+stride,'af_surface_dma':0x80026B44}
    if part=='surface_preview':symbols.update(af_surface_stock=0x800C0490,af_surface_price=0x800C0194)
    return stride,symbols,buffers


def patch_owner(data, reloc, owner, code, compiled):
    vrom, rel_vrom, ram, start, part, digests, rel_hash, removed = owner
    stride,expected,buffers=reader_layout(owner)
    windows=[(start,stride),(start+stride,stride)]
    if (sha256(reloc)!=rel_hash or
            [sha256(data[a:a+n]) for a,n in windows]!=list(digests)):
        raise ValueError('Changed complete native surface reader or relocation table')
    locations=relocation_offsets(reloc,len(data))
    guard_incoming(data,struct.unpack_from('>I',reloc)[0],ram,windows)
    if (compiled['symbols']!=expected or not stride<len(code)<=2*stride or
            compiled['bytes']!=len(code) or compiled['sha256']!=sha256(code)):
        raise ValueError('Surface reader escapes original complete function storage')
    # Only the fixed engine DMA target may use an absolute call address.
    # Internal branches remain PC-relative when the actor is relocated.
    for (word,) in struct.iter_unpack('>I',code):
        if word>>26 in (2,3) and ((word&0x3FFFFFF)<<2|0x80000000) not in {a for n,a in expected.items() if not n.startswith('af_v3_')}:
            raise ValueError('Surface copy has an unrelocated absolute call')
    count=struct.unpack_from('>I',reloc,16)[0]
    entries=list(struct.unpack_from('>'+str(count)+'I',reloc,20))
    observed=[w for w in entries if w>>30==1 and start<=(w&0xFFFFFF)<start+2*stride]
    if observed!=list(removed) or {w&0xFFFFFF for w in observed}!=locations&set(range(start,start+2*stride,4)):
        raise ValueError('Unexpected native surface reader relocations')
    if any(reloc[20+count*4:-4]):raise ValueError('Unexpected native relocation padding')
    keep=[w for w in entries if w not in observed]
    changed=bytearray(data);changed[start:start+2*stride]=code+bytes(2*stride-len(code))
    fixed=bytearray(reloc);struct.pack_into('>I',fixed,16,len(keep))
    fixed[20:-4]=struct.pack('>'+str(len(keep))+'I',*keep)+bytes(len(fixed)-24-len(keep)*4)
    relocation_offsets(fixed,len(changed))
    return bytes(changed),bytes(fixed),dict(vrom=vrom,relocation_vrom=rel_vrom,ram=ram,
        windows=[dict(offset=a,bytes=n,before_sha256=d) for (a,n),d in zip(windows,digests)],
        previous_sha256=sha256(data),sha256=sha256(changed),
        previous_relocation_sha256=sha256(reloc),relocation_sha256=sha256(fixed),
        removed_relocations=observed,compiled=compiled,buffer_offsets=buffers,
        buffer_counts=([1]*len(buffers) if part in ('surface_arrange','surface_preview') else [2,2]),
        actor_bytes_changed=0,incoming_interiors_checked=True)


def arrange_bounds(data,reloc):
    """Keep 0..63 and additive 73..77; retain native fallback 63 otherwise."""
    first,last=0x154,0x2B0;start,end=0x1B0,0x1F8;ram=0x80950E50
    digest='7d9d333196087bf90eddc37d9469fddbdeccec527db7f4f1d23a7c70ea07cf90'
    before=bytes.fromhex('048100030008440310000005000040252881004054200003000314002408003f00031400000214030441000328410040100000040000382554200003ae0001742407003fae000174')
    if sha256(data[first:last])!=digest or data[start:end]!=before:
        raise ValueError('Changed complete arranged-room constructor and bounds')
    if relocation_offsets(reloc,len(data))&set(range(start,end,4)):
        raise ValueError('Arranged-room bounds overlap relocations')
    guard_incoming(data,struct.unpack_from('>I',reloc)[0],ram,[(start,end-start)])
    words=(0x2C810040,0x2498FFB7,0x2F180005,0x00380825,0x14200002,0x00804025,0x2408003F,
           0x2CE10040,0x24F8FFB7,0x2F180005,0x00380825,0x14200002,0,0x2407003F,0xAE000174,0,0,0)
    after=struct.pack('>18I',*words)
    changed=bytearray(data);changed[start:end]=after
    return bytes(changed),dict(offset=start,bytes=end-start,before=before.hex(),after=after.hex(),
        function_offset=first,function_bytes=last-first,native_function_sha256=digest,
        compiled_function_sha256=sha256(changed[first:last]),original_count=64,
        additive_first=73,additive_count=5,missing_fallback=63)


def retain_catalogue(prior,base,data,reloc):
    """Retain installed surface readers when ordinary bulk imports rebuild menus."""
    surface=prior.get('room_surfaces',{})
    if not surface.get('catalogue_texture_reader_installed'):return data,reloc,None
    owner=SECONDARY[1];vrom,_,_,start,_,_,_,_=owner
    record=next(r for r in surface['secondary_owners'] if r['vrom']==vrom)
    old=by_vrom(base)[vrom].extract(base)
    code=old[start:start+record['compiled']['bytes']]
    if sha256(code)!=record['compiled']['sha256']:raise ValueError('Changed retained surface preview code')
    # The rebuilt complete relocation table has legitimate new suffix entries.
    # patch_owner still checks both native bodies and all four removed entries.
    rebuilt=(*owner[:6],sha256(reloc),owner[7])
    changed,fixed,receipt=patch_owner(data,reloc,rebuilt,code,record['compiled'])
    return changed,fixed,dict(code_sha256=sha256(code),removed_relocations=receipt['removed_relocations'])


def install_consumers(base,prior,blob,output,prepared):
    surface=copy.deepcopy(prior['room_surfaces'])
    if surface.get('secondary_owners'):raise ValueError('Secondary surface consumers are already installed')
    files=by_vrom(base)
    if {r['source_item_id'] for r in surface['rows']}!=set(prepared):raise ValueError('Incomplete installed surface category')
    for row in surface['rows']:
        data=blob[row['blob_offset']:row['blob_offset']+row['bytes']]
        if data!=prepared[row['source_item_id']][0] or sha256(data)!=row['converted_sha256']:
            raise ValueError('Changed installed complete surface palette/texture')
    for record in surface['owners']:
        data=files[record['vrom']].extract(base);start=record['windows'][0]['offset']
        if sha256(data[start:start+record['compiled']['bytes']])!=record['compiled']['sha256']:
            raise ValueError('Changed retained double-buffer surface reader')
    defines=tuple(f'AF_SURFACE_{b["kind"].upper()}_VROM=0x{b["vrom"]:X}u' for b in surface['banks'])
    changes={};records=[]
    for owner,source in zip(SECONDARY,('surface_single','surface_preview')):
        vrom,rel,_,_,part,*_=owner
        code,compiled=compile_part(part,output/part,primary_source=f'overlays/v3/{source}.c',defines=defines)
        changes[vrom],changes[rel],record=patch_owner(files[vrom].extract(base),files[rel].extract(base),owner,code,compiled)
        if part=='surface_arrange':
            changes[vrom],record['bounds']=arrange_bounds(changes[vrom],changes[rel])
            record['sha256']=sha256(changes[vrom])
        records.append(record)
    surface.update(secondary_owners=records,catalogue_texture_reader_installed=True,arrange_room_reader_installed=True,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    surface['pending'].remove('catalogue preview and arranged NPC-room resource readers')
    cat=copy.deepcopy(prior['catalogue'])
    cat.update(output_sha256=sha256(changes[0x3970000]),relocation_sha256=sha256(changes[0x3980000]),
        surface_preview_code_sha256=records[1]['compiled']['sha256'])
    return changes,{'room_surfaces':surface,'catalogue':cat}


def install(base, prior, blob, core, original, output, art_path, *, module=None):
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    inventory,assets=discover(source,base)
    prepared=checked_prepared(art_path,inventory,assets)
    if set(prepared)!=set(assets):raise ValueError('Install the complete prepared surface category')
    if prior.get('room_surfaces',{}).get('items'):
        from v3_surface_application import install as install_application
        if module is None:raise ValueError('Surface application requires the checked English module')
        changes,updates=install_application(base,prior,blob,core,module,output)
        updates['room_surfaces']['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
        return changes,updates
    if prior.get('room_surfaces',{}).get('secondary_owners'):
        from v3_surface_items import install as install_items
        if module is None:raise ValueError('Surface item installation requires the checked English module')
        changes,updates=install_items(prior,blob,core,module,output)
        updates['room_surfaces']['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
        return changes,updates
    if prior.get('room_surfaces'):return install_consumers(base,prior,blob,output,prepared)
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
