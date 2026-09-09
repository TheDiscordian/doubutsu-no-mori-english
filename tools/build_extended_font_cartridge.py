#!/usr/bin/env python3
"""Build persistent source-exact glyph code, pixels, and native relocations."""

import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE
from extended_font_cartridge import RAM,RESOURCE_HASH,MAIL_RESOURCE_HASH,source_hashes,validate
from extended_glyphs import validate_resource

ROOT = Path(__file__).resolve().parents[1]


def build(resource,out):
    digest = sha256(resource)
    mail = digest == MAIL_RESOURCE_HASH
    if digest not in (RESOURCE_HASH,MAIL_RESOURCE_HASH):
        raise ValueError('Unapproved complete English glyph resource')
    validate_resource(resource,mail=mail)
    sources=source_hashes();out=out.resolve();out.mkdir(parents=True,exist_ok=True)
    (out/'glyphs.bin').write_bytes(resource)
    common=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}/overlays:/source:ro','-v',f'{out}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                              capture_output=True,text=True,timeout=60)
        if result.returncode: raise ValueError(f'Font {tool} failed: '+result.stdout+result.stderr)
        return result.stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
           '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
           '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror',
           '-I/source/extended_font']
    for name in ('font','native','install'):
        directory='extended_font_cartridge' if name=='install' else 'extended_font'
        run('gcc',*flags,f'/source/{directory}/{name}.c','-o',name+'.o')
    for name,directory in (('texture','extended_font'),('entry','extended_font_cartridge')):
        run('as','-EB','-mabi=32','-march=vr4300','-I/out','-o',name+'.o',f'/source/{directory}/{name}.s')
    run('ld','-EB','--emit-relocs','-T','/source/extended_font_cartridge/font.ld','-Map=font.map',
        '-o','font.elf','entry.o','font.o','native.o','texture.o','install.o')
    if run('nm','--undefined-only','font.elf').strip(): raise ValueError('Undefined persistent font symbol')
    symbols={}
    for line in run('nm','--defined-only','font.elf').splitlines():
        parts=line.split()
        if len(parts)==3: symbols[parts[2]]=int(parts[0],16)
    text=symbols['__font_text_end']-RAM
    writable=symbols['__font_data_end']-RAM-text
    rodata=symbols['__font_bss_start']-RAM-text-writable
    bss=symbols['__font_end']-symbols['__font_bss_start']
    total=text+writable+rodata+bss
    run('objcopy','-O','binary','font.elf','font.bin')
    raw=(out/'font.bin').read_bytes()
    if symbols['__font_start']!=RAM or len(raw)!=total-bss or not 0<total<=0x3000:
        raise ValueError('Persistent font section sizes disagree')
    data=raw+bytes(bss)
    elf_relocs=run('readelf','-rW','font.elf');entries=[]
    for line in elf_relocs.splitlines():
        if 'R_MIPS_' not in line: continue
        match=re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(32|26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: raise ValueError('Unsupported complete font ELF relocation: '+line)
        at,kind,target=int(match[1],16)-RAM,match[2],int(match[3],16)
        if not RAM<=target<RAM+total: raise ValueError('Unexpected external font ELF relocation')
        if 0<=at<text: section,offset=1,at
        elif text<=at<text+writable: section,offset=2,at-text
        elif text+writable<=at<total-bss: section,offset=3,at-text-writable
        else: raise ValueError('Font ELF relocation outside stored sections')
        entries.append((section<<30)|({'32':2,'26':4,'HI16':5,'LO16':6}[kind]<<24)|offset)
    entries.sort(key=lambda value:(value>>30,value&0xFFFFFF))
    raw_reloc=struct.pack('>5I',text,writable,rodata,bss,len(entries))+struct.pack('>'+str(len(entries))+'I',*entries)
    length=(len(raw_reloc)+4+15)&~15
    reloc=raw_reloc.ljust(length-4,b'\0')+struct.pack('>I',length)
    if sources!=source_hashes(): raise ValueError('Font sources changed while compiling')
    report={'ram':RAM,'bytes':len(data),'relocation_bytes':len(reloc),'sha256':sha256(data),
            'relocation_sha256':sha256(reloc),'resource_sha256':digest,'sources':sources,
            'symbols':{name:value-RAM for name,value in symbols.items() if RAM<=value<RAM+total},
            'compiler':run('gcc','--version').splitlines()[0],'toolchain_image':IMAGE,'flags':flags,
            'stack_usage':{name:(out/(name+'.su')).read_text() for name in ('font','native','install')},
            'scope':'Persistent cartridge image; requires the matching guarded startup loader'}
    if mail:
        report['mail_glyphs'] = True
    validate(data,reloc,report)
    (out/'font.bin').write_bytes(data);(out/'relocation.bin').write_bytes(reloc)
    (out/'font-relocations.txt').write_text(elf_relocs)
    (out/'font.asm').write_text(run('objdump','-d','font.elf'))
    (out/'font.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resource',type=Path,default=Path('build/extended-glyphs/glyphs.bin'))
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(build(args.resource.read_bytes(),args.output),indent=2))
