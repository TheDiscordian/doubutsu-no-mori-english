#!/usr/bin/env python3
"""Exercise separate English glyphs through both actual native drawing paths.

Hooks and resources exist only inside a restored emulator checkpoint. This does
not install a cartridge resource, approve saved text, or validate reveal timing.
"""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from build_extended_font_probe import RAM, LIMIT, source_hashes, relocate
from extended_glyphs import GLYPHS, RESOURCE_BYTES, validate_resource
from font import WIDTH_TABLE
from runtime_layout import GUARD_ADDRESS, GUARD_WORD, TEST_STACK
from runtime_module import verify_test_module

RESOURCE, SENTENCE, GAME, GRAPH = 0x8019B400, 0x8019BA80, 0x8019BB20, 0x8019BB40
GFX_PP, GFX, VERTEX_END = 0x8019BE50, 0x8019BE80, 0x8019C200
TEXT, WINDOW, DATA, LOW_STACK = 0x8019C220, 0x8019C2A0, 0x8019C2E0, 0x8019C340
EDGE = b'GLYP'*4
HOOKS = {0x80090178:'af_glyph_texture', 0x8009028C:'af_glyph_code_width',
         0x8009069C:'af_glyph_load_texture', 0x800918A8:'af_glyph_draw_char'}


def words(*values):
    return struct.pack('>'+'I'*len(values), *values)


def floats(*values):
    return struct.pack('>'+'f'*len(values), *values)


def texture_commands(texture, code):
    x, y = code%16*12, code//16*16
    return words(0xFD88005F, texture, 0xF5880200, 0x070C0300,
                 0xE6000000, 0, 0xF4000000 | x*2<<12 | y*4,
                 0x07000000 | (x+11)*2<<12 | (y+15)*4,
                 0xE7000000, 0, 0xF5800200, 0x000C0300,
                 0xF2000000 | x*4<<12 | y*4, (x+11)*4<<12 | (y+15)*4)


