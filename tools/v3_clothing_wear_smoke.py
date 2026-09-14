"""Execute the current player index window without another full player allocation."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_clothing_wear import START, END, SPEC, OWNER_POINTER
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing'].get('wearing'):
        raise ValueError('Player clothing index probe requires its exact current cartridge')
    files, proofs = by_vrom(rom), boot_proofs(rom)
    blob, player = files[BLOB].extract(rom)[:0xC000], files[SPEC.vrom].extract(rom)
    wear = report['clothing']['wearing']
    if sha256(player) != wear['output_sha256']: raise ValueError('Changed installed player owner')
    window = player[START-SPEC.ram:END-SPEC.ram]
    edge = b'V3CW'*4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_wear_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected: raise ValueError('Clothing wearing mismatch: '+label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proofs.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected current item-type result')
        return result['return_value']

    check('complete current prefix', BLOB_RAM, blob)
    allocation = call(0x8009BFC0, [192])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-192:
        raise ValueError('Player index window allocation failed')
    start, end, bridge = allocation+16, allocation+16+len(window), allocation+96
    # Only this fixed instruction window is copied, not a complete relocated
    # player overlay. Its bytes contain no native relocation records.
    debug.write_memory(start, window)
    wrapper = struct.pack('>4I', 0x0811A000, 0, 0, 0)  # Stable shared value entry.
    debug.write_memory(bridge, wrapper)
    call(0x8002FE00, [allocation, 192])
    call(0x80034CE0, [allocation, 192])
    proofs[bridge] = (bridge, wrapper)
    guards = (allocation, allocation+64, allocation+176, TEST_STACK-0x800, TEST_STACK+0x40)
    for address in guards: debug.write_memory(address, edge)
    saved_pointer = debug.read_memory(OWNER_POINTER, 4)
    saved_selection = debug.read_memory(BLOB_RAM+0xD7, 1)
    before = debug.command('g')
    original = [int(before[i:i+16], 16) for i in range(0, len(before), 16)]
    if len(original) != 71 or original[37] & 0xFFFFFFFF != 0x800D334C:
        raise ValueError('Player window requires a paused game frame')
    try:
        debug.write_memory(OWNER_POINTER, struct.pack('>I', start-(START-SPEC.ram)))
        for item, disabled, expected in ((0x24BF, False, 0xBF), (0x34BF, False, 0x10BF),
                                         (0x34BF, True, 0), (0x34BC, False, 0),
                                         (0x23FF, False, 0), (0x2500, False, 0)):
            debug.write_memory(BLOB_RAM+0xD7, bytes([saved_selection[0] & 0x7F]) if disabled else saved_selection)
            regs = original.copy()
            for i in range(1, 32):
                if i not in (26, 27): regs[i] = (0x13579000+i) << 32 | (0x2468A000+i)
            regs[5], regs[7], regs[29], regs[37] = item, 0, extend(TEST_STACK), extend(start)
            wanted = regs.copy(); wanted[1], wanted[2], wanted[7] = int(item < 0x2500), item, expected
            breakpoint = f'0,{end:x},4'
            if debug.command('Z'+breakpoint) != 'OK': raise ValueError('Player continuation breakpoint refused')
            try:
                if debug.command('G'+''.join(f'{value:016x}' for value in regs)) != 'OK':
                    raise ValueError('Player window register write refused')
                stopped = debug.command('c')
                raw = debug.command('g')
                actual = [int(raw[i:i+16], 16) for i in range(0, len(raw), 16)]
                differences = {str(i): [f'{wanted[i]:016X}', f'{actual[i]:016X}']
                    for i in (*range(26), 28, 29, 30, 31, 33, 34, *range(38, 70)) if wanted[i] != actual[i]}
                passed = stopped[:3] in ('T05', 'S05') and actual[37] & 0xFFFFFFFF == end and not differences
                record({'player_index_window': f'{item:04X}', 'disabled': disabled,
                        'expected_index': f'{expected:04X}', 'register_differences': differences,
                        'assertion': 'passed' if passed else 'failed'})
                if not passed: raise ValueError('Player index window changed unrelated registers or index')
            finally:
                debug.command('z'+breakpoint)
                debug.command('G'+before)
        debug.write_memory(BLOB_RAM+0xD7, saved_selection)
        for item, category in ((0x24BF, 2), (0x34BF, 2), (0x3224, 1)):
            call(bridge, [item, 2], category)
    finally:
        debug.write_memory(OWNER_POINTER, saved_pointer)
        debug.write_memory(BLOB_RAM+0xD7, saved_selection)
    for address in guards: check('fixture guard', address, edge)
    check('complete current prefix restored', BLOB_RAM, blob)
    check('exact installed player window retained', start, window)
    check('owner pointer restored', OWNER_POINTER, saved_pointer)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'player_index_register_windows': 6, 'existing_classification_cases': 3,
            'full_player_overlay_or_ordinary_wearing_tested': False,
            'requires_checkpoint_restore': True}
