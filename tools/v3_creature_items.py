"""One source-derived carried/display path for the fish and insect categories."""
import copy
import json
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import ROOT,BLOB,MODULE_RAM,compile_part
from v3_import_storage import ROWS,ROWS_RAM,ITEMS,slot,jump
from v3_registry import (CREATURE_DISPLAYS,CREATURE_PARENT_REGISTRY_VERSION,
    creature_parent_identity,furniture_representation_identity)
from v3_room_aliases import creature_parent
from v3_furniture_rigs import EMBEDDED_CATEGORY,CREATURE_STATIC_CATEGORY

RAM,SIZE,TABLE,GUARD=0x804FF100,0xF00,0x800,0xAF435249
SOURCES=('tools/v3_creature_items.py','tools/v3_registry.py','tools/v3_room_aliases.py',
    'tools/v3_furniture_install.py','tools/v3_furniture_pipeline.py','tools/v3_room_goods.py',
    'tools/v3_asset_loader.py','overlays/v3/creature_items.c','overlays/v3/creature_items.ld',
    'overlays/v3/surface_bootstrap.c','translations/provenance.json')
TABLES={
    'fish_price_table':(82,'4432b2d0c52a896812341a08c7afcd33affff5277f92f4e63935f2c93585535b'),
    'insect_price_table':(92,'4bd112dfe4dbf06aec27b6d3bc2a5484e40496967b8a86ebb8a73bc9deef26f5'),
    'itemName_fish':(640,'706b161c90f072db075550849416febb4e96a86e0e3190f86d0c2ed64ca14f99'),
    'itemName_insect':(720,'8a64af80770fe8cc1a1f85d5739bd5a9e64ff601bbbcc5c8ee941662f1c933f2'),
}
NATIVE_FUNCTIONS=(
    (0x800BEFCC,0x800BF10C,'cc2f486a63f4266eb6249f27362d1365ba116b56e14891a8447d0a157b7ac8bb'),
    (0x800BF10C,0x800BF230,'f022be17120922ce15db644ff63308dff25e150537320bed7659bbc3ac6602e5'),
)


def source_records(source):
    tables={};receipts={}
    for name,(size,digest) in TABLES.items():
        raw=source.raw(name)
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed complete creature table: '+name)
        tables[name]=raw;receipts[name]=dict(offset=source.symbol(name)[0],bytes=size,sha256=digest)
    functions=[]
    for at,size,digest in ((0x78408,36,'7bf2f0cfba36247d0178e9df17c8462a710ab2dbb629273dfc3bfe865e094ca3'),
            (0x784E0,544,'3f45cc5bf10f883d41575bc4f66cd1f8cfa1f86e46795ec386baaf412a7edb2b')):
        raw,receipt=source.function(at)
        if len(raw)!=size or sha256(raw)!=digest:raise ValueError('Changed source creature price reader')
        functions.append(receipt)
    rows=[]
    for display in CREATURE_DISPLAYS:
        # Source placement functions establish the parent, not name similarity.
        parent=creature_parent(source,display,0x80 if display<0x1C68 else 0x40)
        donor=int(parent['parent_item_id'],16);item=creature_parent_identity(donor)
        index,destination=furniture_representation_identity(display)
        kind=parent['category'];prices=tables[kind+'_price_table'];source_index=donor&255
        if prices[-2:]!=b'\xff\xff' or source_index>=len(prices)//2-1:
            raise ValueError('Creature price index escapes sentinel-bounded table')
        price=struct.unpack_from('>H',prices,source_index*2)[0]
        rows.append(dict(id=parent['parent_id'],source_item_id=f'{donor:04X}',item_id=f'{item:04X}',
            source_display_item_id=f'{display:04X}',display_item_id=f'{destination:04X}',runtime_index=index,
            category=kind,native_category=8 if kind=='fish' else 18,source_index=source_index,
            name=parent['parent_name'],name_sha256=parent['parent_name_sha256'],
            name_source_symbol=parent['parent_name_symbol'],name_source_index=source_index,
            price_word=price,parent_source=parent,ready=False,selected=False))
    rows.sort(key=lambda r:r['item_id'])
    if (len(rows)!=17 or len({r['item_id'] for r in rows})!=17 or
            {r['item_id'] for r in rows}!={f'{i:04X}' for i in (*range(0x2320,0x2329),*range(0x2D20,0x2D28))}):
        raise ValueError('Incomplete additive creature identity category')
    return rows,dict(registry_version=CREATURE_PARENT_REGISTRY_VERSION,tables=receipts,price_functions=functions,
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()))


