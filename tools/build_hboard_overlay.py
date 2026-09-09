#!/usr/bin/env python3
"""Compile the complete owner-message editor and in-place window bridge."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256, verified_rom
from check_keyboard_assembly import IMAGE
from gyroid_default import DEFAULT, native_sources as default_sources, reference_payloads
from hboard_editor import audit, EDITOR, EDITOR_RELOC
from hboard_overlay import (ROOT, RAM, CODE_START, IMPORTS, native_sources, source_hashes,
                             patch_editor, elf_inventory, relocation_bytes, validate, window_bytes)
from runtime_module import module_command_info


def build(native, out):
    originals = native_sources(native); sources = source_hashes(); approval = audit(native)
    out = out.resolve(); out.mkdir(parents=True, exist_ok=True)
    (out/'native.bin').write_bytes(originals[EDITOR])
    (out/'saved-default.bin').write_bytes(default_sources(native)['string'][DEFAULT])
    (out/'english-default.bin').write_bytes(reference_payloads(native, module_command_info(native))[0])
    (out/'imports.ld').write_text(''.join(f'{name} = 0x{value:08X};\n' for name, value in IMPORTS.items()))
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode: raise ValueError(f'Owner-editor {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls', '-fno-pic',
             '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector', '-fno-merge-constants',
             '-mno-explicit-relocs', '-mno-split-addresses', '-fstack-usage', '-Wall', '-Wextra', '-Werror']
    for name, source in (('core', 'runtime/hboard_editor.c'), ('editor', 'overlays/hboard/editor.c')):
        run('gcc', *flags, '/source/'+source, '-o', name+'.o')
    for name, source in (('native', 'editor.s'), ('window', 'window.s')):
        run('as', '-EB', '-mabi=32', '-march=vr4300', '-I/out', '-o', name+'.o', '/source/overlays/hboard/'+source)
    run('objcopy', '-O', 'binary', '-j', '.text', 'window.o', 'window.bin')
    if (out/'window.bin').read_bytes() != window_bytes(): raise ValueError('Changed window bridge assembly')
    run('ld', '-EB', '--emit-relocs', '-T', '/source/overlays/hboard/editor.ld', '-Map=overlay.map',
        '-o', 'overlay.elf', 'native.o', 'core.o', 'editor.o')
    if run('nm', '--undefined-only', 'overlay.elf').strip(): raise ValueError('Unresolved owner-editor import')
    symbols = {}
    for line in run('nm', '--defined-only', 'overlay.elf').splitlines():
        fields = line.split()
        if len(fields) == 3: symbols[fields[2]] = int(fields[0], 16)
    exports = {name: value-RAM for name, value in symbols.items() if name.startswith('af_hboard_') and name not in IMPORTS}
    run('objcopy', '-O', 'binary', '-j', '.text', 'overlay.elf', 'overlay.bin')
    data = bytearray((out/'overlay.bin').read_bytes()); data[:len(originals[EDITOR])] = patch_editor(native, exports)
    if symbols['__hboard_end'] != RAM+len(data): raise ValueError('Owner-editor linked bounds disagree')
    elf_text = run('readelf', '-rW', 'overlay.elf'); inventory = elf_inventory(elf_text)
    reloc = relocation_bytes(originals[EDITOR_RELOC], inventory, len(data))
    report = {'version': 1, 'ram': RAM, 'bytes': len(data), 'overlay_sha256': sha256(data),
              'suffix_sha256': sha256(data[CODE_START:]), 'relocation_bytes': len(reloc),
              'relocation_sha256': sha256(reloc), 'sources': sources, 'approval': approval,
              'symbols': exports, 'imports': IMPORTS, 'elf_relocations': inventory,
              'code_end': symbols['__hboard_code_end']-RAM, 'bss_start': symbols['__hboard_bss_start']-RAM,
              'toolchain_image': IMAGE, 'flags': flags, 'compiler': run('gcc', '--version').splitlines()[0],
              'stack_usage': {name: (out/(name+'.su')).read_text() for name in ('core', 'editor')}}
    if sources != source_hashes(): raise ValueError('Owner-editor sources changed during compilation')
    (out/'overlay.bin').write_bytes(data); (out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'elf-relocations.txt').write_text(elf_text)
    (out/'overlay.asm').write_text(run('objdump', '-d', 'overlay.elf'))
    validate(native, bytes(data), reloc, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, default=ROOT/'build/hboard-editor-overlay')
    args = parser.parse_args()
    report = build(verified_rom(args.rom.read_bytes()), args.output)
    print(json.dumps({key: report[key] for key in ('bytes', 'suffix_sha256', 'relocation_bytes', 'symbols', 'stack_usage')}, indent=2))


if __name__ == '__main__': main()
