"""Native garment acquisition, conditional collection, and per-player ownership."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
from v3_save_clothing import PROFILE, RAM, RUNTIME_BYTES, VROM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['collection']['clothing_collection_enabled']:
        raise ValueError('Clothing collection probe requires its exact current cartridge')
    blob = by_vrom(rom)[BLOB].extract(rom)
    proofs = boot_proofs(rom)
    players, pointer, runtime_address = 0x80126EC0, 0x80136FD8, 0x8046C000
    original_players = debug.read_memory(players, 4*0xBD0)
    original_pointer = debug.read_memory(pointer, 4)
    runtime = debug.read_memory(runtime_address, RUNTIME_BYTES)
    expected = bytearray.fromhex(report['save_runtime']['profile_hex'])+bytearray(640)
    edge = b'V3CC'*4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_collection_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Clothing collection mismatch: '+label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proofs.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native clothing acquisition/query result')
        return result['return_value']

    check('complete current prefix', BLOB_RAM, blob[:0xC000])
    check('complete separate code', RAM, blob[VROM-BLOB:])
    check('empty initialized extended ownership', runtime_address+16, bytes(expected))
    allocation = call(0x8009BFC0, [64])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-64:
        raise ValueError('Clothing collection fixture allocation failed')
    target = report['collection']['code']['symbols']['af_v3_catalogue_owned']
    bridge = struct.pack('>4I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0)
    debug.write_memory(allocation, bridge)
    call(0x8002FE00, [allocation, 16])
    call(0x80034CE0, [allocation, 16])
    proofs[allocation] = (allocation, bridge)
    guards = (allocation+16, allocation+48, TEST_STACK-0x800, TEST_STACK+0x40)
    for address in guards: debug.write_memory(address, edge)

    def owned(player, item, value):
        call(allocation, [players+player*0xBD0, item], value)

    def mark(player):
        expected[PROFILE+512+player*32+23] = 0x80
        check('complete four-player furniture/clothing state', runtime_address+16, bytes(expected))

    profile_address = BLOB_RAM+0xD7
    selected = debug.read_memory(profile_address, 1)
    try:
        for player in range(4):
            private = players+player*0xBD0
            debug.write_memory(pointer, struct.pack('>I', private))
            debug.write_memory(private+0x14, bytes(0x24))
            condition = player if player in (1, 2) else 0
            call(0x800B8B8C, [private, 0x34BF, condition], 1)
            check('full imported identity in native pocket', private+0x14, bytes.fromhex('34BF'))
            if condition:
                owned(player, 0x34BF, 0)
                check('present/quest condition does not collect', runtime_address+16, bytes(expected))
                call(0x800B8B08, [private, 0, 0x34BF, 0])
            mark(player)
            owned(player, 0x34BF, 1)
        call(0x800B8B8C, [players+3*0xBD0, 0x32BB, 0], 1)
        expected[PROFILE+3*128+21] = 64
        check('furniture rotation ownership remains independent', runtime_address+16, bytes(expected))
        owned(3, 0x32B8, 1)
        call(0x800B88EC, [0x24BF])
        check('original garment does not enter imported ownership', runtime_address+16, bytes(expected))
        debug.write_memory(profile_address, bytes([selected[0] & 0x7F]))
        call(0x800B88EC, [0x34BF])
        owned(3, 0x34BF, 0)
        check('unselected garment does not write ownership', runtime_address+16, bytes(expected))
        debug.write_memory(profile_address, selected)
        call(0x800B88EC, [0x34BC])
        owned(3, 0x34BC, 0)
        check('adjacent item cannot alias shirt ownership', runtime_address+16, bytes(expected))
        call(0x800B7ADC, [players+3*0xBD0])
        expected[PROFILE+3*128:PROFILE+4*128] = bytes(128)
        expected[PROFILE+512+3*32:] = bytes(32)
        check('native player clear removes only that acquired ownership', runtime_address+16, bytes(expected))
        owned(3, 0x34BF, 0)
    finally:
        debug.write_memory(profile_address, selected)
        debug.write_memory(players, original_players)
        debug.write_memory(pointer, original_pointer)
        debug.write_memory(runtime_address, runtime)
    for address in guards: check('fixture guard', address, edge)
    check('complete player records restored', players, original_players)
    check('runtime state and guards restored', runtime_address, runtime)
    check('complete prefix restored', BLOB_RAM, blob[:0xC000])
    check('complete separate code retained', RAM, blob[VROM-BLOB:])
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_acquisition_and_collection': True, 'players_checked': 4,
            'present_quest_and_original_behaviour_retained': True,
            'ordinary_shop_or_reward_route_tested': False, 'device_io_performed': False,
            'requires_checkpoint_restore': True}
