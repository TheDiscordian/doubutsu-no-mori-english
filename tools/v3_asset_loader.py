"""Build an experimental V3 object-loader cartridge, without enabling move-ins."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

from aflib import (CODE_RAM, CODE_VROM, apply_ups, by_vrom, fix_checksum, make_ups,
                   replace_dma, sha256, u32, verified_rom)
from apply_translation import write_new
from toolchain import IMAGE
from v3_import_catalog import ROOT, read_donor
from v3_villager_art import build_art

BASE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
MODULE, MODULE_RAM = 0x02800000, 0x801948E0
STARTUP, CONFIG, STATE, STARTUP_END = 0x6000, 0x63E0, 0x63F0, 0x6400
BLOB, BLOB_RAM, BLOB_SIZE, TABLE_OFFSET = 0x03F00000, 0x80460000, 0x2000, 0x1000
OBJECT_TABLE, OBJECT_COUNT, CAPACITY = 0x8010DDD0, 410, 430
STARTUP_CALL, ORIGINAL_CALL = 0x800D65D0, 0x0C0275B4
TEXTURE_BASE, TEXTURE_STRIDE = 0x03F10000, 0x2000
SOURCE_FILES = ('tools/v3_asset_loader.py', 'overlays/v3/startup.c', 'overlays/v3/startup.ld',
                'overlays/v3/asset.c', 'overlays/v3/asset.ld', 'tools/v3_villager_art.py',
                'tools/v3_import_catalog.py')


def texture_slot(donor_index):
    """Fixed English-donor slots, independent of the chosen subset or its order."""
    if not 216 <= donor_index < 236:
        raise ValueError('Not a new named English-donor villager')
    slot = donor_index - 216
    return OBJECT_COUNT + slot, TEXTURE_BASE + slot * TEXTURE_STRIDE


def compile_part(part, out):
    out.mkdir(parents=True, exist_ok=False)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        return subprocess.run(docker + ['/n64_toolchain/bin/mips64-elf-' + tool, IMAGE, *args],
                              check=True, capture_output=True, text=True, timeout=60).stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0',
             '-mno-abicalls', '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common',
             '-fno-stack-protector', '-ffunction-sections', '-fdata-sections', '-fstack-usage',
             '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, f'/source/overlays/v3/{part}.c', '-o', 'code.o')
    run('ld', '-EB', '-T', f'/source/overlays/v3/{part}.ld', '-o', 'code.elf', 'code.o')
    if run('nm', '--undefined-only', 'code.elf').strip():
        raise ValueError('Unresolved V3 loader symbol')
    symbols = {name: int(address, 16) for address, kind, name in
               (line.split() for line in run('nm', '--defined-only', 'code.elf').splitlines())}
    run('objcopy', '-O', 'binary', '-j', '.text', '-j', '.rodata', 'code.elf', 'code.bin')
    code = (out / 'code.bin').read_bytes()
    expected = MODULE_RAM + STARTUP if part == 'startup' else BLOB_RAM + 0x100
    if symbols[f'af_v3_{part if part == "startup" else "asset_init"}'] != expected:
        raise ValueError('V3 linker moved the public entry')
    write_new(out / 'code.asm', run('objdump', '-d', 'code.elf').encode())
    return code, {'bytes': len(code), 'sha256': sha256(code), 'symbols': symbols,
                  'toolchain': IMAGE, 'flags': flags, 'stack_usage': (out / 'code.su').read_text()}


def compose(native, base, changes, added):
    """Preserve current DMA identities and startup copies while adding new files."""
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('V3 composition requires exact stable V2-11')
    current, original = by_vrom(base), by_vrom(native)
    if not changes and not added:
        return base
    if not set(changes) <= set(current) or set(added) & set(current):
        raise ValueError('Unknown change or colliding V3 addition')
    if any(len(data) != current[v].size or v in (0x1060, 0x19D40) for v, data in changes.items()):
        raise ValueError('Unexpected resize or boot change in V3 asset batch')
    original_by_index = {e.index: e for e in original.values()}
    if not set(original_by_index) <= {e.index for e in current.values()}:
        raise ValueError('V2 has lost an original DMA identity')
    replacements, moves, additions = {}, {}, dict(added)
    for v, entry in current.items():
        data = changes.get(v, entry.extract(base))
        old = original_by_index.get(entry.index)
        if old is None:
            additions[v] = data
        elif v != 0x19D40:
            if v != old.vstart or len(data) != old.size:
                moves[old.vstart] = v
            if data != old.extract(native) or old.vstart in moves:
                replacements[old.vstart] = data
    image = bytearray(replace_dma(native, replacements, moves, additions))
    boot = original[0x1060]
    boot_data = current[0x1060].extract(base)
    if base[boot.pstart:boot.pstart + boot.size] != boot_data:
        raise ValueError('V2 physical and virtual startup copies disagree')
    image[boot.pstart:boot.pstart + boot.size] = boot_data
    fix_checksum(image)
    image = bytes(image)
    installed = by_vrom(image)
    if set(installed) != set(current) | set(added):
        raise ValueError('V3 composition loses DMA resources')
    for v, before in current.items():
        actual, expected = installed[v].extract(image), changes.get(v, before.extract(base))
        if v == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if installed[v].index != before.index or actual != expected:
            raise ValueError(f'V3 composition changes an unrelated resource: {v:08X}')
    if any(installed[v].extract(image) != data for v, data in added.items()):
        raise ValueError('V3 composition does not retain complete added data')
    return image


def build(native, base, rel, symbols, out):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Asset loader requires exact stable V2-11')
    sources = {p: sha256((ROOT / p).read_bytes()) for p in SOURCE_FILES}
    artifacts, art = build_art(native, rel, symbols)
    files, originals = by_vrom(base), by_vrom(native)
    code = bytearray(files[CODE_VROM].extract(base))
    module = bytearray(files[MODULE].extract(base))
    if (len(module) != 0x8000 or any(module[STARTUP:STARTUP_END])
            or u32(module, 12) != STARTUP or u32(code, STARTUP_CALL - CODE_RAM) != ORIGINAL_CALL):
        raise ValueError('Changed resident diagnostic space or existing startup chain')
    object_at = 0x800C5AA0 - CODE_RAM
    if code[object_at:object_at + 144] != originals[CODE_VROM].extract(native)[object_at:object_at + 144]:
        raise ValueError('Object loader is no longer the reviewed native function')
    table_at = OBJECT_TABLE - CODE_RAM
    table = bytes(code[table_at:table_at + OBJECT_COUNT * 8])
    for start, end in struct.iter_unpack('>II', table):
        if start == end == 0:
            continue
        if start not in files or end != files[start].vend:
            raise ValueError('Existing object bank does not match its current DMA resource')
    startup, startup_report = compile_part('startup', out / 'startup')
    helper, helper_report = compile_part('asset', out / 'asset')
    if len(startup) > CONFIG - STARTUP or len(helper) > TABLE_OFFSET - 0x100:
        raise ValueError('V3 code exceeds its owned reservation')
    blob = bytearray(BLOB_SIZE)
    struct.pack_into('>5I', blob, 0, 0x41465633, 1, BLOB_SIZE, CAPACITY, OBJECT_COUNT)
    blob[0x100:0x100 + len(helper)] = helper
    blob[TABLE_OFFSET:TABLE_OFFSET + len(table)] = table
    struct.pack_into('>4I', blob, BLOB_SIZE - 16, *([0xAF33C0DE] * 4))
    additions, imports = {}, []
    for row in art['villagers']:
        index = int(row['id'].rsplit('/', 1)[-1], 16)
        bank, vrom = texture_slot(index)
        texture = artifacts[row['texture_file']]
        struct.pack_into('>II', blob, TABLE_OFFSET + bank * 8, vrom, vrom + len(texture))
        additions[vrom] = texture
        imports.append({'id': row['id'], 'name': row['name'], 'object_bank': bank,
                        'texture_vrom': f'{vrom:08X}', 'texture_sha256': sha256(texture),
                        'playable': False, 'draw_record_installed': False})
    module[STARTUP:STARTUP + len(startup)] = startup
    struct.pack_into('>4I', module, CONFIG, BLOB, BLOB_SIZE, zlib.crc32(blob), 1)
    struct.pack_into('>I', code, STARTUP_CALL - CODE_RAM,
                     0x0C000000 | ((MODULE_RAM + STARTUP) >> 2 & 0x3FFFFFF))
    additions[BLOB] = bytes(blob)
    changes = {CODE_VROM: bytes(code), MODULE: bytes(module)}
    image = compose(native, base, changes, additions)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('V3 asset patch reconstruction failed')
    if sources != {p: sha256((ROOT / p).read_bytes()) for p in SOURCE_FILES}:
        raise ValueError('V3 sources changed during construction')
    return image, patch, {'build': 'V3 asset-loader development 02', 'baseline_sha256': BASE_SHA,
        'source_sha256': sha256(native), 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'sources': sources, 'startup': startup_report, 'asset': helper_report,
        'blob_sha256': sha256(blob), 'original_object_table_sha256': sha256(table),
        'object_capacity': CAPACITY, 'imports': imports, 'rom_bytes': len(image),
        'resident_startup_range': ['8019A8E0', '8019ACE0'],
        'expansion_data_range': ['80460000', '80462000'], 'ordinary_heap_growth': 0,
        'required_ram_bytes': 0x800000, 'saved_format_changed': False,
        'new_villager_ids_enabled': False, 'native_test': 'pending', 'hardware_test': 'not performed',
        'save_warning': 'Development loader only; use disposable saves. V3 import/profile compatibility is unverified.',
        'added_resources': {f'{v:08X}': sha256(data) for v, data in additions.items()},
        'changed_resources': {f'{v:08X}': sha256(data) for v, data in changes.items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'build') or out.exists():
        raise ValueError('Choose a fresh output directory inside ignored build/')
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    out.mkdir(parents=True)
    image, patch, report = build((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes(), donor['rel'],
        (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), out)
    for name, data in {'animal-forest-v3-asset-loader.z64': image, 'asset-loader.ups': patch,
                      'build.json': (json.dumps(report, indent=2) + '\n').encode()}.items():
        write_new(out / name, data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
