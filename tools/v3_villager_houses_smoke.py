"""Native house-table initialization and foreground sorting/selection, not move-in."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
from v3_furniture_room_smoke import extend
from v3_villager_houses import HOUSE, FOREGROUND, STRIDE, NATIVE_START, TARGET_COUNT


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    houses = report.get('villager_houses')
    if sha256(rom) != report['output_sha256'] or not houses:
        raise ValueError('House probe requires the current assembled cartridge')
    files, proofs = by_vrom(rom), boot_proofs(rom)
    dma_at, dma_size = 0x80026B44, 0x7C
    dma_offset = dma_at - 0x80025C60 + 0x1060
    dma = rom[dma_offset:dma_offset + dma_size]
    if sha256(dma) != '2afa01edf9346c8c9f4a0c6b5fbadb03970d0e348c25f045d09af4ee2602f8d1':
        raise ValueError('Changed native synchronous DMA function')
    proofs[dma_at] = (dma_at, dma)
    code = files[CODE_VROM].extract(rom)
    blob = files[BLOB].extract(rom)[:0xC000]
    for start, end in ((0x800AB134, 0x800AB3A0), (0x80084FAC, 0x800850E4),
                       (0x80085490, 0x8008557C), (0x80085A84, 0x80085B40),
                       (0x80085178, 0x800851C8)):
        proofs[start] = (start, code[start - CODE_RAM:end - CODE_RAM])

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'house_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native house check failed: ' + label +
                             f'; expected={expected.hex()} observed={actual.hex()}')

    def call(address, args):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proofs.get(address))
        record(result)
        return result['return_value']

    check('complete unchanged resident prefix', BLOB_RAM, blob)
    # Probe the appended records only. A full foreground fixture duplicates the
    # scene's large allocation while the title scene still owns its heap.
    size = 0x4000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('House fixture allocation failed')
    fg, pointers, animals, npc, output = (allocation + value for value in
                                         (16, 0xA00, 0x1300, 0x2400, 0x2600))
    fg_vrom = int(houses.get('foreground_vrom', f'{FOREGROUND:08X}'), 16)
    data, table = (files[v].extract(rom) for v in (fg_vrom, HOUSE))
    if (sha256(data), sha256(table)) != (houses['output_fg_sha256'], houses['output_house_sha256']):
        raise ValueError('Changed installed house data')
    count = len(houses['appended_layers'])
    actor_ids = [0xE000] + [int(value,16) for value in houses['installed_villagers']]
    animal_count = len(actor_ids)
    tail_offset = (houses['foreground_records'] - count) * STRIDE
    tail = data[tail_offset:]
    padding = tail[count*STRIDE:]
    if count not in (2,4) or padding != bytes(len(padding)) or len(padding) >= 8:
        raise ValueError('House probe requires complete appended layers and alignment padding')
    # Use the private instruction-window route, avoiding a duplicate scene heap.
    # These twelve installed instructions contain no PC-relative references.
    start = allocation+0x3000
    window = code[0x800860FC-CODE_RAM:0x8008612C-CODE_RAM]
    end = start+len(window)
    check('installed native foreground bounds instructions',0x800860FC,window)
    debug.write_memory(start,window)
    call(0x8002FE00,[start,len(window)])
    call(0x80034CE0,[start,len(window)])
    before = debug.command('g')
    regs = [int(before[i:i+16],16) for i in range(0,len(before),16)]
    if len(regs)!=71 or regs[37]&0xFFFFFFFF != 0x800D334C:
        raise ValueError('House bounds window requires a paused game frame')
    stop = f'0,{end:x},4'
    if debug.command('Z'+stop) != 'OK': raise ValueError('House bounds breakpoint refused')
    try:
        regs[37] = extend(start)
        if debug.command('G'+''.join(f'{v:016x}' for v in regs)) != 'OK':
            raise ValueError('House bounds register write refused')
        stopped = debug.command('c'); raw = debug.command('g')
        actual = [int(raw[i:i+16],16) for i in range(0,len(raw),16)]
        expected = {1:STRIDE, 2:(fg_vrom+0x8000)&0xFFFF0000, 3:len(data), 5:fg_vrom,
                    9:TARGET_COUNT, 10:NATIVE_START, 11:fg_vrom+len(data), 12:len(data)+7,
                    13:houses['foreground_records'], 25:TARGET_COUNT*4,
                    33:houses['foreground_records'], 34:len(data)%STRIDE, 37:extend(end)}
        differences = {str(i):[v,actual[i]] for i,v in expected.items() if actual[i]!=v}
        passed = stopped[:3] in ('T05','S05') and not differences
        record({'house_bounds_window': True, 'differences': differences,
                'assertion':'passed' if passed else 'failed'})
        if not passed: raise ValueError('Native relocated house bounds mismatch')
    finally:
        debug.command('z'+stop)
        if debug.command('G'+before) != 'OK': raise ValueError('House bounds register restore refused')
    edge = b'V3HS' * 4
    guards = (allocation, fg + len(tail), pointers - 16, pointers + TARGET_COUNT * 4,
              animals - 16, animals + animal_count * 0x528, npc - 16, npc + animal_count * 56,
              output - 16, output + 0x200, allocation + size - 16,
              TEST_STACK - 0x800, TEST_STACK + 0x40)
    for address in guards:
        debug.write_memory(address, edge)
    call(0x80026B44, [fg, fg_vrom + tail_offset, len(tail)])
    check('complete appended foreground DMA', fg, tail)
    debug.write_memory(pointers, b'\xA5' * (TARGET_COUNT * 4))
    call(0x80084FAC, [pointers, fg, TARGET_COUNT, count, NATIVE_START])
    expected = bytearray(TARGET_COUNT * 4)
    for at in range(0, count * STRIDE, STRIDE):
        number = struct.unpack_from('>H', tail, at)[0]
        struct.pack_into('>I', expected, (number - NATIVE_START) * 4, fg + at)
    check('imported layer pointers and every empty subset slot', pointers, expected)
    animal_data = bytearray(b'\xA5' * (animal_count * 0x528))
    npc_data = bytearray(b'\xA5' * (animal_count * 56))
    for i, actor in enumerate(actor_ids):
        at = i * 0x528
        struct.pack_into('>H', animal_data, at, actor)
        animal_data[at + 0x4E1:at + 0x4E5] = bytes((3, 4, 5, 6))
        at = i * 56
        struct.pack_into('>H', npc_data, at, actor)
        for position in (4, 16):
            # mFI_UtNum2PosXZInBk returns the unit origin, not its centre.
            struct.pack_into('>3f', npc_data, at + position, 2120.0, 0.0, 2800.0)
        npc_data[at + 28] = 1
        npc_data[at + 44:at + 52] = table[(actor & 0xFFF) * 8:(actor & 0xFFF) * 8 + 8]
        struct.pack_into('>H', npc_data, at + 52, 0)
    debug.write_memory(animals, animal_data)
    debug.write_memory(npc, b'\xA5' * (animal_count * 56))
    call(0x800AB134, [npc, animals, animal_count, 1])
    check('complete native and imported NPC-list initialization', npc, npc_data)
    check('source animal records remain intact', animals, animal_data)
    saved = {address: debug.read_memory(address, length) for address, length in
             ((0x80130DB8, 2), (0x80137000, 56), (0x80137348, 2))}
    try:
        for n, actor in enumerate(actor_ids[1:]):
            offset = n*2*STRIDE
            debug.write_memory(0x80130DB8, struct.pack('>H',actor))
            debug.write_memory(0x80137000, npc_data[(n+1)*56:(n+2)*56])
            debug.write_memory(0x80137348, struct.pack('>H',actor))
            debug.write_memory(output, bytes(512))
            call(0x80085490, [output, 398, 0x4000, 0])
            check('native main-layer selection', output, tail[offset:offset+2])
            call(0x80085A84, [output, pointers, 0x4000, NATIVE_START])
            check('complete secondary layer including donor music', output,
                  tail[offset+STRIDE+2:offset+STRIDE+514])
            call(0x80085178, [output, fg+offset+2])
            check('complete main-layer transfer retains furniture IDs and rotations', output,
                  tail[offset+2:offset+514])
    finally:
        for address, previous in saved.items():
            debug.write_memory(address, previous)
    check('appended foreground remains intact', fg, tail)
    check('resident prefix remains intact', BLOB_RAM, blob)
    for address in guards:
        check('fixture guard', address, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_house_records': animal_count, 'native_layer_pointers': TARGET_COUNT,
            'foreground_records_loaded': count, 'complete_scene_foreground_allocation_tested': False,
            'native_imported_layer_transfers': count, 'house_visit_tested': False,
            'saved_data_written': False, 'requires_checkpoint_restore': True}
