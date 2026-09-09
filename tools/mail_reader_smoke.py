"""Observe complete snapshot pages and actual native glyph allocations."""

import struct
import time

from emulator_smoke import require_program_counter
from mail_view_smoke import snapshot as submenu_snapshot, pointer
from runtime_layout import MODULE_RAM, TEST_RETURN
from mail_glyph_codes import ADVANCES, glyph


def glyph_advances(text, widths):
    """Count complete displayed glyphs, not bytes in catalogue-four pairs."""
    result = [];pos = 0
    while pos < len(text):
        if text[pos] == 0x80:
            result.append(ADVANCES[glyph(text,pos)]);pos += 2
        else:
            advance = widths[text[pos]]
            if not 0 < advance <= 192: raise ValueError('Invalid native glyph width')
            result.append(advance);pos += 1
    return result


def snapshot(debug, address):
    address = int(address,16) if isinstance(address,str) else address
    if address & 15 or not MODULE_RAM+0x300 <= address <= TEST_RETURN-2236:
        raise ValueError('Snapshot reader cache must remain inside linked module RAM')
    owner,status,page,total,h,b,f = struct.unpack('>7I',debug.read_memory(address,28))
    if status not in (1,2) or not 0 <= page < total <= 1029 or h > 1032 or b > 1024 or f > 1024:
        raise ValueError('Invalid active snapshot-reader cache')
    layout = debug.read_memory(address+28,136)
    pages,count = struct.unpack_from('>2I',layout)
    if pages != total or count > 8:
        raise ValueError('Invalid snapshot page layout')
    letter = debug.read_memory(address+1196,1040)
    offsets = struct.unpack_from('>3H',letter)
    if offsets[1]+b > 1024 or offsets[2]+f > 1024:
        raise ValueError('Invalid snapshot text offsets')
    parts = (debug.read_memory(address+164,h) if h else b'',
             letter[16+offsets[1]:16+offsets[1]+b],letter[16+offsets[2]:16+offsets[2]+f])
    spans = []
    for i in range(count):
        section,offset,length,y = struct.unpack_from('>4I',layout,8+i*16)
        if section > 2 or offset+length > len(parts[section]) or y > 136:
            raise ValueError('Invalid snapshot page span')
        text = parts[section][offset:offset+length]
        if 205 in text:
            raise ValueError('An explicit newline reached the glyph renderer')
        spans.append({'section':section,'offset':offset,'length':length,'y':y,'text':text.hex()})
    return {'owner':f'{owner:08X}','status':status,'page':page,'total':total,
            'header':parts[0].hex(),'body':parts[1].hex(),'footer':parts[2].hex(),'spans':spans}


def graphics(debug):
    game = pointer(debug,0x8010EF90,0x1DAC)
    graph = pointer(debug,game,0x300)
    size,base,front,back = struct.unpack('>4I',debug.read_memory(graph+0x290,16))
    if not 0x80000000 <= base <= front <= back <= base+size <= 0x80400000:
        raise ValueError('Native font graphics arena overflow or invalid pointers')
    return {'game':f'{game:08X}','graph':f'{graph:08X}',
            'size':size,'base':base,'front':front,'back':back}


