#!/usr/bin/env python3
"""Compile the owned full-name catalogue integration with the pinned toolchain."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
import catalogue_names as c


def build(native, module, out, c=c):
    stem = 'map' if c.__name__ == 'map_names' else 'catalog'
    sources = c.source_hashes()
    out = out.resolve(); out.mkdir(parents=True, exist_ok=True)
    (out/'native.bin').write_bytes(c.native_sources(native)[0])
    (out/'imports.ld').write_text(''.join(f'{name} = 0x{value:08X};\n' for name, value in c.IMPORTS.items()))
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{c.ROOT}:/source:ro', '-v', f'{out}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        r = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                           capture_output=True, text=True, timeout=60)
        if r.returncode: raise ValueError(r.stdout+r.stderr)
        return r.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
             '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
             '-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses',
             '-fstack-usage', '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, f'/source/overlays/{stem}/names.c', '-o', 'names.o')
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-I/out', '-o', 'native.o', f'/source/overlays/{stem}/image.s')
    run('ld', '-EB', '--emit-relocs', '-T', f'/source/overlays/{stem}/image.ld', '-Map=overlay.map',
        '-o', 'overlay.elf', 'native.o', 'names.o')
    if run('nm', '--undefined-only', 'overlay.elf').strip(): raise ValueError('Unresolved catalogue import')
    symbols = {}
    for line in run('nm', '--defined-only', 'overlay.elf').splitlines():
        parts = line.split()
        if len(parts) == 3: symbols[parts[2]] = int(parts[0], 16)
    exports = {name: value-c.RAM for name, value in symbols.items()
               if name.startswith(f'af_{stem}_') and name not in c.IMPORTS}
    if symbols[f'__{stem}_code_start'] != c.RAM+c.START: raise ValueError('Native BSS moved')
    run('objcopy', '-O', 'binary', '-j', '.text', 'overlay.elf', 'overlay.bin')
    data = bytearray((out/'overlay.bin').read_bytes()); data[:c.PREFIX] = c.patch_prefix(native, exports)
    if symbols[f'__{stem}_end'] != c.RAM+len(data): raise ValueError('Overlay linked bounds disagree')
    elf = run('readelf', '-rW', 'overlay.elf'); inventory = c.elf_inventory(elf)
    reloc = c.relocation_data(native, inventory, len(data))
    if sources != c.source_hashes(): raise ValueError('Catalogue sources changed during compilation')
    report = {'bytes': len(data), 'symbols': exports, 'sources': sources, 'imports': c.IMPORTS,
              'overlay_sha256': sha256(data), 'suffix_sha256': sha256(data[c.START:]),
              'relocation_sha256': sha256(reloc), 'elf_relocations': inventory,
              'code_end': symbols[f'__{stem}_code_end']-c.RAM, 'bss_start': symbols[f'__{stem}_bss_start']-c.RAM,
              'toolchain_image': IMAGE, 'flags': flags, 'stack_usage': (out/'names.su').read_text()}
    (out/'overlay.bin').write_bytes(data); (out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'elf-relocations.txt').write_text(elf)
    (out/'overlay.asm').write_text(run('objdump', '-d', 'overlay.elf'))
    if c.APPROVED: c.validate(native, bytes(data), reloc, report, module)
    else: report['approval_required_before_installation'] = True
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=c.ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module', type=Path, default=c.ROOT/'build/notice-seasonal-runtime/module.json')
    parser.add_argument('--output', type=Path, default=c.ROOT/'build/catalogue-names-overlay')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(), json.loads(args.module.read_text()), args.output), indent=2))


if __name__ == '__main__': main()
