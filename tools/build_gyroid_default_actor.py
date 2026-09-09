#!/usr/bin/env python3
"""Build the save-preserving full-default Haniwa actor with the pinned toolchain."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256, verified_rom
from check_keyboard_assembly import IMAGE
from gyroid_default import native_sources as text_sources, DEFAULT
from gyroid_default_actor import (ROOT, RAM, SIZE, SYMBOLS, native_sources, patch_prefix,
                                  source_hashes, elf_inventory, relocation_bytes, validate)


def build(native, out):
    original, native_reloc = native_sources(native); saved = text_sources(native)['string'][DEFAULT]
    sources = source_hashes(); out.mkdir(parents=True, exist_ok=True)
    (out/'native.bin').write_bytes(original); (out/'saved-default.bin').write_bytes(saved)
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode: raise ValueError(f'Gyroid actor {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls', '-fno-pic',
             '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector', '-fno-merge-constants',
             '-mno-explicit-relocs', '-mno-split-addresses', '-fstack-usage', '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/gyroid_default/default.c', '-o', 'default.o')
    for source, target in (('default.s', 'adapter.o'), ('actor.s', 'native.o')):
        run('as', '-EB', '-mabi=32', '-march=vr4300', '-I/out', '-o', target, '/source/overlays/gyroid_default/'+source)
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/gyroid_default/actor.ld', '-Map=overlay.map',
        '-o', 'overlay.elf', 'native.o', 'default.o', 'adapter.o')
    if run('nm', '--undefined-only', 'overlay.elf').strip(): raise ValueError('Unresolved gyroid actor import')
    symbols = {}
    for line in run('nm', '--defined-only', 'overlay.elf').splitlines():
        fields = line.split()
        if len(fields) == 3: symbols[fields[2]] = int(fields[0], 16)
    exports = {n: v-RAM for n, v in symbols.items() if n.startswith('af_')}
    if (exports != SYMBOLS or symbols['__gyroid_start'] != RAM or symbols['__gyroid_end'] != RAM+SIZE
            or symbols['__gyroid_code_end'] != RAM+SYMBOLS['af_gyroid_native_default']):
        raise ValueError('Changed gyroid linked symbols or bounds')
    run('objcopy', '-O', 'binary', '-j', '.text', 'overlay.elf', 'overlay.bin')
    data = bytearray((out/'overlay.bin').read_bytes()); data[:len(original)] = patch_prefix(native)
    elf_text = run('readelf', '-rW', 'overlay.elf'); inventory = elf_inventory(elf_text)
    reloc = relocation_bytes(native_reloc)
    report = {'version': 1, 'ram': RAM, 'bytes': len(data), 'overlay_sha256': sha256(data),
              'relocation_bytes': len(reloc), 'relocation_sha256': sha256(reloc), 'sources': sources,
              'symbols': exports, 'elf_relocations': inventory, 'toolchain_image': IMAGE, 'flags': flags,
              'compiler': run('gcc', '--version').splitlines()[0], 'stack_usage': (out/'default.su').read_text()}
    if sources != source_hashes(): raise ValueError('Gyroid sources changed during compilation')
    validate(native, bytes(data), reloc, report)
    (out/'overlay.bin').write_bytes(data); (out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'elf-relocations.txt').write_text(elf_text)
    (out/'overlay.asm').write_text(run('objdump', '-d', 'overlay.elf'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, default=ROOT/'build/gyroid-default-actor')
    args = parser.parse_args()
    print(json.dumps(build(verified_rom(args.rom.read_bytes()), args.output.resolve()), indent=2))


if __name__ == '__main__': main()
