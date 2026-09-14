"""Install the verified twenty-villager artwork bundle without enabling move-ins."""
import argparse
import json
from pathlib import Path
import struct
import zlib

from aflib import (DMA_START, apply_ups, by_vrom, fix_checksum, make_ups, sha256,
                   verified_rom)
from apply_translation import write_new
from v3_asset_loader import BLOB, BLOB_RAM, CONFIG, MODULE, ROOT, STARTUP, compile_part
from v3_storage import END

ABI, CAPACITY, RESIDENT = 51, 448, 0xC000
REGISTRY_VERSION = 1
GROWTH, OLD_GROWTH, FLAGS = 0x1E80, 0x1D80, 0x1E60
BASE = ROOT/'build/v3-punchy-house-02'
BASE_SHA = '55cb90c0cc9eac32aa6e180051f1791072cfa6dd5ba1c6b8a72a413f6211e060'
OLD_BLOB_SHA = 'cb624cea70ff4b9cb77887cf0ed1145c2a6dfbd674b5a39c7e3227599402e61d'
OLD_MODULE_SHA = '7a11850af5da9aacc09a80d40202d5959ca9904ea08c6c375e6b131cab0660da'
ART = ROOT/'build/v3-all-villager-art-01'
ART_SHA = '3c0e9a645d457feddbc17be2dc12eb66670313300d373b6b5a35c70fbef704a5'
GROWTH_SHA = 'a3936366a0229ecacd2eaeca7fa72b31ed1149394d7b5c93a031d19b57bb6eb6'
ASSET_EXTRAS = ('overlays/v3/npc_draw.c', 'overlays/v3/npc_voice.S',
    'overlays/v3/melody.c', 'overlays/v3/clothing.c', 'overlays/v3/npc_clothing.c',
    'overlays/v3/player_clothing.c', 'overlays/v3/clothing_stock.c',
    'overlays/v3/clothing_stock.S')
SOURCES = ('tools/v3_villager_assets_runtime.py', 'overlays/v3/asset.c',
    'overlays/v3/startup.c', 'overlays/v3/villager_selection.c')


def texture_slot(donor):
    if not 216 <= donor < 236:
        raise ValueError('Unknown English-donor villager')
    slot = donor-216
    # Preserve the already installed pilot identities and physical resources.
    vrom = 0x03F10000+slot*0x2000 if donor in (232, 235) else BLOB+0x40000+slot*0x2000
    return 410+slot, vrom


def model_slot(donor):
    if donor not in (233, 229):
        raise ValueError('No separate converted model for this villager')
    return (430, BLOB+0x12000) if donor == 233 else (431, BLOB+0x14000)


def accessory_slot(tool):
    if not 52 <= tool < 68:
        raise ValueError('Unknown converted accessory')
    return 432+tool-52, BLOB+0x18000+(tool-52)*0x2000


def load_art(directory):
    raw = (directory/'art.json').read_bytes()
    if sha256(raw) != ART_SHA:
        raise ValueError('Expected the complete verified twenty-villager bundle')
    report = json.loads(raw)
    records, resources = [], {}

    def add(row, kind, bank, vrom, filename, size, digest, **extra):
        if Path(filename).name != filename:
            raise ValueError('Artwork filename escapes its bundle')
        data = (directory/filename).read_bytes()
        limit = 0x2800 if kind == 'model' else 0x1620 if kind == 'texture' else 0x2000
        if not 0 < len(data) <= limit or len(data) != size or len(data) % 16 or sha256(data) != digest:
            raise ValueError('Changed or oversized converted artwork: '+filename)
        if bank in resources:
            raise ValueError('Duplicate artwork bank')
        resources[bank] = data
        records.append({'id': row['id'], 'name': row['name'], 'kind': kind,
            'bank': bank, 'vrom': f'{vrom:08X}', 'bytes': size, 'sha256': digest,
            'source_file': filename, **extra})

    for row in report['villagers']:
        donor = int(row['id'].rsplit('/', 1)[1], 16)
        add(row, 'texture', *texture_slot(donor), row['texture_file'],
            row['native_texture_bytes'], row['texture_sha256'])
        if 'model_file' in row:
            add(row, 'model', *model_slot(donor), row['model_file'], row['model_bytes'],
                row['model_sha256'], skeleton=row.get('converted_skeleton', row['native_skeleton']))
        if 'accessory' in row:
            a = row['accessory']
            add(row, 'accessory', *accessory_slot(a['tool']), a['object_file'],
                a['object_bytes'], a['object_sha256'], joint=a['joint'],
                display_list=f"{0x06000000+a['native_model_offset']:08X}",
                donor_tool=a['tool'], runtime_attached=False)
    if set(resources) != set(range(410, CAPACITY)) or sum(map(len, resources.values())) != 162016:
        raise ValueError('Incomplete converted artwork registry')
    return sorted(records, key=lambda r: r['bank']), resources


