"""Batched isolated calls through the real relocated resident-date preparers."""

import calendar
import struct

from aflib import sha256
from dialogue_dates import SPEC, patch, relocated
from flash_mail import SAVE_RAM, SAVE_BYTES
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from textcodec import tokenize

EDGE = b'EDGE'*4
WINDOW, RTC_YEAR = 0x80142410, 0x80136FC2


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
    saved, rtc = read(SAVE_RAM, SAVE_BYTES), read(RTC_YEAR, 2)
    size = 16+SPEC.resident_bytes+len(reloc)+16+0x460+16
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Dialogue date fixture allocation failed')
    base = allocation+16
    data = base+SPEC.resident_bytes+len(reloc)+16
    cursor, date_source, date_result = data+0x420, data+0x430, data+0x440
    guard_addresses = (allocation, data-16, data+0x410, allocation+size-16,
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
    write(RTC_YEAR, rtc)
    check('complete saved game retained', SAVE_RAM, saved)
    check('original clock year restored', RTC_YEAR, rtc)
    check('complete overlay code retained', base, proof[1])
    for address in guard_addresses:
        check('heap and call-stack guard', address, EDGE)
    check('resident module guard', GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
    call(0x8009C040, [allocation])
    return {'dialogue_date_preparations': prepared, 'calendar_conversions': conversions,
            'message_loads': message_loads, 'date_insertions': insertions,
            'allocation_freed': f'{allocation:08X}', 'normal_gameplay': False,
            'requires_checkpoint_restore': True}
