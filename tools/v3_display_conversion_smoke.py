"""Actual current native conversion entries, profile rejection, and retained code."""
import json
from pathlib import Path

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_save_clothing import RAM, VROM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing']['display'].get('conversion'):
        raise ValueError('Conversion check requires the exact current cartridge')
    blob = by_vrom(rom)[BLOB].extract(rom)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'display_conversion_check': label, 'address': f'{address:08X}',
                'bytes': len(expected), 'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Conversion check failed: '+label)

    def call(address, item, expected):
        result = debug.call(f'{address:08X}', [item], return_address=MODULE_RAM+0x6480)
        record(result)
        if result['return_value'] != expected:
            raise ValueError(f'Conversion {address:08X} item {item:08X}: '
                             f'{result["return_value"]} != {expected}')

    check('complete current resident code', BLOB_RAM, blob[:0xC000])
    check('complete current secondary code', RAM, blob[VROM-BLOB:])
    edge = b'V3DC'*4
    for address in (TEST_STACK-0x800, TEST_STACK+0x40): debug.write_memory(address, edge)
    call(0x800BEFCC, 0x34BF, 0x3AFC)
    call(0x800BEFCC, 0xABCD34BF, 0x3AFC)
    for rotation in range(4):
        call(0x800BF10C, 0x3AFC | rotation, 0x34BF)
        call(0x800BF10C, 0xABCD3AFC | rotation, 0x34BF)
    # Actual original functions retain every conversion group and its bounds.
    for item, expected in ((0x2400, 0x17AC), (0x24BF, 0x1AA8), (0x24FE, 0x1BA4),
                           (0x24FF, 0x1BA8), (0x2500, 0x2500), (0x2D00, 0x1BA8),
                           (0x2D20, 0x1C28), (0x2300, 0x1C28), (0x2320, 0x1CA8),
                           (0x2204, 0x1CA8), (0x2223, 0x1D24), (0x2224, 0x2224),
                           (0x3224, 0x3224), (0x32BB, 0x32BB), (0, 0), (0xFFFF, 0xFFFF)):
        call(0x800BEFCC, item, expected)
    for item, expected in ((0x17AB, 0x17AB), (0x17AC, 0x2400), (0x1BAB, 0x2D00),
                           (0x1BA7, 0x24FE), (0x1C27, 0x2D1F), (0x1C28, 0x2300),
                           (0x1CA7, 0x231F), (0x1CA8, 0x2204), (0x1D27, 0x2223),
                           (0x1D28, 0x1D28), (0x3227, 0x3227), (0x32B8, 0x32B8),
                           (0x34BF, 0x34BF), (0x3AFB, 0x3AFB), (0x3B00, 0x3B00)):
        call(0x800BF10C, item, expected)
    for address in (BLOB_RAM+0x20+119, BLOB_RAM+0x20+183):
        selected = debug.read_memory(address, 1)
        try:
            debug.write_memory(address, bytes([selected[0] & 0x7F]))
            call(0x800BEFCC, 0x34BF, 0x34BF)
            for rotation in range(4): call(0x800BF10C, 0x3AFC | rotation, 0x3AFC | rotation)
        finally:
            debug.write_memory(address, selected)
    for address in (TEST_STACK-0x800, TEST_STACK+0x40): check('stack guard', address, edge)
    check('complete resident restored', BLOB_RAM, blob[:0xC000])
    check('complete secondary code retained', RAM, blob[VROM-BLOB:])
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'native_global_conversions': True, 'all_four_display_rotations': True,
            'native_fallbacks_and_missing_dependencies': True,
            'ordinary_placement_pickup_tested': False, 'requires_checkpoint_restore': True}