def encode(rows):
    if len(rows)!=17 or len({r['item_id'] for r in rows})!=17:
        raise ValueError('Creature metadata requires all fixed parent identities')
    raw=bytearray(struct.pack('>4I',0x41464349,1,len(rows),28))
    for row in rows:
        parent=creature_parent_identity(int(row['source_item_id'],16))
        index,display=furniture_representation_identity(int(row['source_display_item_id'],16))
        name=row['name'].encode('ascii').ljust(16,b' ')
        if (row['item_id']!=f'{parent:04X}' or row['display_item_id']!=f'{display:04X}' or
                row['runtime_index']!=index or len(name)!=16 or sha256(name)!=row['name_sha256'] or
                row['native_category']!=(8 if parent>>8==0x23 else 18) or
                row['ready'] is not False or row['selected'] is not False):
            raise ValueError('Changed creature identity, official name, or incomplete readiness')
        raw.extend(struct.pack('>HHHBBI',parent,display,row['price_word'],row['native_category'],row['source_index'],0)+name)
    return bytes(raw)


def native_contract(core,prior):
    normalized=bytearray(core);proof=[]
    for hook in prior.get('equipment_resources',{}).get('creature_items',{}).get('hooks',[]):
        if hook['kind'] not in ('display','pocket'):continue
        at=hook['address']-CODE_RAM
        if normalized[at:at+8].hex()!=hook['after']:raise ValueError('Changed creature conversion wrapper')
        normalized[at:at+8]=bytes.fromhex(hook['before'])
    for hook in prior['clothing']['display']['conversion']['hooks']:
        at=hook['entry']-CODE_RAM;before=bytes.fromhex(hook['before']);after=bytes.fromhex(hook['after'])
        if normalized[at:at+8]!=after:raise ValueError('Changed native room conversion hook')
        normalized[at:at+8]=before
    for start,end,digest in NATIVE_FUNCTIONS:
        if sha256(normalized[start-CODE_RAM:end-CODE_RAM])!=digest:
            raise ValueError('Changed complete native creature conversion')
        proof.append(dict(address=start,bytes=end-start,sha256=digest))
    categories=[]
    for category,expected,address in ((3,8,0x8010B09C),(13,18,0x8010B30C)):
        pointer=u32(core,0x8010B334-CODE_RAM+category*4)
        if pointer!=address or core[address-CODE_RAM:address-CODE_RAM+32]!=bytes([expected])*32:
            raise ValueError('Changed complete native creature category')
        categories.append(dict(category=category,address=address,count=32,value=expected))
    return dict(conversions=proof,categories=categories,native_herabuna_item='2301',native_herabuna_display='1C2C')


def lifecycle(descriptor):
    category=descriptor['callback_adapter']['category'];parent=descriptor.get('creature_parent')
    if category not in (EMBEDDED_CATEGORY,CREATURE_STATIC_CATEGORY) or not parent:return None
    return dict(category='creature-parent-room',source_parent=parent['parent_item_id'],
        source_display=parent['display_item_id'],embedded=category==EMBEDDED_CATEGORY,
        interaction=descriptor['interaction_flags'])


