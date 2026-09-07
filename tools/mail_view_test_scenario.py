#!/usr/bin/env python3
"""Execute read-only mail layout, real font drawing, and relocated call shims."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from font import WIDTH_TABLE
from aflib import CODE_VROM
from display_names import HEADER as NAME_HEADER, VROM as NAME_VROM
from mail_view_patch import CALLS
from mail_viewer import RAM, VROM
from runtime_layout import TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from runtime_module import MODULE_RAM, verify_test_module

SUBMENU, COLOUR, GAME = TEST_RETURN+0x20, TEST_RETURN+0x58, TEST_RETURN+0x60
LINE, POS, GRAPH = TEST_RETURN+0x80, TEST_RETURN+0x100, TEST_RETURN+0x180
BOARD_PTR, BOARD = TEST_RETURN+0x4A0, TEST_RETURN+0x4D0
OVERLAY = BOARD_PTR-0x106E4
MENU = OVERLAY+0x103E8
GFX, GFX_BYTES, LOW_STACK = TEST_RETURN+0x600, 4608, TEST_RETURN+0x1840
SOURCE, ALT_RETURN = TEST_RETURN+0x500, TEST_RETURN+0x900
EDGE = b'EDGE'*4


def fword(value):
    return struct.unpack('>I',struct.pack('>f',value))[0]


def scenario(rom, module):
    verify_test_module(rom,module)
    files = by_vrom(rom)
    overlay = files[VROM].extract(rom)
    for address, _, symbol in CALLS:
        target = int(module['symbols'][symbol],16)
        if struct.unpack_from('>I',overlay,address-RAM)[0] != 0x0C000000 | ((target&0x0FFFFFFF)>>2):
            raise ValueError('Native mail-view scenario requires its installed overlay calls')
    cuts = files[CODE_VROM].extract(rom)[WIDTH_TABLE:WIDTH_TABLE+256]
    if GFX+GFX_BYTES+16 >= LOW_STACK or LOW_STACK+16 >= TEST_STACK-0x600:
        raise ValueError('Native mail-view test fixture/stack overlap')
    actions = [{'wait':8},{'save_state':True},{'pause_game_thread':True}]
    def write(address,data):
        actions.append({'write':[f'{address:08X}',data.hex()]})
    def read(address,data):
        actions.append({'read':[f'{address:08X}',len(data)],'expect':data.hex()})
    def call(symbol,args,expected=None,alternate=False):
        value = {'address':module['symbols'][symbol],'arguments':args}
        if expected is not None: value['expect_return'] = expected
        if alternate: value['return_address'] = f'{ALT_RETURN:08X}'
        actions.append({'call':value})
    write(LOW_STACK,EDGE)
    write(TEST_STACK+0x30,EDGE)
    for text in (b'',b'\xcdabc',b'  a\xcd  z',b'a'*33,b'i'*49,b'\xa1'*17,b"I'i"*30):
        used = drawn = pixels = newline = 0
        for code in text:
            if code == 205:
                used += 1
                newline = 1
                break
            advance = 12-cuts[code]
            if pixels+advance > 192: break
            pixels += advance
            used += 1
            drawn += 1
        write(SOURCE-16,EDGE+text+b'\0'+EDGE)
        write(LINE-16,EDGE+b'!'*16+EDGE)
        call('af_mail_next_line',[LINE,SOURCE,len(text)],1)
        read(LINE-16,EDGE+struct.pack('>4I',used,drawn,pixels,newline)+EDGE)
        read(SOURCE-16,EDGE+text+b'\0'+EDGE)
    for args in ([0,SOURCE,1],[LINE,0,1],[LINE,SOURCE,1025]):
        write(LINE-16,EDGE+b'!'*16+EDGE)
        call('af_mail_next_line',args,0)
        read(LINE-16,EDGE+b'!'*16+EDGE)

    write(SUBMENU,bytes(0x2C)+struct.pack('>I',OVERLAY))
    write(COLOUR,bytes([70,40,50,255]))
    write(GAME,struct.pack('>I',GRAPH))
    write(BOARD_PTR,struct.pack('>I',BOARD))
    def graphics():
        write(GRAPH,bytes(0x300))
        write(MENU+0x38,struct.pack('>I',1))
        write(GRAPH+0x290,struct.pack('>4I',GFX_BYTES,GFX,GFX,GFX+GFX_BYTES))
        write(GFX-16,EDGE+bytes(GFX_BYTES)+EDGE)
    def guards(glyphs,lines):
        read(GRAPH+0x298,struct.pack('>2I',GFX+24*lines+glyphs*72,GFX+GFX_BYTES-glyphs*64))
        read(GFX-16,EDGE)
        read(GFX+GFX_BYTES,EDGE)
        read(LOW_STACK,EDGE)
        read(TEST_STACK+0x30,EDGE)
    def vertices(spans,x,y):
        glyph = 0
        for row,span in spans:
            offset = 0
            for code in span:
                left = int((x+offset-160)*16)
                top = int((120-y-row*16)*16)
                right = left+(12-cuts[code])*16
                base = GFX+GFX_BYTES-(glyph+1)*64
                for corner,(vx,vy) in enumerate(((left,top),(left,top-256),(right,top-256),(right,top))):
                    read(base+corner*16,struct.pack('>3h',vx,vy,0))
                offset += 12-cuts[code]
                glyph += 1
    for text, lines, glyphs in ((b'a'*33,2,33),(b'i'*20,1,20),(b' a \xcd\xcd z',2,5)):
        value = bytearray(192)
        value[6] = len(text)
        value[0x3C:0x9C] = text.ljust(96,b' ')
        write(BOARD,bytes(value))
        graphics()
        write(POS,struct.pack('>3f',64,-96,56))
        call('af_mail_body_hook',[SUBMENU,MENU,GAME,fword(64),POS,POS+4,POS+8,COLOUR])
        read(POS,struct.pack('>f',160))
        read(BOARD,bytes(value))
        guards(glyphs,lines)
        spans,remaining = [],text
        for row in range(6):
            count = pixels = 0
            while count < len(remaining) and remaining[count] != 205:
                advance = 12-cuts[remaining[count]]
                if pixels+advance > 192: break
                pixels += advance
                count += 1
            if count: spans.append((row,remaining[:count]))
            consumed = count+int(count < len(remaining) and remaining[count] == 205)
            remaining = remaining[consumed:]
        if remaining: raise ValueError('Native glyph probe unexpectedly exceeds six lines')
        vertices(spans,64,64)
        actions.append({'read':[f'{GFX:08X}',GFX_BYTES]})
    text = b"iI'hello"
    value = bytearray(192)
    value[7] = len(text)
    value[0x9C:0xAC] = text.ljust(16,b' ')
    write(BOARD,bytes(value))
    graphics()
    call('af_mail_footer_hook',[SUBMENU,GAME,fword(64),fword(172),COLOUR])
    read(BOARD,bytes(value))
    guards(len(text),1)
    vertices([(0,text)],256-sum(12-cuts[code] for code in text),172)
    actions.append({'read':[f'{GFX:08X}',GFX_BYTES]})

    # The full reader also replaces ordinary read-mode headers. Name insertion
    # and special no-name types must retain the native semantics.
    names = files[NAME_VROM].extract(rom)
    if len(names) != 2272 or names[:32] != NAME_HEADER:
        raise ValueError('Ordinary NPC headers require the complete display-name resource')
    rows = [names[32+i*8:40+i*8].rstrip(b' ') for i in range(216)]
    longest = [i for i,row in enumerate(rows) if len(row) == 8]
    if len(longest) < 2:
        raise ValueError('Missing full-width NPC header witnesses')
    shortest = min(range(216),key=lambda i:len(rows[i]))
    name_configuration = MODULE_RAM+0x3C
    cases = [(4,0,0,True),(3,0,0,True)]
    cases += [(4,1,i,True) for i in (longest[0],longest[-1],shortest,216)]
    cases += [(4,0,longest[0],True),(4,2,longest[0],True),
              (4,1,longest[0],False),(3,1,longest[0],True)]
    for kind,recipient_type,npc_index,enabled in cases:
        value = bytearray(192)
        value[3],value[5],value[0x2F],value[0x30] = 6,5,3,kind
        value[8:14] = b'READER'
        value[8+0x0C],value[8+0x10] = npc_index,recipient_type
        value[0x32:0x3C] = b'To ! '.ljust(10,b' ')
        name = rows[npc_index] if enabled and recipient_type == 1 and npc_index < 216 else b'READER'
        text = b'To '+name+b'! ' if kind == 4 else bytes(value[0x32:0x3C])
        read(name_configuration,struct.pack('>I',NAME_VROM))
        if not enabled:
            write(name_configuration,bytes(4))
        write(BOARD,bytes(value))
        graphics()
        call('af_mail_header_hook',[SUBMENU,GAME,MENU,fword(64),fword(36),COLOUR])
        read(BOARD,bytes(value))
        guards(len(text),1)
        vertices([(0,text)],64,36)
        if not enabled:
            write(name_configuration,struct.pack('>I',NAME_VROM))

    # Emulate distinct loaded overlay bases through a return address inside
    # isolated scratch. Only the original target is replaced by a test stub;
    # every hook instruction executes unchanged. Stubs preserve all arguments.
    for symbol,delta,token,args in (
            ('af_mail_body_hook',0x60C,0xB0,[SUBMENU,MENU,GAME,fword(64),POS,POS+4,POS+8,COLOUR]),
            ('af_mail_footer_hook',0x6F8,0xF0,[SUBMENU,GAME,fword(64),fword(172),COLOUR]),
            ('af_mail_header_hook',0x364,0xA0,[SUBMENU,GAME,MENU,fword(64),fword(36),COLOUR])):
        stub = [0x3C0A0000|(POS>>16),0x354A0000|(POS&0xFFFF)]
        stub += [0xAD400000|(reg<<16)|(index*4) for index,reg in enumerate(range(4,8))]
        stub += [0x24020000|token,0x03E00008,0]
        write(ALT_RETURN-delta,struct.pack('>'+str(len(stub))+'I',*stub))
        for mode in (0,2,3,4):
            write(MENU+0x38,struct.pack('>I',mode))
            write(POS,bytes(16))
            call(symbol,args,token,alternate=True)
            read(POS,struct.pack('>4I',*args[:4]))
            read(TEST_STACK+16,struct.pack('>'+str(len(args)-4)+'I',*args[4:]))
    read(LOW_STACK,EDGE)
    read(TEST_STACK+0x30,EDGE)
    read(GUARD_ADDRESS,struct.pack('>4I',*([GUARD_WORD]*4)))
    actions += [{'load_state':True},{'resume':True},{'wait':2}]
    read(SUBMENU,bytes(4))
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions = scenario(rom,json.loads(args.module.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'rom_sha256':sha256(rom)}))


if __name__ == '__main__':
    main()
