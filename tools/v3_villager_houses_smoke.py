"""Native house-table initialization and foreground sorting/selection, not move-in."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
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
            raise ValueError('Native house check failed: ' + label)

    def call(address, args):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proofs.get(address))
        record(result)
        return result['return_value']

    check('complete unchanged resident prefix', BLOB_RAM, blob)
    # Probe the appended records only. A full foreground fixture duplicates the
    # scene's large allocation while the title scene still owns its heap.
    size = 0x3000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('House fixture allocation failed')
    fg, pointers, animals, npc, output = (allocation + value for value in
                                         (16, 0x500, 0x1000, 0x1C00, 0x1E00))
    data, table = (files[v].extract(rom) for v in (FOREGROUND, HOUSE))
    if (sha256(data), sha256(table)) != (houses['output_fg_sha256'], houses['output_house_sha256']):
        raise ValueError('Changed installed house data')
    tail_offset = (houses['foreground_records'] - 2) * STRIDE
    tail = data[tail_offset:]
    if len(tail) != STRIDE * 2 + 4 or tail[-4:] != bytes(4):
        raise ValueError('House probe expects precisely two appended layers and alignment padding')
    edge = b'V3HS' * 4
    guards = (allocation, fg + len(tail), pointers - 16, pointers + TARGET_COUNT * 4,
              animals - 16, animals + 2 * 0x528, npc - 16, npc + 2 * 56,
              output - 16, output + 0x200, allocation + size - 16,
              TEST_STACK - 0x800, TEST_STACK + 0x40)
    for address in guards:
        debug.write_memory(address, edge)
    call(0x80026B44, [fg, FOREGROUND + tail_offset, len(tail)])
    check('complete appended foreground DMA', fg, tail)
    debug.write_memory(pointers, b'\xA5' * (TARGET_COUNT * 4))
    call(0x80084FAC, [pointers, fg, TARGET_COUNT, 2, NATIVE_START])
    expected = bytearray(TARGET_COUNT * 4)
    for at in range(0, 2 * STRIDE, STRIDE):
        number = struct.unpack_from('>H', tail, at)[0]
        struct.pack_into('>I', expected, (number - NATIVE_START) * 4, fg + at)
    check('imported layer pointers and every empty subset slot', pointers, expected)
    animal_data = bytearray(b'\xA5' * (2 * 0x528))
    npc_data = bytearray(b'\xA5' * (2 * 56))
    for i, actor in enumerate((0xE000, 0xE0EA)):
        at = i * 0x528
        struct.pack_into('>H', animal_data, at, actor)
        animal_data[at + 0x4E1:at + 0x4E5] = bytes((3, 4, 5, 6))
        at = i * 56
        struct.pack_into('>H', npc_data, at, actor)
        for position in (4, 16):
            struct.pack_into('>3f', npc_data, at + position, 2140.0, 0.0, 2820.0)
        npc_data[at + 28] = 1
        npc_data[at + 44:at + 52] = table[(actor & 0xFFF) * 8:(actor & 0xFFF) * 8 + 8]
        struct.pack_into('>H', npc_data, at + 52, 0)
    debug.write_memory(animals, animal_data)
    debug.write_memory(npc, b'\xA5' * (2 * 56))
    call(0x800AB134, [npc, animals, 2, 1])
    check('complete native and Cheri NPC-list initialization', npc, npc_data)
    check('source animal records remain intact', animals, animal_data)
    saved = {address: debug.read_memory(address, length) for address, length in
             ((0x80130DB8, 2), (0x80137000, 56), (0x80137348, 2))}
    try:
        debug.write_memory(0x80130DB8, bytes.fromhex('E0EA'))
        debug.write_memory(0x80137000, npc_data[56:])
        debug.write_memory(0x80137348, bytes.fromhex('E0EA'))
        debug.write_memory(output, bytes(512))
        call(0x80085490, [output, 398, 0x4000, 0])
        check('native main-layer selection', output, struct.pack('>H', 888))
        call(0x80085A84, [output, pointers, 0x4000, NATIVE_START])
        check('complete secondary layer including K.K. Samba', output, tail[STRIDE + 2:STRIDE + 514])
        call(0x80085178, [output, fg + 2])
        check('complete main-layer transfer retains furniture IDs and rotations', output,
              tail[2:514])
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
    return {'native_house_records': 2, 'native_layer_pointers': TARGET_COUNT,
            'foreground_records_loaded': 2, 'complete_scene_foreground_allocation_tested': False,
            'native_imported_layer_transfers': 2, 'house_visit_tested': False,
            'saved_data_written': False, 'requires_checkpoint_restore': True}
