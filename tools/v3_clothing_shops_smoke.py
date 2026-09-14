"""Exercise the installed shop category reader without changing town stock."""
import json
from pathlib import Path

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB, BLOB_RAM
from v3_shops import ENTRY


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['shops']['clothing_category_enabled']:
        raise ValueError('Clothing shop check requires its exact installed cartridge')
    blob = by_vrom(rom)[BLOB].extract(rom)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_shop_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Clothing shop mismatch: '+label)

    check('complete current prefix', BLOB_RAM, blob[:0xC000])
    selection = debug.read_memory(BLOB_RAM+0xD7, 1)
    if not selection[0] & 0x80: raise ValueError('Clothing test requires the selected shirt')
    cases = ((0x24BF, False, 2), (0x34BF, False, 2), (0x134BF, False, 2),
             (0x34BF, True, -1), (0x34BC, False, -1), (0x34FF, False, -1),
             (0x3224, False, 0), (0x32BB, False, 0))
    try:
        for item, disabled, expected in cases:
            debug.write_memory(BLOB_RAM+0xD7, bytes([selection[0] & 0x7F]) if disabled else selection)
            result = debug.call(f'{ENTRY:08X}', [item], return_address=MODULE_RAM+0x6480)
            record(result)
            if result['return_value'] & 0xFFFFFFFF != expected & 0xFFFFFFFF:
                raise ValueError(f'Wrong native shop category for {item:05X}')
    finally:
        debug.write_memory(BLOB_RAM+0xD7, selection)
    check('complete prefix restored', BLOB_RAM, blob[:0xC000])
    check('no faulted thread', 0x8003CE34, bytes(4))
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('save guard', 0x8046C350, bytes.fromhex('AF53C0DE')*4)
    return {'native_shop_category_cases': len(cases), 'ordinary_stock_or_purchase_tested': False,
            'requires_checkpoint_restore': True}
