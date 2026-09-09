#!/usr/bin/env python3
"""Cross-compile the notice codec, full-body decoder, and page planner."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE

ROOT = Path(__file__).resolve().parents[1]
UNITS = ('record', 'initial', 'page')
IMPORTS = ('af_crc32', 'af_mail_next_line', 'af_mail_record_pack',
           'af_mail_record_unpack', 'af_mail_restore')
HEADERS = ('runtime/mail/record.h', 'runtime/mail/format.h', 'runtime/mail/catalog.h',
           'runtime/mail/glyph.h', 'runtime/mail/view.h', 'runtime/crc32.h')


def build(output, *, treasure=False, seasonal=False):
    units = UNITS+(('treasure',) if treasure else ())+(('seasonal',) if seasonal else ())
    imports = sorted(IMPORTS+(('af_mail_format',) if treasure or seasonal else ()))
    paths = [ROOT/'runtime/notice'/f'{name}.{suffix}' for name in units for suffix in ('c', 'h')]
    paths += [ROOT/name for name in HEADERS]
    if seasonal: paths.append(ROOT/'tools/notice_seasonal.py')
    sources = {p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()) for p in paths}
    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if seasonal:
        from notice_seasonal import compiled_resource
        resource = compiled_resource((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                     (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes())
        (output/'seasonal_data.h').write_text(resource['header'])
    common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}/runtime:/source:ro', '-v', f'{output}:/out', '-w', '/out', '--entrypoint']

    def run(tool, *args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise RuntimeError(result.stderr or result.stdout)
        return result.stdout

    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0', '-mno-abicalls',
             '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common', '-fno-stack-protector',
             '-ffunction-sections', '-fdata-sections', '-fstack-usage', '-Wall', '-Wextra', '-Werror',
             '-mno-explicit-relocs', '-mno-split-addresses', '-I/out']
    for name in units:
        run('gcc', *flags, f'/source/notice/{name}.c', '-o', f'{name}.o')
    run('ld', '-EB', '-r', '-o', 'notice.o', *(name+'.o' for name in units))
    undefined = sorted(line.split()[-1] for line in run('nm', '--undefined-only', 'notice.o').splitlines())
    if undefined != imports:
        raise ValueError('Unexpected notice runtime imports: '+repr(undefined))
    symbols = run('nm', '--defined-only', 'notice.o')
    if any(line.split()[1] in ('b', 'B', 'd', 'D', 'C', 'G', 'g', 's', 'S')
           for line in symbols.splitlines() if len(line.split()) == 3):
        raise ValueError('Notice helpers unexpectedly allocate mutable global state')
    if sources != {p.relative_to(ROOT).as_posix(): sha256(p.read_bytes()) for p in paths}:
        raise ValueError('Notice sources changed during compilation')
    report = {'sources': sources, 'flags': flags, 'toolchain_image': IMAGE,
              'compiler': run('gcc', '--version').splitlines()[0], 'imports': undefined,
              'object_sha256': sha256((output/'notice.o').read_bytes()),
              'sections': run('size', '-A', 'notice.o'),
              'stack_usage': {name: (output/(name+'.su')).read_text() for name in units},
              'symbols': symbols, 'installed': False,
              'scope': 'Relocatable VR4300 objects only; no ROM hooks or native execution'}
    if seasonal:
        report['seasonal'] = {'header_sha256': sha256(resource['header'].encode()),
                              'data_sha256': sha256(resource['data']), 'data_bytes': len(resource['data']),
                              'table_sha256': sha256(resource['table']), 'table_bytes': len(resource['table'])}
    (output/'notice.asm').write_text(run('objdump', '-dr', 'notice.o'))
    (output/'notice.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-foundation/mips')
    parser.add_argument('--treasure', action='store_true')
    parser.add_argument('--seasonal', action='store_true')
    args = parser.parse_args()
    report = build(args.output, treasure=args.treasure, seasonal=args.seasonal)
    print(json.dumps({key: report[key] for key in ('object_sha256', 'imports', 'installed')}))


if __name__ == '__main__':
    main()
