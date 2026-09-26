"""Prepare complete material-frame banks without flattening their callbacks.

Draw implementations identify resource layouts, not individual item IDs. All
frames and their duplicate table entries survive. Preparation never implies
that the renderer, source timing, interaction, sound, or acquisition is ported.
"""
import struct
import copy
import json

from aflib import sha256, u32

CATEGORY='material-frame-assets'
# size, complete normalized draw digest, table pair, model pairs in actual
# submission order, matrix call, material kind, segment, table entries, selector.
FORMS=(
    (204,'cfb95eaef4f9a64d4f50229828d086ef2f2efe3b6e6628a7452650a43413c518',
     (0x6A,0x82),((0x6E,0x96),),0x4C,'palette',9,7,
     dict(input='room-or-preview-frame',division=8,modulo=7)),
    (232,'7e97ef50f92d6664d20f8d8f2a88598e0666931e3ccee718204e910186003fb9',
     (0x6A,0x8E),((0x6E,0x9E),(0x7A,0xA2)),0x4C,'palette',9,7,
     dict(input='room-or-preview-frame',division=8,modulo=7)),
    (240,'f33cdbbaa63cdab4a2c1308ed3aef3d374ff0db2da411a87594d93b0b4f2de51',
     (0x92,0xA6),((0x96,0xB6),),0x84,'palette',9,4,
     dict(input='room-or-preview-frame',division=10,modulo=4,signed=True,
          stopped_in_room_when_switch_off=True)),
    (220,'2df0ca124079361330a3e575f1860f3fd3a61e31fe5492125e964e81e0da70b9',
     (0x76,0x7A),((0x66,0x8E),(0x86,0x96)),0x4C,'palette',9,4,
     dict(input='room-or-preview-frame',division=20,modulo=4)),
    (212,'8d55b9c94b8ca5e3b1dc3949f2227d16736a7032eb261a7a4c7b98b7b7fac027',
     (0x5E,0x6A),((0x5A,0x86),(0x6E,0x7E)),0x4C,'texture',9,2,
     dict(input='room-or-preview-frame',division=2,modulo=2)),
    (168,'848b13d31a924efdfd525f925d6d2456e1d4b8640f7b4cba9bc3f3b3abc08af6',
     (0x4A,0x5E),((0x4E,0x6E),),0x3C,'texture',8,2,
     dict(input='actor-s16',offset=0x82C,mask=1)),
)


def discover(source,name,at,functions):
    from v3_furniture_pipeline import ReviewRequired
    draw=functions['draw'];raw,_=source.function(draw['offset'])
    forms=[r for r in FORMS if r[0]==len(raw)]
    if not forms:return None
    # Fingerprinting only chooses a candidate. Complete relocation, helper,
    # branch, table, and model validation below establishes its resource contract.
    normalized=bytearray(raw)
    for loc,(kind,_,_,_) in draw['relocations'].items():
        if kind in (4,6):normalized[loc:loc+2]=bytes(2)
        elif kind==10:struct.pack_into('>I',normalized,loc,u32(raw,loc)&0xFC000003)
        else:return None
    for loc in range(0,len(raw),4):
        word=u32(raw,loc)
        if word&0xFC000003==0x48000001:
            struct.pack_into('>I',normalized,loc,word&0xFC000003)
    form=next((r for r in forms if sha256(normalized)==r[1]),None)
    if form is None:return None
    size,digest,table_pair,model_pairs,call,kind,segment,count,selector=form
    module=u32(source.rel,0)
    expected={0x10:(10,0,4,0x8009AED4),size-20:(10,0,4,0x8009AF20)}
    def pair(hi,lo):
        pointer=draw['relocations'].get(hi)
        if pointer is None or pointer[:3]!=(6,module,5):
            raise ReviewRequired('material frames: missing paired data binding')
        target=pointer[3]
        expected.update({hi:(6,module,5,target),lo:(4,module,5,target)})
        return source.containing(target,exact=True)
    table,table_at,n=pair(*table_pair);pointers=source.pointers(table_at,n)
    if (n!=count*4 or any(source.data[table_at:table_at+n]) or
            set(pointers)!=set(range(table_at,table_at+n,4))):
        raise ReviewRequired('material frames: incomplete source frame table')
    frames=[]
    for pos in range(table_at,table_at+n,4):
        symbol,target,length=source.containing(pointers[pos],exact=True)
        if source.pointers(target,length) or (kind=='palette' and length!=32):
            raise ReviewRequired('material frames: incomplete frame resource')
        frames.append(dict(symbol=symbol,donor_offset=target,bytes=length,
                           source_sha256=sha256(source.data[target:target+length])))
    if len({r['bytes'] for r in frames})!=1:
        raise ReviewRequired('material frames: inconsistent complete frame sizes')
    models={f'part{i}':pair(*p) for i,p in enumerate(model_pairs)}
    helpers=source.checked_callback_code(draw,size,digest,expected,
        {call:(0x9D214,'_Matrix_to_Mtx_new')},'material frames',internal_branches=True)
    material=dict(kind=kind,segment_address=segment<<24,frames=frames,selector=dict(selector),
        table=dict(symbol=table,donor_offset=table_at,bytes=n,
                   source_sha256=sha256(source.data[table_at:table_at+n]),targets=list(pointers.values())))
    return models,{},dict(category=CATEGORY,vtable_symbol=name,vtable_offset=at,
        functions=functions,helpers=helpers,material_frames=[material],
        model_order=list(models),draw_arena='opaque',runtime_installed=False,
        pending_callbacks=list(functions),
        resource_scope='complete draw models and every material frame; lifecycle effects remain pending')


