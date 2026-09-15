"""Install seven complete camping objects without inventing their reward route.

Experimental cartridge only. Summer-camper acquisition is not installed here;
neither the local nor the public web patcher is changed.
"""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (DMA_START, DMA_END, by_vrom, fix_checksum, sha256, verified_rom,
                   make_ups, apply_ups)
from apply_translation import write_new
from gc_names import symbol_data
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP, ROOT, compile_part
from v3_camping_items import BASE, BASE_SHA, REPORT_SHA, identity_evidence, metadata, score_mapping
from v3_furniture_art import CAMPING_PILOTS, native_profile
from v3_garden_runtime import install_catalogue
from v3_import_catalog import read_donor
from v3_import_storage import (PACKAGE, PACKAGE_RAM, PACKAGE_SIZE, ROWS, ROWS_RAM,
                               ITEMS, ITEMS_RAM, TABLE_END, SLOTS, END, slot)
from v3_registry import furniture_slot
import v3_catalogue as catalogue
import v3_hra as hra
import v3_feng_shui as feng

ABI = 68
ART = ROOT / 'build/v3-camping-art-01'
ART_SHA = '5ac42594d8bb7605fff8b62b2bf8e1a251c9001eb3fd828904266a222ea7daa5'
SOURCES = ('tools/v3_camping_runtime.py', 'tools/v3_camping_items.py',
    'tools/v3_furniture_art.py', 'tools/v3_registry.py', 'tools/v3_import_storage.py',
    'tools/v3_catalogue.py', 'tools/v3_garden_runtime.py', 'overlays/v3/catalogue.c',
    'overlays/v3/catalogue.ld', 'overlays/v3/startup.c')


