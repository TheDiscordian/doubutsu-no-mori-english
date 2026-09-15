"""Expand import storage and install fixed metadata slots; leave both patchers V2."""
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
from v3_clothing_items import DEFINES as ITEM_DEFINES
from v3_furniture_runtime import VROM as ROOM, RAM as ROOM_RAM

ABI = 67
BASE = ROOT / 'build/v3-western-large-runtime-01'
BASE_SHA = '5c51f80525a253e889a38b4ed4730df7e21b9a5e63a80917f0406b512faaebfe'
REPORT_SHA = 'ce78cdb3f8fe717679fd8b74bf92cadb11cec19fc0f6abbe8b6b26284946547e'
CHOICE_OLD, CHOICE_NEW, CHOICE_READER = 0x02400000, 0x025F0000, 0x80065614
END = CHOICE_NEW
PACKAGE, PACKAGE_RAM, PACKAGE_SIZE = 0x200000, 0x80473000, 0x2D010
ROWS, ROWS_RAM = PACKAGE + 0x11000, 0x80484000
ITEMS, ITEMS_RAM = PACKAGE + 0x25000, 0x80498000
SLOTS, TABLE_END = 1024, ITEMS + 1024 * 32
DEFINES = ('AF_V3_CONSTRUCTION_ITEMS=1', 'AF_V3_WESTERN_LARGE=1',
           'AF_V3_SPARSE_FURNITURE=1')
SOURCES = ('tools/v3_import_storage.py', 'tools/v3_asset_loader.py',
    'overlays/v3/sparse_furniture.h', 'overlays/v3/construction.h',
    'overlays/v3/furniture.c', 'overlays/v3/furniture_expanded.ld',
    'overlays/v3/furniture_tables.c', 'overlays/v3/furniture_tables.ld',
    'overlays/v3/items.c', 'overlays/v3/items_large.ld',
    'overlays/v3/startup.c', 'overlays/v3/accessory.h')


def slot(item):
    if type(item) is not int or not 0x3000 <= item <= 0x3FFC or item & 3:
        raise ValueError('Sparse furniture requires a canonical 3xxx identity')
    return (item - 0x3000) // 4


def jump(target, *, link=False):
    return (0x0C000000 if link else 0x08000000) | ((target >> 2) & 0x3FFFFFF)


