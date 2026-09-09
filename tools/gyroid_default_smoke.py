"""Execute the cartridge-owned gyroid selector, real owner route, and full loads."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from gyroid_message_test_scenario import expected_message
import gyroid_default_actor as actor
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

EDGE = b'GYRO'*4


def exercise(debug, request, record):
    read, write = debug.read_memory, debug.write_memory
    assertions = 0
    def check(label, at, expected):
        nonlocal assertions
        value = read(at, len(expected))
        record({'gyroid_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if value == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(value)})
        if value != expected: raise ValueError('Native gyroid mismatch: '+label)
        assertions += 1
    def call(at, args=(), expected=None, proof=None):
        result = debug.call(f'{at:08X}', args, verified_code=proof); record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Gyroid return mismatch at {at:08X}')
        return result['return_value']
    def words(*values): return struct.pack('>'+'I'*len(values), *values)
    for at, value in request['guards'].items(): check('native state and continuation helper', int(at, 16), bytes.fromhex(value))
    saved = read(SAVE_RAM, SAVE_BYTES)
    originals = {at: read(at, size) for at, size in ((0x80104A70, 4), (0x80136EA3, 1), (0x80142410, 0x330))}
    metadata = read(actor.METADATA, 32); masked = bytearray(metadata)
    masked[16:20] = bytes(4); masked[30] = 0
    live = int.from_bytes(metadata[16:20], 'big')
    if (masked != actor.metadata() or bool(live) != bool(metadata[30])
            or live and (live & 3 or not MODULE_RAM+RESERVATION <= live <= 0x80400000-actor.SIZE)):
        raise ValueError('Changed live gyroid actor ownership')
    live_image = read(live, actor.SIZE) if live else None
    allocation = call(0x8009BFC0, [0x3000])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-0x3000:
        raise ValueError('Gyroid fixture allocation failed')
    base, relocation_buffer, instance, demo, owner, metrics, buffer, window, index = (
        allocation+at for at in (0x10, 0x1B60, 0x1D40, 0x2050, 0x23A0, 0x2420, 0x2500, 0x2920, 0x2C60))
    data, reloc, default = (bytes.fromhex(request[k]) for k in ('actor', 'relocation', 'saved_default'))
    edges = (allocation, base+actor.SIZE, relocation_buffer+len(reloc), instance+0x300,
             demo+0x340, owner+0x70, buffer-16, buffer+1040, window+0x330,
             allocation+0x2FF0, TEST_STACK-0x800, TEST_STACK+0x60)
    for at in edges: write(at, EDGE)
    call(0x800262D0, [actor.NEW_VROM, actor.NEW_VROM+actor.SIZE, actor.RAM, actor.RAM+actor.SIZE,
                     base, relocation_buffer, len(reloc)], proof=(0x800262D0, bytes.fromhex(request['loader'])))
    spec = actor.ActorImage(actor.RAM, actor.SIZE, struct.unpack_from('>5I', reloc))
    loaded = relocate_verified_data(spec, data, reloc, base)
    check('complete cartridge-loaded actor', base, loaded)
    check('cartridge-loaded relocation records', relocation_buffer, reloc)
    proof = (base, loaded)
    call(0x8009C0C0, [metrics, metrics+4, metrics+8]); heap = read(metrics, 12)
    write(demo, bytes(0x340)); write(demo+0xE4, words(7)); write(0x80104A70, words(demo))
    write(owner, bytes(0x70)); write(owner+0x18, default)
    selector, adapter = (base+actor.SYMBOLS[n] for n in ('af_gyroid_default_select', 'af_gyroid_default_demo'))
    for requested in (0x928, 0x934, 0x935, 0x925, 0x92E, 0x929, 0x10000928, 0xFFFFFFFF):
        expected = 0x2AE7 if requested == 0x928 else requested
        call(selector, [requested, owner+0x18], expected, proof)
        # Nine o32 arguments place the actual incoming owner pointer at sp+20.
        call(adapter, [requested, 0, 0, 0, 0, 0, 0, 0, owner], proof=proof)
        check('adapter passes selected ID to real native setter', demo+0x300, words(expected))
    call(selector, [0x928, 0], 0x928, proof)
    for offset in range(64):
        custom = bytearray(default); custom[offset] ^= 1
        write(owner+0x18, custom)
        call(selector, [0x928, owner+0x18], 0x928, proof)
        check('custom byte and source retained', owner+0x18, bytes(custom))
    for kind in (0, 7, 8, 9):
        write(owner+0x18, default); write(demo+0xE4, words(kind)); write(demo+0x300, words(0x12345678))
        call(adapter, [0x928, 0, 0, 0, 0, 0, 0, 0, owner], proof=proof)
        check('native demo eligibility retained', demo+0x300, words(0x2AE7 if kind else 0x12345678))
    write(demo+0xE4, words(7)); write(instance, bytes(0x300)); write(0x80135DFA, b'\xe4')
    # Execute the complete original other-owner decision, custom formatter,
    # table delay slot, and new adapter for all four actual home records.
    for home in range(4):
        write(instance+0x283, bytes((home,))); write(0x80136EA3, bytes(((home+1)%4,)))
        identity = SAVE_RAM+0x3588+home*0xB48
        message = SAVE_RAM+0x4080+home*0xB48
        write(identity, b'OWNER '+b'HOME  '+bytes.fromhex('12341234'))
        for is_default in (True, False):
            content = default if is_default else b'Welcome!\xcdPlease come in.'.ljust(64, b' ')
            write(message, content); retained = read(SAVE_RAM, SAVE_BYTES)
            call(base+0x8096B1A4-actor.RAM, [instance], 3, proof)
            call(base+0x8096B2D8-actor.RAM, [instance], proof=proof)
            check('real other-owner route selects complete default or custom ID', demo+0x300,
                  words(0x2AE7 if is_default else 0x928))
            check('actual owner route preserves all saved bytes', SAVE_RAM, retained)
            if not is_default:
                formatted = expected_message(content, 64, bytes.fromhex(request['font_cuts']))
                check('complete custom message still uses the native field', 0x80142410+0x132, formatted)
            record({'gyroid_home': home, 'default': is_default, 'passed': True})
    write(window, bytes(0x330)); write(window+12, words(buffer))
    for number in (0x928, 0x2AE7):
        payload = bytes.fromhex(request['messages'][f'{number:04X}'])
        write(buffer, b'!'*1040)
        call(0x8009E558, [buffer, number, 0], 1)
        check('complete native cartridge message load', buffer, words(1, number, len(payload), 0)+payload)
        # The same outgoing continuation is retained in default and custom text.
        at = payload.index(bytes.fromhex('7F0E0929'))
        write(index, words(at)); call(0x800A21C0, [window, index], 0)
        check('native next-message selection', window+0x2C4, words(0x929))
        check('native command cursor', index, words(at+4))
        call(0x8009E658, [window, 0x929], 1)
        next_payload = bytes.fromhex(request['messages']['0929'])
        check('complete native outgoing continuation load', buffer, words(1, 0x929, len(next_payload), 0)+next_payload)
    check('entire test actor retained', base, loaded)
    check('actual actor ownership retained', actor.METADATA, metadata)
    if live_image is not None: check('live actor retained', live, live_image)
    call(0x8009C0C0, [metrics, metrics+4, metrics+8]); check('gyroid calls retain heap allocation', metrics, heap)
    for at in edges: check('fixture and stack guard', at, EDGE)
    check('resident end guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    write(SAVE_RAM, saved); check('entire saved state restored', SAVE_RAM, saved)
    for at, value in originals.items():
        write(at, value); check('global restored', at, value)
    call(0x8009C040, [allocation])
    return {'gyroid_assertions': assertions, 'complete_other_owner_cases': 8,
            'native_single_byte_custom_cases': 64, 'complete_loaded_messages': [0x928, 0x2AE7, 0x929],
            'debugger_uploaded_production_bytes': 0, 'normal_interaction': False,
            'editor_tested': False, 'game_save_validation': False, 'hardware_verified': False,
            'requires_checkpoint_restore': True}
