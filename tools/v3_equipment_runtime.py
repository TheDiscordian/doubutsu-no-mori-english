"""Shared native resource loading for checked held models and motion data.

This installs resources, not inventory identities or player action support.
All item choices and saved profiles remain unchanged.
"""
import json
import copy
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_import_storage import PACKAGE_RAM, END, jump
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_pipeline import Source, prepare_models
from v3_handheld_items import scan, descriptor, motion, selector_tables, kind_bindings
from v3_keyframes import compile_animations, animation
from v3_npc_clothing import guard_incoming

RAM, SIZE, TABLE, MAGIC, GUARD = 0x804A3000, 0x2000, 0x1000, 0x41464852, 0xAF48C0DE
FIRST, COUNT, CAPACITY = 17, 50, 4376
SOURCES = ('tools/v3_equipment_runtime.py','tools/v3_handheld_items.py','tools/v3_keyframes.py',
    'tools/v3_furniture_pipeline.py','tools/v3_asset_loader.py',
    'overlays/v3/equipment_resources.c','overlays/v3/equipment_resources.S',
    'overlays/v3/equipment_resources.ld','overlays/v3/startup.c')
ENTRIES = (
    (0x800B12C8,0x800B12F4,'af_v3_equipment_pointer'),
    (0x800B12F4,0x800B131C,'af_v3_equipment_type'),
    (0x800B131C,0x800B1364,'af_v3_equipment_size'),
    (0x800B1614,0x800B1650,'af_v3_equipment_origin'),
    (0x800B1650,0x800B167C,'af_v3_equipment_vrom'),
)
PLAYER_VROM, PLAYER_RELOC, PLAYER_RAM = 0x007AC420, 0x007D9BA0, 0x808B2D50
PLAYER_TABLE, PLAYER_MASK, PLAYER_BRIDGE = 0x1340, 0x1FD0, 0xFE0
PLAYER_FIRST, PLAYER_COUNT, PLAYER_CAPACITY = 130, 157, 3848
KIND_TABLE, KIND_FIRST, KIND_COUNT, KIND_STRIDE = 0xB00, 36, 79, 12
KIND_ENTRIES = (
    (0x808BD668,0x808DF508,'player_animation',-1),
    (0x808BD690,0x808DF52C,'item_main',0),
    (0x808BD6B8,0x808DF550,'shape',-1),
    (0x808BD6E0,0x808DF574,'animation',-1),
    (0x808C2D4C,0x808DF9D0,'tumble',33),
    (0x808C32CC,0x808DF9F4,'getup',34),
)
PLAYER_ENTRIES = (
    (0x800B11B0,0x800B11F8,'af_v3_player_animation_size'),
    (0x800B1264,0x800B12A0,'af_v3_player_animation_origin'),
    (0x800B1D68,0x800B1D94,'af_v3_player_animation_vrom'),
    (0x800B1DE8,0x800B1E94,'af_v3_player_part_copy'),
)


def player_resources(source, original):
    """Complete holding/action motions and the donor's actual split-body masks."""
    description=motion(source)
    functions,tables,values=selector_tables(source,{
        'player_part':(0x68A9C,'mPlib_Get_BasicPartTableIndex_fromAnimeIndex',44,
            'b86a74a6d599ce78aab4e428b83f87f14124396a953d3d3b5b3fd11b5f7b50bf',4,0x16),
    })
    raw,copy_function=source.function(0x69564)
    if (copy_function['symbol']!='mPlib_DMA_player_Part_Table' or len(raw)!=72
            or sha256(raw)!='d43cd9bfc9489ee7958373c5b3a0cf1e91f370882fe91357dff62eef7a297425'
            or copy_function['relocations']!={0x34:(10,0,4,0x8005D01C),
                0x22:(6,1,5,0x188A60),0x2A:(4,1,5,0x188A60)}):
        raise ValueError('Changed complete player part-mask consumer')
    masks=source.raw('BOY_part_data')
    if len(masks)!=135 or sha256(masks)!='550af4a04ef29a6fc44c0741264230eff559c65d7b3a02456b1fb15cd305ae87':
        raise ValueError('Changed complete player part masks')
    native=by_vrom(original)[0x00B8A000].extract(original)
    if len(native)!=112 or any(native[i*28:i*28+27]!=masks[i*27:i*27+27] for i in range(4)):
        raise ValueError('Native and donor split-body conventions disagree')
    records=[];assets={}
    for index,row in description['player_animations'].items():
        asset,compiled=compile_animations(source,[row]);part=values['player_part'][index]
        if (not 0<=index<PLAYER_COUNT or not 0<len(asset)<=PLAYER_CAPACITY
                or len(asset)%16 or part>=5 or row['joints']!=26):
            raise ValueError('Player animation exceeds native buffer/rig or part table')
        assets[index]=asset
        records.append(dict(source_index=index,index=PLAYER_FIRST+index,bytes=len(asset),
            pointer=0x06000000+compiled['headers'][0]['native_offset'],type=part,
            sha256=sha256(asset),source=row,compiled=compiled))
    return assets,records,masks[108:],dict(functions=functions,tables=tables,
        copy_function=copy_function,masks_sha256=sha256(masks),native_masks_sha256=sha256(native),
        native_masks_retained=True,animation_capacity=PLAYER_CAPACITY,
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()))


def prepared_resources(source, art_path):
    """Reuse checked graphics and pack each complete motion for native DMA."""
    art_path=art_path.resolve();raw=(art_path/'art.json').read_bytes();art=json.loads(raw)
    if (art['format']!='AFV3-HANDHELD-PREPARED-ASSETS-1' or art['version']!=1
            or art['source_rel_sha256']!=sha256(source.rel)
            or art['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed handheld artwork source/format')
    inventory=scan(source)
    rows={r['shape_index']:r for r in inventory['rows']
          if r['asset_ready'] and r['category']=='static-held-model'}
    assets={};receipts=[]
    for row in art['objects']:
        index=row['shape_index']
        if index not in rows or index in assets:
            raise ValueError('Duplicate or unsupported held model root')
        prepared=prepare_models(source,descriptor(rows[index]))
        profile,body,resources,_,models,commands,sections=prepared
        file=(art_path/row['object_file']).resolve()
        if file.parent!=art_path:raise ValueError('Held object escapes prepared directory')
        asset=file.read_bytes();offsets=row['model_offsets']
        if (row['profile']!=json.loads(json.dumps(profile)) or row['resources']!=resources
                or set(models)!={'opaque'} or set(offsets)!={'opaque'} or len(row['models'])!=1
                or len(asset)!=rows[index]['object_bytes'] or len(asset)!=row['object_bytes']
                or sha256(asset)!=row['object_sha256'] or asset[:len(body)]!=body
                or (art_path/f'data-{index:04X}'/'commands.c').read_text()!=commands):
            raise ValueError('Changed complete held model or compiled source')
        model=row['models'][0];at=(len(body)+7)&~7;n=sections[0][1]
        if (offsets['opaque']!=at or model['native_offset']!=at or model['bytes']!=n
                or model['source_sha256']!=models['opaque']['source_sha256']
                or model['output_sha256']!=sha256(asset[at:at+n])
                or asset[at+n:]!=bytes(len(asset)-at-n)):
            raise ValueError('Changed complete compiled held model')
        assets[index]=asset
        receipts.append(dict(source_index=index,index=FIRST+index,kind='static-model',type=0,
            pointer=0x06000000+at,bytes=len(asset),sha256=sha256(asset),source=row))
    if set(assets)!=set(rows):raise ValueError('Incomplete prepared static held category')
    motions=motion(source)
    for index,row in motions['equipment_animations'].items():
        description={k:v for k,v in row.items() if k!='resource_type'}
        asset,compiled=compile_animations(source,[description])
        if index in assets:raise ValueError('Animation collides with a model resource')
        assets[index]=asset
        receipts.append(dict(source_index=index,index=FIRST+index,kind='animation',type=row['resource_type'],
            pointer=0x06000000+compiled['headers'][0]['native_offset'],bytes=len(asset),
            sha256=sha256(asset),source=row,compiled=compiled))
    if any(not 0<=i<COUNT or not 0<len(a)<=CAPACITY or len(a)%16 for i,a in assets.items()):
        raise ValueError('Held resource exceeds native isolated transfer capacity')
    return assets,sorted(receipts,key=lambda r:r['index']),dict(
        art_directory=str(art_path.relative_to(ROOT)),art_report_sha256=sha256(raw),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()))


