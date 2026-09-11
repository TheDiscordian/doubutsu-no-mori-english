"""One bounded native V2 drawing/appearance check, using isolated title scratch."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

from aflib import by_vrom,sha256
from birthday_draw_scenario import CALLBACK
from catalogue_names import Image
from flash_mail import SAVE_RAM,SAVE_BYTES
from keyboard_background_smoke import rectangles
from keyboard_v2 import ROOT,VROM,RELOC,RAM,ART_VROM,source_hashes
from npc_mail_show import relocate_verified_data
from runtime_layout import GUARD_ADDRESS,GUARD_WORD
from texture_preview import rgba5551,png_rgba
from title_start_smoke import locate
from toolchain import IMAGE

CODE,META=0x80500000,0x80503000
EDGE=b'V2KB'*4
SOURCES=('tests/fixtures/keyboard_v2_preview.c','tests/fixtures/keyboard_v2_preview.ld')
def words(*v): return struct.pack('>'+'I'*len(v),*v)


def exercise(debug,request,rom,state):
    directory=(ROOT/request['build']).resolve()
    if not directory.is_relative_to(ROOT/'build'): raise ValueError('Unowned V2 fixture')
    report=json.loads((directory/'build.json').read_text())
    fixture=json.loads((directory/'preview/preview.json').read_text())
    if sha256(rom)!=report['output_sha256'] or report['sources']!=source_hashes():
        raise ValueError('Changed current V2 cartridge or source')
    read,write=debug.read_memory,debug.write_memory
    if read(0x80000318,4)!=words(0x800000) or read(GUARD_ADDRESS,16)!=words(*([GUARD_WORD]*4)):
        raise ValueError('Changed Expansion Pak or resident guard')
    if read(0x800418D8,4)!=bytes(4): raise ValueError('Native fault before V2 check')
    _,actor,title,_=locate(debug,memory_end=0x80800000)
    if title!=0x80400010: raise ValueError('Unexpected title allocation')
    if request.get('setup'):
        if state: raise ValueError('V2 fixture already installed')
        code=(directory/'preview/preview.bin').read_bytes()
        if (not 4<=len(code)<=0x2000 or sha256(code)!=fixture['code_sha256'] or
            fixture['sources']!={p:sha256((ROOT/p).read_bytes()) for p in SOURCES}):
            raise ValueError('Changed V2 fixture code')
        for p,n in ((CODE,len(code)),(META,64)):
            if read(p-16,n+32)!=bytes(n+32): raise ValueError('V2 title scratch is occupied')
        saved=read(SAVE_RAM,SAVE_BYTES);size=0x70000;allocation=0x80510000
        # This preview must not compete with the title's main-heap allocations.
        # Like the existing title previews, use verified-empty Expansion Pak
        # scratch and restore the checkpoint after the bounded drawing check.
        if read(allocation,size)!=bytes(size):
            raise ValueError('V2 Expansion Pak scratch is occupied')
        base,parent,ovl,submenu,menu,ed,text,art=(allocation+v for v in
            (0x10,0xA000,0x20000,0x32000,0x32100,0x32200,0x32300,0x50000))
        files=by_vrom(rom);loaded={};guards=[allocation+size-16,CODE-16,CODE+len(code),META-16,META+64]
        loader_at=0x1060+0x800262D0-0x80025C60;loader=rom[loader_at:loader_at+0xF0]
        if sha256(loader)!='2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
            raise ValueError('Changed native loader')
        for name,v,r,ram,dest,limit in (('editor',VROM,RELOC,RAM,base,parent-16),
                                      ('parent',0x7749C0,0x7778B0,0x8085BAC0,parent,ovl-16)):
            data,rel=files[v].extract(rom),files[r].extract(rom)
            sections=struct.unpack_from('>5I',rel);resident=sum(sections[:4])
            if dest+resident+len(rel)>=limit: raise ValueError('Overlapping V2 fixture owner')
            expected=relocate_verified_data(Image(ram,resident,sections),data,rel,dest,
                                             memory_end=0x80800000)
            debug.call('800262D0',[v,v+len(data),ram,ram+resident,dest,dest+resident,len(rel)],
                       verified_code=(0x800262D0,loader))
            if read(dest,resident)!=expected: raise ValueError('V2 cartridge loader mismatch')
            loaded[name]=expected;guards.extend((dest-16,dest+resident+len(rel)))
        if loaded['parent'][0x218:0x248]!=CALLBACK: raise ValueError('Changed native matrix callback')
        for at,count in ((ovl,0x10720),(submenu,0x40),(menu,0x48),(ed,0x34),(text,64)):
            write(at,bytes(count));guards.extend((at-16,at+count))
        artwork=files[ART_VROM].extract(rom);write(art,artwork);guards.extend((art-16,art+len(artwork)))
        write(submenu+0x2C,words(ovl));write(ovl+0x106E0,words(ed));write(ovl+0x106B4,words(parent+0x218))
        write(menu+0x28,words(art&0x1FFFFFFF));write(menu+0x38,words(3))
        write(ed+0x18,struct.pack('>2h',6,1));write(ed+0x24,words(text))
        context=base+28608
        write(context,bytes([0,0,1])+bytes(9)+words(submenu,menu,ed,text,0,0))
        callback=read(actor+0x168,4)
        if not title<=int.from_bytes(callback,'big')<0x804475F0: raise ValueError('Unknown title callback')
        for at in guards:write(at,EDGE)
        write(CODE,code);write(META,words(base+report['editor']['symbols']['af_bg_editor_draw'],submenu,menu)+bytes(52))
        write(actor+0x168,words(CODE))
        state.update(actor=actor,callback=callback,code=code,saved=saved,guards=guards,base=base,
                     context=context,ed=ed,editor=read(ed,0x34),text=text,art=art,artwork=artwork)
        return {'v2_fixture_installed':True,'cartridge_loader_verified':True,'checkpoint_restore_required':True}
    if not state or actor!=state['actor']: raise ValueError('V2 fixture is missing')
    if request.get('verify'):
        values=struct.unpack('>9I',read(META,36));draws,error,front,end,tail,fb=values[3:]
        if draws<2 or error or not 0x80000000<=front<end<tail<=0x80800000:
            raise ValueError('V2 native drawing failed or exceeded the graphics buffer')
        if read(state['context']+32,4)!=bytes(4): raise ValueError('V2 grid reported a draw error')
        for at in state['guards']:
            if read(at,16)!=EDGE: raise ValueError('V2 fixture guard changed')
        if read(state['ed'],0x34)!=state['editor'] or read(state['text'],64)!=bytes(64):
            raise ValueError('V2 drawing changed the input buffer or editor')
        if read(SAVE_RAM,SAVE_BYTES)!=state['saved']: raise ValueError('V2 drawing changed save RAM')
        if read(CODE,len(state['code']))!=state['code'] or read(state['art'],len(state['artwork']))!=state['artwork']:
            raise ValueError('V2 fixture code or native artwork changed')
        commands=read(front,end-front);rects=rectangles(commands)
        if len(rects)!=55: raise ValueError('Missing V2 panel, icon, or key rectangle')
        for i,rect in enumerate(rects[15:]):
            x=60+16*(i%10)+(0,3,7,10)[i//10];y=133+16*(i//10)
            if rect!=dict(bounds=[x,y,x+16,y+16],st=[0,0],delta=[2048,2048]):
                raise ValueError('V2 changed an accepted key position')
        rows=list(struct.iter_unpack('>2I',commands))
        if (0xFA0000FF,0xE1E1E1FF) not in rows or (0xFB000000,0x696E73FF) not in rows:
            raise ValueError('V2 grey panel material is missing')
        fb|=0x80000000
        if not 0x80000000<=fb<=0x80800000-153600: raise ValueError('Unknown V2 framebuffer')
        frame=b''.join(read(fb+i,min(4096,153600-i)) for i in range(0,153600,4096))
        output=directory/'preview'
        for name,data in (('commands.bin',commands),('framebuffer.bin',frame),
            ('framebuffer.png',png_rgba(320,240,b''.join(rgba5551(v) for (v,) in struct.iter_unpack('>H',frame)),3))):
            with (output/name).open('xb') as f:f.write(data)
        return {'v2_native_draws':draws,'rectangles':rects,'display_list_bytes':len(commands),
                'guards_intact':True,'input_and_save_unchanged':True,'ordinary_screen_tested':False}
    if request.get('restored'):
        if read(actor+0x168,4)!=state['callback'] or read(SAVE_RAM,SAVE_BYTES)!=state['saved']:
            raise ValueError('V2 checkpoint did not restore')
        if read(CODE-16,len(state['code'])+32)!=bytes(len(state['code'])+32):
            raise ValueError('V2 preview code remains after restore')
        if read(0x80510000,0x70000)!=bytes(0x70000):
            raise ValueError('V2 owner scratch remains after restore')
        return {'v2_checkpoint_restored':True}
    raise ValueError('Unknown V2 preview operation')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--build',type=Path,required=True)
    a=p.parse_args();out=a.build/'preview';out.mkdir(parents=True,exist_ok=False)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
            '-v',f'{ROOT}:/source:ro','-v',f'{out.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],check=True,timeout=60)
    run('gcc','-c','-Os','-EB','-mabi=32','-march=vr4300','-G0','-mno-abicalls','-fno-pic',
        '-ffreestanding','-fno-common','-D_LANGUAGE_C','-DF3DEX_GBI_2',
        '-I/source/upstream/af/lib/ultralib/include','/source/'+SOURCES[0],'-o','preview.o')
    run('ld','-EB','-T','/source/'+SOURCES[1],'-o','preview.elf','preview.o')
    run('objcopy','-O','binary','preview.elf','preview.bin')
    report={'code_sha256':sha256((out/'preview.bin').read_bytes()),
            'sources':{p:sha256((ROOT/p).read_bytes()) for p in SOURCES},'toolchain':IMAGE}
    (out/'preview.json').write_text(json.dumps(report,indent=2)+'\n')
    req={'build':str(a.build.resolve().relative_to(ROOT))}
    actions=[{'wait':12},{'save_state':True},{'pause_game_thread':True},
        {'test_keyboard_v2_preview':dict(req,setup=True)},{'resume':True},{'wait':2},
        {'pause_game_thread':True},{'test_keyboard_v2_preview':dict(req,verify=True)},
        {'load_state':True},{'wait':2},{'pause_game_thread':True},
        {'test_keyboard_v2_preview':dict(req,restored=True)},{'resume':True}]
    (out/'scenario.json').write_text(json.dumps(actions,indent=2)+'\n')
    print(out/'scenario.json')


if __name__=='__main__':main()
