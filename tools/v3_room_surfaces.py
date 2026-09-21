"""Bulk room-surface conversion with additive identities and source metadata.

Complete shared surfaces are mapped by rendered pixels, not equal indices.
Preparation keeps runtime, acquisition, and persistence requirements explicit.
"""
import json
from pathlib import Path
import re
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from apply_translation import write_new
from item_identity_sheet import SHEET_SHA, sheet_rows
from v3_asset_loader import ROOT
from v3_registry import SURFACE_REGISTRY_VERSION, SURFACES, surface_identity
from v3_villager_art import native_palette, pack4, untile
from v3_villager_houses import surface_pixels

VERSION = 1
KINDS = (
    dict(kind='floor', prefix='carpet', base=0x2600, stride=0x2020, tiles=4, vrom=0x17A1000,
        source_sha256='2d3eda53f23337b06e17e37179d4934514354bd348e978c6cc61ab5802a57301',
        native_sha256='95ebd4471652f879192e917ea9a0938e9026918459d2ddb8408956f673427419'),
    dict(kind='wall', prefix='wall', base=0x2700, stride=0x1020, tiles=2, vrom=0x182A000,
        source_sha256='2ed5e747a35ceeacbf1eff9f4655afe0ad4ae95c4b466759f09bb116d9c9037c',
        native_sha256='f91961e5ed58dc4542f3ad1c05f9776fba1d57f5f00d9ee1d5bf0cc2671aee5a'),
)
SOURCES = ('tools/v3_room_surfaces.py', 'tools/v3_registry.py', 'tools/v3_furniture_pipeline.py',
    'tools/v3_furniture_install.py','tools/title_assets.py','tools/v3_villager_audio.py',
    'tools/v3_villager_art.py', 'tools/v3_villager_houses.py', 'tools/item_identity_sheet.py')


def floor_sound_inputs(image):
    """Retain actual selector data; equal selectors do not certify full sounds."""
    from v3_villager_audio import read_audio_donor, DOL_SHA
    dol,_ = read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    donor = dol.read(0x800A9938,95*2)
    core = by_vrom(image)[CODE_VROM].extract(image)
    start = 0x80113A64-CODE_RAM
    native = core[start:start+73*2]
    if (sha256(donor)!='104e7f8b0fac4806301b2366491aefc715f6d6ecf39d731a7a8ae1d98c38f8ef' or
            sha256(native)!='4b0c696020afdc533cfb4a6b3e799b5f297900fbc4f979e1e59671d69410b6be'):
        raise ValueError('Changed complete source/native floor sound selectors')
    return dict(source_dol_sha256=DOL_SHA,source_address=0x800A9938,source_sha256=sha256(donor),
        source_selectors=list(struct.unpack('>95H',donor)),native_address=0x80113A64,
        native_sha256=sha256(native),native_selectors=list(struct.unpack('>73H',native)),
        native_reserved_count=73,complete_sound_equivalence_verified=False)


def convert_record(raw, tiles):
    if tiles not in (2, 4) or len(raw) != 32+tiles*0x800:
        raise ValueError('Incomplete room-surface palette or 64x64 tile set')
    return native_palette(raw[:32])+b''.join(
        pack4(untile(raw[at:at+0x800], 64, 64, 4)) for at in range(32, len(raw), 0x800))


def pixel_digest(raw):
    pixels = surface_pixels(raw)
    return sha256(struct.pack('>'+str(len(pixels))+'H', *pixels))


