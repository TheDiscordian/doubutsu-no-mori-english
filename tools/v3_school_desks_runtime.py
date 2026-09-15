"""Install complete optional school desks without changing either web patcher."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import (CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, fix_checksum,
                   sha256, verified_rom, make_ups, apply_ups)
from apply_translation import write_new
from gc_names import symbol_data
from v3_asset_loader import BLOB, CONFIG, MODULE, STARTUP, ROOT, compile_part
from v3_campsite_calendar import PACKAGE_SIZE
from v3_furniture_art import SCHOOL_DESKS, native_profile
from v3_garden_runtime import install_catalogue
from v3_import_storage import (PACKAGE, PACKAGE_RAM, ROWS, ROWS_RAM, ITEMS,
                               ITEMS_RAM, TABLE_END, END, slot)
from v3_registry import furniture_slot
from v3_school_desks import metadata
import v3_catalogue as catalogue
import v3_hra as hra
import v3_feng_shui as feng
import v3_shops as shops

BASE = ROOT / 'build/v3-tent-lamp-runtime-02'
BASE_SHA = 'ff4e5ebafcb15d8ef777d569e0b2f4d29d848223d8e44ef15653c539796279d0'
REPORT_SHA = '90a463751b63876534df9bcc0f1e49cdbf500f468dd175056155fcbda7a51413'
ART = ROOT / 'build/v3-school-desks-art-04'
ART_SHA = '0d83eba785650fba5d1cc8760649f1e8a3e928893e09ae807fbb398fac43d474'
# The ABI-83 report retains an older package hash after environment code was
# added. Bind the actual package in the pinned ROM and refresh all receipt
# fields in this build. Its installed CRC descriptor already matches.
PACKAGE_SHA = '9ac35ca3e500ab684b468deac4e211719e5addf1e9e85b408ed6b7f0d4968c27'
ABI = 84
SOURCES = ('tools/v3_school_desks_runtime.py', 'tools/v3_school_desks.py',
    'tools/v3_furniture_art.py', 'tools/v3_registry.py', 'tools/v3_catalogue.py',
    'tools/v3_garden_runtime.py', 'tools/v3_shops.py', 'overlays/v3/startup.c',
    'overlays/v3/catalogue.c', 'overlays/v3/catalogue.ld', 'translations/provenance.json')


def scoring(base, prior, rows, rel, symbols):
    """Extend the existing native school group; do not replace its definition."""
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
            info = report['series']['info_address'] - hra.RAM + 19 * 3
            native_members = sum(data[table + i * 4] >> 2 == 19 for i in range(report['metadata_rows']))
            if (data[info:info + 3] != bytes.fromhex('020006') or native_members != 14 or
                    symbol_data(rel, symbols.decode(), 'mMkRm_series_info')[57:60] != data[info:info + 3]):
                raise ValueError('Changed native/donor school scoring group')
        for row in rows:
            index = row['runtime_index']
            at = table + index * width
            empty = bytes.fromhex('fc000000') if width == 4 else bytes(2)
            if not 1024 <= index < 2048 or data[at:at + width] != empty:
                raise ValueError('School score metadata overwrites an installed item')
            payload = bytes.fromhex(row['native_hra_hex'] if width == 4 else row['feng_hex'])
            if len(payload) != width:
                raise ValueError('Incorrect complete scoring record width')
            data[at:at + width] = payload
            record = dict(item_id=row['item_id'], runtime_index=index, metadata=payload.hex())
            if width == 4:
                record.update(donor_metadata=row['donor_hra_hex'], series=19,
                              birth_category=row['birth_category'], surface=row['surface'])
            else:
                record.update(colour_code=0, facing_penalty=0)
            report['imports'].append(record)
        report.update(output_sha256=sha256(data),
            metadata_sha256=sha256(data[table:table + report['metadata_rows'] * width]))
        if width == 4:
            if sum(data[table + i * 4] >> 2 == 19 for i in range(report['metadata_rows'])) != 17:
                raise ValueError('School group does not contain exactly the three added desks')
            report['school_desks'] = dict(series=19, original_metadata_members=14,
                full_profile_metadata_members=17, selected_members_filtered_by_composer=True,
                native_definition_preserved=True)
        changes[tool.NEW_VROM], reports[key] = bytes(data), report
    return changes, reports


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw, art_raw = (BASE / 'build.json').read_bytes(), (ART / 'art.json').read_bytes()
    if (sha256(base), sha256(raw), sha256(art_raw)) != (BASE_SHA, REPORT_SHA, ART_SHA):
        raise ValueError('Changed school-desk prerequisite cartridge, report, or complete assets')
    prior, art = json.loads(raw), json.loads(art_raw)
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    stable = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed import-free translation')
    files = by_vrom(base)
    old_blob = files[BLOB].extract(base)
    blob = bytearray(old_blob)
    package = old_blob[PACKAGE:PACKAGE + PACKAGE_SIZE]
    extra_vrom, extra_size, extra_crc, extra_ram = struct.unpack_from('>4I', blob, 0xE0)
    if (prior['runtime_abi'] != 83 or len(base) != 0x4000000 or len(blob) != 0x2A7CF0
            or sha256(blob) != prior['blob_sha256'] or PACKAGE_SIZE != 0x30000
            or struct.unpack_from('>4I', blob, 0xF0) !=
            (BLOB + PACKAGE, PACKAGE_SIZE, zlib.crc32(package), PACKAGE_RAM)
            or sha256(package) != PACKAGE_SHA
            or sha256(blob[ROWS:ITEMS]) != prior['import_storage']['profile_rows_sha256']
            or sha256(blob[ITEMS:TABLE_END]) != prior['import_storage']['item_rows_sha256']
            or package[-16:] != bytes.fromhex('AFACC0DE') * 4
            or (extra_vrom, extra_size, extra_ram) != (0x024A1080, 0x3000, 0x8046D000)
            or zlib.crc32(blob[extra_vrom-BLOB:extra_vrom-BLOB+extra_size]) != extra_crc
            or len(prior['furniture']['imports']) != 35
            or prior['furniture_items']['active_metadata_rows'] != 36
            or DMA_START + (len(files) + 1) * 16 != DMA_END
            or base[DMA_END - 16:DMA_END] != bytes(16)):
        raise ValueError('Changed complete current storage, lamp, or directory prerequisite')
    rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    prepared, rows = metadata(rel, symbols, ROOT / 'build/item-identity-megasheet.xlsx')
    if len(prepared) != 96 or len(rows) != 3 or len(art['objects']) != 3:
        raise ValueError('Incomplete school-desk metadata or conversion')
    changes, score_reports = scoring(base, prior, rows, rel, symbols)
    profile = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if blob[0x20:0xE0] != profile:
        raise ValueError('Changed current selected save profile')
    installed = []
    for n, (pilot, model, row) in enumerate(zip(SCHOOL_DESKS, art['objects'], rows, strict=True)):
        index, item, vrom = furniture_slot(pilot.item)
        i = slot(item)
        asset = (ART / model['object_file']).read_bytes()
        if (model['id'] != row['id'] or row['runtime_index'] != index or item != pilot.item
                or sha256(asset) != model['object_sha256'] or len(asset) != model['object_bytes']
                or not 0 < len(asset) <= 0x1000 or vrom % 0x1000
                or set(model['model_offsets']) != {r[0] for r in pilot.models}
                or vrom - BLOB < len(blob) or vrom + 0x1000 > END
                or any(blob[ROWS + i * 80:ROWS + (i + 1) * 80])
                or any(blob[ITEMS + i * 32:ITEMS + (i + 1) * 32])
                or any(blob[0x5800 + index * 4:0x5804 + index * 4])
                or profile[32 + i // 8] & (1 << (i & 7))):
            raise ValueError('Desk asset, fixed identity, or sparse slot is not unclaimed')
        blob.extend(bytes(vrom - BLOB - len(blob)))
        blob.extend(asset + bytes(0x1000 - len(asset)))
        native = native_profile(pilot, len(asset), model['model_offsets'], vrom)
        blob[ROWS + i * 80:ROWS + (i + 1) * 80] = struct.pack('>HHI', index, item, 1) + native + bytes(4)
        blob[ITEMS + i * 32:ITEMS + (i + 1) * 32] = prepared[n * 32:(n + 1) * 32]
        profile[32 + i // 8] |= 1 << (i & 7)
        installed.append({**row, 'registry_version': 1, 'object_vrom': f'{vrom:08X}',
            'object_bytes': len(asset), 'object_sha256': sha256(asset),
            'profile_ram': f'{ROWS_RAM + i * 80 + 8:08X}', 'profile_sha256': sha256(native),
            'runtime_installed': True, 'enabled': True, 'selectable': False,
            'ordinary_stock': True, 'catalogue_orderable': True,
            'ordinary_gameplay_tested': False,
            'remaining': ['native directional seating and two-cell placement checks',
                          'ordinary acquisition, interaction, and persistence']})
    output.mkdir(parents=True)
    furniture = copy.deepcopy(prior['furniture'])
    furniture['imports'].extend(installed)
    cat_changes, cat_report = install_catalogue(base, stable, prior,
        furniture['imports'] + [prior['speed_bag']], output, rel, symbols,
        western=True, western_large=True, camping=True, tent_model=True, fire=True, school_desks=True)
    changes.update(cat_changes)
    current_stock = {r['item_id'] for r in prior['shops']['imports']}
    goods, table_at, stock_rows = shops.goods(stable, rel, symbols,
        [r for r in furniture['imports'] + [prior['speed_bag']]
         if r['item_id'] in current_stock or int(r['item_id'], 16) in (0x3200, 0x3204, 0x3220)],
        garden=True, western=True, western_large=True, school_desks=True)
    stock = prior['shops']
    code = bytearray(files[CODE_VROM].extract(base))
    if (sha256(files[shops.VROM].extract(base)) != stock['output_sha256'] or
            struct.unpack_from('>3I', code, shops.DESCRIPTOR - CODE_RAM) !=
            (shops.VROM, shops.VROM + stock['bytes'], 0x06000000 | stock['table_offset'])):
        raise ValueError('Changed complete current goods resource or descriptor')
    struct.pack_into('>3I', code, shops.DESCRIPTOR - CODE_RAM,
                     shops.VROM, shops.VROM + len(goods), 0x06000000 | table_at)
    changes[shops.VROM], changes[CODE_VROM] = goods, code
    stock_report = {**stock, 'imports': stock_rows, 'bytes': len(goods),
                   'table_offset': table_at, 'output_sha256': sha256(goods)}
    moves = []
    for vrom in (catalogue.VROM, catalogue.RELOC, shops.VROM):
        blob.extend(bytes(-len(blob) % 16))
        offset, data = len(blob), changes.pop(vrom)
        blob.extend(data)
        moves.append(dict(vrom=vrom, blob_offset=offset, bytes=len(data),
                          physical=files[BLOB].pstart + offset, sha256=sha256(data)))
    # Preserve the complete source owners; changed fixed-size resources already
    # inside the blob retain their actual physical allocations.
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
    defines = tuple(f[2:] if not f.startswith('-DAF_V3_ABI=') else f'AF_V3_ABI={ABI}'
                    for f in prior['startup']['flags'] if f.startswith('-D'))
    startup, startup_report = compile_part('startup', output / 'startup', defines=defines)
    old = prior['startup']
    if (sha256(module[STARTUP:STARTUP + old['bytes']]) != old['sha256']
            or any(module[STARTUP + old['bytes']:CONFIG]) or len(startup) > CONFIG - STARTUP):
        raise ValueError('Changed complete current startup reservation')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    start, end = files[BLOB].pstart + len(old_blob), files[BLOB].pstart + len(blob)
    if (BLOB + len(blob) > END or end > len(base) or any(base[start:end])
            or any(e.pstart < end and start < (e.pend or e.pstart + e.size)
                   for v, e in files.items() if v != BLOB and e.pstart != 0xFFFFFFFF)
            or any(e.vstart < BLOB + len(blob) and BLOB + len(old_blob) < e.vend
                   for v, e in files.items() if v != BLOB)):
        raise ValueError('School-desk allocation overlaps actual virtual or physical resources')
    changes.update({BLOB: blob, MODULE: module})
    result = bytearray(base)
    for vrom, data in changes.items():
        result[files[vrom].pstart:files[vrom].pstart + len(data)] = data
    struct.pack_into('>I', result, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    for row in moves:
        struct.pack_into('>4I', result, DMA_START + files[row['vrom']].index * 16,
            row['vrom'], row['vrom'] + row['bytes'], row['physical'], 0)
    fix_checksum(result)
    result = bytes(result)
    if len(by_vrom(result)) != len(files) or result[DMA_END - 16:DMA_END] != bytes(16):
        raise ValueError('Desk import changes directory count or sole terminator')
    patch = make_ups(original, result)
    if apply_ups(original, patch) != result:
        raise ValueError('Complete school-desk patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-school-desks-runtime', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        furniture=furniture, catalogue=cat_report, shops=stock_report, **score_reports,
        native_test='pending current school-desk readers, DMA, seats, and placement')
    report['save_runtime'].update(profile_hex=profile.hex(), profile_sha256=sha256(profile))
    report['furniture_items']['imports'].extend(installed)
    report['furniture_items']['active_metadata_rows'] = 39
    for section in report.values():
        if isinstance(section, dict) and 'package_sha256' in section:
            section['package_sha256'] = sha256(package)
    report['import_storage'].update(remaining_bytes=END - BLOB - len(blob),
        static_installed=38, items_installed=39,
        profile_rows_sha256=sha256(blob[ROWS:ITEMS]), item_rows_sha256=sha256(blob[ITEMS:TABLE_END]),
        saved_profile_changed=True)
    report['school_desks'] = dict(imports=installed, art_report_sha256=ART_SHA,
        resource_moves=moves, profile_rows_ram=f'{ROWS_RAM:08X}', item_rows_ram=f'{ITEMS_RAM:08X}',
        package_sha256=sha256(package), additional_resident_bytes=0, ordinary_heap_growth=0,
        saved_format_changed=False, saved_profile_changed=True, older_builds_accept_new_saves=False,
        stock_catalogue_scoring_installed=True, shared_item_and_model_code_unchanged=True,
        lamp_resource_unchanged=True, web_patcher_enabled=False, not_a_playtest_handoff=True,
        pending=['native directional seating and two-cell placement checks',
                 'optional composition', 'ordinary acquisition, interaction, and persistence'])
    report['sources'].update({p: sha256((ROOT / p).read_bytes()) for p in SOURCES})
    write_new(output / 'animal-forest-v3-asset-loader.z64', result)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(report, indent=2, sort_keys=True) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    report = build(parser.parse_args().output)
    print(json.dumps({k: report[k] for k in ('runtime_abi', 'output_sha256', 'patch_sha256')}, indent=2))