def observe_draw(debug, reader, hook, record):
    """Verify all generated glyph quads between actual header entry and return."""
    record(debug.pause_game_thread())
    current = snapshot(debug,reader)
    board = submenu_snapshot(debug)
    if board.get('board_mode') != 1 or board.get('board_state') != 2 or current['owner'] != board.get('board'):
        raise ValueError('Snapshot reader is not the active native read-only board')
    target = int(hook,16)
    returned = int(board['board_base'],16)+0x11AC
    installed = set()
    def command(value,expected=None):
        result = debug.command(value)
        record({'mail_draw_command':value,'result':result})
        if expected is not None and result != expected:
            raise ValueError('Unexpected mail-draw debugger response')
        return result
    def add(address):
        command(f'Z0,{address:x},4','OK')
        installed.add(address)
    def remove(address):
        command(f'z0,{address:x},4','OK')
        installed.remove(address)
    def stopped(address):
        command('c','S05')
        registers = command('g')
        require_program_counter(registers,f'{address:08X}')
        return [int(registers[i:i+16],16)&0xFFFFFFFF for i in range(0,len(registers),16)]
    try:
        add(target)
        registers = stopped(target)
        if registers[31] != returned:
            raise ValueError('Snapshot renderer has an unexpected native return address')
        x = struct.unpack('>f',struct.pack('>I',registers[7]))[0]
        y = struct.unpack('>f',debug.read_memory(registers[29]+16,4))[0]
        if (x,y) != (64.0,36.0):
            raise ValueError(f'Letter is not fully settled at its native origin: {(x,y)}')
        before = graphics(debug)
        widths = [12-cut for cut in debug.read_memory(0x80106AF4,256)]
        remove(target)
        add(returned)
        stopped(returned)
        after = graphics(debug)
        remove(returned)
    finally:
        for address in sorted(installed):
            command(f'z0,{address:x},4','OK')
    draws = []
    for span in current['spans']:
        text = bytes.fromhex(span['text'])
        if text:
            advances = glyph_advances(text,widths)
            px = x+192-sum(advances) if span['section'] == 2 else x
            draws.append((advances,px,y+span['y']))
    if current['total'] > 1:
        draws.append((glyph_advances(f"Left/Right: {current['page']+1}/{current['total']}".encode(),widths),x,y+164))
    glyphs = sum(len(advances) for advances,_,_ in draws)
    if (before['base'],before['size']) != (after['base'],after['size']):
        raise ValueError('Native font arena changed during a draw')
    if after['front']-before['front'] != 24*len(draws)+72*glyphs or before['back']-after['back'] != 64*glyphs:
        raise ValueError(f'Unexpected complete-letter graphics allocation: {before}, {after}, glyphs={glyphs}')
    vertices = debug.read_memory(after['back'],glyphs*64) if glyphs else b''
    index = 0
    for advances,px,py in draws:
        for advance in advances:
            left,top = int((px-160)*16),int((120-py)*16)
            right = left+advance*16
            base = before['back']-(index+1)*64
            for corner,expected in enumerate(((left,top,0),(left,top-256,0),(right,top-256,0),(right,top,0))):
                actual = struct.unpack_from('>3h',vertices,base-after['back']+corner*16)
                if actual != expected:
                    raise ValueError(f'Mail glyph {index}, corner {corner}: {actual}, expected {expected}')
            px += advance
            index += 1
    record({'mail_page_drawing':current,'glyphs_verified':glyphs,'vertex_positions_verified':glyphs*4,
            'graphics_before':before,'graphics_after':after,'entry_pc':f'{target:08X}',
            'return_pc':f'{returned:08X}','native_origin':[x,y]})
    return current


def all_pages(debug, keyboard, spec, record):
    state = snapshot(debug,spec['reader'])
    if state['page'] != 0:
        raise ValueError('A full letter-page probe must start on page zero')
    for field in ('header','body','footer','status'):
        if state[field] != spec[field]:
            raise ValueError(f'Unexpected complete-letter {field}')
    collected = [bytearray(),bytearray()]
    for page in range(state['total']):
        current = observe_draw(debug,spec['reader'],spec['hook'],record)
        if current['page'] != page or any(current[field] != state[field] for field in ('header','body','footer','total','status')):
            raise ValueError('Letter content changed or the page did not advance')
        for span in current['spans']:
            if span['section']:
                collected[span['section']-1].extend(bytes.fromhex(span['text']))
        debug.send('c')
        if page+1 < state['total']:
            time.sleep(0.2)
            keyboard.press('Right',0.12)
            time.sleep(0.4)
    if tuple(map(bytes,collected)) != tuple(bytes.fromhex(state[field]).replace(b'\xcd',b'') for field in ('body','footer')):
        raise ValueError('The full page traversal omitted or duplicated letter text')
    if state['total'] > 1:
        keyboard.press('Left',0.12)
        time.sleep(0.4)
        previous = snapshot(debug,spec['reader'])
        if previous['page'] != state['total']-2:
            raise ValueError('Left did not return to the previous letter page')
    record({'complete_mail_page_traversal':True,'pages':state['total'],
            'body_bytes':len(bytes.fromhex(state['body'])),'footer_bytes':len(bytes.fromhex(state['footer'])),
            'backward_page_checked':state['total'] > 1})
