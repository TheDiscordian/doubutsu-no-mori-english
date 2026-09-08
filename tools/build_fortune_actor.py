#!/usr/bin/env python3
"""Append complete fortune-letter hand-off to the verified native Miko overlay."""

import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import sha256, verified_rom
from check_keyboard_assembly import IMAGE
from fortune_actor import (RAM, INSTANCE_BYTES, PROFILE_SIZE, INIT_SLOT, GIVE_SLOT,
                           INTERNAL_IMPORTS, WORDS_HASH, native_sources, source_hashes,
                           imports_for, elf_inventory, relocation_bytes, validate,patch_prefix)


def build(rom,module,words,out):
    native,native_reloc = native_sources(rom)
    if len(words) != 1088 or sha256(words) != WORDS_HASH:
        raise ValueError('Complete Miko phrase resource changed')
    sources = source_hashes();imports = imports_for(module)
    root = Path(__file__).resolve().parents[1]
    out.mkdir(parents=True,exist_ok=True)
    (out/'native.bin').write_bytes(native);(out/'words.bin').write_bytes(words)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{root}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(f'Miko {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    flags = ['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
             '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
             '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror']
    names = ('generate','fortune_slip','fortune_actor','fortune_recovery')
    for name in names:
        run('gcc',*flags,'/source/overlays/mail_generation/'+name+'.c','-o',name+'.o')
    run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o','native.o',
        '/source/overlays/mail_generation/fortune_actor.s')
    run('ld','-EB','--emit-relocs','-T','/source/overlays/mail_generation/fortune_actor.ld','-Map=overlay.map',
        *(f'--defsym={name}=0x{value:08X}' for name,value in {**imports,**INTERNAL_IMPORTS}.items()),
        '-o','overlay.elf','native.o',*(name+'.o' for name in names))
    if run('nm','--undefined-only','overlay.elf').strip(): raise ValueError('Undefined Miko symbol')
    symbols = {}
    for line in run('nm','--defined-only','overlay.elf').splitlines():
        fields = line.split()
        if len(fields) == 3: symbols[fields[2]] = int(fields[0],16)
    run('objcopy','-O','binary','-j','.text','-j','.rodata','overlay.elf','overlay.bin')
    data = bytearray((out/'overlay.bin').read_bytes())
    data[:3008] = patch_prefix(native,{name:value-RAM for name,value in symbols.items()})
    text = symbols['__miko_text_end']-RAM
    if symbols['__miko_start'] != RAM or symbols['__miko_end'] != RAM+len(data):
        raise ValueError('Miko linked bounds disagree with extracted data')
    elf_text = run('readelf','-rW','overlay.elf')
    inventory = elf_inventory(elf_text)
    reloc = relocation_bytes(native_reloc,inventory,imports,text,len(data))
    report = {'version':1,'ram':RAM,'bytes':len(data),'text_bytes':text,'instance_bytes':INSTANCE_BYTES,
              'overlay_sha256':sha256(data),'relocation_bytes':len(reloc),'relocation_sha256':sha256(reloc),
              'sources':sources,'imports':imports,'module_sha256':module['module_sha256'],'word_sha256':sha256(words),
              'symbols':{name:value-RAM for name,value in symbols.items() if name.startswith('af_') and RAM <= value < RAM+len(data)},
              'elf_relocations':inventory,'compiler':run('gcc','--version').splitlines()[0],
              'flags':flags,'toolchain_image':IMAGE,'stack_usage':{name:(out/(name+'.su')).read_text() for name in names},
              'status':'Native hand-off and guarded payment recovery; normal interaction, scene removal, and hardware remain unverified'}
    if source_hashes() != sources: raise ValueError('Miko sources changed while building')
    validate(rom,bytes(data),reloc,report,module)
    (out/'overlay.bin').write_bytes(data);(out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'elf-relocations.txt').write_text(elf_text)
    (out/'overlay.asm').write_text(run('objdump','-d','overlay.elf'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--words',type=Path,default=Path('build/fortune-slip-resources/fortune-words.bin'))
    parser.add_argument('--output',type=Path,default=Path('build/fortune-actor'))
    args = parser.parse_args()
    print(json.dumps(build(verified_rom(args.rom.read_bytes()),json.loads(args.module.read_text()),
                           args.words.read_bytes(),args.output.resolve()),indent=2))


if __name__ == '__main__': main()
