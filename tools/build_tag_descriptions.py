#!/usr/bin/env python3
"""Compile complete letter/quest label composition using the pinned MIPS image."""
import argparse
import json
import os
from pathlib import Path
import subprocess
from aflib import sha256, by_vrom, CODE_VROM, CODE_RAM
from check_keyboard_assembly import IMAGE
import inventory_english as inv
import inventory_menu_text as menu
import tag_descriptions as desc


def build(native, module, base_dir, out):
    sources = desc.source_hashes()
    base = (base_dir/'overlay.bin').read_bytes()
    menu.validate(native, base, (base_dir/'relocation.bin').read_bytes(),
                  json.loads((base_dir/'overlay.json').read_text()), module)
    out = out.resolve(); out.mkdir(parents=True, exist_ok=True)
    (out/'native.bin').write_bytes(base)
    (out/'quest.bin').write_bytes(desc.quest_source(native))
    (out/'imports.ld').write_text(''.join(f'{name} = 0x{value:08X};\n' for name, value in desc.IMPORTS.items()))
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{inv.ROOT}:/source:ro', '-v', f'{out}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        r = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                           capture_output=True, text=True, timeout=60)
        if r.returncode: raise ValueError(r.stdout+r.stderr)
        return r.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
             '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
             '-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses',
             '-fstack-usage', '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/tag/descriptions.c', '-o', 'descriptions.o')
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-I/out', '-o', 'native.o', '/source/overlays/tag/descriptions.s')
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/tag/descriptions.ld', '-Map=overlay.map',
        '-o', 'overlay.elf', 'native.o', 'descriptions.o')
    if run('nm', '--undefined-only', 'overlay.elf').strip(): raise ValueError('Unresolved tag description import')
    symbols = {}
    for line in run('nm', '--defined-only', 'overlay.elf').splitlines():
        fields = line.split()
        if len(fields) == 3: symbols[fields[2]] = int(fields[0], 16)
    exports = {name: value-inv.RAM for name, value in symbols.items()
               if name.startswith('af_tag_') and name not in desc.IMPORTS}
    run('objcopy', '-O', 'binary', '-j', '.text', 'overlay.elf', 'overlay.bin')
    data = (out/'overlay.bin').read_bytes()
    if symbols['__description_start'] != inv.RAM+menu.SIZE or symbols['__description_end'] != inv.RAM+len(data):
        raise ValueError('Description link dimensions disagree')
    data = desc.patch_image(native, data, exports)
    elf = run('readelf', '-rW', 'overlay.elf'); inventory = desc.elf_inventory(elf)
    reloc = desc.relocation_data(native, inventory, exports, len(data))
    report = desc.make_report(native, data, reloc, exports, inventory)
    report.update(toolchain_image=IMAGE, flags=flags, stack_usage=(out/'descriptions.su').read_text(),
                  lines_bytes=symbols['__description_lines_end']-symbols['__description_lines_start'])
    if sources != desc.source_hashes(): raise ValueError('Description sources changed during build')
    (out/'overlay.bin').write_bytes(data); (out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'elf-relocations.txt').write_text(elf)
    (out/'overlay.asm').write_text(run('objdump', '-d', 'overlay.elf'))
    (out/'installed.asm').write_text(run('objdump', '-D', '-b', 'binary', '-m', 'mips:4300', '-EB',
                                        f'--adjust-vma={inv.RAM}', 'overlay.bin'))
    if desc.APPROVED: desc.validate(native, data, reloc, report, module)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=inv.ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module', type=Path, default=inv.ROOT/'build/notice-seasonal-runtime/module.json')
    parser.add_argument('--base', type=Path, default=inv.ROOT/'build/inventory-menu-text-overlay')
    parser.add_argument('--output', type=Path, default=inv.ROOT/'build/tag-descriptions-overlay')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(), json.loads(args.module.read_text()), args.base, args.output), indent=2))


if __name__ == '__main__': main()
