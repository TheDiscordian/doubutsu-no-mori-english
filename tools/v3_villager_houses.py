"""Verify donor house layers and exact native room-surface artwork matches."""
import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from apply_translation import write_new
from gamecube import rarc_files
from gc_names import symbol_data
from item_identity_sheet import SHEET_SHA, sheet_rows
from item_matches import load_matches, verify_source
from textbanks import banks
from textcodec import command_info
from v3_import_catalog import DONOR_FILES, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_registry import villager_actor, villager_house_layers
from v3_registry import FURNITURE
from v3_villager_art import native_palette, pack4, untile

HOUSE, FOREGROUND, STRIDE = 0xE02000, 0x11AB000, 0x206
NATIVE_START, NATIVE_COUNT, TARGET_COUNT = 398, 458, 498
DONOR_FG_SHA = 'f443f2f451e3a579d183176ba97a81a6685be4746509a4c8a9979e7c900f6fa5'
SHARED_HOUSE_ITEMS = (0x10B8, 0x1154, 0x11E4, 0x1358, 0x136C)
ABI = 23
SOURCES = ('tools/v3_villager_houses.py', 'tools/v3_registry.py', 'tools/item_matches.py',
           'tools/item_identity_sheet.py', 'translations/item_reference_matches.json',
           'translations/item_sheet_matches.json', 'translations/item_resolved_matches.json',
           'translations/item_design_matches.json')
NATIVE_HOUSE_SHA = '87f661e99699666583c3478947066f11f8408da7e168b68c7764e347a3c45a69'
NATIVE_FG_SHA = '8adb6d26b23eaba8f70483040dfc78211c3e5436422e93ee32397fcf97836f3a'
WINDOWS = ((0x800AB194, 0x25EF26D0, 0x25EF2770),
           (0x800AB1B0, 0x271826D0, 0x27182770),
           (0x80086104, 0x256B1A20, 0x256B1E30),
           (0x80086118, 0x24190728, 0x241907C8),
           (0x8008611C, 0x240901CA, 0x240901F2))


def layers(data):
    if len(data) % STRIDE:
        raise ValueError('Partial house foreground record')
    result = {}
    for at in range(0, len(data), STRIDE):
        row = data[at:at + STRIDE]
        number = struct.unpack_from('>H', row)[0]
        if number in result:
            raise ValueError('Duplicate house foreground identity')
        result[number] = row
    return result


def surface_pixels(data):
    colours = struct.unpack_from('>16H', data)
    return tuple(colours[index] for byte in data[32:] for index in (byte >> 4, byte & 15))


def surface_match(files, native, raw, index, stride):
    if len(raw) % stride or index * stride + stride > len(raw):
        raise ValueError('House surface exceeds donor bank')
    row = raw[index * stride:(index + 1) * stride]
    palette = native_palette(row[:32])
    # Both room surfaces are composed from independent 64x64 CI4 tiles.
    texture = b''.join(pack4(untile(row[at:at + 0x800], 64, 64, 4))
                       for at in range(32, stride, 0x800))
    converted = palette + texture
    wanted, matches, inspected = surface_pixels(converted), [], []
    for vrom, entry in files.items():
        count, remainder = divmod(entry.size, stride)
        if remainder or not 60 <= count <= 128:
            continue
        bank = entry.extract(native)
        inspected.append({'vrom': f'{vrom:08X}', 'records': count, 'sha256': sha256(bank)})
        for candidate in range(count):
            native_row = bank[candidate * stride:(candidate + 1) * stride]
            if surface_pixels(native_row) == wanted:
                matches.append({'vrom': f'{vrom:08X}', 'index': candidate,
                                'record_sha256': sha256(native_row)})
    return {'donor_index': index, 'donor_record_sha256': sha256(row),
            'converted_sha256': sha256(converted), 'pixels_compared': len(wanted),
            'native_matches': matches, 'native_banks_checked': inspected}


