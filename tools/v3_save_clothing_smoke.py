"""Current native extended save entries, format migration, and player clearing."""
import importlib.util
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
from v3_save_clothing import PROFILE, RAM, RUNTIME_BYTES, STATE, VROM
from v3_save_codec import BANK


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['clothing'].get('save_extension'):
        raise ValueError('Clothing save probe requires the current assembled cartridge')
    spec = importlib.util.spec_from_file_location('clothing_save_reference',
        Path(__file__).resolve().parents[1]/'tests/test_v3_save_clothing.py')
    reference = importlib.util.module_from_spec(spec); spec.loader.exec_module(reference)
    legacy_bank, state_data = reference.fixture()
    expected_bank = bytes(reference.reference_pack(legacy_bank, state_data))
    profile_data = bytes.fromhex(report['save_runtime']['profile_hex'])
    if profile_data != bytes(state_data[:PROFILE]): raise ValueError('Fixture profile differs from current imports')
    blob = by_vrom(rom)[BLOB].extract(rom)
    proofs, edge = boot_proofs(rom), b'V3SC'*4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'clothing_save_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Clothing save mismatch: '+label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proofs.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected & 0xFFFFFFFF:
            raise ValueError('Unexpected clothing-save return value')
        return result['return_value']

    check('complete startup prefix', BLOB_RAM, blob[:0xC000])
    check('separate extended codec loaded completely', RAM, blob[VROM-BLOB:])
    runtime = struct.pack('>4I', 0xAF535633, 0, 0, 0)+profile_data+bytes(640)+bytes.fromhex('AF53C0DE')*4
    check('complete expanded native runtime initialization', 0x8046C000, runtime)
    size = 0x11000
    allocation = call(0x8009BFC0, [size])
    if allocation % 16 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Clothing save fixture allocation failed')
    bank, profile, state, output, bridge = (allocation+x for x in (16, 0x10040, 0x10140, 0x10500, 0x10C00))
    guards = (allocation, bank+BANK, profile+PROFILE, state+STATE, output+STATE,
              allocation+size-16, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    wrappers, entries = bytearray(), {}
    for name in ('check', 'pack', 'collect'):
        entries[name] = bridge+len(wrappers)
        target = report['save_codec']['code']['symbols']['af_v3_save_'+name]
        wrappers.extend(struct.pack('>4I', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0))
    debug.write_memory(bridge, bytes(wrappers))
    call(0x8002FE00, [bridge, len(wrappers)])
    call(0x80034CE0, [bridge, len(wrappers)])
    for address in entries.values(): proofs[address] = (bridge, bytes(wrappers))
    debug.write_memory(bank, bytes(legacy_bank))
    debug.write_memory(profile, profile_data)
    debug.write_memory(state, bytes(state_data))
    call(entries['check'], [bank, BANK, profile, output], 0)
    check('legacy migration initializes all ownership empty', output, profile_data+bytes(640))
    call(entries['pack'], [bank, BANK, state], 1)
    check('complete format-2 bank matches independent encoder', bank, expected_bank)
    call(entries['check'], [bank, BANK, profile, output], 1)
    check('all furniture and clothing ownership restored', output, bytes(state_data))
    missing = bytearray(profile_data); missing[183] = 0
    debug.write_memory(profile, bytes(missing))
    debug.write_memory(output, b'\xA5'*STATE)
    call(entries['check'], [bank, BANK, profile, output], -7)
    check('missing clothing leaves destination intact', output, b'\xA5'*STATE)
    debug.write_memory(profile, profile_data)
    old_bank, old_state = reference.legacy.fixture()
    debug.write_memory(bank, bytes(reference.legacy.reference_pack(old_bank, old_state)))
    call(entries['check'], [bank, BANK, profile, output], 1)
    check('format-1 migration retains furniture and initializes clothing', output,
          profile_data+bytes(old_state[160:])+bytes(128))
    debug.write_memory(state, profile_data+bytes(640))
    for player in range(4):
        call(entries['collect'], [state, player, 0x34BF, 1], 1)
        call(entries['collect'], [state, player, 0x34BC, 0], -7)
    check('clothing ownership never alters furniture rotation bits', state,
          profile_data+bytes(512)+bytes(state_data[PROFILE+512:]))
    call(entries['collect'], [state, 0, 0x3225, 1], 1)
    call(entries['collect'], [state, 0, 0x3227, 0], 1)
    # Exercise the changed native player-clear hook on this disposable machine.
    # The complete emulator checkpoint restores the original private data.
    try:
        debug.write_memory(0x8046C010, bytes(state_data))
        call(0x800B7ADC, [0x80126EC0+3*0xBD0])
        cleared = bytearray(state_data)
        cleared[PROFILE+3*128:PROFILE+4*128] = bytes(128)
        cleared[PROFILE+512+3*32:] = bytes(32)
        check("native player clear removes only that player's furniture and clothing ownership",
              0x8046C000, runtime[:16]+bytes(cleared)+runtime[-16:])
    finally:
        debug.write_memory(0x8046C000, runtime)
    for at in guards: check('fixture guard', at, edge)
    check('expanded runtime restored', 0x8046C000, runtime)
    check('resident prefix intact', BLOB_RAM, blob[:0xC000])
    check('extended codec intact', RAM, blob[VROM-BLOB:])
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_public_save_entries': 3, 'clothing_players': 4,
            'format_1_migration_tested': True, 'format_2_complete_encoding_tested': True,
            'native_player_clear_tested': True, 'runtime_bytes': RUNTIME_BYTES,
            'device_io_performed': False, 'ordinary_clothing_save_reload_tested': False,
            'requires_checkpoint_restore': True}
