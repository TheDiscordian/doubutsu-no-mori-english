"""Cartridge-loaded song-title setter through the real native message reader."""
from dataclasses import replace
import struct

from aflib import sha256
import credits_strings as c
from flash_mail import SAVE_RAM, SAVE_BYTES
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from song_item_names import START

EDGE = b'SONG'*4


def owner_metadata(actual, expected):
    """Only the native loaded address and instance count are mutable fields."""
    if len(actual) != 32 or len(expected) != 32:
        raise ValueError('Invalid song actor metadata length')
    masked = bytearray(actual)
    masked[16:20] = expected[16:20]
    masked[30] = expected[30]
    address = int.from_bytes(actual[16:20], 'big')
    count = actual[30]
    if (masked != expected or bool(address) != bool(count) or count > 127 or
            address and (address & 3 or not MODULE_RAM+RESERVATION <= address <= 0x80400000-c.RESIDENT_BYTES)):
        raise ValueError('Changed song actor identity or invalid live ownership')
    return address, count


def exercise(debug, request, record):
    read, write = debug.read_memory, debug.write_memory
    assertions = 0
    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected))
        record({'song_item_check':label, 'address':f'{at:08X}', 'bytes':len(expected),
                'assertion':'passed' if actual == expected else 'failed',
                'expected_sha256':sha256(expected), 'observed_sha256':sha256(actual)})
        if actual != expected:
            raise ValueError('Native song-title mismatch: '+label)
        assertions += 1
    def call(at, args=(), expected=None, proof=None):
        result = debug.call(f'{at:08X}', args, verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Song-title return mismatch at {at:08X}')
        return result['return_value']
    def words(*values):
        return struct.pack('>'+'I'*len(values), *values)

    symbols = request['module']['symbols']
    rows, valid = (int(symbols[n], 16) for n in ('item_rows', 'item_valid'))
    main = 0x80142410
    saved = read(SAVE_RAM, SAVE_BYTES)
    globals_before = {at:read(at, size) for at,size in (
        (main+12,4), (main+0xFC,58), (main+0x28C,4), (rows,80), (valid,4), (MODULE_RAM+56,4))}
    metadata = read(c.METADATA, 32)
    live_base, live_count = owner_metadata(metadata, bytes.fromhex(request['metadata']))
    live_actor = read(live_base, c.RESIDENT_BYTES) if live_base else None
    record({'song_actor_live_base':f'{live_base:08X}', 'native_instances':live_count,
            'static_ownership_verified':True})
    check('installed native actor ownership', c.METADATA, metadata)
    allocation = call(0x8009BFC0, [8192])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-8192:
        raise ValueError('Song-title fixture allocation failed')
    base = allocation+16
    relocation_buffer = base+c.RESIDENT_BYTES
    metrics, buffer = allocation+0x1600, allocation+0x1710
    relocation = bytes.fromhex(request['relocation'])
    edges = (allocation, relocation_buffer+len(relocation), buffer-32, buffer+1024,
             allocation+8176, TEST_STACK-0x800, TEST_STACK+0x60)
    for at in edges:
        write(at, EDGE)
    call(0x800262D0, [c.VROM,c.VROM+c.FILE_BYTES,c.RAM,c.RAM+c.RESIDENT_BYTES,
                     base,relocation_buffer,len(relocation)], proof=(0x800262D0, bytes.fromhex(request['loader'])))
    spec = replace(c.CreditsOverlay(), sections=(*c.SECTIONS[:3],c.OLD_BSS+c.EXTRA_BSS,c.SECTIONS[4]))
    if live_base:
        expected_live = relocate_verified_data(spec, bytes.fromhex(request['actor']), relocation, live_base,
                                               base_alignment=8)
        check('native live actor code matches cartridge', live_base, expected_live[:c.FILE_BYTES])
    loaded = relocate_verified_data(spec, bytes.fromhex(request['actor']), relocation, base)
    check('complete cartridge-loaded actor and owned BSS', base, loaded)
    check('original relocation records and credits BSS length', relocation_buffer, relocation)
    proof = (base, loaded[:c.SECTIONS[0]])
    entry = base+START-c.RAM
    call(0x8009C0C0, [metrics,metrics+4,metrics+8])
    heap = read(metrics, 12)
    write(main+0xFC, b'G'*58)
    names = [bytes.fromhex(v) for v in request['names']]
    def field(song, slot, expected):
        call(entry, [slot,song], proof=proof)
        check('complete selected song field', rows+slot*16, expected)
        check('native ten-byte compatibility mirror', main+0x100+slot*10, expected[:10])
    for song, name in enumerate(names):
        slot = song % 5
        field(song, slot, name)
        original = bytes((0x7F,0x31+slot))+b'!'
        expected = name.rstrip(b' ')+b'!'
        write(buffer-16, words(1,1,len(original),0)+original.ljust(1024,b' '))
        write(main+12, words(buffer-16))
        write(main+0x28C, words(0))
        call(0x800A17FC, [main,0,slot], 0)
        check('complete native song-title insertion', buffer, expected)
        check('complete inserted message length', buffer-8, words(len(expected)))
        check('song field retained after insertion', rows+slot*16, name)
        record({'native_song_item':song, 'slot':slot, 'passed':True})
    for song, slot in ((55,0),(255,0),(0,5),(1,0xFFFFFFFF),(2,256)):
        before_rows, before_native, before_valid = read(rows,80), read(main+0x100,50), read(valid,4)
        call(entry, [slot,song], proof=proof)
        check('invalid song or slot retains full fields', rows, before_rows)
        check('invalid song or slot retains native mirrors', main+0x100, before_native)
        check('invalid song or slot retains validity', valid, before_valid)
    for song in (0x100,0x101,0xFFFFFF00):
        field(song, 4, names[song & 255])
    write(MODULE_RAM+56, words(0))
    short = bytes.fromhex(request['short_names'])[:10]
    field(0, 0, short+b' '*6)
    write(MODULE_RAM+56, globals_before[MODULE_RAM+56])
    field(0, 0, names[0])
    check('leading native field guard', main+0xFC, b'G'*4)
    check('trailing native field guard', main+0x132, b'G'*4)
    check('entire actor and credits state retained', base, loaded)
    check('native live actor ownership retained', c.METADATA, metadata)
    if live_actor is not None:
        check('native live actor code and credits state retained', live_base, live_actor)
    check('saved state unchanged', SAVE_RAM, saved)
    call(0x8009C0C0, [metrics,metrics+4,metrics+8])
    check('song setter heap retained', metrics, heap)
    for at in edges:
        check('song fixture and stack guard', at, EDGE)
    check('resident module guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    for at, value in globals_before.items():
        write(at, value)
        check('song global restored', at, value)
    call(0x8009C040, [allocation])
    return {'complete_song_fields':55, 'native_message_insertions':55, 'rejections':5,
            'byte_argument_cases':3, 'resource_fallback_and_retry':True, 'song_assertions':assertions,
            'debugger_uploaded_production_bytes':0, 'normal_performance':False,
            'song_request_input_tested':False, 'game_save_validation':False,
            'hardware_verified':False, 'requires_checkpoint_restore':True}
