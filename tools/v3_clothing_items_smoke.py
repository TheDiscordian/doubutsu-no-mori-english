"""Current installed garment item readers; no acquisition or FlashRAM writes."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_save_clothing import RAM, VROM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing'].get('item_readers'):
        raise ValueError('Clothing item probe requires its exact current cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)
    text, place = MODULE_RAM+0x6501, MODULE_RAM+0x6580
    edge = b'V3CI'*4
    guards = (text-17, text+16, place-16, place+48,
              TEST_STACK-0x800, TEST_STACK+0x40)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_item_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Clothing item mismatch: '+label)

    def call(address, args, expected):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480)
        record(result)
        if result['return_value'] != expected:
            raise ValueError(f'Clothing item entry {address:08X}: '
                             f'{result["return_value"]} != {expected}')

    check('complete current prefix', BLOB_RAM, blob[:0xC000])
    check('complete separate code loaded', RAM, blob[VROM-BLOB:])
    for address in guards: debug.write_memory(address, edge)
    debug.write_memory(text-1, b'\xA5'*17)
    name = b'cherry shirt'.ljust(16, b' ')
    call(0x801969C8, [text, 16, 0x34BF], 1)
    check('complete unaligned English garment name', text, name)
    call(0x800A5630, [0x34BF], 12)
    call(0x800C0194, [0x34BF], 380)
    call(0x800BE69C, [0x34BF], 0)
    call(0x800BE72C, [0x34BF, 0xFFFFFFFC, 7, place], 3)
    check('garment retains furniture-only footprint rejection', place, bytes(48))
    for capacity, item in ((15, 0x34BF), (16, 0x134BF), (16, 0x34BC)):
        call(0x801969C8, [text, capacity, item], 0)
        check('invalid name request leaves destination intact', text, name)
    profile_address = BLOB_RAM+0xD7
    selected = debug.read_memory(profile_address, 1)
    if not selected[0] & 0x80: raise ValueError('Current shirt is not selected')
    try:
        debug.write_memory(profile_address, bytes([selected[0] & 0x7F]))
        for item in (0x34BF, 0x34BC):
            call(0x801969C8, [text, 16, item], 0)
            check('missing profile keeps name intact', text, name)
            call(0x800A5630, [item], 0)
            call(0x800C0194, [item], 0)
            call(0x800BE72C, [item, 0xFFFFFFFC, 7, place], 3)
            check('missing garment rejects and clears footprint', place, bytes(48))
    finally:
        debug.write_memory(profile_address, selected)
    # The changed shared functions must still retain both furniture pilots.
    for row in report['furniture_items']['imports']:
        item = int(row['item_id'], 16) | 3
        call(0x801969C8, [text, 16, item], 1)
        check('rotated furniture full name retained', text, row['name'].encode().ljust(16, b' '))
        call(0x800A5630, [item], 10)
        call(0x800C0194, [item], row['price'])
    names = files[0x02A00000].extract(rom)
    original_name = names[32+327*16:32+328*16]
    call(0x801969C8, [text, 16, 0x24BF], 1)
    check('original garment retains its different native name', text, original_name)
    call(0x800A5630, [0x24BF], 12)
    call(0x800BE72C, [0x24BF, 0xFFFFFFFC, 7, place], 3)
    check('original garment rejects furniture-only footprint', place, bytes(48))
    for address in guards: check('fixture guard', address, edge)
    check('unaligned name leading byte retained', text-1, b'\xA5')
    check('complete current prefix restored', BLOB_RAM, blob[:0xC000])
    check('complete separate code retained', RAM, blob[VROM-BLOB:])
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'native_garment_name_category_price_footprint': True,
            'selected_profile_rejection': True, 'original_and_furniture_retained': True,
            'ordinary_inventory_or_save_tested': False, 'requires_checkpoint_restore': True}
