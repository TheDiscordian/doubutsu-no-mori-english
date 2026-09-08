#!/usr/bin/env python3
"""Append complete sale/Redd publication and retry ownership to the event actor."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256,verified_rom
from check_keyboard_assembly import IMAGE
from event_actor import (RAM,PREFIX_BYTES,native_sources,source_hashes,imports_for,
                         creator_image,elf_inventory,patch_prefix,relocation_bytes,validate)


def build(rom,module,creator_code,creator,out):
    native,native_reloc = native_sources(rom)
    embedded = creator_image(creator_code,creator,module)
    sources = source_hashes();imports = imports_for(module)
    root = Path(__file__).resolve().parents[1]
    out.mkdir(parents=True,exist_ok=True)
    (out/'native.bin').write_bytes(native);(out/'creator.bin').write_bytes(embedded)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{root}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(f'Event {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    flags = ['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
             '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
             '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror']
    run('gcc',*flags,'/source/overlays/mail_generation/event_actor.c','-o','event_actor.o')
    run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o','native.o','/source/overlays/mail_generation/event_actor.s')
    entry = RAM+PREFIX_BYTES+creator['symbols']['af_event_leaflet_publish']
    run('ld','-EB','--emit-relocs','-T','/source/overlays/mail_generation/event_actor.ld','-Map=overlay.map',
        *(f'--defsym={name}=0x{value:08X}' for name,value in imports.items()),
        f'--defsym=af_event_leaflet_publish=0x{entry:08X}',
        '-o','overlay.elf','native.o','event_actor.o')
    if run('nm','--undefined-only','overlay.elf').strip(): raise ValueError('Undefined event symbol')
    symbols = {}
    for line in run('nm','--defined-only','overlay.elf').splitlines():
        fields = line.split()
        if len(fields) == 3: symbols[fields[2]] = int(fields[0],16)
    run('objcopy','-O','binary','-j','.text','overlay.elf','overlay.bin')
    data = bytearray((out/'overlay.bin').read_bytes())
    offsets = {name:value-RAM for name,value in symbols.items() if name.startswith('af_') and RAM <= value < RAM+len(data)}
    data[:PREFIX_BYTES] = patch_prefix(rom,module,offsets)
    if (symbols['__event_start'] != RAM or symbols['__event_end'] != RAM+len(data)
            or symbols['__event_creator'] != RAM+PREFIX_BYTES or symbols['__event_adapter'] != RAM+PREFIX_BYTES+len(embedded)):
        raise ValueError('Event linked bounds disagree with extracted image')
    elf_text = run('readelf','-rW','overlay.elf');inventory = elf_inventory(elf_text)
    reloc = relocation_bytes(native_reloc,inventory,imports,creator,len(data))
    report = {'version':1,'ram':RAM,'bytes':len(data),'text_bytes':symbols['__event_text_end']-RAM,
              'overlay_sha256':sha256(data),'relocation_bytes':len(reloc),'relocation_sha256':sha256(reloc),
              'sources':sources,'imports':imports,'module_sha256':module['module_sha256'],
              'creator':creator,'creator_sha256':sha256(creator_code),'symbols':offsets,
              'elf_relocations':inventory,'compiler':run('gcc','--version').splitlines()[0],
              'flags':flags,'toolchain_image':IMAGE,'stack_usage':(out/'event_actor.su').read_text(),
              'status':'Complete event publication owner; native and normal gameplay validation remain separate'}
    if source_hashes() != sources: raise ValueError('Event sources changed while building')
    validate(rom,bytes(data),reloc,report,module,creator_code,creator)
    (out/'overlay.bin').write_bytes(data);(out/'relocation.bin').write_bytes(reloc)
    (out/'creator-original.bin').write_bytes(creator_code)
    (out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n')
    (out/'elf-relocations.txt').write_text(elf_text)
    (out/'overlay.asm').write_text(run('objdump','-d','overlay.elf'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/renewal-actor-pilot/runtime-module.json'))
    parser.add_argument('--creator',type=Path,default=Path('build/event-leaflet-probe'))
    parser.add_argument('--output',type=Path,default=Path('build/event-actor'))
    args = parser.parse_args()
    print(json.dumps(build(verified_rom(args.rom.read_bytes()),json.loads(args.module.read_text()),
                          (args.creator/'generate.bin').read_bytes(),
                          json.loads((args.creator/'generate.json').read_text()),args.output.resolve()),indent=2))


if __name__ == '__main__': main()