def bindings(adapter):
    """Require complete typed frame records before exposing dynamic segments."""
    if adapter.get('category')!=CATEGORY:return {}
    result={}
    for row in adapter['material_frames']:
        address=row['segment_address']
        if (address not in (0x08000000,0x09000000) or address in result or
                row['kind'] not in ('palette','texture') or not row['frames']):
            raise ValueError('Invalid complete material-frame binding')
        result[address]=row
    if not result:raise ValueError('Missing material-frame dependencies')
    return result


def runtime_record(row):
    """Translate a fully checked source descriptor into the shared draw ABI."""
    from v3_registry import furniture_identity
    from v3_room_rig_runtime import encode_materials
    adapter=row['profile']['callback_adapter'];materials=bindings(adapter)
    if len(materials)!=1 or adapter['draw_arena']!='opaque':
        raise ValueError('Unsupported material draw layout')
    address,material=next(iter(materials.items()));selector=material['selector']
    if selector==dict(input='actor-s16',offset=0x82C,mask=1):mode,divisor,state=2,0,0x1A4
    elif selector==dict(input='room-or-preview-frame',division=10,modulo=4,signed=True,
                       stopped_in_room_when_switch_off=True):mode,divisor,state=1,10,0
    elif (set(selector)=={'input','division','modulo'} and selector['input']=='room-or-preview-frame'
          and (selector['division'],selector['modulo']) in ((8,7),(20,4),(2,2))):
        mode,divisor,state=0,selector['division'],0
    else:raise ValueError('Unsupported material selector semantics')
    if mode!=2 and selector['modulo']!=len(material['frames']):raise ValueError('Incomplete material frame sequence')
    resources={r['symbol']:r for r in row['resources']};frames=[]
    for frame in material['frames']:
        r=resources[frame['symbol']]
        if any(r[k]!=frame[k] for k in ('donor_offset','bytes','source_sha256')) or r['kind']!=material['kind']:
            raise ValueError('Changed complete material frame resource')
        frames.append(r['native_offset'])
    models=[row['model_offsets'][name] for name in adapter['model_order']]
    if models!=[r['native_offset'] for r in row['models']]:raise ValueError('Changed material model order')
    index,item=furniture_identity(int(row['item_id'],16))
    record=dict(source_item_id=row['item_id'],item_id=f'{item:04X}',runtime_index=index,
        bytes=row['object_bytes'],sha256=row['object_sha256'],mode=mode,divisor=divisor,
        state_offset=state,segment=address>>24,kind=int(material['kind']=='texture'),
        frame_bytes=material['frames'][0]['bytes'],frame_offsets=frames,model_offsets=models,
        source=row,renderer_installed=True,lifecycle_installed=False,profile_installed=False,parent_selectable=False)
    encode_materials([record])
    return record


