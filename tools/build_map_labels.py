#!/usr/bin/env python3
"""Build bounded GameCube-English map labels over the complete name cache."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
import map_labels as l
import map_names as m


def build(native, module, baseline, out):
    out = out.resolve(); out.mkdir(parents=True, exist_ok=True)
    before = (baseline/'overlay.bin').read_bytes()
    m.validate(native, before, (baseline/'relocation.bin').read_bytes(),
               json.loads((baseline/'overlay.json').read_text()), module)
    sources, reference = l.source_hashes(), l.reference()
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{l.ROOT}:/source:ro', '-v', f'{out}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
             '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
             '-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses',
             '-fstack-usage', '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/map/labels.c', '-o', 'labels.o')
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/map/labels.ld', '-o', 'labels.elf', 'labels.o')
    if run('nm', '--undefined-only', 'labels.elf').strip(): raise ValueError('Unresolved map label import')
    symbols = {}
    for line in run('nm', '--defined-only', 'labels.elf').splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] in ('af_map_label_draw', 'af_map_labels'):
            symbols[parts[2]] = int(parts[0], 16)-m.RAM
    run('objcopy', '-O', 'binary', '-j', '.text', 'labels.elf', 'labels.bin')
    suffix = (out/'labels.bin').read_bytes()
    data = l.patch_prefix(native, symbols)+before[m.PREFIX:]+suffix
    elf = run('readelf', '-rW', 'labels.elf'); inventory = m.elf_inventory(elf)
    reloc = l.relocation_data(native, inventory, len(data))
    if sources != l.source_hashes(): raise ValueError('Map label sources changed during compilation')
    report = {'labels': True, 'bytes': len(data), 'symbols': {**m.APPROVED['symbols'], **symbols},
              'sources': sources, 'imports': m.IMPORTS, 'references': reference,
              'overlay_sha256': sha256(data), 'suffix_sha256': sha256(suffix),
              'relocation_sha256': sha256(reloc), 'elf_relocations': inventory,
              'toolchain_image': IMAGE, 'flags': flags, 'stack_usage': (out/'labels.su').read_text()}
    (out/'overlay.bin').write_bytes(data); (out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'labels.asm').write_text(run('objdump', '-d', 'labels.elf'))
    if l.APPROVED: l.validate(native, data, reloc, report, module)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=l.ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module', type=Path, default=l.ROOT/'build/notice-seasonal-runtime/module.json')
    parser.add_argument('--baseline', type=Path, default=l.ROOT/'build/map-names-overlay')
    parser.add_argument('--output', type=Path, default=l.ROOT/'build/map-labels-overlay')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(), json.loads(args.module.read_text()), args.baseline, args.output), indent=2))


if __name__ == '__main__': main()
