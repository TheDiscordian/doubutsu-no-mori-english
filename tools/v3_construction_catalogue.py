"""Install expanded catalogue, ordinary stock, and construction scoring together."""
import argparse
import copy
import json
from pathlib import Path
import struct
import zlib

from aflib import CODE_RAM, CODE_VROM, DMA_START, apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from v3_asset_loader import BLOB, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_catalogue_capacity import GROWTH, shifted
from v3_import_catalog import read_donor
import v3_catalogue as catalogue
import v3_shops as shops
import v3_hra as hra
import v3_feng_shui as feng

ABI = 62
BASE = ROOT / 'build/v3-construction-runtime-02'
BASE_SHA = 'd9d2c30034d0e53f54b22679974f9b3bfa3136ca174d918e0f1991e10c526964'
REPORT_SHA = '4d9fc75e007de3466228206146fb3b0011c4043b0f8755bc64c596bbb2c3f458'
SOURCES = ('tools/v3_construction_catalogue.py', 'tools/v3_catalogue.py',
           'tools/v3_catalogue_capacity.py', 'tools/v3_construction_items.py',
           'tools/v3_shops.py', 'tools/v3_hra.py', 'tools/v3_feng_shui.py',
           'tools/v3_asset_loader.py', 'overlays/v3/catalogue.c',
           'overlays/v3/catalogue_bridge.S', 'overlays/v3/catalogue.ld',
           'overlays/v3/startup.c', 'overlays/v3/startup.ld')


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE / 'build.json').read_bytes()
    if sha256(base) != BASE_SHA or sha256(raw) != REPORT_SHA:
        raise ValueError('Changed complete construction runtime parent')
    prior = json.loads(raw)
    if prior['runtime_abi'] != 61: raise ValueError('Changed runtime contract')
    stable = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
    if sha256(stable) != '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507':
        raise ValueError('Changed translation-only baseline')
    original = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    files = by_vrom(base)
    blob = bytearray(files[BLOB].extract(base))
    code = bytearray(files[CODE_VROM].extract(base))
    module = bytearray(files[MODULE].extract(base))
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    rel, symbols = donor['rel'], (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    imports = prior['furniture']['imports'] + [{'item_id': '3350', 'runtime_index': 1236}]
    if len(imports) != 10: raise ValueError('Incomplete construction runtime roster')
    ordering, records = catalogue.table(stable, rel, symbols, imports, expanded=True)
    old_cat = files[catalogue.VROM].extract(base)
    cloth_report = copy.deepcopy(prior['catalogue']['clothing'])
    at = cloth_report['table_address'] - catalogue.RAM
    cloth = old_cat[at:at + 248 * 2]
    from v3_clothing_catalogue import TABLE as CLOTH_TABLE
    native_cat, _, native_parent = catalogue.sources(stable)
    if (sha256(old_cat) != prior['catalogue']['output_sha256']
            or sha256(cloth) != cloth_report['table_sha256']
            or cloth[:490] != native_cat[CLOTH_TABLE - catalogue.RAM:CLOTH_TABLE - catalogue.RAM + 490]
            or struct.unpack('>3H', cloth[-6:]) != tuple(r['catalogue_index'] for r in cloth_report['imports'])):
        raise ValueError('Changed complete three-garment catalogue')
    output.mkdir(parents=True)
    assembly = ('.section .rodata.catalogue_order\n.balign 4\n.globl af_v3_catalogue_order\n'
                'af_v3_catalogue_order:\n.byte ' + ','.join(map(str, ordering)) + '\n'
                '.balign 2\n.globl af_v3_catalogue_clothing_order\naf_v3_catalogue_clothing_order:\n.byte ' +
                ','.join(map(str, cloth)) + '\n')
    write_new(output / 'catalogue_tables.S', assembly.encode())
    suffix, compiled = compile_part('catalogue', output / 'catalogue',
        extra_sources=('overlays/v3/catalogue_bridge.S', str((output / 'catalogue_tables.S').relative_to(ROOT))),
        defines=('AF_V3_FURNITURE_TABLES=1', 'AF_V3_CLOTHING_CATALOGUE=1', 'AF_V3_ALOHA_DISPLAY=1'))
    parent = bytearray(files[catalogue.PARENT].extract(base))
    expected = bytearray(native_parent[catalogue.OWNER:catalogue.OWNER + 32])
    struct.pack_into('>I', expected, 4, catalogue.VROM + len(old_cat))
    struct.pack_into('>I', expected, 12, catalogue.RAM + len(old_cat))
    if parent[catalogue.OWNER:catalogue.OWNER + 32] != expected:
        raise ValueError('Changed current catalogue owner')
    parent[catalogue.OWNER:catalogue.OWNER + 32] = native_parent[catalogue.OWNER:catalogue.OWNER + 32]
    changes, cat_report = catalogue.install(stable, parent, suffix, compiled, ordering, records,
        prior['collection']['code'], prior['save_runtime']['code'], prior['furniture_room']['code'],
        clothing=(cloth, cloth_report), expanded=True)
    new_code = changes.pop(CODE_VROM)
    native_code = by_vrom(stable)[CODE_VROM].extract(stable)
    pool_patches = []
    for address in (0x800C4AFC, 0x800C4B10):
        at = address - CODE_RAM
        if code[at:at + 4] != native_code[at:at + 4]:
            raise ValueError('Current shared-menu reservation differs')
        pool_patches.append({'address': address, 'before': code[at:at + 4].hex(), 'after': new_code[at:at + 4].hex()})
        code[at:at + 4] = new_code[at:at + 4]
    cat_report['linked_code'] = compiled
    cat_report['code'] = {**compiled, 'symbols': {k: shifted(v) for k, v in compiled['symbols'].items()},
                          'sha256': sha256(changes[catalogue.VROM][catalogue.SIZE + GROWTH:])}
    cat_report['code'].pop('elf_relocations')  # Linked locations remain in linked_code.
    cat_report['capacity_expansion']['pool_patches'] = pool_patches

    # Only the reviewed metadata rows change; keep complete code, relocation,
    # series search storage, original values, and every preceding display row.
    score_reports = {}
    from v3_clothing_display import profile_dependency
    display = profile_dependency()
    if any(next(r for r in prior['hra']['imports'] if r['item_id'] == '3AFC')[k] != v
           for k, v in display.items()):
        raise ValueError('Changed current scoring mannequin identity')
    for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
        old = files[tool.NEW_VROM].extract(base)
        report = prior[key]
        at = report['metadata_address'] - tool.RAM
        if (sha256(old) != report['output_sha256']
                or sha256(files[tool.NEW_RELOC].extract(base)) != report['relocation_sha256']):
            raise ValueError('Changed current scoring resource')
        old_imports = [r for r in report['imports'] if r['item_id'] != '3AFC']
        kwargs = {'speed_bag': True} if key == 'hra' else {}
        before_inputs = [r for r in old_imports if r['item_id'] != '3350'] if key == 'hra' else old_imports
        new_inputs = prior['furniture']['imports'] if key == 'hra' else imports
        before, _ = tool.table(stable, rel, symbols, before_inputs, display, **kwargs)
        after, rows = tool.table(stable, rel, symbols, new_inputs, display, **kwargs)
        if (old[at:at + len(before)] != before or len(before) != len(after)
                or len(before) != report['metadata_rows'] * width):
            raise ValueError('Current scoring table differs from complete preceding imports')
        patched = bytearray(old)
        patched[at:at + len(after)] = after
        changes[tool.NEW_VROM] = bytes(patched)
        score_reports[key] = {**report, 'imports': rows, 'output_sha256': sha256(patched),
                              'metadata_sha256': sha256(after)}
    goods, table_at, stock = shops.goods(stable, rel, symbols, imports)
    stock_report = prior['shops']
    if sha256(files[shops.VROM].extract(base)) != stock_report['output_sha256']:
        raise ValueError('Changed current ordinary stock')
    at = shops.DESCRIPTOR - CODE_RAM
    if struct.unpack_from('>3I', code, at) != (shops.VROM, shops.VROM + stock_report['bytes'], 0x06000000 | stock_report['table_offset']):
        raise ValueError('Changed current ordinary-stock descriptor')
    struct.pack_into('>3I', code, at, shops.VROM, shops.VROM + len(goods), 0x06000000 | table_at)
    changes[shops.VROM] = goods
    stock_report = {**stock_report, 'imports': stock, 'bytes': len(goods),
                    'table_offset': table_at, 'output_sha256': sha256(goods)}

    # Append revised resources to the existing physical backing allocation.
    # Existing object/audio addresses and original compressed resources stay put.
    moved = []
    old_blob_bytes = len(blob)
    for vrom in (catalogue.VROM, catalogue.RELOC, hra.NEW_VROM, feng.NEW_VROM, shops.VROM):
        blob.extend(bytes(-len(blob) % 16))
        offset, data = len(blob), changes.pop(vrom)
        blob.extend(data)
        moved.append({'vrom': vrom, 'blob_offset': offset, 'bytes': len(data),
                      'physical': files[BLOB].pstart + offset, 'sha256': sha256(data)})
    if len(blob) > 0x200000 or files[BLOB].pstart + len(blob) > len(base):
        raise ValueError('Construction catalogue exceeds existing cartridge storage')
    struct.pack_into('>I', blob, 4, ABI)
    startup, startup_report = compile_part('startup', output / 'startup', defines=(
        'AF_V3_BLOB_SIZE=49152', f'AF_V3_ABI={ABI}', 'AF_V3_OBJECT_CAPACITY=448',
        'AF_V3_SAVE_RUNTIME=1', 'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1',
        'AF_V3_ACCESSORIES=1', 'AF_V3_ACCESSORY_BYTES=61440'))
    old_startup = prior['startup']
    if (sha256(module[STARTUP:STARTUP + old_startup['bytes']]) != old_startup['sha256']
            or any(module[STARTUP + old_startup['bytes']:CONFIG]) or len(startup) > CONFIG - STARTUP):
        raise ValueError('Changed startup code or bounds')
    module[STARTUP:CONFIG] = startup + bytes(CONFIG - STARTUP - len(startup))
    struct.pack_into('>4I', module, CONFIG, BLOB, 0xC000, zlib.crc32(blob[:0xC000]), ABI)
    image = bytearray(base)
    if any(image[files[BLOB].pstart + old_blob_bytes:files[BLOB].pstart + len(blob)]):
        raise ValueError('New resources overlap live cartridge data')
    changes.update({BLOB: blob, CODE_VROM: code, MODULE: module})
    for vrom, data in changes.items():
        entry = files[vrom]
        if entry.pend or (vrom != BLOB and len(data) != entry.size):
            raise ValueError('Unexpected construction allocation change')
        image[entry.pstart:entry.pstart + len(data)] = data
    struct.pack_into('>I', image, DMA_START + files[BLOB].index * 16 + 4, BLOB + len(blob))
    for row in moved:
        struct.pack_into('>4I', image, DMA_START + files[row['vrom']].index * 16,
                         row['vrom'], row['vrom'] + row['bytes'], row['physical'], 0)
    fix_checksum(image)
    image = bytes(image)
    patch = make_ups(original, image)
    if apply_ups(original, patch) != image: raise ValueError('Construction cartridge reconstruction failed')
    report = {**prior, 'build': 'v3-construction-catalogue', 'runtime_abi': ABI,
        'input_build_sha256': BASE_SHA, 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'blob_bytes': len(blob), 'blob_sha256': sha256(blob), 'startup': startup_report,
        'catalogue': cat_report, 'shops': stock_report, **score_reports,
        'construction': {**prior['construction'], 'ordinary_stock_installed': True,
            'catalogue_installed': True, 'scoring_installed': True,
            'pending': ['optional composition', 'ordinary acquisition, placement, and persistence']},
        'construction_catalogue': {'resource_moves': moved, 'saved_format_changed': False,
            'saved_profile_changed': False, 'additional_pool_allocation': 6144,
            'ordinary_gameplay_tested': False, 'optional_composition_updated': False,
            'compatibility': 'Same profile and saved format as ABI 61; ordinary cross-build reload is unverified. Keep backups.',
            'not_a_playtest_handoff': True}, 'native_test': 'pending changed catalogue/stock/scoring checks',
        'sources': {**prior['sources'], **{p: sha256((ROOT / p).read_bytes()) for p in SOURCES}}}
    write_new(output / 'animal-forest-v3-asset-loader.z64', image)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({k: result[k] for k in ('runtime_abi', 'output_sha256', 'patch_sha256')}))
