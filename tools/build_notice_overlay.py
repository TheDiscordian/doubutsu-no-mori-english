#!/usr/bin/env python3
"""Build a relocatable full-body notice reader and in-place initial creator."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256, verified_rom
from check_keyboard_assembly import IMAGE
from notice_overlay import (ROOT, RAM, INIT_START, INIT_END, native_sources, source_hashes,
                            imports, elf_inventory, patch_prefix, relocation_bytes, validate)
from audit_noticeboard import audit


def build(native, module, catalog, output):
    output = output.resolve()
    original, native_reloc, _, _ = native_sources(native)
    approval = audit(native, catalog)
    sources = source_hashes()
    output.mkdir(parents=True, exist_ok=True)
    (output/'native.bin').write_bytes(original)
    (output/'imports.ld').write_text(''.join(f'{name} = 0x{value:08X};\n'
                                           for name, value in imports(module).items()))
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{output}:/out', '-w', '/out', '--entrypoint']

    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode: raise ValueError(f'Notice {tool} failed: '+result.stdout+result.stderr)
        return result.stdout

    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
             '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
             '-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses', '-fstack-usage',
             '-Wall', '-Wextra', '-Werror']
    units = {name: 'runtime/notice/'+name+'.c' for name in ('record', 'initial', 'page')}
    units['reader'] = 'overlays/notice/reader.c'
    for name, path in units.items(): run('gcc', *flags, '/source/'+path, '-o', name+'.o')
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-I/out', '-o', 'native.o', '/source/overlays/notice/reader.s')
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/notice/reader.ld', '-Map=overlay.map',
        '-o', 'overlay.elf', 'native.o', *(name+'.o' for name in units))
    if run('nm', '--undefined-only', 'overlay.elf').strip(): raise ValueError('Unresolved notice import')
    symbols = {}
    for line in run('nm', '--defined-only', 'overlay.elf').splitlines():
        fields = line.split()
        if len(fields) == 3: symbols[fields[2]] = int(fields[0], 16)
    run('objcopy', '-O', 'binary', '-j', '.text', 'overlay.elf', 'overlay.bin')
    data = bytearray((output/'overlay.bin').read_bytes())
    exports = {name: value-RAM for name, value in symbols.items()
               if name.startswith('af_notice_') and name not in imports(module)}
    data[:len(original)] = patch_prefix(native, exports)
    if symbols['__notice_end'] != RAM+len(data): raise ValueError('Notice linked bounds disagree')
    elf_text = run('readelf', '-rW', 'overlay.elf')
    inventory = elf_inventory(elf_text)
    reloc = relocation_bytes(native_reloc, inventory, len(data), module)
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'init.o', '/source/overlays/notice/initial.s')
    run('ld', '-EB', '-Ttext', f'0x{INIT_START:X}', '-e', 'af_notice_native_init', '-o', 'init.elf', 'init.o')
    run('objcopy', '-O', 'binary', '-j', '.text', 'init.elf', 'init.bin')
    init = (output/'init.bin').read_bytes()
    if len(init) > INIT_END-INIT_START: raise ValueError('Initial creator exceeds native function')
    init = init.ljust(INIT_END-INIT_START, b'\0')
    report = {'version': 1, 'ram': RAM, 'bytes': len(data), 'overlay_sha256': sha256(data),
              'suffix_sha256': sha256(data[0x1A80:]), 'relocation_bytes': len(reloc),
              'relocation_sha256': sha256(reloc), 'init_sha256': sha256(init), 'sources': sources,
              'module_sha256': module['module_sha256'], 'imports': imports(module), 'symbols': exports,
              'code_end': symbols['__notice_code_end']-RAM, 'bss_start': symbols['__notice_bss_start']-RAM,
              'elf_relocations': inventory, 'approval': approval, 'flags': flags, 'toolchain_image': IMAGE,
              'compiler': run('gcc', '--version').splitlines()[0],
              'stack_usage': {name: (output/(name+'.su')).read_text() for name in units}}
    if source_hashes() != sources: raise ValueError('Notice sources changed during compilation')
    (output/'overlay.bin').write_bytes(data)
    (output/'relocation.bin').write_bytes(reloc)
    (output/'init.bin').write_bytes(init)
    (output/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (output/'elf-relocations.txt').write_text(elf_text)
    (output/'overlay.asm').write_text(run('objdump', '-d', 'overlay.elf'))
    (output/'init.asm').write_text(run('objdump', '-d', 'init.elf'))
    validate(native, bytes(data), reloc, init, report, module, catalog)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module', type=Path, default=ROOT/'build/shop-notice-runtime/module.json')
    parser.add_argument('--catalog', type=Path, default=ROOT/'build/mail-glyph-resources/glyph-catalog.bin')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-reader')
    args = parser.parse_args()
    report = build(verified_rom(args.rom.read_bytes()), json.loads(args.module.read_text()),
                   args.catalog.read_bytes(), args.output)
    print(json.dumps({key: report[key] for key in ('bytes', 'suffix_sha256', 'overlay_sha256',
                     'relocation_bytes', 'relocation_sha256', 'init_sha256', 'symbols', 'stack_usage')}, indent=2))


if __name__ == '__main__': main()
