"""Compose local experimental import selections; never update a served patcher."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT
from v3_registry import (CLOTHING, CLOTHING_DISPLAYS, FURNITURE, VILLAGERS,
                         villager_actor, villager_house_layers, furniture_identity)
from v3_save_runtime import profile_bytes
from v3_villager_houses import layers

BUILD_PIN = json.loads((ROOT/'config/v3-import-build.json').read_bytes())
BASE = ROOT/BUILD_PIN['directory']
BASE_SHA = BUILD_PIN['rom_sha256']
REPORT_SHA = BUILD_PIN['report_sha256']
STABLE = ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64'
STABLE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
PREFIX_SIZE, ABI, PACKAGE_SIZE = 0xC000, BUILD_PIN['runtime_abi'], 0x30000
from v3_import_storage import PACKAGE, PACKAGE_RAM, ROWS as STATIC_ROWS, SLOTS as STATIC_COUNT


def resident_offset(blob, address, size):
    if 0x80460000 <= address <= 0x80460000 + PREFIX_SIZE - size:
        return address - 0x80460000
    if (struct.unpack_from('>4I', blob, 0xF0) !=
            (BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]), PACKAGE_RAM)):
        raise ValueError('Changed package address or checksum descriptor')
    if PACKAGE_RAM <= address <= PACKAGE_RAM + PACKAGE_SIZE - size:
        return PACKAGE + address - PACKAGE_RAM
    raise ValueError('Import row is outside checked resident resources')


def canonical(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=True)+'\n').encode()


def item_key(item):
    return f'GAFE01-r0/item/{item:04X}'


def inputs():
    image = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE/'build.json').read_bytes()
    if sha256(image) != BASE_SHA or sha256(raw) != REPORT_SHA:
        raise ValueError('Changed optional-composition base cartridge or report')
    report = json.loads(raw)
    if report['output_sha256'] != BASE_SHA or report['runtime_abi'] != ABI:
        raise ValueError('Mismatching optional-composition base report')
    return image, report


def catalogue(image, report):
    if sha256(image) != BASE_SHA or report['output_sha256'] != BASE_SHA:
        raise ValueError('Catalogue needs the pinned installed cartridge')
    files = by_vrom(image)
    blob = files[BLOB].extract(image)
    rooms = layers(files[int(report['villager_houses']['foreground_vrom'], 16)].extract(image))
    result = {}
    furniture_rows = report['furniture']['imports']+[report['speed_bag']]
    for row in furniture_rows:
        donor = int(row['id'].rsplit('/', 1)[1], 16)
        if row.get('registry_version') == 2:
            index,item = furniture_identity(donor)
            at=int(row['object_vrom'],16)-BLOB
            if sha256(blob[at:at+row['object_bytes']]) != row['object_sha256']:
                raise ValueError('Changed manifest-bound furniture artwork')
        else:
            index, item, _ = FURNITURE[donor]
        row_ram = int(row['profile_ram'], 16) - 8
        at = resident_offset(blob, row_ram, 80)
        if (row['item_id'] != f'{item:04X}' or row['runtime_index'] != index
                or struct.unpack_from('>HHI', blob, at) != (index, item, 1)):
            raise ValueError('Changed installed furniture binding')
        result[row['id']] = {'id':row['id'], 'name':row['name'], 'kind':'furniture',
            'item_id':row['item_id'], 'runtime_index':index, 'dependencies':[],
            'enable_offset':at+4, 'enable_bytes':4, 'enable_ram':row_ram+4}
    for slot, row in enumerate(report['clothing']['imports']):
        donor = int(row['donor_item_id'], 16)
        item, index, source = CLOTHING[donor]
        at = 0x2820+slot*32
        display = next(r for r in report['aloha_display']['rows'] if r['donor_item_id']==f'{donor:04X}')
        display_index, display_item = CLOTHING_DISPLAYS[donor]
        display_at = int(display['profile_ram'], 16)-0x80460000-8
        if (struct.unpack_from('>HHI', blob, at) != (item, index, source) or blob[at+10] != 1
                or row['item_id'] != f'{item:04X}' or row['resource_index'] != index
                or struct.unpack_from('>HHI', blob, display_at) != (display_index, display_item, 1)):
            raise ValueError('Changed installed shirt/mannequin binding')
        key = item_key(donor)
        result[key] = {'id':key, 'name':row['name'], 'kind':'clothing',
            'item_id':row['item_id'], 'dependencies':[], 'enable_offset':at+10, 'enable_bytes':1,
            'display_item_id':f'{display_item:04X}', 'display_runtime_index':display_index,
            'display_enable_offset':display_at+4, 'source_record':row}
    for row in report['villager_text']['imports']:
        donor = int(row['id'].rsplit('/', 1)[1], 16)
        actor = villager_actor(donor)
        at = 0x2C00+(actor-0xE0DA)*32
        metadata = blob[at:at+32]
        if (row['actor_id'] != f'{actor:04X}' or sha256(metadata) != row['record_sha256']
                or metadata[7] != 1 or blob[0x1E60+actor-0xE0DA] != 1
                or not row['initial_defaults_applied']):
            raise ValueError('Changed installed villager/default binding')
        dependencies = set()
        cloth = int(row['donor_clothing_id'], 16)
        if cloth in CLOTHING:
            if int.from_bytes(metadata[30:32], 'big') != CLOTHING[cloth][0]:
                raise ValueError('Villager does not wear its imported source shirt')
            dependencies.add(item_key(cloth))
        elif not 0x2400 <= int.from_bytes(metadata[30:32], 'big') < 0x2500:
            raise ValueError('Villager lacks a reviewed starting outfit')
        house_layers = villager_house_layers(donor)
        for layer in house_layers:
            for item in struct.unpack_from('>256H', rooms[layer], 2):
                if 0x3000 <= item < 0x4000:
                    key = item_key(item & 0xFFFC)
                    if key not in result or result[key]['kind'] != 'furniture':
                        raise ValueError('House requires an unreviewed imported furnishing')
                    dependencies.add(key)
        result[row['id']] = {'id':row['id'], 'name':row['name'], 'kind':'villager',
            'actor_id':f'{actor:04X}', 'registry_version':1,
            'dependencies':sorted(dependencies), 'house_layers':list(house_layers),
            'enable_offset':at+7, 'enable_bytes':1, 'town_flag_offset':0x1E60+actor-0xE0DA}
    # The fixed registry can reserve later imports before this pinned cartridge
    # installs them. Its catalogue must cover its actual installed records only.
    expected = ({row['id'] for row in report['villager_text']['imports']} |
                {row['id'] for row in furniture_rows} |
                {item_key(int(row['donor_item_id'], 16)) for row in report['clothing']['imports']})
    if (set(result) != expected or len(result) != len(VILLAGERS)+len(furniture_rows)+len(CLOTHING)):
        raise ValueError('Incomplete or duplicated installed development catalogue')
    return dict(sorted(result.items()))


def resolve(catalog, selected):
    if not isinstance(selected, (list, tuple)) or any(type(key) is not str for key in selected):
        raise ValueError('Selections must be a list of fixed source identities')
    requested = sorted(set(selected))
    if set(requested)-catalog.keys():
        raise ValueError('Unknown or unimplemented import: '+', '.join(sorted(set(requested)-catalog.keys())))
    enabled, reasons = set(requested), {}
    pending = list(requested)
    while pending:
        parent = pending.pop()
        for child in catalog[parent]['dependencies']:
            if child not in catalog:
                raise ValueError('Missing compiled import dependency')
            reasons.setdefault(child, set()).add(parent)
            if child not in enabled:
                enabled.add(child)
                pending.append(child)
    villagers = [catalog[key] for key in sorted(enabled) if catalog[key]['kind']=='villager']
    furniture = [catalog[key] for key in sorted(enabled) if catalog[key]['kind']=='furniture']
    shirts = [catalog[key] for key in sorted(enabled) if catalog[key]['kind']=='clothing']
    displays = [{'item_id':row['display_item_id'], 'runtime_index':row['display_runtime_index']}
                for row in shirts]
    profile = profile_bytes(villagers, furniture+displays, [row['source_record'] for row in shirts])
    return {'format':'AFV3-LOCAL-SELECTION-1', 'donor':'GAFE01-r0',
        'registry_versions':{'villagers':1, 'furniture':1, 'clothing':1, 'displays':1},
        'requested':requested, 'enabled':sorted(enabled),
        'required':sorted(enabled-set(requested)),
        'dependency_reasons':{key:sorted(value) for key,value in sorted(reasons.items())},
        'destinations':[{key:row[key] for key in ('id','name','kind','actor_id','item_id',
            'house_layers','display_item_id') if key in row} for row in
            (catalog[key] for key in sorted(enabled))],
        'profile_hex':profile.hex(), 'profile_sha256':sha256(profile),
        'experimental':True, 'web_patcher_enabled':False, 'playable_handoff':False}


def apply_writes(source, writes):
    end = 0
    for row in sorted(writes, key=lambda r:r['offset']):
        at, before, after = row['offset'], bytes.fromhex(row['before']), bytes.fromhex(row['after'])
        if (type(at) is not int or not before or len(before)!=len(after)
                or at < end or at+len(before)>len(source) or source[at:at+len(before)]!=before):
            raise ValueError('Overlapping, out-of-range, or mismatching composition write')
        end = at+len(before)
    result = bytearray(source)
    for row in writes:
        at = row['offset']; value = bytes.fromhex(row['after'])
        result[at:at+len(value)] = value
    return bytes(result)


def catalogue_selection(image, report, enabled):
    """Pack selected appended rows without changing native order or identities."""
    from v3_catalogue import VROM, RAM
    from v3_clothing_catalogue import COUNT
    entry = by_vrom(image)[VROM]
    data = entry.extract(image)
    cat = report['catalogue']
    if entry.pend or sha256(data) != cat['output_sha256']:
        raise ValueError('Changed full source catalogue resource')
    rows = [row for row in cat['imports'] if item_key(int(row['item_id'], 16)) in enabled]
    clothes = [row for row in cat['clothing']['imports'] if item_key(int(row['donor_item_id'], 16)) in enabled]
    writes = []

    def change(address, before, after, purpose):
        at = address - RAM
        if len(before) != len(after) or not 0 <= at <= len(data) - len(before) or data[at:at + len(before)] != before:
            raise ValueError('Changed optional catalogue table or count')
        if before != after:
            writes.append({'offset': entry.pstart + at, 'before': before.hex(), 'after': after.hex(), 'purpose': purpose})

    for key, width, native_count, original, selected in (
            ('af_v3_catalogue_order', 4, 436, cat['imports'], rows),
            ('af_v3_catalogue_clothing_order', 2, 245, cat['clothing']['imports'], clothes)):
        address = cat['code']['symbols'][key]
        at = address - RAM
        prefix = data[at:at + native_count * width]
        encode = lambda row: struct.pack('>HH', row['catalogue_index'], row['mode']) if width == 4 else struct.pack('>H', row['catalogue_index'])
        before = prefix + b''.join(encode(row) for row in original)
        after = prefix + b''.join(encode(row) for row in selected) + bytes((len(original) - len(selected)) * width)
        change(address, before, after, 'selected furniture ordering' if width == 4 else 'selected clothing ordering')
    furniture_count, clothing_count = 436 + len(rows), 245 + len(clothes)
    for address, opcode in ((0x808A6600, 0x24050000), (0x808A9460, 0x24140000), (0x808AF7A8, 0)):
        change(address, struct.pack('>I', opcode | cat['total_rows']),
               struct.pack('>I', opcode | furniture_count), 'selected furniture iteration/search/completion count')
    change(COUNT, struct.pack('>I', cat['clothing']['total_rows']), struct.pack('>I', clothing_count),
           'selected clothing iteration/completion count')
    return writes, {'imports': rows, 'total_rows': furniture_count,
                    'clothing_imports': clothes, 'clothing_total_rows': clothing_count}


def compose(image, report, catalog, selection):
    # Re-resolve instead of trusting a caller-supplied enabled set or profile.
    if selection != resolve(catalog, selection['requested']):
        raise ValueError('Selection receipt does not match its dependency resolution')
    if not selection['enabled']:
        stable = STABLE.read_bytes()
        if sha256(stable) != STABLE_SHA:
            raise ValueError('Changed import-free V2 baseline')
        return stable, [], None
    if sha256(image)!=BASE_SHA:
        raise ValueError('Composition needs the pinned integration cartridge')
    if catalog != catalogue(image, report):
        raise ValueError('Selection catalogue differs from actual installed bindings')
    files = by_vrom(image)
    blob = files[BLOB].extract(image)
    if (len(blob)!=files[BLOB].size or files[BLOB].pend or files[MODULE].pend
            or blob[0x20:0xE0].hex()!=report['save_runtime']['profile_hex']):
        raise ValueError('Changed physical prefix or source save-profile contract')
    writes = []
    def change(offset, value, label):
        before = image[offset:offset+len(value)]
        if before != value:
            writes.append({'offset':offset, 'before':before.hex(), 'after':value.hex(), 'purpose':label})
    def prefix(offset, value, label):
        if not (0x20 <= offset < offset+len(value) <= PREFIX_SIZE or
                len(value) == 4 and offset in (STATIC_ROWS + slot * 80 + 4 for slot in range(STATIC_COUNT))):
            raise ValueError('Selection field escapes reviewed resident enable words')
        change(files[BLOB].pstart+offset, value, label)
    prefix(0x20, bytes.fromhex(selection['profile_hex']), 'complete saved import profile')
    enabled = set(selection['enabled'])
    for key, row in catalog.items():
        active = int(key in enabled)
        prefix(row['enable_offset'], active.to_bytes(row['enable_bytes'], 'big'), key)
        if row['kind']=='villager':
            prefix(row['town_flag_offset'], bytes((active,)), key+' town eligibility')
        if row['kind']=='clothing':
            prefix(row['display_enable_offset'], active.to_bytes(4, 'big'), key+' mannequin')
    catalogue_writes, _ = catalogue_selection(image, report, enabled)
    writes.extend(catalogue_writes)
    scoring_writes, _ = scoring_selection(image, report, catalog, enabled)
    writes.extend(scoring_writes)
    intermediate = apply_writes(image, writes)
    start = files[BLOB].pstart
    new_blob = intermediate[start:start+len(blob)]
    resident_offset(blob, PACKAGE_RAM, PACKAGE_SIZE)  # Bind the actual package descriptor.
    prefix(0xF8, struct.pack('>I', zlib.crc32(new_blob[PACKAGE:PACKAGE + PACKAGE_SIZE])), 'resident package CRC')
    # The package checksum is inside the main prefix and must be included in
    # its checksum, after all selected package enable words have been applied.
    intermediate = apply_writes(image, writes)
    new_blob = intermediate[start:start+len(blob)]
    module = files[MODULE].extract(image)
    if struct.unpack_from('>4I', module, CONFIG) != (BLOB, PREFIX_SIZE, zlib.crc32(blob[:PREFIX_SIZE]), ABI):
        raise ValueError('Changed startup CRC descriptor')
    change(files[MODULE].pstart+CONFIG+8, struct.pack('>I', zlib.crc32(new_blob[:PREFIX_SIZE])), 'prefix CRC')
    result = bytearray(apply_writes(image, writes))
    fix_checksum(result)
    change(0x10, result[0x10:0x18], 'N64 header checksum')
    if apply_writes(image, writes) != result:
        raise ValueError('Unreported composition modification')
    return bytes(result), sorted(writes, key=lambda row:row['offset']), new_blob


def scoring_selection(image, report, catalog, enabled):
    """Exclude disabled imports from native group totals and recommendations.

    The HRA grouping loops scan the entire metadata table, independently of
    the placed-item enabled checks. Keeping disabled rows would make selected
    themes require furniture the chosen cartridge cannot acquire.
    """
    import v3_hra as hra
    entry, hr = by_vrom(image)[hra.NEW_VROM], report['hra']
    data = entry.extract(image)
    if entry.pend or sha256(data) != hr['output_sha256']:
        raise ValueError('Changed complete source scoring image')
    indices = {catalog[key]['runtime_index'] for key in enabled if catalog[key]['kind'] == 'furniture'}
    indices |= {catalog[key]['display_runtime_index'] for key in enabled if catalog[key]['kind'] == 'clothing'}
    writes, rows = [], []
    for row in hr['imports']:
        at = hr['metadata_address'] - hra.RAM + row['runtime_index'] * 4
        before = bytes.fromhex(row['metadata'])
        if data[at:at + 4] != before:
            raise ValueError('Changed bound furniture scoring record')
        if row['runtime_index'] in indices:
            rows.append(row)
        else:
            writes.append({'offset': entry.pstart + at, 'before': before.hex(), 'after': 'fc000000',
                           'purpose': 'disabled item excluded from HRA groups and recommendations'})
    return writes, rows


def build(output, selected=(), *, select_all=False):
    if not output.resolve().is_relative_to(ROOT/'build') or output.exists():
        raise ValueError('A fresh ignored build/ output directory is required')
    if select_all and selected:
        raise ValueError('Choose explicit identities or all installed development entries')
    image, report = inputs()
    catalog = catalogue(image, report)
    selection = resolve(catalog, list(catalog) if select_all else list(selected))
    result, writes, blob = compose(image, report, catalog, selection)
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    patch = make_ups(native, result)
    if apply_ups(native, patch) != result:
        raise ValueError('Optional cartridge patch reconstruction failed')
    receipt = {**selection, 'base_sha256':BASE_SHA if blob is not None else STABLE_SHA,
        'base_report_sha256':REPORT_SHA, 'converter_sources_sha256':sha256(canonical(report['sources'])),
        'composer_sha256':sha256(Path(__file__).read_bytes()), 'output_sha256':sha256(result),
        'patch_sha256':sha256(patch), 'rom_bytes':len(result), 'writes':writes,
        'retains_unselected_resource_storage':blob is not None,
        'save_compatibility':'V2 baseline' if blob is None else
            'Format 2: equal or larger profiles accepted by codec; missing dependencies rejected. '
            'Do not load imported saves in V2. Ordinary cross-profile reload is unverified.'}
    if blob is None:
        current = {'build':'v2-import-free', 'output_sha256':sha256(result), 'composition':receipt}
    else:
        current = copy.deepcopy(report)
        current.update(build='v3-optional-composition', input_build_sha256=BASE_SHA,
            output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
            composition=receipt, native_test='not executed for this composed profile',
            new_villager_ids_enabled=any(catalog[key]['kind']=='villager' for key in selection['enabled']))
        current['save_runtime'].update(profile_hex=selection['profile_hex'], profile_sha256=selection['profile_sha256'])
        actors = []
        for row in current['villager_text']['imports']:
            active = row['id'] in selection['enabled']
            row['selected_for_profile'] = row['move_in_enabled'] = active
            slot = int(row['actor_id'],16)-0xE0DA
            row['record_sha256'] = sha256(blob[0x2C00+32*slot:0x2C20+32*slot])
            if active: actors.append(row['actor_id'])
        current['villager_selection']['move_in_enabled'] = actors
        current['villager_houses']['new_villager_ids_enabled'] = bool(actors)
        for row in current['villager_houses']['houses']:
            row['selected_for_profile'] = row['move_in_enabled'] = row['actor_id'] in actors
        current['town_residents']['selection_mode'] = 'explicit_profile'
        for row in current['town_residents']['adaptations']:
            row['enabled_for_integration'] = row['actor_id'] in actors
        for row in current['furniture']['imports']+[current['speed_bag']]:
            row['enabled'] = row['id'] in selection['enabled']
        for row in current['furniture_items']['imports']:
            row['enabled'] = item_key(int(row['item_id'], 16)) in selection['enabled']
        current['speed_bag']['saved_profile_included'] = current['speed_bag']['enabled']
        current['clothing']['punchy_defaults_enabled'] = 'E0ED' in actors
        for slot,row in enumerate(current['clothing']['imports']):
            row['selected_for_profile'] = item_key(int(row['donor_item_id'],16)) in selection['enabled']
            row['metadata_sha256'] = sha256(blob[0x2820+slot*32:0x2840+slot*32])
        _, selected_cat = catalogue_selection(image, report, set(selection['enabled']))
        from v3_catalogue import VROM, RAM
        from v3_import_storage import ROWS, ITEMS, ITEMS_RAM, TABLE_END, slot
        cat = current['catalogue']
        cat['installed_total_rows'] = cat['total_rows']
        cat.update(imports=selected_cat['imports'], total_rows=selected_cat['total_rows'])
        cat['clothing']['installed_total_rows'] = cat['clothing']['total_rows']
        cat['clothing'].update(imports=selected_cat['clothing_imports'], total_rows=selected_cat['clothing_total_rows'])
        data = by_vrom(result)[VROM].extract(result)
        cat['output_sha256'] = sha256(data)
        at = cat['code']['symbols']['af_v3_catalogue_bit'] - RAM
        cat['code']['sha256'] = sha256(data[at:at + cat['code']['bytes']])
        at = cat['clothing']['table_address'] - RAM
        cat['clothing']['table_sha256'] = sha256(data[at:at + cat['clothing']['total_rows'] * 2])
        package_sha = sha256(blob[PACKAGE:PACKAGE + PACKAGE_SIZE])
        for section, count in (('construction', 9), ('garden', 15), ('western', 22), ('western_large', 25)):
            records = current['furniture']['imports'][:count]
            profile_rows = b''.join(blob[ROWS + slot(int(r['item_id'], 16)) * 80:
                ROWS + slot(int(r['item_id'], 16)) * 80 + 80] for r in records)
            item_rows = b''.join(blob[ITEMS + slot(int(r['item_id'], 16)) * 32:
                ITEMS + slot(int(r['item_id'], 16)) * 32 + 32] for r in records + [current['speed_bag']])
            current[section].update(optional_composition_updated=True,
                profile_rows_sha256=sha256(profile_rows), item_rows_sha256=sha256(item_rows),
                item_rows_ram=f'{ITEMS_RAM:08X}', package_sha256=package_sha,
                pending=(['post-office reward delivery'] if section == 'garden' else []) +
                        ['ordinary acquisition, placement, and persistence'])
            for row in current[section]['imports']:
                row['enabled'] = row['id'] in selection['enabled']
        current['construction_catalogue']['optional_composition_updated'] = True
        current['accessory_runtime']['package_sha256'] = package_sha
        current['campsite'].update(package_sha256=package_sha, optional_composition_updated=True)
        current['campsite_calendar'].update(package_sha256=package_sha, optional_composition_updated=True)
        current['camper'].update(package_sha256=package_sha, optional_composition_updated=True)
        current['campsite_exterior'].update(package_sha256=package_sha, optional_composition_updated=True)
        current['campsite_placement'].update(package_sha256=package_sha, optional_composition_updated=True)
        current['import_storage'].update(package_sha256=package_sha,
            profile_rows_sha256=sha256(blob[ROWS:ITEMS]), item_rows_sha256=sha256(blob[ITEMS:TABLE_END]))
        for section in ('camping', 'tent_model', 'fire', 'school_desks'):
            current[section].update(package_sha256=package_sha, optional_composition_updated=True)
            for row in current[section]['imports']:
                row['enabled'] = row['id'] in selection['enabled']
        current['school_desks']['pending'] = [p for p in current['school_desks']['pending']
                                              if p != 'optional composition']
        import v3_hra as hra
        _, selected_hra = scoring_selection(image, report, catalog, set(selection['enabled']))
        hr = current['hra']
        data = by_vrom(result)[hra.NEW_VROM].extract(result)
        at = hr['metadata_address'] - hra.RAM
        hr.update(imports=selected_hra, output_sha256=sha256(data),
                  metadata_sha256=sha256(data[at:at + hr['metadata_rows'] * 4]))
    output.mkdir(parents=True, exist_ok=False)
    write_new(output/'animal-forest-v3-asset-loader.z64', result)
    write_new(output/'asset-loader.ups', patch)
    write_new(output/'profile.json', canonical(receipt))
    write_new(output/'build.json', canonical(current))
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--select', action='append', default=[], help='Fixed GAFE01-r0 identity; repeat as needed')
    parser.add_argument('--all', action='store_true', help='All installed experimental entries, not the whole donor disc')
    args = parser.parse_args()
    result = build(args.output, args.select, select_all=args.all)
    print(json.dumps({key:result[key] for key in ('requested','required','output_sha256','save_compatibility')}, indent=2))
