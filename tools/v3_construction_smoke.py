"""Current construction readers, moved tables, retained garments, and guards."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB


def exercise(debug, rom_path, record, *, garden=False):
    if garden:
        from v3_garden_runtime import ABI, ITEMS, ITEMS_RAM, ROWS, ROWS_RAM, TABLE_END
        key, count, item_count = 'garden', 15, 16
    else:
        from v3_construction_runtime import ABI, ITEMS, ITEMS_RAM, ROWS, ROWS_RAM, TABLE_END
        key, count, item_count = 'construction', 9, 10
    path = Path(rom_path)
    image = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_text())
    if sha256(image) != report['output_sha256'] or report['runtime_abi'] != ABI:
        raise ValueError('Construction probe needs its exact current cartridge')
    blob = by_vrom(image)[BLOB].extract(image)
    rows = report[key]['imports']
    scratch = MODULE_RAM + 0x6500
    state = debug.read_memory(0x8046C000, 864)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({key + '_reader_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Construction native memory mismatch: ' + label)

    def call(address, args, expected):
        value = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(value)
        if value['return_value'] != expected:
            raise ValueError(f'Construction native return {address:08X}: {value["return_value"]} != {expected}')

    check('startup ready', 0x8019ACD0, struct.pack('>I', 1))
    check(f'{count} complete static profiles', ROWS_RAM, blob[ROWS:ROWS + count * 80])
    check(f'{item_count} complete item records', ITEMS_RAM, blob[ITEMS:TABLE_END])
    for row in rows:
        item = int(row['item_id'], 16)
        call(0x800A5630, [item | 3], 10)
        call(0x800C0194, [item | 1], row['price'])
        debug.write_memory(scratch, b'\xA5' * 64)
        call(0x801969C8, [scratch, 16, item], 1)
        check(row['name'] + ' full English name', scratch,
              row['name'].encode().ljust(16, b' ') + b'\xA5' * 48)
    for row in (rows[1], rows[-1]):
        item = int(row['item_id'], 16)
        debug.write_memory(scratch, b'\xA5' * 64)
        call(0x800BE72C, [item, 1, 2, scratch], 0)
        expected = struct.pack('>12i', 1, 1, 2, 0, 1, 2, 0, 1, 2, 0, 1, 2)
        check(row['name'] + ' complete placement cells', scratch, expected + b'\xA5' * 16)
    # Existing static, animated, and all three garment paths share the changed
    # metadata reader. Verify each category still resolves its original value.
    for item, price in ((0x3224, 830), (0x32B8, 840), (0x3350, 2990)):
        call(0x800A5630, [item], 10)
        call(0x800C0194, [item], price)
    for item in (0x34BF, 0x341A, 0x341B):
        call(0x800A5630, [item], 12)
    row = rows[0]
    enabled = int(row['profile_ram'], 16) - 4
    try:
        debug.write_memory(enabled, bytes(4))
        call(0x800A5630, [int(row['item_id'], 16)], 0)
        call(0x800C0194, [int(row['item_id'], 16)], 0)
    finally:
        debug.write_memory(enabled, struct.pack('>I', 1))
    check('complete static profiles restored', ROWS_RAM, blob[ROWS:ROWS + count * 80])
    check('runtime save state retained', 0x8046C000, state)
    for label, address, value in (('translation', 0x8019C8D0, 'AF32C0DE'),
            ('save', 0x8046C350, 'AF53C0DE'), ('resident', 0x8046BFF0, 'AF33C0DE'),
            ('package', 0x80481FF0, 'AFACC0DE')):
        check(label + ' guard', address, bytes.fromhex(value) * 4)
    check('no fault', 0x8003CE34, bytes(4))
    return {key + '_readers': len(rows), 'retained_static_animated_and_clothing_readers': True,
            'ordinary_acquisition_or_persistence_tested': False, 'requires_checkpoint_restore': True}
