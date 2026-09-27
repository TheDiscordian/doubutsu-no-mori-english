"""Bounded native console-state execution on a disposable checkpoint.

The transition uses the actual game-state manager. It does not pretend that a
title-state test entered a room or acquired furniture through ordinary play.
"""
import json
import struct
import zlib
from pathlib import Path

from aflib import by_vrom,sha256,CODE_RAM,CODE_VROM
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB
from v3_console_games import NATIVE_RAM

HANDOVER=(0x800D20B4,32,'d84dc83756b24c65fa3eaf674d26684786090b342450e5c1cdd390841408b743')


def graph_snapshot(debug):
    """Saved OS context locates graph-thread waits when another thread runs."""
    raw=debug.read_memory(0x80145630,0x1B0)
    sp=struct.unpack_from('>Q',raw,0xF0)[0]&0xFFFFFFFF
    return dict(pointer='80145630',state=struct.unpack_from('>H',raw,16)[0],
        id=struct.unpack_from('>I',raw,20)[0],pc=f'{struct.unpack_from(">I",raw,0x11C)[0]:08X}',
        ra=f'{struct.unpack_from(">Q",raw,0x100)[0]&0xFFFFFFFF:08X}',sp=f'{sp:08X}',
        context=raw.hex(),stack=debug.read_memory(sp,128).hex()
        if not sp&7 and 0x80000400<=sp<=0x80400000-128 else None)


def exercise(debug,rom_path,action,state,record):
    path=Path(rom_path);image=path.read_bytes();report=json.loads((path.parent/'build.json').read_bytes())
    if sha256(image)!=report['output_sha256']:raise ValueError('Changed console gameplay test cartridge')
    images=report['equipment_resources']['console_images'];packet=images['packet']
    files=by_vrom(image);blob=files[BLOB].extract(image)
    def words(address,count):return struct.unpack('>'+str(count)+'I',debug.read_memory(address,count*4))
    def core_call(address,size,args):
        core=files[CODE_VROM].extract(image)
        result=debug.call(f'{address:08X}',args,return_address=MODULE_RAM+0x6480,
            verified_code=(address,core[address-CODE_RAM:address-CODE_RAM+size]))
        record(result);return result
    owner=words(0x8010EF90,1)[0]
    if owner&3 or not 0x80000400<=owner<=0x80400000-0xE0:
        raise ValueError('Invalid native game-state owner')
    if action.get('launch'):
        game=action['launch']
        if type(game) is not int or not 8<=game<=19:raise ValueError('Invalid imported test game')
        actual=debug.read_memory(packet['ram'],packet['bytes'])
        if actual!=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]:
            raise ValueError('Console startup packet differs from cartridge')
        if words(0x804DC800,1)!=(0x41464335,):raise ValueError('Console storage is not initialized')
        debug.write_memory(0x80137898,bytes((game,0)))
        debug.write_memory(0x80136EA3,b'\0')
        state['game']=game
        state['metadata']=actual[images['metadata']['ram']-packet['ram']:]
        # The real room calls sAdo_SubGameStart after requesting the transition
        # (8093A4F8..8093A518). Title-state launch must provide the same handover;
        # otherwise initialization waits for an audio command never submitted.
        at,size,digest=HANDOVER;core=files[CODE_VROM].extract(image)
        if sha256(core[at-CODE_RAM:at-CODE_RAM+size])!=digest:
            raise ValueError('Changed complete native console audio handover')
        core_call(0x800D36F4,32,[owner])
        core_call(at,size,[])
        return dict(console_native_launch=game,transition='native_game_state_manager',
                    source_audio_handover=True,
                    ordinary_room_entry_tested=False)
    header=words(0x804FE820,18)
    magic,base,game,player,image_bytes,error,image_ram,emulator,battery=header[:9]
    heap=words(owner+0x78,4);size,start,head,tail=heap
    fault=words(0x8003CE34,1)[0]
    record(dict(console_native_snapshot=dict(session=[f'{n:08X}' for n in header],
        heap=dict(size=size,start=f'{start:08X}',head=f'{head:08X}',tail=f'{tail:08X}',free=tail-head),
        fault_thread=f'{fault:08X}',owner=f'{owner:08X}',
        current_registers=debug.command('g'),thread=debug.thread_snapshot(),
        graph_thread=graph_snapshot(debug),
        fault_context=debug.read_memory(fault,0x1B0).hex() if 0x80000400<=fault<=0x80400000-0x1B0 else None)))
    if (magic!=0x41464E45 or game!=state['game'] or player!=0 or error or not emulator or
            header[17]!=1 or fault or base&15 or not 0x80000400<=base<=0x80400000-0x2E990):
        raise ValueError('Native console did not reach an active healthy imported session')
    if not 0x80000400<=start<=head<=tail<=start+size<=0x80400000:
        raise ValueError('Native console game arena is out of bounds')
    globals_at=base+0x80854A08-NATIVE_RAM
    native=words(globals_at,13);graphics=native[2]
    entry=state['metadata'][32+(game-1)*64:32+game*64]
    values=struct.unpack('>16I',entry)
    header_at=values[4];chr_banks=state['metadata'][header_at+5]
    graphics_bytes=max(0x25008,0x2008+(chr_banks<<13))
    ranges=((image_ram,image_bytes),(emulator,0x16F90),(battery,8192),(graphics,graphics_bytes))
    for address,length in ranges:
        if not start<=address<address+length<=start+size:
            raise ValueError('Native console buffer is outside its game arena')
    for i,(a,n) in enumerate(ranges):
        for b,m in ranges[i+1:]:
            if a<b+m and b<a+n:raise ValueError('Native console buffers overlap')
    if image_bytes!=values[5] or zlib.crc32(debug.read_memory(image_ram,image_bytes))!=values[3]:
        raise ValueError('Native console image differs from the full donor image')
    work=debug.read_memory(emulator,2048)
    if 'work' in state and state['work']==work:raise ValueError('Native console work RAM did not advance')
    state['work']=work
    return dict(console_native_execution='passed',game=game,full_image_bytes=image_bytes,
        graphics_bytes=graphics_bytes,arena_free_bytes=tail-head,work_sha256=sha256(work),
        ordinary_room_entry_tested=False,reset_return_tested=False,hardware_tested=False)
