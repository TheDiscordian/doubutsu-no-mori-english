"""Install seven complete construction objects and scalable native item readers.

This is an integration cartridge, not a playable handoff or web-patcher update.
Ordinary stock and the expanded catalogue are a following combined integration.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import DMA_START, apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_clothing_items import DEFINES as ITEM_DEFINES
from v3_construction_items import metadata
from v3_furniture_art import CONSTRUCTION_PILOTS, native_profile
from v3_import_catalog import read_donor
from v3_registry import furniture_slot
from v3_save_clothing import DEFINES as SAVE_DEFINES

ABI = 61
BASE = ROOT / 'build/v3-house-markers-01'
BASE_SHA = '55a715831671c989aa465fbf6d04c49caa975a761105ffa1f3acecd10ac7b8cf'
REPORT_SHA = 'adb6c52ed51b3606cf86f07febc459d31cc15bad6fc69459c612aec4130a53a3'
ART = ROOT / 'build/v3-construction-art-02'
ART_SHA = 'd2ca46dd3dff8dde4243a69c5e0fc44df66a27df3caf396681ddf58dc4311197'
PACKAGE, PACKAGE_RAM, PACKAGE_SIZE = 0x70000, 0x80473000, 0xF000
ROWS, ITEMS, TABLE_END = 0x7E500, 0x7E800, 0x7E940
ROWS_RAM, ITEMS_RAM = 0x80481500, 0x80481800
SOURCES = ('tools/v3_construction_runtime.py', 'tools/v3_construction_items.py',
           'tools/v3_furniture_art.py', 'tools/v3_registry.py', 'tools/v3_asset_loader.py',
           'overlays/v3/construction.h', 'overlays/v3/furniture.c',
           'overlays/v3/furniture_expanded.ld', 'overlays/v3/furniture_entry.S',
           'overlays/v3/items.c', 'overlays/v3/save_codec.c', 'overlays/v3/save_clothing.ld',
           'overlays/v3/startup.c', 'overlays/v3/startup.ld')


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    image = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw_report = (BASE / 'build.json').read_bytes()
    raw_art = (ART / 'art.json').read_bytes()
    if (sha256(image) != BASE_SHA or sha256(raw_report) != REPORT_SHA or sha256(raw_art) != ART_SHA):
        raise ValueError('Changed construction parent or complete converted assets')
    prior, art = json.loads(raw_report), json.loads(raw_art)
    if prior['runtime_abi'] != 60 or prior['output_sha256'] != BASE_SHA:
        raise ValueError('Changed current runtime contract')
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    files = by_vrom(image)
    original_blob = files[BLOB].extract(image)
    blob = bytearray(original_blob)
    module = bytearray(files[MODULE].extract(image))
    if (len(blob) != 0x132DD0 or files[BLOB].pend or files[MODULE].pend
            or any(blob[ROWS:TABLE_END]) or ITEMS + 10 * 32 != TABLE_END
            or ROWS + 9 * 80 > ITEMS):
        raise ValueError('Changed resident construction reservation')
    if struct.unpack_from('>4I', blob, 0xF0) != (
            BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]), PACKAGE_RAM):
        raise ValueError('Changed complete resident package descriptor')
    if blob[PACKAGE + PACKAGE_SIZE - 16:PACKAGE + PACKAGE_SIZE] != bytes.fromhex('AFACC0DE') * 4:
        raise ValueError('Changed final package guard')
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    new_metadata, item_rows = metadata(donor['rel'], symbols)
    furniture = copy.deepcopy(prior['furniture'])
    expanded = furniture['expanded_tables']
    output.mkdir(parents=True)
    helper, compiled = compile_part('furniture_expanded', output / 'furniture_expanded',
        defines=('AF_V3_FURNITURE_TABLES=1', 'AF_V3_CLOTHING_DISPLAY=1',
                 'AF_V3_SPEED_BAG=1', 'AF_V3_ALOHA_DISPLAY=1', 'AF_V3_CONSTRUCTION_ITEMS=1'),
        extra_sources=('overlays/v3/furniture_entry.S',), primary_source='overlays/v3/furniture.c')
    old = expanded['expanded_code']
    if (sha256(blob[0x5800:0x5800 + old['bytes']]) != old['sha256']
            or any(blob[0x5800 + old['bytes']:0x6000]) or not 0 < len(helper) <= 0x800):
        raise ValueError('Expanded static finder overwrites a changed owner')
    blob[0x5800:0x6000] = helper + bytes(0x800 - len(helper))
    for row in expanded['public_entries']:
        at = row['entry'] - 0x80460000
        if blob[at:at + 8].hex() != row['after']:
            raise ValueError('Changed public furniture forwarding entry')
        row['target'] = compiled['symbols'][row['name']]
        after = struct.pack('>II', 0x08000000 | (row['target'] >> 2 & 0x3FFFFFF), 0)
        blob[at:at + 8] = after
        row['after'] = after.hex()
    expanded['expanded_code'] = compiled

    # The actual current shared item readers live with the clothing codec.
    # Keep all public addresses and the codec itself; only the item table moves.
    extra, extra_compiled = compile_part('save_clothing', output / 'save_clothing',
        defines=SAVE_DEFINES + ITEM_DEFINES + ('AF_V3_SPEED_BAG=1', 'AF_V3_CONSTRUCTION_ITEMS=1'),
        primary_source='overlays/v3/save_codec.c', extra_sources=('overlays/v3/items.c',))
    old_extra = prior['clothing']['save_extension']['code']
    extra_at = 0xF400
    source_extra = bytearray(blob[extra_at:extra_at + old_extra['bytes']])
    clothing_hook = next(r for r in prior['aloha_outfits']['hooks'] if r['address'] == '8046D7D8')
    if source_extra[0x7D8:0x7E0].hex() != clothing_hook['after']:
        raise ValueError('Changed complete-roster clothing bridge')
    source_extra[0x7D8:0x7E0] = bytes.fromhex(clothing_hook['before'])
    reader_fixes = prior['aloha_outfits']['reader_fixes']
    for fix in reader_fixes:
        at = int(fix['address'], 16) - 0x8046D000
        if source_extra[at:at + 4].hex() != fix['after']:
            raise ValueError('Changed applied complete-roster item reader')
        source_extra[at:at + 4] = bytes.fromhex(fix['before'])
    if (sha256(source_extra) != old_extra['sha256'] or len(extra) != old_extra['bytes']
            or extra_compiled['symbols'] != old_extra['symbols']
            or extra[:0x7D8] != source_extra[:0x7D8]
            or extra[0x7D8:0x7E0].hex() != clothing_hook['before']):
        raise ValueError('Construction item readers change codec code or public addresses')
    extra = bytearray(extra)
    extra[0x7D8:0x7E0] = bytes.fromhex(clothing_hook['after'])
    for fix in reader_fixes:
        at = int(fix['address'], 16) - 0x8046D000
        if extra[at:at + 4].hex() != fix['before']:
            raise ValueError('Construction readers moved a required clothing fix')
        extra[at:at + 4] = bytes.fromhex(fix['after'])
    extra.extend(bytes((-len(extra)) % 16))
    old_descriptor = struct.unpack_from('>4I', blob, 0xE0)
    if old_descriptor != (BLOB + extra_at, len(extra),
                          zlib.crc32(blob[extra_at:extra_at + len(extra)]), 0x8046D000):
        raise ValueError('Changed item/codec resource descriptor')
    blob[extra_at:extra_at + len(extra)] = extra
    struct.pack_into('>I', blob, 0xE8, zlib.crc32(extra))

    rows = bytearray()
    for slot, row in enumerate(furniture['imports']):
        old_at = int(row['profile_ram'], 16) - 0x80460000 - 8
        record = original_blob[old_at:old_at + 80]
        if struct.unpack_from('>HHI', record) != (row['runtime_index'], int(row['item_id'], 16), 1):
            raise ValueError('Changed existing static furniture profile')
        rows.extend(record)
        seed = 0x5800 + row['runtime_index'] * 4
        if struct.unpack_from('>I', blob, seed)[0] != 0x80460000 + old_at + 8:
            raise ValueError('Changed original furniture profile seed')
        row['profile_ram'] = f'{ROWS_RAM + slot * 80 + 8:08X}'
        struct.pack_into('>I', blob, seed, ROWS_RAM + slot * 80 + 8)
    if len(rows) != 160 or len(art['objects']) != 7:
        raise ValueError('Changed original or construction static roster')
    profile = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if blob[0x20:0xE0] != profile or len(profile) != 192:
        raise ValueError('Changed complete current save profile')
    assets, installed = [], []
    for pilot, model, item_row in zip(CONSTRUCTION_PILOTS, art['objects'], item_rows, strict=True):
        index, item, vrom = furniture_slot(pilot.item)
        data = (ART / model['object_file']).read_bytes()
        if (model['id'] != item_row['id'] or index != item_row['runtime_index'] or item != pilot.item
                or sha256(data) != model['object_sha256'] or len(data) != model['object_bytes']
                or not 0 < len(data) <= 0x1000 or vrom % 0x1000
                or set(model['model_offsets']) != {'opaque'}):
            raise ValueError('Changed converted construction object or fixed allocation')
        at = vrom - BLOB
        if at < len(blob) or at + len(data) > 0x200000:
            raise ValueError('Construction object overlaps installed ROM storage')
        blob.extend(bytes(at - len(blob)))
        blob.extend(data)
        native = native_profile(pilot, len(data), model['model_offsets'], vrom)
        profile_ram = ROWS_RAM + len(rows) + 8
        rows.extend(struct.pack('>HHI', index, item, 1) + native + bytes(4))
        seed = 0x5800 + index * 4
        bit = (item - 0x3000) // 4
        if any(blob[seed:seed + 4]) or profile[32 + bit // 8] & (1 << (bit & 7)):
            raise ValueError('Construction identity replaces an existing profile or selected bit')
        struct.pack_into('>I', blob, seed, profile_ram)
        profile[32 + bit // 8] |= 1 << (bit & 7)
        record = {**item_row, 'registry_version': 1, 'object_vrom': f'{vrom:08X}',
            'object_bytes': len(data), 'object_sha256': sha256(data),
            'profile_ram': f'{profile_ram:08X}', 'profile_sha256': sha256(native),
            'runtime_installed': True, 'enabled': True, 'selectable': False,
            'ordinary_gameplay_tested': False}
        installed.append(record)
        assets.append({'vrom': f'{vrom:08X}', 'bytes': len(data), 'sha256': sha256(data)})
    if len(rows) != 9 * 80 or len(new_metadata) != 7 * 32:
        raise ValueError('Construction table size changed')
    blob[ROWS:ROWS + len(rows)] = rows
    blob[ITEMS:TABLE_END] = original_blob[0x72A0:0x7300] + new_metadata
    blob[0x20:0xE0] = profile
    struct.pack_into('>I', blob, 4, ABI)
    struct.pack_into('>I', blob, 0xF8, zlib.crc32(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]))
    furniture['imports'].extend(installed)

    startup, startup_report = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', 'AF_V3_ACCESSORY_BYTES=61440'))
    old_start = prior['startup']
    if (sha256(module[STARTUP:STARTUP + old_start['bytes']]) != old_start['sha256']
            or any(module[STARTUP + old_start['bytes']:CONFIG]) or len(startup) > CONFIG - STARTUP):
        raise ValueError('Changed bounded startup code')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    old_end, new_end = files[BLOB].pstart + len(original_blob), files[BLOB].pstart + len(blob)
    if new_end > len(image) or len(image) != 0x4000000 or any(image[old_end:new_end]):
        raise ValueError('Construction assets exceed verified physical padding or 64-MiB limit')
    if any(e.vstart < BLOB + len(blob) and BLOB + len(original_blob) < e.vend
           for vrom, e in files.items() if vrom != BLOB):
        raise ValueError('Construction append overlaps another virtual resource')
    result = bytearray(image)
    result[files[BLOB].pstart:new_end] = blob
    result[files[MODULE].pstart:files[MODULE].pstart + len(module)] = module
    struct.pack_into('>I', result, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    fix_checksum(result)
    result = bytes(result)
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result:
        raise ValueError('Construction cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-construction-runtime', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), rom_bytes=len(result),
        startup=startup_report, furniture=furniture,
        native_test='pending construction loader and shared-reader checks')
    report['save_runtime'].update(profile_hex=profile.hex(), profile_sha256=sha256(profile))
    report['clothing']['save_extension'].update(code=extra_compiled, resource_sha256=sha256(extra))
    report['furniture_items']['imports'].extend(item_rows)
    report['furniture_items'].update(active_metadata_ram=f'{ITEMS_RAM:08X}', active_metadata_rows=10)
    report['construction'] = {'imports': installed, 'assets': assets, 'art_report_sha256': ART_SHA,
        'profile_rows_ram': f'{ROWS_RAM:08X}', 'profile_rows': 9, 'profile_rows_sha256': sha256(rows),
        'item_rows_ram': f'{ITEMS_RAM:08X}', 'item_rows': 10,
        'item_rows_sha256': sha256(blob[ITEMS:TABLE_END]),
        'package_sha256': sha256(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]),
        'additional_ram_allocation': 0, 'rom_bytes': len(result),
        'saved_format_changed': False, 'saved_profile_changed': True,
        'older_builds_accept_new_saves': False, 'ordinary_stock_installed': False,
        'catalogue_installed': False, 'scoring_installed': False,
        'web_patcher_enabled': False, 'not_a_playtest_handoff': True,
        'pending': ['ordinary stock and expanded catalogue', 'scoring tables',
                    'optional composition', 'ordinary placement and persistence']}
    report['sources'].update({p: sha256((ROOT / p).read_bytes()) for p in SOURCES})
    write_new(output / 'animal-forest-v3-asset-loader.z64', result)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    report = build(parser.parse_args().output)
    print(json.dumps({key: report[key] for key in ('runtime_abi', 'output_sha256', 'patch_sha256')}))
