#!/usr/bin/env python3
"""Build complete secret letters inside the existing conversation allocation."""

import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256,verified_rom
from check_keyboard_assembly import IMAGE
from secret_actor import ROOT,RAM,baseline,source_hashes,elf_inventory,patch_prefix,relocation_bytes,validate
from audit_secret_letters import snapshots


def build(native,module,catalog,out):
    original,native_reloc = baseline(native,module);table,prepared = snapshots(native,catalog)
    sources = source_hashes();out.mkdir(parents=True,exist_ok=True)
    (out/'native.bin').write_bytes(original);(out/'snapshots.bin').write_bytes(table)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{ROOT}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(f'Secret creator {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    flags = ['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
             '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
             '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror']
    run('gcc',*flags,'/source/overlays/mail_generation/secret_creator.c','-o','creator.o')
    run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o','native.o','/source/overlays/mail_generation/secret_actor.s')
    run('ld','-EB','--emit-relocs','-T','/source/overlays/mail_generation/secret_actor.ld','-Map=overlay.map',
        '-o','overlay.elf','native.o','creator.o')
    if run('nm','--undefined-only','overlay.elf').strip(): raise ValueError('Unresolved secret creator import')
    symbols = {}
    for line in run('nm','--defined-only','overlay.elf').splitlines():
        fields = line.split()
        if len(fields)==3: symbols[fields[2]] = int(fields[0],16)
    run('objcopy','-O','binary','-j','.text','overlay.elf','overlay.bin')
    data = bytearray((out/'overlay.bin').read_bytes())
    exports = {n:v-RAM for n,v in symbols.items() if n.startswith('af_')}
    data[:len(original)] = patch_prefix(native,module,exports)
    if symbols['__secret_start']!=RAM or symbols['__secret_end']!=RAM+len(data):
        raise ValueError('Secret creator linked bounds disagree')
    elf_text = run('readelf','-rW','overlay.elf');inventory = elf_inventory(elf_text)
    reloc = relocation_bytes(native_reloc,inventory,len(data))
    report = {'version':1,'ram':RAM,'bytes':len(data),'overlay_sha256':sha256(data),
              'relocation_bytes':len(reloc),'relocation_sha256':sha256(reloc),'sources':sources,
              'module_sha256':module['module_sha256'],'capital_ram':int(module['symbols']['af_mail_generation_capital'],16),
              'snapshots':prepared,'symbols':exports,'code_end':symbols['__secret_code_end']-RAM,
              'elf_relocations':inventory,'compiler':run('gcc','--version').splitlines()[0],
              'flags':flags,'toolchain_image':IMAGE,'stack_usage':(out/'creator.su').read_text()}
    if sources!=source_hashes(): raise ValueError('Secret creator sources changed during build')
    validate(native,bytes(data),reloc,report,module,catalog)
    (out/'overlay.bin').write_bytes(data);(out/'relocation.bin').write_bytes(reloc)
    (out/'overlay.json').write_text(json.dumps(report,indent=2)+'\n');(out/'elf-relocations.txt').write_text(elf_text)
    (out/'overlay.asm').write_text(run('objdump','-d','overlay.elf'))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--module',type=Path,default=ROOT/'build/shop-notice-runtime/module.json')
    parser.add_argument('--catalog',type=Path,default=ROOT/'build/mail-glyph-catalog/catalog.bin')
    parser.add_argument('--output',type=Path,default=ROOT/'build/secret-actor')
    args = parser.parse_args()
    report = build(verified_rom(args.rom.read_bytes()),json.loads(args.module.read_text()),
                   args.catalog.read_bytes(),args.output.resolve())
    print(json.dumps({k:report[k] for k in ('bytes','overlay_sha256','relocation_bytes','relocation_sha256','symbols','stack_usage')},indent=2))


if __name__=='__main__': main()