def replace_constants(before, after, pairs):
    """Retained MIPS code may change only reviewed instruction immediates."""
    if len(before) != len(after) or len(before) % 4:
        raise ValueError('Recompiled helper size changed')
    changes = []
    for at in range(0, len(before), 4):
        a, b = struct.unpack_from('>I', before, at)[0], struct.unpack_from('>I', after, at)[0]
        if a == b:
            continue
        if a >> 16 != b >> 16 or (a & 0xFFFF, b & 0xFFFF) not in pairs:
            raise ValueError(f'Unexpected recompiled instruction at {at:04X}: {a:08X} -> {b:08X}')
        changes.append({'offset': at, 'before': f'{a:08X}', 'after': f'{b:08X}'})
    if not changes:
        raise ValueError('Recompiled helper did not apply its required constants')
    return changes


def install_art(blob, records, resources, files, base):
    if sha256(blob) != OLD_BLOB_SHA:
        raise ValueError('Changed ABI-50 resident/resources file')
    growth = files[0xE0D000].extract(base)
    if (len(growth) != 224 or sha256(growth) != GROWTH_SHA
            or blob[OLD_GROWTH:OLD_GROWTH+224] != growth
            or any(blob[GROWTH:GROWTH+224]) or any(blob[FLAGS:FLAGS+20])):
        raise ValueError('Changed native growth permissions or occupied destination')
    result = bytearray(blob)
    result[OLD_GROWTH:OLD_GROWTH+224] = bytes(224)
    result[GROWTH:GROWTH+224] = growth
    for row in records:
        bank, start = row['bank'], int(row['vrom'], 16)
        data = resources[bank]
        at = 0x1000+bank*8
        if bank in (426, 429):
            if (struct.unpack_from('>II', result, at) != (start, start+len(data))
                    or files[start].extract(base) != data):
                raise ValueError('Changed installed pilot texture')
            continue
        if any(result[at:at+8]) or start < BLOB+len(result) or start+len(data) > END:
            raise ValueError('New bank overlaps existing table/data or V3 storage limit')
        struct.pack_into('>II', result, at, start, start+len(data))
        # Registry order is not VROM order: collect the resources below instead.
    appended = sorted((int(r['vrom'], 16), resources[r['bank']])
                      for r in records if r['bank'] not in (426, 429))
    for start, data in appended:
        if start < BLOB+len(result):
            raise ValueError('Overlapping new artwork resources')
        result.extend(bytes(start-BLOB-len(result)))
        result.extend(data)
    if result[FLAGS:FLAGS+20] != bytes(20) or result[GROWTH:GROWTH+224] != growth:
        raise ValueError('Expanded bank table overwrote selection data')
    return result


def compose(base, blob, module):
    """Append one expanded file in verified padding; retain all other physical DMAs."""
    if sha256(base) != BASE_SHA:
        raise ValueError('Expected the exact complete ABI-50 implementation cartridge')
    files = by_vrom(base)
    old, resident = files[BLOB], files[MODULE]
    if (len(module) != resident.size or resident.pend or len(blob) % 16
            or not old.size < len(blob) <= END-BLOB):
        raise ValueError('Unexpected module/storage layout')
    end = max(e.pend or e.pstart+e.size for e in files.values() if e.pstart != 0xFFFFFFFF)
    start = (end+15) & ~15
    if any(base[end:]) or start+len(blob) > len(base):
        raise ValueError('Expanded artwork does not fit verified unused cartridge padding')
    if any(e.vstart < BLOB+len(blob) and BLOB < e.vend for v, e in files.items() if v != BLOB):
        raise ValueError('Expanded artwork overlaps another virtual file')
    result = bytearray(base)
    result[start:start+len(blob)] = blob
    result[resident.pstart:resident.pstart+resident.size] = module
    struct.pack_into('>4I', result, DMA_START+old.index*16, BLOB, BLOB+len(blob), start, 0)
    fix_checksum(result)
    return bytes(result)