def install(base,prior,blob,core,module,output,directory):
    from v3_furniture_pipeline import Source,PreparedAssets,prepare
    from v3_furniture_install import profile,provenance_patch
    from v3_room_rig_runtime import bind_profiles,VTABLE
    from v3_furniture_capacity import checked as checked_capacity
    from v3_resource_capacity import checked_limit
    from apply_translation import write_new
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    bind_profiles(source,base,prior)
    rows,receipt=source_records(source);table=encode(rows);native=native_contract(core,prior)
    equipment=copy.deepcopy(prior['equipment_resources'])
    if equipment.get('creature_items'):raise ValueError('Creature parent path already installed')
    session=equipment['console_images']['emulator']['state']
    if session['ram']+session['bytes']>RAM or RAM+SIZE>prior['furniture']['bank_pool']['start']:
        raise ValueError('Creature packet overlaps console state or model banks')
    def reservations(value):
        if isinstance(value,dict):
            if isinstance(value.get('ram'),int) and isinstance(value.get('bytes'),int):
                yield value['ram'],value['bytes']
            for v in value.values():yield from reservations(v)
        elif isinstance(value,list):
            for v in value:yield from reservations(v)
    if any(at<RAM+SIZE and RAM<at+n for at,n in reservations(equipment)):
        raise ValueError('Creature packet intersects a retained allocation')
    directory=directory.resolve();art=json.loads((directory/'art.json').read_bytes())
    if not directory.is_relative_to(ROOT/'build') or art['format']!='AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1':
        raise ValueError('Creature path requires complete prepared category assets')
    assets={r['item_id']:r for r in art['objects']}
    if set(assets)!={r['source_display_item_id'] for r in rows}:raise ValueError('Incomplete prepared creature category')
    cache=PreparedAssets(source,[directory]);rigs=equipment['room_rigs']
    bindings={r['source_item_id']:r for r in rigs['rows']};profiles=[]
    limit=checked_limit(base,prior);bank=checked_capacity(base,prior)
    for row in rows:
        donor=row['source_display_item_id'];art_row=assets[donor];prepared=prepare(source,int(donor,16))
        if cache.reuse(source,donor,prepared) is None:raise ValueError('Changed complete prepared creature model')
        data=(directory/art_row['object_file']).read_bytes();descriptor=prepared[0];embedded=lifecycle(descriptor)['embedded']
        if descriptor['creature_parent']!=row['parent_source']:raise ValueError('Creature art and parent disagree')
        if embedded:
            binding=bindings[donor]
            if (binding['mode']!=13 or binding['profile_installed'] or binding['bytes']!=len(data) or
                    binding['sha256']!=sha256(data) or blob[binding['blob_offset']:binding['blob_offset']+len(data)]!=data):
                raise ValueError('Missing complete installed creature rig')
            sound=descriptor['callback_adapter'].get('level_sound')
            if sound and binding['last']!=sound['source_sound_id']:raise ValueError('Creature sound callback is not installed')
            vrom=binding['vrom'];vtable=VTABLE
        else:
            blob.extend(bytes(-len(blob)%16));vrom=BLOB+len(blob);blob.extend(data);vtable=0
        destination=int(row['display_item_id'],16);index=row['runtime_index'];i=slot(destination)
        if (any(blob[ROWS+i*80:ROWS+(i+1)*80]) or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]) or
                blob[0x40+i//8]&(1<<(i&7))):raise ValueError('Creature display overwrites occupied or selected identity')
        generated=copy.deepcopy(art_row)
        generated.update(room_runtime=dict(vrom=vrom,vtable=vtable),room_lifecycle=lifecycle(descriptor))
        native_profile=profile(generated,vrom,limit=limit,model_capacity=bank)
        # Inactive complete profile. Selection and readiness are enabled together
        # only when the remaining carried/catching/collection consumers exist.
        profile_record=struct.pack('>HHI',index,destination,0)+native_profile+bytes(4)
        metadata=struct.pack('>HHHBB',index,destination,0,descriptor['size_code'],0)+bytes(20)+struct.pack('>HH',int(row['item_id'],16),0)
        blob[ROWS+i*80:ROWS+(i+1)*80]=profile_record;blob[ITEMS+i*32:ITEMS+(i+1)*32]=metadata
        if embedded:binding.update(profile_installed=True,parent_selectable=False)
        profiles.append(dict(source_item_id=donor,item_id=row['display_item_id'],parent_item_id=row['item_id'],
            runtime_index=index,profile_ram=ROWS_RAM+i*80+8,profile_hex=native_profile.hex(),
            profile_record_sha256=sha256(profile_record),item_record_sha256=sha256(metadata),
            object_vrom=vrom,object_bytes=len(data),object_sha256=sha256(data),reused_asset=embedded,
            room_runtime=generated['room_runtime'],room_lifecycle=generated['room_lifecycle'],
            source=art_row,selected=False))
    surface=prior['room_surfaces']['items'];hooks=[];defines=[]
    for h in surface['hooks']:
        hooks.append(dict(kind=h['kind'],address=h['address'],prior=h['target'],
            before=h['after'],symbol='af_v3_creature_item_'+h['kind']))
    for h in prior['clothing']['display']['conversion']['hooks']:
        hooks.append(dict(kind=h['kind'],address=h['entry'],prior=h['target'],
            before=h['after'],symbol='af_v3_creature_room_'+h['kind']))
    for h in hooks:defines.append(f'AF_CREATURE_PRIOR_{h["kind"].upper()}=0x{h["prior"]:X}u')
    code,compiled=compile_part('creature_items',output/'creature_items',defines=tuple(defines))
    if len(code)>TABLE or TABLE+len(table)>SIZE-16:raise ValueError('Creature reader packet exceeds reservation')
    packet=bytearray(SIZE);packet[:len(code)]=code;packet[TABLE:TABLE+len(table)]=table
    packet[-16:]=struct.pack('>4I',*([GUARD]*4));blob.extend(bytes(-len(blob)%16));offset=len(blob);blob.extend(packet)
    if BLOB+len(blob)>limit:raise ValueError('Creature packet exceeds checked cartridge allocation')
    for hook in hooks:
        owner,origin=(module,MODULE_RAM) if hook['address']>=MODULE_RAM else (core,CODE_RAM)
        at=hook['address']-origin;before=bytes.fromhex(hook['before']);target=compiled['symbols'][hook['symbol']]
        if owner[at:at+8]!=before:raise ValueError('Changed complete creature predecessor entry')
        after=struct.pack('>2I',jump(target),0);owner[at:at+8]=after
        hook.update(target=target,after=after.hex())
    equipment['creature_items']=dict(format='AFV3-CREATURE-ITEMS-1',source=receipt,rows=rows,profiles=profiles,
        native=native,code=compiled,hooks=hooks,table_offset=TABLE,table_bytes=len(table),table_sha256=sha256(table),
        packet=dict(ram=RAM,bytes=SIZE,blob_offset=offset,vrom=BLOB+offset,sha256=sha256(packet),crc32=zlib.crc32(packet)),
        prepared=dict(directory=str(directory.relative_to(ROOT)),sha256=sha256((directory/'art.json').read_bytes())),
        names_prices_categories_installed=True,room_conversion_installed=True,room_profiles_installed=True,
        ready_items=0,profile_bits_enabled=0,additional_resident_bytes=SIZE,saved_format_changed=False,
        remaining=['carried models and icons','catching and releasing','collection and save-profile readers','spawn tables'],
        native_execution_tested=False,hardware_tested=False,web_patcher_enabled=False)
    attribution=provenance_patch(rows)
    if attribution:write_new(output/'provenance.patch',attribution.encode())
    return equipment,{}


def checked(base,report,source):
    """Bind the connected room path without promoting unfinished gameplay."""
    from v3_asset_loader import MODULE
    from v3_furniture_install import profile
    from v3_furniture_capacity import checked as checked_capacity
    from v3_resource_capacity import checked_limit
    r=report['equipment_resources'].get('creature_items')
    if not r:return None
    files=by_vrom(base);blob=files[BLOB].extract(base);core=files[CODE_VROM].extract(base)
    module=files[MODULE].extract(base);p=r['packet'];packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
    rows,receipt=source_records(source);table=encode(rows);code=r['code']
    if (r['format']!='AFV3-CREATURE-ITEMS-1' or r['rows']!=json.loads(json.dumps(rows)) or
            r['source']!=json.loads(json.dumps(receipt)) or p['ram']!=RAM or p['bytes']!=SIZE or
            p['vrom']!=BLOB+p['blob_offset'] or sha256(packet)!=p['sha256'] or
            zlib.crc32(packet)!=p['crc32'] or sha256(packet[:code['bytes']])!=code['sha256'] or
            any(packet[code['bytes']:TABLE]) or packet[TABLE:TABLE+len(table)]!=table or
            any(packet[TABLE+len(table):-16]) or packet[-16:]!=struct.pack('>4I',*([GUARD]*4)) or
            r['native']!=native_contract(core,report) or len(r['profiles'])!=17):
        raise ValueError('Changed complete creature parent packet or source')
    for hook in r['hooks']:
        owner,origin=(module,MODULE_RAM) if hook['address']>=MODULE_RAM else (core,CODE_RAM)
        target=code['symbols'][hook['symbol']]
        if (hook['target']!=target or not RAM<=target<RAM+code['bytes'] or
                owner[hook['address']-origin:hook['address']-origin+8]!=struct.pack('>2I',jump(target),0)):
            raise ValueError('Changed connected native creature hook')
    by_display={row['display_item_id']:row for row in rows}
    bank=checked_capacity(base,report);limit=checked_limit(base,report)
    for row in r['profiles']:
        parent=by_display[row['item_id']];i=slot(int(row['item_id'],16));art=copy.deepcopy(row['source'])
        if row['parent_item_id']!=parent['item_id']:raise ValueError('Changed creature display parent')
        art.update(room_runtime=row['room_runtime'],room_lifecycle=row['room_lifecycle'])
        raw=profile(art,row['object_vrom'],limit=limit,model_capacity=bank)
        profile_record=struct.pack('>HHI',row['runtime_index'],int(row['item_id'],16),0)+raw+bytes(4)
        data=blob[row['object_vrom']-BLOB:row['object_vrom']-BLOB+row['object_bytes']]
        metadata=blob[ITEMS+i*32:ITEMS+(i+1)*32]
        if (row['runtime_index']!=parent['runtime_index'] or sha256(data)!=row['object_sha256'] or
                blob[ROWS+i*80:ROWS+(i+1)*80]!=profile_record or
                sha256(profile_record)!=row['profile_record_sha256'] or sha256(metadata)!=row['item_record_sha256'] or
                row['profile_hex']!=raw.hex() or blob[0x40+i//8]&(1<<(i&7))):
            raise ValueError('Changed complete creature display profile, artwork, or activation')
    return r