def native_contract(original, core):
    native=by_vrom(original)[CODE_VROM].extract(original)
    ranges=[(a,b) for a,b,_ in ENTRIES]+[(0x800B167C,0x800B16F8),
        (0x800B1384,0x800B149C),(0x800B1590,0x800B1614),(0x8010BF30,0x8010BFD0)]
    for a,b in ranges:
        if core[a-CODE_RAM:b-CODE_RAM]!=native[a-CODE_RAM:b-CODE_RAM]:
            raise ValueError('Changed native equipment resource consumer/table')
    pointers=struct.unpack_from('>17I',native,0x8010BF30-CODE_RAM)
    types=native[0x8010BF74-CODE_RAM:0x8010BF74-CODE_RAM+17]
    bounds=struct.unpack_from('>18I',native,0x8010BF88-CODE_RAM)
    sizes=[b-a-8 for a,b in zip(bounds,bounds[1:])]
    if (sizes[1]+max(n for n,t in zip(sizes,types) if t==2)!=CAPACITY
            or max(sizes)>CAPACITY):
        raise ValueError('Changed native equipment buffer capacity')
    return dict(ranges=[dict(start=a,end=b,sha256=sha256(native[a-CODE_RAM:b-CODE_RAM])) for a,b in ranges],
        pointers=list(pointers),types=list(types),bounds=list(bounds),sizes=sizes,
        item_bank_bytes=CAPACITY, native_joint_work_vectors=7,
        native_animation_loader=0x800B167C, native_bank_change=0x808B5A10,
        menu_reload='mSM_load_player_anime', buffer_sizes_changed=False)


def prepared_rigs(source, art_path, *, categories=(22,), joint_work_vectors=7):
    """Validate the complete prepared category without recompiling its artwork."""
    from v3_handheld_items import rig_descriptor
    from v3_keyframes import compile_skeleton
    art_path=art_path.resolve();raw=(art_path/'art.json').read_bytes();art=json.loads(raw)
    if (not art_path.is_relative_to(ROOT/'build') or art['format']!='AFV3-ANIMATED-HELD-PREPARED-1'
            or art['version']!=1 or art['source_rel_sha256']!=sha256(source.rel)
            or art['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed prepared equipment rig source/format')
    if (not categories or len(set(categories))!=len(categories)
            or any(type(c) is not int or c<0 for c in categories)
            or type(joint_work_vectors) is not int or not 1<=joint_work_vectors<=256):
        raise ValueError('Invalid equipment rig category/capacity contract')
    description=motion(source);inventory=scan(source)
    # Conversion support is not runtime support. The current installer supplies
    # category 22; new converters must not silently enlarge its required bundle.
    kinds=kind_bindings(source)['rows']
    if not set(categories)<={r['item_main'] for r in kinds}:
        raise ValueError('Unknown equipment rig source category')
    identities={r['item_id'] for r in kinds if r['item_main'] in categories}
    parents=[r for r in inventory['rows'] if r['category']=='animated-held-model'
             and r['item_id'] in identities]
    parent_ids={r['item_id'] for r in parents}
    if (not parents or any(not r['asset_ready'] for r in parents)
            or {r['item_main'] for r in kinds if r['item_id'] in parent_ids}!=set(categories)):
        raise ValueError('Incomplete convertible equipment rig categories')
    roots={r['shape_index'] for r in parents};assets={};records=[]
    for row in art['objects']:
        index=row['shape_index'];matches=[r for r in parents if r['shape_index']==index]
        if index not in roots or index in assets:raise ValueError('Duplicate or unsupported equipment rig')
        rig=description['skeletons'][index]
        profile,body,resources,_,models,commands,sections=prepare_models(source,rig_descriptor(matches[0],rig))
        file=(art_path/row['object_file']).resolve()
        if file.parent!=art_path:raise ValueError('Equipment rig escapes prepared directory')
        asset=file.read_bytes();offsets=row['model_offsets'];at=(len(body)+7)&~7
        if (row['profile']!=json.loads(json.dumps(profile)) or row['resources']!=resources
                or row['parent_item_ids']!=[r['item_id'] for r in matches]
                or row['motion_bindings']!=[r['motion_binding'] for r in matches]
                or row['resource_type']!=1 or len(asset)!=row['object_bytes']
                or len(asset)!=matches[0]['object_bytes'] or sha256(asset)!=row['object_sha256']
                or asset[:len(body)]!=body or any(asset[len(body):at])
                or set(offsets)!=set(models) or len(row['models'])!=len(models)
                or (art_path/f'data-{index:04X}'/'commands.c').read_text()!=commands):
            raise ValueError('Changed complete equipment rig artwork/bindings')
        for compiled,(label,n) in zip(row['models'],sections):
            if (offsets[label]!=at or compiled['native_offset']!=at or compiled['bytes']!=n
                    or compiled['source_sha256']!=models[label]['source_sha256']
                    or compiled['output_sha256']!=sha256(asset[at:at+n])):
                raise ValueError('Changed compiled joint graphics')
            at+=n
        aligned=(at+15)&~15
        targets={root[1]:offsets[label] for label,root in profile['models'].items()}
        suffix,compiled=compile_skeleton(source,rig,targets,start=aligned)
        if (any(asset[at:aligned]) or row['artwork_bytes']!=aligned or asset[aligned:]!=suffix
                or row['skeleton']!=json.loads(json.dumps(compiled))
                or row['root_offset']!=compiled['header']['native_offset']
                or not 0<rig['joints']<joint_work_vectors or rig['shown_joints']>joint_work_vectors
                or row['maximum_animation_bytes']!=matches[0]['maximum_animation_bytes']
                or row['maximum_model_animation_bytes']!=matches[0]['maximum_model_animation_bytes']):
            raise ValueError('Changed complete joint hierarchy or native work-vector capacity')
        assets[index]=asset
        records.append(dict(source_index=index,index=FIRST+index,kind='animated-model',type=1,
            pointer=0x06000000+row['root_offset'],bytes=len(asset),sha256=sha256(asset),source=row))
    if set(assets)!=roots:raise ValueError('Incomplete prepared equipment rig category')
    return assets,records,dict(art_directory=str(art_path.relative_to(ROOT)),art_report_sha256=sha256(raw),
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()))


