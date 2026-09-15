"""Bounded current B/C goods selection and actual pocket/ownership insertion."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION
from v3_shops import DESCRIPTOR


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    image = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_text())
    if sha256(image) != report['output_sha256'] or report['runtime_abi'] != 62:
        raise ValueError('Construction stock probe requires the current catalogue build')
    code = by_vrom(image)[CODE_VROM].extract(image)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'construction_stock_check': label, 'address': f'{address:08X}',
                'bytes': len(expected), 'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Construction stock mismatch: ' + label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Construction stock return {address:08X} differs: {result["return_value"]} != {expected}')
        return result['return_value']

    def put(address, value): debug.write_memory(address, struct.pack('>I', value))

    allocation = call(0x8009BFC0, [0x100])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation < 0x803FFF00:
        raise ValueError('Construction stock fixture allocation failed')
    result_at, player, state = allocation + 16, 0x80126EC0, 0x8046C000
    saved = {at: debug.read_memory(at, size) for at, size in (
        (player, 0xBD0), (state, 864), (0x80136FD8, 4), (0x80135B1C, 1),
        (0x80135C00, 2), (0x8003C590, 4), (0x801458B8, 4))}
    edge = b'V3ST' * 4
    for at in (allocation, result_at + 16, allocation + 0xF0): debug.write_memory(at, edge)
    try:
        check('actual revised goods descriptor', DESCRIPTOR, code[DESCRIPTOR - CODE_RAM:DESCRIPTOR - CODE_RAM + 12])
        debug.write_memory(0x80135B1C, bytes([0x18]))  # Native A/B/C priorities 0/1/2.
        debug.write_memory(0x80135C00, bytes(2))
        put(0x80136FD8, player)
        debug.write_memory(player + 0x14, bytes(0x24))
        debug.write_memory(state + 208, bytes(640))
        next_random = 0xFF800000
        seed = ((next_random - 0x3C6EF35F) * pow(0x19660D, -1, 1 << 32)) & 0xFFFFFFFF
        for slot, (item, group) in enumerate(((0x3218, 1), (0x322C, 2))):
            for rarity in range(3): call(0x800C0490, [item, 0, rarity, 0], int(rarity == group))
            put(0x8003C590, seed)
            call(0x800BFCF0, [0, result_at, 1, 0, 0, 0, group])
            check('native stock chooses construction item', result_at, struct.pack('>H', item))
            check('native random selection advances once', 0x8003C590, struct.pack('>I', next_random))
            call(0x800B8B8C, [player, item, 0], 1)
            check('actual pocket acquisition retains complete item ID', player + 0x14 + slot * 2, struct.pack('>H', item))
        ownership = bytearray(128)
        for item in (0x3218, 0x322C):
            bit = (item - 0x3000) // 4
            ownership[bit // 8] |= 1 << (bit & 7)
        check('both new stock items enter the saved ownership catalogue', state + 208, ownership)
        for at in (allocation, result_at + 16, allocation + 0xF0): check('fixture guard', at, edge)
        check('no fault', 0x8003CE34, bytes(4))
    finally:
        for at, data in saved.items(): debug.write_memory(at, data)
    check('complete private record restored', player, saved[player])
    check('complete saved import state restored', state, saved[state])
    call(0x8009C040, [allocation])
    return {'construction_stock_groups': ['B', 'C'], 'native_pocket_acquisition': ['3218', '322C'],
            'ordinary_shop_payment_tested': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
