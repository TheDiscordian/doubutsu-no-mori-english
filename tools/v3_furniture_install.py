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
from v3_furniture_pipeline import (Source,LAYERS,prepare,metadata,identity_rows,draw_sequence,
    PENDING_MOVE_CATEGORY,PENDING_SEQUENCE_CATEGORY,SELECTED_PALETTE_CATEGORY)
from v3_furniture_pipeline import VERSION as ASSET_VERSION
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
import v3_physical_resources as physical

VERSION = 21
LOCK = ROOT/'config/v3-import-build.json'
STABLE = ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64'
STABLE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
SOURCES = capacity.SOURCES + physical.SOURCES + ('tools/v3_furniture_pipeline.py', 'tools/v3_furniture_install.py', 'tools/map_artwork.py', 'tools/v3_room_aliases.py',
    'tools/v3_furniture_rigs.py', 'tools/v3_furniture_materials.py', 'tools/v3_furniture_scroll.py', 'tools/v3_keyframes.py',
    'tools/v3_furniture_art.py', 'tools/v3_furniture_composite.py', 'tools/v3_registry.py', 'tools/v3_catalogue.py',
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
    physical.verify(base,report.get('physical_resources',[]))
    return base, report


def profile(row, vrom, *, limit=END, model_capacity=9216):
    n, offsets = row['object_bytes'], row['model_offsets']
    scalar = bytes.fromhex(row['native_profile_scalar_hex'])
    adapter=row.get('profile',{}).get('callback_adapter',{})
    fading = adapter.get('category') == 'switch-palette-fade'
    from v3_console_room import CATEGORY as CONSOLE_CATEGORY,VTABLE as CONSOLE_VTABLE,profile_lifecycle as console_lifecycle
    console = adapter.get('category') == CONSOLE_CATEGORY and console_lifecycle(row['profile'],row.get('room_lifecycle'))
    sequence = adapter.get('category') == 'constant-model-sequence' or console
    sound = adapter.get('category') == 'switch-trigger-sound'
    static = adapter.get('category') == 'static-interaction'
    from v3_furniture_rigs import RIG_CATEGORIES,FIXED_CATEGORY,JOINT_CATEGORY,EMBEDDED_CATEGORY,CREATURE_STATIC_CATEGORY
    from v3_creature_items import lifecycle as creature_lifecycle
    creature=adapter.get('category') in (EMBEDDED_CATEGORY,CREATURE_STATIC_CATEGORY)
    embedded=creature and adapter['category']==EMBEDDED_CATEGORY
    from v3_furniture_materials import CATEGORY as MATERIAL_CATEGORY
    from v3_furniture_scroll import CATEGORY as SCROLL_CATEGORY,VTABLE as SCROLL_VTABLE,profile_lifecycle
    material=adapter.get('category')==MATERIAL_CATEGORY
    scrolling=adapter.get('category')==SCROLL_CATEGORY
    roof=adapter.get('category')==SELECTED_PALETTE_CATEGORY
    from v3_furniture_roofs import profile_lifecycle as roof_lifecycle
    from v3_furniture_joint_rigs import profile_lifecycle as joint_lifecycle
    from v3_furniture_composite import ROTATED_CATEGORY,DUAL_CATEGORY,dual_profile_lifecycle
    from v3_room_music import lifecycle as music_lifecycle
    radio=adapter.get('category')==ROTATED_CATEGORY
    if (adapter.get('category')==JOINT_CATEGORY and not joint_lifecycle(
            row['profile'],row.get('room_lifecycle'),row.get('room_placement')) or
            roof and not roof_lifecycle(row['profile'],row.get('room_lifecycle')) or
            adapter.get('category')==DUAL_CATEGORY and not dual_profile_lifecycle(row['profile'],row.get('room_lifecycle'),row.get('room_placement')) or
            radio and row.get('room_lifecycle')!=music_lifecycle(row['profile']) or
            creature and (creature_lifecycle(row['profile']) is None or
                row.get('room_lifecycle')!=creature_lifecycle(row['profile'])) or
            adapter.get('category') in (FIXED_CATEGORY,PENDING_MOVE_CATEGORY) or
            adapter.get('category')==PENDING_SEQUENCE_CATEGORY and not console or scrolling and
            (not profile_lifecycle(row['profile'],row.get('room_lifecycle'),row.get('room_placement')) or
             row.get('room_runtime')!={'vtable':SCROLL_VTABLE,'vrom':vrom})):
        raise ValueError('Prepared resources have no implemented native lifecycle')
    rigged = embedded or adapter.get('category') in RIG_CATEGORIES
    layers = tuple(offsets) if rigged else tuple(adapter['model_order']) if fading or sequence or material or scrolling or roof or radio else LAYERS
    if (model_capacity not in (9216,12288) or limit not in (END,capacity.LIMIT) or not 0 < n <= model_capacity or n%16 or vrom%16 or vrom+n > limit or len(scalar) != 16
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
    if console and row.get('room_runtime')!={'vtable':CONSOLE_VTABLE,'vrom':vrom}:
        raise ValueError('Console furniture needs its complete installed room dispatch')
    if sound or static:
        from v3_room_rig_runtime import SOUND_VTABLE
        if row.get('room_runtime')!={'vtable':SOUND_VTABLE,'vrom':vrom}:
            raise ValueError('Sound profile requires its complete installed room lifecycle')
    if material:
        from v3_room_rig_runtime import MATERIAL_VTABLE
        from v3_furniture_materials import initializer_lifecycle,steam_profile_lifecycle,switched_profile_lifecycle
        from v3_furniture_reactions import profile_lifecycle as reaction_lifecycle,colour_profile_lifecycle
        initial=initializer_lifecycle(None,row['profile'])
        reaction=(reaction_lifecycle(row['profile'],row.get('room_lifecycle')) or
                  colour_profile_lifecycle(row['profile'],row.get('room_lifecycle')) or
                  steam_profile_lifecycle(row['profile'],row.get('room_lifecycle')) or
                  switched_profile_lifecycle(row['profile'],row.get('room_lifecycle'),row.get('room_placement')))
        if (row.get('room_runtime')!={'vtable':MATERIAL_VTABLE,'vrom':vrom} or
                (row.get('room_lifecycle')!=initial if initial else not reaction and set(adapter['functions'])!={'move','draw'}) or
                set(offsets)!=set(layers)):
            raise ValueError('Prepared resources have no implemented native material lifecycle')
        pointers=[0,0,0,0]
    if scrolling:
        if set(offsets)!=set(layers):raise ValueError('Scrolling profile needs every source model')
        pointers=[0,0,0,0]
    if roof or radio:
        from v3_room_rig_runtime import VTABLE
        if row.get('room_runtime')!={'vtable':VTABLE,'vrom':vrom} or set(offsets)!=set(layers):
            raise ValueError('Selected roof profile requires its complete installed native lifecycle')
        pointers=[0,0,0,0]
    return (struct.pack('>12I', vrom, vrom+n, 0x06000000, 0x06000000+n, *pointers, 0,0,0,0)+scalar+
            struct.pack('>I',VTABLE if rigged or roof or radio else SOUND_VTABLE if sound or static else MATERIAL_VTABLE if material else
                        SCROLL_VTABLE if scrolling else CONSOLE_VTABLE if console else palette_fade.VTABLE if fading else 0))


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


def provenance_patch(rows,locators=('tools/v3_furniture_pipeline.py','tools/v3_furniture_install.py')):
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
            locator=list(locators),
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
    from v3_hra_birth import checked_categories
    mapping, binding = checked_categories(files[hra.NEW_VROM].extract(base), prior['hra'], source)
    for row in rows:
        donor,native=row['donor_birth_category'],row['birth_category']
        if (not 0 <= donor < len(mapping) or native != mapping[donor]
                or native >= binding['native_counter_count']):
            raise ValueError('Scoring category lacks its installed native counter')
        value=int(row['donor_hra_hex'],16)
        expected=(value&0xFFFFC000)|(native<<9)|((value>>6&3)<<7)
        if value>>8&63 != donor or value&63 or row['native_hra_hex'] != f'{expected:08x}':
            raise ValueError('Scoring metadata differs from the complete donor birth conversion')
        if donor!=native:
            points=struct.unpack_from('>I',source.raw('mMkRm_birth_point_table'),donor*4)[0]
            aliases.append(dict(**binding,donor_category=donor,native_scoring_category=native,
                points=points,item_id=row['item_id']))
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
                if not 0 <= row['series'] < report['series']['count']:
                    raise ValueError('Scoring series exceeds installed category storage')
                series = report['series']; start = series['info_address']-hra.RAM+row['series']*3
                actual = data[start:start+3]; expected = bytes.fromhex(row['donor_series_hex'])
                # Existing theme adapters explicitly omit unavailable matching
                # surfaces. Do not invent a surface ID or another per-item rule.
                adapters = [r for r in series.values() if isinstance(r,dict) and r.get('series')==row['series']]
                if actual != expected and not (len(adapters)==1
                        and actual == expected[:2]+bytes([adapters[0]['native_wall_floor_index']])
                        and expected[2]==adapters[0]['donor_wall_floor_index']):
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
    if (art['format'] != 'AFV3-AUTO-FURNITURE-ASSETS-1' or art['version'] not in range(7, ASSET_VERSION+1)
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
        # Generated metadata is JSON: relocation offsets inside full lifecycle
        # receipts become string keys, just as in the checked model descriptor.
        meta = json.loads(json.dumps(metadata(source,item,descriptor,identities[item])))
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
    padding=previous.get('resource_tail_padding')
    if padding is not None:
        first=padding['blob_offset'];end=files[BLOB].pstart+len(old_blob)
        if (first%16 or not PACKAGE+PACKAGE_SIZE<=first<=len(old_blob) or
                padding['bytes']!=len(old_blob)-first or any(old_blob[first:]) or
                any(e.pstart<end and files[BLOB].pstart+first<(e.pend or e.pstart+e.size)
                    for v,e in files.items() if v!=BLOB and e.pstart!=0xFFFFFFFF)):
            raise ValueError('Changed reusable zero padding or overlapping DMA owner')
        for row in moves:
            entry=files[row['vrom']]
            if (entry.pend or entry.pstart!=row['physical'] or entry.size!=row['bytes'] or
                    sha256(entry.extract(base))!=row['sha256'] or 'blob_offset' in row or
                    entry.pstart<end and files[BLOB].pstart<entry.pstart+entry.size):
                raise ValueError('Changed external regenerated resource')
        for at in range(ROWS,ITEMS,80):
            if any(old_blob[at:at+80]):
                lo,hi=struct.unpack_from('>II',old_blob,at+8)
                if lo<BLOB+len(old_blob) and BLOB+first<hi:
                    raise ValueError('Reusable zero padding overlaps retained furniture')
        return bytearray(old_blob[:first]),dict(reused_bytes=len(old_blob)-first,
            blob_offset=first,source_blob_sha256=sha256(old_blob),
            retained_prefix_sha256=sha256(old_blob[:first]),retired_resources=[],
            external_resources=copy.deepcopy(moves))
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


def place_resource_tail(base,prior,blob,resources,limit,*,reservations=()):
    """Keep regenerated owners outside item storage when the common tail fills.

    Preserve their DMA identities and complete contents. Reclaimed item storage
    remains a checked zero tail, reusable by ordinary imports and runtime batches.
    """
    files=by_vrom(base);order=(catalogue.VROM,catalogue.RELOC,shops.VROM)
    if set(resources)!=set(order):raise ValueError('Incomplete regenerated owner batch')
    old_bytes=files[BLOB].size;after=len(blob)
    for vrom in order:after=((after+15)&~15)+len(resources[vrom])
    external=prior.get('automatic_furniture',{}).get('resource_tail_padding') is not None
    if not external and old_bytes<=after<=limit-BLOB:
        moves=[]
        for vrom in order:
            data=resources[vrom];blob.extend(bytes(-len(blob)%16));at=len(blob);blob.extend(data)
            moves.append(dict(vrom=vrom,blob_offset=at,bytes=len(data),
                physical=files[BLOB].pstart+at,sha256=sha256(data)))
        return moves,{},None
    blob.extend(bytes(-len(blob)%16));first=len(blob)
    if max(first,old_bytes)>limit-BLOB:raise ValueError('Complete resources exceed reusable item storage')
    blob.extend(bytes(max(0,old_bytes-len(blob))))
    moved=[];pending=[];writes={}
    for vrom in order:
        entry=files[vrom];data=resources[vrom]
        if not data:raise ValueError('Empty regenerated resource')
        if external and not entry.pend and data==entry.extract(base):
            moved.append(dict(vrom=vrom,bytes=len(data),physical=entry.pstart,
                storage='retained-external',sha256=sha256(data),original_sha256=sha256(data)))
        else:pending.append((vrom,data));writes[vrom]=data
    moved.extend(owner_tail_storage(base,files,pending,
        minimum_end=max(files[BLOB].pstart+len(blob),
            prior.get('resource_capacity',{}).get('reserved_physical_end',0)),reservations=reservations))
    moved.sort(key=lambda r:order.index(r['vrom']))
    return moved,writes,dict(blob_offset=first,bytes=len(blob)-first)


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
            native = profile(row,vrom,limit=limit,model_capacity=source.model_bank_capacity); blob.extend(asset)
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
    tail_resources={v:changes.pop(v) for v in (catalogue.VROM,catalogue.RELOC,shops.VROM)}
    moves,tail_writes,tail_padding=place_resource_tail(base,prior,blob,tail_resources,limit,
        reservations=prior.get('physical_resources',[]))
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
    for row in moves:
        if row['vrom'] in tail_writes:
            result[row['physical']:row['physical']+row['bytes']]=tail_writes[row['vrom']]
    struct.pack_into('>I',result,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
    for row in owner_moves+moves:
        struct.pack_into('>4I',result,DMA_START+files[row['vrom']].index*16,
            row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
    physical.verify(result,prior.get('physical_resources',[]))
    fix_checksum(result); result=bytes(result)
    if set(by_vrom(result))!=set(files) or result[DMA_END-16:DMA_END]!=bytes(16): raise ValueError('Directory changed')
    patch=make_ups(original,result)
    if apply_ups(original,patch)!=result: raise ValueError('Patch reconstruction failed')
    report=copy.deepcopy(prior)
    if report.get('staged_furniture'):
        promoted={r['item_id'] for r in installed}
        promoted_sources={f'{furniture_source(r)[0]:04X}' for r in installed}
        report['staged_furniture']['rows']=[r for r in report['staged_furniture']['rows'] if r['item_id'] not in promoted]
        complete={f'{furniture_source(r)[0]:04X}' for r in all_furniture['imports']+report['staged_furniture']['rows']}
        report['staged_furniture']['deferred_resources']=[r for r in report['staged_furniture'].get('deferred_resources',[])
            if r['source_item_id'] not in complete]
        runtime=report['equipment_resources']['room_rigs']
        for row in runtime['rows']+runtime['sound_rows']+runtime.get('material_rows',[])+runtime.get('static_rows',[])+runtime.get('plain_rows',[])+runtime.get('scrolling',{}).get('rows',[]):
            if row['source_item_id'] in promoted_sources:row['parent_selectable']=True
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
        resource_moves=moves,resource_tail_padding=tail_padding,owner_moves=owner_moves,resource_tail_reuse=reused,additional_resident_bytes=0,saved_format_changed=False,
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


def owner_tail_storage(base,files,changes,*,minimum_end=0,reservations=()):
    """Allocate complete changed overlays after live physical cartridge data.

    Overlay VROM identities already exist; consuming import-object VROM space
    for their uncompressed copies needlessly constrains later shared adapters.
    Keep the 64-MiB image, require zero padding, and retain every old resource.
    """
    cursor=max(minimum_end,max(e.pend or e.pstart+e.size for e in files.values() if e.pstart!=0xFFFFFFFF))
    rows=[]
    for vrom,data in changes:
        first=(cursor+15)&~15;end=first+len(data);entry=files[vrom]
        for row in sorted(reservations,key=lambda r:r['physical']):
            if row['physical']<end and first<row['physical']+row['bytes']:
                cursor=row['physical']+row['bytes'];first=(cursor+15)&~15;end=first+len(data)
        if (not data or len(base)!=0x4000000 or end>len(base) or any(base[cursor:end])
                or physical.overlaps(reservations,first,end)
                or any(e.pstart<end and first<(e.pend or e.pstart+e.size)
                       for e in files.values() if e.pstart!=0xFFFFFFFF)):
            raise ValueError('Changed owner requires verified unused cartridge-tail storage')
        rows.append(dict(vrom=vrom,bytes=len(data),physical=first,storage='cartridge-tail',
                         sha256=sha256(data),original_sha256=sha256(entry.extract(base))))
        cursor=end
    return rows


def append_resource_plan(base,files,vrom,data,relocatable,*,target_vrom=None):
    """Append a complete resource in place; move only checked DMA-owned blockers."""
    entry=files[vrom];before=entry.extract(base)
    if entry.pend or len(data)<=len(before) or data[:len(before)]!=before:
        raise ValueError('In-place growth must retain the complete uncompressed resource')
    first=entry.pstart+entry.size;end=entry.pstart+len(data)
    target=vrom if target_vrom is None else target_vrom
    if (type(target) is not int or target&15 or not 0<=target<target+len(data)<=0x100000000 or
            end>len(base) or any(e.vstart<target+len(data) and target<e.vend
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
    record=dict(vrom=vrom,physical=entry.pstart,previous_bytes=entry.size,
        bytes=len(data),previous_sha256=sha256(before),sha256=sha256(data),relocated_blockers=blockers)
    if target!=vrom:record['target_vrom']=target
    return changes,record


def relocate_resource_plan(base,files,vrom,data,*,minimum_physical,target_vrom=None,reservations=(),append_only=True,allow_compressed=False):
    """Keep a whole growing resource in verified zero, unmapped cartridge space.

    Logical identity is retained unless the caller declares a new virtual base.
    Callers must account for every reader of either changed address;
    old copies are left untouched, never treated as free data merely because
    they are absent from the current DMA directory.
    """
    entry=files[vrom];before=entry.extract(base)
    destination=vrom if target_vrom is None else target_vrom
    if ((entry.pend and (not allow_compressed or append_only)) or not data or append_only and (len(data)<=len(before) or data[:len(before)]!=before) or
            type(destination) is not int or destination&15 or not 0<=destination<destination+len(data)<=0x100000000 or
            any(e.vstart<destination+len(data) and destination<e.vend for v,e in files.items() if v!=vrom)):
        raise ValueError('Relocation needs a complete non-overlapping resource')
    occupied=sorted([(e.pstart,e.pend or e.pstart+e.size) for e in files.values() if e.pstart!=0xFFFFFFFF]+
        [(r['physical'],r['physical']+r['bytes']) for r in reservations])
    cursor=minimum_physical
    for first,last in occupied+[(len(base),len(base))]:
        start=(cursor+15)&~15
        if start+len(data)<=first and not any(base[start:start+len(data)]):
            record=dict(vrom=vrom,physical=start,previous_physical=entry.pstart,
                previous_bytes=entry.size,bytes=len(data),previous_sha256=sha256(before),sha256=sha256(data),
                relocated_blockers=[],relocated=True,retains_old_allocation=True)
            if destination!=vrom:record['target_vrom']=destination
            if entry.pend:record['previous_compressed_end']=entry.pend
            return {vrom:data},record
        cursor=max(cursor,last)
    raise ValueError('No verified zero cartridge gap for complete resource growth')


def refresh_runtime(output, lock=LOCK, *, equipment_art=None, player_motion=False, equipment_kinds=False,
                    player_actions=False, item_category_art=None, ground_categories=False, event_acquisition=False,
                    held_collection=False, held_catalogue_art=None, held_selection=False, translation_updates=False,
                    room_rigs_art=None, room_rigs_code=False, room_goods=None, room_carry=None, scenery_art=None, scenery_gameplay=False,
                    equipment_rigs=None, expand_storage=False, furniture_audio_art=None, furniture_profiles=None,
                    material_frames_art=None,scrolling_materials_art=None,room_surfaces_art=None,furniture_scoring=False,
                    password_runtime=None,password_editor=False,room_effects=None,furniture_capacity=False,console_storage=False,
                    console_images=None,console_emulator=False,console_disk=None,creature_items=None,creature_field=None,creature_fish=False,creature_insects=None,clothing_batch=None,diaries=None,diary_items=False,diary_room_art=None,diary_catalogue=False,npc_registry_art=None,holiday_actor_services=False,holiday_participants=None,carried_items=None):
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
    moved=[];tail_writes={};tail_padding=None;equipment_report=None;reused=None;owner_changes={};owner_moves=[];owner_updates=[];report_updates={};text_moves=[];physical_writes=[]
    equipment_mode=any((equipment_art is not None,equipment_rigs is not None,player_motion,equipment_kinds,player_actions,
                        item_category_art is not None,ground_categories,event_acquisition,held_collection,held_catalogue_art is not None,held_selection,room_rigs_art is not None,scenery_art is not None,scenery_gameplay))
    resource_mode=equipment_mode or room_rigs_code or room_goods is not None or room_carry is not None or translation_updates or expand_storage or furniture_audio_art is not None or furniture_profiles is not None or material_frames_art is not None or scrolling_materials_art is not None or room_surfaces_art is not None or furniture_scoring or password_runtime is not None or password_editor or room_effects is not None or furniture_capacity or console_storage or console_images is not None or console_emulator
    if sum((equipment_art is not None,equipment_rigs is not None,player_motion,equipment_kinds,player_actions,
            item_category_art is not None,ground_categories,event_acquisition,held_collection,held_catalogue_art is not None,held_selection,translation_updates,room_rigs_art is not None,room_rigs_code,room_goods is not None,room_carry is not None,scenery_art is not None,scenery_gameplay,expand_storage,furniture_audio_art is not None,furniture_profiles is not None,material_frames_art is not None,scrolling_materials_art is not None,room_surfaces_art is not None,furniture_scoring,password_runtime is not None,password_editor,room_effects is not None,furniture_capacity,console_storage,console_images is not None,console_emulator))>1:
        raise ValueError('Install shared runtime updates in dependency order')
    if console_disk is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if creature_items is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if creature_field is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if creature_fish:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if creature_insects is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if clothing_batch is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if diaries is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if diary_items:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if diary_room_art is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if diary_catalogue:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if npc_registry_art is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if holiday_actor_services:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if carried_items is not None:
        if resource_mode:raise ValueError('Install shared runtime updates in dependency order')
        resource_mode=True
    if resource_mode:
        blob,reused=reuse_resource_tail(base,prior,old_blob)
        if not reused['reused_bytes'] and not reused.get('external_resources'):
            raise ValueError('Equipment integration requires the checked shared resource tail')
    parent_readers=bool(player_actions and prior.get('equipment_resources',{}).get('player_actions',{}).get('equipment_selection'))
    wrapped_names=bool(player_actions and prior.get('equipment_resources',{}).get('wrapped_presents'))
    if carried_items is not None:
        import v3_carried_runtime as equipment
        equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
            base,prior,blob,core,module,output,carried_items)
        display_report=prior['clothing']['display'];alias_report=prior['display_aliases']
    elif holiday_actor_services:
        current_events=prior['equipment_resources'].get('npc_extra',{}).get('events',{})
        if holiday_participants is not None:
            import v3_holiday_participants_install as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
                base,prior,blob,core,output,holiday_participants)
        elif (prior['equipment_resources']['npc_extra'].get('optional_dialogue') and
                not current_events.get('selection')):
            import v3_holiday_selection as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
                base,prior,blob,core,output)
        elif (current_events.get('festivals') and
                not prior['equipment_resources']['npc_extra'].get('optional_dialogue')):
            import v3_holiday_world as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_optional(
                base,prior,blob,core,output)
        elif (current_events.get('exercise') and
                not prior['equipment_resources']['holiday_items'].get('controls')):
            import v3_holiday_items as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_controls(
                base,prior,blob,core,output)
        elif (prior['equipment_resources'].get('holiday_items',{}).get('controls') and
                not current_events.get('calendar')):
            import v3_holiday_calendar as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
                base,prior,blob,core,output)
        elif (current_events.get('decorations',{}).get('controllers') and
                not prior['equipment_resources'].get('holiday_items')):
            import v3_holiday_items as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
                base,prior,blob,core,module,output)
        elif (prior['equipment_resources'].get('holiday_items') and
                not prior['equipment_resources']['holiday_items'].get('pickup')):
            import v3_holiday_items as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_pickup(
                base,prior,blob,core,output)
        elif not prior['equipment_resources'].get('holiday_fishing'):
            import v3_holiday_fishing as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
                base,prior,blob,core,output)
        elif not prior['equipment_resources']['holiday_fishing'].get('live'):
            import v3_holiday_fishing as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_live(
                base,prior,blob,core,output)
        elif not prior['equipment_resources']['holiday_fishing']['live'].get('angler'):
            import v3_holiday_fishing as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_angler(
                base,prior,blob,core,output)
        elif not prior['equipment_resources']['holiday_fishing']['live'].get('mail'):
            import v3_holiday_fishing as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_mail(
                base,prior,blob,core,output)
        elif not prior['equipment_resources']['holiday_fishing']['live'].get('measurement_choice'):
            import v3_holiday_fishing as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_measurements(
                base,prior,blob,core,output)
        elif not prior['equipment_resources']['npc_extra']['events'].get('demo'):
            import v3_holiday_scene as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_demo(
                base,prior,blob,core,output)
        elif not current_events['demo'].get('scene_services'):
            import v3_holiday_scene as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_demo(
                base,prior,blob,core,output,scene_services=True)
        elif not current_events['transition'].get('native_scene_services_bound'):
            import v3_holiday_transition as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
                base,prior,blob,core,output)
        elif not current_events.get('dispatch'):
            import v3_holiday_active as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install_dispatch(
                base,prior,blob,core,output)
        elif not current_events.get('sky'):
            import v3_holiday_sky as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
                base,prior,blob,core,output)
        else:
            import v3_holiday_motion as equipment
            equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
                base,prior,blob,core,output)
        display_report=prior['clothing']['display'];alias_report=prior['display_aliases']
    elif npc_registry_art is not None:
        import v3_npc_registry as equipment
        equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
            base,prior,blob,core,output,npc_registry_art,lock,module=module)
        display_report=prior['clothing']['display'];alias_report=prior['display_aliases']
    elif diary_catalogue:
        import v3_diary_items as equipment
        equipment_report,owner_changes,report_updates,physical_writes=equipment.install_catalogue(base,prior,blob,core,output)
        display_report=prior['clothing']['display'];alias_report=prior['display_aliases']
    elif diary_room_art is not None:
        import v3_diary_items as equipment
        equipment_report,owner_changes,report_updates,physical_writes=equipment.install_room(
            base,prior,blob,core,output,diary_room_art)
        display_report=prior['clothing']['display'];alias_report=prior['display_aliases']
    elif diary_items:
        import v3_diary_items as equipment
        equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
            base,prior,blob,core,module,output)
        display_report=report_updates['clothing']['display']
        alias_report=prior['display_aliases']
    elif diaries is not None:
        import v3_diary_install as equipment
        equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
            base,prior,blob,core,output,diaries)
        display_report=report_updates['clothing']['display']
        alias_report=prior['display_aliases']
    elif clothing_batch is not None:
        import v3_clothing_install as equipment
        equipment_report,owner_changes,report_updates=equipment.install(
            base,prior,blob,core,output,clothing_batch.resolve())
        display_report=report_updates['clothing']['display']
        alias_report=report_updates['display_aliases']
    elif creature_insects is not None:
        import v3_creature_insect_install as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes,report_updates,physical_writes=equipment.install(
            base,prior,blob,output,creature_insects,core)
        display_report=report_updates['clothing']['display']
    elif creature_fish:
        import v3_creature_fish as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        result=equipment.install(base,prior,blob,output,core=core)
        equipment_report,owner_changes=result[:2]
        if len(result)==3:
            report_updates=result[2]
            display_report=report_updates['clothing']['display']
    elif creature_field is not None:
        import v3_creature_field_native as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes,report_updates,physical_writes=equipment.install(base,prior,blob,output,creature_field)
    elif creature_items is not None:
        import v3_creature_items as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,module,output,creature_items)
    elif console_disk is not None:
        import v3_console_disk_install as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes=equipment.install(base,prior,blob,output,console_disk)
    elif console_emulator:
        import v3_console_emulator as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes=equipment.install(base,prior,blob,output,original)
    elif console_images is not None:
        import v3_console_image_native as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,report_updates,physical_writes=equipment.install(base,prior,blob,output,console_images)
    elif console_storage:
        import v3_console_storage as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes,report_updates=equipment.install(base,prior,blob,core,output)
        display_report=report_updates['clothing']['display']
    elif furniture_capacity:
        import v3_furniture_capacity as model_capacity
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        owner_changes,report_updates=model_capacity.install(base,prior,blob,core,output)
    elif room_effects is not None:
        import v3_room_effects as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes,report_updates=equipment.install(base,prior,blob,core,original,output,room_effects)
    elif room_carry is not None:
        import v3_room_carry_native as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes=equipment.install(base,prior,blob,output,room_carry)
    elif room_goods is not None:
        import v3_room_goods as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report,owner_changes=equipment.install(base,prior,blob,output,room_goods)
    elif room_rigs_code:
        import v3_room_rig_runtime as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report=copy.deepcopy(prior['equipment_resources'])
        equipment.refresh_code(equipment_report,blob,output,core=core)
    elif password_editor:
        import v3_password_editor as password_ui
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        owner_changes,report_updates=password_ui.install(base,prior,core,original,output)
    elif password_runtime is not None:
        import v3_password_runtime as equipment
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        equipment_report=equipment.install(base,prior,blob,original,output,password_runtime,lock)
    elif furniture_scoring:
        import v3_furniture_scoring as scoring_categories
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        owner_changes,report_updates=scoring_categories.install(base,prior,core,module)
    elif expand_storage:
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        report_updates,text_moves=capacity.expand(base,prior,core)
        limit=report_updates['import_storage']['virtual_limit']
    elif translation_updates:
        import v3_translation_updates as translation
        display_report,alias_report=prior['clothing']['display'],prior['display_aliases']
        owner_changes,report_updates=translation.install(base,prior,module,output)
    elif held_catalogue_art is not None or wrapped_names or furniture_audio_art is not None or furniture_profiles is not None or material_frames_art is not None or scrolling_materials_art is not None or room_surfaces_art is not None:
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
    elif scrolling_materials_art is not None:
        import v3_furniture_scroll as equipment
        equipment_report,owner_changes=equipment.install(base,prior,blob,core,original,output,scrolling_materials_art)
    elif room_surfaces_art is not None:
        import v3_surface_runtime as surfaces
        import v3_surface_items as equipment
        owner_changes,report_updates=surfaces.install(base,prior,blob,core,original,output,room_surfaces_art,module=module)
        equipment_report=report_updates.get('equipment_resources')
        if 'clothing' in report_updates:display_report=report_updates['clothing']['display']
    elif held_selection:
        import v3_held_catalogue as equipment
        equipment_report,owner_changes,report_updates=equipment.select_installed(prior,blob)
    if equipment_report and equipment_report.get('room_rigs',{}).get('music'):
        from v3_room_music import publish_owner
        publish_owner(base,prior,equipment_report,owner_changes)
    if equipment_report and equipment_report.get('room_rigs',{}).get('embedded_engine'):
        from v3_furniture_motion import publish_embedded_dispatch,OWNER as room_owner
        publish_embedded_dispatch(base,prior,equipment_report,owner_changes)
        digest=sha256(owner_changes[room_owner])
        for name,path in (('furniture_placement',('owner_sha256',)),
                          ('furniture_behaviours',('contacts','native_owner_sha256'))):
            updated=copy.deepcopy(report_updates.get(name,prior[name]));row=updated
            for key in path[:-1]:row=row[key]
            row[path[-1]]=digest;report_updates[name]=updated
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
        menu_resizes={r['vrom']:r for r in report_updates.get('furniture_scoring',{}).get('owner_resizes',[])}
        if password_editor:
            menu_resizes={r['vrom']:r for r in report_updates['password_editor']['owner_resizes']}
        if (player_actions and equipment_report['player_actions'].get('balloon_menu') and
                not prior['equipment_resources']['player_actions'].get('balloon_menu')):
            menu_resizes={r['vrom']:r for r in equipment_report['player_actions']['balloon_menu']['owner_resizes']}
            if set(menu_resizes)!={0x3950000,0x3960000} or not set(menu_resizes)<=set(owner_changes):
                raise ValueError('Incomplete declared balloon-menu owner resize')
        runtime_resizes=report_updates.get('runtime_owner_resizes',[])
        runtime_by_vrom={r['vrom']:r for r in runtime_resizes}
        if (len(runtime_by_vrom)!=len(runtime_resizes) or set(runtime_by_vrom)&set(menu_resizes)
                or not set(runtime_by_vrom)<=set(owner_changes)):
            raise ValueError('Conflicting or incomplete declared runtime owner resize')
        menu_resizes.update(runtime_by_vrom)
        for vrom,data in owner_changes.items():
            entry=files[vrom]
            if vrom in growth_vroms:
                row=next(r for r in growth if r['vrom']==vrom)
                if (entry.pend!=row.get('previous_compressed_end',0) or
                        (entry.pend and not row.get('relocated')) or
                        entry.size!=row['previous_bytes'] or entry.pstart!=row.get('previous_physical',row['physical'])
                        or len(data)!=row['bytes'] or sha256(data)!=row['sha256']
                        or sha256(entry.extract(base))!=row['previous_sha256']):
                    raise ValueError('Changed complete resource growth plan')
                if row.get('relocated'):
                    start,end=row['physical'],row['physical']+row['bytes']
                    if (start&15 or not 0<=start<end<=len(base) or any(base[start:end]) or
                            physical.overlaps(report_updates.get('physical_resources',prior.get('physical_resources',[])),start,end) or
                            any(e.pstart<end and start<(e.pend or e.pstart+e.size)
                                for e in files.values() if e.pstart!=0xFFFFFFFF) or
                            any(r is not row and r['physical']<end and start<r['physical']+r['bytes'] for r in growth)):
                        raise ValueError('Relocated resource overlaps occupied or nonzero cartridge data')
                target=row.get('target_vrom',vrom)
                if (target&15 or not 0<=target<target+len(data)<=0x100000000 or
                        any(e.vstart<target+len(data) and target<e.vend for v,e in files.items() if v!=vrom) or
                        any(r is not row and r.get('target_vrom',r['vrom'])<target+len(data) and
                            target<r.get('target_vrom',r['vrom'])+r['bytes'] for r in growth)):
                    raise ValueError('Changed resource virtual destination overlaps a live owner')
                continue
            if vrom in (catalogue.VROM,catalogue.RELOC,shops.VROM):
                # These complete owners are placed once by the shared tail
                # planner, including when their prior mapping is external.
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
        tail_resources={v:owner_changes.get(v,files[v].extract(base))
            for v in (catalogue.VROM,catalogue.RELOC,shops.VROM)}
        moved,tail_writes,tail_padding=place_resource_tail(base,prior,blob,tail_resources,limit,
            reservations=report_updates.get('physical_resources',prior.get('physical_resources',[]))+growth)
        external=[(v,d) for v,d in external if v not in tail_resources]
        owner_moves=owner_tail_storage(base,files,external,
            minimum_end=max([files[BLOB].pstart+len(blob)]+[r['physical']+r['bytes'] for r in growth+moved]),
            reservations=report_updates.get('physical_resources',prior.get('physical_resources',[])))
        owner_moves.extend(dict(vrom=r['vrom'],bytes=r['bytes'],physical=r['physical'],
            storage='checked-zero-gap' if r.get('relocated') else 'checked-in-place-append',
            sha256=r['sha256'],original_sha256=r['previous_sha256'],
            **({'target_vrom':r['target_vrom']} if 'target_vrom' in r else {})) for r in growth)
    if equipment_report and equipment_report.get('furniture_melody_audio'):
        from v3_furniture_melody import rebind_wave_header
        rebind_wave_header(equipment_report,core)
    if equipment_report and equipment_report.get('room_goods'):
        import v3_room_goods as loose_items
        surface=copy.deepcopy(report_updates.get('room_surfaces',prior['room_surfaces']))
        loose_items.publish_bootstrap(equipment_report,blob,surface,output)
        report_updates['room_surfaces']=surface
    abi=prior['runtime_abi']+1; struct.pack_into('>I',blob,4,abi)
    package=blob[PACKAGE:PACKAGE+PACKAGE_SIZE]; struct.pack_into('>I',blob,0xF8,zlib.crc32(package))
    old=prior['startup']
    defines=tuple(f[2:] if not f.startswith('-DAF_V3_ABI=') else f'AF_V3_ABI={abi}'
        for f in old['flags'] if f.startswith('-D'))
    if 'object_capacity' in report_updates:
        defines=tuple(f for f in defines if not f.startswith('AF_V3_OBJECT_CAPACITY='))
        defines+=(f'AF_V3_OBJECT_CAPACITY={report_updates["object_capacity"]}',)
    if equipment_report:
        defines=tuple(f for f in defines if not f.startswith(('AF_V3_EQUIPMENT_VROM=','AF_V3_EQUIPMENT_CRC=',
                                                            'AF_V3_EQUIPMENT_BYTES=')))
        defines+=(f'AF_V3_EQUIPMENT_VROM=0x{equipment_report["vrom"]:08X}u',
                  f'AF_V3_EQUIPMENT_CRC=0x{equipment_report["crc32"]:08X}u',
                  f'AF_V3_EQUIPMENT_BYTES=0x{equipment_report["bytes"]:X}u')
    surface_items=report_updates.get('room_surfaces',{}).get('items')
    if report_updates.get('room_surfaces',{}).get('optional_selection'):
        defines=tuple(f for f in defines if not f.startswith('AF_V3_EDITABLE_CHECKSUMS='))
        defines+=('AF_V3_EDITABLE_CHECKSUMS=1',)
    if surface_items:
        defines=tuple(f for f in defines if not f.startswith('AF_V3_FURNITURE_INIT='))
        defines+=(f'AF_V3_FURNITURE_INIT=0x{surface_items["bootstrap"]["ram"]:X}u',)
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
        for row in moved:
            if row['vrom'] in tail_writes:
                result[row['physical']:row['physical']+row['bytes']]=tail_writes[row['vrom']]
        for row in owner_moves:
            result[row['physical']:row['physical']+row['bytes']]=owner_changes[row['vrom']]
        struct.pack_into('>I',result,DMA_START+files[BLOB].index*16+4,BLOB+len(blob))
        for row in moved+owner_moves:
            target=row.get('target_vrom',row['vrom'])
            struct.pack_into('>4I',result,DMA_START+files[row['vrom']].index*16,
                             target,target+row['bytes'],row['physical'],0)
    if text_moves:capacity.relocate_directory(result,files,text_moves)
    expected=bytearray(base[DMA_START:DMA_END])
    if resource_mode:
        struct.pack_into('>I',expected,files[BLOB].index*16+4,BLOB+len(blob))
        for row in moved+owner_moves:
            target=row.get('target_vrom',row['vrom'])
            struct.pack_into('>4I',expected,files[row['vrom']].index*16,
                             target,target+row['bytes'],row['physical'],0)
    for row in text_moves:
        struct.pack_into('>2I',expected,row['directory_index']*16,row['vrom'],row['vrom']+row['bytes'])
    if result[DMA_START:DMA_END]!=expected:raise ValueError('Undeclared DMA-directory change')
    if event_acquisition and equipment_report:
        result=equipment.finish(result,base,output,equipment_report)
    if player_actions and equipment_report:
        result=equipment.finish(result,base,prior,output,equipment_report)
    if creature_fish and equipment_report:
        from v3_creature_ui import finish as finish_creature_text
        result=finish_creature_text(result,base,prior,output,equipment_report)
    installed=by_vrom(result)
    for vrom,data in owner_changes.items():
        target=next((r.get('target_vrom',vrom) for r in owner_moves if r['vrom']==vrom),vrom)
        if installed[target].extract(result)!=data:
            raise ValueError('Shared runtime loses a complete changed owner')
    # Superseded startup copies are reclaimed only in the newly built image.
    # The category planner verifies their live replacement; this writer checks
    # the exact original records again before making the space reusable.
    for retired in report_updates.get('retired_physical_resources',[]):
        old=next((r for r in prior.get('physical_resources',[]) if r['id']==retired['id']),None)
        first=retired['physical'];end=first+retired['bytes']
        if (old is None or any(old[k]!=retired[k] for k in ('physical','bytes','sha256')) or
                any(r['id']==retired['id'] for r in report_updates['physical_resources']) or
                sha256(result[first:end])!=retired['sha256'] or
                any(e.pstart<end and first<(e.pend or e.pstart+e.size)
                    for e in installed.values() if e.pstart!=0xFFFFFFFF)):
            raise ValueError('Changed obsolete physical packet before reuse')
        result[first:end]=bytes(retired['bytes'])
    for row,data in physical_writes:
        first=row['physical'];end=first+row['bytes']
        if 'previous_sha256' in row:
            old=next((r for r in prior.get('physical_resources',[]) if r['id']==row['id']),None)
            previous_first=row.get('previous_physical',first)
            previous_size=row.get('previous_bytes',row['bytes']);previous_end=previous_first+previous_size
            if (old is None or (old['physical'],old['bytes'],old['sha256'])!=
                    (previous_first,previous_size,row['previous_sha256']) or
                    not first<=previous_first<previous_end<=end or
                    sha256(result[previous_first:previous_end])!=row['previous_sha256'] or
                    any(result[first:previous_first]) or any(result[previous_end:end])):
                raise ValueError('Changed declared physical-resource predecessor')
        elif any(result[first:end]):raise ValueError('Physical resource write overlaps changed cartridge bytes')
        if len(data)!=row['bytes'] or sha256(data)!=row['sha256']:
            raise ValueError('Changed complete physical-resource replacement')
        result[first:end]=data
    if holiday_actor_services and equipment_report:
        from v3_holiday_dialogue import finish as finish_holiday_text
        result=finish_holiday_text(result,base,prior,output,equipment_report,
            physical_resources=report_updates.get('physical_resources',prior.get('physical_resources',[])))
    if creature_insects is not None:
        result=equipment.finish(result,base,prior,output,equipment_report,report_updates['physical_resources'])
    physical.verify(result,report_updates.get('physical_resources',prior.get('physical_resources',[])))
    fix_checksum(result);result=bytes(result)
    patch=make_ups(original,result)
    if apply_ups(original,patch)!=result: raise ValueError('Runtime patch reconstruction failed')
    report=copy.deepcopy(prior)
    report.update(report_updates)
    if resource_mode:
        report['automatic_furniture'].update(resource_moves=moved,resource_tail_padding=tail_padding)
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
    if furniture_capacity:
        report['automatic_furniture']['resource_moves']=moved
        report['import_storage']['remaining_bytes']=limit-BLOB-len(blob)
        report['shared_runtime_refresh'].update(adapters=['furniture_capacity'],
            resource_allocations_changed=True,resource_tail_reuse=reused,
            unchanged_owner_moves=moved,changed_owner_moves=owner_moves,
            in_place_owner_updates=owner_updates,
            additional_resident_bytes=report['furniture_capacity']['additional_resident_bytes'],
            additional_menu_bytes=report['furniture_capacity']['additional_pool_bytes'])
        report['sources'].update(report['furniture_capacity']['sources'])
        report['native_test']='pending enlarged room banks and catalogue model buffers'
        model_capacity.checked(result,report)
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
        report['shared_runtime_refresh'].update(adapters=['translation_dresser' if report['translation_updates'].get('dresser_menu') else 'translation_headers'],
            resource_allocations_changed=True,resource_tail_reuse=reused,
            unchanged_owner_moves=moved,changed_owner_moves=owner_moves,
            in_place_owner_updates=owner_updates,additional_resident_bytes=0)
        report['sources'].update(report['translation_updates']['sources'])
        report['native_test']=report['translation_updates']['native_test']+'; inherited gameplay limits retained'
    if furniture_scoring:
        report['automatic_furniture']['resource_moves']=moved
        report['import_storage']['remaining_bytes']=limit-BLOB-len(blob)
        report['shared_runtime_refresh'].update(adapters=['furniture_scoring'],
            resource_allocations_changed=True,resource_tail_reuse=reused,
            unchanged_owner_moves=moved,changed_owner_moves=owner_moves,
            in_place_owner_updates=owner_updates,additional_resident_bytes=0)
        report['sources'].update(report['furniture_scoring']['sources'])
        report['native_test']='pending expanded birth-point evaluator; acquisition remains incomplete'
    if room_surfaces_art is not None:
        report['automatic_furniture']['resource_moves']=moved
        report['import_storage']['remaining_bytes']=limit-BLOB-len(blob)
        report['shared_runtime_refresh'].update(adapters=['room_surfaces'],
            artwork_changed=not bool(prior.get('room_surfaces')),resource_allocations_changed=True,resource_tail_reuse=reused,
            unchanged_owner_moves=moved,changed_owner_moves=owner_moves,
            in_place_owner_updates=owner_updates,additional_resident_bytes=(surface_items or {}).get('additional_resident_bytes',0))
        report['sources'].update(report['room_surfaces']['sources'])
        report['native_test']='pending additive room/shop surface reader execution; actions, saves, and selection remain incomplete'
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
        if password_runtime is not None:
            report['shared_runtime_refresh'].update(adapters=['password_runtime'],
                additional_resident_bytes=equipment_report['passwords']['additional_resident_bytes'])
            report['sources'].update(equipment_report['passwords']['sources'])
            report['native_test']='pending linked password engine and lazy loader; Nook input/delivery remain incomplete'
        if room_effects is not None:
            effects=equipment_report['room_rigs']['effects']
            report['shared_runtime_refresh'].update(adapters=['room_effects'],artwork_changed=True,
                additional_scene_bytes=effects['additional_scene_bytes'])
            report['sources'].update(effects['sources'])
            report['native_test']='pending focused integration of the changed native effects'
        if surface_items and room_surfaces_art is not None:
            report['shared_runtime_refresh'].update(adapters=['room_surfaces','surface_items'],
                additional_resident_bytes=surface_items['additional_resident_bytes'])
        if player_motion:
            report['shared_runtime_refresh']['adapters'].append('player_motion')
        if equipment_kinds:
            report['shared_runtime_refresh']['adapters'].append('equipment_kinds')
        if equipment_rigs is not None:
            report['shared_runtime_refresh']['adapters'].append('equipment_rigs')
            report['shared_runtime_refresh']['artwork_changed']=True
        if player_actions:
            report['shared_runtime_refresh']['adapters'].append('player_actions')
            exercise=equipment_report['player_motion'].get('exercise')
            if exercise and not prior['equipment_resources']['player_motion'].get('exercise'):
                report['shared_runtime_refresh'].update(artwork_changed=True,resource_allocations_changed=True,
                    additional_scene_resident_bytes=equipment_report['player_motion']['allocation']['additional_scene_bytes'])
            if exercise and exercise.get('action_installed') and not prior['equipment_resources']['player_motion'].get('exercise',{}).get('action_installed'):
                report['shared_runtime_refresh'].update(resource_allocations_changed=True,
                    additional_scene_resident_bytes=exercise['native']['additional_scene_bytes'],
                    additional_resident_bytes=exercise['native']['packet']['bytes'])
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
        if room_rigs_code:
            report['shared_runtime_refresh']['adapters']=['room_rigs_code']
            report['sources'].update({name:sha256((ROOT/name).read_bytes()) for name in equipment.SOURCES})
        if room_goods is not None:
            report['shared_runtime_refresh']['adapters'].append('room_goods')
            report['shared_runtime_refresh']['additional_resident_bytes']+=equipment.CODE_END-equipment.CODE_RAM+equipment.STATE_BYTES
            report['sources'].update({name:sha256((ROOT/name).read_bytes()) for name in equipment.SOURCES})
        if room_carry is not None:
            report['shared_runtime_refresh']['adapters'].append('room_carry')
            report['shared_runtime_refresh']['additional_resident_bytes']+=equipment.CODE_END-equipment.CODE_RAM+equipment.STATE_BYTES
        if furniture_audio_art is not None:
            audio_format=json.loads((furniture_audio_art/'audio.json').read_bytes()).get('format')
            kind={'AFV3-FURNITURE-MELODY-PREPARED-1':'furniture_melody_audio',
                  'AFV3-FURNITURE-LEVEL-AUDIO-PREPARED-1':'furniture_level_audio'}.get(audio_format,'furniture_audio')
            report['shared_runtime_refresh']['adapters'].append(kind)
            report['shared_runtime_refresh']['additional_resident_bytes']=equipment_report[kind]['audio_heap_growth']
        if furniture_profiles is not None:
            report['shared_runtime_refresh']['adapters'].append('inactive_furniture_profiles')
            report['shared_runtime_refresh']['artwork_changed']=True
        reaction=equipment_report.get('room_rigs',{}).get('reactions')
        if reaction and not prior.get('equipment_resources',{}).get('room_rigs',{}).get('reactions'):
            report['shared_runtime_refresh']['adapters'].append('timed_material_reactions')
            report['shared_runtime_refresh']['additional_resident_bytes']+=reaction['state']['bytes']
        colour=equipment_report.get('room_rigs',{}).get('colours')
        if colour and not prior.get('equipment_resources',{}).get('room_rigs',{}).get('colours'):
            report['shared_runtime_refresh']['adapters'].append('player_colour_materials')
            report['shared_runtime_refresh']['additional_resident_bytes']+=colour['state']['bytes']
        if material_frames_art is not None:
            report['shared_runtime_refresh']['adapters'].append('material_frames')
            report['shared_runtime_refresh']['artwork_changed']=True
        if scrolling_materials_art is not None:
            report['shared_runtime_refresh']['adapters'].append('scrolling_materials')
            report['shared_runtime_refresh']['artwork_changed']=True
            report['shared_runtime_refresh']['additional_resident_bytes']=equipment_report['additional_resident_bytes']
        if held_selection:
            report['shared_runtime_refresh']['adapters'].append('held_selection')
        if report['save_runtime']['profile_hex']!=prior['save_runtime']['profile_hex']:
            report['shared_runtime_refresh']['saved_profile_changed']=True
        report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in equipment.SOURCES})
        if equipment_report.get('parent_readers'):
            report['sources']['translations/provenance.json']=sha256((ROOT/'translations/provenance.json').read_bytes())
        report['native_test']='pending shared equipment resource DMA/readers'
        if creature_items is not None:
            report['shared_runtime_refresh'].update(adapters=['creature_items'],artwork_changed=True,
                additional_resident_bytes=equipment_report['creature_items']['additional_resident_bytes'])
            report['native_test']='pending connected creature parent/room execution; catching, release, collection, and selection remain incomplete'
        if material_frames_art is not None:
            report['native_test']='pending material-frame renderer native execution and GPU appearance; lifecycle/acquisition remain incomplete'
        if scrolling_materials_art is not None:
            report['native_test']='pending scrolling renderer native execution and GPU appearance; lifecycle/acquisition remain incomplete'
        if surface_items and room_surfaces_art is not None:
            report['native_test']='pending shared surface item startup/name/type/price execution; application, saves, and selection remain incomplete'
            if report['room_surfaces'].get('application'):
                report['shared_runtime_refresh']['adapters'].append('surface_application')
                report['native_test']='pending shared surface reservation/application and full floor identity; profile, catalogue, acquisition, and ordinary persistence remain incomplete'
            if report['room_surfaces'].get('save'):
                report['shared_runtime_refresh']['adapters'].append('surface_save')
                report['shared_runtime_refresh'].update(saved_format_changed=not bool(prior.get('room_surfaces',{}).get('save')),
                    additional_save_state_bytes=report['save_runtime']['state_bytes']-prior['save_runtime']['state_bytes'])
                report['native_test']='pending format-4 surface codec/runtime and collection; inventory/catalogue pages, acquisition, and ordinary persistence remain incomplete'
            if report['room_surfaces'].get('menu'):
                report['shared_runtime_refresh']['adapters'].append('surface_menu')
                report['native_test']='pending shared surface catalogue execution; inventory verification, acquisition, sound/scoring, and private selection remain incomplete'
            if report['room_surfaces'].get('scoring'):
                report['shared_runtime_refresh']['adapters'].append('surface_scoring')
                report['native_test']='pending full-index surface scoring and matching themes; acquisition, sound, and private selection remain incomplete'
            if report['room_surfaces'].get('sound'):
                report['shared_runtime_refresh']['adapters'].append('surface_sound')
                report['shared_runtime_refresh']['additional_resident_bytes']=(0 if prior.get('room_surfaces',{}).get('sound')
                    else report['room_surfaces']['sound']['audio_heap_growth'])
                report['native_test']='pending full-index surface sound dispatch; acquisition, full remaining themes, and private selection remain incomplete'
            if report['room_surfaces'].get('stock'):
                report['shared_runtime_refresh']['adapters'].append('surface_stock')
                report['native_test']='pending selected-only surface stock execution; HomePage/Harvest acquisition, full remaining themes, and private selection remain incomplete'
            if report['room_surfaces'].get('optional_selection'):
                report['shared_runtime_refresh']['adapters'].append('surface_selection')
                report['native_test']='pending private surface composition/startup; ordinary gameplay/persistence and HomePage/Harvest categories remain incomplete'
    if console_storage:
        storage=equipment_report['console_storage']
        report['shared_runtime_refresh'].update(adapters=['console_storage'],saved_format_changed=True,
            additional_save_state_bytes=storage['state']['bytes'],
            additional_resident_bytes=storage['packet']['bytes'],
            additional_scratch_bytes=storage['scratch']['bytes']+storage['hash']['bytes']+32)
        report['sources'].update(storage['sources'])
        report['native_test']='pending format-five native storage execution and fresh save/reload; console launch remains uninstalled'
    if creature_field is not None:
        field=equipment_report['creature_field']
        report['shared_runtime_refresh'].update(adapters=['creature_field'],artwork_changed=True,
            additional_resident_bytes=field['additional_resident_bytes'],additional_scene_bytes=0,
            resource_allocations_changed=True)
    if creature_fish:
        report['shared_runtime_refresh'].update(adapters=['creature_fish'],artwork_changed=False,
            additional_resident_bytes=equipment_report['creature_fish']['additional_resident_bytes'],
            additional_scene_bytes=0,resource_allocations_changed=bool(equipment_report['creature_fish'].get('world')))
        report['shared_runtime_refresh']['saved_profile_changed']=report['save_runtime']['profile_hex']!=prior['save_runtime']['profile_hex']
        report['sources'].update(equipment_report['creature_fish']['sources'])
        if report_updates.get('saved_format_changed'):
            report['shared_runtime_refresh'].update(saved_format_changed=True,
                additional_save_state_bytes=report['save_runtime']['state_bytes']-prior['save_runtime']['state_bytes'])
    if creature_insects is not None:
        insects=equipment_report['creature_insects']
        report['shared_runtime_refresh'].update(adapters=['creature_insects'],artwork_changed=True,
            additional_resident_bytes=insects['additional_resident_bytes'],
            additional_scene_bytes=insects['additional_scene_bytes'],resource_allocations_changed=True,
            saved_format_changed=True,
            saved_profile_changed=report['save_runtime']['profile_hex']!=prior['save_runtime']['profile_hex'])
        report['sources'].update(insects['sources'])
        report['native_test']='pending connected insect gameplay/save verification; fish constructor and sound-scheduler failures remain unresolved'
    if clothing_batch is not None:
        clothing=equipment_report['clothing_batch']
        report['shared_runtime_refresh'].update(adapters=['clothing_batch'],artwork_changed=True,
            additional_resident_bytes=clothing['additional_resident_bytes'],
            additional_scene_bytes=0,resource_allocations_changed=True,saved_format_changed=False,
            additional_menu_pool_bytes=report['catalogue']['category_pool_bytes']-prior['catalogue'].get('category_pool_bytes',0),
            saved_profile_changed=report['save_runtime']['profile_hex']!=prior['save_runtime']['profile_hex'])
        report['sources'].update(clothing['sources'])
        report['native_test']='pending connected clothing gameplay/save verification; retained creature failures remain unresolved'
    if diaries is not None:
        diary=equipment_report['diaries']
        report['shared_runtime_refresh'].update(adapters=['diaries'],artwork_changed=True,
            additional_resident_bytes=diary['additional_resident_bytes'],
            additional_menu_pool_bytes=diary['hooks']['additional_pool_bytes'],
            resource_allocations_changed=True,saved_format_changed=True,saved_profile_changed=False,
            changed_owner_moves=owner_moves)
        report['sources'].update(diary['sources'])
        report['native_test']='pending connected diary UI/save verification; carried readers and selection remain unfinished'
    if diary_items:
        diary=equipment_report['diary_items']
        report['shared_runtime_refresh'].update(adapters=['diary_items'],artwork_changed=True,
            additional_resident_bytes=diary['additional_resident_bytes'],saved_format_changed=False)
        report['sources'].update(diary['sources'])
        report['native_test']='pending connected diary gameplay; room artwork, catalogue, participation, and selection remain unfinished'
    if diary_room_art is not None:
        diary=equipment_report['diary_items']
        report['shared_runtime_refresh'].update(adapters=['diary_room_art'],artwork_changed=True,
            additional_resident_bytes=0,additional_owner_bytes=diary['room_art']['bytes']-diary['room_art']['previous_bytes']-16)
        report['sources'].update(diary['sources'])
        report['native_test']='pending connected diary gameplay; catalogue/scoring, participation, and selection remain unfinished'
    if diary_catalogue:
        diary=equipment_report['diary_items']
        report['shared_runtime_refresh'].update(adapters=['diary_catalogue'],artwork_changed=False,
            additional_resident_bytes=0,additional_menu_pool_bytes=
                report['catalogue']['category_pool_bytes']-prior['catalogue'].get('category_pool_bytes',0))
        report['sources'].update(diary['sources'])
        report['native_test']='pending diary participation, selection, and connected gameplay/save verification'
    if npc_registry_art is not None:
        npc=equipment_report['npc_extra']
        report['shared_runtime_refresh'].update(adapters=['npc_registry'],artwork_changed=True,
            additional_resident_bytes=(npc.get('events',{}).get('sky',{}).get('packet',{}).get('bytes',0)-
                prior['equipment_resources']['npc_extra'].get('events',{}).get('sky',{}).get('packet',{}).get('bytes',0)
                if prior['equipment_resources'].get('npc_extra') else npc['packet']['bytes']),resource_allocations_changed=True,
            saved_format_changed=False,saved_profile_changed=False)
        report['sources'].update(npc['sources'])
        report['native_test']='pending connected Tortimer event/conversation/animation providers and diary gameplay/save verification'
    if carried_items is not None:
        carried=equipment_report['carried_items']
        report['shared_runtime_refresh'].update(adapters=['carried_items'],artwork_changed=True,
            additional_resident_bytes=carried['additional_resident_bytes'],resource_allocations_changed=True,
            saved_format_changed=False,saved_profile_changed=False,changed_owner_moves=owner_moves)
        report['sources'].update(carried['sources'])
        report['native_test']='pending connected carried-item menus, behaviours, persistence, and selection; readiness remains off'
    if holiday_actor_services:
        npc=equipment_report['npc_extra']
        decorations=npc['events'].get('decorations') and not prior['equipment_resources']['npc_extra']['events'].get('decorations')
        holiday_state=equipment_report.get('holiday_state')
        new_state=holiday_state and not prior['equipment_resources'].get('holiday_state')
        state_growth=(holiday_state['packet']['bytes']-
            prior['equipment_resources'].get('holiday_state',{}).get('packet',{}).get('bytes',0)) if holiday_state else 0
        event_items=equipment_report.get('holiday_items') and not prior['equipment_resources'].get('holiday_items')
        fishing=equipment_report.get('holiday_fishing') and not prior['equipment_resources'].get('holiday_fishing')
        sky=npc['events'].get('sky') and not prior['equipment_resources']['npc_extra']['events'].get('sky')
        participants=npc['events'].get('participants') and not prior['equipment_resources']['npc_extra']['events'].get('participants')
        exercise=npc['events'].get('exercise') and not prior['equipment_resources']['npc_extra']['events'].get('exercise')
        festivals=(npc['events'].get('festivals')
            if not prior['equipment_resources']['npc_extra']['events'].get('festivals') else None)
        item_controls=(equipment_report.get('holiday_items',{}).get('controls')
            if not prior['equipment_resources'].get('holiday_items',{}).get('controls') else None)
        report['shared_runtime_refresh'].update(adapters=['holiday_actor_services'],artwork_changed=bool(decorations or event_items or sky or participants or exercise),
            additional_resident_bytes=state_growth+(176 if fishing else 0)+(npc['events']['sky']['additional_resident_bytes'] if sky else 0)+(npc['events']['participants']['additional_resident_bytes'] if participants else 0)+(npc['events']['exercise']['additional_resident_bytes'] if exercise else 0),
            resource_allocations_changed=bool(new_state or fishing or npc['events'].get('reserved')),
            saved_format_changed=bool(new_state or fishing or exercise),saved_profile_changed=False)
        if npc['events'].get('selection') and not prior['equipment_resources']['npc_extra']['events'].get('selection'):
            report['shared_runtime_refresh']['saved_profile_changed']=True
        report['sources'].update(npc['sources'])
        report['native_test']=('pending dedicated/costume/exercise owners, calendar behaviour choice, actor activation, '
            'and connected diary gameplay/save verification' if holiday_state else
            'pending native calendar caller, dedicated/costume/exercise owners, actor activation, '
            'and connected diary gameplay/save verification')
        if exercise:
            report['native_test']='pending calendar behaviour choice/admission and connected diary/exercise gameplay/save verification'
        if festivals:
            report['shared_runtime_refresh']['additional_resident_bytes']+=festivals['additional_resident_bytes']
            report['shared_runtime_refresh']['resource_allocations_changed']=True
            report['shared_runtime_refresh']['artwork_changed']=True
            report['native_test']='pending complete actor/service admission, diary selection, and connected festival/diary gameplay/save verification'
        if item_controls:
            report['shared_runtime_refresh']['additional_resident_bytes']+=item_controls['additional_resident_bytes']
            report['shared_runtime_refresh']['resource_allocations_changed']=True
            report['shared_runtime_refresh']['saved_format_changed']=True
            report['native_test']='pending calendar choice/admission and connected diary/event gameplay/save verification'
        calendar=npc['events'].get('calendar')
        if calendar and not prior['equipment_resources']['npc_extra']['events'].get('calendar'):
            report['shared_runtime_refresh']['additional_resident_bytes']+=calendar['additional_resident_bytes']
            report['shared_runtime_refresh']['resource_allocations_changed']=True
            report['native_test']='pending complete actor/service and choice admission, diary selection, and connected gameplay/save verification'
        optional=npc.get('optional_dialogue')
        if optional and not prior['equipment_resources']['npc_extra'].get('optional_dialogue'):
            report['shared_runtime_refresh']['additional_resident_bytes']+=optional['additional_resident_bytes']
            report['shared_runtime_refresh']['resource_allocations_changed']=True
            report['native_test']='pending event/service activation, diary selection, and connected native gameplay/save verification'
        if npc['events'].get('selection'):
            report['native_test']='pending native diary UI/save and activated festival gameplay verification'
    if console_images is not None:
        images=equipment_report['console_images']
        report['shared_runtime_refresh'].update(adapters=['console_images'],
            additional_resident_bytes=images['packet']['bytes'],
            physical_resource_bytes=images['pool']['bytes'])
        report['sources'].update(images['sources'])
        report['native_test']='pending native streamed game reads; room launch, graphics, persistence hooks, and QD remain incomplete'
    if console_emulator:
        stage=equipment_report['console_images']['emulator']
        report['shared_runtime_refresh'].update(adapters=['console_emulator'],additional_resident_bytes=stage['state']['bytes'])
        report['sources'].update(stage['sources'])
        report['native_test']='pending installed console lifecycle execution; room furniture launch and QD remain incomplete'
    if console_disk is not None:
        stage=equipment_report['console_disk']
        report['shared_runtime_refresh'].update(adapters=['console_disk'],
            additional_resident_bytes=stage['packet']['bytes'],saved_format_changed=False)
        report['sources'].update(stage['sources'])
        report['native_test']='pending native disk preload; session hooks and disk gameplay remain incomplete'
    if room_goods is not None:
        report['native_test']='pending loose-item bridge execution; moving-table owner hooks remain uninstalled'
    if room_carry is not None:
        report['native_test']='pending installed carrying hooks, occupied-table gameplay, scene transitions, and GPU appearance'
    if password_runtime is not None:
        report['native_test']='pending linked password engine and lazy loader; Nook input/delivery remain incomplete'
    if password_editor:
        report['shared_runtime_refresh'].update(adapters=['password_editor'],
            additional_menu_pool_bytes=report['password_editor']['additional_menu_pool_bytes'],
            resource_allocations_changed=True,changed_owner_moves=owner_moves)
        report['sources'].update(report['password_editor']['sources'])
        report['native_test']='pending two-row code-entry UI; Nook conversation and gift delivery remain incomplete'
    if report.get('resource_capacity'):
        report['resource_capacity']['resources']=capacity.text_records(result,report)
        capacity.checked_limit(result,report)
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
    parser.add_argument('--holiday-participants',type=Path,
        help='Install a checked complete participant preparation with --holiday-actor-services')
    parser.add_argument('--clothing-batch',type=Path,
        help='With --refresh-runtime, install the complete prepared clothing category')
    parser.add_argument('--carried-items',type=Path,
        help='With --refresh-runtime, connect the prepared shared carried-item resources and readers')
    parser.add_argument('--diary-core',type=Path,help='Prepared shared diary save/controller directory')
    parser.add_argument('--diary-ui',type=Path,help='Prepared diary native UI and menu hooks directory')
    parser.add_argument('--diary-screen',type=Path,help='Prepared complete diary screen artwork directory')
    parser.add_argument('--diary-items',action='store_true',help='Install all shared carried diary readers and artwork')
    parser.add_argument('--diary-room-art',type=Path,help='Install all prepared diary covers in room and preview contexts')
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
    parser.add_argument('--room-rigs-code',action='store_true',
        help='With --refresh-runtime, rebuild shared room code and callback bindings while preserving all assets and selections')
    parser.add_argument('--room-goods',type=Path,
        help='With --refresh-runtime, install prepared loose-item rotation and native drawing hooks')
    parser.add_argument('--room-carry',type=Path,
        help='With --refresh-runtime, install prepared moving-table registration, transform, drawing, and release hooks')
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
    parser.add_argument('--scrolling-materials-art',type=Path,action='append',
        help='With --refresh-runtime, install shared scrolling-material rendering without enabling unfinished items')
    parser.add_argument('--room-surfaces-art',type=Path,
        help='With --refresh-runtime, install prepared floor/wall artwork and shared room readers without enabling items')
    parser.add_argument('--furniture-scoring',action='store_true',
        help='With --refresh-runtime, install complete donor themes, names, and source-mapped base-point categories')
    parser.add_argument('--diary-catalogue',action='store_true',
        help='With --refresh-runtime, connect all installed diary covers to catalogue previews and scoring metadata')
    parser.add_argument('--npc-registry-art',type=Path,
        help='With --refresh-runtime, connect complete prepared additional-NPC art, allocation, and rendering; actors remain inactive')
    parser.add_argument('--holiday-actor-services',action='store_true',
        help='With --refresh-runtime, connect shared holiday actor services to the installed additional-NPC registry')
    parser.add_argument('--password-runtime',type=Path,
        help='With --refresh-runtime, link prepared password rules and live engine bindings without enabling delivery')
    parser.add_argument('--password-editor',action='store_true',
        help='With --refresh-runtime, install two-row code entry without enabling Nook delivery')
    parser.add_argument('--room-effects',type=Path,
        help='With --refresh-runtime, install prepared shared effects through the native controller')
    parser.add_argument('--furniture-capacity',action='store_true',
        help='With --refresh-runtime, extend complete room and catalogue model buffers')
    parser.add_argument('--console-storage',action='store_true',
        help='With --refresh-runtime, install complete format-five console save storage')
    parser.add_argument('--console-images',type=Path,
        help='With --refresh-runtime, install the complete prepared console game pool and bounded native reader')
    parser.add_argument('--console-emulator',action='store_true',
        help='With --refresh-runtime, connect the native full-image iNES lifecycle and save hooks')
    parser.add_argument('--creature-items',type=Path,
        help='With --refresh-runtime, connect the complete prepared creature parent/room category')
    parser.add_argument('--creature-fish',action='store_true',help='Install shared fish world behaviours')
    parser.add_argument('--creature-insects',type=Path,help='Install the complete prepared insect runtime and resources together')
    parser.add_argument('--creature-field',type=Path,
        help='With --refresh-runtime, install the complete field frames and capture/release tables')
    parser.add_argument('--console-disk',type=Path,
        help='With --refresh-runtime, preload the prepared shared disk engine without enabling unfinished games')
    args=parser.parse_args()
    diary_paths=(args.diary_core,args.diary_ui,args.diary_screen)
    if any(diary_paths) and (not all(diary_paths) or not args.refresh_runtime):
        parser.error('Diary installation requires --refresh-runtime and all three --diary-* directories')
    if args.diary_items and not args.refresh_runtime:
        parser.error('--diary-items requires --refresh-runtime')
    if args.diary_room_art is not None and not args.refresh_runtime:
        parser.error('--diary-room-art requires --refresh-runtime')
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
    if args.room_rigs_code and not args.refresh_runtime:parser.error('--room-rigs-code requires --refresh-runtime')
    if args.room_goods and not args.refresh_runtime:parser.error('--room-goods requires --refresh-runtime')
    if args.room_carry and not args.refresh_runtime:parser.error('--room-carry requires --refresh-runtime')
    if args.translation_updates and not args.refresh_runtime:parser.error('--translation-updates requires --refresh-runtime')
    if args.expand_storage and not args.refresh_runtime:parser.error('--expand-storage requires --refresh-runtime')
    if args.furniture_audio_art and not args.refresh_runtime:parser.error('--furniture-audio-art requires --refresh-runtime')
    if args.furniture_profiles and not args.refresh_runtime:parser.error('--furniture-profiles requires --refresh-runtime')
    if args.material_frames_art and not args.refresh_runtime:parser.error('--material-frames-art requires --refresh-runtime')
    if args.scrolling_materials_art and not args.refresh_runtime:parser.error('--scrolling-materials-art requires --refresh-runtime')
    if args.room_surfaces_art and not args.refresh_runtime:parser.error('--room-surfaces-art requires --refresh-runtime')
    if args.furniture_scoring and not args.refresh_runtime:parser.error('--furniture-scoring requires --refresh-runtime')
    if args.diary_catalogue and not args.refresh_runtime:parser.error('--diary-catalogue requires --refresh-runtime')
    if args.npc_registry_art is not None and not args.refresh_runtime:parser.error('--npc-registry-art requires --refresh-runtime')
    if args.holiday_actor_services and not args.refresh_runtime:parser.error('--holiday-actor-services requires --refresh-runtime')
    if args.holiday_participants is not None and not args.holiday_actor_services:
        parser.error('--holiday-participants requires --holiday-actor-services')
    if args.password_runtime and not args.refresh_runtime:parser.error('--password-runtime requires --refresh-runtime')
    if args.password_editor and not args.refresh_runtime:parser.error('--password-editor requires --refresh-runtime')
    if args.room_effects and not args.refresh_runtime:parser.error('--room-effects requires --refresh-runtime')
    if args.furniture_capacity and not args.refresh_runtime:parser.error('--furniture-capacity requires --refresh-runtime')
    if args.console_storage and not args.refresh_runtime:parser.error('--console-storage requires --refresh-runtime')
    if args.console_images is not None and not args.refresh_runtime:parser.error('--console-images requires --refresh-runtime')
    if args.console_emulator and not args.refresh_runtime:parser.error('--console-emulator requires --refresh-runtime')
    if args.console_disk is not None and not args.refresh_runtime:parser.error('--console-disk requires --refresh-runtime')
    if args.creature_items is not None and not args.refresh_runtime:parser.error('--creature-items requires --refresh-runtime')
    if args.creature_field is not None and not args.refresh_runtime:parser.error('--creature-field requires --refresh-runtime')
    if args.creature_fish and not args.refresh_runtime:parser.error('--creature-fish requires --refresh-runtime')
    if args.creature_insects is not None and not args.refresh_runtime:parser.error('--creature-insects requires --refresh-runtime')
    if args.clothing_batch is not None and not args.refresh_runtime:parser.error('--clothing-batch requires --refresh-runtime')
    if args.carried_items is not None and not args.refresh_runtime:parser.error('--carried-items requires --refresh-runtime')
    result=(refresh_runtime(args.output,args.base_lock,equipment_art=args.equipment_art,player_motion=args.player_motion,
                            equipment_kinds=args.equipment_kinds,player_actions=args.player_actions,
                            item_category_art=args.item_category_art,ground_categories=args.ground_categories,
                            event_acquisition=args.event_acquisition,held_collection=args.held_collection,
                            held_catalogue_art=args.held_catalogue_art,held_selection=args.held_selection,
                            translation_updates=args.translation_updates,equipment_rigs=args.equipment_rigs,
                            room_rigs_art=args.room_rigs_art,room_rigs_code=args.room_rigs_code,room_goods=args.room_goods,room_carry=args.room_carry,scenery_art=args.scenery_art,scenery_gameplay=args.scenery_gameplay,
                            expand_storage=args.expand_storage,furniture_audio_art=args.furniture_audio_art,
                            furniture_profiles=args.furniture_profiles,material_frames_art=args.material_frames_art,
                            scrolling_materials_art=args.scrolling_materials_art,room_surfaces_art=args.room_surfaces_art,
                            furniture_scoring=args.furniture_scoring,password_runtime=args.password_runtime,
                            password_editor=args.password_editor,room_effects=args.room_effects,
                            furniture_capacity=args.furniture_capacity,console_storage=args.console_storage,
                            console_images=args.console_images,console_emulator=args.console_emulator,
                            console_disk=args.console_disk,creature_items=args.creature_items,creature_field=args.creature_field,
                            creature_fish=args.creature_fish,creature_insects=args.creature_insects,clothing_batch=args.clothing_batch,
                            diaries=dict(zip(('core','ui','screen'),diary_paths)) if all(diary_paths) else None,
                            diary_items=args.diary_items,diary_room_art=args.diary_room_art,diary_catalogue=args.diary_catalogue,
                            npc_registry_art=args.npc_registry_art,holiday_actor_services=args.holiday_actor_services,
                            holiday_participants=args.holiday_participants,carried_items=args.carried_items)
            if args.refresh_runtime else build(args.output,args.art,args.base_lock))
    print(json.dumps({k:result[k] for k in ('runtime_abi','output_sha256','patch_sha256')},indent=2))
