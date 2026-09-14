"""Populate the storage fixture through actual native acquisition/clear calls."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom
from flash_mail import SAVE_RAM, SAVE_BYTES
from runtime_layout import MODULE_RAM, RESERVATION
from v3_collection import ENTRIES
from v3_save_runtime import STATE_RAM


def prepare(debug, rom, report, call, check, record):
    if not report.get('collection'):
        raise ValueError('Collection fixture needs the installed collection cartridge')
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    for address, size, *_ in ENTRIES:
        check('complete installed collection owner', address, code[address - CODE_RAM:address - CODE_RAM + size])
    check('empty imported catalogue before acquisition', STATE_RAM + 16 + 160, bytes(512))
    pointer_at, players = 0x80136FD8, SAVE_RAM + 0x20
    old_pointer = debug.read_memory(pointer_at, 4)
    expected_state = bytearray.fromhex(report['save_runtime']['profile_hex']) + bytearray(512)
    fixture = bytearray(debug.read_memory(SAVE_RAM, SAVE_BYTES))
    fixture[0x2F68:0x2F6A] = bytes.fromhex('3012')
    for player in range(4):
        at = 0x20 + player * 0xBD0
        fixture[at + 0x14:at + 0x38] = bytes(0x24)
    debug.write_memory(SAVE_RAM, bytes(fixture))
    allocation = call(0x8009BFC0, [0xC00])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - 0xC00:
        raise ValueError('Collection fixture allocation failed')
    target = report['collection']['code']['symbols']['af_v3_catalogue_owned']
    bridge = struct.pack('>4I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0)
    debug.write_memory(allocation, bridge)
    call(0x8002FE00, [allocation, 16])
    call(0x80034CE0, [allocation, 16])
    temporary = allocation + 16
    debug.write_memory(temporary + 0xBD0, b'V3CL' * 4)

    def owned(player, item, expected):
        result = debug.call(f'{allocation:08X}', [players + player * 0xBD0, item],
            return_address=MODULE_RAM + 0x6480, verified_code=(allocation, bridge))
        record(result)
        if result['return_value'] != expected:
            raise ValueError('Actual collected-item ownership query differs')

    def select(player):
        debug.write_memory(pointer_at, struct.pack('>I', players + player * 0xBD0))

    def expect(player, item):
        group = (item & 0xFFF) >> 2
        expected_state[160 + player * 128 + (group >> 3)] |= 1 << (group & 7)
        check('complete four-player collected state', STATE_RAM + 16, bytes(expected_state))

    try:
        select(0)
        call(0x800B8B8C, [players, 0x3225, 0], 1)
        expect(0, 0x3225)
        owned(0, 0x3227, 1)
        check('native free-pocket acquisition', players + 0x14, bytes.fromhex('3225'))
        original_catalogue = bytearray(debug.read_memory(players + 0xAF0, 120))
        struct.pack_into('>I', original_catalogue, 0, struct.unpack_from('>I', original_catalogue)[0] | 2)
        call(0x800B88EC, [0x1004])
        check('original furniture collection retained', players + 0xAF0, bytes(original_catalogue))
        check('original item does not enter imported catalogue', STATE_RAM + 16, bytes(expected_state))
        select(1)
        call(0x800B8B8C, [players + 0xBD0, 0x32BB, 1], 1)
        owned(1, 0x32B8, 0)
        check('wrapped present is not yet collected', STATE_RAM + 16, bytes(expected_state))
        call(0x800B8B08, [players + 0xBD0, 0, 0x32BB, 0])
        expect(1, 0x32BB)
        owned(1, 0x32B9, 1)
        select(2)
        call(0x800B8B8C, [players + 2 * 0xBD0, 0x3224, 2], 1)
        owned(2, 0x3224, 0)
        check('quest item is not collected', STATE_RAM + 16, bytes(expected_state))
        select(3)
        call(0x800B8B8C, [players + 3 * 0xBD0, 0x32B8, 0], 1)
        expect(3, 0x32B8)
        call(0x800B7ADC, [temporary])
        check('clearing temporary private data retains resident catalogues', STATE_RAM + 16, bytes(expected_state))
        check('temporary private clear stays within allocation', temporary + 0xBD0, b'V3CL' * 4)
        call(0x800B7ADC, [players + 3 * 0xBD0])
        expected_state[160 + 384:] = bytes(128)
        check('clearing a player clears only that imported catalogue', STATE_RAM + 16, bytes(expected_state))
        owned(3, 0x32B8, 0)
        check('native clear also clears the original pockets', players + 3 * 0xBD0 + 0x14, bytes(30))
        call(0x800B8B8C, [players + 3 * 0xBD0, 0x3224, 0], 1)
        expect(3, 0x3224)
        owned(3, 0x3226, 1)
    finally:
        debug.write_memory(pointer_at, old_pointer)
    call(0x8009C040, [allocation])
    record({'native_acquisition_and_collection': 'passed', 'players_checked': 4,
            'wrapped_and_quest_conditions_retained': True, 'temporary_and_resident_clear_checked': True,
            'ordinary_shop_or_reward_route_tested': False})
    return bytearray(debug.read_memory(SAVE_RAM, SAVE_BYTES)), expected_state
