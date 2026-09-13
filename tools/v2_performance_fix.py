"""Fix the museum recipient and credits drawing budget on the preserved V2-07."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom, make_ups, apply_ups
from apply_translation import write_new
from catalogue_names import Image
from credits_strings import VROM, RAM, RELOCATION, FIRST, END, PAGES, VALUES_HASH, group_hash
from letter_ui_fix import PARTS, compile_part
from npc_mail_show import relocate_verified_data
from textbanks import Bank
from title_start_fix import reconstruct
from toolchain import IMAGE

ROOT = Path(__file__).resolve().parents[1]
BASE_SHA = '400423ea152338df763192f95c159a037453f4ddbc8711e83ef38d0a34fc8c25'
ACTOR_SHA = 'cbb0b08439b7289c3e22ff7332d953c31ad385dc2aff05983671c4a009569e12'
REL_SHA = '5b347ca673af7e0487ee7ef1a5ab68e9647ae878bb0ee70d49cbbaf9068b2123'
ADDRESS_SHA = 'fdb4633fcbf23f003609ac9c7d9881c9a5a6222bc547b11b40bffd7991fedc2f'
ADDRESS_REL_SHA = '261281a57dd1f8419988269a10f486e427a251ae739f15188e134c353b3888f8'
CALL, CAVE, CAVE_END = 0x80AA3FFC, 0x80AA47A4, 0x80AA47E8
DRAW = 0x80090E1C
BRANCH = 0x04110000 | ((CAVE-CALL-4)//4 & 0xFFFF)
SOURCES = ('tools/v2_performance_fix.py', 'overlays/credits/trim.s',
           'overlays/letter_ui/address.c', 'overlays/letter_ui/ui.h')


def credits_rows(rom):
    files = by_vrom(rom)
    rows = Bank('string', 0x2600000, 0xD18000, files[0x2600000].extract(rom),
                files[0xD18000].extract(rom)).entries()[FIRST:END]
    if group_hash(rows) != VALUES_HASH or any(len(row) > 25 for row in rows):
        raise ValueError('Changed complete credit wording')
    return rows


def compile_trim(out):
    out.mkdir(parents=True, exist_ok=False)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                              check=True, capture_output=True, text=True, timeout=60).stdout
    run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'trim.o', '/source/overlays/credits/trim.s')
    run('ld', '-EB', '-Ttext', hex(CAVE), '-e', 'af_credits_line', '-o', 'trim.elf', 'trim.o')
    if run('nm', '--undefined-only', 'trim.elf').strip():
        raise ValueError('Unresolved credits adapter symbol')
    run('objcopy', '-O', 'binary', '-j', '.text', 'trim.elf', 'trim.bin')
    code = (out/'trim.bin').read_bytes()
    # Independent instruction encoding binds the no-stack ABI and branch targets.
    expected = struct.pack('>14I', 0x18C00009, 0x00A64021, 0x240A0020,
        0x9109FFFF, 0x2508FFFF, 0x152A0006, 0, 0x24C6FFFF, 0x1CC0FFFA, 0,
        0x03E00008, 0, 0x08000000 | (DRAW >> 2 & 0x3FFFFFF), 0)
    if not 56 <= len(code) <= CAVE_END-CAVE or code[:56] != expected or any(code[56:]):
        raise ValueError('Credits adapter differs from its independently checked instructions')
    write_new(out/'trim.asm', run('objdump', '-d', 'trim.elf').encode())
    return code.ljust(CAVE_END-CAVE, b'\0')


def patch_credits(actor, relocation, adapter):
    if sha256(actor) != ACTOR_SHA or sha256(relocation) != REL_SHA:
        raise ValueError('Changed current credits owner')
    if len(adapter) != CAVE_END-CAVE or any(actor[CAVE-RAM:CAVE_END-RAM]):
        raise ValueError('Credits adapter cave is not the verified unused song-helper tail')
    if struct.unpack_from('>I', actor, CALL-RAM)[0] != 0x0C000000 | (DRAW >> 2 & 0x3FFFFFF):
        raise ValueError('Changed credits line call')
    sections = struct.unpack_from('>5I', relocation)
    for (row,) in struct.iter_unpack('>I', relocation[20:20+4*sections[4]]):
        at = row & 0xFFFFFF
        if (row >> 30) == 1 and (CAVE-RAM <= at < CAVE_END-RAM or at == CALL-RAM):
            raise ValueError('Credits adapter must not overlap an existing relocation')
    result = bytearray(actor)
    result[CAVE-RAM:CAVE_END-RAM] = adapter
    struct.pack_into('>I', result, CALL-RAM, BRANCH)
    for base in (0x80200010, 0x80378018):
        relocated = relocate_verified_data(Image(RAM, len(actor)+sections[3], sections),
                                          bytes(result), relocation, base, base_alignment=8)
        if (struct.unpack_from('>I', relocated, CALL-RAM)[0] != BRANCH
                or relocated[CAVE-RAM:CAVE_END-RAM] != adapter):
            raise ValueError('Credits adapter changes under native relocation')
    return bytes(result)


def build(native, base, out):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Performance correction requires exact V2-07')
    sources = {p: sha256((ROOT/p).read_bytes()) for p in SOURCES}
    files = by_vrom(base); spec = PARTS['address']
    old_address = files[spec['new_vrom']].extract(base)
    old_rel = files[spec['new_reloc']].extract(base)
    if sha256(old_address) != ADDRESS_SHA or sha256(old_rel) != ADDRESS_REL_SHA:
        raise ValueError('Changed preceding address-list helper')
    # Recompile the same original native prefix; install it only in the current ROM.
    address, address_rel, profile = compile_part('address', native, out/'address')
    if (len(old_address)+63)//64 != (len(address)+63)//64:
        raise ValueError('Museum display must fit the existing rounded address allocation')
    for offset, (old, new) in enumerate(zip(old_address[:7392], address[:7392])):
        if old != new and offset not in profile['touched_offsets']:
            raise ValueError('Museum display changes unrelated native address code')
    owner = bytearray(files[0x7749C0].extract(base)); at = spec['owner_at']
    if struct.unpack_from('>4I', owner, at) != (spec['new_vrom'], spec['new_vrom']+len(old_address),
                                               spec['ram'], spec['ram']+len(old_address)):
        raise ValueError('Changed current address allocation owner')
    struct.pack_into('>4I', owner, at, spec['new_vrom'], spec['new_vrom']+len(address),
                     spec['ram'], spec['ram']+len(address))
    adapter = compile_trim(out/'credits')
    actor = patch_credits(files[VROM].extract(base), files[RELOCATION].extract(base), adapter)
    rows = credits_rows(base)
    changes = {VROM: actor, spec['new_vrom']: address, spec['new_reloc']: address_rel, 0x7749C0: bytes(owner)}
    image = reconstruct(native, base, changes, resized=(spec['new_vrom'], spec['new_reloc']))
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image or credits_rows(image) != rows:
        raise ValueError('Performance patch reconstruction or text preservation failed')
    if sources != {p: sha256((ROOT/p).read_bytes()) for p in SOURCES}:
        raise ValueError('Sources changed during compilation')
    return image, patch, {'build': 'V2-08', 'baseline_sha256': BASE_SHA, 'source_sha256': sha256(native),
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'sources': sources,
        'toolchain': IMAGE, 'address': profile, 'address_allocation_growth': 0,
        'credits_adapter_sha256': sha256(adapter), 'credits_actor_sha256': sha256(actor),
        'credits_relocation_unchanged': True, 'credits_allocation_unchanged': True,
        'credit_rows_unchanged': True, 'credit_pages_unchanged': True,
        'audio_code_unchanged': True, 'save_format_changed': False, 'required_ram_bytes': 0x800000,
        'ups_roundtrip': True, 'native_validation': 'pending', 'hardware_retest': 'pending',
        'changed_resources': {f'{v:08X}': sha256(data) for v, data in changes.items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'build/v2-performance-fix-08')
    args = p.parse_args(); out = args.output.resolve()
    if not out.is_relative_to(ROOT/'build') or out.exists():
        raise ValueError('Choose a fresh output directory inside ignored build/')
    out.mkdir(parents=True)
    image, patch, report = build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/v2-map-suffix-07/Animal Forest English V2.z64').read_bytes(), out)
    for name, raw in {'Animal Forest English V2.z64': image, 'Animal Forest English V2.ups': patch,
                      'build.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(out/name, raw)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
