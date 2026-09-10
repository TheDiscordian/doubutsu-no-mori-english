"""Compile the bounded birthday drawing replacement with the pinned MIPS toolchain."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256
from check_keyboard_assembly import IMAGE

ROOT=Path(__file__).resolve().parents[1]
FLAGS=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls','-fno-pic',
       '-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector','-fno-merge-constants',
       '-mno-explicit-relocs','-mno-split-addresses','-fstack-usage','-Wall','-Wextra','-Werror']


def compile_draw(output):
    output=output.resolve();output.mkdir(parents=True,exist_ok=False)
    common=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        p=subprocess.run(common+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            check=True,capture_output=True,text=True,timeout=60)
        return p.stdout
    sources={str(p.relative_to(ROOT)):sha256(p.read_bytes()) for p in
             (ROOT/'overlays/birthday/draw.c',ROOT/'overlays/birthday/draw.ld')}
    run('gcc',*FLAGS,'/source/overlays/birthday/draw.c','-o','draw.o')
    run('ld','-EB','--emit-relocs','-T','/source/overlays/birthday/draw.ld',
        '-Map=draw.map','-o','draw.elf','draw.o')
    if run('nm','--undefined-only','draw.elf').strip():raise ValueError('Unresolved birthday import')
    run('objcopy','-O','binary','-j','.draw','draw.elf','draw.bin')
    data=(output/'draw.bin').read_bytes()
    result={'bytes':len(data),'sha256':sha256(data),'ram':0x8089A684,'native_capacity':0x40C,
        'fits_native_function':len(data)<=0x40C,'sources':sources,'toolchain_image':IMAGE,
        'flags':FLAGS,'stack_usage':(output/'draw.su').read_text(),
        'status':'Compiled candidate only; cartridge integration and verification pending'}
    for name,value in (('draw.asm',run('objdump','-d','draw.elf')),
                       ('relocations.txt',run('readelf','-rW','draw.elf')),
                       ('symbols.txt',run('nm','--defined-only','draw.elf')),
                       ('draw.json',json.dumps(result,indent=2)+'\n')):
        (output/name).write_text(value)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'build/birthday-draw-01')
    args=parser.parse_args();print(json.dumps(compile_draw(args.output),indent=2))


if __name__=='__main__':main()
