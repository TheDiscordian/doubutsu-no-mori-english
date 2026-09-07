"""Test native animation selection, explicitly stopping before pose initialization."""

import struct
from types import SimpleNamespace

from aflib import sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from npc_mail_show import relocate_verified_data
from reference_animations import (NPC_VROM, NPC_RAM, NPC_SHA256, RELOCATION_SHA256, SECTIONS,
                                  CONSUMER, ANIMATION_INIT, TABLES, ALLOWED_VALUES,
                                  RELOCATION_CONSTANTS, is_resident_animation)
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from textcodec import tokenize

EDGE = b'EDGE'*4
ORDER_POINTER = 0x80104A70


def exercise(debug, request, record):
    read = debug.read_memory
    def write(address, value):
        debug.write_memory(address, value)
        record({'animation_test_write': f'{address:08X}', 'bytes': len(value), 'sha256': sha256(value)})
    def check(label, address, expected):
        actual = read(address, len(expected))
        record({'animation_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('Resident animation check failed: '+label)
    def call(address, args, proof=None, expected=None):
        result = debug.call(f'{address:08X}', args, verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Resident animation native return differs')
        return result['return_value']

    original, reloc = bytes.fromhex(request['source']), bytes.fromhex(request['relocation'])
    if sha256(original) != NPC_SHA256 or sha256(reloc) != RELOCATION_SHA256:
        raise ValueError('Unverified resident animation test source')
    spec = SimpleNamespace(ram=NPC_RAM, file_bytes=sum(SECTIONS[:3]), sections=SECTIONS,
                           resident_bytes=sum(SECTIONS[:4]))
    for address, value in request['guards'].items():
        check('unchanged native dispatch', int(address, 16), bytes.fromhex(value))
    saved, order_pointer = read(SAVE_RAM, SAVE_BYTES), read(ORDER_POINTER, 4)
    size = 16+spec.resident_bytes+len(reloc)+16+0xA00+0x100+0x340+0x440+32
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Resident animation fixture allocation failed')
    base = allocation+16
    actor = base+spec.resident_bytes+len(reloc)+16
    orders, window, message = actor+0xA00, actor+0xB00, actor+0xE40
    cursor = message+0x420
    guard_addresses = (allocation, actor-16, message+0x410, allocation+size-16,
                       TEST_STACK-0x800, TEST_STACK+0x30)
    for address in guard_addresses: write(address, EDGE)
    call(0x800262D0, [NPC_VROM, NPC_VROM+spec.file_bytes, NPC_RAM,
                     NPC_RAM+spec.resident_bytes, base, base+spec.resident_bytes, len(reloc)],
         proof=(0x800262D0, bytes.fromhex(request['loader'])))
    loaded = relocate_verified_data(spec, original, reloc, base, address_constants=RELOCATION_CONSTANTS)
    check('complete native cartridge relocation and BSS', base, loaded)
    # Recording boundary, not a replacement animation implementation: capture
    # the selected sequence/talk flag and call count, then return. The real
    # selector and all six tables stay intact. No pose/rendering proof is claimed.
    stub = struct.pack('>7I', 0xAC850000, 0xAC860004, 0x8C880008, 0x25080001,
                       0xAC880008, 0x03E00008, 0)
    at = ANIMATION_INIT-NPC_RAM
    instrumented = loaded[:at]+stub+loaded[at+len(stub):]
    write(base+at, stub)
    proof = (base, instrumented[:SECTIONS[0]])
    write(ORDER_POINTER, struct.pack('>I', orders))
    order_offset = 16+4*20
    preparations = 0
    for holder, pair in ((0, 0), (0x2300, 2), (0x1001, 4)):
        primary = struct.unpack_from('>42i', original, TABLES[pair]-NPC_RAM)
        secondary = struct.unpack_from('>42i', original, TABLES[pair+1]-NPC_RAM)
        for value in sorted(ALLOWED_VALUES):
            cases = ['entry']+(['continuation', 'repeat_running'] if value != 255 else ['reset_idle'])
            for kind in cases:
                fixture = bytearray(b'X'*0xA00)
                fixture[:12] = bytes(12)
                struct.pack_into('>H', fixture, 0x842, holder)
                fixture[0x92A] = 0 if kind == 'entry' else value
                sequence, talk = (21, 1) if value == 255 else (primary[value], 0)
                struct.pack_into('>I', fixture, 0x704, sequence)
                struct.pack_into('>I', fixture, 0x188, 1 if kind == 'continuation' else 0)
                expected = bytearray(fixture)
                if kind in ('entry', 'continuation'):
                    struct.pack_into('>3I', expected, 0,
                                     secondary[value] if kind == 'continuation' else sequence, talk, 1)
                    expected[0x92A] = value
                order_data = bytearray(b'Q'*216)
                struct.pack_into('>H', order_data, order_offset, value if kind in ('entry', 'repeat_running') else 0)
                write(actor, fixture); write(orders, order_data)
                call(base+CONSUMER-NPC_RAM, [actor], proof=proof)
                struct.pack_into('>H', order_data, order_offset, 0)
                check('complete actor selection '+kind, actor, expected)
                check('only consumed NPC0 slot zero cleared', orders, order_data)
                preparations += 1
    write(window, bytes(0x330))
    write(window+12, struct.pack('>I', message))
    loads = dispatches = 0
    for number, raw in request['messages'].items():
        entry = bytes.fromhex(raw)
        write(message, b'G'*0x410)
        call(0x8009E558, [message, int(number, 16), 0], expected=1)
        check('complete approved cartridge message', message,
              struct.pack('>4I', 1, int(number, 16), len(entry), 0)+entry)
        for token in tokenize(entry, request['info']):
            if token.kind != 'cmd' or not is_resident_animation(token.data): continue
            order_data = bytearray(b'Q'*216)
            write(orders, order_data); write(cursor, struct.pack('>I', token.offset))
            call(0x800A21C0, [window, cursor], expected=0)
            order_data[order_offset:order_offset+2] = token.data[3:5]
            check('exact native animation request; other orders retained', orders, order_data)
            check('complete animation command advancement', cursor, struct.pack('>I', token.offset+5))
            dispatches += 1
        check('full cartridge text retained after all requests', message,
              struct.pack('>4I', 1, int(number, 16), len(entry), 0)+entry)
        loads += 1
    write(ORDER_POINTER, order_pointer)
    write(base+at, loaded[at:at+len(stub)])
    check('complete original overlay restored', base, loaded)
    check('complete saved game retained', SAVE_RAM, saved)
    check('original order pointer restored', ORDER_POINTER, order_pointer)
    for address in guard_addresses: check('allocation and stack guard', address, EDGE)
    check('module guard', GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
    call(0x8009C040, [allocation])
    return {'resident_animation_selections': preparations, 'message_loads': loads,
            'animation_dispatches': dispatches, 'allocation_freed': f'{allocation:08X}',
            'pose_initialization_tested': False, 'normal_gameplay': False, 'requires_checkpoint_restore': True}