def replace_checked(data, at, before, after):
    if not before or len(before) != len(after) or not 0 <= at <= len(data) - len(before) or data[at:at + len(before)] != before:
        raise ValueError(f'Changed storage prerequisite at {at:08X}')
    data[at:at + len(before)] = after


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base, raw = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes(), (BASE / 'build.json').read_bytes()
    if (sha256(base), sha256(raw)) != (BASE_SHA, REPORT_SHA):
        raise ValueError('Changed complete ABI-66 source cartridge or report')
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    prior = json.loads(raw)
    files = by_vrom(base)
    old_blob = files[BLOB].extract(base)
    old_package = old_blob[0x1CA000:0x1DB000]
    if (prior['runtime_abi'] != 66 or len(base) != 0x4000000 or len(old_blob) != 0x1F44F0
            or struct.unpack_from('>4I', old_blob, 0xF0) !=
            (0x023CA000, 0x11000, zlib.crc32(old_package), PACKAGE_RAM)
            or sha256(old_package) != prior['accessory_runtime']['package_sha256']
            or old_package[-16:] != bytes.fromhex('AFACC0DE') * 4
            or PACKAGE_RAM + PACKAGE_SIZE > prior['furniture']['bank_pool']['start']
            or DMA_START + (len(files) + 1) * 16 != DMA_END
            or base[DMA_END - 16:DMA_END] != bytes(16)):
        raise ValueError('Changed package, directory terminator, or memory reservation')
    blob = bytearray(old_blob + bytes(PACKAGE + PACKAGE_SIZE - len(old_blob)))
    package = bytearray(old_package + bytes(PACKAGE_SIZE - len(old_package)))
    struct.pack_into('>I', package, 8, PACKAGE_SIZE)
    rows, items = bytearray(SLOTS * 80), bytearray(SLOTS * 32)
    relocated = {}
    for n, record in enumerate(prior['furniture']['imports']):
        row = old_blob[0x1D9000 + n * 80:0x1D9000 + (n + 1) * 80]
        index, item, active = struct.unpack_from('>HHI', row)
        i = slot(item)
        old_address = 0x80482008 + n * 80
        address = ROWS_RAM + i * 80 + 8
        if (record['runtime_index'] != index or index != 1024 + i or active != 1
                or record['item_id'] != f'{item:04X}' or int(record['profile_ram'], 16) != old_address
                or any(rows[i * 80:(i + 1) * 80])):
            raise ValueError('Changed static profile identity or duplicate sparse slot')
        replace_checked(blob, 0x5800 + index * 4, struct.pack('>I', old_address), bytes(4))
        rows[i * 80:(i + 1) * 80] = row
        relocated[record['item_id']] = f'{address:08X}'
    for n in range(26):
        row = old_blob[0x1D9800 + n * 32:0x1D9800 + (n + 1) * 32]
        index, item = struct.unpack_from('>HH', row)
        i = slot(item)
        if index != 1024 + i or row[7] != 1 or any(items[i * 32:(i + 1) * 32]):
            raise ValueError('Changed item identity or duplicate sparse slot')
        items[i * 32:(i + 1) * 32] = row
    package[ROWS - PACKAGE:ITEMS - PACKAGE] = rows
    package[ITEMS - PACKAGE:TABLE_END - PACKAGE] = items
    package[-16:] = bytes.fromhex('AFACC0DE') * 4
    output.mkdir(parents=True)
    helper, helper_report = compile_part('furniture_expanded', output / 'furniture_expanded',
        defines=DEFINES + ('AF_V3_FURNITURE_TABLES=1', 'AF_V3_CLOTHING_DISPLAY=1',
            'AF_V3_SPEED_BAG=1', 'AF_V3_ALOHA_DISPLAY=1', 'AF_V3_EXPANDED_BANKS=1'),
        primary_source='overlays/v3/furniture.c', extra_sources=('overlays/v3/furniture_entry.S',))
    expanded = copy.deepcopy(prior['furniture']['expanded_tables'])
    old = expanded['expanded_code']
    if sha256(blob[0x5800:0x5800 + old['bytes']]) != old['sha256'] or any(blob[0x5800 + old['bytes']:0x6000]):
        raise ValueError('Changed expanded furniture code reservation')
    blob[0x5800:0x6000] = helper + bytes(0x800 - len(helper))
    for row in expanded['public_entries']:
        target = helper_report['symbols'][row['name']]
        after = struct.pack('>2I', jump(target), 0)
        replace_checked(blob, row['entry'] - 0x80460000, bytes.fromhex(row['after']), after)
        row.update(before=row['after'], after=after.hex(), target=target)
    room = bytearray(files[ROOM].extract(base))
    banks = copy.deepcopy(prior['furniture']['bank_pool'])
    hook = banks['hook']
    if sha256(room) != banks['output_owner_sha256']:
        raise ValueError('Changed dedicated model-bank owner')
    before = bytes.fromhex(hook['after'])
    if struct.unpack_from('>I', before, 4)[0] != jump(old['symbols']['af_v3_furniture_secure_banks'], link=True):
        raise ValueError('Unbound model-bank owner call')
    after = before[:4] + struct.pack('>I', jump(helper_report['symbols']['af_v3_furniture_secure_banks'], link=True)) + before[8:]
    replace_checked(room, hook['address'] - ROOM_RAM, before, after)
    hook.update(before=before.hex(), after=after.hex())
    banks.update(source_owner_sha256=banks['output_owner_sha256'], output_owner_sha256=sha256(room))
    expanded.update(expanded_code=helper_report, output_sha256=sha256(room))
    initializer, init_report = compile_part('furniture_tables', output / 'furniture_tables',
        defines=('AF_V3_SPARSE_FURNITURE=1', 'AF_V3_CLOTHING_DISPLAY=1', 'AF_V3_ALOHA_DISPLAY=1'))
    old = expanded['initializer']
    if sha256(blob[0xA000:0xA000 + old['bytes']]) != old['sha256'] or any(blob[0xA000 + old['bytes']:0xA200]):
        raise ValueError('Changed complete table initializer reservation')
    blob[0xA000:0xA200] = initializer + bytes(0x200 - len(initializer))
    expanded['initializer'] = init_report
    code, item_report = compile_part('items_large', output / 'items_large',
        defines=ITEM_DEFINES + DEFINES + ('AF_V3_CLOTHING_PROFILE=1',
            'AF_V3_ROSTER_CLOTHING=1', 'AF_V3_MULTI_CELL_ITEMS=1'), primary_source='overlays/v3/items.c')
    package[0x10000:0x10FF0] = code + bytes(0xFF0 - len(code))
    extra = prior['clothing']['save_extension']
    size = extra['resource_bytes']
    if sha256(blob[0xF400:0xF400 + size]) != extra['resource_sha256']:
        raise ValueError('Changed actual saved-format codec and item dispatch')
    dispatch = copy.deepcopy(extra['item_dispatch'])
    for row in dispatch:
        target = item_report['symbols'][row['name']]
        after = struct.pack('>2I', jump(target), 0)
        replace_checked(blob, 0xF400 + row['entry'] - 0x8046D000, bytes.fromhex(row['after']), after)
        row.update(before=row['after'], after=after.hex(), target=target)
    struct.pack_into('>I', blob, 0xE8, zlib.crc32(blob[0xF400:0xF400 + size]))
    blob[PACKAGE:PACKAGE + PACKAGE_SIZE] = package
    struct.pack_into('>4I', blob, 0xF0, BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
    struct.pack_into('>I', blob, 4, ABI)
    startup, startup_report = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB + PACKAGE}', 'AF_V3_WESTERN_LARGE=1'))
    module = bytearray(files[MODULE].extract(base))
    old = prior['startup']
    if sha256(module[STARTUP:STARTUP + old['bytes']]) != old['sha256'] or any(module[STARTUP + old['bytes']:CONFIG]):
        raise ValueError('Changed current startup reservation')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    game = bytearray(files[CODE_VROM].extract(base))
    replace_checked(game, CHOICE_READER - CODE_RAM, bytes.fromhex('3c18024027180000'), bytes.fromhex('3c18025f27180000'))
    extension_start, extension_end = files[BLOB].pstart + len(old_blob), files[BLOB].pstart + len(blob)
    if (BLOB + len(blob) > END or extension_end > len(base) or any(base[extension_start:extension_end])
            or any(e.pstart < extension_end and extension_start < (e.pend or e.pstart + e.size)
                   for v, e in files.items() if v != BLOB and e.pstart != 0xFFFFFFFF)
            or any(e.vstart < END and BLOB < e.vend for v, e in files.items() if v not in (BLOB, CHOICE_OLD))
            or any(e.vstart < CHOICE_NEW + files[CHOICE_OLD].size and CHOICE_NEW < e.vend
                   for v, e in files.items() if v != CHOICE_OLD)):
        raise ValueError('Storage expansion overlaps actual virtual or physical resources')
    result = bytearray(base)
    for vrom, data in ((BLOB, blob), (MODULE, module), (ROOM, room), (CODE_VROM, game)):
        entry = files[vrom]
        if entry.pend or (vrom != BLOB and len(data) != entry.size):
            raise ValueError('Unexpected in-place allocation change')
        result[entry.pstart:entry.pstart + len(data)] = data
    struct.pack_into('>I', result, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    struct.pack_into('>2I', result, DMA_START + files[CHOICE_OLD].index * 16,
                     CHOICE_NEW, CHOICE_NEW + files[CHOICE_OLD].size)
    fix_checksum(result)
    result = bytes(result)
    installed = by_vrom(result)
    if (len(installed) != len(files) or result[DMA_END - 16:DMA_END] != bytes(16)
            or installed[CHOICE_NEW].extract(result) != files[CHOICE_OLD].extract(base)):
        raise ValueError('Choice relocation changes file count, terminator, or text')
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result:
        raise ValueError('Expanded cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-import-storage', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        native_test='pending changed storage and sparse-table verification')
    report['furniture'].update(expanded_tables=expanded, bank_pool=banks)
    for section in ('furniture', 'furniture_items', 'construction', 'garden', 'western', 'western_large'):
        for row in report[section]['imports']:
            if row['item_id'] in relocated:
                row['profile_ram'] = relocated[row['item_id']]
    for section, count in (('construction', 9), ('garden', 15), ('western', 22), ('western_large', 25)):
        target = report[section]
        selected_rows = report['furniture']['imports'][:count]
        target.update(profile_rows_ram=f'{ROWS_RAM:08X}', item_rows_ram=f'{ITEMS_RAM:08X}',
            profile_layout='canonical-sparse-1024',
            profile_rows_sha256=sha256(b''.join(rows[slot(int(r['item_id'], 16)) * 80:slot(int(r['item_id'], 16)) * 80 + 80] for r in selected_rows)),
            item_rows_sha256=sha256(b''.join(items[slot(int(r['item_id'], 16)) * 32:slot(int(r['item_id'], 16)) * 32 + 32] for r in selected_rows + [report['speed_bag']])),
            package_sha256=sha256(package))
    report['furniture_items'].update(active_metadata_ram=f'{ITEMS_RAM:08X}', active_metadata_rows=26,
                                    metadata_capacity=SLOTS, metadata_layout='canonical-sparse-1024')
    report['accessory_runtime'].update(active_package_vrom=f'{BLOB + PACKAGE:08X}',
        active_package_bytes=PACKAGE_SIZE, package_sha256=sha256(package))
    report['western_large'].update(package_vrom=f'{BLOB + PACKAGE:08X}',
        package_ram=f'{PACKAGE_RAM:08X}', package_bytes=PACKAGE_SIZE,
        item_code=item_report, item_dispatch=dispatch)
    report['clothing']['save_extension'].update(resource_sha256=sha256(blob[0xF400:0xF400 + size]),
        active_item_code=item_report, item_dispatch=dispatch)
    report['import_storage'] = {'virtual_start': BLOB, 'virtual_limit': END,
        'remaining_bytes': END - BLOB - len(blob), 'directory_entries': len(installed),
        'choice_vrom': CHOICE_NEW, 'choice_prior_vrom': CHOICE_OLD,
        'choice_bytes': files[CHOICE_OLD].size, 'choice_sha256': sha256(files[CHOICE_OLD].extract(base)),
        'choice_reader': CHOICE_READER, 'package_vrom': BLOB + PACKAGE,
        'package_ram': PACKAGE_RAM, 'package_bytes': PACKAGE_SIZE, 'package_sha256': sha256(package),
        'profile_rows_ram': ROWS_RAM, 'item_rows_ram': ITEMS_RAM, 'slots': SLOTS,
        'static_installed': 25, 'items_installed': 26, 'profile_rows_sha256': sha256(rows),
        'item_rows_sha256': sha256(items), 'item_code': item_report,
        'additional_resident_bytes': PACKAGE_SIZE - len(old_package), 'ordinary_heap_growth': 0,
        'saved_format_changed': False, 'saved_profile_changed': False,
        'web_patcher_enabled': False, 'not_a_playtest_handoff': True}
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
