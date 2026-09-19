"""Shared native resource loading for checked held models and motion data.

This installs resources, not inventory identities or player action support.
All item choices and saved profiles remain unchanged.
"""
import json
import copy
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
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
    'overlays/v3/equipment_resources.c','overlays/v3/equipment_resources.ld','overlays/v3/startup.c')
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
