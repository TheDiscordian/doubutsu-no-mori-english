#!/usr/bin/env python3
"""Compile the owner-editor core and bound local sources for overlay integration."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256, verified_rom
from check_keyboard_assembly import IMAGE
from gyroid_default import DEFAULT, native_sources, reference_payloads
from hboard_editor import ROOT, audit
from runtime_module import module_command_info


def build(native, out):
    evidence = audit(native)
    saved = native_sources(native)['string'][DEFAULT]
    english = reference_payloads(native, module_command_info(native))[0]
    paths = ('runtime/hboard_editor.c', 'runtime/hboard_editor.h',
             'tools/hboard_editor.py', 'tools/build_hboard_editor_core.py')
    sources = {name: sha256((ROOT/name).read_bytes()) for name in paths}
    out.mkdir(parents=True, exist_ok=True)
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
    run('gcc', *flags, '/source/runtime/hboard_editor.c', '-o', 'core.o')
    undefined = run('nm', '--undefined-only', 'core.o').strip()
    if undefined: raise ValueError('Owner-editor core must not require libc or unbound imports: '+undefined)
    stack = (out/'core.su').read_text()
    sections = run('size', '-A', 'core.o')
    for name, content in (('core.asm', run('objdump', '-dr', 'core.o')),
                          ('core-sections.txt', sections),
                          ('core-symbols.txt', run('nm', '-S', '--defined-only', 'core.o'))):
        (out/name).write_text(content)
    (out/'saved-default.bin').write_bytes(saved)
    (out/'english-default.bin').write_bytes(english)
    evidence.update({'source_sha256': sources, 'toolchain_image': IMAGE, 'flags': flags,
                     'compiler': run('gcc', '--version').splitlines()[0], 'stack_usage': stack,
                     'sections': sections, 'object_sha256': sha256((out/'core.o').read_bytes()),
                     'unresolved_imports': [], 'cartridge_installed': False})
    if sources != {name: sha256((ROOT/name).read_bytes()) for name in paths}:
        raise ValueError('Owner-editor source changed during compilation')
    (out/'core.json').write_text(json.dumps(evidence, indent=2)+'\n')
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, default=ROOT/'build/hboard-editor-core')
    args = parser.parse_args()
    report = build(verified_rom(args.rom.read_bytes()), args.output.resolve())
    print(json.dumps({'object_sha256': report['object_sha256'], 'stack_usage': report['stack_usage'],
                      'sections': report['sections'], 'cartridge_installed': False}, indent=2))


if __name__ == '__main__': main()