def grow_banks(original, core, owner, capacity):
    """Grow both real outdoor banks and their containing scene arena together."""
    native=by_vrom(original);old=native[CODE_VROM].extract(original)
    native_owner=native[PLAYER_VROM].extract(original)
    ranges=((0x800B1364,0x800B1614),(0x800B167C,0x800B16F8),
            (0x800B1838,0x800B190C),(0x800B1A28,0x800B1A60),
            (0x800C5C30,0x800C5CC4),(0x800C4440,0x800C453C),(0x800C65E4,0x800C6678),
            (0x8010BF30,0x8010C0D0),(0x8010DDD0+35*8,0x8010DDD0+36*8))
    for a,b in ranges:
        if core[a-CODE_RAM:b-CODE_RAM]!=old[a-CODE_RAM:b-CODE_RAM]:
            raise ValueError('Changed native equipment bank owner or reload consumer')
    first,last=0x808B59C0-PLAYER_RAM,0x808B5B38-PLAYER_RAM
    if owner[first:last]!=native_owner[first:last]:raise ValueError('Changed native double-bank loader')
    bounds=struct.unpack_from('>18I',old,0x8010BF88-CODE_RAM)
    sizes=[b-a-8 for a,b in zip(bounds,bounds[1:])]
    types=old[0x8010BF74-CODE_RAM:0x8010BF74-CODE_RAM+17]
    starts=struct.unpack_from('>32I',old,0x8010BFD0-CODE_RAM)
    ends=struct.unpack_from('>32I',old,0x8010C050-CODE_RAM)
    maximum=max(sizes[0],sizes[1]+max(n for n,t in zip(sizes,types) if t==2),
                sizes[9]+max(n for n,t in zip(sizes,types) if t==3),sizes[16],
                max(b-a for a,b in zip(starts,ends) if a and b))
    menu_bounds=struct.unpack_from('>2I',old,0x8010DDD0+35*8-CODE_RAM)
    if maximum!=CAPACITY or not CAPACITY<capacity<32768 or capacity%16 or capacity>menu_bounds[1]-menu_bounds[0]:
        raise ValueError('Invalid shared equipment-bank growth')
    growth=2*(capacity-((maximum+15)&~15));arena=0x93400+growth
    if arena>>16!=9:raise ValueError('Scene arena growth exceeds audited immediate pair')
    guard_incoming(bytes(core),len(core),CODE_RAM,[(0x800B1590-CODE_RAM,8)])
    patches=[]
    for address,data in ((0x800B1590,struct.pack('>2I',0x03E00008,0x24020000|capacity)),
                         (0x800C6618,struct.pack('>I',0x34A50000|(arena&65535))),
                         (0x800C6628,struct.pack('>I',0x34210000|(arena&65535)))):
        at=address-CODE_RAM;before=bytes(core[at:at+len(data)]);core[at:at+len(data)]=data
        patches.append(dict(address=address,before=before.hex(),after=data.hex()))
    return dict(previous_bank_bytes=maximum,bank_bytes=capacity,banks=2,
        previous_aligned_bank_bytes=(maximum+15)&~15,additional_scene_bytes=growth,
        previous_scene_arena_bytes=0x93400,scene_arena_bytes=arena,
        inventory_bank_bytes=menu_bounds[1]-menu_bounds[0],inventory_bank_changed=False,
        native_joint_work_vectors=7,patches=patches,
        native_consumers=[dict(start=a,end=b,sha256=sha256(old[a-CODE_RAM:b-CODE_RAM])) for a,b in ranges],
        double_bank_loader_sha256=sha256(owner[first:last]),
        ordinary_reload_tested=False,hardware_tested=False)


