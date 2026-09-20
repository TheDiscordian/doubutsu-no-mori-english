"""Install six complete garden models, readers, catalogue, stock, and scoring.

Experimental cartridge only. Post-office reward delivery and ordinary gameplay
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
from v3_furniture_art import GARDEN_PILOTS, native_profile
from v3_garden_items import metadata, identity_evidence
from v3_import_catalog import read_donor
from v3_registry import furniture_slot
from v3_save_clothing import DEFINES as SAVE_DEFINES
import v3_catalogue as catalogue
import v3_feng_shui as feng
import v3_hra as hra
import v3_hra_mail as mail
import v3_shops as shops

ABI = 64
BASE = ROOT / 'build/v3-hra-birth-01'
BASE_SHA = 'ad8c7be6e3ec0918b0bcbc3df5028dbccbca4c2d29370f6ef9d726f3d41eedef'
REPORT_SHA = 'f365e023c7cf2b94ef0dccc5cd61c982a34fb07128d872c3c2172995856c197c'
ART = ROOT / 'build/v3-garden-art-01'
ART_SHA = '07c873050eed3cc1e4a60ba5142eaa54d9e6c38fb934fa44b7492adfee4be917'
ITEMS, ITEMS_RAM, TABLE_END = 0x7EA00, 0x80481A00, 0x7EC00
STATIC_COUNT, ITEM_COUNT = 15, 16
SOURCES = ('tools/v3_garden_runtime.py', 'tools/v3_garden_items.py',
    'tools/v3_registry.py', 'tools/v3_catalogue.py', 'tools/v3_shops.py',
    'overlays/v3/construction.h', 'overlays/v3/catalogue.c',
    'overlays/v3/furniture.c', 'overlays/v3/items.c', 'overlays/v3/save_codec.c')


def install_readers(blob, prior, output, *, extra_defines=()):
    expanded = copy.deepcopy(prior['furniture']['expanded_tables'])
    helper, compiled = compile_part('furniture_expanded', output / 'furniture_expanded',
        defines=('AF_V3_FURNITURE_TABLES=1', 'AF_V3_CLOTHING_DISPLAY=1',
            'AF_V3_SPEED_BAG=1', 'AF_V3_ALOHA_DISPLAY=1', 'AF_V3_CONSTRUCTION_ITEMS=1', 'AF_V3_GARDEN_ITEMS=1') + extra_defines,
        extra_sources=('overlays/v3/furniture_entry.S',), primary_source='overlays/v3/furniture.c')
    old = expanded['expanded_code']
    if (sha256(blob[0x5800:0x5800 + old['bytes']]) != old['sha256']
            or any(blob[0x5800 + old['bytes']:0x6000]) or not 0 < len(helper) <= 0x800):
        raise ValueError('Changed static helper or exceeded its existing reservation')
    blob[0x5800:0x6000] = helper + bytes(0x800 - len(helper))
    for row in expanded['public_entries']:
        at = row['entry'] - 0x80460000
        if blob[at:at + 8].hex() != row['after']:
            raise ValueError('Changed fixed furniture entry')
        row['target'] = compiled['symbols'][row['name']]
        after = struct.pack('>II', 0x08000000 | (row['target'] >> 2 & 0x3FFFFFF), 0)
        blob[at:at + 8] = after
        row['after'] = after.hex()
    expanded['expanded_code'] = compiled
    extra, code = compile_part('save_clothing', output / 'save_clothing',
        defines=SAVE_DEFINES + ITEM_DEFINES + ('AF_V3_SPEED_BAG=1',
            'AF_V3_CONSTRUCTION_ITEMS=1', 'AF_V3_GARDEN_ITEMS=1') + extra_defines,
        primary_source='overlays/v3/save_codec.c', extra_sources=('overlays/v3/items.c',))
    old_code = prior['clothing']['save_extension']['code']
    before = bytearray(blob[0xF400:0xF400 + old_code['bytes']])
    hook = next(r for r in prior['aloha_outfits']['hooks'] if r['address'] == '8046D7D8')
    fixes = [hook, *prior['aloha_outfits']['reader_fixes']]
    for fix in fixes:
        at = int(fix['address'], 16) - 0x8046D000
        width = len(bytes.fromhex(fix['after']))
        if before[at:at + width].hex() != fix['after']:
            raise ValueError('Changed complete-roster item fix')
        before[at:at + width] = bytes.fromhex(fix['before'])
    if (sha256(before) != old_code['sha256'] or len(extra) != old_code['bytes']
            or code['symbols'] != old_code['symbols'] or extra[:0x7D8] != before[:0x7D8]):
        raise ValueError('Garden item readers change codec instructions or public addresses')
    changed = [at for at in range(0, len(extra), 4) if extra[at:at + 4] != before[at:at + 4]]
    if changed != [0x858, 0x860]:
        raise ValueError('Unexpected garden item code change beyond table start/end')
    extra = bytearray(extra)
    for fix in fixes:
        at = int(fix['address'], 16) - 0x8046D000
        width = len(bytes.fromhex(fix['before']))
        if extra[at:at + width].hex() != fix['before']:
            raise ValueError('Garden item reader moved an applied clothing fix')
        extra[at:at + width] = bytes.fromhex(fix['after'])
    extra.extend(bytes(-len(extra) % 16))
    if struct.unpack_from('>4I', blob, 0xE0) != (
            BLOB + 0xF400, len(extra), zlib.crc32(blob[0xF400:0xF400 + len(extra)]), 0x8046D000):
        raise ValueError('Changed checked item-reader resource')
    blob[0xF400:0xF400 + len(extra)] = extra
    struct.pack_into('>I', blob, 0xE8, zlib.crc32(extra))
    return expanded, code, sha256(extra)


def score_tables(base, prior, item_rows, *, theme=56, extend_western=False):
    if theme not in (55, 56):
        raise ValueError('Unreviewed new furniture theme')
    name, members, donor_surface = ('western', 7, 18) if theme == 55 else ('backyard', 5, 26)
    if extend_western:
        if theme != 55 or [r['item_id'] for r in item_rows] != ['32C4', '32D4', '32D8']:
            raise ValueError('Unreviewed Western theme extension')
        members = 10
    files = by_vrom(base)
    changes, reports = {}, {}
    for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
        report = copy.deepcopy(prior[key])
        old = files[tool.NEW_VROM].extract(base)
        if (sha256(old) != report['output_sha256'] or
                sha256(files[tool.NEW_RELOC].extract(base)) != report['relocation_sha256']):
            raise ValueError('Changed current scoring image or relocations')
        data = bytearray(old)
        table = report['metadata_address'] - tool.RAM
        if key == 'hra':
            birth = report['birth_extension']
            if (birth['count'] != 23 or birth['stack_bytes'] != 264 or
                    sha256(data[birth['points_address'] - hra.RAM:birth['points_address'] - hra.RAM + 92]) != birth['points_sha256']
                    or any(u32(data, p['address'] - hra.RAM) != p['after'] for p in birth['patches'])):
                raise ValueError('Mailbox requires the actual expanded category evaluator')
        for row in item_rows:
            index, item = row['runtime_index'], row['item_id']
            at = table + index * width
            if data[at:at + width] != (bytes.fromhex('FC000000') if width == 4 else bytes(2)):
                raise ValueError('Garden scoring replaces an existing item')
            if width == 4:
                value = int(row['donor_hra_hex'], 16)
                birth, surface = value >> 8 & 63, value >> 6 & 3
                if birth >= report['birth_extension']['count'] or value & 63:
                    raise ValueError('Garden birth category exceeds actual evaluator')
                payload = struct.pack('>I', value & 0xFFFFC000 | birth << 9 | surface << 7)
                record = {'item_id': item, 'runtime_index': index, 'metadata': payload.hex(),
                    'donor_metadata': row['donor_hra_hex'], 'series': row['series'],
                    'birth_category': birth, 'surface': surface}
            else:
                payload = bytes.fromhex(row['feng_hex'])
                record = {'item_id': item, 'runtime_index': index, 'metadata': payload.hex(),
                    'colour': {0: 'none', 4: 'green', 5: 'gold'}[row['feng_colour']],
                    'facing_penalty': row['feng_facing_penalty']}
            data[at:at + width] = payload
            report['imports'].append(record)
        if key == 'hra':
            series = report['series']
            info, names = series['info_address'] - hra.RAM, series['names_address'] - hra.RAM
            before_info = bytes.fromhex('0200FF' if extend_western else 'FF00FF')
            before_name = name.encode().ljust(10, b' ') if extend_western else b' ' * 10
            if (data[info + theme * 3:info + (theme + 1) * 3] != before_info
                    or data[names + theme * 10:names + (theme + 1) * 10] != before_name):
                raise ValueError('New series replaces an existing definition')
            data[info + theme * 3:info + (theme + 1) * 3] = bytes.fromhex('0200FF')
            data[names + theme * 10:names + (theme + 1) * 10] = name.encode().ljust(10, b' ')
            if sum(data[table + i * 4] >> 2 == theme for i in range(report['metadata_rows'])) != members:
                raise ValueError('New series has an unexpected member count')
            series['resource_sha256'].update(af_v3_hra_series_info=sha256(data[info:info + 59 * 3]),
                af_v3_hra_series_names=sha256(data[names:names + 590]))
            series[name] = {'series': theme, 'type': 2, 'name': name,
                'donor_wall_floor_index': donor_surface, 'native_wall_floor_index': 255,
                'matching_surfaces_installed': False, 'score_letter_name_installed': True}
        report.update(output_sha256=sha256(data),
                      metadata_sha256=sha256(data[table:table + report['metadata_rows'] * width]))
        changes[tool.NEW_VROM], reports[key] = bytes(data), report
    return changes, reports


def extend_letters(source, module, report, rel, symbols, *, theme=56):
    if theme not in (55, 56):
        raise ValueError('Unreviewed score-letter theme')
    name, count, image = ('western', 57, 62688) if theme == 55 else ('backyard', 56, 62656)
    if (sha256(source) != report['output_sha256'] or report['image_bytes'] != image
            or report['name_rows'] != count or len(source) != image + 960
            or list(struct.unpack_from('>8I', module, 0x48)) != report['configuration']):
        raise ValueError('Changed complete English score-letter resource')
    image_size = report['image_bytes']
    at = report['name_table_address'] - mail.RAM
    table_end = at + count * 26
    if (at != 0xEF10 or sha256(source[at:table_end]) != report['name_table_sha256']
            or any(source[table_end:image_size]) or image_size - table_end != (-count * 26) % 16):
        raise ValueError('Changed full installed theme-name table')
    donor = symbol_data(rel, symbols.decode(), 'mMkRm_series_name')[theme * 16:(theme + 1) * 16]
    if donor != name.encode().ljust(16, b' '):
        raise ValueError('Changed new English letter name')
    table = source[at:table_end] + donor[:10] + donor
    padding = (-len(table)) % 16
    data = bytearray(source[:at] + table + bytes(padding))
    relocation = bytearray(source[image_size:])
    if struct.unpack_from('>5I', relocation) != (image_size, 0, 0, 0, 233) or len(data) > 65536:
        raise ValueError('Changed letter relocation or exceeded loader capacity')
    patches = []
    for offset, original in mail.COUNTERS.items():
        before = original & 0xFFFF0000 | ((count * 26 + 15) & ~15 if offset == 0x25F4 else count)
        after = original & 0xFFFF0000 | (len(table) + padding if offset == 0x25F4 else count + 1)
        if u32(data, offset) != before:
            raise ValueError('Changed installed letter-name counter')
        struct.pack_into('>I', data, offset, after)
        patches.append({'offset': offset, 'before': before, 'after': after})
    if u32(data, 0x2A04) != 0x24020037:
        raise ValueError('Letter-name extension changed an English template selector')
    struct.pack_into('>I', relocation, 0, len(data))
    allowed = {i for p in patches for i in range(p['offset'], p['offset'] + 4)} | set(range(table_end, image_size))
    for loaded in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(SimpleNamespace(ram=mail.RAM, resident_bytes=image_size,
            sections=(image_size, 0, 0, 0, 233)), source[:image_size], source[image_size:], loaded)
        after = relocate_verified_data(SimpleNamespace(ram=mail.RAM, resident_bytes=len(data),
            sections=(len(data), 0, 0, 0, 233)), data, relocation, loaded)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('Backyard name modifies unrelated relocated letter code/data')
    result = bytes(data + relocation)
    config = list(struct.unpack_from('>8I', module, 0x48))
    config[1], config[2], config[5], config[6] = len(result), len(data), len(data), zlib.crc32(result)
    struct.pack_into('>8I', module, 0x48, *config)
    return result, {**report, 'output_sha256': sha256(result), 'image_bytes': len(data),
        'bytes': len(result), 'name_rows': count + 1, 'name_table_sha256': sha256(table),
        'name_table_bytes': len(table), 'name_table_padding': padding, 'added_name': name,
        'series': theme, 'patches': report['patches'] + patches, 'configuration': config,
        'native_letter_generation_tested': False}


def install_catalogue(base, stable, prior, imports, output, rel, symbols, *, western=False,
                      western_large=False, camping=False, tent_model=False, fire=False, school_desks=False,
                      reviewed_rows=None, handheld=None):
    from v3_catalogue_capacity import GROWTH, shifted
    files = by_vrom(base)
    old = files[catalogue.VROM].extract(base)
    if sha256(old) != prior['catalogue']['output_sha256']:
        raise ValueError('Changed current complete catalogue')
    ordering, rows = catalogue.table(stable, rel, symbols, imports, expanded=True, garden=True,
        western=western, western_large=western_large, camping=camping, tent_model=tent_model,
        fire=fire, school_desks=school_desks, reviewed_rows=reviewed_rows)
    clothes = copy.deepcopy(prior['catalogue']['clothing'])
    at = clothes['table_address'] - catalogue.RAM
    cloth = old[at:at + 496]
    if sha256(cloth) != clothes['table_sha256'] or clothes['total_rows'] != 248:
        raise ValueError('Changed complete clothing catalogue')
    assembly = ('.section .rodata.catalogue_order\n.balign 4\n.globl af_v3_catalogue_order\n'
        'af_v3_catalogue_order:\n.byte ' + ','.join(map(str, ordering)) + '\n'
        '.balign 2\n.globl af_v3_catalogue_clothing_order\naf_v3_catalogue_clothing_order:\n.byte ' +
        ','.join(map(str, cloth)) + '\n')
    if handheld is None and prior['catalogue'].get('handheld'):
        held=copy.deepcopy(prior['catalogue']['handheld']);start=held['table_address']-catalogue.RAM
        table=old[start:start+held['total_rows']*2]
        if sha256(table)!=held['table_sha256']:raise ValueError('Changed retained handheld catalogue')
        handheld=(table,held)
    if handheld is not None:
        assembly+=('.balign 2\n.globl af_v3_catalogue_handheld_order\naf_v3_catalogue_handheld_order:\n.byte '+
            ','.join(map(str,handheld[0]))+'\n')
    write_new(output / 'catalogue_tables.S', assembly.encode())
    defines = (tuple(f[2:] for f in prior['catalogue']['linked_code']['flags'] if f.startswith('-D'))
               + ('AF_V3_CATALOGUE_RECORDS=1','AF_V3_CATALOGUE_PREVIEW_RECORDS=1')) if reviewed_rows is not None else (
        ('AF_V3_FURNITURE_TABLES=1', 'AF_V3_CLOTHING_CATALOGUE=1',
         'AF_V3_ALOHA_DISPLAY=1', 'AF_V3_GARDEN_ITEMS=1')
        + (('AF_V3_WESTERN_ITEMS=1',) if western else ())
        + (('AF_V3_WESTERN_LARGE=1',) if western_large else ())
        + (('AF_V3_CAMPING_ITEMS=1',) if camping else ())
        + (('AF_V3_TENT_MODEL=1',) if tent_model else ())
        + (('AF_V3_FIRE=1',) if fire else ()))
    suffix, compiled = compile_part('catalogue', output / 'catalogue',
        extra_sources=('overlays/v3/catalogue_bridge.S', str((output / 'catalogue_tables.S').relative_to(ROOT))),
        defines=tuple(dict.fromkeys(defines+(('AF_V3_HELD_CATALOGUE=1',) if handheld is not None else ()))))
    parent = bytearray(files[catalogue.PARENT].extract(base))
    _, _, native_parent = catalogue.sources(stable)
    expected = bytearray(native_parent[catalogue.OWNER:catalogue.OWNER + 32])
    struct.pack_into('>I', expected, 4, catalogue.VROM + len(old))
    struct.pack_into('>I', expected, 12, catalogue.RAM + len(old))
    owner_repair=None
    if parent[catalogue.OWNER:catalogue.OWNER + 32] != expected:
        # The ABI-127 icon refresh copied its predecessor's 16-byte-short
        # catalogue descriptor over the new descriptor. Migrate only this
        # exact diagnosed owner/image pair; unknown mismatches still reject.
        before=bytes(parent[catalogue.OWNER:catalogue.OWNER+32])
        if (prior['runtime_abi']!=127 or
                sha256(parent)!='4d8b82a0ba116fb601a384c8ef235501b2a60fc95ac4cdd8b2243c8780293dbb' or
                sha256(old)!='30a95d70fbfde3b744530ffe6dc93d17feacb6ace05d90d154ff5aeba2b7a7b8' or
                len(old)!=0xF5E0 or
                before!=bytes.fromhex('039700000397f5d0808a6100808b56d0808a96ac808a97c0808a92ec00000000')):
            raise ValueError('Changed current catalogue owner')
        owner_repair=dict(before=before.hex(),after=expected.hex(),restored_bytes=16,
            source_owner_sha256=sha256(parent),reason='retained icon refresh overwrote catalogue descriptor')
    parent[catalogue.OWNER:catalogue.OWNER + 32] = native_parent[catalogue.OWNER:catalogue.OWNER + 32]
    changes, report = catalogue.install(stable, parent, suffix, compiled, ordering, rows,
        prior['collection']['code'], prior['save_runtime']['code'], prior['furniture_room']['code'],
        clothing=(cloth, clothes), expanded=True,handheld=handheld)
    rebuilt_code = changes.pop(CODE_VROM)
    current_code = files[CODE_VROM].extract(base)
    retained_inventory=prior.get('equipment_resources',{}).get('inventory_preview',{}).get('joint_work',{})
    retained_pool=None
    for address in (0x800C4AFC, 0x800C4B10):
        at = address - CODE_RAM
        if rebuilt_code[at:at + 4] != current_code[at:at + 4]:
            patch=retained_inventory.get('pool_patch',{})
            if (patch.get('address')!=address or retained_inventory.get('additional_pool_bytes')!=64 or
                    struct.unpack_from('>I',rebuilt_code,at)[0]!=patch.get('before') or
                    struct.unpack_from('>I',current_code,at)[0]!=patch.get('after') or
                    patch['after']-patch['before']!=64):
                raise ValueError(f'Catalogue allocation mismatch at {address:08X}: rebuilt '
                    f'{rebuilt_code[at:at+4].hex()}, current {current_code[at:at+4].hex()}, '
                    f'expected retained inventory {patch}')
            retained_pool=copy.deepcopy(patch)
    if retained_pool:
        report['conservative_pool_required']+=64
        report['pool_reserved']+=64
        report['retained_inventory_pool_patch']=retained_pool
    report['linked_code'] = compiled
    if owner_repair:report['owner_descriptor_repair']=owner_repair
    report['code'] = {**compiled, 'symbols': {k: shifted(v) for k, v in compiled['symbols'].items()},
                     'sha256': sha256(changes[catalogue.VROM][catalogue.SIZE + GROWTH:])}
    report['code'].pop('elf_relocations')
    report['capacity_expansion']['pool_patches'] = prior['catalogue']['capacity_expansion']['pool_patches']
    return changes, report


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw, raw_art = (BASE / 'build.json').read_bytes(), (ART / 'art.json').read_bytes()
    if (sha256(base), sha256(raw), sha256(raw_art)) != (BASE_SHA, REPORT_SHA, ART_SHA):
        raise ValueError('Changed garden source cartridge, report, or converted assets')
    prior, art = json.loads(raw), json.loads(raw_art)
    if prior['runtime_abi'] != 63:
        raise ValueError('Garden installation requires ABI 63')
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    stable = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed import-free baseline')
    files = by_vrom(base)
    old_blob = files[BLOB].extract(base)
    blob, module, code = bytearray(old_blob), bytearray(files[MODULE].extract(base)), bytearray(files[CODE_VROM].extract(base))
    if (len(blob) != 0x15C170 or any(blob[0x7E7D0:0x7E800]) or any(blob[0x7E940:TABLE_END])
            or ROWS + STATIC_COUNT * 80 > ITEMS or ITEMS + ITEM_COUNT * 32 != TABLE_END
            or TABLE_END > PACKAGE + PACKAGE_SIZE - 16
            or blob[PACKAGE + PACKAGE_SIZE - 16:PACKAGE + PACKAGE_SIZE] != bytes.fromhex('AFACC0DE') * 4
            or struct.unpack_from('>4I', blob, 0xF0) != (BLOB + PACKAGE, PACKAGE_SIZE,
                zlib.crc32(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]), PACKAGE_RAM)):
        raise ValueError('Changed garden resident reservation or package')
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    rel, symbols = donor['rel'], (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    evidence = identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx')
    prepared, item_rows = metadata(rel, symbols)
    if len(prepared) != 192 or len(item_rows) != 6 or len(art['objects']) != 6:
        raise ValueError('Incomplete garden source conversion')
    output.mkdir(parents=True)
    expanded, item_code, extra_sha = install_readers(blob, prior, output)
    old_rows = old_blob[ROWS:ROWS + 9 * 80]
    old_items = old_blob[0x7E800:0x7E940]
    if (sha256(old_rows) != prior['construction']['profile_rows_sha256']
            or sha256(old_items) != prior['construction']['item_rows_sha256']
            or len(prior['furniture']['imports']) != 9):
        raise ValueError('Changed installed furniture tables')
    rows = bytearray(old_rows)
    profile = bytearray.fromhex(prior['save_runtime']['profile_hex'])
    if blob[0x20:0xE0] != profile:
        raise ValueError('Changed selected save profile')
    installed = []
    for pilot, model, row in zip(GARDEN_PILOTS, art['objects'], item_rows, strict=True):
        index, item, vrom = furniture_slot(pilot.item)
        asset = (ART / model['object_file']).read_bytes()
        if (model['id'] != row['id'] or row['runtime_index'] != index or item != pilot.item
                or sha256(asset) != model['object_sha256'] or len(asset) != model['object_bytes']
                or not 0 < len(asset) <= 0x1000 or vrom % 0x1000
                or set(model['model_offsets']) != {'opaque'} or vrom - BLOB < len(blob)):
            raise ValueError('Changed garden object, identity, or fixed storage')
        blob.extend(bytes(vrom - BLOB - len(blob)))
        blob.extend(asset)
        native = native_profile(pilot, len(asset), model['model_offsets'], vrom)
        address = ROWS_RAM + len(rows) + 8
        rows.extend(struct.pack('>HHI', index, item, 1) + native + bytes(4))
        seed, bit = 0x5800 + index * 4, (item - 0x3000) // 4
        if any(blob[seed:seed + 4]) or profile[32 + bit // 8] & (1 << (bit & 7)):
            raise ValueError('Garden import replaces an existing selected identity')
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
    imports = furniture['imports'] + [{'item_id': '3350', 'runtime_index': 1236}]
    changes, cat_report = install_catalogue(base, stable, prior, imports, output, rel, symbols)
    score_changes, score_reports = score_tables(base, prior, item_rows)
    changes.update(score_changes)
    letters, letter_report = extend_letters(files[mail.VROM].extract(base), module,
        prior['hra']['score_letters'], rel, symbols)
    changes[mail.VROM] = letters
    score_reports['hra']['score_letters'] = letter_report
    for row in installed:
        row['native_hra_hex'] = next(r['metadata'] for r in score_reports['hra']['imports'] if r['item_id'] == row['item_id'])
    goods, table_at, stock_rows = shops.goods(stable, rel, symbols,
        [r for r in imports if r['item_id'] != '3294'], garden=True)
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
        raise ValueError('Garden resources exceed verified physical or virtual storage')
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
        raise ValueError('Garden cartridge patch reconstruction failed')
    report = copy.deepcopy(prior)
    report.update(build='v3-garden-runtime', runtime_abi=ABI, input_build_sha256=BASE_SHA,
        output_sha256=sha256(result), patch_sha256=sha256(patch), blob_sha256=sha256(blob),
        blob_bytes=len(blob), blob_file_bytes=len(blob), startup=startup_report,
        furniture=furniture, catalogue=cat_report, shops=stock_report, **score_reports,
        native_test='pending changed garden runtime checks')
    report['save_runtime'].update(profile_hex=profile.hex(), profile_sha256=sha256(profile))
    report['clothing']['save_extension'].update(code=item_code, resource_sha256=extra_sha)
    report['furniture_items']['imports'].extend(installed)
    report['furniture_items'].update(active_metadata_ram=f'{ITEMS_RAM:08X}', active_metadata_rows=ITEM_COUNT)
    report['garden'] = {'imports': installed, 'identity_evidence': evidence,
        'art_report_sha256': ART_SHA, 'profile_rows_ram': f'{ROWS_RAM:08X}',
        'profile_rows': STATIC_COUNT, 'profile_rows_sha256': sha256(rows),
        'item_rows_ram': f'{ITEMS_RAM:08X}', 'item_rows': ITEM_COUNT,
        'item_rows_sha256': sha256(blob[ITEMS:TABLE_END]),
        'package_sha256': sha256(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]), 'resource_moves': moves,
        'additional_permanent_ram': 0, 'additional_menu_pool': 0, 'saved_format_changed': False,
        'saved_profile_changed': True, 'older_builds_accept_new_saves': False,
        'ordinary_and_lottery_stock_installed': True, 'post_office_reward_installed': False,
        'catalogue_installed': True, 'scoring_installed': True, 'web_patcher_enabled': False,
        'optional_composition_updated': False, 'not_a_playtest_handoff': True,
        'pending': ['post-office reward delivery', 'optional composition',
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
