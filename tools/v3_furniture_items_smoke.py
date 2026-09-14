"""Native current-item name/type/price/footprint entries; no inventory/save calls."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['furniture_items']:
        raise ValueError('Furniture item probe requires its exact current cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)[:32768]
    text, place = MODULE_RAM + 0x6501, MODULE_RAM + 0x6580
    edge = b'V3IT' * 4
    guards = (text - 17, text + 16, place - 16, place + 48,
              TEST_STACK - 0x800, TEST_STACK + 0x40)

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'v3_item_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('V3 item check failed: ' + label)

    def call(address, args, expected):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(result)
        if result['return_value'] != expected:
            raise ValueError(f'Furniture item entry {address:08X}: '
                             f'{result["return_value"]} != {expected}')

    check('complete current resident prefix', BLOB_RAM, blob)
    for at in guards:
        debug.write_memory(at, edge)
    debug.write_memory(text - 1, b'\xA5' * 17)
    cells = b''.join(struct.pack('>3i', i == 0, -4, 7) for i in range(4))
    for row in report['furniture_items']['imports']:
        item = int(row['item_id'], 16)
        expected_name = row['name'].encode().ljust(16, b' ')
        for rotation in (0, 3):
            call(0x801969C8, [text, 16, item | rotation], 1)
            check('complete unaligned imported name', text, expected_name)
            call(0x800A5630, [item | rotation], 10)
            call(0x800C0194, [item | rotation], row['price'])
            call(0x800BE69C, [item | rotation], 0)
            call(0x800BE72C, [item | rotation, 0xFFFFFFFC, 7, place], 0)
            check('complete donor 1x1 placement cells', place, cells)
    last_name = expected_name
    for capacity, item in ((15, 0x3224), (16, 0x3000), (16, 0x13224)):
        call(0x801969C8, [text, capacity, item], 0)
        check('invalid name leaves destination intact', text, last_name)
    # A metadata row is insufficient if its furniture profile is disabled.
    debug.write_memory(BLOB_RAM + 0x7204, bytes(4))
    call(0x801969C8, [text, 16, 0x3224], 0)
    check('disabled profile is no-write for names', text, last_name)
    for item in (0x3224, 0x3000):
        call(0x800A5630, [item], 0)
        call(0x800C0194, [item], 0)
        call(0x800BE72C, [item, 0xFFFFFFFC, 7, place], 3)
        check('missing item clears/rejects placement cells', place, bytes(48))
    debug.write_memory(BLOB_RAM + 0x7204, struct.pack('>I', 1))
    # Original full-name DMA, native classification, native footprint reads,
    # and original transient price-resource allocation all remain active.
    names = files[0x02A00000].extract(rom)
    original_name = names[32 + 756 * 16:32 + 757 * 16]
    # Native LUI 011F followed by ADDIU -8000 resolves to 011E8000.
    original_price = struct.unpack_from('>H', files[0x011E8000].extract(rom))[0]
    call(0x801969C8, [text, 16, 0x1000], 1)
    check('original complete sixteen-byte name DMA', text, original_name)
    call(0x800A5630, [0x1000], 10)
    call(0x800C0194, [0x1000], original_price)
    call(0x800BE69C, [0x1000], 0)
    call(0x800BE72C, [0x1000, 0xFFFFFFFC, 7, place], 0)
    check('original complete placement footprint', place, cells)
    for at in guards:
        check('fixture guard', at, edge)
    check('unaligned-name leading byte retained', text - 1, b'\xA5')
    check('complete current resident prefix retained', BLOB_RAM, blob)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'native_imported_metadata_readers': 5, 'native_original_fallbacks': 5,
            'disabled_profile_rejection': True, 'ordinary_inventory_tested': False,
            'placed_actor_tested': False, 'save_reload_tested': False,
            'requires_checkpoint_restore': True}
