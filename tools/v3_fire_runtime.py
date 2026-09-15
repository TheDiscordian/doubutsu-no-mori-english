"""Install both complete fires, four-cell placement, and native callback loading.

Experimental cartridge only; never changes either served web patcher.
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
    ITEMS, TABLE_END, END, slot, DEFINES, ROOM, ROOM_RAM, replace_checked, jump)
from v3_registry import furniture_slot
from v3_four_cell_items import DEFINES as ITEM_DEFINES, source_evidence
import v3_catalogue as catalogue
import v3_fire as fire

BASE, BASE_SHA = fire.BASE, fire.BASE_SHA
REPORT_SHA = '75894b4b5a77b31ffcc34e32766d38abc6a65c899326b0aaa8e66413a246e7ce'
CALLBACKS = ROOT / 'build/v3-fire-callbacks-05'
CALLBACK_SHA = 'fd4c5741b54f83795c5e29a90ce0c5ae5ca870f60430a8fb31dd056070bcafab'
ABI = 70
SOURCES = ('tools/v3_fire_runtime.py', 'tools/v3_fire.py', 'tools/v3_four_cell_items.py',
    'tools/v3_registry.py', 'tools/v3_catalogue.py', 'tools/v3_garden_runtime.py',
    'overlays/v3/fire.c', 'overlays/v3/fire.ld', 'overlays/v3/furniture.c',
    'overlays/v3/items.c', 'overlays/v3/catalogue.c', 'overlays/v3/startup.c')


def install_readers(base, prior, blob, output, original, rel, symbols):
    evidence = source_evidence(original, rel, symbols)
    code, compiled = compile_part('items_large', output / 'items', defines=ITEM_DEFINES,
        primary_source='overlays/v3/items.c')
    old = prior['import_storage']['item_code']
    at = PACKAGE + 0x10000
    if (sha256(blob[at:at + old['bytes']]) != old['sha256']
            or any(blob[at + old['bytes']:at + 0x400]) or len(code) > 0x400):
        raise ValueError('Four-cell reader conflicts with the installed tent callbacks')
    blob[at:at + 0x400] = code + bytes(0x400 - len(code))
    extra = copy.deepcopy(prior['clothing']['save_extension'])
    size = extra['resource_bytes']
    if sha256(blob[0xF400:0xF400 + size]) != extra['resource_sha256']:
        raise ValueError('Changed actual item-dispatch resource')
    for row in extra['item_dispatch']:
        target = compiled['symbols'][row['name']]
        after = struct.pack('>2I', jump(target), 0)
        replace_checked(blob, 0xF400 + row['entry'] - 0x8046D000, bytes.fromhex(row['after']), after)
        row.update(before=row['after'], after=after.hex(), target=target)
    extra['resource_sha256'] = sha256(blob[0xF400:0xF400 + size])
    struct.pack_into('>I', blob, 0xE8, zlib.crc32(blob[0xF400:0xF400 + size]))
    helper, helper_report = compile_part('furniture_expanded', output / 'furniture_expanded',
        defines=DEFINES + ('AF_V3_FURNITURE_TABLES=1', 'AF_V3_CLOTHING_DISPLAY=1',
            'AF_V3_SPEED_BAG=1', 'AF_V3_ALOHA_DISPLAY=1', 'AF_V3_EXPANDED_BANKS=1',
            'AF_V3_TENT_MODEL=1', 'AF_V3_FIRE=1'),
        primary_source='overlays/v3/furniture.c', extra_sources=('overlays/v3/furniture_entry.S',))
    expanded = copy.deepcopy(prior['furniture']['expanded_tables'])
    old = expanded['expanded_code']
    if (sha256(blob[0x5800:0x5800 + old['bytes']]) != old['sha256']
            or any(blob[0x5800 + old['bytes']:0x6000]) or len(helper) > 0x800):
        raise ValueError('Changed furniture helper or insufficient existing reservation')
    blob[0x5800:0x6000] = helper + bytes(0x800 - len(helper))
    for row in expanded['public_entries']:
        target = helper_report['symbols'][row['name']]
        after = struct.pack('>2I', jump(target), 0)
        replace_checked(blob, row['entry'] - 0x80460000, bytes.fromhex(row['after']), after)
        row.update(before=row['after'], after=after.hex(), target=target)
    room = bytearray(by_vrom(base)[ROOM].extract(base))
    banks = copy.deepcopy(prior['furniture']['bank_pool'])
    hook = banks['hook']
    before = bytes.fromhex(hook['after'])
    if (sha256(room) != banks['output_owner_sha256'] or
            struct.unpack_from('>I', before, 4)[0] != jump(old['symbols']['af_v3_furniture_secure_banks'], link=True)):
        raise ValueError('Changed complete native model-bank owner')
    after = before[:4] + struct.pack('>I', jump(helper_report['symbols']['af_v3_furniture_secure_banks'], link=True)) + before[8:]
    replace_checked(room, hook['address'] - ROOM_RAM, before, after)
    hook.update(before=before.hex(), after=after.hex())
    banks.update(source_owner_sha256=banks['output_owner_sha256'], output_owner_sha256=sha256(room))
    expanded.update(expanded_code=helper_report, output_sha256=sha256(room))
    return bytes(room), expanded, banks, compiled, extra, evidence


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base, raw = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes(), (BASE / 'build.json').read_bytes()
    callback_raw = (CALLBACKS / 'callbacks.json').read_bytes()
    if (sha256(base), sha256(raw), sha256(callback_raw)) != (BASE_SHA, REPORT_SHA, CALLBACK_SHA):
        raise ValueError('Changed complete current cartridge, report, or fire callbacks')
    prior, callbacks = json.loads(raw), json.loads(callback_raw)
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    stable = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed import-free translation')
    if (fire.native_contract(original, base) != callbacks['native_contract'] or
            any(sha256((ROOT / p).read_bytes()) != digest for p, digest in callbacks['source_sha256'].items())):
        raise ValueError('Changed complete compiled fire contract')
    rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    assets, metadata = fire.asset_contract(rel, symbols)
    if metadata != callbacks['source_metadata']:
        raise ValueError('Fire source metadata differs from checked callbacks')
    code = (CALLBACKS / 'code/code.bin').read_bytes()
    vroms = [furniture_slot(a.item)[2] for a in fire.ACTORS[:2]]
    profiles = fire.profiles(vroms, code, callbacks['code'])
    if vroms != callbacks['proposed_objects_vrom']:
        raise ValueError('Fire fixed identities differ from callback reservations')
    files = by_vrom(base)
    old_blob = files[BLOB].extract(base)
    blob = bytearray(old_blob)
    package = blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
    if (prior['runtime_abi'] != 69 or len(blob) != 0x2672A0 or sha256(blob) != prior['blob_sha256']
            or struct.unpack_from('>4I', blob, 0xF0) !=
            (BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
            or sha256(package) != prior['import_storage']['package_sha256']
            or sha256(blob[ROWS:ITEMS]) != prior['import_storage']['profile_rows_sha256']
            or sha256(blob[ITEMS:TABLE_END]) != prior['import_storage']['item_rows_sha256']
            or package[-16:] != bytes.fromhex('AFACC0DE') * 4
            or package[0x10FF0:0x11000] != bytes.fromhex('AFACC0DE') * 4
            or DMA_START + (len(files) + 1) * 16 != DMA_END
            or base[DMA_END - 16:DMA_END] != bytes(16)):
        raise ValueError('Changed sparse package, resident bounds, or full directory')
    profile = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    code_at = PACKAGE + fire.RAM - PACKAGE_RAM
    if blob[0x20:0xE0] != profile or any(blob[code_at:code_at + fire.LIMIT - fire.RAM]):
        raise ValueError('Changed selected dependencies or occupied fire code reservation')
    blob[code_at:code_at + len(code)] = code
    installed, rows = [], []
    for n, (actor, asset, details, (native, table)) in enumerate(zip(fire.ACTORS, assets, metadata, profiles)):
        index, item, vrom = furniture_slot(actor.item)
        i = slot(item)
        record = struct.pack('>HHHBB', index, item, details['price'], 2 if n else 0, 1) + details['name'].encode().ljust(16, b' ') + bytes(8)
        if (index != details['donor_runtime_index'] or vrom - BLOB < len(blob)
                or len(asset) > 0x2000 or vrom + 0x2000 > END
                or any(blob[ROWS + i * 80:ROWS + (i + 1) * 80])
                or any(blob[ITEMS + i * 32:ITEMS + (i + 1) * 32])
                or any(blob[0x5800 + index * 4:0x5804 + index * 4])
                or profile[32 + i // 8] & (1 << (i & 7))):
            raise ValueError('Fire object or canonical metadata slot is not unclaimed')
        blob.extend(bytes(vrom - BLOB - len(blob)))
        blob.extend(asset + bytes(0x2000 - len(asset)))
        table_at = PACKAGE + fire.VTABLE + n * 24 - PACKAGE_RAM
        blob[table_at:table_at + len(table)] = table
        blob[ROWS + i * 80:ROWS + (i + 1) * 80] = struct.pack('>HHI', index, item, 1) + native + bytes(4)
        blob[ITEMS + i * 32:ITEMS + (i + 1) * 32] = record
        profile[32 + i // 8] |= 1 << (i & 7)
        row = {**details, 'runtime_index': index, 'ordinary_stock': False,
            'native_hra_hex': 'd4050600', 'series': 53, 'native_scoring_birth_category': 3,
            'surface': 0, 'feng_colour': 0, 'feng_facing_penalty': 0}
        rows.append(row)
        installed.append({**row, 'registry_version': 1, 'object_vrom': f'{vrom:08X}',
            'object_bytes': len(asset), 'object_sha256': sha256(asset),
            'profile_ram': f'{ROWS_RAM + i * 80 + 8:08X}', 'profile_sha256': sha256(native),
            'item_record_sha256': sha256(record), 'runtime_installed': True, 'behaviour_installed': True,
            'enabled': True, 'selectable': False, 'ordinary_gameplay_tested': False})
    changes, score_reports, mapping = scoring(base, prior, rows, rel, symbols, source_sha256=BASE_SHA)
    output.mkdir(parents=True)
    room, expanded, banks, item_code, extra, footprint = install_readers(base, prior, blob, output, original, rel, symbols)
    changes[ROOM] = room
    furniture = copy.deepcopy(prior['furniture'])
    furniture.update(expanded_tables=expanded, bank_pool=banks)
    furniture['imports'].extend(installed)
    cat_changes, cat_report = install_catalogue(base, stable, prior,
        furniture['imports'] + [prior['speed_bag']], output, rel, symbols,
        western=True, western_large=True, camping=True, tent_model=True, fire=True)
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
            raise ValueError('Unexpected native owner allocation change')
        at = entry.pstart - files[BLOB].pstart
        if 0 <= at <= len(old_blob) - len(data):
            blob[at:at + len(data)] = data
            changes.pop(v)
    blob[0x20:0xE0] = profile
    package = blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
    struct.pack_into('>I', blob, 0xF8, zlib.crc32(package))
    struct.pack_into('>I', blob, 4, ABI)
    startup, startup_report = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', f'AF_V3_ACCESSORY_BYTES={PACKAGE_SIZE}',
        f'AF_V3_ACCESSORY_VROM={BLOB + PACKAGE}', 'AF_V3_WESTERN_LARGE=1'))
    module = bytearray(files[MODULE].extract(base))
    old = prior['startup']
    if (sha256(module[STARTUP:STARTUP + old['bytes']]) != old['sha256']
            or any(module[STARTUP + old['bytes']:CONFIG]) or len(startup) > CONFIG - STARTUP):
        raise ValueError('Changed complete startup reservation')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    start, end = files[BLOB].pstart + len(old_blob), files[BLOB].pstart + len(blob)
    if (BLOB + len(blob) > END or end > len(base) or any(base[start:end])
            or any(e.pstart < end and start < (e.pend or e.pstart + e.size)
                   for v, e in files.items() if v != BLOB and e.pstart != 0xFFFFFFFF)
            or any(e.vstart < BLOB + len(blob) and BLOB + len(old_blob) < e.vend
                   for v, e in files.items() if v != BLOB)):
        raise ValueError('Fire installation overlaps a live physical or virtual resource')
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
        raise ValueError('Fire installation changes the full directory or terminator')
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result:
        raise ValueError('Complete fire cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-fire-runtime', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        furniture=furniture, catalogue=cat_report, **score_reports,
        native_test='pending current full fire callbacks, DMA, and native four-cell readers')
    report['clothing']['save_extension'] = extra
    report['save_runtime'].update(profile_hex=profile.hex(), profile_sha256=sha256(profile))
    report['furniture_items']['imports'].extend(installed)
    report['furniture_items']['active_metadata_rows'] = 36
    for section in ('construction', 'garden', 'western', 'western_large', 'accessory_runtime', 'camping', 'tent_model'):
        report[section]['package_sha256'] = sha256(package)
    report['western_large'].update(item_code=item_code, item_dispatch=extra['item_dispatch'])
    report['import_storage'].update(remaining_bytes=END - BLOB - len(blob),
        package_sha256=sha256(package), static_installed=35, items_installed=36, item_code=item_code,
        profile_rows_sha256=sha256(blob[ROWS:ITEMS]), item_rows_sha256=sha256(blob[ITEMS:TABLE_END]),
        saved_profile_changed=True)
    report['fire_sound']['furniture_callbacks_installed'] = True
    report['fire'] = {'imports': installed, 'code': callbacks['code'],
        'callback_report_sha256': CALLBACK_SHA, 'native_contract': callbacks['native_contract'],
        'vtables_ram': callbacks['vtables_ram'], 'vtables_hex': callbacks['vtables_hex'],
        'art_report_sha256': fire.ART_SHA, 'scoring_mapping': mapping, 'resource_moves': moves,
        'package_sha256': sha256(package), 'four_cell_evidence': footprint,
        'additional_resident_bytes': 0, 'ordinary_heap_growth': 0,
        'saved_format_changed': False, 'saved_profile_changed': True,
        'acquisition_installed': False, 'ordinary_stock_unchanged': True,
        'web_patcher_enabled': False, 'not_a_playtest_handoff': True,
        'pending': ['summer-camper acquisition', 'ordinary placement, appearance, and persistence']}
    report['sources'].update({p: sha256((ROOT / p).read_bytes()) for p in SOURCES})
    write_new(output / 'animal-forest-v3-asset-loader.z64', result)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({'abi': ABI, 'sha256': result['output_sha256'],
        'remaining_bytes': result['import_storage']['remaining_bytes']}))
