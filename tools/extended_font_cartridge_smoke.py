"""Verify startup-owned cartridge glyphs after normal scene progression."""

import struct

from aflib import sha256
from extended_font_cartridge import RAM,relocate,validate
from extended_font_test_scenario import texture_commands
from extended_glyphs import GLYPHS
from flash_mail import SAVE_RAM,SAVE_BYTES
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE=b'FCRT'*4
def words(*values): return struct.pack('>'+'I'*len(values),*values)
def floats(*values): return struct.pack('>'+'f'*len(values),*values)


def exercise(debug,request,record):
    def read(at,size): return debug.read_memory(at,size)
    def write(at,value):
        debug.write_memory(at,value)
        record({'font_cartridge_write':f'{at:08X}','bytes':len(value),'data':value.hex()})
    def check(label,at,value):
        observed=read(at,len(value))
        record({'font_cartridge_check':label,'address':f'{at:08X}','bytes':len(value),
                'expected_sha256':sha256(value),'observed_sha256':sha256(observed),
                'assertion':'passed' if observed==value else 'failed'})
        if observed!=value: raise ValueError(f'Cartridge font {label} differs at {at:08X}')
    def call(at,args=(),expected=None):
        result=debug.call(f'{at:08X}',list(args));record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError(f'Cartridge font {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']
    data,relocations=bytes.fromhex(request['image']),bytes.fromhex(request['relocations'])
    report,module=request['font'],request['module'];validate(data,relocations,report)
    pointer=int(module['symbols']['af_extended_font_image'],16)
    base=int.from_bytes(read(pointer,4),'big')
    expected=bytearray(relocate(data,relocations,base))
    symbols={name:base+value for name,value in report['symbols'].items()}
    resource=symbols['af_font_resource'];pixels=data[report['symbols']['af_font_resource']:report['symbols']['af_font_resource']+1600]
    struct.pack_into('>I',expected,report['symbols']['glyph_resource'],resource)
    check('complete cartridge code/pixels and initial binding',base,bytes(expected))
    for at,name in ((0x80090178,'af_glyph_texture'),(0x8009028C,'af_glyph_code_width'),
                    (0x800902CC,'native_width'),(0x8009069C,'af_glyph_load_texture'),(0x800918A8,'af_glyph_draw_char')):
        check('installed native draw/width hook',at,words(0x08000000|((symbols[name]&0x0FFFFFFF)>>2),0))
    check('installed reveal hook',0x800A23C4,words(0x02002025,0x0C000000|((symbols['af_glyph_skip_tag']&0x0FFFFFFF)>>2),
        0x8FA50050,0x10400006,0x8FA50050,0x24A50002,0xAFA50050,0x080288DB,0,0))
    saved=read(SAVE_RAM,SAVE_BYTES);font=read(0x8013A680,0x6000);cuts=read(0x80106AF4,256)
    check('approved complete native font',0x8013A680,bytes.fromhex(request['native_font']))
    check('approved width table',0x80106AF4,bytes.fromhex(request['cuts']))
    call(int(module['symbols']['af_extended_font_init'],16),(),1)
    check('startup owner retained on repeated init',pointer,words(base))
    allocation=call(0x8009BFC0,[0x2000])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-0x2000:
        raise ValueError('Cartridge glyph drawing fixture allocation failed')
    if base<allocation+0x2000 and allocation<base+len(data)+len(relocations):
        raise ValueError('Gameplay fixture overlaps persistent font ownership')
    window=allocation+16;message=window+0x350;sentence=window+0x780;game=window+0x820
    graph=window+0x840;gfx_pp=window+0xB50;gfx=window+0xB80;vertex_end=window+0xE90;text=window+0xEA0
    guards=(allocation,window+0x330,message-16,message+0x410,sentence-16,sentence+0x88,
            gfx-16,gfx+256,vertex_end-512-16,vertex_end,text+96,allocation+0x2000-16,
            TEST_STACK-0x600,TEST_STACK+0x30)
    for at in guards: write(at,EDGE)
    write(game,words(graph))
    tokens=[b'i',b'\x80\xD0',b'I',b'\x80\xAE',b"'",b'\x80\xA7',b'l',b'\x80\xAB',
            b'\xA1',b'\x80\xBA',b'Z',b'\x80\x42',b'\xE0']
    payload=b''.join(tokens);write(text,payload)
    registered={code:i for i,(_,code,_) in enumerate(GLYPHS)}
    prefix_width=sum(pixels[48+registered[t[1]]] if len(t)==2 and t[1] in registered
                     else sum(12-cuts[c] for c in t) for t in tokens)
    call(0x800902CC,[text,len(payload),1],(prefix_width+1)&~1)
    call(0x800902CC,[text,len(payload),0],(prefix_width+1)&~1)
    call(0x800902CC,[text,0xFFFFFFFF,1],0)
    for poly in (False,True):
        write(sentence,bytes(0x88));write(sentence,words(text,len(payload)))
        write(sentence+0x0C,floats(25,100));write(sentence+0x18,bytes((50,60,50,255)))
        write(sentence+0x1C,floats(1,1,1,1));write(sentence+0x34,floats(11,1,1))
        write(sentence+0x4D,bytes((0x83 if poly else 0x81,)))
        write(sentence+0x54,floats(100));write(sentence+0x58,floats(*([1]*8)))
        index,width=0,11
        for token in tokens:
            slot=registered.get(token[1]) if len(token)==2 else None
            advance=pixels[48+slot] if slot is not None else 12-cuts[token[0]]
            texture,character=(resource+64,slot) if slot is not None else (0x8013A680,token[0])
            write(graph,bytes(0x300));write(graph+0x29C,words(vertex_end))
            write(gfx_pp,words(gfx));write(gfx,bytes(256));write(vertex_end-512,bytes(512))
            call(0x80091C98,[sentence,game,gfx_pp])
            commands=texture_commands(texture,character)
            left,right=25+width,25+width+advance;tx,ty=character%16*12,character//16*16
            if poly:
                commands+=words(0x01004008,vertex_end-64,0x06000204,0x00000406)
                vertices=b''
                for x,y,s,t in ((left,100,tx,ty),(left,116,tx,ty+16),
                                (right,116,tx+advance,ty+16),(right,100,tx+advance,ty)):
                    vertices+=struct.pack('>4h2h4B',int((x-160)*16),int((120-y)*16),0,0,s*64,t*64,0,0,0,0)
                check('complete cartridge glyph vertices',vertex_end-64,vertices)
            else:
                commands+=words(0xE4000000|right*4<<12|116*4,left*4<<12|100*4,
                                0xE1000000,tx*32<<16|ty*32,0xF1000000,0x04000400)
                check('rectangle retains vertex arena',vertex_end-512,bytes(512))
            check('complete native display list',gfx,commands+bytes(256-len(commands)))
            check('complete display-list length',gfx_pp,words(gfx+len(commands)))
            check('vertex arena position',graph+0x29C,words(vertex_end-64 if poly else vertex_end))
            index+=len(token);width+=advance
            check('complete token consumed',sentence+0x2C,words(index))
            check('sentence width',sentence+0x34,floats(width))
            check('glyph width',sentence+0x84,floats(advance))
            check('draw scope restored',symbols['active_glyph'],words(0))
            check('native stack lower guard',TEST_STACK-0x600,EDGE)
    # The actual cursor must wait for each registered pair as one character.
    # Unknown tags retain their native skip, consuming the following ! instead.
    cases=[(bytes((0x80,code)),2) for _,code,_ in GLYPHS]+[(b'\x80\x42',3),(b'i',1),(b'\xA1',1)]
    for token,consumed in cases:
        payload=token+b'!\x7f\x00'
        write(window,bytes(0x330));write(window+12,words(message))
        write(window+0x28C,words(0x4100));write(window+0x294,floats(2))
        message_data=words(1,1,len(payload),0)+payload
        write(message,message_data)
        call(0x800A223C,[window],1)
        check('protected cursor waits',window+0x2A0,words(0))
        check('native timer ticks',window+0x294,floats(1))
        call(0x800A223C,[window],1)
        check('native reveal consumes one registered character',window+0x2A0,words(consumed))
        # The native voice-queue setter at 8009F830 adds 0020 for the
        # ordinary fallback character. Registered symbols have no voice.
        check('pacing flags and native voice scheduling',window+0x28C,
              words(0x4100 if consumed==2 else 0x4120))
        check('complete message input retained',message,message_data)
    check('complete persistent image retained',base,bytes(expected))
    check('whole live save payload retained',SAVE_RAM,saved)
    check('complete native font retained',0x8013A680,font)
    check('approved widths retained',0x80106AF4,cuts)
    for at in guards: check('fixture or stack guard',at,EDGE)
    check('resident module guard',GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    check('persistent owner survives fixture release',pointer,words(base))
    return {'cartridge_font_draws':26,'native_cursor_cases':len(cases),'font_ram':f'{base:08X}',
            'fixture_released':True,'font_code_or_resource_uploaded':False,'requires_checkpoint_restore':True}
