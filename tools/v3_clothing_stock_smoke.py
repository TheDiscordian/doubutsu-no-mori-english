"""Run complete native clothing stock selection and acquisition on a disposable town."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_clothing_stock import DESCRIPTOR, OWNERS, VROM
from v3_save_clothing import PROFILE, RUNTIME_BYTES


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing'].get('stock'):
        raise ValueError('Clothing stock probe requires its exact installed cartridge')
    files = by_vrom(rom)
    blob, code, goods = (files[v].extract(rom) for v in (BLOB, CODE_VROM, VROM))
    player, pointer, runtime = 0x80126EC0, 0x80136FD8, 0x8046C000
    selected, priority, month, seed_at = BLOB_RAM+0xD7, 0x80135B1E, 0x80136FC1, 0x8003C590
    calls = 0

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_stock_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Clothing stock mismatch: '+label)

    def call(address, args, expected=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480)
        record(result); calls += 1
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Unexpected clothing stock call result at {address:08X}')
        return result['return_value']

    def put(address, value): debug.write_memory(address, struct.pack('>I', value))

    check('complete current prefix', BLOB_RAM, blob[:0xC000])
    for start, end, _ in OWNERS:
        check('complete installed stock owner', start, code[start-CODE_RAM:end-CODE_RAM])
    check('expanded descriptor', DESCRIPTOR, struct.pack('>3I', VROM, VROM+720, 0x60001F0))
    saved = {at: debug.read_memory(at, size) for at, size in
             ((player, 0xBD0), (pointer, 4), (runtime, RUNTIME_BYTES), (selected, 1),
              (priority, 1), (month, 1), (seed_at, 4), (0x800419F0, 4),
              (0x801458B8, 4), (0x80135C00, 2))}
    if not saved[selected][0] & 0x80: raise ValueError('Stock probe needs selected cherry shirt')
    allocation = call(0x8009BFC0, [64])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x803FFFC0:
        raise ValueError('Clothing stock fixture allocation failed')
    result_at, edge = allocation+16, b'V3CS'*4
    guards = (allocation, allocation+32, allocation+48, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    # Month, A/B/C group, selected profile, ordinal among eligible rows, reversed rarity.
    cases = ((9, 0, True, 32, False), (1, 0, True, 32, False),
             (9, 0, True, 33, False), (7, 1, True, 32, False),
             (12, 2, True, 40, False), (9, 0, False, 40, False),
             (7, 0, True, 32, True))
    counts = (32, 10, 11, 9, 9)
    seasons = (0, 4, 4, 1, 1, 1, 2, 2, 2, 3, 3, 3, 4)
    try:
        debug.write_memory(0x80135C00, bytes(2))
        for m, group, enabled, ordinal, reverse in cases:
            priorities = (2, 1, 0) if reverse else (0, 1, 2)
            encoded = priorities[0] << 6 | priorities[1] << 4 | priorities[2] << 2
            debug.write_memory(priority, bytes([encoded]))
            debug.write_memory(month, bytes([m]))
            debug.write_memory(selected, saved[selected] if enabled else bytes([saved[selected][0] & 0x7F]))
            season = seasons[m]
            any_count = 32+int(group == 0 and enabled)
            count = any_count+counts[season]
            next_random = int((ordinal+0.25)/count*(1 << 32))
            seed = ((next_random-0x3C6EF35F)*pow(0x19660D, -1, 1 << 32)) & 0xFFFFFFFF
            put(seed_at, seed)
            index = ordinal+(sum(counts[1:season]) if ordinal >= any_count else 0)
            if group == 0 and not enabled and index >= 32: index += 1
            offset = (0x230, 0x90, 0x120)[group]+index*2
            expected = goods[offset:offset+2]
            record({'stock_case': {'month': m, 'group': group, 'enabled': enabled,
                    'rarity': priorities[group], 'eligible_ordinal': ordinal,
                    'expected_item': expected.hex().upper()}})
            call(0x800BFCF0, [0, result_at, 1, 0, 0, 2, priorities[group]])
            check('native stock choice', result_at, expected)
            check('exactly one native RNG draw', seed_at, struct.pack('>I', next_random))
        for priorities in ((0, 1, 2), (2, 1, 0)):
            debug.write_memory(priority, bytes([priorities[0] << 6 | priorities[1] << 4 | priorities[2] << 2]))
            for rarity in range(3):
                call(0x800C0490, [0x34BF, 2, rarity, 0], int(rarity == priorities[0]))
        # Acquire the actual last native stock result, not a substituted item.
        item = int.from_bytes(debug.read_memory(result_at, 2), 'big')
        if item != 0x34BF: raise ValueError('Last stock choice is not cherry shirt')
        put(pointer, player)
        debug.write_memory(player+0x14, bytes(0x24))
        debug.write_memory(runtime+16+PROFILE, bytes(640))
        call(0x800B8B8C, [player, item, 0], 1)
        check('full acquired stock identity', player+0x14, bytes.fromhex('34BF'))
        expected_owned = bytearray(640); expected_owned[512+23] = 0x80
        check('independent imported ownership', runtime+16+PROFILE, bytes(expected_owned))
        for at in guards: check('fixture guard', at, edge)
        check('save guard', 0x8046C350, bytes.fromhex('AF53C0DE')*4)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        for at, data in saved.items(): debug.write_memory(at, data)
    check('complete prefix restored', BLOB_RAM, blob[:0xC000])
    check('private record restored', player, saved[player])
    check('runtime restored', runtime, saved[runtime])
    call(0x8009C040, [allocation])
    return {'native_calls': calls, 'native_stock_cases': len(cases), 'rarity_membership_cases': 6,
            'native_stock_acquisition': True, 'ordinary_shop_purchase_tested': False,
            'device_io_performed': False, 'requires_checkpoint_restore': True}
