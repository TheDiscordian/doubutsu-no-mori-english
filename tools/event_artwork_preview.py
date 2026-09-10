"""Build a local, checkpoint-restored N64 graphics fixture; never change the ROM."""
import argparse
import json
import math
import os
from pathlib import Path
import struct
import subprocess

from aflib import by_vrom, sha256
from check_keyboard_assembly import IMAGE

ROOT = Path(__file__).resolve().parents[1]
ROM_SHA = '128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19'
CODE_SHA = '07ca93bc15d2cf2f1c984d32ecc1813645726e6f0a31f4b20bcdb80c8249a308'
OBJECT = 0x03D00000
CODE, META, ASSETS, DEPTH = 0x80500000, 0x80503000, 0x80510000, 0x80600000
EDGE = b'EVNT' * 4


def matrix(values):
    if len(values) != 16:
        raise ValueError('A native matrix requires sixteen values')
    fixed = [round(v * 65536) for v in values]
    if any(not -0x80000000 <= v <= 0x7FFFFFFF for v in fixed):
        raise ValueError('Native matrix value out of range')
    return struct.pack('>32H', *[(v >> 16) & 0xFFFF for v in fixed],
                       *[v & 0xFFFF for v in fixed])


def transforms(mode):
    if mode not in (0, 1, 2):
        raise ValueError('Unknown event preview model')
    projection = matrix([1/160, 0, 0, 0, 0, 1/120, 0, 0,
                         0, 0, -1/1000, 0, 0, 0, 0, 1])
    scale = 0.018 if mode != 2 else 0.025
    angle = math.radians(25)
    c, s = math.cos(angle)*scale, math.sin(angle)*scale
    x, y = (0, -50) if mode != 2 else (-50, 50)
    model = matrix([scale, 0, 0, 0, 0, c, s, 0, 0, -s, c, 0, x, y, 500, 1])
    return projection + model


def compile_fixture(out):
    out.mkdir(parents=True, exist_ok=False)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                capture_output=True, text=True, timeout=60)
        if result.returncode:
            raise ValueError(result.stderr)
    run('gcc', '-c', '-O2', '-EB', '-mabi=32', '-march=vr4300', '-G0', '-mno-abicalls',
        '-fno-pic', '-ffreestanding', '-fno-common', '-D_LANGUAGE_C', '-DF3DEX_GBI_2',
        '-I/source/upstream/af/lib/ultralib/include', '/source/tests/fixtures/event_artwork_preview.c',
        '-o', 'preview.o')
    run('ld', '-EB', '-T', '/source/tests/fixtures/event_artwork_preview.ld', '-o', 'preview.elf', 'preview.o')
    run('objcopy', '-O', 'binary', 'preview.elf', 'preview.bin')
    code = (out/'preview.bin').read_bytes()
    if not 4 <= len(code) <= 0x2000 or len(code) % 4:
        raise ValueError('Preview exceeds its test-only code region')
    if sha256(code) != CODE_SHA:
        raise ValueError('Preview differs from the independently checked callback')
    return code


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom', type=Path, default=ROOT/'build/title-stall-combined-01/animal-forest-title-preview.z64')
    p.add_argument('--output', type=Path, default=ROOT/'build/event-artwork-preview-fixture-01')
    args = p.parse_args()
    rom = args.rom.read_bytes()
    if sha256(rom) != ROM_SHA:
        raise ValueError('Event preview requires the exact combined stall cartridge')
    code = compile_fixture(args.output)
    actions = [{'wait': 12}, {'save_state': True}, {'pause_game_thread': True},
               {'test_event_artwork_preview': {'setup': True, 'code': code.hex()}}]
    for mode, name in enumerate(('stall-left', 'stall-right', 'fortune-table')):
        if mode:
            actions.append({'pause_game_thread': True})
        actions += [{'test_event_artwork_preview': {'select': mode}}, {'resume': True}, {'wait': 2},
                    {'capture': name+'.png'}, {'pause_game_thread': True},
                    {'test_event_artwork_preview': {'verify': mode}}, {'resume': True}]
    actions += [{'load_state': True}, {'wait': 2}, {'pause_game_thread': True},
                {'test_event_artwork_preview': {'restored': True}}, {'resume': True}]
    with (args.output/'scenario.json').open('x') as output:
        json.dump(actions, output, indent=2)
    print(json.dumps({'output': str(args.output), 'code_bytes': len(code), 'code_sha256': sha256(code),
                      'object_sha256': sha256(by_vrom(rom)[OBJECT].extract(rom)),
                      'ordinary_scene': False, 'rom_modified': False}))


if __name__ == '__main__':
    main()