def scenario(rom, native, module, binary, report, resource):
    native = verified_rom(native)
    verify_test_module(rom, module)
    validate_resource(resource)
    if (report['sources'] != source_hashes() or report['ram'] != RAM
            or report['bytes'] != len(binary) or report['sha256'] != sha256(binary)
            or not 0 < len(binary) <= LIMIT or report['installed'] is not False):
        raise ValueError('Stale or invalid isolated font probe')
    symbols = report['symbols']
    if any(not RAM <= symbols[name] < RAM+len(binary) for name in set(HOOKS.values()) | {
            'af_glyph_bind','af_glyph_string_width','af_glyph_skip_tag','active_glyph','glyph_resource'}):
        raise ValueError('Font probe symbol escapes its isolated allocation')
    files = by_vrom(rom)
    code = files[CODE_VROM].extract(rom)
    original = by_vrom(native)[CODE_VROM].extract(native)
    cuts = code[WIDTH_TABLE:WIDTH_TABLE+256]
    guards = {}
    for start, end in ((0x80090178,0x80090188),(0x8009069C,0x80090878),
                       (0x8009113C,0x800918E8),(0x80091C98,0x80091DFC),
                       (0x800BE1D4,0x800BE27C)):
        value = code[start-CODE_RAM:end-CODE_RAM]
        if value != original[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError(f'Changed native font caller at {start:08X}')
        guards[start] = value
    width = bytearray(original[0x8009028C-CODE_RAM:0x800902CC-CODE_RAM])
    width[8:12] = bytes(4)  # The approved always-proportional font patch.
    if code[0x8009028C-CODE_RAM:0x800902CC-CODE_RAM] != width:
        raise ValueError('Unexpected native width implementation')
    guards[0x8009028C] = bytes(width)
    for start,end in ((0x8002FE00,0x8002FE74),(0x80034CE0,0x80034D54)):
        at = 0x1060+start-0x80025C60
        if rom[at:at+end-start] != native[at:at+end-start]:
            raise ValueError('Changed native cache maintenance function')
        guards[start] = native[at:at+end-start]
    plan = {'binary':binary.hex(),'report':report,'resource':resource.hex(),'cuts':cuts.hex(),
            'guards':{f'{at:08X}':value.hex() for at,value in guards.items()}}
    # Validate the generated fixture before starting an emulator.
    native_actions(plan,0x801A0010)
    actions = [{'wait':8},{'save_state':True},{'pause_game_thread':True},
               {'test_extended_font':plan},{'load_state':True},{'resume':True},{'wait':2}]
    for at in HOOKS:
        actions.append({'read':[f'{at:08X}',8],'expect':code[at-CODE_RAM:at-CODE_RAM+8].hex()})
    return actions


def native_actions(plan, base):
    """Generate the same complete expected native calls for an owned allocation."""
    report = plan['report']
    binary = relocate(bytes.fromhex(plan['binary']),report,base)
    resource = validate_resource(bytes.fromhex(plan['resource']))
    guards = {int(at,16):bytes.fromhex(value) for at,value in plan['guards'].items()}
    cuts = bytes.fromhex(plan['cuts'])
    symbols = {name:value+base-RAM for name,value in report['symbols'].items()}
    resource_at,sentence,game,graph,gfx_pp,gfx,vertex_end,text,window,data = (
        at+base-RAM for at in (RESOURCE,SENTENCE,GAME,GRAPH,GFX_PP,GFX,VERTEX_END,TEXT,WINDOW,DATA))
    return _native_actions(base,binary,resource,guards,cuts,symbols,resource_at,sentence,game,graph,
                           gfx_pp,gfx,vertex_end,text,window,data)


def _native_actions(RAM,binary,resource,guards,cuts,symbols,RESOURCE,SENTENCE,GAME,GRAPH,
                    GFX_PP,GFX,VERTEX_END,TEXT,WINDOW,DATA):
    if not (RAM+LIMIT+16 < RESOURCE and RESOURCE+RESOURCE_BYTES+16 < SENTENCE
            and DATA+64+16 < RAM+0x2000 and LOW_STACK < TEST_STACK-0x400):
        raise ValueError('Font fixture overlaps code, resources, or the native test stack')
    actions = []
    def write(at,value): actions.append({'write':[f'{at:08X}',value.hex()]})
    def read(at,value): actions.append({'read':[f'{at:08X}',len(value)],'expect':value.hex()})
    def call(target,args=(),expected=None):
        at = symbols[target] if isinstance(target,str) else target
        value = {'address':f'{at:08X}','arguments':list(args)}
        if expected is not None: value['expect_return'] = expected
        actions.append({'call':value})
    for at,value in guards.items(): read(at,value)
    write(RAM,binary)
    write(RESOURCE-16,EDGE+resource+EDGE)
    for at in (RAM-16,RAM+LIMIT,SENTENCE-16,SENTENCE+0x88,
               GFX-16,GFX+256,VERTEX_END-512-16,VERTEX_END,TEXT-16,TEXT+96,
               WINDOW-16,WINDOW+16,DATA-16,DATA+64,LOW_STACK,TEST_STACK+0x30):
        write(at,EDGE)
    call(0x8002FE00,[RAM,DATA+64-RAM])
    call(0x80034CE0,[RAM,len(binary)])
    read(RAM,binary)
    call('af_glyph_bind',[RESOURCE,len(resource)],1)
    read(symbols['glyph_resource'],words(RESOURCE))
    for args in ((RESOURCE+1,len(resource)),(RESOURCE,len(resource)-1),(0,len(resource))):
        call('af_glyph_bind',args,0)
    for at,name in HOOKS.items():
        patch = words(0x08000000 | (symbols[name]&0x0FFFFFFF)>>2,0)
        write(at,patch)
        call(0x8002FE00,[at,len(patch)])
        call(0x80034CE0,[at,len(patch)])
        read(at,patch)
    write(GAME,words(GRAPH))
    # Mixed-width neighbours detect context leakage, wrong token lengths, and
    # disagreement between the native rectangles and textured polygon quads.
    tokens = [b'i',b'\x80\xD0',b'I',b'\x80\xAE',b"'",b'\x80\xA7',
              b'l',b'\x80\xAB',b'\xA1',b'\x80\xBA',b'Z',b'\x80\x42',b'\xE0']
    payload = b''.join(tokens)
    write(TEXT,payload)
    registered = {code:i for i,(_,code,_) in enumerate(GLYPHS)}
    pixel_width = sum(resource[48+registered[t[1]]] if len(t)==2 and t[1] in registered
                      else 12-cuts[t[0]] for t in tokens)
    # Unknown tags retain the old byte-wise prefix-width fallback.
    call('af_glyph_string_width',[TEXT,len(payload)],(pixel_width+12-cuts[0x42]+1)&~1)
    call('af_glyph_string_width',[TEXT,0],0)
    call('af_glyph_string_width',[TEXT,1025],0xFFFFFFFF)
    for poly in (False,True):
        write(SENTENCE,bytes(0x88))
        write(SENTENCE,words(TEXT,len(payload)))
        write(SENTENCE+0x0C,floats(25,100))
        write(SENTENCE+0x18,bytes((50,60,50,255)))
        write(SENTENCE+0x1C,floats(1,1,1,1))
        write(SENTENCE+0x34,floats(11,1,1))
        write(SENTENCE+0x48+5,bytes((0x83 if poly else 0x81,)))
        write(SENTENCE+0x48+0x0C,floats(100))
        write(SENTENCE+0x48+0x10,floats(*([1]*8)))
        index, width = 0,11
        for token in tokens:
            slot = registered.get(token[1]) if len(token)==2 else None
            advance = resource[48+slot] if slot is not None else 12-cuts[token[0]]
            texture, character = (RESOURCE+64,slot) if slot is not None else (0x8013A680,token[0])
            write(GRAPH,bytes(0x300))
            write(GRAPH+0x29C,words(VERTEX_END))
            write(GFX_PP,words(GFX))
            write(GFX,bytes(256))
            write(VERTEX_END-512,bytes(512))
            call(0x8009034C,[TEXT+index],len(token))
            call(0x80091C98,[SENTENCE,GAME,GFX_PP])
            expected = texture_commands(texture,character)
            left, right = 25+width,25+width+advance
            tx,ty = character%16*12,character//16*16
            if poly:
                expected += words(0x01004008,VERTEX_END-64,0x06000204,0x00000406)
                vertices = b''
                for x,y,s,t in ((left,100,tx,ty),(left,116,tx,ty+16),
                                 (right,116,tx+advance,ty+16),(right,100,tx+advance,ty)):
                    vertices += struct.pack('>4h2h4B',int((x-160)*16),int((120-y)*16),
                                            0,0,s*64,t*64,0,0,0,0)
                read(VERTEX_END-64,vertices)
                read(GRAPH+0x29C,words(VERTEX_END-64))
            else:
                expected += words(0xE4000000 | right*4<<12 | 116*4,left*4<<12 | 100*4,
                                  0xE1000000,tx*32<<16 | ty*32,0xF1000000,0x04000400)
                read(VERTEX_END-512,bytes(512))
                read(GRAPH+0x29C,words(VERTEX_END))
            read(GFX,expected+bytes(256-len(expected)))
            read(GFX_PP,words(GFX+len(expected)))
            index += len(token);width += advance
            read(SENTENCE+0x2C,words(index))
            read(SENTENCE+0x34,floats(width))
            read(SENTENCE+0x48+0x3C,floats(advance))
            read(symbols['active_glyph'],words(0))
            call(0x80090178,(),0x8013A680)
            read(LOW_STACK,EDGE)
        read(TEXT,payload)
    write(WINDOW,bytes(12)+words(DATA))
    for payload,at,result in ((b'\x80\xD0',0,0),(b'\x80\x42',0,1),(b'\x80',0,1),
                              (b'A\x80\xAB',1,0),(b'A',-1,0),(b'A',1,0)):
        value = words(1,1,len(payload),0)+payload
        write(DATA,value)
        call('af_glyph_skip_tag',[WINDOW,at&0xFFFFFFFF],result)
        read(DATA,value)
    write(DATA,words(1,1,1025,0))
    call('af_glyph_skip_tag',[WINDOW,0],0)
    write(WINDOW+12,words(0))
    call('af_glyph_skip_tag',[WINDOW,0],0)
    read(RESOURCE-16,EDGE+resource+EDGE)
    for at in (RAM-16,RAM+LIMIT,SENTENCE-16,SENTENCE+0x88,GFX-16,GFX+256,
               VERTEX_END-512-16,VERTEX_END,TEXT-16,TEXT+96,WINDOW-16,WINDOW+16,
               DATA-16,DATA+64,LOW_STACK,TEST_STACK+0x30): read(at,EDGE)
    read(GUARD_ADDRESS,words(*([GUARD_WORD]*4)))
    # No generated display list is submitted to the GPU. Restore every hook
    # before releasing the allocation, then restore the whole checkpoint.
    for at in HOOKS:
        original = next(value[at-start:at-start+8] for start,value in guards.items()
                        if start<=at<=start+len(value)-8)
        write(at,original)
        call(0x8002FE00,[at,8])
        call(0x80034CE0,[at,8])
        read(at,original)
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module',type=Path,required=True,help='Configured runtime-module report beside the built ROM')
    parser.add_argument('--probe',type=Path,default=Path('build/extended-font-probe'))
    parser.add_argument('--resource',type=Path,default=Path('build/extended-glyphs/glyphs.bin'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),json.loads(args.module.read_text()),
                       (args.probe/'font.bin').read_bytes(),json.loads((args.probe/'font.json').read_text()),
                       args.resource.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'native_glyph_draws':26,'production_installed':False}))


if __name__ == '__main__': main()
