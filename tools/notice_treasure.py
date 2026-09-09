"""Independent complete-body model for native treasure notices."""

from audit_notice_treasure import IDS, NATIVE_FIELDS
from mail_record import Record
from mail_format import Templates, format_letter
from notice_record import pack

HEADING = b"\x7f\x29's Treasure Hunt!\xcdCome and join the fun! Woo!\xcd"
DONOR_HEADING = b'Free \x7f\x74\x7f\x26\xcdfor whoever finds it! Woo!\xcd'


def fields_for(number):
    if number not in IDS: raise ValueError('Unapproved treasure template')
    return (2, 4) if number == 0x1FE else NATIVE_FIELDS[number-0x1F0]


def valid(record):
    if not isinstance(record, Record) or record.catalog != 4 or record.kind or len(record.templates) != 1:
        raise ValueError('Unapproved treasure record')
    if tuple(i for i, _ in record.fields) != fields_for(record.templates[0]):
        raise ValueError('Changed native treasure clue fields')
    for index, field in record.fields:
        if (not 1 <= len(field.text) <= 16 or not field.text.rstrip(b' ')
                or any(code in field.text for code in (0x7F, 0x80, 0xCD))
                or (index != 2 and field.article)):
            raise ValueError('Invalid complete treasure field')
        if index in (3, 4) and (len(field.text) != 1 or not ord('1') <= field.text[0] <= ord('6' if index == 3 else '5')):
            raise ValueError('Treasure acre must retain its native numeric coordinate')
        if index == 5 and len(field.text) > 6:
            raise ValueError('Treasure town must retain its native identity')
    return pack(record)


def body(record, catalog_banks):
    valid(record)
    number = record.templates[0]
    parts = tuple(catalog_banks[name][number] for name in ('super', 'mail', 'ps'))
    if parts[0] != b'\xcd' or parts[2]: raise ValueError('Changed treasure mail sections')
    if number == 0x1F4:
        if not parts[1].startswith(DONOR_HEADING): raise ValueError('Changed native-specific clue adaptation span')
        parts = (parts[0], HEADING+parts[1][len(DONOR_HEADING):], parts[2])
    letter = format_letter(record, Templates(4, 0, (number,)*3, parts))
    if letter.header or letter.footer: raise ValueError('Treasure body has unexpected mail sections')
    return letter.body
