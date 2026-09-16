"""Shared native resource loading for checked held models and motion data.

This installs resources, not inventory identities or player action support.
All item choices and saved profiles remain unchanged.
"""
import json
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from v3_asset_loader import BLOB, ROOT, compile_part
from v3_import_storage import PACKAGE_RAM, END, jump
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_pipeline import Source, prepare_models
from v3_handheld_items import scan, descriptor, motion
from v3_keyframes import compile_animations
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


def prepared_resources(source, art_path):
    """Reuse checked graphics and pack each complete motion for native DMA."""
    art_path=art_path.resolve();raw=(art_path/'art.json').read_bytes();art=json.loads(raw)
    if (art['format']!='AFV3-HANDHELD-PREPARED-ASSETS-1' or art['version']!=1
            or art['source_rel_sha256']!=sha256(source.rel)
            or art['source_symbols_sha256']!=sha256(source.symbols.encode())):
        raise ValueError('Changed handheld artwork source/format')
    inventory=scan(source)
    rows={r['shape_index']:r for r in inventory['rows'] if r['asset_ready']}
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
