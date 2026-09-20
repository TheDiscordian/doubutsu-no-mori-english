"""Install a source-discovered furniture batch through the shared V3 readers.

No item IDs, model descriptions, theme membership lists, or family switches live
here. A pinned base receipt and converter output supply all item records.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, fix_checksum,
                   sha256, verified_rom, make_ups, apply_ups)
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP, ROOT, compile_part
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_pipeline import Source, LAYERS, prepare, metadata, identity_rows, draw_sequence, PENDING_MOVE_CATEGORY
from v3_garden_runtime import install_catalogue
from v3_import_storage import PACKAGE, PACKAGE_RAM, ROWS, ROWS_RAM, ITEMS, TABLE_END, END, slot
from v3_registry import furniture_source
import v3_furniture_behaviours as behaviours
import v3_furniture_placement as placement
import v3_furniture_rewards as rewards
import v3_camper_trade as camper_trade
import v3_furniture_palette as palette_fade
import v3_display_aliases as display_aliases
import v3_catalogue as catalogue
import v3_hra as hra
import v3_feng_shui as feng
import v3_shops as shops
import v3_resource_capacity as capacity

VERSION = 15
LOCK = ROOT/'config/v3-import-build.json'
STABLE = ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64'
STABLE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
SOURCES = capacity.SOURCES + ('tools/v3_furniture_pipeline.py', 'tools/v3_furniture_install.py', 'tools/map_artwork.py', 'tools/v3_room_aliases.py',
    'tools/v3_furniture_rigs.py', 'tools/v3_furniture_materials.py', 'tools/v3_keyframes.py',
    'tools/v3_furniture_art.py', 'tools/v3_registry.py', 'tools/v3_catalogue.py',
    'tools/v3_garden_runtime.py', 'tools/v3_shops.py', 'overlays/v3/catalogue.c',
    'overlays/v3/startup.c', 'translations/provenance.json',
    'tools/v3_camper_trade.py','tools/v3_camping_items.py','overlays/v3/camper_trade.c',
    'overlays/v3/camper_trade.h','overlays/v3/camper_trade.ld','overlays/v3/camper_trade_tail.S') + behaviours.SOURCES + placement.SOURCES + rewards.SOURCES + palette_fade.SOURCES + display_aliases.SOURCES


def inputs(lock=LOCK):
    pin = json.loads(lock.read_bytes())
    directory = (ROOT/pin['directory']).resolve()
    if not directory.is_relative_to(ROOT/'build'): raise ValueError('Base is not an ignored build')
    base = (directory/'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (directory/'build.json').read_bytes()
    report = json.loads(raw)
    if (sha256(base) != pin['rom_sha256'] or sha256(raw) != pin['report_sha256']
            or report['output_sha256'] != pin['rom_sha256'] or report['runtime_abi'] != pin['runtime_abi']
            or report.get('optional_composition_updated') or 'composition' in report):
        raise ValueError('Changed base cartridge, receipt, ABI, or selected-only base')
    return base, report


def profile(row, vrom, *, limit=END):
    n, offsets = row['object_bytes'], row['model_offsets']
    scalar = bytes.fromhex(row['native_profile_scalar_hex'])
    adapter=row.get('profile',{}).get('callback_adapter',{})
    fading = adapter.get('category') == 'switch-palette-fade'
    sequence = adapter.get('category') == 'constant-model-sequence'
    sound = adapter.get('category') == 'switch-trigger-sound'
    from v3_furniture_rigs import RIG_CATEGORIES,FIXED_CATEGORY
    from v3_furniture_materials import CATEGORY as MATERIAL_CATEGORY
    material=adapter.get('category')==MATERIAL_CATEGORY
    if adapter.get('category') in (FIXED_CATEGORY,PENDING_MOVE_CATEGORY):
        raise ValueError('Prepared resources have no implemented native lifecycle')
    rigged = adapter.get('category') in RIG_CATEGORIES
    layers = tuple(offsets) if rigged else tuple(adapter['model_order']) if fading or sequence or material else LAYERS
    if (limit not in (END,capacity.LIMIT) or not 0 < n <= 9216 or n%16 or vrom%16 or vrom+n > limit or len(scalar) != 16
            or not offsets or set(offsets)-set(layers) or (fading or sequence) and set(offsets)!=set(layers)
            or any(type(at) is not int or at%8 or not 0 <= at <= n-8 for at in offsets.values())):
        raise ValueError('Invalid complete native object/profile bounds')
    pointers = [0x06000000+offsets[k] if k in offsets else 0 for k in LAYERS]
    if rigged:
        from v3_room_rig_runtime import VTABLE
        if row.get('room_runtime')!={'vtable':VTABLE,'vrom':vrom} or len(offsets)!=row['profile']['skeleton']['shown_joints']:
            raise ValueError('Animated profile requires its complete installed room lifecycle')
        pointers=[0,0,0,0]
    if sequence:
        linked=row['draw_sequence'];at=linked['native_offset']
        if (linked['model_offsets']!=offsets or linked['arena']!='opaque' or
                at%8 or not 0<=at<=n-linked['bytes'] or linked['bytes']!=(len(offsets)+1)*8):
            raise ValueError('Invalid static model sequence bounds')
        pointers=[0x06000000+at,0,0,0]
    if sound:
        from v3_room_rig_runtime import SOUND_VTABLE
        if row.get('room_runtime')!={'vtable':SOUND_VTABLE,'vrom':vrom}:
            raise ValueError('Sound profile requires its complete installed room lifecycle')
    if material:
        from v3_room_rig_runtime import MATERIAL_VTABLE
        if (row.get('room_runtime')!={'vtable':MATERIAL_VTABLE,'vrom':vrom} or
                set(adapter['functions'])!={'move','draw'} or set(offsets)!=set(layers)):
            raise ValueError('Prepared resources have no implemented native material lifecycle')
        pointers=[0,0,0,0]
    return (struct.pack('>12I', vrom, vrom+n, 0x06000000, 0x06000000+n, *pointers, 0,0,0,0)+scalar+
            struct.pack('>I',VTABLE if rigged else SOUND_VTABLE if sound else MATERIAL_VTABLE if material else palette_fade.VTABLE if fading else 0))


def catalogue_record(row):
    return dict(item_id=row['item_id'], runtime_index=row['runtime_index'],
        **{k:row[k] for k in ('id','donor_item_id','donor_runtime_index') if k in row},
        catalogue_index=(int(row['item_id'],16)-0x1000)//4, mode=0,
        donor_position=row['donor_catalogue_position'], donor_acquisition_list=row['donor_list'],
        donor_preview_mode=row['preview_mode'],donor_preview_scalar_hex=row['donor_preview_scalar_hex'],
        preview_override=row['preview_mode']!=0,preview_define='AF_V3_CATALOGUE_PREVIEW_RECORDS',
        ordinary_shop_list=row['donor_list'] if row['ordinary_stock'] else None,
        shop_list_sha256=row['donor_list_sha256'], catalogue_orderable=row['catalogue_orderable'])


def order_mask(row):
    if not row.get('catalogue_orderable', True): return 0
    group = row.get('donor_acquisition_list') or row['ordinary_shop_list']
    masks = {'ftr_listA':7, 'ftr_listB':7, 'ftr_listC':7, 'ftr_listEvent':8, 'ftr_listTrain':16, 'ftr_listLottery':32}
    if group not in masks: raise ValueError('Unsupported orderable acquisition category')
    return masks[group]


def provenance_patch(rows):
    """Generate additions to the sole text catalogue, preserving human edits."""
    existing = {r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
    additions = []
    for row in rows:
        key = row['id']+'/name'
        if key in existing:
            locale = existing[key]['locales']['en']
            if locale['credit'] != 'official' or locale.get('encoded_sha256') != row['name_sha256']:
                raise ValueError('Existing text attribution differs; preserve it for review')
            continue
        entry = dict(id=key,native_sha256=None,locales={'en':dict(credit='official',
            locator=['tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py'],
            source=dict(source='user-supplied GAFE01 revision 0 disc',symbol=row.get('name_source_symbol','ftrName2_table'),
                index=row['name_source_index'],reference_sha256=row['name_sha256']),
            text=row['name'],evidence_id=key,human_review='not_recorded',encoded_sha256=row['name_sha256'])})
        additions.append('+'+'    '+json.dumps(entry,separators=(',',':'))+',')
    if not additions: return ''
    return ('*** Begin Patch\n*** Update File: '+str(ROOT/'translations/provenance.json')+
            '\n@@\n   "entries": [\n'+'\n'.join(additions)+'\n*** End Patch\n')


def scoring(base, prior, rows, source):
    changes, reports = {}, {}
    files = by_vrom(base)
    aliases=[]
    for row in rows:
        if row['donor_birth_category']!=row['birth_category']:
            from v3_camping_items import score_mapping
            mapping=score_mapping(source.rel,source.symbols.encode(),base,prior,source_sha256=sha256(base))
            points=source.raw('mMkRm_birth_point_table')
            donor=row['donor_birth_category'];native=row['birth_category']
            if (native!=mapping['native_scoring_category'] or
                    struct.unpack_from('>I',points,donor*4)[0]!=mapping['points']):
                raise ValueError('Changed source/native reward scoring equivalence')
            aliases.append(dict(**{**mapping,'donor_category':donor},item_id=row['item_id']))
    for key, tool, width in (('hra',hra,4), ('feng_shui',feng,2)):
        report = copy.deepcopy(prior[key]); data = bytearray(files[tool.NEW_VROM].extract(base))
        if (sha256(data) != report['output_sha256'] or
                sha256(files[tool.NEW_RELOC].extract(base)) != report['relocation_sha256']):
            raise ValueError('Changed scoring owner or relocation resource')
        table = report['metadata_address']-tool.RAM
        for row in rows:
            index = row['runtime_index']; at = table+index*width
            if not 1024 <= index < 2048 or data[at:at+width] != (bytes.fromhex('fc000000') if width==4 else bytes(2)):
                raise ValueError('Scoring record would replace an installed identity')
            if width == 4:
                series = report['series']; start = series['info_address']-hra.RAM+row['series']*3
                actual = data[start:start+3]; expected = bytes.fromhex(row['donor_series_hex'])
                # Existing theme adapters explicitly omit unavailable matching
                # surfaces. Do not invent a surface ID or another per-item rule.
                adapters = [r for r in series.values() if isinstance(r,dict) and r.get('series')==row['series']]
                if actual != expected and not (len(adapters)==1 and not adapters[0]['matching_surfaces_installed']
                        and actual == expected[:2]+b'\xff' and expected[2]==adapters[0]['donor_wall_floor_index']):
                    raise ValueError('Scoring series needs a shared category adapter')
                if row['birth_category'] >= report['birth_extension']['count']:
                    raise ValueError('Unimplemented scoring birth category')
            payload = bytes.fromhex(row['native_hra_hex'] if width==4 else row['feng_hex'])
            if len(payload) != width: raise ValueError('Incomplete scoring record')
            data[at:at+width] = payload
            report['imports'].append(dict(item_id=row['item_id'], runtime_index=index, metadata=payload.hex(),
                **({k:row[k] for k in ('series','birth_category','surface')} if width==4 else {})))
        report.update(output_sha256=sha256(data), metadata_sha256=sha256(data[table:table+report['metadata_rows']*width]))
        if width==4:report['automatic_scoring_aliases']=report.get('automatic_scoring_aliases',[])+aliases
        changes[tool.NEW_VROM], reports[key] = bytes(data), report
    return changes, reports


def checked_assets(art_path, source, worksheet):
    from v3_furniture_pipeline import PreparedAssets
    raw = (art_path/'art.json').read_bytes(); art = json.loads(raw)
    # Prior objects still undergo complete current metadata and model checks;
    # a display alias cannot pass as standalone furniture through an old report.
    if (art['format'] != 'AFV3-AUTO-FURNITURE-ASSETS-1' or art['version'] not in (7, 8, 9, 10, 11, 12, 13, 14, VERSION)
            or art['source_rel_sha256'] != sha256(source.rel)
            or art['source_symbols_sha256'] != sha256(source.symbols.encode())):
        raise ValueError('Unknown converter/source revision')
    identities = identity_rows(worksheet,include_unmapped_legacy=True); seen = set(); rows = []
    cache=PreparedAssets(source,[art_path])
    for row in art['objects']:
        item,_ = furniture_source(row)
        if item in seen: raise ValueError('Duplicate batch identity')
        seen.add(item)
        prepared=prepare(source,item);descriptor=prepared[0]
        meta = metadata(source,item,descriptor,identities[item])
        if any(row.get(k) != v for k,v in meta.items()) or row['profile'] != json.loads(json.dumps(descriptor)):
            raise ValueError('Import metadata differs from source discovery')
        if (row['native_profile_scalar_hex']!=descriptor['scalar_hex'] or
                cache.reuse(source,f'{item:04X}',prepared) is None):
            raise ValueError('Changed complete converted asset or native profile scalar')
        asset=(art_path/row['object_file']).read_bytes()
        rows.append((row,asset))
    if not rows: raise ValueError('Empty automatic import batch')
    return rows, sha256(raw)


def reuse_resource_tail(base, prior, old_blob):
    """Retire only the three terminal resources this builder regenerates.

    Input files remain untouched. Existing object VROMs never move. Receipts,
    DMA mappings, padding, and every resident profile must agree before reuse.
    """
    previous=prior.get('automatic_furniture')
    if not previous:
        return bytearray(old_blob),dict(reused_bytes=0)
    files=by_vrom(base);moves=previous['resource_moves']
    owners={catalogue.VROM,catalogue.RELOC,shops.VROM}
    if (len(moves)!=3 or {r['vrom'] for r in moves}!=owners
            or sha256(old_blob)!=prior['blob_sha256'] or files[BLOB].pend):
        raise ValueError('Changed regenerated resource tail inventory')
    first=min(r['blob_offset'] for r in moves);cursor=first
    if first%16 or not PACKAGE+PACKAGE_SIZE <= first < len(old_blob):
        raise ValueError('Regenerated resource tail overlaps resident data')
    for row in sorted(moves,key=lambda r:r['blob_offset']):
        at,n=row['blob_offset'],row['bytes'];entry=files[row['vrom']]
        if (at!=(cursor+15)&~15 or n<=0 or at+n>len(old_blob) or any(old_blob[cursor:at])
                or entry.pend or entry.size!=n or entry.pstart!=files[BLOB].pstart+at
                or row['physical']!=entry.pstart or sha256(old_blob[at:at+n])!=row['sha256']
                or entry.extract(base)!=old_blob[at:at+n]):
            raise ValueError('Changed regenerated resource extent, mapping, padding, or contents')
        cursor=at+n
    if cursor!=len(old_blob): raise ValueError('Regenerated resources are not the complete terminal tail')
    physical=files[BLOB].pstart+first;end=files[BLOB].pstart+len(old_blob)
    if any(e.pstart<end and physical<(e.pend or e.pstart+e.size)
           for v,e in files.items() if v not in owners|{BLOB} and e.pstart!=0xFFFFFFFF):
        raise ValueError('Regenerated resource tail overlaps another DMA resource')
    for at in range(ROWS,ITEMS,80):
        if any(old_blob[at:at+80]):
            lo,hi=struct.unpack_from('>II',old_blob,at+8)
            if lo<BLOB+len(old_blob) and BLOB+first<hi:
                raise ValueError('Regenerated resource tail overlaps retained furniture')
    return bytearray(old_blob[:first]),dict(reused_bytes=len(old_blob)-first,
        blob_offset=first,source_blob_sha256=sha256(old_blob),
        retained_prefix_sha256=sha256(old_blob[:first]),retired_resources=copy.deepcopy(moves))


def build(output, art_path, lock=LOCK):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'): raise ValueError('Use a fresh ignored build directory')
    base, prior = inputs(lock); files = by_vrom(base)
    limit=capacity.checked_limit(base,prior)
    base_pin=json.loads(lock.read_bytes())
    if base_pin['rom_sha256']!=sha256(base): raise ValueError('Base lock changed during the build')
    stable = STABLE.read_bytes()
    if sha256(stable) != STABLE_SHA: raise ValueError('Changed translation-only cartridge')
    original = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                    (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    from v3_room_rig_runtime import bind_profiles,reuse_profile
    bind_profiles(source,base,prior)
    prepared, art_sha = checked_assets(art_path.resolve(), source, ROOT/'build/item-identity-megasheet.xlsx')
    old_blob = files[BLOB].extract(base); blob = bytearray(old_blob)
    package = blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    profile_bits = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if (prior['runtime_abi'] < 84 or len(base) != 0x4000000 or PACKAGE_SIZE != 0x30000
            or sha256(blob) != prior['blob_sha256'] or blob[0x20:0xE0] != profile_bits
            or sha256(package) != prior['import_storage']['package_sha256']
            or sha256(blob[ROWS:ITEMS]) != prior['import_storage']['profile_rows_sha256']
            or sha256(blob[ITEMS:TABLE_END]) != prior['import_storage']['item_rows_sha256']
            or struct.unpack_from('>4I',blob,0xF0) != (BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)
            or package[-16:] != bytes.fromhex('AFACC0DE')*4
            or DMA_START+(len(files)+1)*16 != DMA_END or base[DMA_END-16:DMA_END] != bytes(16)):
        raise ValueError('Changed complete shared storage prerequisite')
    blob,reused=reuse_resource_tail(base,prior,old_blob)
    changes, score_reports = scoring(base,prior,[r for r,_ in prepared],source)
    installed = []
    for row,asset in prepared:
        item,index = int(row['item_id'],16),row['runtime_index']; i=slot(item)
        existing=reuse_profile(source,row,asset,blob,limit=limit)
        if (index != 1024+i or profile_bits[32+i//8]&(1<<(i&7)) or
                existing is None and (any(blob[ROWS+i*80:ROWS+(i+1)*80]) or any(blob[ITEMS+i*32:ITEMS+(i+1)*32]))):
            raise ValueError('Canonical identity is already installed')
        if existing is None:
            blob.extend(bytes(-len(blob)%16)); vrom = BLOB+len(blob)
            native = profile(row,vrom,limit=limit); blob.extend(asset)
        else:vrom,native=existing
        blob[ROWS+i*80:ROWS+(i+1)*80] = struct.pack('>HHI',index,item,1)+native+bytes(4)
        record = struct.pack('>HHHBB',index,item,row['price'],row['size_code'],1)+row['name'].encode().ljust(16,b' ')+bytes(8)
        blob[ITEMS+i*32:ITEMS+(i+1)*32] = record
        profile_bits[32+i//8] |= 1<<(i&7)
        installed.append({**row, 'registry_version':3 if row.get('donor_item_id') else 2, 'object_vrom':f'{vrom:08X}',
            'profile_ram':f'{ROWS_RAM+i*80+8:08X}', 'profile_sha256':sha256(native),
            'record_sha256':sha256(record), 'runtime_installed':True, 'enabled':True,
            'selectable':False, 'ordinary_gameplay_tested':False,
            'remaining':['representative native execution', 'ordinary gameplay and save/restart']})
    all_furniture = copy.deepcopy(prior['furniture']); all_furniture['imports'].extend(installed)
    imports = all_furniture['imports']+[prior['speed_bag']]
    cat_rows = prior['catalogue']['imports']+[catalogue_record(r) for r in installed]
    for row in cat_rows:
        at = ITEMS+slot(int(row['item_id'],16))*32
        old = blob[at+24]
        if old not in (0,order_mask(row)) or any(blob[at+28:at+32]):
            raise ValueError('Catalogue mask overwrites reserved metadata')
        blob[at+24] = order_mask(row)
    preview_report=catalogue.install_preview_records(blob,prior,source,cat_rows)
    output.mkdir(parents=True)
    palette_report, expanded = palette_fade.install(original,base,prior,blob,source,output,imports)
    all_furniture['expanded_tables'] = expanded
    text_patch=provenance_patch([r for r,_ in prepared])
    if text_patch: write_new(output/'provenance.patch',text_patch.encode())
    cat_changes, cat_report = install_catalogue(base,stable,prior,imports,output,source.rel,
        source.symbols.encode(),reviewed_rows=cat_rows)
    changes.update(cat_changes)
    stock_rows = prior['shops']['imports']+[dict(item_id=r['item_id'],group=r['stock_group'],
        **{k:r[k] for k in ('donor_item_id','donor_runtime_index') if k in r},
        donor_list=r['donor_list'],donor_list_sha256=r['donor_list_sha256']) for r in installed if not r['reward_route']]
    stock_ids = {r['item_id'] for r in stock_rows}
    goods,table_at,stock_rows = shops.goods(stable,source.rel,source.symbols.encode(),
        [r for r in imports if r['item_id'] in stock_ids],reviewed_rows=stock_rows)
    code = bytearray(files[CODE_VROM].extract(base)); stock = prior['shops']
    display_report,alias_report=display_aliases.install(prior,blob,code,output)
    if (sha256(files[shops.VROM].extract(base)) != stock['output_sha256']
            or struct.unpack_from('>3I',code,shops.DESCRIPTOR-CODE_RAM) !=
                (shops.VROM,shops.VROM+stock['bytes'],0x06000000|stock['table_offset'])):
        raise ValueError('Changed goods owner/descriptor')
    struct.pack_into('>3I',code,shops.DESCRIPTOR-CODE_RAM,shops.VROM,shops.VROM+len(goods),0x06000000|table_at)
    behaviour_report=behaviours.install(original,base,prior,blob,code,imports,source,output)
    placement_changes,placement_report=placement.install(original,base,prior,blob,imports,source)
    changes.update(placement_changes)
    reward_changes,reward_report=rewards.install(original,base,prior,blob,imports,source,output)
    changes.update(reward_changes)
    trade_changes,trade_report=camper_trade.install_shared(base,prior,reward_report,output)
    changes.update(trade_changes)
    changes[shops.VROM],changes[CODE_VROM] = goods,code
    stock_report = {**stock,'imports':stock_rows,'bytes':len(goods),'table_offset':table_at,'output_sha256':sha256(goods)}
    # Compressed NPC owners need one new uncompressed mapping, before the
    # three regenerable terminal resources. Future batches update that owner
    # in place. Its unchanged relocation resource remains at the original VROM.
    owner_moves=[]
    for vrom in sorted(reward_changes):
        entry=files[vrom];data=changes[vrom]
        if len(data)!=entry.size: raise ValueError('Reward owner allocation changes size')
        if entry.pend:
            blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(changes.pop(vrom))
            owner_moves.append(dict(vrom=vrom,blob_offset=at,bytes=len(data),
                physical=files[BLOB].pstart+at,sha256=sha256(data)))
    moves = []
    for vrom in (catalogue.VROM,catalogue.RELOC,shops.VROM):
        blob.extend(bytes(-len(blob)%16)); at=len(blob); data=changes.pop(vrom); blob.extend(data)
        moves.append(dict(vrom=vrom,blob_offset=at,bytes=len(data),physical=files[BLOB].pstart+at,sha256=sha256(data)))
    for vrom,data in list(changes.items()):
        entry=files[vrom]; at=entry.pstart-files[BLOB].pstart
        if entry.pend or len(data)!=entry.size: raise ValueError('Unexpected fixed-owner allocation change')
        if 0 <= at <= len(old_blob)-len(data):
            if at+len(data)>reused.get('blob_offset',len(old_blob)):
                raise ValueError('Fixed owner update overlaps reused resource tail')
            blob[at:at+len(data)]=data; changes.pop(vrom)
    abi=prior['runtime_abi']+1
    blob[0x20:0xE0]=profile_bits; package=blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    struct.pack_into('>I',blob,0xF8,zlib.crc32(package)); struct.pack_into('>I',blob,4,abi)
    module=bytearray(files[MODULE].extract(base))
    defines=tuple(f[2:] if not f.startswith('-DAF_V3_ABI=') else f'AF_V3_ABI={abi}'
                  for f in prior['startup']['flags'] if f.startswith('-D'))
    if reward_report and 'AF_V3_FURNITURE_REWARDS=1' not in defines:
        defines+=('AF_V3_FURNITURE_REWARDS=1',)
    startup,startup_report=compile_part('startup',output/'startup',defines=defines)
    old=prior['startup']
    if (sha256(module[STARTUP:STARTUP+old['bytes']]) != old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),abi)
    start,end=files[BLOB].pstart+len(old_blob),files[BLOB].pstart+len(blob)
    if (len(blob)<len(old_blob) or BLOB+len(blob)>limit or end>len(base) or any(base[start:end])
            or any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                   for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)
            or any(e.vstart<BLOB+len(blob) and BLOB+len(old_blob)<e.vend for v,e in files.items() if v!=BLOB)):
        raise ValueError('Batch overlaps a live physical or virtual resource')
    changes.update({BLOB:blob,MODULE:module}); result=bytearray(base)
    for vrom,data in changes.items(): result[files[vrom].pstart:files[vrom].pstart+len(data)]=data
    struct.pack_into('>I',result,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in owner_moves+moves:
        struct.pack_into('>4I',result,DMA_START+files[row['vrom']].index*16,
            row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    fix_checksum(result); result=bytes(result)
    if set(by_vrom(result))!=set(files) or result[DMA_END-16:DMA_END]!=bytes(16): raise ValueError('Directory changed')
    patch=make_ups(original,result)
    if apply_ups(original,patch)!=result: raise ValueError('Patch reconstruction failed')
    report=copy.deepcopy(prior)
    if report.get('staged_furniture'):
        promoted={r['item_id'] for r in installed}
        report['staged_furniture']['rows']=[r for r in report['staged_furniture']['rows'] if r['item_id'] not in promoted]
        for row in report['equipment_resources']['room_rigs']['rows']+report['equipment_resources']['room_rigs']['sound_rows']:
            if row['source_item_id'] in promoted:row['parent_selectable']=True
    report.update(build='v3-automatic-furniture',runtime_abi=abi,input_build_sha256=sha256(base),
        output_sha256=sha256(result),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        blob_bytes=len(blob),blob_file_bytes=len(blob),startup=startup_report,furniture=all_furniture,
        catalogue=cat_report,shops=stock_report,furniture_behaviours=behaviour_report,
        catalogue_preview_records=preview_report,
        furniture_placement=placement_report,camper_trade=trade_report,**score_reports,
        native_test='pending representative automatic-import execution')
    if reward_report: report['furniture_rewards']=reward_report
    report['clothing']['display']=display_report
    report['display_aliases']=alias_report
    if palette_report:
        report['furniture_palette_fade']=palette_report
        linked=palette_report['code'];at=PACKAGE+palette_report['ram']-PACKAGE_RAM
        report['tent_model'].update(shared_palette_runtime=True,
            runtime_code_receipt='furniture_palette_fade',legacy_asset_unchanged=True,
            code={**linked,'linked_sha256':linked['sha256'],
                  'sha256':sha256(blob[at:at+linked['bytes']])},
            vtable_hex=palette_report['vtables']['80483700'],native_contract=palette_report['native_contract'])
    report['save_runtime'].update(profile_hex=profile_bits.hex(),profile_sha256=sha256(profile_bits))
    report['furniture_items']['imports'].extend(installed)
    report['furniture_items']['active_metadata_rows']=len(imports)
    for section in report.values():
        if isinstance(section,dict) and 'package_sha256' in section: section['package_sha256']=sha256(package)
    report['import_storage'].update(remaining_bytes=limit-BLOB-len(blob),static_installed=len(imports)-1,
        items_installed=len(imports),profile_rows_sha256=sha256(blob[ROWS:ITEMS]),
        item_rows_sha256=sha256(blob[ITEMS:TABLE_END]),saved_profile_changed=True)
    for section in (report['furniture']['imports'],report['furniture_items']['imports']):
        for row in section:
            at=ITEMS+slot(int(row['item_id'],16))*32; row['record_sha256']=sha256(blob[at:at+32])
            row['action_sound']=blob[at+25]
            row['reward_route']=blob[at+27]
            row['layer_type']=source.raw('aMR_layer_set_info')[furniture_source(row)[1]]
    report['automatic_furniture']=dict(version=VERSION,imports=installed,art_report_sha256=art_sha,
        base=base_pin,art_directory=str(art_path.resolve().relative_to(ROOT)),
        resource_moves=moves,owner_moves=owner_moves,resource_tail_reuse=reused,additional_resident_bytes=0,saved_format_changed=False,
        saved_profile_changed=True,older_builds_accept_new_saves=False,web_patcher_enabled=False,
        catalogue_masks_sha256=sha256(bytes(blob[ITEMS+i*32+24] for i in range(1024))),
        provenance_catalogue_complete=not bool(text_patch))
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'animal-forest-v3-asset-loader.z64',result); write_new(output/'asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    pin=dict(directory=str(output.relative_to(ROOT)),runtime_abi=abi,rom_sha256=sha256(result),
        report_sha256=sha256((output/'build.json').read_bytes()))
    write_new(output/'build-lock.json',(json.dumps(pin,indent=2)+'\n').encode())
    write_new(output/'base-lock.json',(json.dumps(base_pin,indent=2)+'\n').encode())
    return report


def owner_tail_storage(base,files,changes,*,minimum_end=0):
    """Allocate complete changed overlays after live physical cartridge data.

    Overlay VROM identities already exist; consuming import-object VROM space
    for their uncompressed copies needlessly constrains later shared adapters.
    Keep the 64-MiB image, require zero padding, and retain every old resource.
    """
    cursor=max(minimum_end,max(e.pend or e.pstart+e.size for e in files.values() if e.pstart!=0xFFFFFFFF))
    rows=[]
    for vrom,data in changes:
        first=(cursor+15)&~15;end=first+len(data);entry=files[vrom]
        if (not data or len(base)!=0x4000000 or end>len(base) or any(base[cursor:end])
                or any(e.pstart<end and first<(e.pend or e.pstart+e.size)
                       for e in files.values() if e.pstart!=0xFFFFFFFF)):
            raise ValueError('Changed owner requires verified unused cartridge-tail storage')
        rows.append(dict(vrom=vrom,bytes=len(data),physical=first,storage='cartridge-tail',
                         sha256=sha256(data),original_sha256=sha256(entry.extract(base))))
        cursor=end
    return rows


def append_resource_plan(base,files,vrom,data,relocatable):
    """Append a complete resource in place; move only checked DMA-owned blockers."""
    entry=files[vrom];before=entry.extract(base)
    if entry.pend or len(data)<=len(before) or data[:len(before)]!=before:
        raise ValueError('In-place growth must retain the complete uncompressed resource')
    first=entry.pstart+entry.size;end=entry.pstart+len(data)
    if (end>len(base) or any(e.vstart<vrom+len(data) and vrom<e.vend
            for v,e in files.items() if v!=vrom)):
        raise ValueError('In-place resource growth exceeds cartridge or virtual bounds')
    occupied=sorted((e.pstart,e.pend or e.pstart+e.size,v,e) for v,e in files.items()
                    if v!=vrom and e.pstart!=0xFFFFFFFF and e.pstart<end and first<(e.pend or e.pstart+e.size))
    changes={vrom:data};cursor=first;blockers=[]
    for a,b,v,e in occupied:
        old=e.extract(base)
        if (v not in relocatable or sha256(old)!=relocatable[v] or a<first
                or a<cursor or any(base[cursor:a])):
            raise ValueError('Resource append overlaps undeclared or changed live data')
        blockers.append(v);changes[v]=old;cursor=min(end,b)
    if any(base[cursor:end]):raise ValueError('Resource append crosses unowned nonzero data')
    return changes,dict(vrom=vrom,physical=entry.pstart,previous_bytes=entry.size,
        bytes=len(data),previous_sha256=sha256(before),sha256=sha256(data),relocated_blockers=blockers)


def relocate_resource_plan(base,files,vrom,data,*,minimum_physical):
    """Keep a whole growing resource in verified zero, unmapped cartridge space.

    Logical identity is retained. Callers must update any physical readers;
    old copies are left untouched, never treated as free data merely because
    they are absent from the current DMA directory.
    """
    entry=files[vrom];before=entry.extract(base)
    if (entry.pend or len(data)<=len(before) or data[:len(before)]!=before or
            any(e.vstart<vrom+len(data) and vrom<e.vend for v,e in files.items() if v!=vrom)):
        raise ValueError('Relocation needs a complete non-overlapping append')
    occupied=sorted((e.pstart,e.pend or e.pstart+e.size) for e in files.values() if e.pstart!=0xFFFFFFFF)
    cursor=minimum_physical
    for first,last in occupied+[(len(base),len(base))]:
        start=(cursor+15)&~15
        if start+len(data)<=first and not any(base[start:start+len(data)]):
            return {vrom:data},dict(vrom=vrom,physical=start,previous_physical=entry.pstart,
                previous_bytes=entry.size,bytes=len(data),previous_sha256=sha256(before),sha256=sha256(data),
                relocated_blockers=[],relocated=True,retains_old_allocation=True)
        cursor=max(cursor,last)
    raise ValueError('No verified zero cartridge gap for complete resource growth')


def refresh_runtime(output, lock=LOCK, *, equipment_art=None, player_motion=False, equipment_kinds=False,
                    player_actions=False, item_category_art=None, ground_categories=False, event_acquisition=False,
                    held_collection=False, held_catalogue_art=None, held_selection=False, translation_updates=False,
                    room_rigs_art=None, scenery_art=None, scenery_gameplay=False,
                    equipment_rigs=None, expand_storage=False, furniture_audio_art=None, furniture_profiles=None,
                    material_frames_art=None):
    """Update shared readers; optionally install the shared held-resource adapter."""
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):
        raise ValueError('Use a fresh ignored build directory')
    base,prior=inputs(lock); files=by_vrom(base)
    limit=capacity.checked_limit(base,prior)
    base_pin=json.loads(lock.read_bytes())
    if base_pin['rom_sha256']!=sha256(base): raise ValueError('Base lock changed during the build')
    original=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    old_blob=files[BLOB].extract(base);blob=bytearray(old_blob)
    core=bytearray(files[CODE_VROM].extract(base))
    module=bytearray(files[MODULE].extract(base))
    package=blob[PACKAGE:PACKAGE+PACKAGE_SIZE]
    if (sha256(blob)!=prior['blob_sha256'] or sha256(package)!=prior['import_storage']['package_sha256']
            or struct.unpack_from('>4I',blob,0xF0)!=(BLOB+PACKAGE,PACKAGE_SIZE,zlib.crc32(package),PACKAGE_RAM)):
        raise ValueError('Changed shared runtime package')
    output.mkdir(parents=True)
    moved=[];equipment_report=None;reused=None;owner_changes={};owner_moves=[];owner_updates=[];report_updates={};text_moves=[]
    equipment_mode=any((equipment_art is not None,equipment_rigs is not None,player_motion,equipment_kinds,player_actions,
                        item_category_art is not None,ground_categories,event_acquisition,held_collection,held_catalogue_art is not None,held_selection,room_rigs_art is not None,scenery_art is not None,scenery_gameplay))
    resource_mode=equipment_mode or translation_updates or expand_storage or furniture_audio_art is not None or furniture_profiles is not None or material_frames_art is not None
    if sum((equipment_art is not None,equipment_rigs is not None,player_motion,equipment_kinds,player_actions,
            item_category_art is not None,ground_categories,event_acquisition,held_collection,held_catalogue_art is not None,held_selection,translation_updates,room_rigs_art is not None,scenery_art is not None,scenery_gameplay,expand_storage,furniture_audio_art is not None,furniture_profiles is not None,material_frames_art is not None))>1:
        raise ValueError('Install shared runtime updates in dependency order')
    if resource_mode:
        blob,reused=reuse_resource_tail(base,prior,old_blob)
        if not reused['reused_bytes']:
            raise ValueError('Equipment integration requires the checked shared resource tail')
    parent_readers=bool(player_actions and prior.get('equipment_resources',{}).get('player_actions',{}).get('equipment_selection'))
    wrapped_names=bool(player_actions and prior.get('equipment_resources',{}).get('wrapped_presents'))
    if expand_storage:
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        report_updates,text_moves=capacity.expand(base,prior,core)
        limit=report_updates['import_storage']['virtual_limit']
    elif translation_updates:
        import v3_translation_updates as translation
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        owner_changes,report_updates=translation.install(base,prior,module,output)
    elif held_catalogue_art is not None or wrapped_names or furniture_audio_art is not None or furniture_profiles is not None or material_frames_art is not None:
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
    else:
        display_report,alias_report=display_aliases.install(prior,blob,core,output,held_items=parent_readers,
            held_collection=held_collection)
    if equipment_art is not None:
        import v3_equipment_runtime as equipment
        equipment_report=equipment.install(prior,blob,core,original,output,equipment_art)
    elif equipment_rigs is not None:
        import v3_equipment_runtime as equipment
        equipment_report,owner_changes=equipment.install_rigs(base,prior,blob,core,original,output,equipment_rigs)
    elif player_motion:
        import v3_equipment_runtime as equipment
        equipment_report,owner_changes=equipment.install_player_motion(base,prior,blob,core,original,output)
    elif equipment_kinds:
        import v3_equipment_runtime as equipment
        equipment_report,owner_changes=equipment.install_kind_readers(base,prior,blob,core,original,output)
    elif player_actions:
        import v3_player_actions as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output)
        reward_state=equipment_report['player_actions'].get('reward_state')
        if reward_state and not prior['equipment_resources']['player_actions'].get('reward_state'):
            report_updates.update(equipment.v3_save_rewards.report_updates(prior,reward_state))
    elif item_category_art is not None:
        import v3_category_runtime as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output,item_category_art)
    elif ground_categories:
        import v3_ground_categories as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output)
    elif scenery_art is not None:
        import v3_scenery_runtime as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output,scenery_art)
    elif scenery_gameplay:
        import v3_scenery_runtime as equipment
        equipment_report,owner_changes=equipment.install_gameplay(base,prior,blob,core,original,output)
    elif event_acquisition:
        import v3_event_acquisition as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output)
    elif held_collection:
        import v3_held_collection as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output)
    elif held_catalogue_art is not None:
        import v3_held_catalogue as equipment
        equipment_report,owner_changes,report_updates=equipment.install(base,prior,blob,core,original,output,held_catalogue_art)
    elif room_rigs_art is not None:
        import v3_room_rig_runtime as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output,room_rigs_art)
    elif furniture_audio_art is not None:
        import v3_sound_programs as equipment
        equipment_report,owner_changes,report_updates=equipment.install_furniture(
            base,prior,blob,core,original,output,furniture_audio_art)
    elif furniture_profiles is not None:
        import v3_room_rig_runtime as equipment
        equipment_report,owner_changes,report_updates=equipment.install_profiles(
            base,prior,blob,core,original,output,furniture_profiles)
    elif material_frames_art is not None:
        import v3_furniture_materials as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output,material_frames_art)
    elif held_selection:
        import v3_held_catalogue as equipment
        equipment_report,owner_changes,report_updates=equipment.select_installed(prior,blob)
    if equipment_report:
        if held_catalogue_art is not None or wrapped_names:
            display_report,alias_report=display_aliases.install(
                {**prior,**report_updates,'equipment_resources':equipment_report},blob,core,output)
        if equipment_report.get('parent_readers'):
            present_names=equipment_report.get('wrapped_presents',{}).get('name_readers',{})
            name_rows=[dict(id=r['id'].removesuffix('/name'),name=r['text'],
                name_sha256=r['encoded_sha256'],name_source_symbol=r['source_symbol'],
                name_source_index=r['source_index']) for r in present_names.get('rows',[])]
            attribution=provenance_patch(equipment_report['parent_readers']['rows']+name_rows)
            if attribution:write_new(output/'provenance.patch',attribution.encode())
            equipment_report['parent_readers']['provenance_complete']=not bool(attribution)
            if present_names:present_names['provenance_complete']=not bool(attribution)
    if resource_mode:
        # Changed compressed owners retain their logical DMA identities. Store
        # their complete images outside the bounded import-object VROM region.
        external=[]
        growth=report_updates.get('resource_growth',[])
        growth_vroms={r['vrom'] for r in growth}
        forced_moves={v for r in growth for v in r['relocated_blockers']}
        if len(growth_vroms)!=len(growth) or growth_vroms&forced_moves:
            raise ValueError('Conflicting in-place resource growth plans')
        menu_resizes={}
        if (player_actions and equipment_report['player_actions'].get('balloon_menu') and
                not prior['equipment_resources']['player_actions'].get('balloon_menu')):
            menu_resizes={r['vrom']:r for r in equipment_report['player_actions']['balloon_menu']['owner_resizes']}
            if set(menu_resizes)!={0x3950000,0x3960000} or not set(menu_resizes)<=set(owner_changes):
                raise ValueError('Incomplete declared balloon-menu owner resize')
        for vrom,data in owner_changes.items():
            entry=files[vrom]
            if vrom in growth_vroms:
                row=next(r for r in growth if r['vrom']==vrom)
                if (entry.pend or entry.size!=row['previous_bytes'] or entry.pstart!=row.get('previous_physical',row['physical'])
                        or len(data)!=row['bytes'] or sha256(data)!=row['sha256']
                        or sha256(entry.extract(base))!=row['previous_sha256']):
                    raise ValueError('Changed complete resource growth plan')
                if row.get('relocated'):
                    start,end=row['physical'],row['physical']+row['bytes']
                    if (start&15 or not 0<=start<end<=len(base) or any(base[start:end]) or
                            any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                                for e in files.values() if e.pstart!=0xFFFFFFFF) or
                            any(r is not row and r['physical']<end and start<r['physical']+r['bytes'] for r in growth)):
                        raise ValueError('Relocated resource overlaps occupied or nonzero cartridge data')
                continue
            if vrom in forced_moves:
                if data!=entry.extract(base):raise ValueError('Relocated blocker changes its complete contents')
                external.append((vrom,data));continue
            if held_catalogue_art is not None and vrom in (catalogue.VROM,catalogue.RELOC):
                if vrom not in {r['vrom'] for r in reused['retired_resources']}:
                    raise ValueError('Resized catalogue is not owned by the reusable tail')
                continue
            resized=translation_updates and vrom in (0x3B60000,0x3B70000)
            if vrom in menu_resizes:
                row=menu_resizes[vrom]
                if (row['previous_bytes']!=entry.size or row['previous_sha256']!=sha256(entry.extract(base))
                        or row['bytes']!=len(data) or row['sha256']!=sha256(data)):
                    raise ValueError('Changed declared menu owner dimensions or complete data')
                resized=True
            if len(data)!=entry.size and not resized:raise ValueError('Runtime update changes owner dimensions')
            if entry.pend or resized:
                external.append((vrom,data))
            elif files[BLOB].pstart<=entry.pstart<files[BLOB].pstart+len(blob):
                # An earlier refresh can already own uncompressed overlay
                # relocations inside the import blob. Update that same copy so
                # startup/report checksums describe the actual emitted bytes.
                at=entry.pstart-files[BLOB].pstart
                if blob[at:at+len(data)]!=entry.extract(base):
                    raise ValueError('In-place owner update overlaps another changed resource')
                blob[at:at+len(data)]=data
                owner_updates.append(dict(vrom=vrom,blob_offset=at,bytes=len(data),
                    sha256=sha256(data),original_sha256=sha256(entry.extract(base))))
        for row in sorted(reused['retired_resources'],key=lambda r:r['blob_offset']):
            data=owner_changes.get(row['vrom'],files[row['vrom']].extract(base))
            blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(data)
            moved.append(dict(vrom=row['vrom'],blob_offset=at,bytes=len(data),
                              physical=files[BLOB].pstart+at,sha256=sha256(data)))
        owner_moves=owner_tail_storage(base,files,external,
            minimum_end=max([files[BLOB].pstart+len(blob)]+[r['physical']+r['bytes'] for r in growth]))
        owner_moves.extend(dict(vrom=r['vrom'],bytes=r['bytes'],physical=r['physical'],
            storage='checked-zero-gap' if r.get('relocated') else 'checked-in-place-append',
            sha256=r['sha256'],original_sha256=r['previous_sha256']) for r in growth)
    abi=prior['runtime_abi']+1; struct.pack_into('>I',blob,4,abi)
    package=blob[PACKAGE:PACKAGE+PACKAGE_SIZE]; struct.pack_into('>I',blob,0xF8,zlib.crc32(package))
    old=prior['startup']
    defines=tuple(f[2:] if not f.startswith('-DAF_V3_ABI=') else f'AF_V3_ABI={abi}'
        for f in old['flags'] if f.startswith('-D'))
    if equipment_report:
        defines=tuple(f for f in defines if not f.startswith(('AF_V3_EQUIPMENT_VROM=','AF_V3_EQUIPMENT_CRC=',
                                                            'AF_V3_EQUIPMENT_BYTES=')))
        defines+=(f'AF_V3_EQUIPMENT_VROM=0x{equipment_report["vrom"]:08X}u',
                  f'AF_V3_EQUIPMENT_CRC=0x{equipment_report["crc32"]:08X}u',
                  f'AF_V3_EQUIPMENT_BYTES=0x{equipment_report["bytes"]:X}u')
    startup,startup_report=compile_part('startup',output/'startup',defines=defines)
    if (sha256(module[STARTUP:STARTUP+old['bytes']])!=old['sha256']
            or any(module[STARTUP+old['bytes']:CONFIG]) or len(startup)>CONFIG-STARTUP):
        raise ValueError('Changed runtime startup reservation')
    module[STARTUP:CONFIG]=startup+bytes(CONFIG-STARTUP-len(startup))
    struct.pack_into('>4I',module,CONFIG,BLOB,0xC000,zlib.crc32(blob[:0xC000]),abi)
    result=bytearray(base)
    if resource_mode:
        start=files[BLOB].pstart+len(old_blob);end=files[BLOB].pstart+len(blob)
        if (len(blob)<len(old_blob) or BLOB+len(blob)>limit or end>len(base) or any(base[start:end])
                or any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                       for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)
                or any(e.vstart<BLOB+len(blob) and BLOB+len(old_blob)<e.vend
                       for v,e in files.items() if v!=BLOB)):
            raise ValueError('Equipment resource growth overlaps live cartridge data')
    for vrom,data in ((BLOB,blob),(CODE_VROM,core),(MODULE,module),*owner_changes.items()):
        entry=files[vrom]
        if any(row['vrom']==vrom for row in owner_moves+moved):continue
        if entry.pend or entry.size!=len(data) and not (resource_mode and vrom==BLOB):
            raise ValueError('Runtime update changes an undeclared resource allocation')
        result[entry.pstart:entry.pstart+len(data)]=data
    if resource_mode:
        for row in owner_moves:
            result[row['physical']:row['physical']+row['bytes']]=owner_changes[row['vrom']]
        struct.pack_into('>I',result,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
        for row in moved+owner_moves:
            struct.pack_into('>4I',result,DMA_START+files[row['vrom']].index*16,
                             row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    if text_moves:capacity.relocate_directory(result,files,text_moves)
    expected=bytearray(base[DMA_START:DMA_END])
    if resource_mode:
        struct.pack_into('>I',expected,files[BLOB].index*16+4,BLOB+len(blob))
        for row in moved+owner_moves:
            struct.pack_into('>4I',expected,files[row['vrom']].index*16,
                             row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    for row in text_moves:
        struct.pack_into('>2I',expected,row['directory_index']*16,row['vrom'],row['vrom']+row['bytes'])
    if result[DMA_START:DMA_END]!=expected:raise ValueError('Undeclared DMA-directory change')
    if event_acquisition and equipment_report:
        result=equipment.finish(result,base,output,equipment_report)
    if player_actions and equipment_report:
        result=equipment.finish(result,base,prior,output,equipment_report)
    installed=by_vrom(result)
    for vrom,data in owner_changes.items():
        if installed[vrom].extract(result)!=data:
            raise ValueError('Shared runtime loses a complete changed owner')
    fix_checksum(result);result=bytes(result)
    patch=make_ups(original,result)
    if apply_ups(original,patch)!=result: raise ValueError('Runtime patch reconstruction failed')
    report=copy.deepcopy(prior)
    report.update(report_updates)
    report.update(build='v3-shared-item-runtime',runtime_abi=abi,input_build_sha256=sha256(base),
        output_sha256=sha256(result),patch_sha256=sha256(patch),blob_sha256=sha256(blob),
        blob_bytes=len(blob),blob_file_bytes=len(blob),
        startup=startup_report,display_aliases=alias_report,
        native_test='pending changed shared item readers')
    report['clothing']['display']=display_report
    for section in report.values():
        if isinstance(section,dict) and 'package_sha256' in section: section['package_sha256']=sha256(package)
    report['import_storage']['item_rows_sha256']=sha256(blob[ITEMS:TABLE_END])
    report['import_storage']['profile_rows_sha256']=sha256(blob[ROWS:ITEMS])
    report['shared_runtime_refresh']=dict(base=base_pin,adapters=['display_aliases'],
        artwork_changed=False,resource_allocations_changed=False,saved_format_changed=False,
        saved_profile_changed=False,web_patcher_enabled=False)
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in capacity.SOURCES+display_aliases.SOURCES})
    if expand_storage:
        report['import_storage']['remaining_bytes']=limit-BLOB-len(blob)
        report['shared_runtime_refresh'].update(adapters=['resource_capacity'],
            resource_allocations_changed=True,resource_tail_reuse=reused,
            unchanged_owner_moves=moved,changed_owner_moves=owner_moves,
            in_place_owner_updates=owner_updates,additional_resident_bytes=0,
            text_resource_relocations=text_moves)
        capacity.checked_limit(result,report)
        report['native_test']='pending shared text address/DMA and expanded-resource verification'
    if translation_updates:
        report['automatic_furniture']['resource_moves']=moved
        report['import_storage']['remaining_bytes']=limit-BLOB-len(blob)
        report['shared_runtime_refresh'].update(adapters=['translation_headers'],
            resource_allocations_changed=True,resource_tail_reuse=reused,
            unchanged_owner_moves=moved,changed_owner_moves=owner_moves,
            in_place_owner_updates=owner_updates,additional_resident_bytes=0)
        report['sources'].update(report['translation_updates']['sources'])
        report['native_test']='pending changed translation headers; inherited gameplay limits retained'
    if equipment_report:
        report['equipment_resources']=equipment_report
        report['automatic_furniture']['resource_moves']=moved
        report['import_storage']['remaining_bytes']=limit-BLOB-len(blob)
        report['shared_runtime_refresh'].update(adapters=['display_aliases','equipment_resources'],
            resource_allocations_changed=bool(owner_moves or len(blob)!=len(old_blob)
                or any(row['physical']!=files[row['vrom']].pstart for row in moved)),resource_tail_reuse=reused,
            unchanged_owner_moves=moved,changed_owner_moves=owner_moves,
            in_place_owner_updates=owner_updates,
            additional_resident_bytes=equipment_report['bytes']-prior.get('equipment_resources',{}).get('bytes',0))
        if player_motion:
            report['shared_runtime_refresh']['adapters'].append('player_motion')
        if equipment_kinds:
            report['shared_runtime_refresh']['adapters'].append('equipment_kinds')
        if equipment_rigs is not None:
            report['shared_runtime_refresh']['adapters'].append('equipment_rigs')
            report['shared_runtime_refresh']['artwork_changed']=True
        if player_actions:
            report['shared_runtime_refresh']['adapters'].append('player_actions')
            if 'save_codec' in report_updates:
                report['shared_runtime_refresh'].update(saved_format_changed=True,
                    additional_save_state_bytes=report['save_runtime']['state_bytes']-prior['save_runtime']['state_bytes'])
        if item_category_art is not None:
            report['shared_runtime_refresh']['adapters'].append('item_categories')
            report['shared_runtime_refresh']['artwork_changed']=True
        if ground_categories:
            report['shared_runtime_refresh']['adapters'].append('ground_categories')
        if scenery_art is not None:
            report['shared_runtime_refresh']['adapters'].append('seasonal_scenery')
            report['shared_runtime_refresh'].update(artwork_changed=True,resource_allocations_changed=True,
                additional_resident_bytes=equipment_report['scenery']['additional_fixed_resident_bytes'],
                additional_scene_resident_bytes=equipment_report['scenery']['additional_scene_resident_bytes'])
        if scenery_gameplay:
            daily=equipment_report['scenery'].get('daily_growth')
            contents=equipment_report['scenery'].get('hidden_contents')
            world=equipment_report['scenery'].get('world_queries')
            interaction=equipment_report['scenery'].get('interactions')
            player_tree=equipment_report['scenery'].get('player_queries')
            added=(player_tree or interaction or world or contents or daily or equipment_report['scenery']['tree_states'])['additional_resident_bytes']
            adapter='scenery_planting_sparkle' if equipment_report['scenery'].get('planting_sparkle') else 'scenery_field_insects' if equipment_report['scenery'].get('field_insects') else 'scenery_felling_camera' if equipment_report['scenery'].get('felling_camera') else 'scenery_player_queries' if player_tree else 'scenery_interactions' if interaction else 'scenery_world_queries' if world else 'scenery_hidden_contents' if contents else 'scenery_daily_growth' if daily else 'scenery_tree_states'
            report['shared_runtime_refresh']['adapters'].append(adapter)
            report['shared_runtime_refresh'].update(resource_allocations_changed=bool(added),
                additional_resident_bytes=added,
                additional_scene_resident_bytes=0)
        if event_acquisition:
            report['shared_runtime_refresh']['adapters'].append('event_acquisition')
        if held_collection:
            report['shared_runtime_refresh']['adapters'].append('held_collection')
        if held_catalogue_art is not None:
            report['shared_runtime_refresh']['adapters'].append('held_catalogue')
            report['shared_runtime_refresh']['artwork_changed']=True
        if room_rigs_art is not None:
            report['shared_runtime_refresh']['adapters'].append('room_rigs')
            report['shared_runtime_refresh']['artwork_changed']=True
            report['shared_runtime_refresh']['additional_resident_bytes']=equipment_report['room_rigs']['additional_resident_bytes']
        if furniture_audio_art is not None:
            report['shared_runtime_refresh']['adapters'].append('furniture_trigger_audio')
            report['shared_runtime_refresh']['additional_resident_bytes']=equipment_report['furniture_audio']['audio_heap_growth']
        if furniture_profiles is not None:
            report['shared_runtime_refresh']['adapters'].append('inactive_furniture_profiles')
            report['shared_runtime_refresh']['artwork_changed']=True
        if material_frames_art is not None:
            report['shared_runtime_refresh']['adapters'].append('material_frames')
            report['shared_runtime_refresh']['artwork_changed']=True
        if held_selection:
            report['shared_runtime_refresh']['adapters'].append('held_selection')
        if report['save_runtime']['profile_hex']!=prior['save_runtime']['profile_hex']:
            report['shared_runtime_refresh']['saved_profile_changed']=True
        report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in equipment.SOURCES})
        if equipment_report.get('parent_readers'):
            report['sources']['translations/provenance.json']=sha256((ROOT/'translations/provenance.json').read_bytes())
        report['native_test']='pending shared equipment resource DMA/readers'
        if material_frames_art is not None:
            report['native_test']='pending material-frame renderer native execution and GPU appearance; lifecycle/acquisition remain incomplete'
    write_new(output/'animal-forest-v3-asset-loader.z64',result)
    write_new(output/'asset-loader.ups',patch)
    write_new(output/'build.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    pin=dict(directory=str(output.relative_to(ROOT)),runtime_abi=abi,rom_sha256=sha256(result),
        report_sha256=sha256((output/'build.json').read_bytes()))
    write_new(output/'build-lock.json',(json.dumps(pin,indent=2)+'\n').encode())
    write_new(output/'base-lock.json',(json.dumps(base_pin,indent=2)+'\n').encode())
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--art',type=Path)
    mode.add_argument('--refresh-runtime',action='store_true')
    parser.add_argument('--base-lock',type=Path,default=LOCK)
    parser.add_argument('--equipment-art',type=Path,
        help='With --refresh-runtime, install prepared shared held models and source-derived motion resources')
    parser.add_argument('--equipment-rigs',type=Path,
        help='With --refresh-runtime, install complete prepared rigs and grow their native equipment banks')
    parser.add_argument('--player-motion',action='store_true',
        help='With --refresh-runtime, extend the installed held module with complete player motions and split-body masks')
    parser.add_argument('--equipment-kinds',action='store_true',
        help='With --refresh-runtime, connect shared kind-indexed readers and complete tumble/get-up motions')
    parser.add_argument('--player-actions',action='store_true',
        help='With --refresh-runtime, extend shared player action tables and native dispatch')
    parser.add_argument('--item-category-art',type=Path,
        help='With --refresh-runtime, install prepared shared category artwork and police/handover consumers')
    parser.add_argument('--ground-categories',action='store_true',
        help='With --refresh-runtime, integrate installed categories in all four seasonal ground owners')
    parser.add_argument('--scenery-art',type=Path,
        help='With --refresh-runtime, install prepared seasonal scenery with owner-local resource banks')
    parser.add_argument('--scenery-gameplay',action='store_true',
        help='With --refresh-runtime, connect shared planting and tree-state rules to installed scenery')
    parser.add_argument('--event-acquisition',action='store_true',
        help='With --refresh-runtime, install separate source-derived event stock for selected handhelds')
    parser.add_argument('--held-collection',action='store_true',
        help='With --refresh-runtime, connect selected handheld ownership using source collection identities')
    parser.add_argument('--held-catalogue-art',type=Path,
        help='With --refresh-runtime, connect prepared parent display models to their actual catalogue category')
    parser.add_argument('--held-selection',action='store_true',
        help='With --refresh-runtime, enable installed parents in the full experimental composition reference')
    parser.add_argument('--room-rigs-art',type=Path,action='append',
        help='With --refresh-runtime, install a complete prepared animated room category without enabling parents')
    parser.add_argument('--translation-updates',action='store_true',
        help='With --refresh-runtime, carry corrected translation headers and the pinned import-free baseline')
    parser.add_argument('--expand-storage',action='store_true',
        help='With --refresh-runtime, relocate complete English resources and expand the checked import reservation')
    parser.add_argument('--furniture-audio-art',type=Path,
        help='With --refresh-runtime, install prepared shared furniture audio and its callback')
    parser.add_argument('--furniture-profiles',type=Path,action='append',
        help='With --refresh-runtime, bind complete room categories to inactive ordinary profiles and names')
    parser.add_argument('--material-frames-art',type=Path,action='append',
        help='With --refresh-runtime, install shared complete material-frame rendering without enabling unfinished items')
    args=parser.parse_args()
    if args.equipment_art and not args.refresh_runtime:parser.error('--equipment-art requires --refresh-runtime')
    if args.equipment_rigs and not args.refresh_runtime:parser.error('--equipment-rigs requires --refresh-runtime')
    if args.player_motion and not args.refresh_runtime:parser.error('--player-motion requires --refresh-runtime')
    if args.equipment_kinds and not args.refresh_runtime:parser.error('--equipment-kinds requires --refresh-runtime')
    if args.player_actions and not args.refresh_runtime:parser.error('--player-actions requires --refresh-runtime')
    if args.item_category_art and not args.refresh_runtime:parser.error('--item-category-art requires --refresh-runtime')
    if args.ground_categories and not args.refresh_runtime:parser.error('--ground-categories requires --refresh-runtime')
    if args.scenery_art and not args.refresh_runtime:parser.error('--scenery-art requires --refresh-runtime')
    if args.scenery_gameplay and not args.refresh_runtime:parser.error('--scenery-gameplay requires --refresh-runtime')
    if args.event_acquisition and not args.refresh_runtime:parser.error('--event-acquisition requires --refresh-runtime')
    if args.held_collection and not args.refresh_runtime:parser.error('--held-collection requires --refresh-runtime')
    if args.held_catalogue_art and not args.refresh_runtime:parser.error('--held-catalogue-art requires --refresh-runtime')
    if args.held_selection and not args.refresh_runtime:parser.error('--held-selection requires --refresh-runtime')
    if args.room_rigs_art and not args.refresh_runtime:parser.error('--room-rigs-art requires --refresh-runtime')
    if args.translation_updates and not args.refresh_runtime:parser.error('--translation-updates requires --refresh-runtime')
    if args.expand_storage and not args.refresh_runtime:parser.error('--expand-storage requires --refresh-runtime')
    if args.furniture_audio_art and not args.refresh_runtime:parser.error('--furniture-audio-art requires --refresh-runtime')
    if args.furniture_profiles and not args.refresh_runtime:parser.error('--furniture-profiles requires --refresh-runtime')
    if args.material_frames_art and not args.refresh_runtime:parser.error('--material-frames-art requires --refresh-runtime')
    result=(refresh_runtime(args.output,args.base_lock,equipment_art=args.equipment_art,player_motion=args.player_motion,
                            equipment_kinds=args.equipment_kinds,player_actions=args.player_actions,
                            item_category_art=args.item_category_art,ground_categories=args.ground_categories,
                            event_acquisition=args.event_acquisition,held_collection=args.held_collection,
                            held_catalogue_art=args.held_catalogue_art,held_selection=args.held_selection,
                            translation_updates=args.translation_updates,equipment_rigs=args.equipment_rigs,
                            room_rigs_art=args.room_rigs_art,scenery_art=args.scenery_art,scenery_gameplay=args.scenery_gameplay,
                            expand_storage=args.expand_storage,furniture_audio_art=args.furniture_audio_art,
                            furniture_profiles=args.furniture_profiles,material_frames_art=args.material_frames_art)
            if args.refresh_runtime else build(args.output,args.art,args.base_lock))
    print(json.dumps({k:result[k] for k in ('runtime_abi','output_sha256','patch_sha256')},indent=2))
