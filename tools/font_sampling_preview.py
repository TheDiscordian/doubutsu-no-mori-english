"""Compile a bounded, checkpoint-restored comparison of the native font paths."""
import argparse
import json
import os
from pathlib import Path
import subprocess

from aflib import sha256,by_vrom
from font import FONT_VROM,ATLAS_OFFSET,ATLAS_SIZE,get_glyph,pixels,pack_pixels
from toolchain import IMAGE

ROOT=Path(__file__).resolve().parents[1]
ROM_SHA='7a265fca118e522591085d0f7ce3a926b46d78a86c67e6f07443c64befe005bb'
SOURCES=('tests/fixtures/font_sampling_preview.c','tests/fixtures/font_sampling_preview.ld')

def padded_fixture(rom):
    font=by_vrom(rom)[FONT_VROM].extract(rom)
    if sha256(font)!='7e4fdb93f1b0109e3d609434163d8c31174ef6699b7d439aef1a8305a18d2798':
        raise ValueError('Changed comparison glyph pixels')
    atlas=pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
    textures=[]
    for code in b'AB gijpqy 01':
        texture=[0]*288
        for y,row in enumerate(get_glyph(atlas,code)):
            texture[(y+1)*16+1:(y+1)*16+13]=row
        textures.append(pack_pixels(texture))
    return b''.join(textures)

def compile_fixture(out):
    out.mkdir(parents=True,exist_ok=False)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/source:ro','-v',f'{out.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],check=True,timeout=60)
    run('gcc','-c','-O2','-EB','-mabi=32','-march=vr4300','-G0','-mno-abicalls','-fno-pic',
        '-ffreestanding','-fno-common','-D_LANGUAGE_C','-DF3DEX_GBI_2',
        '-I/source/upstream/af/lib/ultralib/include','/source/'+SOURCES[0],'-o','preview.o')
    run('ld','-EB','-T','/source/'+SOURCES[1],'-o','preview.elf','preview.o')
    run('objcopy','-O','binary','preview.elf','preview.bin')
    code=(out/'preview.bin').read_bytes()
    if not 4<=len(code)<=0x2000 or len(code)%4: raise ValueError('Invalid font preview extent')
    report={'code_sha256':sha256(code),'sources':{p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
            'toolchain':IMAGE,'rows':['speech rectangle','name/option polygon','polygon with transparent border',
                                    'bordered polygon S/T +0.5']}
    (out/'preview.json').write_text(json.dumps(report,indent=2)+'\n')
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--corrected-build',type=Path)
    args=p.parse_args()
    report=compile_fixture(args.output)
    request={'build':str(args.output.relative_to(ROOT) if args.output.is_absolute() else args.output)}
    if args.corrected_build: request['corrected_build']=str(args.corrected_build)
    actions=[{'wait':12},{'save_state':True},{'pause_game_thread':True},
        {'test_font_sampling_preview':dict(request,setup=True)}, {'resume':True},{'wait':2},
        {'capture':'font-paths.png'},{'pause_game_thread':True},
        {'test_font_sampling_preview':dict(request,verify=True)},
        {'test_font_sampling_preview':dict(request,select=1)},{'resume':True},{'wait':2},
        {'capture':'font-paths-1x.png'},{'pause_game_thread':True},
        {'test_font_sampling_preview':dict(request,verify=True)},
        {'load_state':True},{'wait':2},{'pause_game_thread':True},
        {'test_font_sampling_preview':dict(request,restored=True)},{'resume':True}]
    (args.output/'scenario.json').write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__': main()
