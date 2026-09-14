"""Build relocatable native speed-bag callbacks with an explicit sound dependency."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import by_vrom, sha256, verified_rom
from apply_translation import write_new
from toolchain import IMAGE
from v3_import_catalog import ROOT

ORIGIN = 0x80000000
ENTRIES = ('af_v3_speed_bag_ct', 'af_v3_speed_bag_mv', 'af_v3_speed_bag_dw')
ENGINE = {'cKF_SkeletonInfo_R_ct': 0x80052228,
          'cKF_SkeletonInfo_R_init_standard_stop': 0x80052298,
          'cKF_SkeletonInfo_R_play': 0x800528D4,
          'cKF_Si3_draw_R_SV': 0x800530D8,
          'Lib_SegmentedToVirtual': 0x8009ADA8,
          '_Matrix_to_Mtx_new': 0x800E13C4}
SOURCE_FILES = ('overlays/v3/speed_bag.c', 'overlays/v3/speed_bag.ld', 'tools/v3_speed_bag.py')


def native_contract(native):
    verified_rom(native)
    owner = by_vrom(native)[0x82D7F0].extract(native)
    if sha256(owner) != '4c67db43a7cebe9a35119621a13bac2fe8cb977cd7ab894b6b5e6b08e1d296a0':
        raise ValueError('Changed complete native room owner')
    def words(at, count):
        return struct.unpack_from('>'+str(count)+'I', owner, at-0x80936710)
    if words(0x8093DC5C, 10) != (
            0x8462003C, 0x24010006, 0x10410007, 0x2401000F, 0x10410005,
            0x24010005, 0x10410003, 0x2401000D, 0x14410003, 0x8FAE0060):
        raise ValueError('Changed native furniture transition-state exclusion')
    if words(0x80945060, 4) != (0xA040012D, 0x8CB80000, 0x24840001, 0x24420740):
        raise ValueError('Changed native room switch clear or actor stride')
    return {'room_vrom': '0082D7F0', 'room_sha256': sha256(owner),
            'actor_bytes': 0x740, 'state_offset': 0x3C, 'changed_offset': 0x12D,
            'silent_native_states': [5, 6, 13, 15], 'silent_donor_states': [12, 13, 14, 15],
            'keyframe_offset': 0x134, 'joint_offset': 0x1A4, 'morph_offset': 0x1DA,
            'matrix_offset': 0x210, 'matrix_bank_bytes': 0x280,
            'game_gfx_offset': 0, 'game_frame_offset': 0xA0, 'opaque_head_offset': 0x298}


def validate_calls(code, relocation_text, targets):
    """Only fixed engine/sound JALs may depend on absolute addresses."""
    calls = []
    for line in relocation_text.splitlines():
        if 'R_MIPS_' not in line:
            continue
        fields = line.split()
        if (len(fields) != 5 or fields[2] != 'R_MIPS_26'
                or fields[4] not in targets):
            raise ValueError('Speed-bag text has an unreviewed relocation: '+line)
        at, target = int(fields[0], 16)-ORIGIN, targets[fields[4]]
        if at % 4 or not 0 <= at <= len(code)-4 or int(fields[3], 16) != target:
            raise ValueError('Speed-bag relocation escapes text or changed its target')
        word = struct.unpack_from('>I', code, at)[0]
        if word != 0x0C000000 | ((target & 0x0FFFFFFF) >> 2):
            raise ValueError('Speed-bag external call is not the checked JAL')
        calls.append({'offset': at, 'symbol': fields[4], 'target': target})
    if not calls or set(row['symbol'] for row in calls) != set(targets):
        raise ValueError('Missing speed-bag callback dependency')
    if len({row['offset'] for row in calls}) != len(calls):
        raise ValueError('Duplicate speed-bag relocation')
    # Reject unrecorded absolute jumps; relative branches remain relocatable.
    for at in range(0, len(code), 4):
        word = struct.unpack_from('>I', code, at)[0]
        if word >> 26 in (2, 3) and at not in {row['offset'] for row in calls}:
            raise ValueError('Unrecorded speed-bag absolute jump')
    return calls


def build(native, out, sound_entry):
    contract = native_contract(native)
    if sound_entry % 4 or not 0x80000400 <= sound_entry < 0x80800000:
        raise ValueError('Speed-bag sound dependency needs an aligned N64 KSEG0 entry')
    out.mkdir(parents=True, exist_ok=False)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                              check=True, capture_output=True, text=True, timeout=60).stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0',
             '-mno-abicalls', '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common',
             '-fno-stack-protector', '-ffunction-sections', '-fdata-sections', '-fstack-usage',
             '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/v3/speed_bag.c', '-o', 'code.o')
    run('ld', '-EB', '--emit-relocs', '--defsym', f'af_v3_speed_bag_sound=0x{sound_entry:08X}',
        '-T', '/source/overlays/v3/speed_bag.ld', '-o', 'code.elf', 'code.o')
    if run('nm', '--undefined-only', 'code.elf').strip():
        raise ValueError('Unresolved speed-bag dependency')
    symbols = {name: int(at, 16) for at, kind, name in
               (line.split() for line in run('nm', '--defined-only', 'code.elf').splitlines())}
    run('objcopy', '-O', 'binary', '-j', '.text', 'code.elf', 'code.bin')
    code = (out/'code.bin').read_bytes()
    targets = {**ENGINE, 'af_v3_speed_bag_sound': sound_entry}
    if any(symbols.get(name) != at for name, at in targets.items()):
        raise ValueError('Speed-bag linker changed an external entry')
    relocations = run('readelf', '-rW', 'code.elf')
    calls = validate_calls(code, relocations, targets)
    entries = {name: symbols[name]-ORIGIN for name in ENTRIES}
    if entries[ENTRIES[0]] != 0 or any(n % 4 or not 0 <= n < len(code) for n in entries.values()):
        raise ValueError('Invalid speed-bag callback entries')
    report = {'format': 'AFV3-SPEED-BAG-CALLBACKS-1', 'native_contract': contract,
              'bytes': len(code), 'sha256': sha256(code), 'entry_offsets': entries,
              'external_calls': calls, 'compiler_image': IMAGE, 'flags': flags,
              'source_sha256': {p: sha256((ROOT/p).read_bytes()) for p in SOURCE_FILES},
              'stack_usage': (out/'code.su').read_text(),
              'sound_entry': sound_entry, 'sound_dependency_verified': False,
              'runtime_installed': False, 'selectable': False}
    write_new(out/'code.asm', run('objdump', '-d', 'code.elf').encode())
    write_new(out/'relocations.txt', relocations.encode())
    write_new(out/'callbacks.json', (json.dumps(report, indent=2)+'\n').encode())
    return code, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--sound-entry', type=lambda s: int(s, 0), required=True,
                        help='Explicit implementation or private-test sound hook; never an implicit GC sound ID')
    args = parser.parse_args()
    _, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                      args.output, args.sound_entry)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
