"""Install the complete light-switching tent model in an experimental cartridge.

The summer-camper reward route remains separate work. Never changes a served
patcher or writes over an existing cartridge.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import DMA_START, DMA_END, by_vrom, fix_checksum, sha256, verified_rom, make_ups, apply_ups
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP, ROOT, compile_part
from v3_camping_runtime import scoring
from v3_garden_runtime import install_catalogue
from v3_import_storage import (PACKAGE, PACKAGE_RAM, PACKAGE_SIZE, ROWS, ROWS_RAM,
                               ITEMS, ITEMS_RAM, TABLE_END, END, slot)
from v3_registry import furniture_slot
import v3_catalogue as catalogue
import v3_tent_model as tent

BASE, BASE_SHA = tent.BASE, tent.BASE_SHA
REPORT_SHA = '7267629efe169d8f12a0a7cd58df65a28051d27eaab8d77f9d7322f22f26ac5a'
CALLBACKS = ROOT / 'build/v3-tent-model-callbacks-02'
CALLBACK_SHA = 'c25559956fd409f0472d259811983144257218216e1804f1cb8fde5a417f1ee8'
ABI = 69
SOURCES = ('tools/v3_tent_model_runtime.py', 'tools/v3_tent_model.py',
    'tools/v3_camping_actor_art.py', 'tools/v3_camping_items.py', 'tools/v3_camping_runtime.py',
    'tools/v3_catalogue.py', 'tools/v3_garden_runtime.py', 'tools/v3_registry.py',
    'tools/v3_import_storage.py', 'overlays/v3/catalogue.c', 'overlays/v3/catalogue.ld',
    'overlays/v3/startup.c', 'overlays/v3/tent_model.c', 'overlays/v3/tent_model.ld')


def prepared(rel, symbols):
    asset, details = tent.asset_contract(rel, symbols)
    row = {**details, 'runtime_index': details['donor_runtime_index'],
        'ordinary_stock': False, 'native_hra_hex': 'd4050600', 'series': 53,
        'native_scoring_birth_category': 3, 'surface': 0, 'feng_colour': 1,
        'feng_facing_penalty': 0}
    record = (struct.pack('>HHHBB', row['runtime_index'], 0x336C, row['price'], 0, 1)
              + row['name'].encode().ljust(16, b' ') + bytes(8))
    if (row['runtime_index'], row['item_id'], row['price'], row['footprint']) != (1243, '336C', 2550, '1x1'):
        raise ValueError('Unreviewed tent identity or native footprint')
    raw = (CALLBACKS / 'callbacks.json').read_bytes()
    if sha256(raw) != CALLBACK_SHA:
        raise ValueError('Changed complete tent callback report')
    callbacks = json.loads(raw)
    code = (CALLBACKS / 'code/code.bin').read_bytes()
    if (callbacks['source_metadata'] != details
            or callbacks['art_report_sha256'] != tent.ART_SHA
            or callbacks['object_sha256'] != sha256(asset)
            or any(sha256((ROOT / p).read_bytes()) != digest
                   for p, digest in callbacks['source_sha256'].items())):
        raise ValueError('Changed compiled tent callback prerequisites')
    native, vtable = tent.profile(furniture_slot(0x336C)[2], code, callbacks['code'])
    if native.hex() != callbacks['profile_hex'] or vtable.hex() != callbacks['vtable_hex']:
        raise ValueError('Tent profile differs from verified callback wiring')
    return asset, row, record, code, native, vtable, callbacks


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE / 'build.json').read_bytes()
    if (sha256(base), sha256(raw)) != (BASE_SHA, REPORT_SHA):
        raise ValueError('Changed complete tent integration source')
    prior = json.loads(raw)
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    stable = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed import-free translation')
    contract = tent.native_contract(original, base)
    files = by_vrom(base)
    old_blob = files[BLOB].extract(base)
    blob = bytearray(old_blob)
    package = old_blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
    if (prior['runtime_abi'] != 68 or len(base) != 0x4000000 or len(blob) != 0x24D7C0
            or struct.unpack_from('>4I', blob, 0xF0) !=
            (BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
            or sha256(package) != prior['import_storage']['package_sha256']
            or sha256(blob[ROWS:ITEMS]) != prior['import_storage']['profile_rows_sha256']
            or sha256(blob[ITEMS:TABLE_END]) != prior['import_storage']['item_rows_sha256']
            or package[-16:] != bytes.fromhex('AFACC0DE') * 4
            or len(prior['furniture']['imports']) != 32
            or prior['furniture_items']['active_metadata_rows'] != 33
            or DMA_START + (len(files) + 1) * 16 != DMA_END
            or base[DMA_END - 16:DMA_END] != bytes(16)):
        raise ValueError('Changed complete sparse-storage prerequisite')
    rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    asset, row, record, code, native, vtable, callbacks = prepared(rel, symbols)
    if callbacks['native_contract'] != contract:
        raise ValueError('Tent callbacks were built for a different native contract')
    changes, score_reports, mapping = scoring(base, prior, [row], rel, symbols, source_sha256=BASE_SHA)
    profile = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    index, item, vrom = furniture_slot(0x336C)
    i = slot(item)
    code_at = PACKAGE + tent.RAM - PACKAGE_RAM
    table_at = PACKAGE + tent.VTABLE - PACKAGE_RAM
    if (blob[0x20:0xE0] != profile or index != row['runtime_index']
            or vrom != 0x244E000 or vrom - BLOB < len(blob) or vrom + 0x2000 > END
            or len(asset) > 0x2000 or len(record) != 32
            or any(blob[ROWS + i * 80:ROWS + (i + 1) * 80])
            or any(blob[ITEMS + i * 32:ITEMS + (i + 1) * 32])
            or any(blob[0x5800 + index * 4:0x5804 + index * 4])
            or profile[32 + i // 8] & (1 << (i & 7))
            or not PACKAGE <= code_at < table_at < ROWS
            or any(blob[code_at:code_at + tent.LIMIT - tent.RAM])):
        raise ValueError('Tent object, profile, item row, or callback reservation is not unclaimed')
    blob.extend(bytes(vrom - BLOB - len(blob)))
    blob.extend(asset + bytes(0x2000 - len(asset)))
    blob[code_at:code_at + len(code)] = code
    blob[table_at:table_at + len(vtable)] = vtable
    blob[ROWS + i * 80:ROWS + (i + 1) * 80] = struct.pack('>HHI', index, item, 1) + native + bytes(4)
    blob[ITEMS + i * 32:ITEMS + (i + 1) * 32] = record
    profile[32 + i // 8] |= 1 << (i & 7)
    installed = {**row, 'registry_version': 1, 'object_vrom': f'{vrom:08X}',
        'object_bytes': len(asset), 'object_sha256': sha256(asset),
        'profile_ram': f'{ROWS_RAM + i * 80 + 8:08X}', 'profile_sha256': sha256(native),
        'item_record_sha256': sha256(record), 'runtime_installed': True, 'behaviour_installed': True,
        'enabled': True, 'selectable': False, 'ordinary_gameplay_tested': False}
    furniture = copy.deepcopy(prior['furniture'])
    furniture['imports'].append(installed)
    output.mkdir(parents=True)
    cat_changes, cat_report = install_catalogue(base, stable, prior,
        furniture['imports'] + [prior['speed_bag']], output, rel, symbols,
        western=True, western_large=True, camping=True, tent_model=True)
    changes.update(cat_changes)
    moves = []
    for v in (catalogue.VROM, catalogue.RELOC):
        blob.extend(bytes(-len(blob) % 16))
        offset, data = len(blob), changes.pop(v)
        blob.extend(data)
        moves.append({'vrom': v, 'blob_offset': offset, 'bytes': len(data),
            'physical': files[BLOB].pstart + offset, 'sha256': sha256(data)})
    for v, data in list(changes.items()):
        entry = files[v]
        if entry.pend or len(data) != entry.size:
            raise ValueError('Unexpected current-owner allocation change')
        at = entry.pstart - files[BLOB].pstart
        if 0 <= at <= len(old_blob) - len(data):
            blob[at:at + len(data)] = data
            changes.pop(v)
    blob[0x20:0xE0] = profile
    package = blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
    struct.pack_into('>I', blob, 0xF8, zlib.crc32(package))
    struct.pack_into('>I', blob, 4, ABI)
    module = bytearray(files[MODULE].extract(base))
    startup, startup_report = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB + PACKAGE}', 'AF_V3_WESTERN_LARGE=1'))
    old = prior['startup']
    if (sha256(module[STARTUP:STARTUP + old['bytes']]) != old['sha256']
            or any(module[STARTUP + old['bytes']:CONFIG]) or len(startup) > CONFIG - STARTUP):
        raise ValueError('Changed startup reservation')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    extension_start = files[BLOB].pstart + len(old_blob)
    extension_end = files[BLOB].pstart + len(blob)
    if (BLOB + len(blob) > END or extension_end > len(base) or any(base[extension_start:extension_end])
            or any(e.pstart < extension_end and extension_start < (e.pend or e.pstart + e.size)
                   for v, e in files.items() if v != BLOB and e.pstart != 0xFFFFFFFF)
            or any(e.vstart < BLOB + len(blob) and BLOB + len(old_blob) < e.vend
                   for v, e in files.items() if v != BLOB)):
        raise ValueError('Tent allocation overlaps virtual or physical resources')
    changes.update({BLOB: blob, MODULE: module})
    result = bytearray(base)
    for v, data in changes.items():
        result[files[v].pstart:files[v].pstart + len(data)] = data
    struct.pack_into('>I', result, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    for move in moves:
        struct.pack_into('>4I', result, DMA_START + files[move['vrom']].index * 16,
            move['vrom'], move['vrom'] + move['bytes'], move['physical'], 0)
    fix_checksum(result)
    result = bytes(result)
    if len(by_vrom(result)) != len(files) or result[DMA_END - 16:DMA_END] != bytes(16):
        raise ValueError('Tent import changes directory count or sole terminator')
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result:
        raise ValueError('Tent cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-tent-model-runtime', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        furniture=furniture, catalogue=cat_report, **score_reports,
        native_test='pending current tent callback and item-reader execution')
    report['save_runtime'].update(profile_hex=profile.hex(), profile_sha256=sha256(profile))
    report['furniture_items']['imports'].append(installed)
    report['furniture_items']['active_metadata_rows'] = 34
    for section in ('construction', 'garden', 'western', 'western_large', 'accessory_runtime', 'camping'):
        report[section]['package_sha256'] = sha256(package)
    report['import_storage'].update(remaining_bytes=END - BLOB - len(blob),
        package_sha256=sha256(package), static_installed=33, items_installed=34,
        profile_rows_sha256=sha256(blob[ROWS:ITEMS]), item_rows_sha256=sha256(blob[ITEMS:TABLE_END]),
        saved_profile_changed=True)
    report['tent_model'] = {'imports': [installed], 'code': callbacks['code'],
        'callback_report_sha256': CALLBACK_SHA, 'native_contract': contract,
        'vtable_ram': tent.VTABLE, 'vtable_hex': vtable.hex(),
        'art_report_sha256': tent.ART_SHA, 'scoring_mapping': mapping, 'resource_moves': moves,
        'package_sha256': sha256(package), 'additional_resident_bytes': 0, 'ordinary_heap_growth': 0,
        'saved_format_changed': False, 'saved_profile_changed': True,
        'acquisition_installed': False, 'ordinary_stock_unchanged': True,
        'web_patcher_enabled': False, 'not_a_playtest_handoff': True,
        'pending': ['summer-camper acquisition adapter', 'ordinary placement, interaction, and persistence']}
    report['sources'].update({p: sha256((ROOT / p).read_bytes()) for p in SOURCES})
    write_new(output / 'animal-forest-v3-asset-loader.z64', result)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    report = build(parser.parse_args().output)
    print(json.dumps({'abi': ABI, 'sha256': report['output_sha256'],
        'remaining_bytes': report['import_storage']['remaining_bytes']}))