def install(base,prior,blob,core,original,output,directories):
    """Install complete frame banks together; never enable incomplete lifecycles."""
    from aflib import by_vrom
    from v3_asset_loader import ROOT,BLOB
    from v3_equipment_runtime import RAM as EQUIPMENT_RAM
    from v3_furniture_pipeline import Source,PreparedAssets,prepare,identity_rows
    from v3_import_storage import ROWS,ITEMS,slot
    from v3_resource_capacity import checked_limit
    from v3_tent_model import native_contract
    import v3_room_rig_runtime as runtime
    result=copy.deepcopy(prior['equipment_resources']);installed=result['room_rigs']
    module=blob[result['blob_offset']:result['blob_offset']+result['bytes']];packet=installed['packet']
    packet_data=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
    ram,table,size=runtime.packet_layout(installed)
    if (installed['format']!='AFV3-ROOM-RIGS-2' or sha256(module)!=result['sha256'] or
            sha256(packet_data)!=packet['sha256'] or packet_data[table-ram:]!=runtime.encode_packet(
                installed['rows'],installed.get('sound_rows',[]),installed.get('material_rows',[])) or
            EQUIPMENT_RAM+result['bytes']>ram or
            ram+size>prior['furniture']['bank_pool']['start']):
        raise ValueError('Changed or overlapping complete shared material runtime')
    contract=native_contract(original,base,expected_sha=sha256(base))
    # Catalogue passes a null room owner; rooms pass the actual room owner.
    original_catalogue=by_vrom(original)[0x7A28F0].extract(original)
    catalogue=by_vrom(base)[0x3970000].extract(base);a=0x808A7814-0x808A6100
    if (sha256(original_catalogue[a:a+0xD0])!='aa1cd409237c29058fb12a0b15225172d7e25c3cbde53509bf87231fa3a790c1' or
            catalogue[a:a+0xD0]!=original_catalogue[a:a+0xD0]):
        raise ValueError('Changed preview null-room drawing contract')
    contract.update(preview_draw_sha256=sha256(catalogue[a:a+0xD0]),preview_frame_offset=0xA0,
        room_frame_offset=0x1EA0,source_frames_per_native_frame=2,state_offset=0x1A4)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    directories=[d.resolve() for d in directories];cache=PreparedAssets(source,directories)
    identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',include_unmapped_legacy=True)
    occupied={r['item_id'] for r in installed['rows']+installed.get('sound_rows',[])+installed.get('material_rows',[])}
    rows=[];evidence=[];assets={}
    for directory in directories:
        if not directory.is_relative_to(ROOT/'build'):raise ValueError('Materials require ignored prepared artwork')
        raw=(directory/'art.json').read_bytes();art=json.loads(raw)
        if art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1':raise ValueError('Expected complete prepared frame assets')
        evidence.append(dict(directory=str(directory.relative_to(ROOT)),sha256=sha256(raw)))
        for row in art['objects']:
            donor=row['item_id'];item=int(donor,16);prepared=prepare(source,item)
            descriptor=prepared[0]
            if (descriptor.get('callback_adapter',{}).get('category')!=CATEGORY or
                    row['profile']!=json.loads(json.dumps(descriptor)) or
                    row['native_profile_scalar_hex']!=descriptor['scalar_hex'] or
                    any(identities[item][1].get(k)!='-' for k in ('C','H','CG','CJ')) or
                    cache.reuse(source,donor,prepared) is None):
                raise ValueError('Incomplete, changed, or unreviewed material resources')
            path=(directory/row['object_file']).resolve()
            if path.parent!=directory:raise ValueError('Material artwork escapes prepared directory')
            data=path.read_bytes();record=runtime_record(row);i=slot(int(record['item_id'],16))
            if (len(data)!=record['bytes'] or sha256(data)!=record['sha256'] or record['item_id'] in occupied or
                    any(blob[ROWS+i*80:ROWS+(i+1)*80]) or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or
                    blob[0x40+i//8]&(1<<(i&7))):raise ValueError('Changed material artwork or occupied native identity')
            occupied.add(record['item_id']);rows.append(record);assets[donor]=data
    if not rows:raise ValueError('Empty material category')
    all_rows=sorted(installed.get('material_rows',[])+rows,key=lambda r:r['runtime_index'])
    runtime.encode_materials(all_rows)
    for r in installed.get('material_rows',[]):
        if sha256(blob[r['blob_offset']:r['blob_offset']+r['bytes']])!=r['sha256']:
            raise ValueError('Changed installed material artwork')
    needed=sum(len(d) for d in assets.values());start=(len(blob)+15)&~15
    if BLOB+start+needed>checked_limit(base,prior):raise ValueError('Material category exceeds cartridge reservation')
    blob.extend(bytes(start-len(blob)))
    for row in rows:
        at=len(blob);blob.extend(assets[row['source_item_id']]);row.update(blob_offset=at,vrom=BLOB+at)
    installed.update(material_rows=all_rows,material_native_contract=contract,material_capacity=runtime.MATERIAL_CAPACITY)
    installed.setdefault('material_sources',[]).extend(evidence)
    installed['artwork_bytes']+=needed
    runtime.publish_packet(result,blob,output)
    result['additional_resident_bytes']=0
    return result,{}


# The common cartridge refresh records these dependencies with its build lock.
SOURCES=('tools/v3_furniture_materials.py','tools/v3_room_rig_runtime.py','tools/v3_registry.py',
    'tools/v3_furniture_scroll.py','tools/v3_asset_loader.py',
    'overlays/v3/room_scroll.c','overlays/v3/room_scroll.h','overlays/v3/room_scroll.ld',
    'tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py','tools/v3_furniture_art.py',
    'tools/v3_tent_model.py','overlays/v3/room_materials.c','overlays/v3/room_materials.h',
    'overlays/v3/room_rigs.c','overlays/v3/room_rigs.h','overlays/v3/room_rigs_packet.ld',
    'overlays/v3/room_rigs_bootstrap.c','overlays/v3/room_rigs_bootstrap.ld')
