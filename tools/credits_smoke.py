"""Cartridge credit loads and native page drawing in isolated owned memory."""

import struct

from aflib import sha256
import credits_strings as c
from flash_mail import SAVE_RAM,SAVE_BYTES
from runtime_layout import MODULE_RAM,RESERVATION,TEST_STACK,GUARD_ADDRESS,GUARD_WORD

EDGE=b'CRED'*4
CLIP=0x80136F80
EVENT=0x80135CF4


def words(*values):return struct.pack('>'+'I'*len(values),*values)


def alpha(timer):
    if timer<20 or timer>=224:return 0
    if timer<60:return int((timer-20)*6.375)&255
    if timer<184:return 255
    return int((223-timer)*6.375)&255


def exercise(debug,request,record):
    read=debug.read_memory;assertions=0;draws=0;glyphs=0
    def write(at,value):
        debug.write_memory(at,value)
        record({'credits_write':f'{at:08X}','bytes':len(value),'sha256':sha256(value)})
    def check(label,at,expected):
        nonlocal assertions
        actual=read(at,len(expected))
        record({'credits_check':label,'address':f'{at:08X}','bytes':len(expected),
                'assertion':'passed' if actual==expected else 'failed',
                'expected_sha256':sha256(expected),'observed_sha256':sha256(actual)})
        if actual!=expected:raise ValueError('Native credits mismatch: '+label)
        assertions+=1
    def call(at,args=(),expected=None,proof=None):
        result=debug.call(f'{at:08X}',args,verified_code=proof);record(result)
        if expected is not None and result['return_value']!=expected:
            raise ValueError('Native credits return differs')
        return result['return_value']

    original,reloc=bytes.fromhex(request['source']),bytes.fromhex(request['relocation'])
    patched,new_reloc=c.patch(original,reloc)
    values=[bytes.fromhex(v) for v in request['rows']]
    saved=read(SAVE_RAM,SAVE_BYTES);clip=read(CLIP,4);event=read(EVENT,44)
    native_font=read(0x8013A680,0x6000);widths=read(0x80106AF4,256)
    check('installed actor ownership metadata',c.METADATA,bytes.fromhex(request['metadata']))
    size=0xC000;allocation=call(0x8009BFC0,[size])
    if allocation&15 or not MODULE_RAM+RESERVATION<=allocation<=0x80400000-size:
        raise ValueError('Credits fixture allocation failed')
    base=allocation+16;relocation_buffer=base+c.RESIDENT_BYTES
    game,graph,arena=allocation+0x1800,allocation+0x1840,allocation+0x2000
    arena_end=allocation+size-16
    edges=(allocation,relocation_buffer+len(reloc),game-16,game+16,graph-16,graph+0x300,
           arena-16,arena_end,TEST_STACK-0x800,TEST_STACK+0x60)
    for at in edges:write(at,EDGE)
    call(0x800262D0,[c.VROM,c.VROM+c.FILE_BYTES,c.RAM,c.RAM+c.RESIDENT_BYTES,
                    base,relocation_buffer,len(new_reloc)],
         proof=(0x800262D0,bytes.fromhex(request['loader'])))
    loaded=c.relocated(original,reloc,base);buffer=base+c.BUFFER-c.RAM
    check('complete relocated cartridge actor and cleared owned BSS',base,loaded)
    check('installed relocation header and unchanged relocation records',relocation_buffer,new_reloc)
    proof=(base,loaded[:c.SECTIONS[0]])
    write(CLIP,words(base+c.FILE_BYTES))
    write(game,words(graph));write(graph,bytes(0x300))
    # Temporarily select the existing first event slot for K.K.'s draw gate.
    # The complete saved payload is restored and checked before leaving.
    fixture=bytearray(event);struct.pack_into('>I',fixture,0,1)
    fixture[4:6]=bytes((0x21,10));struct.pack_into('>H',fixture,14,0x4000)
    write(EVENT,fixture)
    call(0x8008033C,[0x21,10],EVENT+12)
    cases=[(page,100) for page in range(16)]
    cases += [(0,timer) for timer in (19,20,21,59,60,183,184,222,223,224)]
    loaded_ids=set()
    for page,timer in cases:
        start,end=c.PAGES[page:page+2]
        write(buffer,b'G'*256)
        call(base+0x80AA3D08-c.RAM,[page],proof=proof)
        indices=[min(start+i,109) for i in range(10)]
        expected=b''.join(values[i].ljust(25,b' ') for i in indices)
        check('ten complete page rows with terminal clamp',buffer,expected+b'G'*6)
        loaded_ids.update(indices)
        write(graph+0x290,words(arena_end-arena,arena,arena,arena_end))
        write(graph+0x2B0,words(arena_end-arena,arena,arena,arena_end))
        call(base+0x80AA3D94-c.RAM,[game,timer,page],proof=proof)
        front=int.from_bytes(read(graph+0x2B8,4),'big')
        back=int.from_bytes(read(graph+0x29C,4),'big')
        count=25*(end-start)
        if not arena<=front<=back<=arena_end or arena_end-back!=64*count:
            raise ValueError(f'Credits graphics allocation differs: page={page}, timer={timer}, '
                             f'front={front:08X}, back={back:08X}, glyphs={count}')
        vertices=read(back,64*count)
        for offset in range(0,len(vertices),16):
            x,y,z=struct.unpack_from('>3h',vertices,offset)
            if not -2560<=x<=2560 or not -1920<=y<=1920 or z!=0:
                raise ValueError('Credit glyph vertex is outside the native screen')
            # The native font stores zero vertex colours and sets RGBA with
            # gDPSetPrimColor. Fade belongs to that display-list command.
            if vertices[offset+12:offset+16]!=bytes(4):
                raise ValueError('Credit glyph vertex colour storage differs')
        # Every actual glyph must issue its texture load, including padded
        # spaces. This tests the direct drawer, not a synthetic width counter.
        commands=read(arena,front-arena)
        colours=[struct.unpack_from('>I',commands,i+4)[0] for i in range(0,len(commands),8)
                 if struct.unpack_from('>I',commands,i)[0]==0xFA000000]
        if colours!=[0xFFFFFF00|alpha(timer)]*(end-start):
            raise ValueError(f'Credit row colour or fade differs: {colours}, timer={timer}')
        texture_count=sum(struct.unpack_from('>I',commands,i)[0]==0xFD88005F
                          for i in range(0,len(commands),8))
        if texture_count!=count:raise ValueError('Native credits omitted a glyph texture')
        check('drawing retains complete row text',buffer,expected+b'G'*6)
        check('unchanged original actor BSS and code',base,loaded[:c.FILE_BYTES+c.OLD_BSS])
        record({'credits_page':page,'timer':timer,'alpha':alpha(timer),'rows':end-start,
                'glyphs':count,'texture_loads':texture_count,'passed':True})
        draws+=1;glyphs+=count
    if loaded_ids!=set(range(110)):raise ValueError('Credit page fixtures missed loadable rows')
    write(EVENT,event);write(CLIP,clip)
    check('complete saved payload restored',SAVE_RAM,saved)
    check('native clip restored',CLIP,clip)
    check('approved native font unchanged',0x8013A680,native_font)
    check('approved widths unchanged',0x80106AF4,widths)
    check('relocation workspace retained',relocation_buffer,new_reloc)
    for at in edges:check('heap and native stack guard',at,EDGE)
    check('module guard',GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    call(0x8009C040,[allocation])
    return {'credits_pages':16,'credits_complete_rows':110,'credits_draws':draws,
            'credits_glyphs':glyphs,'credits_assertions':assertions,
            'normal_performance':False,'requires_checkpoint_restore':True}
