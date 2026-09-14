"""Execute the current resident save codec on private RAM, without flash writes."""
import importlib.util
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
from v3_save_codec import BANK, BLOB_SIZE, PAYLOAD, PROFILE, STATE


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('save_codec'):
        raise ValueError('Save-codec probe requires its exact current cartridge')
    # Reuse the independent Python/zlib reference, not the C codec under test.
    spec = importlib.util.spec_from_file_location('v3_save_reference',
        Path(__file__).resolve().parents[1] / 'tests/test_v3_save_codec.py')
    reference = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reference)
    legacy, state_data = reference.fixture()
    expected_bank = bytes(reference.reference_pack(legacy, state_data))
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)[:BLOB_SIZE]
    code = files[CODE_VROM].extract(rom)
    proofs, symbols = boot_proofs(rom), report['save_codec']['code']['symbols']
    edge, calls = b'V3SV' * 4, 0

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'save_codec_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native save-codec check failed: ' + label)

    def call(address, args=(), expected=None):
        nonlocal calls
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proofs.get(address))
        record(result)
        calls += 1
        if expected is not None and result['return_value'] != expected & 0xFFFFFFFF:
            raise ValueError('Native save-codec call returned an unexpected value')
        return result['return_value']

    check('complete resident prefix', BLOB_RAM, blob)
    for start, end in ((0x8008ECA0, 0x80090120), (0x800CDB10, 0x800CE120)):
        check('unchanged resident native save code', start, code[start - CODE_RAM:end - CODE_RAM])
    allocation = call(0x8009BFC0, [0x11000])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - 0x11000:
        raise ValueError('Save-codec private allocation failed')
    bank, profile = allocation + 16, allocation + 0x10040
    state, output, bridge = allocation + 0x10100, allocation + 0x10400, allocation + 0x10700
    guards = (allocation, bank + BANK, profile + PROFILE, state + STATE, output + STATE,
              allocation + 0x10FF0, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    # Guarded tail-call bridges keep the debugger's ordinary-code limit intact.
    wrappers = bytearray()
    entries = {}
    for name in ('check', 'pack', 'collect'):
        address = bridge + len(wrappers)
        entries[name] = address
        wrappers.extend(struct.pack('>4I', 0x08000000 | (symbols['af_v3_save_' + name] >> 2 & 0x3FFFFFF), 0, 0, 0))
    debug.write_memory(bridge, bytes(wrappers))
    call(0x8002FE00, [bridge, len(wrappers)])
    call(0x80034CE0, [bridge, len(wrappers)])
    proofs.update({address: (bridge, bytes(wrappers)) for address in entries.values()})
    debug.write_memory(bank, bytes(legacy))
    debug.write_memory(profile, bytes(state_data[:PROFILE]))
    debug.write_memory(state, bytes(state_data))
    call(entries['check'], [bank, BANK, profile, output], 0)
    check('legacy upgrade state starts with empty catalogue', output, bytes(state_data[:PROFILE]) + bytes(512))
    call(0x8008EEE8, [bank], 1)
    call(entries['pack'], [bank, BANK, state], 1)
    check('complete packed bank matches independent encoder', bank, expected_bank)
    call(0x8008EE7C, [bank, PAYLOAD], 0)
    call(0x8008EEE8, [bank], 0)
    call(entries['check'], [bank, BANK, profile, output], 1)
    check('all four catalogues decoded', output, bytes(state_data))
    call(entries['check'], [bank, BANK, profile, 0], 1)
    debug.write_memory(state, bytes(state_data[:PROFILE]) + bytes(512))
    for player, item in ((0, 0x3225), (1, 0x32BB), (2, 0x3224), (2, 0x32BA), (3, 0x32B9)):
        call(entries['collect'], [state, player, item, 1], 1)
        call(entries['collect'], [state, player, item ^ 3, 0], 1)
    call(entries['collect'], [state, 0, 0x3FFF, 1], -7)
    call(entries['collect'], [state, 4, 0x3224, 1], -1)
    call(entries['collect'], [state, 0, 0x1004, 1], -1)
    check('bounded catalogue ownership and rotations', state, bytes(state_data))
    expanded = bytearray(state_data[:PROFILE])
    expanded[-1] |= 0x80
    debug.write_memory(profile, bytes(expanded))
    call(entries['check'], [bank, BANK, profile, output], 1)
    check('added selection retains existing catalogue', output, bytes(expanded + state_data[PROFILE:]))
    for at in (29, 32 + (137 >> 3)):
        missing = bytearray(state_data[:PROFILE])
        missing[at] = 0
        debug.write_memory(profile, bytes(missing))
        debug.write_memory(output, b'\xA5' * STATE)
        call(entries['check'], [bank, BANK, profile, output], -7)
        check('missing import leaves output unchanged', output, b'\xA5' * STATE)
    debug.write_memory(profile, bytes(state_data[:PROFILE]))
    bad_checksum = bytearray(expected_bank)
    bad_checksum[0x800] ^= 1
    bad_binding = bytearray(bad_checksum)
    reference.checksum(bad_binding)
    bad_crc = bytearray(expected_bank)
    bad_crc[PAYLOAD + 0xC0] ^= 1
    bad_catalogue = bytearray(bad_crc)
    reference.seal_extension(bad_catalogue)
    for label, changed, result in (('payload checksum', bad_checksum, -3),
            ('mismatched payload and extension', bad_binding, -5),
            ('extension checksum', bad_crc, -6), ('unselected catalogue bit', bad_catalogue, -8)):
        debug.write_memory(bank, bytes(changed))
        call(entries['check'], [bank, BANK, profile, output], result)
        check(label + ' rejection leaves output unchanged', output, b'\xA5' * STATE)
        check(label + ' rejection leaves bank unchanged', bank, bytes(changed))
    debug.write_memory(bank, expected_bank)
    call(entries['check'], [bank, PAYLOAD, profile, output], -1)
    call(entries['pack'], [bank, BANK, bank + PAYLOAD], -1)
    check('invalid calls retain complete bank', bank, expected_bank)
    check('all tests retain source state', state, bytes(state_data))
    check('all tests retain current profile', profile, bytes(state_data[:PROFILE]))
    check('complete resident prefix retained', BLOB_RAM, blob)
    for at in guards:
        check('private/stack guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_calls': calls, 'independent_complete_encoding_verified': True,
            'native_v2_signature_rejects_v3': True, 'native_payload_checksum_passed': True,
            'device_io_performed': False, 'ordinary_save_reload_tested': False,
            'requires_checkpoint_restore': True}
