"""Native subset-aware counts, move-in candidates, and initial populations."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_villager_selection import FLAGS, CANDIDATES, SHUFFLE


def permutation(seed, count):
    table = list(range(count))
    def draw():
        nonlocal seed
        seed = (seed*0x19660D+0x3C6EF35F) & 0xFFFFFFFF
        product = (seed >> 9) / 8388608 * count
        return int(struct.unpack('>f', struct.pack('>f', product))[0])
    for _ in range(count):
        a, b = draw(), draw()
        table[a], table[b] = table[b], table[a]
    return table


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('villager_selection'):
        raise ValueError('Selection check needs the current cartridge')
    files = by_vrom(rom)
    prefix = files[BLOB].extract(rom)[:0xC000]
    row = next(r for r in report['villager_text']['imports'] if r['actor_id'] == 'E0EA')
    personality = row['personality']
    native_looks = files[CODE_VROM].extract(rom)[0x8010AF58-CODE_RAM:0x8010AF58-CODE_RAM+216]
    growth = files[0xE0D000].extract(rom)

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'selection_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native selection mismatch: '+label)

    def call(at, args=(), expected=None):
        result = debug.call(f'{at:08X}', list(args), return_address=MODULE_RAM+0x6480)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native selection return')
        return result['return_value']

    check('complete startup prefix', BLOB_RAM, prefix)
    size = 0x6000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Selection fixture allocation failed')
    population = allocation+16
    edge = b'V3SL'*4
    guards = (allocation, population+0x528*15, allocation+size-16, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    live, appeared, flag = 0x80130DB8, 0x8013670C, BLOB_RAM+FLAGS+16
    saved = {at: debug.read_memory(at, length) for at, length in (
        (live, 0x528*15), (appeared, 32), (0x8003C590, 4), (0x800419F0, 4),
        (BLOB_RAM+FLAGS, 20), (BLOB_RAM+CANDIDATES, 32), (BLOB_RAM+SHUFFLE, 238*4))}
    try:
        debug.write_memory(live, bytes(0x528*15))
        debug.write_memory(appeared, bytes(32))
        native_count = native_looks.count(personality)
        call(0x800AA3A4, [personality], native_count)
        debug.write_memory(flag, b'\x01')
        call(0x800AA3A4, [personality], native_count+1)
        history = bytearray(b'\xFF'*32); history[29] &= ~4
        debug.write_memory(appeared, history)
        call(0x800AA3A4, [personality], 1)
        call(0x800AD6D4, [personality], 234)
        check('fixed imported candidate bit', BLOB_RAM+CANDIDATES, bytes(29)+b'\x04\0\0')
        call(0x800AA49C)
        check('unseen eligible import prevents premature reset', appeared, history)
        debug.write_memory(live, bytes.fromhex('E0EA'))
        call(0x800AD6D4, [personality], 0xFFFFFFFF)
        debug.write_memory(appeared, b'\xFF'*32)
        call(0x800AA49C)
        check('history reset retains imported resident bit', appeared, bytes(29)+b'\x04\0\0')
        debug.write_memory(flag, b'\0')
        debug.write_memory(live, bytes(2))
        debug.write_memory(appeared, history)
        call(0x800AD6D4, [personality], 0xFFFFFFFF)
        call(0x800AA3A4, [6], 0)

        def expected_population(table, enabled):
            result, used = [], set()
            for position in table:
                npc = 234 if enabled and position == 216 else position
                if npc < 216 and growth[npc]: continue
                looks = personality if npc == 234 else native_looks[npc]
                if looks not in used:
                    result.append(npc); used.add(looks)
                    if len(result) == 6: break
            return result

        selected_seed = next(seed for seed in range(1, 1001)
                             if 234 in expected_population(permutation(seed, 217), True))
        for enabled, seed in ((False, 1), (True, selected_seed)):
            debug.write_memory(flag, bytes((enabled,)))
            debug.write_memory(0x8003C590, struct.pack('>I', seed))
            debug.write_memory(appeared, bytes(32))
            debug.write_memory(population, bytes(0x528*15))
            count = 217 if enabled else 216
            expected_table = permutation(seed, count)
            wanted = expected_population(expected_table, enabled)
            call(0x800AA51C, [population, 6, int(enabled)])
            check('native random permutation retained', BLOB_RAM+SHUFFLE,
                  struct.pack('>'+str(count)+'I', *expected_table))
            actual = debug.read_memory(population, 0x528*15)
            observed = [struct.unpack_from('>H', actual, i*0x528)[0] for i in range(6)]
            expected_ids = [0xE000+n for n in wanted]
            record({'initial_population': [f'{n:04X}' for n in observed],
                    'expected': [f'{n:04X}' for n in expected_ids], 'seed': seed,
                    'import_test_flag': enabled, 'assertion': 'passed' if observed == expected_ids else 'failed'})
            if observed != expected_ids or {actual[i*0x528+11] for i in range(6)} != set(range(6)):
                raise ValueError('Initial population differs from native shuffle/selection rules')
            check('unused population slots remain intact', population+6*0x528, bytes(9*0x528))
    finally:
        for at, previous in saved.items(): debug.write_memory(at, previous)
    for at in guards: check('fixture guard', at, edge)
    check('complete prefix after temporary-state restoration', BLOB_RAM, prefix)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_selection_entries': 4, 'native_initial_populations': 2,
            'ordinary_imported_move_in_tested': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
