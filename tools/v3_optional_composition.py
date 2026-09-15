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
                         villager_actor, villager_house_layers)
from v3_save_runtime import profile_bytes
from v3_villager_houses import layers

BASE = ROOT/'build/v3-house-markers-01'
BASE_SHA = '55a715831671c989aa465fbf6d04c49caa975a761105ffa1f3acecd10ac7b8cf'
REPORT_SHA = 'adb6c52ed51b3606cf86f07febc459d31cc15bad6fc69459c612aec4130a53a3'
STABLE = ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64'
STABLE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
PREFIX_SIZE, ABI = 0xC000, 60


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
        index, item, _ = FURNITURE[donor]
        at = int(row['profile_ram'], 16)-0x80460000-8
        if (row['item_id'] != f'{item:04X}' or row['runtime_index'] != index
                or struct.unpack_from('>HHI', blob, at) != (index, item, 1)):
            raise ValueError('Changed installed furniture binding')
        result[row['id']] = {'id':row['id'], 'name':row['name'], 'kind':'furniture',
            'item_id':row['item_id'], 'runtime_index':index, 'dependencies':[],
            'enable_offset':at+4, 'enable_bytes':4}
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
    if len(result) != len(VILLAGERS)+len(FURNITURE)+len(CLOTHING):
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
        if not 0x20 <= offset < offset+len(value) <= PREFIX_SIZE:
            raise ValueError('Selection field escapes the resident prefix')
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
    intermediate = apply_writes(image, writes)
    start = files[BLOB].pstart
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
        current['speed_bag']['saved_profile_included'] = current['speed_bag']['enabled']
        current['clothing']['punchy_defaults_enabled'] = 'E0ED' in actors
        for slot,row in enumerate(current['clothing']['imports']):
            row['selected_for_profile'] = item_key(int(row['donor_item_id'],16)) in selection['enabled']
            row['metadata_sha256'] = sha256(blob[0x2820+slot*32:0x2840+slot*32])
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
    parser.add_argument('--all', action='store_true', help='All 26 installed experimental entries, not the whole donor disc')
    args = parser.parse_args()
    result = build(args.output, args.select, select_all=args.all)
    print(json.dumps({key:result[key] for key in ('requested','required','output_sha256','save_compatibility')}, indent=2))
