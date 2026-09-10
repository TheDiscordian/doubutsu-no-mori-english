#!/usr/bin/env python3
"""Cross-check every emitted title command against the pinned native GBI macros."""
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
from title_assets import ROOT
from title_graphics import package


def check(blob, report, out):
    lines = ['#include <PR/mbi.h>',
             'const Gfx checks[] __attribute__((section(".title"), aligned(8))) = {']
    expected = bytearray()
    for model in report['models']:
        start = model['package_offset']
        expected.extend(blob[start:start+model['command_bytes']])
        lines.append('gsSPTexture(65535, 65535, 0, 0, G_ON),')
        width, height = model['width'], model['height']
        texture = report['segment'] << 24 | model['texture_offset']
        for band in model['strips']:
            low, high = band['load_rows']
            vertex = report['segment'] << 24 | band['vertex_offset']
            lines.append('gsDPPipeSync(),')
            macro = (f'gsDPLoadTextureTile(0x{texture:08X}, G_IM_FMT_RGBA, G_IM_SIZ_32b,'
                     if model['palette'] else f'gsDPLoadTextureTile_4b(0x{texture:08X}, G_IM_FMT_I,')
            lines.append(macro+f'{width}, {height}, 0, {low}, {width-1}, {high-1}, 0,'
                         ' G_TX_CLAMP, G_TX_CLAMP, 0, 0, 0, 0),')
            lines.append(f'gsSPVertex(0x{vertex:08X}, 4, 0),')
            lines.append('gsSP2Triangles(0, 1, 2, 0, 0, 2, 3, 0),')
        lines.append('gsSPEndDisplayList(),')
    lines.append('};')
    out.mkdir(parents=True, exist_ok=True)
    (out/'commands.c').write_text('\n'.join(lines)+'\n')
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError('Title native GBI check failed: '+result.stdout+result.stderr)
    run('gcc', '-c', '-EB', '-mabi=32', '-march=vr4300', '-G0', '-mno-abicalls', '-fno-pic',
        '-D_LANGUAGE_C', '-DF3DEX_GBI_2', '-I/source/upstream/af/lib/ultralib/include',
        'commands.c', '-o', 'commands.o')
    run('objcopy', '-O', 'binary', '-j', '.title', 'commands.o', 'commands.bin')
    compiled = (out/'commands.bin').read_bytes()
    if compiled != expected:
        mismatch = next((i for i, (a, b) in enumerate(zip(compiled, expected)) if a != b),
                        min(len(compiled), len(expected)))
        raise ValueError(f'Emitted title commands differ from native macros at {mismatch:08X}')
    result = {'passed': True, 'models': len(report['models']), 'command_bytes': len(compiled),
              'command_sha256': sha256(compiled), 'package_sha256': sha256(blob), 'toolchain': IMAGE,
              'headers': {name: sha256((ROOT/'upstream/af/lib/ultralib/include/PR'/name).read_bytes())
                          for name in ('mbi.h', 'gbi.h', 'ultratypes.h')}, 'native_execution': False}
    (out/'check.json').write_text(json.dumps(result, indent=2)+'\n')
    return result


if __name__ == '__main__':
    blob, report = package((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                           (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    print(json.dumps(check(blob, report, ROOT/'build/title-graphics/native-gbi-check'), indent=2))