def install_rigs(base, prior, blob, core, original, output, art_path):
    """Add checked rigs to the same resource/kind namespace and native owners."""
    if prior['equipment_resources'].get('animated_rigs'):
        return extend_rigs(base,prior,blob,core,original,output,art_path)
    old=prior['equipment_resources'];position=old['blob_offset']
    module=bytearray(blob[position:position+old['bytes']]);files=by_vrom(base)
    owner=bytearray(files[PLAYER_VROM].extract(base))
    if (old.get('animated_rigs') or not old.get('kind_readers') or not old.get('inventory_preview')
            or sha256(module)!=old['sha256'] or old['ram']!=RAM
            or RAM+len(module)>prior['furniture']['bank_pool']['start']
            or struct.unpack_from('>4I',module,len(module)-16)!=(GUARD,)*4):
        raise ValueError('Changed shared equipment module or rig dependency')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    assets,records,evidence=prepared_rigs(source,art_path)
    motion_description=motion(source);installed={r['source_index']:r for r in old['records']}
    capacity=CAPACITY
    for row in records:
        for binding in row['source']['motion_bindings']:
            for index in binding['animation_resources']:
                animation_row=installed.get(index)
                desc={k:v for k,v in motion_description['equipment_animations'][index].items() if k!='resource_type'}
                data,_=compile_animations(source,[desc])
                if (not animation_row or animation_row['kind']!='animation' or
                        animation_row['sha256']!=sha256(data) or
                        blob[animation_row['blob_offset']:animation_row['blob_offset']+len(data)]!=data):
                    raise ValueError('Prepared rig lacks its complete installed animation')
                capacity=max(capacity,row['bytes']+len(data))
    capacity=(capacity+15)&~15
    allocation=grow_banks(original,core,owner,capacity)
    report=copy.deepcopy(old)
    for row in records:
        slot=TABLE+16+row['source_index']*16
        if row['source_index'] in installed or any(module[slot:slot+16]):
            raise ValueError('Rig would overwrite an installed resource')
        blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(assets[row['source_index']])
        row.update(vrom=BLOB+at,blob_offset=at)
        struct.pack_into('>4I',module,slot,row['vrom'],row['bytes'],row['pointer'],row['type'])
        report['records'].append(row);installed[row['source_index']]=row
    report['records'].sort(key=lambda r:r['index'])
    for row in report['kind_readers']['rows']:
        shape=installed.get(row['shape']);anim=installed.get(row['animation'])
        if not shape or shape['type']!=1:continue
        combined=shape['bytes']+(anim['bytes'] if anim else 0)
        if not anim or combined>capacity:raise ValueError('Rig kind exceeds its complete bank')
        row['fields'][2:4]=[shape['index'],anim['index']]
        row.update(combined_bank_bytes=combined,shape_installed=True,resource_ready=True)
        struct.pack_into('>6h',module,KIND_TABLE+16+row['source_kind']*KIND_STRIDE,*row['fields'])
    flags=('AF_V3_PLAYER_MOTION=1','AF_V3_EQUIPMENT_KINDS=1','AF_V3_EQUIPMENT_RIGS=1',
           f'AF_V3_EQUIPMENT_CAPACITY={capacity}u')
    code,compiled=compile_part('equipment_resources',output/'equipment_resources',defines=flags,
        extra_sources=('overlays/v3/equipment_resources.S',))
    if len(code)>KIND_TABLE or compiled['symbols']['af_v3_equipment_pointer']!=RAM:
        raise ValueError('Equipment readers exceed code or move the held draw entry')
    module[:KIND_TABLE]=code+bytes(KIND_TABLE-len(code))
    for hooks in (report['hooks'],report['player_motion']['hooks']):
        for hook in hooks:
            off=hook['entry']-CODE_RAM;before=bytes(core[off:off+8])
            if before.hex()!=hook['after']:raise ValueError('Changed installed equipment resource hook')
            target=compiled['symbols'][hook['helper']];after=struct.pack('>II',jump(target),0)
            core[off:off+8]=after;hook.update(before=before.hex(),after=after.hex(),target=target)
    for hooks in (report['player_motion']['owner_hooks'],report['kind_readers']['owner_hooks']):
        for hook in hooks:
            off=hook['entry']-PLAYER_RAM;n=hook['end']-hook['entry'];before=bytes(owner[off:off+n])
            helper=hook.get('helper','af_v3_equipment_kind_field')
            if before.hex()!=hook['after']:raise ValueError('Changed installed equipment owner hook')
            old_jump=struct.pack('>I',jump(old['code']['symbols'][helper]))
            points=[i for i in range(0,n,4) if before[i:i+4]==old_jump]
            if len(points)!=1:raise ValueError('Ambiguous installed equipment helper reference')
            at=points[0];after=before[:at]+struct.pack('>I',jump(compiled['symbols'][helper]))+before[at+4:]
            owner[off:off+n]=after;hook.update(before=before.hex(),after=after.hex())
    from v3_npc_draw import relocation_offsets
    address=0x808B5A68;off=address-PLAYER_RAM;before=bytes(owner[off:off+4])
    if (before!=struct.pack('>I',jump(0x800B167C,link=True))
            or off in relocation_offsets(files[PLAYER_RELOC].extract(base),len(owner))):
        raise ValueError('Changed native model transfer call or relocation')
    after=struct.pack('>I',jump(compiled['symbols']['af_v3_equipment_model_dma'],link=True))
    owner[off:off+4]=after
    model_hook=dict(address=address,before=before.hex(),after=after.hex(),
        helper='af_v3_equipment_model_dma',target=compiled['symbols']['af_v3_equipment_model_dma'])
    # Existing action drawing calls the fixed first entry; no other code may
    # retain a direct jump into a helper that moved during recompilation.
    for data in (module[KIND_TABLE:],owner):
        for at in range(0,len(data)-3,4):
            word=struct.unpack_from('>I',data,at)[0]
            if word>>26 not in (2,3):continue
            target=0x80000000|((word&0x3FFFFFF)<<2)
            if RAM<=target<RAM+KIND_TABLE and target not in compiled['symbols'].values():
                raise ValueError('Unbound direct reference to replaced equipment code')
    blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(module)
    if BLOB+len(blob)>END:raise ValueError('Equipment rigs exceed shared ROM storage')
    report.update(code=compiled,vrom=BLOB+at,blob_offset=at,sha256=sha256(module),
        crc32=zlib.crc32(module),additional_resident_bytes=0,item_bank_bytes_changed=True)
    report['player_motion']['owner_sha256']=sha256(owner)
    report['kind_readers']['item_bank_bytes_changed']=True
    report['animated_rigs']=dict(format='AFV3-EQUIPMENT-RIGS-1',evidence=evidence,
        resource_indices=[r['index'] for r in records],allocation=allocation,
        owner_patches=[model_hook],animation_cache_invalidated_on_model_change=True,
        model_bytes=sum(len(a) for a in assets.values()),logical_imports_added=0,
        player_actions_installed=False,inventory_previews_installed=False,profile_changed=False)
    return report,{PLAYER_VROM:bytes(owner)}


def grow_player_joint_work(original,core,owner,relocation,allocation,vectors,previous=None):
    """Move complete transient work/morph arrays into an enlarged actor tail."""
    from v3_npc_draw import relocation_offsets
    native=by_vrom(original);before=native[PLAYER_VROM].extract(original)
    native_core=native[CODE_VROM].extract(original)
    entry=0x8010BCEC;at=entry-CODE_RAM
    profile=bytearray(core[at-12:at+20])
    if (allocation['address']!=entry or u32(profile,12)!=allocation['bytes']
            or allocation['bytes']%16 or not 7<vectors<=16):
        raise ValueError('Changed player allocation or unsupported joint capacity')
    struct.pack_into('>I',profile,12,allocation['original_bytes'])
    if profile!=native_core[at-12:at+20]:raise ValueError('Changed complete native player profile')
    normalized=bytearray(owner)
    if previous:
        if allocation['bytes']!=previous['player_bytes'] or vectors<=previous['vectors']:
            raise ValueError('Changed previous player joint reservation')
        for patch in previous['patches']:
            off=patch['address']-PLAYER_RAM
            if u32(owner,off)!=patch['after']:raise ValueError('Changed installed player joint pointer')
            struct.pack_into('>I',normalized,off,patch['before'])
    first,last=0x808BD934-PLAYER_RAM,0x808BDACC-PLAYER_RAM
    if normalized[first:last]!=before[first:last]:raise ValueError('Changed complete player skeleton initializer')
    targets={0x808BD9DC:0xAB2,0x808BD9F0:0xA88,0x808BDA20:0xAB2,0x808BDA34:0xA88}
    found={PLAYER_RAM+i:u32(normalized,i)&65535 for i in range(0,0x2AF00,4)
           if u32(normalized,i)>>26==9 and u32(normalized,i)>>21&31 and u32(normalized,i)&65535 in (0xA88,0xAB2)}
    if found!=targets:raise ValueError('Unreviewed player joint-work pointer consumer')
    start=previous['joint_offset'] if previous else allocation['bytes']
    length=vectors*6;end=(start+2*length+15)&~15
    offsets={0xA88:start,0xAB2:start+length};patches=[]
    relocations=relocation_offsets(relocation,len(owner))
    for address,old in targets.items():
        off=address-PLAYER_RAM;word=u32(normalized,off)
        if off in relocations or offsets[old]>=32768:raise ValueError('Invalid player joint pointer patch')
        changed=word&0xFFFF0000|offsets[old];struct.pack_into('>I',owner,off,changed)
        patches.append(dict(address=address,before=word,after=changed))
    struct.pack_into('>I',core,at,end)
    return dict(vectors=vectors,previous_vectors=previous['vectors'] if previous else 7,joint_offset=start,morph_offset=start+length,
        array_bytes=length,previous_player_bytes=allocation['bytes'],player_bytes=end,
        additional_player_bytes=end-allocation['bytes'],patches=patches,
        initializer=dict(start=PLAYER_RAM+first,end=PLAYER_RAM+last,
                         original_sha256=sha256(before[first:last]),sha256=sha256(owner[first:last])),
        save_format_changed=False,inventory_joint_work_changed=False)