def scoring(base, prior, item_rows, rel, symbols, *, source_sha256=BASE_SHA):
    mapping = score_mapping(rel, symbols, base, prior, source_sha256=source_sha256)
    changes, reports = {}, {}
    files = by_vrom(base)
    for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
        report = copy.deepcopy(prior[key])
        old = files[tool.NEW_VROM].extract(base)
        if (sha256(old) != report['output_sha256'] or
                sha256(files[tool.NEW_RELOC].extract(base)) != report['relocation_sha256']):
            raise ValueError('Changed complete current scoring owner or relocations')
        data = bytearray(old)
        table = report['metadata_address'] - tool.RAM
        if width == 4:
            info = report['series']['info_address'] - hra.RAM + 53 * 3
            if (data[info:info + 3] != bytes.fromhex('0000ff') or
                    symbol_data(rel, symbols.decode(), 'mMkRm_series_info')[159:162] != data[info:info + 3]):
                raise ValueError('Camping misc classification differs from native scoring')
        for row in item_rows:
            at, index = table + row['runtime_index'] * width, row['runtime_index']
            empty = bytes.fromhex('fc000000') if width == 4 else bytes(2)
            if not 1024 <= index < 2048 or data[at:at + width] != empty:
                raise ValueError('Camping score metadata overwrites an installed item')
            if width == 4:
                payload = bytes.fromhex(row['native_hra_hex'])
                donor, native = int(row['donor_hra_hex'], 16), int.from_bytes(payload, 'big')
                if (row['series'] != 53 or donor >> 8 & 63 != 37 or donor & 63 or
                        native != (donor & 0xFFFFC000 | 3 << 9 | (donor >> 6 & 3) << 7)):
                    raise ValueError('Camping scoring changes an unreviewed field')
                record = {'item_id': row['item_id'], 'runtime_index': index,
                    'metadata': payload.hex(), 'donor_metadata': row['donor_hra_hex'],
                    'series': 53, 'birth_category': 3, 'donor_birth_category': 37,
                    'surface': row['surface'], 'points': 412, 'scoring_only_category_mapping': True}
            else:
                payload = bytes.fromhex(row['feng_hex'])
                record = {'item_id': row['item_id'], 'runtime_index': index,
                    'metadata': payload.hex(), 'colour_code': row['feng_colour'],
                    'facing_penalty': row['feng_facing_penalty']}
            if len(payload) != width:
                raise ValueError('Incorrect complete scoring record width')
            data[at:at + width] = payload
            report['imports'].append(record)
        report.update(output_sha256=sha256(data),
            metadata_sha256=sha256(data[table:table + report['metadata_rows'] * width]))
        changes[tool.NEW_VROM], reports[key] = bytes(data), report
    return changes, reports, mapping


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw, art_raw = (BASE / 'build.json').read_bytes(), (ART / 'art.json').read_bytes()
    if (sha256(base), sha256(raw), sha256(art_raw)) != (BASE_SHA, REPORT_SHA, ART_SHA):
        raise ValueError('Changed camping source cartridge, report, or complete assets')
    prior, art = json.loads(raw), json.loads(art_raw)
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    stable = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed import-free translation')
    files = by_vrom(base)
    old_blob = files[BLOB].extract(base)
    blob = bytearray(old_blob)
    package = old_blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
    if (prior['runtime_abi'] != 67 or len(base) != 0x4000000 or len(blob) != 0x22D010
            or struct.unpack_from('>4I', blob, 0xF0) !=
            (BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
            or sha256(package) != prior['import_storage']['package_sha256']
            or sha256(blob[ROWS:ITEMS]) != prior['import_storage']['profile_rows_sha256']
            or sha256(blob[ITEMS:TABLE_END]) != prior['import_storage']['item_rows_sha256']
            or package[-16:] != bytes.fromhex('AFACC0DE') * 4
            or len(prior['furniture']['imports']) != 25
            or prior['furniture_items']['active_metadata_rows'] != 26
            or DMA_START + (len(files) + 1) * 16 != DMA_END
            or base[DMA_END - 16:DMA_END] != bytes(16)):
        raise ValueError('Changed complete sparse-storage prerequisite')
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    rel, symbols = donor['rel'], (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    prepared, item_rows = metadata(rel, symbols)
    evidence = identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx')
    if len(prepared) != 224 or len(item_rows) != 7 or len(art['objects']) != 7:
        raise ValueError('Incomplete camping conversion')
    changes, score_reports, mapping = scoring(base, prior, item_rows, rel, symbols)
    profile = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if blob[0x20:0xE0] != profile:
        raise ValueError('Changed current selected save profile')
    installed = []
    for n, (pilot, model, row) in enumerate(zip(CAMPING_PILOTS, art['objects'], item_rows, strict=True)):
        index, item, vrom = furniture_slot(pilot.item)
        i = slot(item)
        asset = (ART / model['object_file']).read_bytes()
        if (model['id'] != row['id'] or row['runtime_index'] != index or item != pilot.item
                or sha256(asset) != model['object_sha256'] or len(asset) != model['object_bytes']
                or not 0 < len(asset) <= 0x2000 or vrom % 0x2000
                or set(model['model_offsets']) != {r[0] for r in pilot.models}
                or vrom - BLOB < len(blob) or vrom + 0x2000 > END
                or any(blob[ROWS + i * 80:ROWS + (i + 1) * 80])
                or any(blob[ITEMS + i * 32:ITEMS + (i + 1) * 32])
                or any(blob[0x5800 + index * 4:0x5804 + index * 4])
                or profile[32 + i // 8] & (1 << (i & 7))):
            raise ValueError('Camping object, fixed identity, or sparse slot is not unclaimed')
        blob.extend(bytes(vrom - BLOB - len(blob)))
        blob.extend(asset + bytes(0x2000 - len(asset)))
        native = native_profile(pilot, len(asset), model['model_offsets'], vrom)
        blob[ROWS + i * 80:ROWS + (i + 1) * 80] = struct.pack('>HHI', index, item, 1) + native + bytes(4)
        blob[ITEMS + i * 32:ITEMS + (i + 1) * 32] = prepared[n * 32:(n + 1) * 32]
        profile[32 + i // 8] |= 1 << (i & 7)
        installed.append({**row, 'registry_version': 1, 'object_vrom': f'{vrom:08X}',
            'object_bytes': len(asset), 'object_sha256': sha256(asset),
            'profile_ram': f'{ROWS_RAM + i * 80 + 8:08X}', 'profile_sha256': sha256(native),
            'runtime_installed': True, 'enabled': True, 'selectable': False,
            'ordinary_gameplay_tested': False})
    output.mkdir(parents=True)
    furniture = copy.deepcopy(prior['furniture'])
    furniture['imports'].extend(installed)
    cat_changes, cat_report = install_catalogue(base, stable, prior,
        furniture['imports'] + [prior['speed_bag']], output, rel, symbols,
        western=True, western_large=True, camping=True)
    changes.update(cat_changes)
    moves = []
    for vrom in (catalogue.VROM, catalogue.RELOC):
        blob.extend(bytes(-len(blob) % 16))
        offset, data = len(blob), changes.pop(vrom)
        blob.extend(data)
        moves.append({'vrom': vrom, 'blob_offset': offset, 'bytes': len(data),
            'physical': files[BLOB].pstart + offset, 'sha256': sha256(data)})
    # Scoring owners already occupy ranges within the import resource. Keep
    # those physical allocations and update the parent resource hash as well.
    for vrom, data in list(changes.items()):
        entry = files[vrom]
        if entry.pend or len(data) != entry.size:
            raise ValueError('Unexpected current-owner allocation change')
        at = entry.pstart - files[BLOB].pstart
        if 0 <= at <= len(old_blob) - len(data):
            blob[at:at + len(data)] = data
            changes.pop(vrom)
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
        raise ValueError('Camping allocation overlaps actual virtual or physical resources')
    changes.update({BLOB: blob, MODULE: module})
    result = bytearray(base)
    for vrom, data in changes.items():
        entry = files[vrom]
        result[entry.pstart:entry.pstart + len(data)] = data
    struct.pack_into('>I', result, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    for row in moves:
        struct.pack_into('>4I', result, DMA_START + files[row['vrom']].index * 16,
            row['vrom'], row['vrom'] + row['bytes'], row['physical'], 0)
    fix_checksum(result)
    result = bytes(result)
    if len(by_vrom(result)) != len(files) or result[DMA_END - 16:DMA_END] != bytes(16):
        raise ValueError('Camping import changes directory count or sole terminator')
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result:
        raise ValueError('Camping cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-camping-runtime', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        furniture=furniture, catalogue=cat_report, **score_reports,
        native_test='pending changed camping catalogue and full-model checks')
    report['save_runtime'].update(profile_hex=profile.hex(), profile_sha256=sha256(profile))
    report['furniture_items']['imports'].extend(installed)
    report['furniture_items']['active_metadata_rows'] = 33
    for section in ('construction', 'garden', 'western', 'western_large', 'accessory_runtime'):
        report[section]['package_sha256'] = sha256(package)
    report['import_storage'].update(remaining_bytes=END - BLOB - len(blob),
        package_sha256=sha256(package), static_installed=32, items_installed=33,
        profile_rows_sha256=sha256(blob[ROWS:ITEMS]), item_rows_sha256=sha256(blob[ITEMS:TABLE_END]),
        saved_profile_changed=True)
    report['camping'] = {'imports': installed, 'identity_evidence': evidence,
        'art_report_sha256': ART_SHA, 'scoring_mapping': mapping, 'resource_moves': moves,
        'profile_rows_ram': f'{ROWS_RAM:08X}', 'item_rows_ram': f'{ITEMS_RAM:08X}',
        'profile_layout': 'canonical-sparse-1024', 'package_sha256': sha256(package),
        'additional_resident_bytes': 0, 'ordinary_heap_growth': 0,
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
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({'abi': ABI, 'sha256': result['output_sha256'],
        'camping_items': len(result['camping']['imports']), 'remaining_bytes': result['import_storage']['remaining_bytes']}))
