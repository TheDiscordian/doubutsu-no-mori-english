"""One bounded cartridge-load, actual caller, mailbox, and reader batch."""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from npc_mail_show import relocate_verified_data
from renewal_actor import ActorImage, RAM, NEW_VROM, METADATA
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

EDGE = b'EDGE'*4


def exercise(debug, request, record):
    read, write = debug.read_memory, debug.write_memory
    assertions = 0

    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected))
        record({'renewal_actor_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('Native renewal check failed: '+label)
        assertions += 1

    def call(at, args=(), expected=None, proof=None):
        result = debug.call(f'{at:08X}', args, verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Renewal call {at:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']

    def word(value):
        return struct.pack('>I', value)

    saved = read(SAVE_RAM, SAVE_BYTES)
    module, report = request['module'], request['report']
    capital = int(module['symbols']['af_mail_generation_capital'], 16)
    globals_before = {at: read(at, size) for at, size in
                      ((capital, 4), (0x8013A0E4, 4), (0x8003C590, 4), (0x80140680, 200))}
    data, reloc = bytes.fromhex(request['data']), bytes.fromhex(request['relocation'])
    size = 0x4000
    allocation = call(0x8009BFC0, [size])
    if allocation&15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Renewal fixture allocation failed')
    base = allocation+16
    relocation_at = base+len(data)
    shim, rtc, arena, work = (allocation+at for at in (0x2000, 0x2040, 0x2060, 0x2100))
    if relocation_at+len(reloc)+16 > shim or work+4720+16 > allocation+size-16:
        raise ValueError('Renewal fixture exceeds its owned allocation')
    edges = (allocation, relocation_at+len(reloc), rtc+16, arena+16,
             work-16, work+4720, allocation+size-16, TEST_STACK-0x1000, TEST_STACK+0x30)
    for at in edges:
        write(at, EDGE)
    spec = ActorImage(RAM, len(data), struct.unpack_from('>5I', reloc))
    loaded = relocate_verified_data(spec, data, reloc, base)
    check('installed actor ownership', METADATA, bytes.fromhex(request['metadata']))
    call(0x800262D0, [NEW_VROM, NEW_VROM+len(data), RAM, RAM+len(data), base, relocation_at, len(reloc)],
         proof=(0x800262D0, bytes.fromhex(request['loader'])))
    check('native cartridge actor relocation', base, loaded)
    check('native merged relocation records', relocation_at, reloc)
    # Enter the actual original JAL/delay slot and new pending-flag gate with
    # the original caller frame. The date-selection prefix is not exercised.
    shim_code = struct.pack('>8I', 0x27BDFFD8, 0xAFBF0014, 0x00801025,
                            0x08000000|(((base+0x2F8)>>2)&0x3FFFFFF), 0, 0, 0, 0)
    write(shim, shim_code)
    call(0x8009C0C0, [arena, arena+4, arena+8])
    heap = read(arena, 12)

    def fixture(case, slot, owners=15, working=0):
        fixture = bytearray(i%251 for i in range(SAVE_BYTES))
        # Player-to-home permutation: player 0 lives in home 2, then 0, 3, 1.
        fixture[0xEF5A] = 2 | (0<<2) | (3<<4) | (1<<6)
        fixture[0xED72] |= 16
        for home in range(4):
            at = 0x3596+home*0xB48
            fixture[at:at+2] = b'AB' if owners>>home&1 else b'\xff\xff'
            for index in range(10):
                fixture[0x3A00+home*0xB48+index*164+38] = 255 if index >= slot else 0
        write(SAVE_RAM, fixture)
        write(0x8013A0E4, word(working<<2))
        write(capital, word(case['capital']))
        write(rtc, bytes.fromhex(case['rtc']))
        return fixture

    def deliver(case, slot, owners=15, working=0):
        before = fixture(case, slot, owners, working)
        call(shim, [case['level'], rtc], 1, (shim, shim_code))
        expected = bytearray(before)
        expected[0xED72] &= ~16
        for home, player in enumerate((1, 3, 0, 2)):
            if slot >= 10 or not owners>>home&1 or working>>player&1:
                continue
            mail = bytearray(164)
            mail[:16] = before[0x20+player*0xBD0:0x30+player*0xBD0]
            mail[18:30] = b' '*12
            mail[30:34] = b'\xff'*4
            mail[34] = 255
            mail[38:42] = bytes((0, 128, 2, 55))
            mail[42:] = bytes.fromhex(case['wire'])
            at = 0x3A00+home*0xB48+slot*164
            expected[at:at+164] = mail
            call(int(module['symbols']['af_mail_restore'], 16), [work+3552, SAVE_RAM+at+42, 122, work], 1)
            check('complete English mailbox-to-reader text', work+3552, bytes.fromhex(case['text']))
        check('whole save changes only by selected complete mail and notification flag', SAVE_RAM, expected)
        # With the pending bit now clear, the complete original wrapper must
        # not send another letter. This path does not enter date helpers.
        call(base+0x244, proof=(base, loaded))
        check('native no-pending path prevents duplicate delivery', SAVE_RAM, expected)
        check('source timestamp retained', rtc, bytes.fromhex(case['rtc']))
        check('capitalization retained', capital, word(case['capital']))
        check('working flags retained', 0x8013A0E4, word(working<<2))
        for at in edges:
            check('owned fixture guard', at, EDGE)

    for number, case in enumerate(request['cases']):
        deliver(case, number%10)
    for slot, owners, working in ((10, 15, 0), (0, 0, 0), (0, 15, 15), (9, 5, 2), (0, 15, 8)):
        deliver(request['cases'][0], slot, owners, working)
    first = request['cases'][0]
    before = fixture(first, 0)
    config = 0x80194924
    check('enabled full catalogue', config, bytes.fromhex('03000000'))
    write(config, bytes(4))
    call(shim, [first['level'], rtc], 0, (shim, shim_code))
    check('failed preparation retains every mailbox and the pending notification', SAVE_RAM, before)
    check('failed preparation retains capitalization', capital, word(first['capital']))
    write(config, bytes.fromhex('03000000'))
    # Retry the actual retained state, without resetting the mailboxes or flag.
    call(shim, [first['level'], rtc], 1, (shim, shim_code))
    check('retry clears only the pending flag', SAVE_RAM+0xED72, bytes((before[0xED72]&~16,)))
    call(0x8009C0C0, [arena, arena+4, arena+8])
    check('heap accounting retained', arena, heap)
    check('installed actor code retained', base, loaded)
    check('module guard', GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
    for at in edges:
        check('final owned fixture guard', at, EDGE)
    write(SAVE_RAM, saved)
    check('live save restored', SAVE_RAM, saved)
    for at, value in globals_before.items():
        if at in (0x8003C590, 0x80140680):
            check('RNG and handbill values unchanged', at, value)
        write(at, value)
        check('live global restored', at, value)
    call(0x8009C040, [allocation])
    return {'complete_renewal_cases': len(request['cases']), 'eligibility_cases': 5,
            'renewal_actor_assertions': assertions, 'actual_caller_failure_gate': True,
            'normal_scheduling': False, 'hardware_verified': False,
            'requires_checkpoint_restore': True}
