#!/usr/bin/env python3
"""Compile the English title adapter with assets owned by the native overlay."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256, by_vrom, verified_rom
from accent_mail_overlays import rows, packed_rows, KINDS
from catalogue_names import Image
from check_keyboard_assembly import IMAGE
from npc_mail_show import relocate_verified_data
from title_assets import ROOT
from title_graphics import package
from title_press_start import ACTOR, RELOC, RAM, SOURCE_HASHES, POSITIONS

PREFIX = 9952
INSTANCE = 0x330+1152
PROFILE = 0x80AA1F40-RAM
IMPORTS = {
    'af_title_native_constructor': 0x80AA1C5C,
    'SegmentBaseAddress': 0x801458A0,
    'cKF_SkeletonInfo_R_ct': 0x80052228,
    'cKF_SkeletonInfo_R_init': 0x80052584,
    'cKF_SkeletonInfo_R_play': 0x800528D4,
    'cKF_Si3_draw_SV_R_child': 0x80052D20,
    'Matrix_push': 0x800E020C, 'Matrix_pull': 0x800E0244,
    'Matrix_translate': 0x800E0314, 'Matrix_scale': 0x800E041C,
    '_Matrix_to_Mtx': 0x800E139C,
}


def compile_overlay(native, rel, symbols, out):
    files = by_vrom(verified_rom(native))
    original, native_reloc = files[ACTOR].extract(native), files[RELOC].extract(native)
    if (len(original) != PREFIX or sha256(original) != SOURCE_HASHES[ACTOR]
            or sha256(native_reloc) != SOURCE_HASHES[RELOC]
            or struct.unpack_from('>5I', native_reloc) != (8912, 992, 48, 0, 145)):
        raise ValueError('Changed native title overlay or relocation')
    blob, graphics = package(rel, symbols)
    out.mkdir(parents=True, exist_ok=True)
    (out/'title.bin').write_bytes(blob)
    (out/'assets.s').write_text('.section .rodata.title_assets,"a"\n.balign 16\n'
                              '.globl af_title_assets\naf_title_assets:\n.incbin "/out/title.bin"\n')
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError('Title '+tool+' failed: '+result.stdout+result.stderr)
        return result.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
             '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
             '-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses', '-fstack-usage',
             '-D_LANGUAGE_C', '-DF3DEX_GBI_2', '-I/source/upstream/af/lib/ultralib/include',
             '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/title/title.c', '-o', 'title.o')
    run('as', '-EB', '-mabi=32', '-march=vr4300', 'assets.s', '-o', 'assets.o')
    start = RAM+PREFIX
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/title/append.ld',
        f'--defsym=__title_extension_base=0x{start:08X}',
        *(f'--defsym={name}=0x{value:08X}' for name, value in IMPORTS.items()),
        '-Map=title.map', '-o', 'title.elf', 'title.o', 'assets.o')
    if run('nm', '--undefined-only', 'title.elf').strip():
        raise ValueError('Undefined title import')
    exports = {}
    for line in run('nm', '--defined-only', 'title.elf').splitlines():
        parts = line.split()
        if len(parts) == 3: exports[parts[2]] = int(parts[0], 16)
    run('objcopy', '-O', 'binary', 'title.elf', 'extension.bin')
    extension = (out/'extension.bin').read_bytes()
    end = start+len(extension)
    if (exports.get('__title_start') != start or exports.get('__title_end') != end
            or len(extension) > 0x50000 or exports['__title_code_end']-start > 0x2000):
        raise ValueError('Invalid title extension ownership')
    blob_at = exports['af_title_assets']-start
    if extension[blob_at:blob_at+len(blob)] != blob:
        raise ValueError('Linked title assets differ from the complete source package')
    entries, inventory = rows(native_reloc, PREFIX), []
    listing = run('readelf', '-rW', 'title.elf')
    for line in listing.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*', line)
        if not match: raise ValueError('Unsupported title ELF relocation: '+line)
        at, kind, target, name = int(match[1], 16), KINDS[match[2]], int(match[3], 16), match[4]
        if not start <= at <= end-4 or at & 3:
            raise ValueError('Title ELF relocation escapes extension')
        inventory.append([at-RAM, kind, target, name])
        if RAM <= target < end:
            if not (start <= target < end or IMPORTS.get(name) == target) or at-RAM in entries:
                raise ValueError('Unapproved title prefix reference')
            entries[at-RAM] = kind
        elif IMPORTS.get(name) != target or (kind not in (5, 6) if name == 'SegmentBaseAddress' else kind != 4):
            raise ValueError('Unapproved title native import')
    data, patches = bytearray(original+extension), []
    def change(at, before, after, kind=None):
        if struct.unpack_from('>I', data, at)[0] != before:
            raise ValueError(f'Changed title patch site: {RAM+at:08X}')
        struct.pack_into('>I', data, at, after)
        entries.pop(at, None)
        if kind is not None: entries[at] = kind
        patches.append({'offset': at, 'before': before, 'after': after, 'relocation': kind})
    def call(at, before, name):
        change(at-RAM, 0x0C000000 | ((before >> 2) & 0x3FFFFFF),
               0x0C000000 | ((exports[name] >> 2) & 0x3FFFFFF), 4)
    change(PROFILE+12, 0x328, INSTANCE)
    change(PROFILE+16, IMPORTS['af_title_native_constructor'], exports['af_title_constructor'], 2)
    call(0x80AA1ED8, 0x80AA0A6C, 'af_title_step')
    call(0x80AA1A24, 0x80AA0C98, 'af_title_draw')
    for at in (0x80AA1A34, 0x80AA1A44, 0x80AA1A54, 0x80AA1A64, 0x80AA1A74):
        change(at-RAM, 0x0C000000 | ((0x80AA0C98 >> 2) & 0x3FFFFFF), 0)
    call(0x80AA1AD4, 0x80AA12A0, 'af_title_trademark')
    for i, (before, after) in enumerate(zip((74, 138, 202, 154, 154, 154), (96, 160, 224, 159, 159, 159))):
        change(POSITIONS+i*4, before, after)
    relocated = packed_rows(entries, len(data))
    if len(relocated) > 4096:
        raise ValueError('Title relocation scratch exceeds its bounded size')
    spec = Image(RAM, len(data), struct.unpack_from('>5I', relocated))
    native_spec = Image(RAM, PREFIX, (8912, 992, 48, 0, 145))
    changed = {p['offset'] for p in patches}
    for base in (0x801A0010, 0x802C0010):
        old = relocate_verified_data(native_spec, original, native_reloc, base)
        new = relocate_verified_data(spec, bytes(data), relocated, base)
        for at in range(0, PREFIX, 4):
            if at not in changed and new[at:at+4] != old[at:at+4]:
                raise ValueError('Title extension changes an unrelated relocated prefix word')
        if new[PREFIX+blob_at:PREFIX+blob_at+len(blob)] != blob:
            raise ValueError('Native relocation changes segmented title asset contents')
    source_paths = ['overlays/title/title.c', 'overlays/title/append.ld', 'tools/title_graphics.py',
                    'tools/title_model.py', 'tools/title_assets.py']
    source_paths += ['upstream/af/lib/ultralib/include/PR/'+name for name in ('mbi.h', 'gbi.h', 'abi.h', 'ultratypes.h')]
    report = {'version': 1, 'ram': RAM, 'bytes': len(data), 'prefix_bytes': PREFIX,
              'actor_instance_bytes': INSTANCE, 'state_offset': 0x330, 'state_bytes': 1152,
              'overlay_sha256': sha256(data), 'relocation_sha256': sha256(relocated),
              'relocation_bytes': len(relocated), 'asset_offset': PREFIX+blob_at,
              'asset_bytes': len(blob), 'asset_sha256': sha256(blob),
              'sources': {p: sha256((ROOT/p).read_bytes()) for p in source_paths},
              'symbols': {k: v-RAM for k, v in exports.items() if start <= v < end},
              'imports': IMPORTS, 'patches': patches, 'elf_relocations': inventory,
              'toolchain': IMAGE, 'flags': flags, 'code_extension_bytes': exports['__title_code_end']-start,
              'stack_usage': (out/'title.su').read_text(), 'installed': False,
              'status': 'Compiled title overlay; cartridge installation and native execution pending'}
    for name, contents in (('overlay.bin', bytes(data)), ('relocation.bin', relocated),
                           ('overlay.json', (json.dumps(report, indent=2)+'\n').encode()),
                           ('elf-relocations.txt', listing.encode())):
        (out/name).write_bytes(contents)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/title-overlay')
    args = parser.parse_args()
    report = compile_overlay((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), args.output)
    print(json.dumps({k: report[k] for k in ('bytes', 'code_extension_bytes', 'relocation_bytes', 'actor_instance_bytes',
        'overlay_sha256', 'relocation_sha256', 'installed')}, indent=2))
