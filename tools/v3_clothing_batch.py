"""Discover and prepare the complete clothing category from verified sources.

Compare decoded pixels, not names or palette indices. A donor appearance without
a native match is an additive candidate; a changed appearance of an existing
garment must not overwrite that garment. Room mannequins follow their parent.
"""
from collections import Counter
import json
import re
import struct

from aflib import by_vrom, sha256, u32
from apply_translation import write_new
from item_identity_sheet import SHEET_SHA, sheet_rows
from v3_clothing import source_assets, garment
from v3_room_aliases import FUNCTIONS
from v3_villager_defaults import pixels

FORMAT = 'AFV3-CLOTHING-ASSETS-1'
CATEGORY = 'clothing-appearances'
STOCK = ('cloth_listA', 'cloth_listB', 'cloth_listC', 'cloth_listEvent', 'cloth_listChristmas')


def parent_contract(source):
    functions = {}
    for role in ('place', 'pickup'):
        address, symbol, size, digest = FUNCTIONS[role]
        raw, receipt = source.function(address)
        if (receipt['symbol'] != symbol or len(raw) != size or sha256(raw) != digest
                or receipt['relocations']):
            raise ValueError('Changed complete clothing placement/pickup function')
        functions[role] = receipt
        if role == 'place':
            first, end, display = (u32(raw, at)&65535 for at in (0x0C, 0x18, 0x50))
        elif (u32(raw, 0x18)&65535, u32(raw, 0x20)&65535, u32(raw, 0x5C)&65535) != (
                display, display+(end-first)*4-1, first):
            raise ValueError('Donor clothing conversions disagree')
    return dict(first=first, end=end, display_first=display, functions=functions)


def representations(source):
    """Mannequins use carried names, not stale furniture-table placeholders."""
    contract = parent_contract(source)
    names = source.raw('itemName_cloth')
    if len(names) != (contract['end']-contract['first'])*16:
        raise ValueError('Clothing names disagree with complete conversion bounds')
    rows = {}
    for index, parent in enumerate(range(contract['first'], contract['end'])):
        name = names[index*16:(index+1)*16]
        if not name.rstrip(b' ') or any(c < 32 or c > 126 for c in name):
            raise ValueError('Mannequin lacks a complete carried garment name')
        display = contract['display_first']+index*4
        rows[display] = dict(category='clothing', display_item_id=f'{display:04X}',
            parent_id=f'GAFE01-r0/item/{parent:04X}', parent_item_id=f'{parent:04X}',
            parent_name=name.decode('ascii').rstrip(), parent_name_sha256=sha256(name),
            parent_name_symbol='itemName_cloth', parent_name_index=index,
            independently_selectable=False, conversion_functions=contract['functions'])
    return rows


