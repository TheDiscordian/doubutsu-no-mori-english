"""Current native house-gift selector, list storage, and identity-based retrieval."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_villager_houses import FOREGROUND, STRIDE
from v3_villager_rewards import ENTRY


def ordinal(seed, count):
    state = (seed*0x19660D+0x3C6EF35F) & 0xFFFFFFFF
    return int(struct.unpack('>f', struct.pack('>f', (state >> 9)/8388608*count))[0]), state


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('villager_rewards'):
        raise ValueError('Reward check requires its current assembled cartridge')
    files = by_vrom(rom)
    prefix = files[BLOB].extract(rom)[:0xC000]

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'reward_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native reward mismatch: '+label+
                             f'; expected={expected.hex()} observed={actual.hex()}')

    def call(at, args=(), expected=None):
        result = debug.call(f'{at:08X}', list(args), return_address=MODULE_RAM+0x6480)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Native reward return: wanted {expected:08X}, got {result["return_value"]:08X}')
        return result['return_value']

    check('complete startup prefix', BLOB_RAM, prefix)
    size = 0x1000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Reward fixture allocation failed')
    fg, pointers, npc = (allocation+n for n in (16, 0x300, 0xD00))
    live, listing = 0x80130DB8, 0x80137000
    flags = (BLOB_RAM+0x7204, BLOB_RAM+0x7254)
    saved = {at: debug.read_memory(at, count) for at, count in (
        (live, 15*0x528), (listing, 15*56), (0x8003C590, 4), (0x800419F0, 4),
        *((at, 4) for at in flags))}
    guards = (allocation, fg+STRIDE, pointers-16, pointers+498*4,
              npc-16, npc+56, allocation+size-16, TEST_STACK-0x800, TEST_STACK+0x40)
    edge = b'V3RW'*4
    for at in guards: debug.write_memory(at, edge)
    pointer_data = bytearray(498*4)
    struct.pack_into('>I', pointer_data, 490*4, fg)
    debug.write_memory(pointers, pointer_data)
    npc_data = bytearray(56)
    struct.pack_into('>H', npc_data, 0, 0xE0EA)
    struct.pack_into('>HH', npc_data, 0x30, 888, 889)
    debug.write_memory(npc, npc_data)
    try:
        # An empty room must not consume even one native random draw.
        debug.write_memory(fg, bytes(STRIDE))
        debug.write_memory(0x8003C590, struct.pack('>I', 123))
        call(ENTRY, (pointers, npc, 398), 0)
        check('no candidates preserve RNG', 0x8003C590, struct.pack('>I', 123))
        layer = bytearray(STRIDE)
        for cell, item in ((0, 0x3227), (1, 0x32BA), (2, 0x17B0), (3, 0x3352),
                           (10, 0x113F), (160, 0x10B8)):
            struct.pack_into('>H', layer, 2+cell*2, item)
        debug.write_memory(fg, layer)
        for seed in (1, 1000):
            index, state = ordinal(seed, 2)
            debug.write_memory(0x8003C590, struct.pack('>I', seed))
            call(ENTRY, (pointers, npc, 398), (0x3227, 0x32BA)[index])
            check('one native random draw', 0x8003C590, struct.pack('>I', state))
        for at in flags: debug.write_memory(at, bytes(4))
        debug.write_memory(0x8003C590, struct.pack('>I', 123))
        call(ENTRY, (pointers, npc, 398), 0)
        check('disabled imports and excluded native items do not draw', 0x8003C590, struct.pack('>I', 123))
        for at in flags: debug.write_memory(at, saved[at])

        data = files[FOREGROUND].extract(rom)
        offset = (report['villager_houses']['foreground_records']-2)*STRIDE
        cheri = data[offset:offset+STRIDE]
        candidates = []
        for row in range(10):
            for column in range(10):
                item = struct.unpack_from('>H', cheri, 2+(row*16+column)*2)[0]
                if ((item >> 12 == 1 and not 0x15B0 <= item < 0x1D44 and not 0x1E3C <= item < 0x1EA0)
                        or item & 0xFFFC in (0x3224, 0x32B8)):
                    candidates.append(item)
        if not {0x3224, 0x32B8} <= {item & 0xFFFC for item in candidates}:
            raise ValueError('Actual Cheri room lacks its expected imported gift candidates')
        debug.write_memory(fg, cheri)
        animal_data = bytearray(15*0x528)
        struct.pack_into('>H', animal_data, 0, 0xE0EA)
        debug.write_memory(live, animal_data)
        debug.write_memory(listing, npc_data+bytes(14*56))
        for wanted in (0x3224, 0x32B8):
            seed = next(seed for seed in range(10000) if candidates[ordinal(seed, len(candidates))[0]] & 0xFFFC == wanted)
            index, state = ordinal(seed, len(candidates))
            expected = candidates[index]
            debug.write_memory(0x8003C590, struct.pack('>I', seed))
            call(0x800ABA14, (pointers, 398))
            stored = bytearray(npc_data+bytes(14*56))
            struct.pack_into('>H', stored, 0x34, expected)
            check('native list stores the complete imported gift and preserves other slots', listing, stored)
            check('native list consumes one draw for its one resident', 0x8003C590, struct.pack('>I', state))
            call(0x800ABAA8, (live,), expected)
            record({'actual_cheri_gift': f'{expected:04X}', 'candidate_count': len(candidates), 'seed': seed})
        check('actual Cheri room remains intact', fg, cheri)
        check('live identity fixture remains intact', live, animal_data)
        check('pointer table remains intact', pointers, pointer_data)
    finally:
        for at, previous in saved.items(): debug.write_memory(at, previous)
    for at in guards: check('fixture guard', at, edge)
    check('complete resident prefix restored', BLOB_RAM, prefix)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, (allocation,))
    return {'native_reward_entries': 3, 'actual_room_imported_gifts': 2,
            'ordinary_gift_dialogue_tested': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