def extend_rigs(base,prior,blob,core,original,output,art_path):
    """Extend complete resource categories while retaining every installed rig."""
    old=prior['equipment_resources'];rigs=old['animated_rigs'];files=by_vrom(base)
    module=bytearray(blob[old['blob_offset']:old['blob_offset']+old['bytes']])
    owner=bytearray(files[PLAYER_VROM].extract(base));rel=files[PLAYER_RELOC].extract(base)
    if (sha256(module)!=old['sha256'] or old['ram']!=RAM
            or not old.get('held_rig_actions') or sha256(owner)!=old['player_motion']['owner_sha256']
            or sha256(rel)!=old['player_motion']['reloc_sha256']
            or struct.unpack_from('>4I',module,len(module)-16)!=(GUARD,)*4):
        raise ValueError('Changed current rig module/owner')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    art=json.loads((art_path/'art.json').read_bytes())
    supplied={p for r in art['objects'] for p in r['parent_item_ids']}
    categories=tuple(sorted({r['item_main'] for r in kind_bindings(source)['rows'] if r['item_id'] in supplied}))
    description=motion(source)
    previous_vectors=old.get('player_joint_work',{}).get('vectors',7)
    vectors=max(previous_vectors,max(description['skeletons'][r['shape_index']]['joints']+1 for r in art['objects']))
    assets,records,evidence=prepared_rigs(source,art_path,categories=categories,joint_work_vectors=vectors)
    report=copy.deepcopy(old);installed={r['source_index']:r for r in report['records']}
    capacity=rigs['allocation']['bank_bytes'];added=[]
    reuse=retired_module_space(base,prior,blob,sum(len(a) for a in assets.values()))
    cursor=reuse['blob_offset'] if reuse else len(blob)
    for row in records:
        if row['source_index'] in installed:raise ValueError('Resource extension would overwrite an installed rig')
        for binding in row['source']['motion_bindings']:
            for index in binding['animation_resources']:
                animation_row=installed.get(index)
                desc={k:v for k,v in description['equipment_animations'][index].items() if k!='resource_type'}
                data,_=compile_animations(source,[desc])
                if (not animation_row or animation_row['kind']!='animation'
                        or animation_row['sha256']!=sha256(data)
                        or blob[animation_row['blob_offset']:animation_row['blob_offset']+len(data)]!=data):
                    raise ValueError('Extended rig lacks its complete installed animation')
                capacity=max(capacity,row['bytes']+len(data))
        slot=TABLE+16+row['source_index']*16
        if any(module[slot:slot+16]):raise ValueError('Extended rig slot is occupied')
        cursor=(cursor+15)&~15;at=cursor;data=assets[row['source_index']];cursor+=len(data)
        if reuse:
            if cursor>reuse['blob_offset']+reuse['bytes']:raise ValueError('Rig exceeds retired module reservation')
            blob[at:cursor]=data
        else:
            blob.extend(bytes(at-len(blob)));blob.extend(data)
        row.update(vrom=BLOB+at,blob_offset=at)
        struct.pack_into('>4I',module,slot,row['vrom'],row['bytes'],row['pointer'],row['type'])
        report['records'].append(row);installed[row['source_index']]=row;added.append(row['source_index'])
    if not added:raise ValueError('No complete new equipment category')
    capacity=(capacity+15)&~15
    # Reconstruct the exact original bank consumers, checking every installed
    # adjustment first, then apply the same shared bank-growth rule anew.
    normalized=bytearray(core);normal_owner=bytearray(owner)
    for patch in rigs['allocation']['patches']:
        at=patch['address']-CODE_RAM;after=bytes.fromhex(patch['after'])
        if normalized[at:at+len(after)]!=after:raise ValueError('Changed installed equipment bank patch')
        normalized[at:at+len(after)]=bytes.fromhex(patch['before'])
    for patch in rigs['owner_patches']:
        at=patch['address']-PLAYER_RAM;after=bytes.fromhex(patch['after'])
        if normal_owner[at:at+len(after)]!=after:raise ValueError('Changed installed model-cache hook')
        normal_owner[at:at+len(after)]=bytes.fromhex(patch['before'])
    allocation=grow_banks(original,normalized,normal_owner,capacity)
    allocation.update(previous_extended_bank_bytes=rigs['allocation']['bank_bytes'],
        incremental_scene_bytes=allocation['scene_arena_bytes']-rigs['allocation']['scene_arena_bytes'])
    core[:]=normalized
    if vectors>previous_vectors:
        joint=grow_player_joint_work(original,core,owner,rel,old['held_rig_actions']['player_allocation'],vectors,
                                     old.get('player_joint_work'))
        report['player_joint_work']=joint
        report['held_rig_actions']['player_allocation']['bytes']=joint['player_bytes']
    report['records'].sort(key=lambda r:r['index'])
    for row in report['kind_readers']['rows']:
        if row['shape'] not in added:continue
        shape,anim=installed[row['shape']],installed[row['animation']]
        combined=shape['bytes']+anim['bytes']
        if anim['kind']!='animation' or combined>capacity:raise ValueError('Extended kind exceeds complete bank')
        row['fields'][2:4]=[shape['index'],anim['index']]
        row.update(combined_bank_bytes=combined,shape_installed=True,resource_ready=True)
        struct.pack_into('>6h',module,KIND_TABLE+16+row['source_kind']*KIND_STRIDE,*row['fields'])
    code,compiled=compile_part('equipment_resources',output/'equipment_resources',defines=(
        'AF_V3_PLAYER_MOTION=1','AF_V3_EQUIPMENT_KINDS=1','AF_V3_EQUIPMENT_RIGS=1',
        f'AF_V3_EQUIPMENT_CAPACITY={capacity}u'),extra_sources=('overlays/v3/equipment_resources.S',))
    if (len(code)>KIND_TABLE or compiled['symbols']!=old['code']['symbols']
            or len(code)!=old['code']['bytes'] or sha256(module[:len(code)])!=old['code']['sha256']
            or any(module[len(code):KIND_TABLE])):
        raise ValueError('Resource refresh changes public entries or checked code bounds')
    module[:KIND_TABLE]=code+bytes(KIND_TABLE-len(code))
    # The resident reservation and module size are unchanged; keep this copy
    # at its current VROM instead of accumulating another obsolete module.
    at=old['blob_offset'];blob[at:at+len(module)]=module
    if BLOB+len(blob)>END:raise ValueError('Extended equipment exceeds shared ROM storage')
    report.update(code=compiled,vrom=BLOB+at,blob_offset=at,sha256=sha256(module),
                  crc32=zlib.crc32(module),additional_resident_bytes=0)
    report['animated_rigs'].update(allocation=allocation,
        resource_indices=sorted(r['index'] for r in report['records'] if r['type']==1),
        model_bytes=sum(r['bytes'] for r in report['records'] if r['type']==1))
    report['animated_rigs'].setdefault('extensions',[]).append(dict(evidence=evidence,
        source_categories=list(categories),source_indices=added,joint_vectors=vectors,
        retired_module_reuse=reuse,model_bytes=sum(len(a) for a in assets.values()),
        player_actions_installed=False,inventory_previews_installed=False,profile_changed=False))
    report['player_motion']['owner_sha256']=sha256(owner)
    report['player_actions']['owner_sha256']=sha256(owner)
    return report,{PLAYER_VROM:bytes(owner)}


