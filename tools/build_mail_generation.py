#!/usr/bin/env python3
"""Build a relocatable native generation probe, without installing game hooks."""

import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
from runtime_layout import MODULE_RAM,LINKED_LIMIT

IMPORTS = ('af_mail_record_pack','af_mail_restore','af_mail_catalog_header_valid')
SOURCES = ('overlays/mail_generation/generate.c','overlays/mail_generation/generate.h',
           'overlays/mail_generation/probe.ld','runtime/mail/catalog.h',
           'runtime/mail/format.h','runtime/mail/record.h')


def build(module,out):
    root = Path(__file__).resolve().parents[1]
    hashes = {name:sha256((root/name).read_bytes()) for name in SOURCES}
    out.mkdir(parents=True,exist_ok=True)
    common = ['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
              '-v',f'{root}:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result = subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(f'Generation {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    imports = {name:int(module['symbols'][name],16) for name in IMPORTS}
    if any(not MODULE_RAM+0x300 <= value < MODULE_RAM+LINKED_LIMIT or value&3 for value in imports.values()):
        raise ValueError('Generation probe imports are outside resident code')
    flags = ['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
             '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
             '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror']
    run('gcc',*flags,'/source/overlays/mail_generation/generate.c','-o','generate.o')
    run('ld','-EB','--emit-relocs','-T','/source/overlays/mail_generation/probe.ld',
        *(f'--defsym={name}=0x{value:08X}' for name,value in imports.items()),
        '-o','generate.elf','generate.o')
    if run('nm','--undefined-only','generate.elf').strip(): raise ValueError('Undefined generation symbols')
    symbols = {}
    for line in run('nm','--defined-only','generate.elf').splitlines():
        fields = line.split()
        if len(fields) == 3: symbols[fields[2]] = int(fields[0],16)
    base,end = symbols['__probe_start'],symbols['__probe_end']
    if base != 0x80200000 or not 0 < end-base <= 4096: raise ValueError('Invalid generation code bounds')
    run('objcopy','-O','binary','-j','.text','generate.elf','generate.bin')
    code = (out/'generate.bin').read_bytes()
    if len(code) != end-base: raise ValueError('Generation code size mismatch')
    relocs = run('readelf','-rW','generate.elf')
    adjustments,seen = [],set()
    for line in relocs.splitlines():
        if 'R_MIPS_' not in line: continue
        match = re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_26\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: raise ValueError('Unsupported generation relocation: '+line)
        address,value,name = int(match[1],16),int(match[2],16),match[3]
        offset = address-base
        if offset&3 or not 0 <= offset <= len(code)-4 or offset in seen:
            raise ValueError('Invalid generation relocation location')
        seen.add(offset)
        word = struct.unpack_from('>I',code,offset)[0]
        target = 0x80000000|((word&0x3FFFFFF)<<2)
        if word>>26 not in (2,3): raise ValueError('Generation jump relocation is not a jump')
        if base <= value < end:
            if not base <= target < end: raise ValueError('Internal generation jump target exceeds code')
            adjustments.append(offset)
        elif name not in imports or value != imports[name] or target != value:
            raise ValueError('Unapproved external generation relocation')
    for offset in range(0,len(code),4):
        if struct.unpack_from('>I',code,offset)[0]>>26 in (2,3) and offset not in seen:
            raise ValueError('Untracked absolute generation jump')
    if hashes != {name:sha256((root/name).read_bytes()) for name in SOURCES}:
        raise ValueError('Generation source changed while building')
    report = {'version':1,'base':base,'bytes':len(code),'sha256':sha256(code),
              'sources':hashes,'module_sha256':module['module_sha256'],'imports':imports,
              'symbols':{name:value-base for name,value in symbols.items() if name.startswith('af_mail_') and base <= value < end},
              'jump_relocations':adjustments,'compiler':run('gcc','--version').splitlines()[0],
              'flags':flags,'stack_usage':(out/'generate.su').read_text(),'toolchain_image':IMAGE,
              'status':'Test-only native generation code; no game hooks or generation setting changed'}
    (out/'generate.asm').write_text(run('objdump','-d','generate.elf'))
    (out/'generate-relocations.txt').write_text(relocs)
    (out/'generate.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--output',type=Path,default=Path('build/mail-generation-probe'))
    args = parser.parse_args()
    print(json.dumps(build(json.loads(args.module.read_text()),args.output.resolve()),indent=2))


if __name__ == '__main__': main()
