"""Free ordinary town memory while retaining RC3's complete bordered font."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

from aflib import apply_ups, by_vrom, make_ups, sha256, verified_rom
from apply_translation import write_new
from catalogue_names import Image
from name_space_markers import BASE_SHA, VROM as NAME, RELOC as NAME_REL, patch_overlay
from npc_mail_show import relocate_verified_data
from title_start_fix import reconstruct
from toolchain import IMAGE

ROOT = Path(__file__).resolve().parents[1]
MODULE, FONT, MODULE_RAM = 0x2800000, 0x3400000, 0x801948E0
START, END, BASE, LIMIT, GUARD = 0x8019614C, 0x801963B8, 0x80450010, 0x80458000, 0xAF46C0DE
MODULE_SHA = 'cfc3905aac05a99e17ad6763604f8e85a155c24f3ef2bbd3009f96e7957d0cd8'
LOADER_SHA = '573ed9d012f0c8f57e1eccc2a16c65b8f299e1e2c30186c1fdbcc07924bc35a7'
FONT_SHA = 'eee404b58a40916500934e1bc5b80025640e35fbea6159a540753e0147c7532f'
SOURCES = ('tools/font_expansion_memory.py', 'tools/name_space_markers.py',
           'overlays/font_memory/loader.c', 'overlays/font_memory/loader.ld')


def source_hashes():
    return {name: sha256((ROOT/name).read_bytes()) for name in SOURCES}


def compile_loader(out):
    out.mkdir(parents=True, exist_ok=False)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        result = subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool, IMAGE, *args],
                                check=True, capture_output=True, text=True, timeout=60)
        return result.stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0',
             '-mno-abicalls', '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common',
             '-fno-stack-protector', '-ffunction-sections', '-fdata-sections', '-fstack-usage',
             '-Wall', '-Wextra', '-Werror']
    run('gcc', *flags, '/source/overlays/font_memory/loader.c', '-o', 'loader.o')
    run('ld', '-EB', '-T', '/source/overlays/font_memory/loader.ld', '-o', 'loader.elf', 'loader.o')
    if run('nm', '--undefined-only', 'loader.elf').strip():
        raise ValueError('Unresolved font startup symbol')
    run('objcopy', '-O', 'binary', '-j', '.text', 'loader.elf', 'loader.bin')
    code = (out/'loader.bin').read_bytes()
    if not 0 < len(code) <= END-START or len(code) & 3:
        raise ValueError('Font startup code exceeds original function')
    write_new(out/'loader.asm', run('objdump', '-d', 'loader.elf').encode())
    return code, {'bytes': len(code), 'sha256': sha256(code), 'toolchain': IMAGE,
                  'compiler': run('gcc', '--version').splitlines()[0], 'flags': flags,
                  'stack_usage': (out/'loader.su').read_text()}


def expected_font(blob, module):
    config = struct.unpack_from('>8I', module, 0x68)
    if (sha256(blob) != FONT_SHA or config[:4] != (FONT, 28528, 27744, 784)
            or config[4:6] != (27744, 0) or config[6:] != (zlib.crc32(blob), 0x41464701)
            or BASE+len(blob) > LIMIT-16):
        raise ValueError('Changed bordered font or dedicated reservation overflow')
    image, reloc = blob[:config[2]], blob[config[2]:]
    spec = Image(0x80C00000, len(image), struct.unpack_from('>5I', reloc))
    return relocate_verified_data(spec, image, reloc, BASE, memory_end=0x80800000)


def build(native, base, out):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Font memory correction requires exact V1RC3')
    sources = source_hashes()
    files = by_vrom(base)
    module = files[MODULE].extract(base)
    blob = files[FONT].extract(base)
    if (sha256(module) != MODULE_SHA
            or sha256(module[START-MODULE_RAM:END-MODULE_RAM]) != LOADER_SHA):
        raise ValueError('Changed resident module or font startup function')
    relocated = expected_font(blob, module)
    code, compiler = compile_loader(out/'loader')
    changed = bytearray(module)
    changed[START-MODULE_RAM:END-MODULE_RAM] = code.ljust(END-START, b'\0')
    name = patch_overlay(files[NAME].extract(base), files[NAME_REL].extract(base))
    image = reconstruct(native, base, {MODULE: bytes(changed), NAME: name})
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('Font memory correction UPS reconstruction failed')
    if sources != source_hashes():
        raise ValueError('Font memory sources changed during compilation')
    return image, patch, {'version': 1, 'baseline_sha256': BASE_SHA, 'source_sha256': sha256(native),
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch), 'sources': sources,
        'loader': compiler, 'module_sha256': sha256(changed), 'font_blob_sha256': FONT_SHA,
        'relocated_font_sha256': sha256(relocated), 'font_base': f'{BASE:08X}',
        'font_limit': f'{LIMIT:08X}', 'font_guard': f'{GUARD:08X}',
        'reclaimed_system_payload_bytes': 28544, 'ordinary_heap_end': '80400000',
        'changed_resources': [f'{MODULE:08X}', f'{NAME:08X}'],
        'font_pixels_and_code_unchanged': True, 'save_format_changed': False,
        'required_ram_bytes': 0x800000, 'fixed_issues': ['V1-19', 'V1-20'],
        'native_existing_save_loading': 'pending', 'hardware_retest': 'pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', type=Path, default=ROOT/'build/v1rc3/Animal Forest English V1RC3.z64')
    parser.add_argument('--native', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    image, patch, report = build(args.native.read_bytes(), args.base.read_bytes(), args.output)
    for name, value in {'animal-forest-memory-fix.z64': image, 'animal-forest-memory-fix.ups': patch,
                        'fixes.json': (json.dumps(report, indent=2)+'\n').encode()}.items():
        write_new(args.output/name, value)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