def retired_module_space(base,prior,blob,needed):
    """Find a hash-bound superseded resident copy, rejecting every live overlap.

    Each predecessor receipt is verified through its descendant's exact hash.
    Only former whole equipment modules qualify, never arbitrary zero padding
    or reserved item slots. DMA mappings and current resource records are live.
    """
    files=by_vrom(base);physical=files[BLOB].pstart;current=prior['equipment_resources']
    live=[(0,PACKAGE_SIZE+0x200000),(current['blob_offset'],current['blob_offset']+current['bytes'])]
    for v,entry in files.items():
        if v==BLOB or entry.pstart==0xFFFFFFFF:continue
        live.append((entry.pstart-physical,(entry.pend or entry.pstart+entry.size)-physical))
    def address(value):
        if type(value) is int:return value
        if isinstance(value,str):
            try:return int(value,16)
            except ValueError:pass
        return None
    def resources(value):
        if isinstance(value,dict):
            lengths=[value[k] for k in ('bytes','object_bytes','model_bytes','animation_bytes')
                     if type(value.get(k)) is int and value[k]>0]
            if type(value.get('blob_offset')) is int and lengths:
                at=value['blob_offset'];live.append((at,at+max(lengths)))
            for key,item in value.items():
                if key.endswith('vrom') and (at:=address(item)) is not None and BLOB<=at<END:
                    live.append((at-BLOB,at-BLOB+max(lengths,default=1)))
                resources(item)
        elif isinstance(value,list):
            for item in value:resources(item)
    resources(prior)
    receipt=prior;seen=set()
    while pin:=receipt.get('shared_runtime_refresh',{}).get('base'):
        path=(ROOT/pin['directory']/'build.json').resolve()
        if not path.is_relative_to(ROOT/'build') or path in seen:
            raise ValueError('Invalid or cyclic equipment receipt lineage')
        seen.add(path);raw=path.read_bytes()
        if sha256(raw)!=pin['report_sha256']:raise ValueError('Changed predecessor equipment receipt')
        receipt=json.loads(raw);candidate=receipt.get('equipment_resources')
        if not candidate:break
        start=candidate['blob_offset'];size=candidate['bytes'];end=start+size
        if (size<needed or start%16 or end>len(blob)
                or any(a<end and start<b for a,b in live)
                or sha256(blob[start:end])!=candidate['sha256']):continue
        return dict(blob_offset=start,bytes=size,used_bytes=needed,
            predecessor_report=str(path.relative_to(ROOT)),predecessor_report_sha256=sha256(raw),
            retired_module_sha256=candidate['sha256'],live_ranges_checked=len(live),
            original_sha256=sha256(base))
    return None


def install(prior, blob, core, original, output, art_path):
    if prior.get('equipment_resources'):
        raise ValueError('Equipment resources are already installed; preserve their stable indices')
    if PACKAGE_RAM+PACKAGE_SIZE!=RAM or RAM+SIZE>prior['furniture']['bank_pool']['start']:
        raise ValueError('Equipment resident region overlaps the package or model pool')
    contract=native_contract(original,core)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    assets,records,evidence=prepared_resources(source,art_path)
    # Append before the caller restores the checked catalogue/shop tail.
    for row in records:
        blob.extend(bytes(-len(blob)%16));at=len(blob);asset=assets[row['source_index']]
        row.update(vrom=BLOB+at,blob_offset=at)
        blob.extend(asset)
    code,compiled=compile_part('equipment_resources',output/'equipment_resources')
    module=bytearray(SIZE)
    if len(code)>TABLE:raise ValueError('Equipment code exceeds its reservation')
    module[:len(code)]=code
    struct.pack_into('>4I',module,TABLE,MAGIC,1,COUNT,16)
    for row in records:
        at=TABLE+16+row['source_index']*16
        struct.pack_into('>4I',module,at,row['vrom'],row['bytes'],row['pointer'],row['type'])
    struct.pack_into('>4I',module,SIZE-16,*([GUARD]*4))
    blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(module)
    if BLOB+len(blob)>END:raise ValueError('Equipment resources exceed import ROM storage')
    guard_incoming(bytes(core),len(core),CODE_RAM,[(a-CODE_RAM,8) for a,_,_ in ENTRIES])
    hooks=[]
    for entry,end,name in ENTRIES:
        target=compiled['symbols'][name];offset=entry-CODE_RAM
        if not RAM<=target<RAM+TABLE or target%4:raise ValueError('Equipment helper escapes code reservation')
        before=core[offset:offset+8];after=struct.pack('>II',jump(target),0)
        core[offset:offset+8]=after
        hooks.append(dict(entry=entry,end=end,helper=name,target=target,before=before.hex(),after=after.hex()))
    return dict(format='AFV3-EQUIPMENT-RESOURCES-1',records=records,evidence=evidence,
        code=compiled,hooks=hooks,native_contract=contract,ram=RAM,bytes=SIZE,
        vrom=BLOB+at,blob_offset=at,sha256=sha256(module),crc32=zlib.crc32(module),
        table_ram=RAM+TABLE,first_index=FIRST,source_slots=COUNT,
        additional_resident_bytes=SIZE,saved_format_changed=False,saved_profile_changed=False,
        item_bank_bytes_changed=False,logical_imports_added=0,player_actions_installed=False,
        ordinary_menu_reload_tested=False,web_patcher_enabled=False)


