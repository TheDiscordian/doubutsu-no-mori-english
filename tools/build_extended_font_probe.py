#!/usr/bin/env python3
"""Compile isolated font adapters without changing the resident production image."""

import argparse
import json
import os
from pathlib import Path
import re
import struct
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE

ROOT = Path(__file__).resolve().parents[1]
RAM, LIMIT = 0x8019A900, 0xA00


def source_hashes():
    return {p.relative_to(ROOT).as_posix():sha256(p.read_bytes())
            for p in sorted((ROOT/'overlays/extended_font').iterdir()) if p.is_file()}


def build(output):
    output=output.resolve();output.mkdir(parents=True,exist_ok=True)
    sources=source_hashes()
    common=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}/overlays/extended_font:/source:ro','-v',f'{output}:/out',
            '-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                              check=True,capture_output=True,text=True,timeout=60)
        return result.stdout
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
           '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
           '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror',
           '-mno-explicit-relocs','-mno-split-addresses']
    for name in ('font','native'): run('gcc',*flags,'/source/'+name+'.c','-o',name+'.o')
    run('as','-EB','-mabi=32','-march=vr4300','-o','texture.o','/source/texture.s')
    run('ld','-EB','--emit-relocs','-T','/source/probe.ld','-Map=font.map','-o','font.elf','font.o','native.o','texture.o')
    if run('nm','--undefined-only','font.elf').strip(): raise ValueError('Undefined extended-font probe symbol')
    run('objcopy','-O','binary','font.elf','font.bin')
    symbols={}
    for line in run('nm','--defined-only','font.elf').splitlines():
        pieces=line.split()
        if len(pieces)==3: symbols[pieces[2]]=int(pieces[0],16)
    size=symbols['__font_end']-RAM
    data=(output/'font.bin').read_bytes()
    if symbols['__font_start']!=RAM or not len(data)<=size<=LIMIT:
        raise ValueError('Extended-font probe bounds differ from their reserved test range')
    data=data.ljust(size,b'\0');(output/'font.bin').write_bytes(data)
    relocations=[]
    elf_relocs=run('readelf','-rW','font.elf')
    for line in elf_relocs.splitlines():
        if 'R_MIPS_' not in line: continue
        match=re.fullmatch(r'\s*([0-9a-fA-F]+)\s+[0-9a-fA-F]+\s+R_MIPS_(26|HI16|LO16)\s+([0-9a-fA-F]+)\s+(\S+)\s*',line)
        if not match: raise ValueError('Unsupported font relocation: '+line)
        at,kind,target=int(match[1],16),match[2],int(match[3],16)
        if not RAM <= target < RAM+len(data): raise ValueError('Unexpected external font relocation')
        relocations.append([at-RAM,kind])
    if sources!=source_hashes(): raise ValueError('Extended-font sources changed during compilation')
    report={'ram':RAM,'bytes':len(data),'sha256':sha256(data),'sources':sources,
            'symbols':symbols,'relocations':sorted(relocations),
            'compiler':run('gcc','--version').splitlines()[0],
            'toolchain_image':IMAGE,'flags':flags,
            'stack_usage':{name:(output/(name+'.su')).read_text() for name in ('font','native')},
            'installed':False,'scope':'Relocatable checkpoint-only native font probe; not a cartridge installation'}
    for base in (0x801A0010,0x802F8010,0x803FD000): relocate(data,report,base)
    (output/'font.asm').write_text(run('objdump','-d','font.elf'))
    (output/'font-relocations.txt').write_text(elf_relocs)
    (output/'font.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


def relocate(data,report,base):
    """Apply only paired internal addresses and inventoried internal jumps."""
    from runtime_layout import MODULE_RAM,RESERVATION
    if (report['ram']!=RAM or report['bytes']!=len(data) or report['sha256']!=sha256(data)
            or report['sources']!=source_hashes() or not 0<len(data)<=LIMIT or len(data)&3
            or type(base) is not int or base&15 or not MODULE_RAM+RESERVATION<=base<=0x80400000-len(data)):
        raise ValueError('Invalid font probe image or allocated destination')
    end=report['symbols']['__font_text_end']-RAM
    bss=report['symbols']['__font_bss_start']-RAM
    if not 0<end<=bss<len(data) or any(data[bss:]): raise ValueError('Invalid font code/state boundaries')
    out=bytearray(data);previous=-1;high={};jumps=set()
    for at,kind in report['relocations']:
        if type(at) is not int or at&3 or not previous<at<=end-4:
            raise ValueError('Invalid font relocation ordering or location')
        previous=at;word=struct.unpack_from('>I',data,at)[0]
        if kind=='26':
            target=0x80000000|((word&0x3FFFFFF)<<2)
            if word>>26 not in (2,3) or not RAM<=target<RAM+end: raise ValueError('Invalid font internal jump')
            word=(word&0xFC000000)|((base+target-RAM)&0xFFFFFFF)>>2
            jumps.add(at)
        elif kind=='HI16':
            register=(word>>16)&31
            if word>>26!=15 or register in high: raise ValueError('Invalid font high address')
            high[register]=(at,word)
            continue
        elif kind=='LO16':
            register=(word>>21)&31
            if word>>26 not in (9,35,43) or register not in high: raise ValueError('Invalid font low address')
            hi_at,hi_word=high.pop(register)
            target=((hi_word&65535)<<16)+(word&65535)-(65536 if word&32768 else 0)
            if not RAM<=target<RAM+len(data): raise ValueError('Font pointer escapes complete image')
            target+=base-RAM
            struct.pack_into('>I',out,hi_at,(hi_word&0xFFFF0000)|(((target+32768)>>16)&65535))
            word=(word&0xFFFF0000)|(target&65535)
        else: raise ValueError('Unsupported font relocation')
        struct.pack_into('>I',out,at,word)
    if high: raise ValueError('Unpaired font high address')
    seen=set()
    for at in range(0,end,4):
        word=struct.unpack_from('>I',data,at)[0]
        if word>>26 not in (2,3): continue
        target=0x80000000|((word&0x3FFFFFF)<<2)
        if RAM<=target<RAM+end: seen.add(at)
        elif target!=0x800906B4: raise ValueError('Unexpected external font jump')
    if seen!=jumps: raise ValueError('Missing font jump relocation')
    return bytes(out)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    print(json.dumps(build(parser.parse_args().output),indent=2))
