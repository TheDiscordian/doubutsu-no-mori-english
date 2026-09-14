"""Execute the current shared clothing reader with guarded native RAM buffers."""
import json
from pathlib import Path

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_clothing import DATA, ENTRY


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('clothing'):
        raise ValueError('Clothing probe requires its current assembled cartridge')
    files = by_vrom(rom)
    blob_file = files[BLOB].extract(rom)
    prefix = blob_file[:0xC000]

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('Native clothing mismatch: '+label)

    def call(address, args):
        result = debug.call(f'{address:08X}', list(args), return_address=MODULE_RAM+0x6480)
        record(result)
        return result['return_value']

    check('complete startup prefix', BLOB_RAM, prefix)
    size = 0x300
    allocation = call(0x8009BFC0, [size])
    if allocation % 16 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Clothing fixture allocation failed')
    texture, palette = allocation+16, allocation+0x230
    edge = b'V3CL'*4
    guards = (allocation, texture+512, palette-16, palette+32, allocation+size-16,
              TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    enabled = BLOB_RAM+DATA+10
    saved = debug.read_memory(enabled, 1)
    try:
        # Native BF is deliberately a different garment; preserve its exact
        # texture/palette before checking the donor-only 10BF index.
        call(ENTRY, (texture, palette, 0xBF))
        check('original BF texture', texture, files[0xB68000].extract(rom)[0x17E00:0x18000])
        check('original BF palette', palette, files[0xB88000].extract(rom)[0x17E0:0x1800])
        call(ENTRY, (texture, palette, 0x10BF))
        expected_tex, expected_pal = blob_file[0xF000:0xF200], blob_file[0xF200:0xF220]
        check('complete imported cherry-shirt texture', texture, expected_tex)
        check('complete imported cherry-shirt palette', palette, expected_pal)
        call(ENTRY, (0, palette, 0x10BF))
        call(ENTRY, (texture, 0, 0x10BF))
        call(ENTRY, (texture, palette, 0x10C0))
        debug.write_memory(enabled, b'\0')
        call(ENTRY, (texture, palette, 0x10BF))
        check('invalid and disabled calls leave texture intact', texture, expected_tex)
        check('invalid and disabled calls leave palette intact', palette, expected_pal)
    finally:
        debug.write_memory(enabled, saved)
    for at in guards: check('fixture guard', at, edge)
    check('resident prefix restored', BLOB_RAM, prefix)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, (allocation,))
    return {'native_reader_entries': 1, 'native_and_imported_complete_garments': 2,
            'saved_data_written': False, 'npc_or_wearing_gameplay_tested': False,
            'requires_checkpoint_restore': True}