def install_player_motion(base,prior,blob,core,original,output):
    """Extend the existing category module and the native player's readers."""
    from v3_npc_draw import relocation_offsets
    old=prior.get('equipment_resources')
    if not old or old.get('player_motion'):
        raise ValueError('Player motion needs one complete, not-yet-extended held-resource module')
    at=old['blob_offset'];module=bytearray(blob[at:at+SIZE])
    if (len(module)!=SIZE or sha256(module)!=old['sha256'] or old['ram']!=RAM
            or old['vrom']!=BLOB+at or old['bytes']!=SIZE
            or any(module[PLAYER_BRIDGE:TABLE]) or any(module[PLAYER_TABLE:SIZE-16])):
        raise ValueError('Changed equipment module or occupied player reservations')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    assets,records,mask,evidence=player_resources(source,original)
    native=by_vrom(original);files=by_vrom(base);native_core=native[CODE_VROM].extract(original)
    ranges=[(a,b) for a,b,_ in PLAYER_ENTRIES]+[(0x800B11F8,0x800B1264),
        (0x800B12A0,0x800B12C8),(0x800B1D94,0x800B1DE8),(0x8010BD20,0x8010BF30)]
    for a,b in ranges:
        if core[a-CODE_RAM:b-CODE_RAM]!=native_core[a-CODE_RAM:b-CODE_RAM]:
            raise ValueError('Changed native player animation consumer/table')
    bounds=struct.unpack_from('>131I',native_core,0x8010BD20-CODE_RAM)
    if max(b-a-8 for a,b in zip(bounds,bounds[1:]))!=PLAYER_CAPACITY:
        raise ValueError('Changed native player animation buffer capacity')
    for row in records:
        blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(assets[row['source_index']])
        row.update(vrom=BLOB+position,blob_offset=position)
    code,compiled=compile_part('equipment_resources',output/'equipment_resources',defines=('AF_V3_PLAYER_MOTION=1',))
    if len(code)>PLAYER_BRIDGE:raise ValueError('Player resource helper exceeds code reservation')
    module[:TABLE]=code+bytes(TABLE-len(code))
    struct.pack_into('>4I',module,PLAYER_TABLE,0x4146504D,1,PLAYER_COUNT,16)
    for row in records:
        struct.pack_into('>4I',module,PLAYER_TABLE+16+16*row['source_index'],
                         row['vrom'],row['bytes'],row['pointer'],row['type'])
    module[PLAYER_MASK:PLAYER_MASK+27]=mask
    # The native part-copy prologue contains no PC-relative instructions.
    bridge=core[0x800B1DE8-CODE_RAM:0x800B1DF0-CODE_RAM]
    if bridge!=bytes.fromhex('27BDFF80AFBF001C'):raise ValueError('Changed native part-copy prologue')
    module[PLAYER_BRIDGE:PLAYER_BRIDGE+16]=bridge+struct.pack('>II',jump(0x800B1DF0),0)
    hooks=[]
    old_hooks={r['entry']:r for r in old['hooks']}
    guard_incoming(bytes(core),len(core),CODE_RAM,[(a-CODE_RAM,8) for a,_,_ in PLAYER_ENTRIES])
    for entry,end,name in (*ENTRIES,*PLAYER_ENTRIES):
        offset=entry-CODE_RAM;before=bytes(core[offset:offset+8])
        if entry in old_hooks and before.hex()!=old_hooks[entry]['after']:
            raise ValueError('Changed installed held-resource hook')
        target=compiled['symbols'][name]
        if not RAM<=target<RAM+PLAYER_BRIDGE:raise ValueError('Player resource hook exceeds code reservation')
        after=struct.pack('>II',jump(target),0);core[offset:offset+8]=after
        hooks.append(dict(entry=entry,end=end,helper=name,target=target,before=before.hex(),after=after.hex()))
    owner=bytearray(files[PLAYER_VROM].extract(base));native_owner=native[PLAYER_VROM].extract(original)
    reloc=files[PLAYER_RELOC].extract(base)
    if reloc!=native[PLAYER_RELOC].extract(original):raise ValueError('Changed player relocation resource')
    slots=relocation_offsets(reloc,len(owner));owner_hooks=[]
    specs=((0x808B468C,0x808B46C4,'af_v3_player_animation_pointer',(16,24)),
           (0x808B5B38,0x808B5B60,'af_v3_player_animation_part',(12,24)))
    guard_incoming(owner,struct.unpack_from('>I',reloc)[0],PLAYER_RAM,
                   [(a-PLAYER_RAM,b-a) for a,b,_,_ in specs])
    for start,end,name,retained in specs:
        off=start-PLAYER_RAM;n=end-start;before=bytes(owner[off:off+n])
        if (before!=native_owner[off:off+n]
                or slots & set(range(off,off+n,4))!={off+i for i in retained}):
            raise ValueError('Changed player animation getter/relocations')
        words=list(struct.unpack('>'+str(n//4)+'I',before))
        if name.endswith('pointer'):
            # Native pointer HI/LO remain at offsets 16 and 24.
            patch=[0x2C810082,0x10200008,0x00047080,0,*words[4:7],
                   0x03E00008,0x00601025,0,jump(compiled['symbols'][name]),0,0,0]
        else:
            # Native part-table HI/LO remain at offsets 12 and 24.
            patch=[0x2C810082,0x10200006,0,*words[3:7],0,jump(compiled['symbols'][name]),0]
        after=struct.pack('>'+str(len(patch))+'I',*patch)
        if len(after)!=n or any(after[i:i+4]!=before[i:i+4] for i in retained):
            raise ValueError('Player getter changed its relocated native table binding')
        owner[off:off+n]=after
        owner_hooks.append(dict(entry=start,end=end,helper=name,before=before.hex(),after=after.hex(),
                                retained_relocations=list(retained)))
    blob[at:at+SIZE]=module
    if BLOB+len(blob)>END:raise ValueError('Player motions exceed import ROM storage')
    report=copy.deepcopy(old)
    report.update(code=compiled,hooks=hooks[:len(ENTRIES)],sha256=sha256(module),crc32=zlib.crc32(module),
                  additional_resident_bytes=0)
    report['player_motion']=dict(records=records,evidence=evidence,hooks=hooks[len(ENTRIES):],
        owner_hooks=owner_hooks,owner_vrom=PLAYER_VROM,owner_reloc=PLAYER_RELOC,owner_ram=PLAYER_RAM,
        owner_sha256=sha256(owner),owner_bytes=len(owner),reloc_sha256=sha256(reloc),
        bounds=list(bounds),native_ranges=[dict(start=a,end=b,sha256=sha256(native_core[a-CODE_RAM:b-CODE_RAM])) for a,b in ranges],
        mask_hex=mask.hex(),table_offset=PLAYER_TABLE,mask_offset=PLAYER_MASK,
        bridge_offset=PLAYER_BRIDGE,first_index=PLAYER_FIRST,source_slots=PLAYER_COUNT,
        animation_buffer_bytes_changed=False,player_actions_installed=False)
    return report,{PLAYER_VROM:bytes(owner)}


def install_kind_readers(base,prior,blob,core,original,output):
    """Connect all six kind-indexed readers without enabling unfinished actions."""
    from v3_npc_draw import relocation_offsets
    old=prior.get('equipment_resources')
    if not old or not old.get('player_motion') or old.get('kind_readers'):
        raise ValueError('Equipment kind readers require the existing player-motion module')
    at=old['blob_offset'];module=bytearray(blob[at:at+SIZE])
    table_end=KIND_TABLE+16+KIND_COUNT*KIND_STRIDE
    if (len(module)!=SIZE or sha256(module)!=old['sha256'] or old['ram']!=RAM
            or old['vrom']!=BLOB+at or old['bytes']!=SIZE
            or old['code']['bytes']>KIND_TABLE or table_end>PLAYER_BRIDGE
            or any(module[KIND_TABLE:PLAYER_BRIDGE])):
        raise ValueError('Changed held-resource module or occupied kind-table reservation')
    files=by_vrom(base);native=by_vrom(original)
    owner=bytearray(files[PLAYER_VROM].extract(base));native_owner=native[PLAYER_VROM].extract(original)
    reloc=files[PLAYER_RELOC].extract(base)
    if (sha256(owner)!=old['player_motion']['owner_sha256']
            or reloc!=native[PLAYER_RELOC].extract(original)):
        raise ValueError('Changed player owner or relocation resource')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                  (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    bindings=kind_bindings(source);description=motion(source)
    if len(bindings['rows'])!=KIND_COUNT or KIND_FIRST+KIND_COUNT>128:
        raise ValueError('Equipment kinds exceed native signed-byte storage')
    report=copy.deepcopy(old);motion_report=report['player_motion']
    required={r[key] for r in bindings['rows'] for key in ('player_animation','tumble','getup')}
    installed={r['source_index'] for r in motion_report['records']}
    new_motion=[]
    for index in sorted(required-installed):
        pointers=description['selector_tables']['player_data']['pointers']
        desc=animation(source,pointers[index*4][3],joints=26)
        asset,compiled_motion=compile_animations(source,[desc])
        if len(asset)>PLAYER_CAPACITY:raise ValueError('Equipment transition exceeds native player-animation bank')
        part=source.rel[source.sections[4][0]+motion_report['evidence']['tables']['player_part']['offset']+index]
        if part>=5:raise ValueError('Equipment transition uses an unsupported part mask')
        blob.extend(bytes(-len(blob)%16));position=len(blob);blob.extend(asset)
        row=dict(source_index=index,index=PLAYER_FIRST+index,bytes=len(asset),
            pointer=0x06000000+compiled_motion['headers'][0]['native_offset'],type=part,
            sha256=sha256(asset),source=desc,compiled=compiled_motion,vrom=BLOB+position,blob_offset=position)
        motion_report['records'].append(row);new_motion.append(row)
        slot=PLAYER_TABLE+16+16*index
        if any(module[slot:slot+16]):raise ValueError('New equipment motion overwrites a live resource')
        struct.pack_into('>4I',module,slot,row['vrom'],row['bytes'],row['pointer'],row['type'])
    motion_report['records'].sort(key=lambda r:r['source_index'])
    code,compiled=compile_part('equipment_resources',output/'equipment_resources',
        defines=('AF_V3_PLAYER_MOTION=1','AF_V3_EQUIPMENT_KINDS=1'))
    if len(code)>KIND_TABLE:raise ValueError('Shared equipment code exceeds kind-table boundary')
    module[:KIND_TABLE]=code+bytes(KIND_TABLE-len(code))
    struct.pack_into('>4I',module,KIND_TABLE,0x41464B44,1,KIND_COUNT,KIND_STRIDE)
    resources={r['source_index']:r for r in old['records']};rows=[]
    for row in bindings['rows']:
        values=[]
        for _,_,field,_ in KIND_ENTRIES:
            value=row[field]
            if field in ('player_animation','tumble','getup'):value+=PLAYER_FIRST
            elif field in ('shape','animation'):value=FIRST+value if value in resources else -1
            values.append(value)
        shape=resources.get(row['shape']);anim=resources.get(row['animation'])
        combined=(shape['bytes']+(anim['bytes'] if anim else 0)) if shape else None
        if combined is not None and combined>CAPACITY:
            raise ValueError('Equipment model and animation exceed combined native bank')
        row=dict(row,native_kind=KIND_FIRST+row['source_kind'],fields=values,
            combined_bank_bytes=combined,shape_installed=shape is not None,
            resource_ready=shape is not None and (row['animation']==-1 or anim is not None),
            selectable=False,player_actions_installed=False)
        rows.append(row)
        struct.pack_into('>6h',module,KIND_TABLE+16+row['source_kind']*KIND_STRIDE,*values)
    # Recompile and rebind the existing readers; their resources and original
    # lookup meanings remain unchanged even if helper code addresses move.
    for hooks in (report['hooks'],motion_report['hooks']):
        for hook in hooks:
            off=hook['entry']-CODE_RAM;before=bytes(core[off:off+8])
            if before.hex()!=hook['after']:raise ValueError('Changed installed equipment core hook')
            target=compiled['symbols'][hook['helper']];after=struct.pack('>II',jump(target),0)
            core[off:off+8]=after;hook.update(before=before.hex(),after=after.hex(),target=target)
    for hook in motion_report['owner_hooks']:
        off=hook['entry']-PLAYER_RAM;n=hook['end']-hook['entry'];before=bytes(owner[off:off+n])
        if before.hex()!=hook['after']:raise ValueError('Changed installed player motion getter')
        old_jump=struct.pack('>I',jump(old['code']['symbols'][hook['helper']]))
        new_jump=struct.pack('>I',jump(compiled['symbols'][hook['helper']]))
        positions=[i for i in range(0,n,4) if before[i:i+4]==old_jump]
        if len(positions)!=1:raise ValueError('Ambiguous installed player helper call')
        position=positions[0];after=before[:position]+new_jump+before[position+4:]
        owner[off:off+n]=after;hook.update(before=before.hex(),after=after.hex())
    slots=relocation_offsets(reloc,len(owner));hooks=[]
    guard_incoming(owner,struct.unpack_from('>I',reloc)[0],PLAYER_RAM,
                   [(a-PLAYER_RAM,40) for a,_,_,_ in KIND_ENTRIES])
    for column,(entry,table,field,missing) in enumerate(KIND_ENTRIES):
        off=entry-PLAYER_RAM;before=bytes(owner[off:off+40]);original_words=struct.unpack('>10I',before)
        table_off=table-PLAYER_RAM;table_bytes=owner[table_off:table_off+KIND_FIRST]
        if (before!=native_owner[off:off+40] or table_bytes!=native_owner[table_off:table_off+KIND_FIRST]
                or slots & set(range(off,off+40,4))!={off+12,off+24}
                or original_words[:3]!=(0x04800006,0x28810024,0x10200004)
                or original_words[5]!=0x03E00008
                or ((original_words[3]&0xFFFF)<<16)+struct.unpack('>h',before[26:28])[0]!=table):
            raise ValueError('Changed complete native equipment kind getter/table')
        patch=[0x2C810024,0x10200005,0,*original_words[3:7],
               jump(compiled['symbols']['af_v3_equipment_kind_field']),0x24050000|column,0]
        after=struct.pack('>10I',*patch);owner[off:off+40]=after
        hooks.append(dict(entry=entry,end=entry+40,field=field,column=column,missing=missing,
            table_ram=table,table_hex=table_bytes.hex(),before=before.hex(),after=after.hex(),
            retained_relocations=[12,24]))
    # The actual equipment selector must remain original until category actions,
    # inventory, selected profiles, and all dependent permissions are integrated.
    selector_start,selector_end=0x808BD3F8-PLAYER_RAM,0x808BD584-PLAYER_RAM
    if owner[selector_start:selector_end]!=native_owner[selector_start:selector_end]:
        raise ValueError('Equipment selector enables unapproved item identities')
    blob[at:at+SIZE]=module
    if BLOB+len(blob)>END:raise ValueError('Equipment kind resources exceed ROM storage')
    motion_report.update(owner_sha256=sha256(owner))
    report.update(code=compiled,sha256=sha256(module),crc32=zlib.crc32(module),additional_resident_bytes=0)
    report['kind_readers']=dict(format='AFV3-EQUIPMENT-KINDS-1',rows=rows,
        source_functions=bindings['functions'],source_tables=bindings['tables'],
        equipment_source_functions=bindings['equipment']['functions'],
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()),
        owner_hooks=hooks,new_player_motions=new_motion,table_offset=KIND_TABLE,
        first_index=KIND_FIRST,count=KIND_COUNT,stride=KIND_STRIDE,
        selector_sha256=sha256(owner[selector_start:selector_end]),selector_changed=False,
        item_bank_bytes_changed=False,actions_installed=False,logical_imports_added=0)
    return report,{PLAYER_VROM:bytes(owner)}
