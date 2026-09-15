"""Install the three full-sized Western furnishings in an experimental cartridge.

Relocate the checked resident package, preserving all existing function/asset
addresses, and give shared multi-cell readers their own bounded code region.
Neither served web patcher is modified.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, apply_ups, by_vrom, fix_checksum,
                   make_ups, sha256, verified_rom)
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_clothing_items import DEFINES as ITEM_DEFINES
from v3_furniture_art import LARGE_WESTERN_PILOTS, native_profile
from v3_garden_runtime import install_catalogue, score_tables
from v3_import_catalog import read_donor
from v3_registry import furniture_slot
from v3_western_items import identity_evidence, metadata
import v3_catalogue as catalogue
import v3_feng_shui as feng
import v3_hra as hra
import v3_shops as shops

ABI = 66
BASE = ROOT / 'build/v3-western-runtime-02'
BASE_SHA = 'e9285a7d301b466b32eb4af022b5dc7ffaa555b3f1de93cffdb86bc838daa858'
REPORT_SHA = 'e6679d4b4faec83566d87d86ca7f942dd494de42405bca68752285325f4465f9'
ART = ROOT / 'build/v3-western-large-art-01'
ART_SHA = 'aa29967549c87df4fa1d0a81536ac08ef0e1e78870db661e592dc3e68f50c3d1'
PACKAGE, PACKAGE_RAM, PACKAGE_SIZE = 0x1CA000, 0x80473000, 0x11000
ROWS, ROWS_RAM, STATIC_COUNT = PACKAGE + 0xF000, 0x80482000, 25
ITEMS, ITEMS_RAM, ITEM_COUNT = PACKAGE + 0xF800, 0x80482800, 26
TABLE_END = ITEMS + ITEM_COUNT * 32
HELPER, HELPER_RAM = PACKAGE + 0x10000, 0x80483000
DEFINES = ('AF_V3_CONSTRUCTION_ITEMS=1', 'AF_V3_GARDEN_ITEMS=1',
           'AF_V3_WESTERN_ITEMS=1', 'AF_V3_WESTERN_LARGE=1', 'AF_V3_EXPANDED_BANKS=1')
SOURCES = ('tools/v3_western_large_runtime.py', 'tools/v3_western_items.py',
    'tools/v3_furniture_art.py', 'tools/v3_registry.py', 'tools/v3_asset_loader.py',
    'tools/v3_catalogue.py', 'tools/v3_garden_runtime.py', 'tools/v3_shops.py',
    'overlays/v3/items.c', 'overlays/v3/items_large.ld', 'overlays/v3/construction.h',
    'overlays/v3/startup.c', 'overlays/v3/accessory.h', 'overlays/v3/catalogue.c',
    'overlays/v3/catalogue.ld', 'overlays/v3/furniture.c')


def install_readers(blob, prior, output):
    expanded = copy.deepcopy(prior['furniture']['expanded_tables'])
    helper, compiled = compile_part('furniture_expanded', output / 'furniture_expanded',
        defines=('AF_V3_FURNITURE_TABLES=1', 'AF_V3_CLOTHING_DISPLAY=1',
                 'AF_V3_SPEED_BAG=1', 'AF_V3_ALOHA_DISPLAY=1') + DEFINES,
        extra_sources=('overlays/v3/furniture_entry.S',), primary_source='overlays/v3/furniture.c')
    old = expanded['expanded_code']
    if (sha256(blob[0x5800:0x5800 + old['bytes']]) != old['sha256']
            or compiled['symbols'] != old['symbols'] or len(helper) != old['bytes']
            or any(blob[0x5800 + old['bytes']:0x6000]) or len(helper) > 0x800):
        raise ValueError('Large furniture reader moves public or bank-owner entries')
    blob[0x5800:0x5800 + len(helper)] = helper
    expanded['expanded_code'] = compiled
    # Every old public and owner call still targets the same address.
    for row in expanded['public_entries']:
        at = row['entry'] - 0x80460000
        if blob[at:at + 8].hex() != row['after'] or row['target'] != compiled['symbols'][row['name']]:
            raise ValueError('Changed fixed furniture dispatch')
    item_code, item_report = compile_part('items_large', output / 'items_large',
        defines=ITEM_DEFINES + DEFINES + ('AF_V3_CLOTHING_PROFILE=1',
            'AF_V3_ROSTER_CLOTHING=1', 'AF_V3_MULTI_CELL_ITEMS=1'), primary_source='overlays/v3/items.c')
    if (len(item_code) > 0xFF0 or
            item_report['symbols']['af_v3_roster_clothing_record'] !=
            prior['aloha_outfits']['code']['symbols']['af_v3_roster_clothing_record']):
        raise ValueError('New shared readers lack the actual full-roster clothing dependency')
    old_extension = prior['clothing']['save_extension']
    size = old_extension['resource_bytes']
    old_extra = bytes(blob[0xF400:0xF400 + size])
    if (sha256(old_extra) != old_extension['resource_sha256']
            or struct.unpack_from('>4I', blob, 0xE0) !=
            (BLOB + 0xF400, size, zlib.crc32(old_extra), 0x8046D000)):
        raise ValueError('Changed complete clothing/save resource')
    extra = bytearray(old_extra)
    entries = []
    for name in ('name', 'type', 'size', 'place', 'price'):
        symbol = 'af_v3_item_' + name + '_extended'
        entry, target = old_extension['code']['symbols'][symbol], item_report['symbols'][symbol]
        at = entry - 0x8046D000
        if not 0x8DC <= at <= size - 8 or not HELPER_RAM <= target < HELPER_RAM + len(item_code):
            raise ValueError('Multi-cell dispatch overwrites save code or leaves its checked package')
        after = struct.pack('>2I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        entries.append({'name': symbol, 'entry': entry, 'target': target,
                        'before': extra[at:at + 8].hex(), 'after': after.hex()})
        extra[at:at + 8] = after
    allowed = {i for r in entries for i in range(r['entry'] - 0x8046D000, r['entry'] - 0x8046D000 + 8)}
    if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(old_extra, extra, strict=True))):
        raise ValueError('Multi-cell item dispatch changes unrelated codec or clothing instructions')
    blob[0xF400:0xF400 + size] = extra
    struct.pack_into('>I', blob, 0xE8, zlib.crc32(extra))
    return expanded, item_code, item_report, entries, sha256(extra)


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw, art_raw = (BASE / 'build.json').read_bytes(), (ART / 'art.json').read_bytes()
    if (sha256(base), sha256(raw), sha256(art_raw)) != (BASE_SHA, REPORT_SHA, ART_SHA):
        raise ValueError('Changed full-sized Western source cartridge, report, or assets')
    prior, art = json.loads(raw), json.loads(art_raw)
    if prior['runtime_abi'] != 65:
        raise ValueError('Full-sized Western imports require ABI 65')
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    stable = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed import-free cartridge')
    files = by_vrom(base)
    old_blob = files[BLOB].extract(base)
    blob, module, code = bytearray(old_blob), bytearray(files[MODULE].extract(base)), bytearray(files[CODE_VROM].extract(base))
    old_package = old_blob[0x70000:0x7F000]
    if (len(blob) != 0x1C20C0 or struct.unpack_from('>4I', blob, 0xF0) !=
            (BLOB + 0x70000, 0xF000, zlib.crc32(old_package), PACKAGE_RAM)
            or old_package[-16:] != bytes.fromhex('AFACC0DE') * 4
            or struct.unpack_from('>4I', old_package) != (0x41464133, 1, 0xF000, 20)
            or PACKAGE_RAM + PACKAGE_SIZE > prior['furniture']['bank_pool']['start']
            or ROWS + STATIC_COUNT * 80 > ITEMS or TABLE_END > HELPER):
        raise ValueError('Changed package identity, resident bounds, or model-bank allocation')
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    rel, symbols = donor['rel'], (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    prepared, item_rows = metadata(rel, symbols, large=True)
    evidence = identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx', large=True)
    if len(prepared) != 96 or len(item_rows) != 3 or len(art['objects']) != 3:
        raise ValueError('Incomplete full-sized Western conversion')
    output.mkdir(parents=True)
    expanded, item_code, item_report, item_entries, extra_sha = install_readers(blob, prior, output)
    rows = bytearray(old_blob[0x7E500:0x7EBE0])
    old_items = old_blob[0x7EC00:0x7EEE0]
    if (sha256(rows) != prior['western']['profile_rows_sha256']
            or sha256(old_items) != prior['western']['item_rows_sha256']
            or len(prior['furniture']['imports']) != 22):
        raise ValueError('Changed installed profile or item records')
    furniture = copy.deepcopy(prior['furniture'])
    for slot, row in enumerate(furniture['imports']):
        index, item, enabled = struct.unpack_from('>HHI', rows, slot * 80)
        before, after = 0x80481508 + slot * 80, ROWS_RAM + slot * 80 + 8
        seed = 0x5800 + index * 4
        if (row['runtime_index'] != index or row['item_id'] != f'{item:04X}' or enabled != 1
                or row['profile_ram'] != f'{before:08X}' or struct.unpack_from('>I', blob, seed)[0] != before):
            raise ValueError('Relocated furniture table changes installed identity')
        struct.pack_into('>I', blob, seed, after)
        row['profile_ram'] = f'{after:08X}'
    profile = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if blob[0x20:0xE0] != profile:
        raise ValueError('Changed current selected save profile')
    installed = []
    for pilot, model, row in zip(LARGE_WESTERN_PILOTS, art['objects'], item_rows, strict=True):
        index, item, vrom = furniture_slot(pilot.item)
        asset = (ART / model['object_file']).read_bytes()
        if (model['id'] != row['id'] or row['runtime_index'] != index or item != pilot.item
                or sha256(asset) != model['object_sha256'] or len(asset) != model['object_bytes']
                or not 0 < len(asset) <= 0x2000 or vrom % 0x2000
                or set(model['model_offsets']) != {r[0] for r in pilot.models}
                or vrom - BLOB < len(blob) or vrom - BLOB + len(asset) > PACKAGE):
            raise ValueError('Changed large Western asset, profile slots, or registry storage')
        blob.extend(bytes(vrom - BLOB - len(blob)))
        blob.extend(asset)
        native = native_profile(pilot, len(asset), model['model_offsets'], vrom)
        address = ROWS_RAM + len(rows) + 8
        rows.extend(struct.pack('>HHI', index, item, 1) + native + bytes(4))
        seed, bit = 0x5800 + index * 4, (item - 0x3000) // 4
        if any(blob[seed:seed + 4]) or profile[32 + bit // 8] & (1 << (bit & 7)):
            raise ValueError('Full-sized Western import replaces an existing selected identity')
        struct.pack_into('>I', blob, seed, address)
        profile[32 + bit // 8] |= 1 << (bit & 7)
        installed.append({**row, 'registry_version': 1, 'object_vrom': f'{vrom:08X}',
            'object_bytes': len(asset), 'object_sha256': sha256(asset),
            'profile_ram': f'{address:08X}', 'profile_sha256': sha256(native),
            'runtime_installed': True, 'enabled': True, 'selectable': False,
            'ordinary_gameplay_tested': False})
    package = bytearray(old_package + bytes(PACKAGE_SIZE - len(old_package)))
    struct.pack_into('>I', package, 8, PACKAGE_SIZE)
    package[ROWS - PACKAGE:ROWS - PACKAGE + len(rows)] = rows
    package[ITEMS - PACKAGE:TABLE_END - PACKAGE] = old_items + prepared
    package[HELPER - PACKAGE:HELPER - PACKAGE + len(item_code)] = item_code
    package[-16:] = bytes.fromhex('AFACC0DE') * 4
    blob.extend(bytes(PACKAGE - len(blob)))
    blob.extend(package)
    blob[0x20:0xE0] = profile
    struct.pack_into('>4I', blob, 0xF0, BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
    furniture['imports'].extend(installed)
    furniture['expanded_tables'] = expanded
    imports = furniture['imports'] + [{'item_id': '3350', 'runtime_index': 1236}]
    changes, cat_report = install_catalogue(base, stable, prior, imports, output, rel, symbols,
        western=True, western_large=True)
    score_changes, score_reports = score_tables(base, prior, item_rows, theme=55, extend_western=True)
    changes.update(score_changes)
    goods, table_at, stock_rows = shops.goods(stable, rel, symbols,
        [r for r in imports if r['item_id'] != '3294'], garden=True, western=True, western_large=True)
    stock = prior['shops']
    if (sha256(files[shops.VROM].extract(base)) != stock['output_sha256']
            or struct.unpack_from('>3I', code, shops.DESCRIPTOR - CODE_RAM) !=
            (shops.VROM, shops.VROM + stock['bytes'], 0x06000000 | stock['table_offset'])):
        raise ValueError('Changed native stock resource')
    struct.pack_into('>3I', code, shops.DESCRIPTOR - CODE_RAM, shops.VROM,
                     shops.VROM + len(goods), 0x06000000 | table_at)
    changes[shops.VROM] = goods
    stock_report = {**stock, 'imports': stock_rows, 'bytes': len(goods),
                   'table_offset': table_at, 'output_sha256': sha256(goods)}
    moves = []
    for vrom in (catalogue.VROM, catalogue.RELOC, hra.NEW_VROM, feng.NEW_VROM, shops.VROM):
        blob.extend(bytes(-len(blob) % 16))
        offset, data = len(blob), changes.pop(vrom)
        blob.extend(data)
        moves.append({'vrom': vrom, 'blob_offset': offset, 'bytes': len(data),
            'physical': files[BLOB].pstart + offset, 'sha256': sha256(data)})
    if (len(blob) > 0x200000 or files[BLOB].pstart + len(blob) > len(base)
            or len(base) != 0x4000000
            or any(base[files[BLOB].pstart + len(old_blob):files[BLOB].pstart + len(blob)])
            or any(e.vstart < BLOB + len(blob) and BLOB + len(old_blob) < e.vend
                   for vrom, e in files.items() if vrom != BLOB)):
        raise ValueError('Large Western allocation exceeds actual free virtual or physical storage')
    struct.pack_into('>I', blob, 4, ABI)
    startup, startup_report = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB + PACKAGE}', 'AF_V3_WESTERN_LARGE=1'))
    old_start = prior['startup']
    if (sha256(module[STARTUP:STARTUP + old_start['bytes']]) != old_start['sha256']
            or any(module[STARTUP + old_start['bytes']:CONFIG]) or len(startup) > CONFIG - STARTUP):
        raise ValueError('Changed startup or exceeded its existing reservation')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    changes.update({BLOB: blob, MODULE: module, CODE_VROM: code})
    result = bytearray(base)
    for vrom, data in changes.items():
        entry = files[vrom]
        if entry.pend or (vrom != BLOB and len(data) != entry.size):
            raise ValueError('Unexpected in-place resource allocation change')
        result[entry.pstart:entry.pstart + len(data)] = data
    struct.pack_into('>I', result, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    for row in moves:
        struct.pack_into('>4I', result, DMA_START + files[row['vrom']].index * 16,
            row['vrom'], row['vrom'] + row['bytes'], row['physical'], 0)
    fix_checksum(result)
    result = bytes(result)
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result:
        raise ValueError('Large Western cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-western-large-runtime', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        furniture=furniture, catalogue=cat_report, shops=stock_report, **score_reports,
        native_test='pending changed two-cell runtime and package checks')
    report['save_runtime'].update(profile_hex=profile.hex(), profile_sha256=sha256(profile))
    report['clothing']['save_extension'].update(resource_sha256=extra_sha,
        item_dispatch=item_entries, active_item_code=item_report)
    report['furniture_items']['imports'].extend(installed)
    report['furniture_items'].update(active_metadata_ram=f'{ITEMS_RAM:08X}', active_metadata_rows=ITEM_COUNT)
    relocated = {r['item_id']: r for r in furniture['imports']}
    for section, count in (('construction', 9), ('garden', 15), ('western', 22)):
        target = report[section]
        for row in target['imports']:
            row['profile_ram'] = relocated[row['item_id']]['profile_ram']
        target.update(profile_rows_ram=f'{ROWS_RAM:08X}', item_rows_ram=f'{ITEMS_RAM:08X}',
            profile_rows_sha256=sha256(rows[:count * 80]),
            item_rows_sha256=sha256(blob[ITEMS:ITEMS + (count + 1) * 32]),
            package_sha256=sha256(package))
    for row in report['furniture_items']['imports']:
        if row['item_id'] in relocated:
            row['profile_ram'] = relocated[row['item_id']]['profile_ram']
    report['accessory_runtime'].update(active_package_vrom=f'{BLOB + PACKAGE:08X}',
        active_package_bytes=PACKAGE_SIZE, package_sha256=sha256(package))
    report['western_large'] = {'imports': installed, 'identity_evidence': evidence,
        'art_report_sha256': ART_SHA, 'profile_rows_ram': f'{ROWS_RAM:08X}',
        'profile_rows': STATIC_COUNT, 'profile_rows_sha256': sha256(rows),
        'item_rows_ram': f'{ITEMS_RAM:08X}', 'item_rows': ITEM_COUNT,
        'item_rows_sha256': sha256(blob[ITEMS:TABLE_END]),
        'package_vrom': f'{BLOB + PACKAGE:08X}', 'package_ram': f'{PACKAGE_RAM:08X}',
        'package_bytes': PACKAGE_SIZE, 'package_sha256': sha256(package),
        'item_code': item_report, 'item_dispatch': item_entries,
        'resource_moves': moves, 'additional_permanent_ram': PACKAGE_SIZE - 0xF000,
        'additional_menu_pool': 0, 'saved_format_changed': False,
        'saved_profile_changed': True, 'older_builds_accept_new_saves': False,
        'catalogue_installed': True, 'stock_and_scoring_installed': True,
        'web_patcher_enabled': False, 'optional_composition_updated': False,
        'not_a_playtest_handoff': True,
        'pending': ['optional composition', 'native two-cell/runtime verification',
                    'ordinary acquisition, placement, and persistence']}
    report['sources'].update({p: sha256((ROOT / p).read_bytes()) for p in SOURCES})
    write_new(output / 'animal-forest-v3-asset-loader.z64', result)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({k: result[k] for k in ('runtime_abi', 'output_sha256', 'patch_sha256')}))
