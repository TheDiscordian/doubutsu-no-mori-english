"""Batched isolated calls through the real relocated resident-date preparers."""

import calendar
import struct

from aflib import sha256
from dialogue_dates import SPEC, patch, relocated
from flash_mail import SAVE_RAM, SAVE_BYTES
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from textcodec import tokenize

EDGE = b'EDGE'*4
WINDOW, RTC_YEAR, RTC_START = 0x80142410, 0x80136FC2, 0x80136FB8
QUIZ_DATES = ((2000, 2, 5), (2001, 5, 23), (2004, 2, 29),
              (2026, 9, 8), (2030, 8, 15), (2032, 12, 31))


def ordinal(day):
    suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return (str(day)+suffix).encode('ascii')


def exercise(debug, request, record):
    read = debug.read_memory

    def write(address, value):
        debug.write_memory(address, value)
        record({'dialogue_date_write': f'{address:08X}', 'bytes': len(value), 'sha256': sha256(value)})

    def check(label, address, expected):
        actual = read(address, len(expected))
        record({'dialogue_date_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError(f'Dialogue date {label}: {actual.hex()} != {expected.hex()}')

    def call(address, arguments, expected=None, proof=None):
        result = debug.call(f'{address:08X}', arguments, verified_code=proof)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Dialogue date native return differs')
        return result['return_value']

    original, reloc = bytes.fromhex(request['source']), bytes.fromhex(request['relocation'])
    module = request['module']
    patch(original, reloc, module)
    for address, value in request['guards'].items():
        check('unchanged original consumer/converter', int(address, 16), bytes.fromhex(value))
    check('complete resident leap-month literal', int(module['symbols']['af_leap_month'], 16), b'leap month')
    saved, rtc = read(SAVE_RAM, SAVE_BYTES), read(RTC_START, 16)
    original_orders_pointer = read(0x80104A70, 4)
    size = 16+SPEC.resident_bytes+len(reloc)+16+0x900+16
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Dialogue date fixture allocation failed')
    base = allocation+16
    data = base+SPEC.resident_bytes+len(reloc)+16
    cursor, date_source, date_result = data+0x420, data+0x430, data+0x440
    manager, orders = data+0x470, data+0x690
    guard_addresses = (allocation, data-16, data+0x410, allocation+size-16,
                       manager-16, manager+0x200, orders-16, orders+216,
                       TEST_STACK-0x800, TEST_STACK+0x30)
    for address in guard_addresses:
        write(address, EDGE)
    call(0x800262D0, [SPEC.vrom, SPEC.vrom+SPEC.file_bytes, SPEC.ram,
                     SPEC.ram+SPEC.resident_bytes, base, base+SPEC.resident_bytes, len(reloc)],
         proof=(0x800262D0, bytes.fromhex(request['loader'])))
    loaded = relocated(original, reloc, module, base)
    check('complete native cartridge relocation and BSS', base, loaded)
    proof = (base, loaded[:SPEC.sections[0]])
    fields_start = WINDOW+0x38
    scratch = base+0x80921E08-SPEC.ram
    prepared = 0
    for offset, values, format_value in (
            (0x8091D954, (0, 1901, 2000, 2026, 2099, 2100),
             lambda value: str(value if 1901 <= value <= 2099 else 2000).encode('ascii')),
            (0x8091D9B8, range(14),
             lambda value: calendar.month_name[value if 1 <= value <= 12 else 1].encode('ascii')),
            (0x8091DA1C, range(33), lambda value: ordinal(value if 1 <= value <= 31 else 1))):
        for value in values:
            slot = prepared % 20
            write(fields_start, b'X'*200)
            call(base+offset-SPEC.ram, [value, slot], proof=proof)
            output = format_value(value).ljust(10, b' ')
            expected = b'X'*(slot*10)+output+b'X'*((19-slot)*10)
            check('one complete prepared date field; other rows retained', fields_start, expected)
            check('ten-byte native preparation buffer', scratch, output)
            prepared += 1
    conversions = 0
    # These years are inside the original native calendar table. Compare the
    # unchanged conversion directly before checking the helper's English fields.
    cases = [(year, 8, 15, False) for year in (2000, 2001, 2004, 2026, 2030, 2032)]
    cases += [(year, 9, 13, False) for year in (2000, 2001, 2004, 2026, 2030, 2032)]
    cases.append((2001, 5, 23, True))  # Native table's leap-month start.
    last_values = {}
    for year, month, day, reverse in cases:
        converter = 0x800D6218 if reverse else 0x800D60E4
        write(RTC_YEAR, struct.pack('>H', year))
        source_date = struct.pack('>HBB', year, month, day)
        write(date_source, source_date)
        write(date_result, b'!'*4)
        call(converter, [date_result, date_source], 1)
        converted_year, converted_month, converted_day = struct.unpack('>HBB', read(date_result, 4))
        if not 2000 <= converted_year <= 2033 or not 1 <= converted_month <= 13 or not 1 <= converted_day <= 31:
            raise ValueError('Native calendar produced an invalid date')
        if reverse and (converted_month, converted_day) != (13, 1):
            raise ValueError('Native leap-month fixture did not reach the leap branch')
        expected_month = b'leap month' if converted_month == 13 else calendar.month_name[converted_month].encode('ascii')
        expected_day = ordinal(converted_day)
        write(fields_start, b'X'*200)
        call(base+0x8091EBB8-SPEC.ram, [converter, 16, 17, month, day], proof=proof)
        check('complete converted date fields and unchanged neighbours', fields_start,
              b'X'*160+expected_month.ljust(10, b' ')+expected_day.ljust(10, b' ')+b'X'*20)
        check('conversion input retained', date_source, source_date)
        check('calendar preparation retains the current year', RTC_YEAR, struct.pack('>H', year))
        if not reverse and month == 8:
            last_values[year] = expected_month, expected_day
        record({'dialogue_date_conversion': [year, month, day], 'reverse': reverse,
                'native_output': [converted_year, converted_month, converted_day], 'passed': True})
        conversions += 1
    write(WINDOW+12, struct.pack('>I', data))
    message_loads, insertions = 0, 0
    for number, raw in request['messages'].items():
        if number == '246D':
            continue
        entry = bytes.fromhex(raw)
        for year in ((2001, 2026) if number in ('11AC', '180B') else (2026,)):
            write(RTC_YEAR, struct.pack('>H', year))
            call(base+0x8091EBB8-SPEC.ram, [0x800D60E4, 16, 17, 8, 15], proof=proof)
            call(0x8009E558, [data, int(number, 16), 0], 1)
            check('complete festival message from cartridge', data,
                  struct.pack('>4I', 1, int(number, 16), len(entry), 0)+entry)
            expected = entry
            for command, value in zip((0x3C, 0x3D), last_values[year]):
                tokens = [t for t in tokenize(expected, request['info']) if t.kind == 'cmd' and t.data[1] == command]
                for token in reversed(tokens):
                    write(cursor, struct.pack('>I', token.offset))
                    write(WINDOW+0x28C, bytes(4))
                    call(0x800A21C0, [WINDOW, cursor], 0)
                    expected = expected[:token.offset]+value+expected[token.offset+2:]
                    check('complete native calendar insertion', data,
                          struct.pack('>4I', 1, int(number, 16), len(expected), 0)+expected)
                    check('retained insertion cursor', cursor, struct.pack('>I', token.offset))
                    insertions += 1
            message_loads += 1
    # The quiz's 0C request writes quest row nine, slot seven. The real demo
    # dispatcher reads manager +1AC/+1AE, not the reminder routine's field slots.
    quiz = bytes.fromhex(request['messages']['246D'])
    if quiz[:5] != bytes.fromhex('7F0C070001'):
        raise ValueError('Old-calendar quiz must retain its complete native request')
    write(0x80104A70, struct.pack('>I', orders))
    quiz_cases = 0
    for year, month, day in QUIZ_DATES:
        current_rtc = bytearray(rtc)
        current_rtc[7], current_rtc[9] = day, month
        struct.pack_into('>H', current_rtc, RTC_YEAR-RTC_START, year)
        write(RTC_START, current_rtc)
        expected_fields = bytearray(b'X'*200)
        for converter, source_month, source_day, slot in (
                (0x800D60E4, 8, 15, 11), (0x800D60E4, 9, 13, 13),
                (0x800D6218, month, day, 15)):
            source_date = struct.pack('>HBB', year, source_month, source_day)
            write(date_source, source_date)
            write(date_result, b'!'*4)
            call(converter, [date_result, date_source], 1)
            converted = struct.unpack('>HBB', read(date_result, 4))
            if not 2000 <= converted[0] <= 2033 or not 1 <= converted[1] <= 13 or not 1 <= converted[2] <= 31:
                raise ValueError('Calendar-order fixture received an invalid conversion')
            output_month = b'leap month' if converted[1] == 13 else calendar.month_name[converted[1]].encode('ascii')
            output_day = ordinal(converted[2])
            expected_fields[slot*10:(slot+2)*10] = output_month.ljust(10, b' ')+output_day.ljust(10, b' ')
            check('calendar-order conversion source retained', date_source, source_date)
            if slot == 15 and (year, month, day) == (2001, 5, 23) and converted[1:] != (13, 1):
                raise ValueError('Calendar-order fixture misses the native leap month')
        call(0x8009E558, [data, 0x246D, 0], 1)
        check('complete old-calendar quiz from cartridge', data, struct.pack('>4I', 1, 0x246D, len(quiz), 0)+quiz)
        write(orders, b'X'*216)
        write(cursor, bytes(4))
        call(0x800A21C0, [WINDOW, cursor], 0)
        expected_orders = bytearray(b'X'*216)
        expected_orders[16+9*20+7*2:16+9*20+7*2+2] = b'\0\1'
        check('complete quest request table; only calendar value changes', orders, expected_orders)
        check('calendar request advances exactly five bytes', cursor, struct.pack('>I', 5))
        state = bytearray(0x200)
        struct.pack_into('>HH', state, 0x1AC, 7, 1)
        write(manager, state)
        write(fields_start, b'X'*200)
        call(base+0x809215E4-SPEC.ram, [manager], proof=proof)
        check('actual order dispatcher prepares fields eleven through sixteen', fields_start, expected_fields)
        check('calendar dispatch retains the complete manager', manager, state)
        check('calendar dispatch retains the complete current clock', RTC_START, current_rtc)
        expected = quiz
        for command, value in ((0x3B, output_month), (0x3C, output_day)):
            tokens = [t for t in tokenize(expected, request['info']) if t.kind == 'cmd' and t.data[1] == command]
            if len(tokens) != 1:
                raise ValueError('Old-calendar quiz must use each exact free field once')
            token = tokens[0]
            write(cursor, struct.pack('>I', token.offset))
            write(WINDOW+0x28C, bytes(4))
            call(0x800A21C0, [WINDOW, cursor], 0)
            expected = expected[:token.offset]+value+expected[token.offset+2:]
            check('complete old-calendar native field insertion', data,
                  struct.pack('>4I', 1, 0x246D, len(expected), 0)+expected)
            check('old-calendar insertion cursor retained', cursor, struct.pack('>I', token.offset))
            insertions += 1
        record({'calendar_quiz_current_date': [year, month, day],
                'month': output_month.decode(), 'day': output_day.decode(), 'passed': True})
        quiz_cases += 1
        message_loads += 1
    for value in (0, 2):
        state = bytearray(0x200)
        struct.pack_into('>HH', state, 0x1AC, 7, value)
        write(manager, state)
        write(fields_start, b'X'*200)
        call(base+0x809215E4-SPEC.ram, [manager], proof=proof)
        check('non-one calendar order leaves all free fields unchanged', fields_start, b'X'*200)
        check('non-one calendar order retains complete manager', manager, state)
    write(0x80104A70, original_orders_pointer)
    check('original actor-order pointer restored', 0x80104A70, original_orders_pointer)
    write(RTC_START, rtc)
    check('complete saved game retained', SAVE_RAM, saved)
    check('complete original clock restored', RTC_START, rtc)
    check('complete overlay code retained', base, proof[1])
    for address in guard_addresses:
        check('heap and call-stack guard', address, EDGE)
    check('resident module guard', GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
    call(0x8009C040, [allocation])
    return {'dialogue_date_preparations': prepared, 'calendar_conversions': conversions,
            'message_loads': message_loads, 'date_insertions': insertions,
            'calendar_quiz_cases': quiz_cases, 'calendar_quiz_direct_conversions': quiz_cases*3,
            'calendar_noop_orders': 2,
            'allocation_freed': f'{allocation:08X}', 'normal_gameplay': False,
            'requires_checkpoint_restore': True}
