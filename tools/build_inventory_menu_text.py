#!/usr/bin/env python3
"""Append complete category and confirmation text to the inventory image."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from check_keyboard_assembly import IMAGE
import inventory_english as inv
import inventory_menu_text as menu


def build(native, module, base_dir, output):
    base = (base_dir/'overlay.bin').read_bytes(); reloc = (base_dir/'relocation.bin').read_bytes()
    inv.validate(native, base, reloc, json.loads((base_dir/'overlay.json').read_text()), module)
    if len(base) != menu.BASE_SIZE: raise ValueError('Expected base inventory profile')
    sources = menu.source_hashes(); output = output.resolve(); output.mkdir(parents=True, exist_ok=True)
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{inv.ROOT}:/source:ro', '-v', f'{output}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode: raise ValueError(result.stdout+result.stderr)
        return result.stdout
    run('as', '-EB', '-mabi=32', '-march=vr4300', '--defsym', 'af_tag_throw_cells=7',
        '-o', 'clamp.o', '/source/overlays/tag/menu_text.s')
    run('ld', '-EB', '-Ttext', f'0x{inv.RAM+menu.CODE_AT:08X}', '--defsym', 'af_tag_width_resume=0x8086FB88',
        '-e', 'af_tag_throw_fit', '-o', 'clamp.elf', 'clamp.o')
    run('objcopy', '-O', 'binary', '-j', '.text', 'clamp.elf', 'clamp.bin')
    if (output/'clamp.bin').read_bytes() != menu.helper(native):
        raise ValueError('Independent menu width-clamp assembly disagrees')
    data, reloc = menu.build_image(native, base), menu.relocation_data(native)
    report = menu.make_report(native, data, reloc)
    if sources != menu.source_hashes(): raise ValueError('Menu clamp source changed during compilation')
    report['toolchain_image'] = IMAGE
    menu.validate(native, data, reloc, report, module)
    (output/'overlay.bin').write_bytes(data); (output/'relocation.bin').write_bytes(reloc)
    (output/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (output/'clamp.asm').write_text(run('objdump', '-d', 'clamp.elf'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=inv.ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module', type=Path, default=inv.ROOT/'build/notice-seasonal-runtime/module.json')
    parser.add_argument('--base', type=Path, default=inv.ROOT/'build/inventory-english-overlay')
    parser.add_argument('--output', type=Path, default=inv.ROOT/'build/inventory-menu-text-overlay')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(), json.loads(args.module.read_text()), args.base, args.output), indent=2))


if __name__ == '__main__': main()
