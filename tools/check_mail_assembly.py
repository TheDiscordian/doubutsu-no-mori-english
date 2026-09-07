#!/usr/bin/env python3
"""Cross-compile the standalone mail implementation without installing hooks."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('build/mail-assembly'))
    args = parser.parse_args()
    out = args.output.resolve()
    source = Path(__file__).resolve().parents[1]/'runtime/mail'
    out.mkdir(parents=True, exist_ok=True)
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{source}:/source:ro', '-v', f'{out}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *arguments):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *arguments],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError(f'Mail {tool} failed: {result.stdout}{result.stderr}')
        return result.stdout
    compiler = run('gcc', '--version').splitlines()[0]
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0',
             '-mno-abicalls', '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common',
             '-fno-stack-protector', '-ffunction-sections', '-fdata-sections', '-fstack-usage',
             '-Wall', '-Wextra', '-Werror']
    for name in ('record', 'format'):
        run('gcc', *flags, '/source/'+name+'.c', '-o', name+'.o')
    run('ld', '-EB', '-r', '-o', 'mail.o', 'record.o', 'format.o')
    undefined = run('nm', '--undefined-only', 'mail.o')
    if undefined.strip():
        raise ValueError('Unexpected mail runtime dependency: '+undefined)
    sections = run('size', '-A', 'mail.o')
    for line in sections.splitlines():
        columns = line.split()
        if len(columns) >= 2 and columns[0].startswith(('.data', '.bss', '.sdata', '.sbss')) and int(columns[1]):
            raise ValueError('Mail implementation unexpectedly retains mutable global state')
    assembly = run('objdump', '-d', 'mail.o')
    (out/'mail.asm').write_text(assembly)
    report = {'compiler': compiler, 'toolchain_image': IMAGE, 'compiler_flags': flags,
              'source_sha256': {path.name: sha256(path.read_bytes()) for path in sorted(source.iterdir()) if path.is_file()},
              'object_sha256': sha256((out/'mail.o').read_bytes()),
              'object_size': run('size', 'mail.o'), 'sections': sections,
              'stack_usage': {name: (out/(name+'.su')).read_text() for name in ('record', 'format')},
              'undefined_symbols': [],
              'status': 'Cross-compilation only; not installed or executed on MIPS'}
    (out/'mail.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
