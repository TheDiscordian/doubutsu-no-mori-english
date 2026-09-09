#!/usr/bin/env python3
"""Build the persistent text extension and its bounded one-shot startup loader."""
import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import zlib

from aflib import sha256, verified_rom
from check_keyboard_assembly import IMAGE

ROOT = Path(__file__).resolve().parents[1]
RAM = 0x80D00000
IMPORTS = {
    'af_native_code_size': 0x800903A8, 'af_native_move': 0x8009EA2C, 'af_native_copy': 0x8009EB44,
    'af_load_item_name': 0x801969C8, 'af_writeback': 0x8002FE00, 'af_invalidate': 0x80034CE0,
    'af_allocate': 0x8002BC60, 'af_release': 0x8002BC90, 'af_dma': 0x80026B44,
    'af_crc32': 0x80195938, 'af_relocate': 0x8002B9C0,
}
CHOICE_IMPORTS = {'af_copy_item_string': 0x801966AC, 'af_copy_talk_name': 0x80195E2C,
                  'af_copy_catchphrase': 0x801952F4}


def relocation(data, size, imports=None):
    imports = IMPORTS if imports is None else imports
    rows, evidence = [], []
    for line in data.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*', line)
        if not match: raise ValueError('Unsupported text-extension relocation')
        at, target, symbol = int(match[1],16)-RAM, int(match[3],16), match[4]
        kind = {'32':2, '26':4, 'HI16':5, 'LO16':6}[match[2]]
        if at & 3 or not 0 <= at <= size-4: raise ValueError('Invalid text-extension relocation offset')
        if RAM <= target < RAM+size:
            rows.append(0x40000000 | kind << 24 | at)
        elif imports.get(symbol) != target or kind != 4:
            raise ValueError('Unbound text-extension external symbol: '+symbol)
        evidence.append([at, kind, target, symbol])
    if not rows or len(rows) != len(set(w & 0xFFFFFF for w in rows)):
        raise ValueError('Missing or repeated text-extension relocations')
    length = (24+len(rows)*4+15) & ~15
    result = struct.pack('>5I', size,0,0,0,len(rows))+struct.pack('>'+str(len(rows))+'I', *rows)
    return result+bytes(length-4-len(result))+struct.pack('>I',length), evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path('build/text-extension'))
    parser.add_argument('--choices', action='store_true', help='Include complete bounded shared choice substitutions')
    args = parser.parse_args()
    verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    source = ROOT/'overlays/text_extension'
    imports = {**IMPORTS, **(CHOICE_IMPORTS if args.choices else {})}
    with tempfile.TemporaryDirectory(prefix='af-text-extension-') as directory:
        out = Path(directory)
        common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
                  '-v',f'{source}:/source:ro','-v',f'{ROOT}/overlays/text_choices:/choices:ro',
                  '-v',f'{out}:/out','-w','/out','--entrypoint']
        def run(tool, *args):
            return subprocess.run(common+[f'/n64_toolchain/bin/mips64-elf-{tool}', IMAGE, *args],
                                  check=True, capture_output=True, text=True, timeout=60).stdout
        flags = ['-Os','-G0','-mabi=32','-march=vr4300','-mno-abicalls','-fno-pic',
                 '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
                 '-fno-asynchronous-unwind-tables','-fno-unwind-tables','-fno-jump-tables',
                 '-Wall','-Wextra','-Werror']
        definitions = [f'--defsym={name}={address:#x}' for name,address in imports.items()]
        rename = ['-Daf_text_extension_init=af_text_fields_init'] if args.choices else []
        run('gcc', *flags, *rename, '-c','/source/fields.c','-o','fields.o')
        objects = ['fields.o']
        if args.choices:
            run('gcc', *flags, '-I/source', '-c', '/choices/choices.c', '-o', 'choices.o')
            objects.insert(0, 'choices.o')
        run('ld','-EB','--emit-relocs','-T','/source/extension.ld',*definitions,'-o','extension.elf',*objects)
        run('objcopy','-O','binary','-j','.text','extension.elf','extension.bin')
        binary = (out/'extension.bin').read_bytes()
        if not 16 <= len(binary) <= 0x8000 or len(binary) & 15:
            raise ValueError('Text-extension image exceeds its bounded allocation')
        rel, inventory = relocation(run('readelf','-rW','extension.elf'),len(binary),imports)
        symbols = {}
        for line in run('nm','-n','extension.elf').splitlines():
            match = re.fullmatch(r'([0-9a-fA-F]+)\s+[a-zA-Z]\s+(\S+)',line)
            if match and RAM <= int(match[1],16) < RAM+len(binary):
                symbols[match[2]] = int(match[1],16)-RAM
        if symbols.get('af_text_extension_init') != 0: raise ValueError('Text-extension entry must be zero')
        blob = binary+rel
        run('gcc',*flags,f'-DAF_IMAGE_SIZE={len(binary)}u',f'-DAF_BLOB_SIZE={len(blob)}u',
            f'-DAF_BLOB_CRC=0x{zlib.crc32(blob):08x}u','-c','/source/loader.c','-o','loader.o')
        run('ld','-EB','-T','/source/loader.ld',*definitions,'-o','loader.elf','loader.o')
        run('objcopy','-O','binary','-j','.text','loader.elf','loader.bin')
        loader = (out/'loader.bin').read_bytes()
        if not 0 < len(loader) <= 336: raise ValueError('Text startup loader exceeds setter span')
        assembly = run('objdump','-d','loader.elf')
        report = {'image_bytes':len(binary),'relocation_bytes':len(rel),'blob_bytes':len(blob),
                  'loader_bytes':len(loader),'image_sha256':sha256(binary),'relocation_sha256':sha256(rel),
                  'blob_sha256':sha256(blob),'blob_crc32':f'{zlib.crc32(blob):08X}',
                  'loader_sha256':sha256(loader),'symbols':symbols,'imports':imports,
                  'elf_relocations':inventory,'compiler_image':IMAGE,
                  'sources':{p.name:sha256(p.read_bytes()) for p in sorted(source.iterdir()) if p.is_file()}}
        if args.choices:
            report['choices'] = True
            report['sources'].update({'choices/'+p.name:sha256(p.read_bytes())
                                     for p in sorted((ROOT/'overlays/text_choices').iterdir()) if p.is_file()})
        args.output.mkdir(parents=True,exist_ok=True)
        for name,data in (('extension.bin',binary),('relocation.bin',rel),('blob.bin',blob),('loader.bin',loader)):
            (args.output/name).write_bytes(data)
        (args.output/'loader.asm').write_text(assembly)
        (args.output/'extension.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({key:report[key] for key in ('image_bytes','relocation_bytes','loader_bytes','blob_sha256')},indent=2))


if __name__ == '__main__': main()
