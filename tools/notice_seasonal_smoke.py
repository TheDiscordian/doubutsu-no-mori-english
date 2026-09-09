"""Real native seasonal selection, calendar capture, publication, and retry.

The paused fixture controls common time and the existing pending cursor. It
does not replace the calendar, creator, allocator, writer, or scheduler code.
The posting cursor is common runtime state outside the FlashRAM payload; this
batch proves same-session retry, not pending-notice persistence across saving.
"""

import struct

from aflib import sha256
from flash_mail import SAVE_RAM, SAVE_BYTES
from mail_record import Field, Record
from notice_record import pack
from notice_seasonal import complete_body
from notice_treasure_smoke import traced_call
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD

POSTS, CURSOR, TIME, CHECKED = 0x80129E0A, 0x80137918, 0x80136FBC, 0x80136744
EDGE = b'NSED'*4


def words(*values): return struct.pack('>'+'I'*len(values), *values)


def date_text(month, day):
    months = 'January February March April May June July August September October November December'.split()
    if not 1 <= month <= 12 or not 1 <= day <= 31: raise ValueError('Invalid actual native calendar date')
    suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f'{months[month-1]} {day}{suffix}'.encode()


def exercise(debug, request, record):
    read, write = debug.read_memory, debug.write_memory
    assertions = completed = direct_cases = prefix_failures = 0
    def check(label, at, expected):
        nonlocal assertions
        actual = read(at, len(expected))
        record({'seasonal_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected: raise ValueError('Native seasonal mismatch: '+label)
        assertions += 1
    def call(at, args=(), expected=None):
        result = debug.call(f'{at:08X}', args)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Unexpected seasonal helper return at {at:08X}')
        return result['return_value']
    for at, value in request['guards'].items(): check('source-bound seasonal code', int(at, 16), bytes.fromhex(value))
    symbols = request['module']['symbols']
    capital, session = (int(symbols[name], 16) for name in ('af_mail_generation_capital', 'af_npc_mail_session'))
    loader = int(symbols['af_npc_mail_load'], 16)
    check('creator detached before native batch', session, bytes(4))
    saved = read(SAVE_RAM, SAVE_BYTES)
    globals_before = {at: read(at, size) for at, size in
                      ((CURSOR, 8), (TIME, 20), (capital, 4), (0x80104F94, 4),
                       (0x80140680, 200), (MODULE_RAM+56, 48), (0x8003C590, 8))}
    allocation = call(0x8009BFC0, [0x1000])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-0x1000:
        raise ValueError('Seasonal scratch allocation failed')
    output, player, descriptor, lunar, solar, metrics = (allocation+at for at in (0x20, 0x100, 0x120, 0x140, 0x160, 0x200))
    edges = (allocation, output+164, player-16, player+16, descriptor+12, lunar+4, solar+4,
             metrics+12, allocation+0xFF0, TEST_STACK-0x1800, TEST_STACK+0x30)
    for at in edges: write(at, EDGE)
    write(player, bytes(16))
    call(0x8007D91C, [0], 0)
    call(0x8007D90C, expected=0)
    call(0x8009C0C0, [metrics, metrics+4, metrics+8])
    heap = read(metrics, 12)
    config = list(struct.unpack('>8I', globals_before[MODULE_RAM+56][16:48]))
    entries = {entry['template']: entry for entry in request['templates']}
    shops = [bytes.fromhex(value) for value in request['shops']]
    empty = b' '*96+bytes.fromhex(request['empty_rtc'])
    calendars = {}

    def calendar(year):
        if year in calendars: return calendars[year]
        values = {}
        for field, month, day in ((2, 8, 15), (3, 9, 13)):
            source = struct.pack('>HBB', year, month, day)
            write(lunar, source); write(solar, b'?'*4)
            returned = call(0x800D60E4, [solar, lunar])
            if returned not in (0, 1): raise ValueError('Unexpected lunar conversion status')
            native = read(solar, 4) if returned else source
            values[field] = date_text(native[2], native[3])
            check('native lunar input remains private and unchanged', lunar, source)
            record({'seasonal_native_calendar': year, 'field': field, 'converted': returned,
                    'native_output': native.hex(), 'complete_date': values[field].decode()})
        week = call(0x800D5CF8, [year, 10, 14])
        if not 0 <= week <= 6: raise ValueError('Unexpected native weekday')
        values[4] = date_text(10, 15-week if week else 8)
        calendars[year] = values
        return values

    def value(number, flag, year=2001, level=3):
        dates = calendar(year)
        fields = {0: b'TownXX', 1: shops[level], **dates}
        result = Record(4, 0, (number,), tuple((i, Field(fields[i])) for i in entries[number]['fields']), bool(flag))
        # Independent host completion also rejects a malformed full field.
        complete_body(result, entries[number])
        return result

    def rtc_for(index, year=2001, hour=6):
        month, day = request['dates'][index] >> 8, request['dates'][index] & 255
        weekday = call(0x800D5CF8, [year, month, day])
        if weekday > 6: raise ValueError('Invalid native posting weekday')
        return bytes((0, 0, hour, day, weekday, month))+struct.pack('>H', year)

    def cursor(year, index, done=0):
        data = bytearray(globals_before[CURSOR])
        data[1], data[2:4], data[6] = index, struct.pack('>H', year), done
        return bytes(data)

    def fixture(index, flag, *, previous=None, year=2001, level=3):
        state = bytearray(saved)
        state[POSTS-SAVE_RAM:POSTS-SAVE_RAM+1560] = empty*15
        state[0x80129E00-SAVE_RAM:0x80129E06-SAVE_RAM] = b'TownXX'
        old_level = struct.unpack_from('>H', state, 0x80135C12-SAVE_RAM)[0]
        struct.pack_into('>H', state, 0x80135C12-SAVE_RAM, (old_level & 0x3FFF) | level << 14)
        write(SAVE_RAM, state)
        now = rtc_for(index, year)
        write(TIME, now+globals_before[TIME][8:])
        write(TIME+16, bytes(4))  # Read the private common RTC, not the hardware clock.
        previous = previous if previous is not None else ((year, index-1) if index else (year-1, 38))
        write(CURSOR, cursor(*previous))
        write(capital, words(flag))
        write(MODULE_RAM+56, globals_before[MODULE_RAM+56])
        call(0x800C165C, expected=level)
        return bytes(state), now, previous

    def verify_after(before, posts, now, last, done):
        expected = bytearray(before)
        expected[POSTS-SAVE_RAM:POSTS-SAVE_RAM+len(posts)*104] = b''.join(posts)
        if done: expected[CHECKED-SAVE_RAM:CHECKED-SAVE_RAM+8] = now
        check('only complete board posts and native checked time change saved payload', SAVE_RAM, bytes(expected))
        check('pending common cursor advances only through published prefix', CURSOR, cursor(*last, done))
        check('native free fields remain unchanged', 0x80140680, globals_before[0x80140680])
        check('creator session detaches', session, bytes(4))
        call(0x8009C0C0, [metrics, metrics+4, metrics+8])
        check('seasonal creator releases allocation', metrics, heap)

    for index in range(39):
        for flag in (0, 1):
            expected_record = value(0x1A4+index, flag)
            before, now, previous = fixture(index, flag)
            call(0x800A65C4)
            verify_after(before, [pack(expected_record)+now], now, (2001, index), 1)
            completed += 1
            record({'native_seasonal_complete': index, 'template': 0x1A4+index, 'capital': flag,
                    'wire': read(POSTS, 96).hex(), 'passed': True})

    # Both translated but unscheduled identities still pass through the real
    # cartridge loader. Do not invent a native event that selects these IDs.
    for number in (0x1CB, 0x1CC):
        for flag in (0, 1):
            expected_record = value(number, flag)
            write(descriptor, struct.pack('>4sHHBBBB', b'AFNS', number, 2001, 0, 0, 0, 243))
            write(output, b'!'*164); write(capital, words(flag))
            before = read(SAVE_RAM, SAVE_BYTES)
            call(loader, [output, player, descriptor, 0, 0, 0], output)
            check('unscheduled complete creator output', output, pack(expected_record)+bytes(68))
            check('direct creation does not publish a fictitious event', SAVE_RAM, before)
            direct_cases += 1
            record({'native_seasonal_direct': number, 'capital': flag, 'passed': True})

    # Fail each possible position in a five-post backlog. Earlier successful
    # posts stay published; retry must append exactly the remaining suffix.
    last_index = 10
    expected_posts = [pack(value(0x1A4+i, 1))+rtc_for(i) for i in range(6, 11)]
    for failed_position in range(5):
        before, now, previous = fixture(last_index, 1, previous=(2001, 5))
        seen = 0
        def entering(registers):
            nonlocal seen
            if registers[31] != 0x800A6780: raise ValueError('Unexpected seasonal bridge caller')
            check('native pending list chooses the expected next ID', registers[29]+16, words(0x1AA+seen))
            if seen == failed_position:
                broken = config[:]; broken[6] ^= 1
                write(MODULE_RAM+0x48, words(*broken))
            seen += 1
        def returned(registers):
            if bool(registers[2]) != (seen-1 != failed_position):
                raise ValueError('Seasonal bridge returned the wrong completion result')
        traced_call(debug, 0x800A65C4, {0x800A6384: entering, 0x800A6780: returned},
                    lambda row: record({key.replace('treasure_', 'seasonal_'): v for key, v in row.items()}),
                    rearm={0x800A6384: (0x800A6780,), 0x800A6780: (0x800A6384,)})
        if seen != failed_position+1: raise ValueError('Seasonal failure did not stop pending publication')
        verify_after(before, expected_posts[:failed_position], now, (2001, 5+failed_position), 0)
        write(MODULE_RAM+0x48, words(*config))
        call(0x800A65C4)
        verify_after(before, expected_posts, now, (2001, last_index), 1)
        prefix_failures += 1
        record({'native_seasonal_pending_failure': failed_position, 'retry_completed': True, 'passed': True})

    for at, value in request['guards'].items(): check('seasonal code retained after batch', int(at, 16), bytes.fromhex(value))
    for at in edges: check('seasonal scratch and stack guard', at, EDGE)
    check('resident module guard', GUARD_ADDRESS, words(*([GUARD_WORD]*4)))
    write(SAVE_RAM, saved); check('complete saved payload restored', SAVE_RAM, saved)
    for at, value in globals_before.items():
        write(at, value); check('seasonal global restored', at, value)
    call(0x8009C040, [allocation])
    return {'native_seasonal_cases': completed, 'native_seasonal_direct_cases': direct_cases,
            'native_seasonal_prefix_failures': prefix_failures, 'seasonal_assertions': assertions,
            'actual_calendar_and_scheduler': True, 'pending_retry_across_save': False,
            'debugger_uploaded_creator_bytes': 0, 'full_reader_executed': False,
            'normal_gameplay': False, 'save_io_tested': False, 'hardware_verified': False,
            'requires_checkpoint_restore': True}
