"""Compile candidate classic-letter adapters against exact retained images."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
from accent_mail_overlays import Overlay, packed_rows, KINDS
from accent_mail_overlay_profile import wrap, validate as validate_creator
from extended_font_cartridge import validate as validate_font, relocate as relocate_font
from npc_mail_show import relocate_verified_data

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT/'build/reserve-letters-pilot'
BASE_SHA = '648d59503d8bf0c6031f24efc02fc2cdca99e0e4a10cd05d5a663b66e6ee3bda'


def source_hashes():
    paths = ['overlays/classic_letters/'+name for name in ('classic.h', 'creator.c', 'hook.c', 'append.ld')]
    paths += ['overlays/mail_generation/'+name for name in ('npc_creator.h', 'npc_capture.h', 'generate.h')]
    paths += ['runtime/mail/'+name for name in ('npc_loader.h', 'npc_generation.h', 'record.h', 'format.h', 'catalog.h')]
    return {path: sha256((ROOT/path).read_bytes()) for path in paths}


def normalized_rows(reloc, size):
    text, data, rodata, bss, count = struct.unpack_from('>5I', reloc)
    if text+data+rodata+bss != size or len(reloc) & 15 or count > (len(reloc)-24)//4:
        raise ValueError('Invalid retained classic-prefix sections')
    starts, sizes = {1: 0, 2: text, 3: text+data}, {1: text, 2: data, 3: rodata}
    result = {}
    for entry in struct.unpack_from('>'+str(count)+'I', reloc, 20):
        section, kind, offset = entry >> 30, (entry >> 24) & 63, entry & 0xFFFFFF
        if section not in starts or kind not in KINDS.values() or offset & 3 or offset+4 > sizes[section]:
            raise ValueError('Invalid retained classic-prefix relocation')
        at = starts[section]+offset
        if at in result:
            raise ValueError('Duplicate retained classic-prefix relocation')
        result[at] = kind
    return result


def compile_one(kind, prior, data, reloc, out):
    ram, prefix = prior['ram'], len(data)
    symbols = prior['symbols']
    if kind == 'font':
        validate_font(data, reloc, prior)
        imports = {'af_accent_font_install': ram+symbols['af_accent_font_install'], 'af_npc_mail_load': 0x80197BB4}
        source, entry, limit = 'hook', 'af_classic_install', 0x3000
    else:
        validate_creator('creator', data, reloc, prior)
        imports = {name: ram+symbols[name] for name in
                   ('af_mail_create_guard', 'af_mail_capture_set', 'af_mail_generate', 'af_notice_seasonal_create')}
        source, entry, limit = 'creator', 'af_classic_mail_create', 0x10000
    hashes = source_hashes()
    out.mkdir(parents=True, exist_ok=True)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError('Classic-letter '+tool+' failed: '+result.stdout+result.stderr)
        return result.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls', '-fno-pic',
             '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector', '-fno-merge-constants',
             '-mno-explicit-relocs', '-mno-split-addresses', '-fstack-usage', '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/classic_letters/'+source+'.c', '-o', 'extension.o')
    start = ram+prefix
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/classic_letters/append.ld',
        f'--defsym=__classic_extension_base=0x{start:08X}',
        *(f'--defsym={k}=0x{v:08X}' for k, v in imports.items()),
        '-Map=extension.map', '-o', 'extension.elf', 'extension.o')
    if run('nm', '--undefined-only', 'extension.elf').strip():
        raise ValueError('Undefined classic-letter import')
    defined = {}
    for line in run('nm', '--defined-only', 'extension.elf').splitlines():
        parts = line.split()
        if len(parts) == 3:
            defined[parts[2]] = int(parts[0], 16)
    run('objcopy', '-O', 'binary', 'extension.elf', 'extension.bin')
    extension = (out/'extension.bin').read_bytes()
    end = start+len(extension)
    if defined.get('__classic_start') != start or defined.get('__classic_end') != end or not 0 < len(extension) <= 0x1000:
        raise ValueError('Invalid classic-letter section ownership')
    entries, inventory = normalized_rows(reloc, prefix), []
    listing = run('readelf', '-rW', 'extension.elf')
    for line in listing.splitlines():
        if 'R_MIPS_' not in line:
            continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*', line)
        if not match:
            raise ValueError('Unapproved classic-letter ELF relocation: '+line)
        at, kind_code, target, name = int(match[1], 16), KINDS[match[2]], int(match[3], 16), match[4]
        if not start <= at < end or at & 3:
            raise ValueError('Classic-letter relocation escapes its appended image')
        inventory.append([at-ram, kind_code, target, name])
        if ram <= target < end:
            if not (start <= target < end or imports.get(name) == target) or at-ram in entries:
                raise ValueError('Unapproved classic-letter prefix import')
            entries[at-ram] = kind_code
        elif kind_code != 4 or imports.get(name) != target:
            raise ValueError('Changed classic-letter resident import')
    final = bytearray(data+extension)
    patches = []
    if kind == 'font':
        target = defined[entry]
        replacement = struct.pack('>2I', 0x08000000 | ((target >> 2) & 0x3FFFFFF), 0)
        patches.append({'at': 0, 'before': data[:8].hex(), 'after': replacement.hex()})
        final[:8] = replacement
        entries.pop(4, None)
        entries[0] = 4
    final = bytes(final)
    packed = packed_rows(entries, len(final))
    if len(final) > limit or len(packed) > 0x1000:
        raise ValueError(f'Classic-letter {kind} exceeds existing loader bounds: {len(final)} / {limit}')
    spec = Overlay(ram, len(final), struct.unpack_from('>5I', packed))
    for base in (0x801A0010, 0x802F8010):
        moved = relocate_verified_data(spec, final, packed, base)
        old = (relocate_font(data, reloc, base, mail_literals=True) if kind == 'font' else
               relocate_verified_data(Overlay(ram, prefix, struct.unpack_from('>5I', reloc)), data, reloc, base))
        first = 8 if kind == 'font' else 0
        if moved[first:prefix] != old[first:prefix]:
            raise ValueError('Classic-letter relocation changes retained code, glyphs, or state')
    if source_hashes() != hashes:
        raise ValueError('Classic-letter compilation inputs changed during the build')
    report = {'version': 1, 'kind': kind, 'ram': ram, 'bytes': len(final),
              'sha256': sha256(final), 'relocation_bytes': len(packed), 'relocation_sha256': sha256(packed),
              'entry_offset': defined[entry]-ram, 'prefix_bytes': prefix,
              'previous_sha256': sha256(data), 'previous_relocation': reloc.hex(),
              'previous_relocation_sha256': sha256(reloc), 'previous_profile': prior,
              'patches': patches, 'imports': imports, 'elf_relocations': inventory,
              'symbols': {k: v-ram for k, v in defined.items() if start <= v < end},
              'sources': hashes, 'toolchain_image': IMAGE, 'flags': flags,
              'stack_usage': (out/'extension.su').read_text(), 'installed': False}
    (out/'image.bin').write_bytes(final)
    (out/'relocation.bin').write_bytes(packed)
    (out/'profile.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'extension.asm').write_text(run('objdump', '-d', 'extension.elf'))
    (out/'extension-relocations.txt').write_text(listing)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/classic-letters-candidate')
    args = parser.parse_args()
    from aflib import by_vrom
    built = (BASE/'animal-forest-halfwidth.z64').read_bytes()
    previous = json.loads((BASE/'build.json').read_text())
    if sha256(built) != BASE_SHA or previous['output_sha256'] != BASE_SHA:
        raise ValueError('Classic letters require the complete reserve-letter predecessor')
    files = by_vrom(built)
    result = {}
    for kind, vrom, prior in (
            ('font', 0x03400000, previous['runtime_module']['extended_font']['font']),
            ('creator', 0x03200000, previous['runtime_module']['npc_mail_loader']['overlay'])):
        blob = files[vrom].extract(built)
        data, reloc = blob[:prior['bytes']], blob[prior['bytes']:]
        result[kind] = compile_one(kind, prior, data, reloc, args.output/kind)
    print(json.dumps({k: {n: p[n] for n in ('bytes', 'relocation_bytes', 'entry_offset', 'sha256', 'installed')}
                      for k, p in result.items()}))


if __name__ == '__main__':
    main()
