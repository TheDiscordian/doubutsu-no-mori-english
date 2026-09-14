"""Current native menu decisions with isolated parent/tag/private RAM fixtures."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_menu import BLOB_SIZE, RAM, RELOC, ROOT_VROM, SIZE, VROM
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    menu = report.get('furniture_menu')
    if sha256(rom) != report['output_sha256'] or not menu:
        raise ValueError('Menu probe requires its exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:BLOB_SIZE]
    edge = b'V3MN' * 4

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'menu_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Menu native check failed: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Menu call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']

    def put(at, value):
        debug.write_memory(at, struct.pack('>I', value))

    check('complete current startup prefix', BLOB_RAM, blob)
    size = 0x24000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Menu fixture allocation failed')
    root, tag, overlay = allocation + 16, allocation + 0x3200, allocation + 0x10000
    hand, submenu, private = allocation + 0x20800, allocation + 0x20C00, allocation + 0x20D00
    debug.write_memory(allocation, bytes(size))
    root_data = files[ROOT_VROM].extract(rom)
    if sha256(root_data) != menu['parent_sha256']:
        raise ValueError('Changed menu parent proof')
    debug.write_memory(root, root_data)
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    if sha256(data) != menu['output_sha256'] or sha256(reloc) != menu['relocation_sha256']:
        raise ValueError('Changed tag proof')
    sections = struct.unpack_from('>5I', reloc)
    loaded = relocate_verified_data(SimpleNamespace(ram=RAM, resident_bytes=SIZE, sections=sections),
                                    data, reloc, tag)
    call(0x800262D0, [VROM, VROM + SIZE, RAM, RAM + SIZE, tag, tag + SIZE, len(reloc)])
    check('complete native-relocated current tag', tag, loaded)
    proof = (tag, loaded)

    def native(address, args, expected=None):
        return call(tag + address - RAM, args, expected, proof)

    # Model the documented post-constructor parent state. The production parent
    # loader is not executed by this fixture; that remains ordinary-menu work.
    put(root + 0x2CC0, tag + 0x808787A0 - RAM)
    put(root + 0x2CCC, 1)
    saved = {0x8010DCEC: debug.read_memory(0x8010DCEC, 4),
             0x80136FD8: debug.read_memory(0x80136FD8, 4),
             0x80136EA1: debug.read_memory(0x80136EA1, 1)}
    put(0x8010DCEC, root)
    put(0x80136FD8, private)
    put(submenu + 0x2C, overlay)
    put(overlay + 0x106D4, hand)
    guards = (allocation, tag - 16, overlay - 16, hand - 16, submenu - 16,
              private - 16, allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    before = debug.command('g')
    original_regs = [int(before[i:i + 16], 16) for i in range(0, len(before), 16)]
    if len(original_regs) != 71 or original_regs[37] & 0xFFFFFFFF != 0x800D334C:
        raise ValueError('Menu windows require the paused game frame')
    for row in menu['sites']:
        for item, selected, disabled in ((0x1004, False, False), (0x3225, True, False),
                                         (0x32BB, True, False), (0x32BB, False, True)):
            if disabled:
                put(BLOB_RAM + 0x7254, 0)
            regs = original_regs.copy()
            for i in range(1, 32):
                if i not in (26, 27):
                    regs[i] = (0x13579000 + i) << 32 | (0x2468A000 + i)
            regs[row['source']] = item
            regs[29], regs[37] = extend(TEST_STACK), extend(tag + row['start'] - RAM)
            wanted = regs.copy()
            wanted[row['temporary']] = item & 0xF000
            wanted[row['destination']] = 1 if selected else item >> 12
            target = tag + row['end'] - RAM
            breakpoint = f'0,{target:x},4'
            if debug.command('Z' + breakpoint) != 'OK':
                raise ValueError('Menu breakpoint refused')
            try:
                if debug.command('G' + ''.join(f'{n:016x}' for n in regs)) != 'OK':
                    raise ValueError('Menu register write refused')
                stopped = debug.command('c')
                raw = debug.command('g')
                actual = [int(raw[i:i + 16], 16) for i in range(0, len(raw), 16)]
                differences = {str(i): [f'{wanted[i]:016X}', f'{actual[i]:016X}']
                    for i in (*range(26), 28, 29, 30, 31, 33, 34, *range(38, 70)) if wanted[i] != actual[i]}
                passed = stopped[:3] in ('T05', 'S05') and actual[37] & 0xFFFFFFFF == target and not differences
                record({'menu_window': f'{row["start"]:08X}', 'item': f'{item:04X}',
                        'selected': selected, 'disabled_profile': disabled,
                        'register_differences': differences, 'assertion': 'passed' if passed else 'failed'})
                if not passed:
                    raise ValueError(f'Menu window failed {row["start"]:08X}/{item:04X}: {differences}')
            finally:
                debug.command('z' + breakpoint)
                debug.command('G' + before)
                if disabled:
                    put(BLOB_RAM + 0x7254, 1)
    for item in (0x1004, 0x3225, 0x32BB):
        debug.write_memory(hand + 0x23C, struct.pack('>H', item))
        for destination in range(5):
            native(0x808747D0, [submenu, destination], int(destination < 2))
        check('hand keeps complete item identity', hand + 0x23C, struct.pack('>H', item))
    for field in range(4):
        debug.write_memory(0x80136EA1, bytes((field,)))
        expected_type = native(0x80875610, [submenu, 0x1004, 0])
        for item in (0x3225, 0x32BB):
            native(0x80875610, [submenu, item, 0], expected_type)
        record({'native_menu_field': field, 'original_and_imported_tag_type': expected_type})
    for condition, expected_type in ((1, 11), (2, 8)):
        put(private + 0x34, condition)
        native(0x80875610, [submenu, 0x3225, 0], expected_type)
    check('complete resident prefix unchanged', BLOB_RAM, blob)
    check('complete current tag unchanged by queries', tag, loaded)
    for at in guards:
        check('fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    for at, value in saved.items():
        debug.write_memory(at, value)
    call(0x8009C040, [allocation])
    return {'menu_register_windows': 12, 'complete_native_hand_destination_cases': 15,
            'native_action_menu_contexts': 4, 'wrapped_and_quest_conditions_retained': True,
            'parent_loader_executed': False, 'ordinary_placement_tested': False,
            'save_reload_tested': False, 'requires_checkpoint_restore': True}
