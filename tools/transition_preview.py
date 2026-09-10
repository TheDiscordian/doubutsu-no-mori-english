"""Measure native transition framebuffer edges in an isolated restored fixture."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from flash_mail import SAVE_RAM,SAVE_BYTES
from runtime_layout import GUARD_ADDRESS,GUARD_WORD
from title_start_smoke import locate
from texture_preview import png_rgba,rgba5551
from toolchain import IMAGE
from transition_edges import ROOT,BASE_SHA,KEEP,OLD,NEW,SCALE

CODE,META,ASSETS=0x80500000,0x80503000,0x80510000
EDGE=b'WIPE'*4
SOURCES=('tests/fixtures/transition_preview.c','tests/fixtures/transition_preview.ld')
def words(*v): return struct.pack('>'+'I'*len(v),*v)

def exercise(debug,request,rom,state):
    read,write=debug.read_memory,debug.write_memory
    directory=(ROOT/request['build']).resolve()
    if not directory.is_relative_to(ROOT/'build'): raise ValueError('Unowned transition fixture')
    report=json.loads((directory/'preview.json').read_text());files=by_vrom(rom)
    if sha256(rom)!=report['rom_sha256'] or read(0x80000318,4)!=words(0x800000):
        raise ValueError('Changed transition ROM or memory size')
    if read(GUARD_ADDRESS,16)!=words(*([GUARD_WORD]*4)) or read(0x800418D8,4)!=bytes(4):
        raise ValueError('Resident guard changed or native fault')
    _,actor,base,_=locate(debug,memory_end=0x80800000)
    if base!=0x80400010: raise ValueError('Unexpected title allocation')
    for at in (0x80400000,0x804475F0):
        if read(at,16)!=words(*([0xAF54C0DE]*4)): raise ValueError('Title guard changed')
    native=files[CODE_VROM].extract(rom)
    if read(0x80083C00,0x458)!=native[0x80083C00-CODE_RAM:0x80084058-CODE_RAM] or read(CODE_RAM+SCALE,4)!=native[SCALE:SCALE+4]:
        raise ValueError('Native transition differs from the bound cartridge')
    if request.get('setup'):
        if state: raise ValueError('Transition fixture already active')
        code=(directory/'preview.bin').read_bytes();assets=files[KEEP].extract(rom)
        if (not 4<=len(code)<=0x2000 or len(code)%4 or sha256(code)!=report['code_sha256']
            or report['sources']!={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}):
            raise ValueError('Stale transition fixture')
        regions=((CODE,len(code)),(META,256),(ASSETS,len(assets)),(0x80600000,153600))
        for at,size in regions:
            if read(at-16,size+32)!=bytes(size+32): raise ValueError('Transition scratch is in use')
        callback=read(actor+0x168,4)
        if not base<=int.from_bytes(callback,'big')<0x804475F0: raise ValueError('Unexpected title callback')
        saved=read(SAVE_RAM,SAVE_BYTES);guards=tuple(a for p,n in regions for a in (p-16,p+n))
        write(CODE,code);write(ASSETS,assets);write(META,bytes(256));write(META+16,words(548))
        for at in guards:write(at,EDGE)
        write(actor+0x168,words(CODE))
        state.update(actor=actor,callback=callback,code=code,assets=assets,saved=saved,guards=guards)
        return {'transition_preview_installed':True,'checkpoint_restore_required':True}
    if not state or actor!=state['actor']: raise ValueError('Missing transition fixture state')
    if 'select' in request:
        mode,phase=request['select']
        if mode not in (0,1,2) or phase not in (0,274,548): raise ValueError('Unknown transition case')
        write(META,words(mode,0,0,0,phase))
        return {'transition_model':mode,'transition_phase':phase}
    if request.get('verify'):
        mode,draws,error,address,phase=struct.unpack('>5I',read(META,20))
        if draws<2 or error or read(actor+0x168,4)!=words(CODE): raise ValueError('Transition did not draw safely')
        if read(CODE,len(state['code']))!=state['code'] or read(ASSETS,len(state['assets']))!=state['assets']:
            raise ValueError('Transition fixture code or assets changed')
        for at in state['guards']:
            if read(at,16)!=EDGE: raise ValueError('Transition scratch overflow')
        if read(SAVE_RAM,SAVE_BYTES)!=state['saved']: raise ValueError('Transition changed saved data')
        address|=0x80000000
        if not 0x80000000<=address<=0x80800000-153600: raise ValueError('Invalid transition framebuffer')
        frame=b''.join(read(address+i,min(4096,153600-i)) for i in range(0,153600,4096))
        pixels=[v for (v,) in struct.iter_unpack('>H',frame)]
        name=f'model-{mode}-phase-{phase}'
        with (directory/(name+'.bin')).open('xb') as out:out.write(frame)
        with (directory/(name+'.png')).open('xb') as out:
            out.write(png_rgba(320,240,b''.join(rgba5551(v) for v in pixels),3))
        rows=[sum(bool(v&0xFFFE) for v in pixels[y*320:(y+1)*320]) for y in range(240)]
        columns=[sum(bool(pixels[y*320+x]&0xFFFE) for y in range(240)) for x in range(320)]
        return {'transition_model':mode,'transition_phase':phase,'draws':draws,
            'nonblack_pixels':sum(rows),'nonblack_top_rows':rows[:4],'nonblack_bottom_rows':rows[-4:],
            'nonblack_left_columns':columns[:4],'nonblack_right_columns':columns[-4:],
            'guards_intact':True,'save_unchanged':True,'ordinary_scene':False}
    if request.get('restored'):
        if read(actor+0x168,4)!=state['callback'] or read(SAVE_RAM,SAVE_BYTES)!=state['saved']:
            raise ValueError('Transition checkpoint not restored')
        for at in state['guards']:
            if read(at,16)!=bytes(16): raise ValueError('Transition scratch not restored')
        return {'transition_checkpoint_restored':True}
    raise ValueError('Unknown transition fixture action')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--corrected-build',type=Path)
    a=p.parse_args();rom=a.rom.read_bytes();expected=BASE_SHA;scale=OLD
    if a.corrected_build:
        receipt=json.loads((a.corrected_build/'fixes.json').read_text());expected=receipt['output_sha256'];scale=NEW
        if receipt['sources']!={'tools/transition_edges.py':sha256((ROOT/'tools/transition_edges.py').read_bytes())}:
            raise ValueError('Stale transition correction')
    if sha256(rom)!=expected or by_vrom(rom)[CODE_VROM].extract(rom)[SCALE:SCALE+4]!=scale:
        raise ValueError('Unknown transition cartridge')
    a.output.mkdir(parents=True,exist_ok=False)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/source:ro','-v',f'{a.output.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],check=True,timeout=60)
    run('gcc','-c','-O2','-EB','-mabi=32','-march=vr4300','-G0','-mno-abicalls','-fno-pic',
        '-ffreestanding','-fno-common','-D_LANGUAGE_C','-DF3DEX_GBI_2',
        '-I/source/upstream/af/lib/ultralib/include','/source/'+SOURCES[0],'-o','preview.o')
    run('ld','-EB','-T','/source/'+SOURCES[1],'-o','preview.elf','preview.o')
    run('objcopy','-O','binary','preview.elf','preview.bin')
    code=(a.output/'preview.bin').read_bytes()
    report={'rom_sha256':expected,'code_sha256':sha256(code),'sources':{s:sha256((ROOT/s).read_bytes()) for s in SOURCES},
            'toolchain_image':IMAGE,'scale':struct.unpack('>f',scale)[0],'ordinary_scene':False}
    (a.output/'preview.json').write_text(json.dumps(report,indent=2)+'\n')
    req={'build':str(a.output.relative_to(ROOT) if a.output.is_absolute() else a.output)}
    actions=[{'wait':12},{'save_state':True},{'pause_game_thread':True},
             {'test_transition_preview':dict(req,setup=True)}]
    cases=((0,548),(1,548),(2,548),(0,274),(0,0)) if a.corrected_build else ((0,548),)
    for mode,phase in cases:
        actions += [{'test_transition_preview':dict(req,select=[mode,phase])},{'resume':True},{'wait':2},
                    {'pause_game_thread':True},{'test_transition_preview':dict(req,verify=True)}]
    actions += [{'load_state':True},{'wait':2},{'pause_game_thread':True},
                {'test_transition_preview':dict(req,restored=True)},{'resume':True}]
    (a.output/'scenario.json').write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps(report))

if __name__=='__main__':main()
