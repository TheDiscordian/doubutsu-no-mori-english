"""Install seven complete Western models, readers, catalogue, stock, and scoring.

Experimental cartridge only. Ordinary acquisition and gameplay
remain separate work; no served patcher is modified by this builder.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
from types import SimpleNamespace
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, apply_ups, by_vrom, fix_checksum,
                   make_ups, sha256, u32, verified_rom)
from apply_translation import write_new
from gc_names import symbol_data
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_clothing_items import DEFINES as ITEM_DEFINES
from v3_construction_runtime import PACKAGE, PACKAGE_RAM, PACKAGE_SIZE, ROWS, ROWS_RAM
from v3_furniture_art import WESTERN_PILOTS, native_profile
from v3_western_items import metadata, identity_evidence
from v3_import_catalog import read_donor
from v3_registry import furniture_slot
from v3_save_clothing import DEFINES as SAVE_DEFINES
import v3_catalogue as catalogue
import v3_feng_shui as feng
import v3_hra as hra
import v3_hra_mail as mail
import v3_shops as shops

ABI = 65
BASE = ROOT / 'build/v3-garden-runtime-02'
BASE_SHA = '436c5cec2aeb1d9f34d1fb71217ec62a6ef232d91573e0112d7055c65345f1d0'
REPORT_SHA = 'e931376f12e03eb3adbff213227c144c39d0debcff5cdf00f399f10ad4279cda'
ART = ROOT / 'build/v3-western-art-01'
ART_SHA = 'ffd098a0bb47a6f759dabdf55983aa71d6d4d7d5c78ce3062c8584d05503b0e6'
ITEMS, ITEMS_RAM, TABLE_END = 0x7EC00, 0x80481C00, 0x7EEE0
STATIC_COUNT, ITEM_COUNT = 22, 23
SOURCES = ('tools/v3_western_runtime.py', 'tools/v3_western_items.py',
    'tools/v3_garden_runtime.py', 'tools/v3_furniture_banks.py',
    'overlays/v3/furniture_banks.h', 'overlays/v3/furniture_expanded.ld',
    'tools/v3_registry.py', 'tools/v3_catalogue.py', 'tools/v3_shops.py',
    'overlays/v3/construction.h', 'overlays/v3/catalogue.c',
    'overlays/v3/furniture.c', 'overlays/v3/items.c', 'overlays/v3/save_codec.c')


from v3_garden_runtime import install_readers, install_catalogue, score_tables, extend_letters
from v3_furniture_banks import install as install_banks


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw, raw_art = (BASE / 'build.json').read_bytes(), (ART / 'art.json').read_bytes()
    if (sha256(base), sha256(raw), sha256(raw_art)) != (BASE_SHA, REPORT_SHA, ART_SHA):
        raise ValueError('Changed Western source cartridge, report, or converted assets')
    prior, art = json.loads(raw), json.loads(raw_art)
    if prior['runtime_abi'] != 64:
        raise ValueError('Western installation requires ABI 64')
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    stable = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed import-free baseline')
    files = by_vrom(base)
    old_blob = files[BLOB].extract(base)
    blob, module, code = bytearray(old_blob), bytearray(files[MODULE].extract(base)), bytearray(files[CODE_VROM].extract(base))
    if (len(blob) != 0x18BAC0 or any(blob[0x7E9B0:0x7EA00]) or any(blob[0x7EC00:TABLE_END])
            or ROWS + STATIC_COUNT * 80 > ITEMS or ITEMS + ITEM_COUNT * 32 != TABLE_END
            or TABLE_END > PACKAGE + PACKAGE_SIZE - 16
            or blob[PACKAGE + PACKAGE_SIZE - 16:PACKAGE + PACKAGE_SIZE] != bytes.fromhex('AFACC0DE') * 4
            or struct.unpack_from('>4I', blob, 0xF0) != (BLOB + PACKAGE, PACKAGE_SIZE,
                zlib.crc32(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]), PACKAGE_RAM)):
        raise ValueError('Changed Western resident reservation or package')
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    rel, symbols = donor['rel'], (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    evidence = identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx')
    prepared, item_rows = metadata(rel, symbols)
    if len(prepared) != 224 or len(item_rows) != 7 or len(art['objects']) != 7:
        raise ValueError('Incomplete Western source conversion')
    output.mkdir(parents=True)
    expanded, item_code, extra_sha = install_readers(blob, prior, output,
        extra_defines=('AF_V3_WESTERN_ITEMS=1', 'AF_V3_EXPANDED_BANKS=1'))
    old_rows = old_blob[ROWS:ROWS + 15 * 80]
    old_items = old_blob[0x7EA00:0x7EC00]
    if (sha256(old_rows) != prior['garden']['profile_rows_sha256']
            or sha256(old_items) != prior['garden']['item_rows_sha256']
            or len(prior['furniture']['imports']) != 15):
        raise ValueError('Changed installed furniture tables')
    rows = bytearray(old_rows)
    profile = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if blob[0x20:0xE0] != profile:
        raise ValueError('Changed selected save profile')
    installed = []
    for pilot, model, row in zip(WESTERN_PILOTS, art['objects'], item_rows, strict=True):
        index, item, vrom = furniture_slot(pilot.item)
        asset = (ART / model['object_file']).read_bytes()
        if (model['id'] != row['id'] or row['runtime_index'] != index or item != pilot.item
                or sha256(asset) != model['object_sha256'] or len(asset) != model['object_bytes']
                or not 0 < len(asset) <= 0x2000 or vrom % 0x2000
                or set(model['model_offsets']) != {r[0] for r in pilot.models} or vrom - BLOB < len(blob)):
            raise ValueError('Changed Western object, identity, or fixed storage')
        blob.extend(bytes(vrom - BLOB - len(blob)))
        blob.extend(asset)
        native = native_profile(pilot, len(asset), model['model_offsets'], vrom)
        address = ROWS_RAM + len(rows) + 8
        rows.extend(struct.pack('>HHI', index, item, 1) + native + bytes(4))
        seed, bit = 0x5800 + index * 4, (item - 0x3000) // 4
        if any(blob[seed:seed + 4]) or profile[32 + bit // 8] & (1 << (bit & 7)):
            raise ValueError('Western import replaces an existing selected identity')
        struct.pack_into('>I', blob, seed, address)
        profile[32 + bit // 8] |= 1 << (bit & 7)
        installed.append({**row, 'registry_version': 1, 'object_vrom': f'{vrom:08X}',
            'object_bytes': len(asset), 'object_sha256': sha256(asset),
            'profile_ram': f'{address:08X}', 'profile_sha256': sha256(native),
            'runtime_installed': True, 'enabled': True, 'selectable': False,
            'ordinary_gameplay_tested': False})
    blob[ROWS:ROWS + len(rows)] = rows
    blob[ITEMS:TABLE_END] = old_items + prepared
    blob[0x20:0xE0] = profile
    furniture = copy.deepcopy(prior['furniture'])
    furniture['imports'].extend(installed)
    furniture['expanded_tables'] = expanded
    bank_changes, furniture = install_banks(base, furniture, expanded['expanded_code'])
    imports = furniture['imports'] + [{'item_id': '3350', 'runtime_index': 1236}]
    changes, cat_report = install_catalogue(base, stable, prior, imports, output, rel, symbols, western=True)
    changes.update(bank_changes)
    score_changes, score_reports = score_tables(base, prior, item_rows, theme=55)
    changes.update(score_changes)
    letters, letter_report = extend_letters(files[mail.VROM].extract(base), module,
        prior['hra']['score_letters'], rel, symbols, theme=55)
    changes[mail.VROM] = letters
    score_reports['hra']['score_letters'] = letter_report
    for row in installed:
        row['native_hra_hex'] = next(r['metadata'] for r in score_reports['hra']['imports'] if r['item_id'] == row['item_id'])
    goods, table_at, stock_rows = shops.goods(stable, rel, symbols,
        [r for r in imports if r['item_id'] != '3294'], garden=True, western=True)
    stock = prior['shops']
    if (sha256(files[shops.VROM].extract(base)) != stock['output_sha256']
            or struct.unpack_from('>3I', code, shops.DESCRIPTOR - CODE_RAM) !=
            (shops.VROM, shops.VROM + stock['bytes'], 0x06000000 | stock['table_offset'])):
        raise ValueError('Changed current native goods resource')
    struct.pack_into('>3I', code, shops.DESCRIPTOR - CODE_RAM, shops.VROM,
                     shops.VROM + len(goods), 0x06000000 | table_at)
    changes[shops.VROM] = goods
    stock_report = {**stock, 'imports': stock_rows, 'bytes': len(goods),
                   'table_offset': table_at, 'output_sha256': sha256(goods)}
    moves = []
    for vrom in (catalogue.VROM, catalogue.RELOC, hra.NEW_VROM, feng.NEW_VROM, shops.VROM, mail.VROM):
        blob.extend(bytes(-len(blob) % 16))
        offset, data = len(blob), changes.pop(vrom)
        blob.extend(data)
        moves.append({'vrom': vrom, 'blob_offset': offset, 'bytes': len(data),
            'physical': files[BLOB].pstart + offset, 'sha256': sha256(data)})
    if (len(blob) > 0x200000 or files[BLOB].pstart + len(blob) > len(base)
            or len(base) != 0x4000000 or any(base[files[BLOB].pstart + len(old_blob):files[BLOB].pstart + len(blob)])
            or any(e.vstart < BLOB + len(blob) and BLOB + len(old_blob) < e.vend for vrom, e in files.items() if vrom != BLOB)):
        raise ValueError('Western resources exceed verified physical or virtual storage')
    struct.pack_into('>I', blob, 4, ABI)
    struct.pack_into('>I', blob, 0xF8, zlib.crc32(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]))
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
    changes.update({BLOB: blob, MODULE: module, CODE_VROM: code})
    result = bytearray(base)
    for vrom, data in changes.items():
        entry = files[vrom]
        if entry.pend or (vrom != BLOB and len(data) != entry.size):
            raise ValueError('Unexpected in-place allocation change')
        result[entry.pstart:entry.pstart + len(data)] = data
    struct.pack_into('>I', result, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    for row in moves:
        struct.pack_into('>4I', result, DMA_START + files[row['vrom']].index * 16,
            row['vrom'], row['vrom'] + row['bytes'], row['physical'], 0)
    fix_checksum(result)
    result = bytes(result)
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result:
        raise ValueError('Western cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-western-runtime', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        furniture=furniture, catalogue=cat_report, shops=stock_report, **score_reports,
        native_test='pending changed Western runtime checks')
    report['save_runtime'].update(profile_hex=profile.hex(), profile_sha256=sha256(profile))
    report['clothing']['save_extension'].update(code=item_code, resource_sha256=extra_sha)
    report['furniture_items']['imports'].extend(installed)
    report['furniture_items'].update(active_metadata_ram=f'{ITEMS_RAM:08X}', active_metadata_rows=ITEM_COUNT)
    report['western'] = {'imports': installed, 'identity_evidence': evidence,
        'art_report_sha256': ART_SHA, 'profile_rows_ram': f'{ROWS_RAM:08X}',
        'profile_rows': STATIC_COUNT, 'profile_rows_sha256': sha256(rows),
        'item_rows_ram': f'{ITEMS_RAM:08X}', 'item_rows': ITEM_COUNT,
        'item_rows_sha256': sha256(blob[ITEMS:TABLE_END]),
        'package_sha256': sha256(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]), 'resource_moves': moves,
        'additional_permanent_ram': 921632, 'additional_menu_pool': 0, 'saved_format_changed': False,
        'saved_profile_changed': True, 'older_builds_accept_new_saves': False,
        'ordinary_and_event_stock_installed': True,
        'catalogue_installed': True, 'scoring_installed': True, 'web_patcher_enabled': False,
        'optional_composition_updated': False, 'not_a_playtest_handoff': True,
        'pending': ['optional composition',
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