def source_metadata(source, kind):
    prefix, base = kind['prefix'], kind['base']
    names = source.raw('itemName_'+prefix)
    prices = source.raw(prefix+'_price_table')
    order = source.raw('mCL_'+prefix+'_idx_list')
    if len(names) != 67*16 or len(prices) != 68*2 or prices[-2:] != b'\xff\xff' or len(order) != 67*2:
        raise ValueError('Changed complete room-surface names, prices, or catalogue order')
    order = list(struct.unpack('>67H', order))
    if sorted(order) != list(range(67)):
        raise ValueError('Surface catalogue order is not a complete permutation')
    table_name = 'mSP_'+prefix+'_list'
    start, size = source.symbol(table_name)
    if size != 23*4 or any(source.raw(table_name)):
        raise ValueError('Changed complete surface acquisition pointer table')
    pointers = source.pointers(start, size)
    lists = []
    membership = {base+i: [] for i in range(67)}
    for location, target in sorted(pointers.items()):
        symbol, at, size = source.containing(target, exact=True)
        if not re.fullmatch(prefix+r'_list[A-Za-z0-9]+', symbol) or size%2:
            raise ValueError('Unknown surface acquisition-list dependency')
        raw = source.raw(symbol)
        items = list(struct.unpack('>'+str(size//2)+'H', raw))
        if not items or items[-1] != 0 or any(item not in membership for item in items[:-1]):
            raise ValueError('Unterminated or out-of-range surface acquisition list')
        if len(set(items[:-1])) != len(items)-1:
            raise ValueError('Duplicate surface acquisition identity')
        record = dict(symbol=symbol, section_offset=at, bytes=size, sha256=sha256(raw),
            table_index=(location-start)//4, items=[f'{item:04X}' for item in items[:-1]])
        lists.append(record)
        for item in items[:-1]:
            membership[item].append(dict(symbol=symbol, table_index=record['table_index']))
    expected = {name for name in source.names if re.fullmatch(prefix+r'_list[A-Za-z0-9]+', name)}
    if {row['symbol'] for row in lists} != expected or any(len(rows)!=1 for rows in membership.values()):
        raise ValueError('Surface acquisition table does not cover each donor identity exactly once')
    return names, prices, order, membership, dict(
        name_symbol='itemName_'+prefix, names_sha256=sha256(names),
        price_symbol=prefix+'_price_table', prices_sha256=sha256(prices),
        catalogue_symbol='mCL_'+prefix+'_idx_list', catalogue_order=order,
        acquisition_table_symbol=table_name, acquisition_lists=lists)


def discover(source, image):
    worksheet = ROOT/'build/item-identity-megasheet.xlsx'
    if sha256(worksheet.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed room-surface identity worksheet')
    evidence = {}
    for number, row in sheet_rows(worksheet, 'Items'):
        if re.fullmatch(r'2[67][0-9A-F]{2}', row.get('E', '')):
            evidence.setdefault(int(row['E'], 16), []).append((number, row))
    files = by_vrom(image)
    sounds = floor_sound_inputs(image)
    rows, banks, assets = [], [], {}
    reserved = set()
    for kind in KINDS:
        stride, base = kind['stride'], kind['base']
        member = f'data/player_room_{kind["kind"]}.bin'
        raw = (ROOT/'build/gamecube/files/forest_2nd.arc.unpacked'/member).read_bytes()
        native = files[kind['vrom']].extract(image)
        if (len(raw) != 71*stride or sha256(raw) != kind['source_sha256'] or
                len(native) != 68*stride or sha256(native) != kind['native_sha256']):
            raise ValueError('Changed complete source/native room-surface bank')
        names, prices, order, membership, metadata = source_metadata(source, kind)
        index = {}
        for i in range(68):
            record = native[i*stride:(i+1)*stride]
            index.setdefault(pixel_digest(record), []).append(dict(index=i, sha256=sha256(record)))
        shops = []
        for i in range(71):
            original = raw[i*stride:(i+1)*stride]
            converted = convert_record(original, kind['tiles'])
            digest = pixel_digest(converted)
            matches = index.get(digest, [])
            if i >= 67:
                if len(matches) != 1 or matches[0]['index'] != i-3:
                    raise ValueError('Changed complete non-item shop surface mapping')
                shops.append(dict(source_index=i, native_index=i-3, pixels_sha256=digest))
                continue
            item = base+i
            name_raw = names[i*16:(i+1)*16]
            try:
                name = name_raw.decode('ascii').rstrip(' ')
            except UnicodeDecodeError:
                raise ValueError('Surface name requires an explicit encoding adapter') from None
            if not name or name.lower() == 'dummy' or any(ord(c)<32 for c in name):
                raise ValueError('Unused or malformed source surface name')
            status = 'existing-native-artwork' if len(matches)==1 else (
                'ambiguous-native-artwork' if matches else 'requires-additive-import')
            target, destination, identity = None, None, None
            if not matches:
                candidates = evidence.get(item, [])
                if (len(candidates)!=1 or candidates[0][1].get('C')!='-' or
                        candidates[0][1].get('J')!=name):
                    raise ValueError('Unmatched surface needs explicit additive identity evidence')
                number, fields = candidates[0]
                identity = dict(worksheet_sha256=SHEET_SHA, row=number,
                    native_id=fields['C'], donor_id=fields['E'], name=fields['J'])
                target, destination = surface_identity(item)
                if target < sounds['native_reserved_count'] or target >= 128 or destination != base+target or destination in reserved:
                    raise ValueError('Surface destination overlaps native/special or reserved identities')
                reserved.add(destination)
                assets[f'{item:04X}'] = converted
            elif item in SURFACES:
                raise ValueError('Reserved additive surface unexpectedly matches original artwork')
            rows.append(dict(id=f'GAFE01-r0/item/{item:04X}', source_item_id=f'{item:04X}',
                kind=kind['kind'], source_index=i, destination_index=target,
                destination_item_id=f'{destination:04X}' if destination is not None else None,
                status=status, native_matches=matches, identity_evidence=identity,
                name=name, name_source_symbol='itemName_'+kind['prefix'], name_source_index=i,
                name_sha256=sha256(name_raw), source_sha256=sha256(original),
                converted_sha256=sha256(converted), pixels_sha256=digest,
                bytes=stride, tiles=kind['tiles'], tile_bytes=0x800, width=64, height=64,
                palette_bytes=32, texture_format='CI4', native_palette_format='RGBA5551',
                price_word=struct.unpack_from('>H', prices, i*2)[0], catalogue_position=order.index(i),
                acquisition=membership[item], selectable=False, runtime_installed=False))
            if kind['kind']=='floor':
                rows[-1]['source_sound_selector']=sounds['source_selectors'][i]
        banks.append(dict(kind=kind['kind'], source_member=member, source_bytes=len(raw),
            source_sha256=sha256(raw), native_vrom=kind['vrom'], native_bytes=len(native),
            native_sha256=sha256(native), source_player_count=67, source_shop_count=4,
            native_player_count=64, native_shop_count=4, shop_mappings=shops, metadata=metadata))
    if set(assets) != {f'{item:04X}' for item in SURFACES}:
        raise ValueError('Discovered surface additions disagree with the stable registry')
    report = dict(format='AFV3-ROOM-SURFACES-INVENTORY-1', version=VERSION,
        registry_version=SURFACE_REGISTRY_VERSION, base_sha256=sha256(image),
        source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()),
        banks=banks, rows=rows, floor_sound_inputs=sounds, counts=dict(player_surfaces=len(rows),
            existing=sum(r['status']=='existing-native-artwork' for r in rows),
            ambiguous=sum(r['status']=='ambiguous-native-artwork' for r in rows),
            additive=len(assets), additive_bytes=sum(map(len, assets.values())),
            non_item_shop_surfaces=sum(b['source_shop_count'] for b in banks)))
    return report, assets


def checked_prepared(directory, inventory, assets):
    directory = Path(directory).resolve()
    raw = (directory/'surfaces.json').read_bytes()
    report = json.loads(raw)
    reference = {r['source_item_id']:r for r in inventory['rows']}
    if (report['format']!='AFV3-ROOM-SURFACES-PREPARED-1' or report['version']!=VERSION or
            report['registry_version']!=SURFACE_REGISTRY_VERSION or
            report['source_rel_sha256']!=inventory['source_rel_sha256'] or
            report['source_symbols_sha256']!=inventory['source_symbols_sha256'] or
            report['banks']!=inventory['banks'] or report['floor_sound_inputs']!=inventory['floor_sound_inputs'] or
            report['runtime_installed']):
        raise ValueError('Changed complete room-surface preparation source or format')
    found = {}
    for row in report['objects']:
        key = row['source_item_id']
        if key in found or key not in assets or any(row.get(k)!=v for k,v in reference[key].items()):
            raise ValueError('Changed prepared surface identity or complete metadata')
        path = (directory/row['object_file']).resolve()
        if path.parent!=directory or path.name!=key+'.surface.bin':
            raise ValueError('Surface object escapes its prepared directory')
        data = path.read_bytes()
        if data!=assets[key] or sha256(data)!=row['converted_sha256']:
            raise ValueError('Changed complete prepared surface palette or texture')
        found[key] = (data, dict(directory=str(directory.relative_to(ROOT)), report_sha256=sha256(raw)))
    if not found:
        raise ValueError('Empty room-surface preparation')
    return found


def convert(source, image, output, selected=(), category=None, reuse=()):
    from v3_furniture_install import provenance_patch
    if category not in (None, 'floor', 'wall'):
        raise ValueError('Room-surface categories are floor and wall')
    inventory, assets = discover(source, image)
    chosen = [r for r in inventory['rows'] if r['source_item_id'] in assets and
        (not selected or r['source_item_id'] in selected) and (category is None or r['kind']==category)]
    if not chosen or selected and set(selected)!={r['source_item_id'] for r in chosen}:
        raise ValueError('Empty, existing, or unsupported room-surface selection')
    reused = {}
    for directory in reuse:
        reused.update(checked_prepared(directory, inventory, assets))
    output.mkdir(parents=True, exist_ok=False)
    objects = []
    for row in chosen:
        key = row['source_item_id'];filename = key+'.surface.bin'
        write_new(output/filename, reused[key][0] if key in reused else assets[key])
        objects.append(dict(row, object_file=filename,
            **({'reused_artwork':reused[key][1]} if key in reused else {})))
    report = dict(inventory, format='AFV3-ROOM-SURFACES-PREPARED-1', objects=objects,
        runtime_installed=False, batch=dict(objects=len(objects),bytes=sum(r['bytes'] for r in objects),
            reused=sum(r['source_item_id'] in reused for r in objects),compiler_containers=0),
        pending=['additive resource readers and selection', 'carried item/name/price/catalogue bounds',
                 'room surface application and persistence', 'source acquisition routes',
                 'floor sound/room-scoring mapping', 'focused native and ordinary room verification'],
        sources={name:sha256((ROOT/name).read_bytes()) for name in SOURCES})
    write_new(output/'surfaces.json', (json.dumps(report, indent=2)+'\n').encode())
    patch = provenance_patch(objects, ('tools/v3_room_surfaces.py','tools/v3_furniture_pipeline.py'))
    if patch:
        write_new(output/'provenance.patch', patch.encode())
    return report
