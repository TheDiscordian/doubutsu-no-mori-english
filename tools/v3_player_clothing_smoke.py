"""Execute player clothing registration and changes using native banks and DMA."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing'].get('player_readers'):
        raise ValueError('Player clothing probe requires the current assembled cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'player_clothing_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Player clothing mismatch: '+label)

    def call(address, args):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480)
        record(result)
        return result['return_value']

    check('complete startup prefix', BLOB_RAM, blob[:0xC000])
    size = 0x3000
    allocation = call(0x8009BFC0, [size])
    if allocation % 16 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Player clothing fixture allocation failed')
    game, player, buffers = allocation+16, allocation+0x1A00, allocation+0x2500
    edge = b'V3PC'*4
    guards = (allocation, game+0x1950, player-16, player+0xA80,
              buffers-16, buffers+0x440, allocation+size-16, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    context = bytearray(0x1950)
    struct.pack_into('>I', context, 0x1910, buffers)
    debug.write_memory(game, context)
    personal = bytearray(0xA80)
    debug.write_memory(player, personal)
    debug.write_memory(buffers, b'\xA5'*0x440)
    saved = {at: debug.read_memory(at, count) for at, count in ((0x80136FD8, 4), (0x8010C0D0, 20))}
    native = files[0xB68000].extract(rom)[0x17E00:0x18000]+files[0xB88000].extract(rom)[0x17E0:0x1800]
    imported = blob[0xF000:0xF220]
    try:
        debug.write_memory(0x80136FD8, struct.pack('>I', player))
        debug.write_memory(0x8010C0D0, struct.pack('>5I', 1, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF))
        for slot, item in enumerate((0x24BF, 0x34BF)):
            struct.pack_into('>HH', personal, 0xA76, item-0x2400, item)
            debug.write_memory(player, personal)
            call(0x800B1960, [game, slot, slot*2])
            call(0x800B19C4, [game, slot, slot*2])
        check('registered double-buffer bank indices', 0x8010C0D0, struct.pack('>5I', 1, 0, 2, 1, 3))
        check('native first and imported second startup garments', buffers, native+imported)
        for index, (bank, pointer, length) in enumerate(((14, buffers, 512), (15, buffers+512, 32),
                (14, buffers+544, 512), (15, buffers+1056, 32))):
            at = 0x110+index*84
            struct.pack_into('>H', context, at, bank)
            struct.pack_into('>II', context, at+4, pointer, pointer)
            struct.pack_into('>I', context, at+16, length)
        struct.pack_into('>I', context, 0x1904, 4)
        struct.pack_into('>I', context, 0x1910, buffers+1088)
        check('complete native bank registration and controller bounds', game, context)
        call(0x800B1BE8, [game, 0x10BF])
        check('change to imported shirt updates inactive first buffer', buffers, imported+imported)
        check('first buffer becomes active', 0x8010C0D0, bytes(4))
        call(0x800B1BE8, [game, 0xBF])
        check('change to native shirt updates inactive second buffer', buffers, imported+native)
        check('second buffer becomes active', 0x8010C0D0, struct.pack('>I', 1))
        call(0x800B1BE8, [game, 0x10C0])
        check('unknown shirt leaves both buffers untouched', buffers, imported+native)
        check('unknown shirt leaves active buffer unchanged', 0x8010C0D0, struct.pack('>I', 1))
        debug.write_memory(0x8010C0D4, bytes.fromhex('FFFFFFFF'))
        call(0x800B1BE8, [game, 0xBF])
        check('missing inactive bank restores previous active buffer', 0x8010C0D0, struct.pack('>I', 1))
        check('missing inactive bank leaves both garments intact', buffers, imported+native)
        check('clothing reads do not modify private fields', player, personal)
        check('clothes changes leave registered native banks unchanged', game, context)
    finally:
        for at, data in saved.items(): debug.write_memory(at, data)
    for at in guards: check('fixture guard', at, edge)
    for at, data in saved.items(): check('native globals restored', at, data)
    check('resident prefix intact', BLOB_RAM, blob[:0xC000])
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_startup_entries': 2, 'native_change_entry': 1,
            'complete_native_imported_startup_and_double_buffering': True,
            'saved_data_written': False, 'ordinary_wearing_gameplay_tested': False,
            'requires_checkpoint_restore': True}