def discover(source, native, first_archive, worksheet, *, installed=None):
    assets = source_assets(native, first_archive, source.rel, source.symbols.encode())
    if sha256(worksheet.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed clothing identity worksheet')
    identities = {}
    for line, row in sheet_rows(worksheet, 'Items'):
        item = row.get('E', '')
        if re.fullmatch('24[0-9A-F]{2}', item):
            if item in identities:
                raise ValueError('Ambiguous clothing worksheet identity')
            identities[item] = (line, row)
    contract = parent_contract(source)
    lo, hi = contract['first'], contract['end']
    if (lo, hi) != (0x2400, 0x24FF):
        raise ValueError('Changed complete clothing source bounds')
    native_textures, native_palettes = assets[-2:]
    native_pixels = {}
    for index in range(256):
        decoded = pixels(native_textures[index*512:(index+1)*512],
                         native_palettes[index*32:(index+1)*32])
        native_pixels.setdefault(decoded, []).append(f'{0x2400+index:04X}')
    season_counts = source.raw('cloth_season_cnt')
    if season_counts != bytes((32, 10, 11, 9, 9)):
        raise ValueError('Changed donor clothing season partition')
    stock, tables = {}, {}
    for name in STOCK:
        raw = source.raw(name)
        values = [v for (v,) in struct.iter_unpack('>H', raw)]
        if not values or values[-1] or any(not lo <= v < hi for v in values[:-1]):
            raise ValueError('Unbounded donor clothing stock list')
        if name in STOCK[:3] and len(values)-1 != sum(season_counts):
            raise ValueError('Clothing seasons do not partition complete stock')
        tables[name] = dict(bytes=len(raw), sha256=sha256(raw))
        for position, value in enumerate(values[:-1]):
            season, boundary = None, 0
            if name in STOCK[:3]:
                for i, count in enumerate(season_counts):
                    if boundary <= position < boundary+count:
                        season = ('all', 'spring', 'summer', 'autumn', 'winter')[i]
                        break
                    boundary += count
            stock.setdefault(value, []).append(dict(symbol=name, position=position, season=season))
    catalogue = source.raw('mCL_cloth_idx_list')
    values = [v for (v,) in struct.iter_unpack('>H', catalogue)]
    if len(set(values)) != len(values):
        raise ValueError('Duplicate donor clothing catalogue identity')
    tables['mCL_cloth_idx_list'] = dict(bytes=len(catalogue), sha256=sha256(catalogue))
    installed_rows, current_files, current_image = {}, None, None
    if installed is not None:
        current_image, current_report = installed
        if sha256(current_image) != current_report['output_sha256']:
            raise ValueError('Changed installed clothing cartridge')
        installed_rows = {r['donor_item_id']: r for r in current_report['clothing']['imports']}
        if len(installed_rows) != len(current_report['clothing']['imports']):
            raise ValueError('Duplicate installed clothing identity')
        current_files = by_vrom(current_image)
    rows, objects = [], []
    for item in range(lo, hi):
        data, row = garment(assets, item)
        key = row['donor_item_id']; index = item-lo
        matches = native_pixels.get(pixels(data[:512], data[512:]), [])
        line, identity = identities.get(key, (None, {}))
        declared = identity.get('C', '')
        declared = declared if re.fullmatch('24[0-9A-F]{2}', declared) else None
        counterpart = declared if declared in matches else matches[0] if len(matches) == 1 else None
        status = 'native-appearance' if matches else 'donor-variant' if declared else 'additive-appearance'
        display = contract['display_first']+index*4
        donor_index = (display-0x1000)//4
        row.update(status=status, native_candidates=matches, native_item_id=counterpart,
            declared_native_item_id=declared, identity_worksheet_row=line,
            parent_item_id=key, display_item_id=f'{display:04X}',
            display_rotation_ids=[f'{display+i:04X}' for i in range(4)],
            independently_selectable_display=False, catalogue_position=(
                values.index(donor_index) if donor_index in values else None),
            stock=stock.get(item, []), runtime_integration_checked=False, selectable=False,
            installed_resource=False)
        old = installed_rows.get(key)
        if old is not None:
            vrom = int(old['vrom'], 16)
            owners = [f for f in current_files.values() if f.vstart <= vrom and vrom+len(data) <= f.vend]
            if (len(owners) != 1 or old['resource_sha256'] != sha256(data) or
                    owners[0].extract(current_image)[vrom-owners[0].vstart:vrom-owners[0].vstart+len(data)] != data):
                raise ValueError('Changed complete installed clothing resource')
            row.update(installed_resource=True, installed_item_id=old['item_id'])
        if not matches:
            if row['catalogue_position'] is None:
                raise ValueError('Added donor garment has no source catalogue identity')
            row['resource_offset'] = sum(len(part) for part in objects)
            objects.append(data)
        rows.append(row)
    if set(installed_rows)-{r['donor_item_id'] for r in rows}:
        raise ValueError('Installed garment escapes donor inventory')
    blob = b''.join(objects)
    return dict(format=FORMAT, category=CATEGORY, rows=rows, counts=dict(Counter(r['status'] for r in rows)),
        new_resource_count=sum(not r['native_candidates'] and not r['installed_resource'] for r in rows),
        bytes=len(blob), sha256=sha256(blob), resource_file='clothing.bin',
        source_rel_sha256=sha256(source.rel), source_symbols_sha256=sha256(source.symbols.encode()),
        source_archive_sha256=sha256(first_archive), original_rom_sha256=sha256(native),
        native_texture_sha256=sha256(native_textures), native_palette_sha256=sha256(native_palettes),
        worksheet_sha256=SHEET_SHA, parent_contract=contract, source_tables=tables,
        source_season_counts=list(season_counts),
        pending=['shared runtime installation for additional garments', 'optional composition',
                 'focused changed-path verification'],
        native_execution_tested=False), blob


def convert(source, native, first_archive, worksheet, output, *, installed=None):
    report, data = discover(source, native, first_archive, worksheet, installed=installed)
    output.mkdir(parents=True, exist_ok=False)
    write_new(output/report['resource_file'], data)
    write_new(output/'art.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


def checked(source, native, first_archive, worksheet, directory, *, installed=None):
    """Reuse a complete prepared category, rejecting stale or altered content."""
    expected, data = discover(source, native, first_archive, worksheet, installed=installed)
    if (json.loads((directory/'art.json').read_bytes()) != expected or
            (directory/expected['resource_file']).read_bytes() != data):
        raise ValueError('Changed complete prepared clothing category')
    return expected, data
