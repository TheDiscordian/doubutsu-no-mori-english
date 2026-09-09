#!/usr/bin/env python3
"""Compile a save-preserving fishing name reader with the pinned toolchain."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
import fishing_name as f


def build(native, names, out):
    sources = f.source_hashes(); out = out.resolve(); out.mkdir(parents=True, exist_ok=True)
    (out/'native.bin').write_bytes(f.source(native)[0]); (out/'aliases.bin').write_bytes(f.aliases(native, names))
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{f.ROOT}:/source:ro', '-v', f'{out}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        r = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                           capture_output=True, text=True, timeout=60)
        if r.returncode: raise ValueError(r.stdout+r.stderr)
        return r.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
             '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
             '-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses',
             '-fstack-usage', '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/fishing/name.c', '-o', 'name.o')
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-I/out', '-o', 'native.o', '/source/overlays/fishing/image.s')
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/fishing/image.ld', '-Map=overlay.map',
        '-o', 'overlay.elf', 'native.o', 'name.o')
    if run('nm', '--undefined-only', 'overlay.elf').strip(): raise ValueError('Unresolved fishing import')
    symbols = {}
    for line in run('nm', '--defined-only', 'overlay.elf').splitlines():
        parts = line.split()
        if len(parts) == 3: symbols[parts[2]] = int(parts[0], 16)
    exports = {k: v-f.RAM for k, v in symbols.items() if k.startswith('af_fishing_') and k not in f.IMPORTS}
    if symbols['__fishing_code_start'] != f.RAM+f.START: raise ValueError('Native fishing BSS moved')
    run('objcopy', '-O', 'binary', '-j', '.text', 'overlay.elf', 'overlay.bin')
    data = bytearray((out/'overlay.bin').read_bytes()); data[:f.PREFIX] = f.patch_prefix(native, exports)
    if symbols['__fishing_end'] != f.RAM+len(data): raise ValueError('Fishing linked bounds disagree')
    elf = run('readelf', '-rW', 'overlay.elf'); inventory = f.inventory(elf, f.RAM)
    reloc = f.relocation_data(native, inventory, len(data))
    if sources != f.source_hashes(): raise ValueError('Fishing sources changed during compilation')
    report = {'bytes': len(data), 'symbols': exports, 'sources': sources, 'imports': f.IMPORTS,
              'overlay_sha256': sha256(data), 'suffix_sha256': sha256(data[f.START:]),
              'relocation_sha256': sha256(reloc), 'elf_relocations': inventory,
              'code_end': symbols['__fishing_code_end']-f.RAM, 'toolchain_image': IMAGE,
              'flags': flags, 'stack_usage': (out/'name.su').read_text()}
    (out/'overlay.bin').write_bytes(data); (out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'elf-relocations.txt').write_text(elf)
    (out/'overlay.asm').write_text(run('objdump', '-d', 'overlay.elf'))
    if f.APPROVED: f.validate(native, bytes(data), reloc, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=f.ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--names', type=Path, default=f.ROOT/'build/display-names')
    parser.add_argument('--output', type=Path, default=f.ROOT/'build/fishing-name-overlay')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(), args.names, args.output), indent=2))


if __name__ == '__main__': main()
