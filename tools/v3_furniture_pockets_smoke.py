"""Complete current native furniture pocket searches using isolated private data."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_pockets import BLOB_SIZE, ENTRIES


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('furniture_pockets'):
        raise ValueError('Pocket probe requires its exact current cartridge')
    files = by_vrom(rom)
    code, blob = files[CODE_VROM].extract(rom), files[BLOB].extract(rom)[:BLOB_SIZE]
    proofs = {a: (a, code[a - CODE_RAM:a - CODE_RAM + n]) for a, n, _, _ in ENTRIES}
    edge = b'V3PK' * 4

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'pocket_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Pocket native check failed: ' + label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proofs.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected & 0xFFFFFFFF:
            raise ValueError('Pocket native call returned an unexpected value')
        return result['return_value']

    check('complete current resident prefix', BLOB_RAM, blob)
    allocation = call(0x8009BFC0, [0x100])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - 0x100:
        raise ValueError('Pocket fixture allocation failed')
    private = allocation + 16
    data = bytearray(0x38)
    for slot, item in ((0, 0x3000), (1, 0x1004), (2, 0x3225), (3, 0x2400), (7, 0x32BB), (14, 0x32B8)):
        struct.pack_into('>H', data, 0x14 + slot * 2, item)
    struct.pack_into('>I', data, 0x34, 1 << 2 | 2 << 28)
    debug.write_memory(private, bytes(data))
    guards = (allocation, private + 0x38, allocation + 0xF0, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    for kind, condition, index, count in ((1, 0, 2, 2), (1, 1, 1, 1), (1, 2, 14, 1),
            (1, 3, -1, 0), (1, 4, -1, 0), (0x10001, 0, 2, 2),
            (0, 0, 4, 9), (2, 0, 3, 1), (3, 0, 0, 3), (0xFFFF, 0, -1, 0)):
        call(0x800B8128, [private, kind, condition], index)
        call(0x800B8544, [private, kind, condition], count)
    debug.write_memory(BLOB_RAM + 0x7254, bytes(4))
    try:
        for condition, index, count in ((0, 2, 1), (2, -1, 0)):
            call(0x800B8128, [private, 1, condition], index)
            call(0x800B8544, [private, 1, condition], count)
    finally:
        debug.write_memory(BLOB_RAM + 0x7254, struct.pack('>I', 1))
    for kind in (1, 2):
        call(0x800B8128, [0, kind, 0], -1)
        call(0x800B8544, [0, kind, 0], 0)
    check('complete private data retained', private, bytes(data))
    check('complete resident prefix retained', BLOB_RAM, blob)
    for at in guards:
        check('fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'complete_native_pocket_queries': 28, 'original_type_fallbacks_executed': True,
            'ordinary_inventory_tested': False, 'save_reload_tested': False,
            'requires_checkpoint_restore': True}
