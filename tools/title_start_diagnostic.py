"""Read one ordinary Press Start draw without changing game memory or saves."""
import struct

from aflib import by_vrom, sha256
from title_start_smoke import locate
from title_press_start import RAM, ASSETS
from title_overlay import NEW_ACTOR, NEW_RELOC
from catalogue_names import Image
from npc_mail_show import relocate_verified_data

BUILDS = {
    '128f19b734565e5e0c3af15aaf1fef8fb066155039404a2bfdd29efe8010bf19',
    'a8072a76783317215ae85afbf31cca77422d5b783512194d8269004f31073780',
}


def observe(debug, rom):
    if sha256(rom) not in BUILDS:
        raise ValueError('Unreviewed title diagnostic cartridge')
    debug.command('?')
    read, actor, base, bank = locate(debug, memory_end=0x80800000)
    files = by_vrom(rom)
    code, reloc = files[NEW_ACTOR].extract(rom), files[NEW_RELOC].extract(rom)
    expected = relocate_verified_data(Image(RAM, len(code), struct.unpack_from('>5I', reloc)),
                                     code, reloc, base, memory_end=0x80800000)
    for at in range(0, len(code), 4096):
        if read(base+at, len(expected[at:at+4096])) != expected[at:at+4096]:
            raise ValueError('Loaded title differs from the cartridge')
    if read(bank, files[ASSETS].size) != files[ASSETS].extract(rom):
        raise ValueError('Loaded title bank differs from the cartridge')
    # Stop after the native routine has emitted all three prompt rectangles.
    pc = base+0x80AA19BC-RAM
    if read(pc, 4) != bytes.fromhex('AD6202B8'):
        raise ValueError('Changed native Press Start return site')
    point = f'0,{pc:x},4'
    if debug.command('Z'+point) != 'OK':
        raise ValueError('Could not set read-only title observation breakpoint')
    try:
        reply = debug.command('c')
        registers = debug.command('g')
        if (reply[:3] not in ('T05', 'S05') or len(registers) != 71*16
                or int(registers[37*16:38*16], 16) & 0xFFFFFFFF != pc):
            raise ValueError('Did not reach the ordinary Press Start drawing path')
        end = int(registers[2*16:3*16], 16) & 0xFFFFFFFF
        graph = int(registers[11*16:12*16], 16) & 0xFFFFFFFF
        start = int.from_bytes(debug.read_memory(graph+0x2B4, 4), 'big')
        if start & 7 or end & 7 or not 0x80000400 <= start < end <= 0x80400000 or end-start > 0x10000:
            raise ValueError('Invalid current font command stream')
        stream = debug.read_memory(start, end-start)
        # Retain nested native/model lists too: root-only segment state can lie.
        segments = [0]*16
        log, steps = [], [0]
        def address(pointer):
            if pointer >> 24 < 16:
                return (segments[pointer >> 24]+(pointer & 0xFFFFFF)) | 0x80000000
            if pointer & 0xE0000000 == 0x80000000:
                return pointer
            raise ValueError('Unsupported display-list pointer')
        def walk(data, depth=0):
            if depth > 12:
                raise ValueError('Excessive display-list nesting')
            offset = 0
            while offset < len(data):
                a, b = struct.unpack_from('>2I', data, offset)
                offset += 8; steps[0] += 1
                if steps[0] > 20000:
                    raise ValueError('Excessive display-list length')
                op = a >> 24
                if op == 0xDB and a >> 16 & 255 == 6:
                    index = (a & 65535)//4
                    if index >= 16:
                        raise ValueError('Invalid graphics segment')
                    segments[index] = b & 0x1FFFFFFF
                    log.append({'segment': index, 'base': f'{b:08X}'})
                elif op == 0xFD:
                    resolved = address(b)
                    log.append({'texture': f'{a:08X}', 'pointer': f'{b:08X}',
                                'resolved': f'{resolved:08X}'})
                elif op == 0xDE:
                    target = address(b)
                    nested = bytearray()
                    for i in range(4096):
                        command = debug.read_memory(target+i*8, 8)
                        nested.extend(command)
                        if command[0] == 0xDF or command[:2] == b'\xde\x01':
                            break
                    else:
                        raise ValueError('Unterminated nested display list')
                    walk(bytes(nested), depth+1)
                    if a >> 16 & 255:
                        return
                elif op == 0xDF:
                    return
        walk(stream)
        return {'title_start_diagnostic': 'observed', 'rom_sha256': sha256(rom),
                'actor': f'{actor:08X}', 'bank': f'{bank:08X}',
                'bank_sha256': sha256(files[ASSETS].extract(rom)),
                'font_start': f'{start:08X}', 'font_end': f'{end:08X}',
                'font_stream': stream.hex(), 'commands_traversed': steps[0],
                'texture_and_segment_trace': log, 'game_memory_modified': False,
                'visual_acceptance': False}
    finally:
        debug.command('z'+point)

