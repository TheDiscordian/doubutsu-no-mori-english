#!/usr/bin/env python3
"""Build the complete English tag overlay using local retail references."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
import inventory_english as inv


def build(native, module, out):
    data, _, _, _ = inv.native_sources(native)
    out.mkdir(parents=True, exist_ok=True)
    (out/'native.bin').write_bytes(data)
    (out/'labels.bin').write_bytes(inv.label_data(native))
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
             '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/tag/labels.c', '-o', 'labels.o')
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-I/out', '-o', 'native.o', '/source/overlays/tag/image.s')
    loader = int(module['symbols']['af_load_item_name'], 16)
    run('ld', '-EB', '--emit-relocs', '--defsym', f'af_load_item_name={loader}',
        '-T', '/source/overlays/tag/image.ld', '-Map=overlay.map', '-o', 'overlay.elf', 'native.o', 'labels.o')
    if run('nm', '--undefined-only', 'overlay.elf').strip(): raise ValueError('Unresolved inventory import')
    symbols = {}
    for line in run('nm', '--defined-only', 'overlay.elf').splitlines():
        parts = line.split()
        if len(parts) == 3: symbols[parts[2]] = int(parts[0], 16)
    exports = {n: symbols[n]-inv.RAM for n in ('af_tag_cells', 'af_tag_load_item', 'af_tag_labels')}
    if symbols['__tag_code_start'] != inv.RAM+inv.START: raise ValueError('Inventory BSS moved')
    run('objcopy', '-O', 'binary', '-j', '.text', 'overlay.elf', 'overlay.bin')
    output = bytearray((out/'overlay.bin').read_bytes())
    output[:inv.PREFIX] = inv.patch_prefix(native, exports)
    relocation = inv.relocation_data(native, exports, len(output))
    elf_reloc = run('readelf', '-rW', 'overlay.elf')
    # The only C relocation is an absolute external tail call. Labels are
    # imported bytes; their native action pointers receive explicit N64 rows.
    rows = [line for line in elf_reloc.splitlines() if 'R_MIPS_' in line]
    if len(rows) != 1 or 'R_MIPS_26' not in rows[0] or 'af_load_item_name' not in rows[0]:
        raise ValueError('Unexpected inventory helper relocation')
    report = {'bytes': len(output), 'symbols': exports, 'loader': loader,
              'helpers_sha256': sha256(output[inv.START:exports['af_tag_labels']]),
              'overlay_sha256': sha256(output), 'relocation_sha256': sha256(relocation),
              'sources': inv.source_hashes(), 'reference_sha256': inv.REFERENCE_SHA,
              'toolchain_image': IMAGE, 'flags': flags}
    (out/'overlay.bin').write_bytes(output); (out/'relocation.bin').write_bytes(relocation)
    (out/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'overlay.asm').write_text(run('objdump', '-d', 'overlay.elf'))
    (out/'elf-relocations.txt').write_text(elf_reloc)
    inv.validate(native, bytes(output), relocation, report, module)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=inv.ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module', type=Path, default=inv.ROOT/'build/notice-seasonal-runtime/module.json')
    parser.add_argument('--output', type=Path, default=inv.ROOT/'build/inventory-english-overlay')
    args = parser.parse_args()
    print(json.dumps(build(args.rom.read_bytes(), json.loads(args.module.read_text()), args.output.resolve()), indent=2))


if __name__ == '__main__': main()