def build(base_directory, art_directory, output):
    if not output.resolve().is_relative_to(ROOT/'build'):
        raise ValueError('Generated game assets must stay in ignored build/')
    base = (base_directory/'animal-forest-v3-asset-loader.z64').read_bytes()
    if sha256(base) != BASE_SHA:
        raise ValueError('Changed ABI-50 implementation cartridge')
    old_report = json.loads((base_directory/'build.json').read_text())
    if old_report['output_sha256'] != BASE_SHA:
        raise ValueError('Wrong source build report')
    files = by_vrom(base)
    old_blob, old_module = files[BLOB].extract(base), files[MODULE].extract(base)
    if sha256(old_module) != OLD_MODULE_SHA:
        raise ValueError('Changed source translation module')
    records, resources = load_art(art_directory)
    blob = install_art(old_blob, records, resources, files, base)
    module = bytearray(old_module)
    output.mkdir(parents=True, exist_ok=False)
    definitions = (
        ('asset', 0x100, old_report['asset'], ASSET_EXTRAS,
         (f'AF_V3_OBJECT_CAPACITY={CAPACITY}',), {(430, CAPACITY)}),
        ('villager_selection', 0x3400, old_report['villager_selection']['code'], (),
         ('AF_V3_OUTFIT_READY=0x80464084u', f'AF_V3_GROWTH_ADDRESS=0x{BLOB_RAM+GROWTH:X}u'),
         {(OLD_GROWTH, GROWTH)}),
        ('startup', STARTUP, old_report['startup'], (),
         (f'AF_V3_BLOB_SIZE={RESIDENT}', f'AF_V3_ABI={ABI}', 'AF_V3_SAVE_RUNTIME=1',
          'AF_V3_CLOTHING_PROFILE=1', 'AF_V3_FURNITURE_TABLES=1', f'AF_V3_OBJECT_CAPACITY={CAPACITY}'),
         {(50, ABI), (430, CAPACITY)}),
    )
    compiled = {}
    for name, at, previous, extra, defines, pairs in definitions:
        code, report = compile_part(name, output/name, extra_sources=extra, defines=defines)
        source = old_module if name == 'startup' else old_blob
        before = source[at:at+previous['bytes']]
        if sha256(before) != previous['sha256'] or report['symbols'] != previous['symbols']:
            raise ValueError('Changed source helper or relocated symbols: '+name)
        report['instruction_changes'] = replace_constants(before, code, pairs)
        target = module if name == 'startup' else blob
        target[at:at+len(code)] = code
        compiled[name] = report
    struct.pack_into('>5I', blob, 0, 0x41465633, ABI, RESIDENT, CAPACITY, 410)
    struct.pack_into('>4I', module, CONFIG, BLOB, RESIDENT, zlib.crc32(blob[:RESIDENT]), ABI)
    image = compose(base, blob, module)
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Complete UPS reconstruction failed')
    report = dict(old_report)
    report.update({'build': 'v3-complete-villager-assets', 'runtime_abi': ABI,
        'input_build_sha256': BASE_SHA, 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'startup': compiled['startup'], 'asset': compiled['asset'],
        'object_capacity': CAPACITY, 'blob_sha256': sha256(blob), 'blob_file_bytes': len(blob),
        'storage': {**old_report['storage'], 'bytes': len(blob)},
        'native_test': 'pending for ABI-51 changes', 'hardware_test': 'not performed',
        'villager_assets': {'registry_version': REGISTRY_VERSION, 'art_manifest_sha256': ART_SHA,
            'banks': records, 'growth_ram': f'{BLOB_RAM+GROWTH:08X}',
            'growth_sha256': GROWTH_SHA, 'converted_asset_bytes': sum(map(len, resources.values())),
            'texture_count': 20, 'model_count': 2, 'accessory_count': 16,
            'accessories_attached': False, 'additional_draw_rows_installed': False,
            'move_in_enabled': [], 'saved_format_changed': False,
            'sources': {p: sha256((ROOT/p).read_bytes()) for p in SOURCES}},
        'villager_selection': {**old_report['villager_selection'],
            'code': compiled['villager_selection'], 'compiled_bytes': compiled['villager_selection']['bytes'],
            'compiled_sha256': compiled['villager_selection']['sha256'],
            'growth_ram': f'{BLOB_RAM+GROWTH:08X}', 'native_execution': 'pending for relocated growth table'},
    })
    report['sources'] = {**old_report['sources'], **report['villager_assets']['sources']}
    write_new(output/'animal-forest-v3-asset-loader.z64', image)
    write_new(output/'asset-loader.ups', patch)
    write_new(output/'build.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=BASE)
    parser.add_argument('--art', type=Path, default=ART)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.base, args.art, args.output)
    print(json.dumps({k: report[k] for k in ('output_sha256', 'patch_sha256', 'object_capacity', 'blob_file_bytes')}))


if __name__ == '__main__':
    main()