def item_dependencies(native, donor, symbols, items):
    """Reuse reviewed identities; never infer an existing item from its number."""
    approved = load_matches()
    native_banks = {bank.name: bank.entries() for bank in banks(native)}
    ftr = symbol_data(donor['rel'], symbols, 'ftrName_table')
    ftr2 = symbol_data(donor['rel'], symbols, 'ftrName2_table')
    music = symbol_data(donor['rel'], symbols, 'itemName_minidisk')
    sheet = ROOT / 'build/item-identity-megasheet.xlsx'
    if sha256(sheet.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed cached house-item identity evidence')
    shared = {int(cell['C'], 16): (row, cell) for row, cell in sheet_rows(sheet, 'Items')
              if cell.get('C') in {f'{item:04X}' for item in SHARED_HOUSE_ITEMS}}
    info = command_info(by_vrom(native)[CODE_VROM].extract(native))
    result = []
    for item in sorted(items):
        if item in (0xFFFE, 0xFFFF, 0x4080):
            continue  # Reviewed wall/reserved/door layout markers, not imports.
        if 0x1000 <= item < 0x2000:
            number, base, width = (item - 0x1000) // 4, 'furniture', 4
            names = ftr
        elif 0x3000 <= item < 0x4000:
            number, base, width = (item - 0x3000) // 4, 'furniture_gc_added', 4
            names = ftr2
        elif 0x2A00 <= item < 0x2B00:
            number, base, width = item - 0x2A00, 'item_2A', 1
            names = music
        else:
            raise ValueError(f'Unreviewed donor house item family: {item:04X}')
        raw = names[number * 16:(number + 1) * 16]
        if len(raw) != 16:
            raise ValueError('House item name exceeds its donor table')
        key, matches = f'{base}:{number:04X}', []
        for row in approved.values():
            if row['reference_id'] != key:
                continue
            group, offset = row['id'].split(':')
            start = int(offset, 16)
            source = native_banks[group][start:start + width]
            if (len(source) != width or len(set(source)) != 1
                    or sha256(source[0]) != row['source_sha256']
                    or sha256(raw) != row['reference_sha256']):
                raise ValueError('House dependency differs from its reviewed identity')
            target = (0x1000 if group == 'item_10' else int(group[5:], 16) << 8) + start
            matches.append(target | (item & 3) if width == 4 else target)
        root, evidence = (item & ~3 if width == 4 else item), None
        if not matches and root in SHARED_HOUSE_ITEMS:
            position, cell = shared[root]
            source = native_banks['item_10'][root - 0x1000:root - 0x1000 + 4]
            if (cell['E'] != f'{root:04X}' or cell['J'].encode('ascii').ljust(16, b' ') != raw
                    or cell['CG'] in ('', '-') or cell['CG'] != cell['CQ']
                    or cell['CJ'] != cell['CX'] or len(set(source)) != 1):
                raise ValueError('Shared house item identity differs between releases')
            verify_source({'source_sha256': sha256(source[0]), 'native_name': cell['H']}, source[0], info)
            matches.append(item)
            evidence = {'sheet_sha256': SHEET_SHA, 'row': position,
                        'source_sha256': sha256(source[0]),
                        'same_model_reference': True, 'same_texture_reference': True}
        imported = FURNITURE.get(root)
        result.append({'donor_item': f'{item:04X}', 'name': raw.decode('ascii').rstrip(),
                       'reference_id': key, 'name_sha256': sha256(raw),
                       'reviewed_native_items': [f'{value:04X}' for value in matches],
                       'imported_item': f'{imported[1] | (item & 3):04X}' if imported else None,
                       'shared_identity_evidence': evidence,
                       'status': 'existing_identity' if len(matches) == 1 else
                                 'import_dependency' if imported else 'identity_or_content_work_required'})
    return result


def metadata(native, donor, symbols):
    verified_rom(native)
    if (sha256(donor['rel']) != REL_SHA or sha256(symbols) != SYMBOLS_SHA
            or sha256(donor['forest_2nd.arc']) != DONOR_FILES['forest_2nd.arc'][1]):
        raise ValueError('House conversion requires the pinned native and donor sources')
    members = dict(rarc_files(donor['forest_2nd.arc']))
    fg = members['data/fgnpcdata.bin']
    if len(fg) != 510 * STRIDE or sha256(fg) != DONOR_FG_SHA:
        raise ValueError('Changed donor house foreground source')
    source = symbol_data(donor['rel'], symbols.decode(), 'npc_house_list')
    if len(source) != 238 * 8:
        raise ValueError('Changed donor house table size')
    files, donor_layers = by_vrom(native), layers(fg)
    original = files[HOUSE].extract(native)
    native_fg = files[FOREGROUND].extract(native)
    native_layers = layers(native_fg)
    if len(original) != 218 * 8 or len(native_layers) != 432:
        raise ValueError('Changed native house table or foreground count')
    if any(not NATIVE_START <= value < NATIVE_START + NATIVE_COUNT for value in native_layers):
        raise ValueError('Native house layer escapes its sorted pointer allocation')
    houses = []
    for index, name in ((232, 'Cheri'), (235, 'Punchy')):
        raw = source[index * 8:(index + 1) * 8]
        kind, palette, wall, floor, main, secondary = struct.unpack('>4B2H', raw)
        actor = villager_actor(index)
        first_target, _ = villager_house_layers(index)
        rows, items = [], set()
        for offset, number in enumerate((main, secondary)):
            row = donor_layers[number]
            counts = Counter(struct.unpack_from('>256H', row, 2))
            items.update(counts)
            rows.append({'donor_layer': number, 'target_layer': first_target + offset,
                         'sha256': sha256(row), 'tail': row[514:].hex(),
                         'items': {f'{item:04X}': count for item, count in sorted(counts.items())},
                         'occupied_cells': [{'x': cell % 16, 'z': cell // 16, 'item': f'{item:04X}'}
                                            for cell, (item,) in enumerate(struct.iter_unpack('>H', row[2:514]))
                                            if item not in (0xFFFE, 0xFFFF)]})
        houses.append({'name': name, 'donor_index': index, 'actor_id': f'{actor:04X}',
            'donor_house_hex': raw.hex(), 'house_type': kind, 'house_palette': palette,
            'wall': surface_match(files, native, members['data/player_room_wall.bin'], wall, 0x1020),
            'floor': surface_match(files, native, members['data/player_room_floor.bin'], floor, 0x2020),
            'layers': rows, 'dependencies': item_dependencies(native, donor, symbols.decode(), items),
            'installed': False})
    return {'native_house_sha256': sha256(original), 'native_fg_sha256': sha256(native_fg),
            'native_layer_min': min(native_layers), 'native_layer_max': max(native_layers),
            'native_fg_bytes': len(native_fg), 'donor_house_sha256': sha256(source),
            'donor_fg_sha256': sha256(fg), 'houses': houses}


def install(native, base, code, donor, symbols, furniture):
    """Install Cheri's complete mapped layers; move-in selection stays disabled."""
    report = metadata(native, donor, symbols)
    files = by_vrom(base)
    original, fg_original = (files[v].extract(base) for v in (HOUSE, FOREGROUND))
    if sha256(original) != NATIVE_HOUSE_SHA or sha256(fg_original) != NATIVE_FG_SHA:
        raise ValueError('House installation requires unchanged native resources')
    native_code = by_vrom(native)[CODE_VROM].extract(native)
    for start, end in ((0x800AB134, 0x800AB3A0), (0x8008609C, 0x800862DC)):
        if bytes(code[start - CODE_RAM:end - CODE_RAM]) != native_code[start - CODE_RAM:end - CODE_RAM]:
            raise ValueError('House loader differs from its reviewed native function')
    cheri = report['houses'][0]
    if cheri['donor_house_hex'] != '00003f2102020203' or cheri['actor_id'] != 'E0EA':
        raise ValueError('Changed pilot house metadata')
    active_items = {row['item_id'] for row in furniture['imports']}
    mapping = {item: item for item in (0x4080, 0xFFFE, 0xFFFF)}
    for row in cheri['dependencies']:
        if len(row['reviewed_native_items']) == 1:
            target = row['reviewed_native_items'][0]
        elif row['status'] == 'import_dependency' and row['imported_item'] in active_items:
            target = row['imported_item']
        else:
            raise ValueError('Cheri house dependency has no complete installed mapping')
        mapping[int(row['donor_item'], 16)] = int(target, 16)
    surface_indices = []
    for name, bank in (('wall', 0x182A000), ('floor', 0x17A1000)):
        matches = cheri[name]['native_matches']
        if len(matches) != 1 or matches[0]['vrom'] != f'{bank:08X}':
            raise ValueError('Cheri room surface lacks its exact native artwork')
        surface_indices.append(matches[0]['index'])
    houses = bytearray(original + bytes(20 * 8))
    struct.pack_into('>4B2H', houses, 234 * 8, cheri['house_type'], cheri['house_palette'],
                     *surface_indices, *villager_house_layers(232))
    donor_layers = layers(dict(rarc_files(donor['forest_2nd.arc']))['data/fgnpcdata.bin'])
    foreground = bytearray(fg_original)
    appended = []
    for row in cheri['layers']:
        raw = donor_layers[row['donor_layer']]
        converted = (struct.pack('>H', row['target_layer']) +
                     b''.join(struct.pack('>H', mapping[item])
                              for (item,) in struct.iter_unpack('>H', raw[2:514])) + raw[514:])
        if row['target_layer'] in layers(fg_original) or len(converted) != STRIDE:
            raise ValueError('Imported house layer collides with native content')
        foreground.extend(converted)
        appended.append({'id': row['target_layer'], 'sha256': sha256(converted), 'bytes': len(converted)})
    foreground.extend(bytes(-len(foreground) % 8))
    if len(houses) != 0x770 or FOREGROUND + len(foreground) != 0x11E1E30:
        raise ValueError('House resources differ from their reviewed loader bounds')
    for address, expected, replacement in WINDOWS:
        if struct.unpack_from('>I', code, address - CODE_RAM)[0] != expected:
            raise ValueError('Changed house loader instruction')
        struct.pack_into('>I', code, address - CODE_RAM, replacement)
    cheri['installed'] = True
    report.update({'installed_villagers': ['E0EA'], 'new_villager_ids_enabled': False,
                   'house_bytes': len(houses), 'foreground_bytes': len(foreground),
                   'foreground_records': 434, 'foreground_pointer_count': TARGET_COUNT,
                   'house_extra_allocation_bytes': len(houses) - len(original),
                   'foreground_extra_allocation_bytes': len(foreground) - len(fg_original),
                   'foreground_pointer_extra_allocation_bytes': (TARGET_COUNT - NATIVE_COUNT) * 4,
                   'appended_layers': appended,
                   'output_house_sha256': sha256(houses), 'output_fg_sha256': sha256(foreground),
                   'code_patches': [{'address': f'{at:08X}', 'expected': f'{before:08X}',
                                     'replacement': f'{after:08X}'} for at, before, after in WINDOWS],
                   'house_visit_tested': False, 'saved_layout_changed': False})
    return {HOUSE: bytes(houses), FOREGROUND: bytes(foreground)}, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT / 'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--donor', type=Path, default=ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    report = metadata(args.rom.read_bytes(), read_donor(args.donor), symbols)
    args.output.mkdir(parents=True, exist_ok=False)
    write_new(args.output / 'houses.json', (json.dumps(report, indent=2) + '\n').encode())
    for house in report['houses']:
        print(house['name'], 'wall', house['wall']['native_matches'], 'floor', house['floor']['native_matches'])
        for layer in house['layers']:
            print('layer', layer['donor_layer'], '->', layer['target_layer'], layer['items'])
        for dependency in house['dependencies']:
            print(dependency['donor_item'], dependency['name'], dependency['status'],
                  dependency['reviewed_native_items'], dependency['imported_item'])


if __name__ == '__main__':
    main()
