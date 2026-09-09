#!/usr/bin/env python3
"""Source-bound complete English seasonal notices, before runtime installation."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from audit_mail_templates import template_fields
from mail_catalog import parse, verify_registered
from mail_format import Templates, format_letter
from mail_record import Field, Record
from notice_record import pack, unpack
from textbanks import banks

ROOT = Path(__file__).resolve().parents[1]
IDS = tuple(range(0x1A4, 0x1CD))
# Native identity -> complete supplied English reference identity. None means
# the event/report has no matching supplied English notice and needs new text.
REFERENCES = (
    0x1A4, 0x1A5, 0x1A7, 0x1A8, None, None, None, 0x1AD, 0x1AA, 0x1AB,
    0x1AC, None, 0x1AF, 0x1B0, 0x1B1, 0x1C6, 0x1B4, 0x1B6, 0x1B7, 0x1B3,
    0x1B5, 0x1B9, 0x1BA, 0x1BB, None, 0x1BC, 0x1BD, 0x1BE, 0x1BF, 0x1C0,
    0x1C1, 0x1C2, 0x1C3, 0x1C5, 0x1C6, 0x1C7, 0x1C8, 0x1C9, 0x1CA, 0x1CB, 0x1CC,
)
GUARDS = (
    (0x800A62EC, 0x800A6384, 'd9161af69605e3ee99b18a25599e2ba99a135d9d661120272f6f35f3fc0d74a4'),
    (0x800A6384, 0x800A63F8, '9482556995c89177e926528712e92986898a0d1084728724bbcf58e86dca89b7'),
    (0x800A63F8, 0x800A6450, '847c122e25e72cc5c2477516bf64e112781ba26ea43ec8ba7398991e753c2d1b'),
    (0x800A6450, 0x800A6548, '9f12ff7112a0434ded5c01429209f010e732590b88dcba846a994398e7c9340c'),
    (0x800A65C4, 0x800A680C, '67baf9ff771aac46d968dd194e7e1b86778430bb487e384fc4aa8818714af69a'),
    (0x8010B4B0, 0x8010B4FE, '830dbaa425398fe878620c8b9538bd54b2d88cdf2ab437030aedc768c99d0b0e'),
    (0x8010B504, 0x8010B50C, 'af02223a300e629a3cd5963c3adb74804b363041f83cbf29acf2b805f95f4ae3'),
)

# Only these source-bound changes are applied to matched references. All other
# words, spaces, glyph pairs, and manual breaks remain supplied English text.
EDITS = {
    0x1AB: ((b'wishing well', b'shrine'),),
    0x1AD: ((b"will be held on the vernal\xcd" b"equinox. Stop by the wishing\xcd" b"well to watch the day's",
             b"will be held on April 20th.\xcd" b"Stop by the shrine plaza\xcd" b"to watch the day's"),),
    0x1B0: ((b'late June', b'mid-June'),),
    0x1B3: ((b'Fall Fishing Tourney', b'Summer Fishing Tourney'),),
    0x1B5: ((b'wishing well', b'shrine'),),
    0x1B6: ((b'wishing well', b'shrine'),),
    0x1BA: ((b'Join us \x7f\x26', b'Join us by the lake \x7f\x26'),),
    0x1BD: ((b'Pete', b'Pelly'),),
    0x1BE: ((b'wishing well', b'shrine'),),
    0x1C5: ((b'and dusk. Take care not to\xcd' b'catch an early winter cold!',
             b'and dusk. Flowers and grass\xcd' b'may suffer in the cold.'),),
    0x1C7: ((b'A fierce cold front is fast\xcd' b'approaching ',
             b'A fierce cold front arrives\xcd' b'tomorrow in '),),
    0x1CA: ((b'wishing well', b'shrine'),),
}


def lines(value): return value.replace(b'\n', b'\xcd')


# Original translations retain native-specific event, speaker, item, and date
# facts. Matched rewrites retain the useful donor framing where possible.
WRITTEN = {
    0x1A8: lines(b"It's almost Doll Festival!\nOur lovely hinaningyo are\n"
                 b"on display now! Miss this\nchance, and you'll have to\n"
                 b"wait until next year, hm?\n              \x7f\x25\n"),
    0x1A9: lines(b"White Day is two weeks away!\nIf your mailbox is full,\n"
                 b"your boyfriend's gift may be\nreturned! Don't forget to\n"
                 b"make some room for it!\n     Pelly, Post Office\n"),
    0x1AA: lines(b"    Blossom Forecast\nWarmer days are swelling\n"
                 b"the buds! Blossoms should be\nabout 70% open by April 1st,\n"
                 b"and at their best around\nthe 5th.\n"),
    0x1AC: lines(b"Attention, residents of\n\x7f\x24! The Spring\n"
                 b"Sports Fair is almost here!\nI'll be joining the aerobics,\n"
                 b"so let's all do our best!\n                    Copper\n"),
    0x1AF: lines(b"Children's Day is almost\nhere! Our lucky samurai suits\n"
                 b"are on display now! Don't\nmiss this chance to pick one\n"
                 b"up for the occasion, hm?\n              \x7f\x25\n"),
    0x1B7: lines(b"  \x80\x2aFireworks Festival\x80\x2a\nJoin us every Saturday in\n"
                 b"August! The fireworks start\nat 7:00 p.m. Summer just\n"
                 b"wouldn't be the same without\nthese colourful displays!\n"),
    0x1BC: lines(b"   Thirteenth-Night Moon\n\nOn \x7f\x27 at 6:00 p.m.,\n"
                 b"take your time and enjoy\nanother quiet evening of\nmoon viewing.\n"),
    0x1C8: lines(b"Happy holidays, everybody!\nJingle here! I'll deliver\n"
                 b"presents on Christmas Eve!\nLeave room in your mailbox,\n"
                 b"and don't get in my way\nwhile I'm working, OK?\n"),
}
REASONS = {
    0x1A8: 'Native Doll Festival stock notice; retain the approved hinaningyo item identity.',
    0x1A9: 'Native White Day mailbox reminder from Pelly, not a blossom notice.',
    0x1AA: 'Native blossom forecast retains April 1st, seventy percent, and peak around the fifth.',
    0x1AC: 'Retain Copper as the speaker and his participation in aerobics.',
    0x1AD: 'Native Spring Sports Fair is April 20th at the shrine, not the vernal equinox.',
    0x1AF: 'Native Children\'s Day stock notice; retain the approved samurai suit item identity.',
    0x1B0: 'The native report predicts rainy season in mid-June, not late June.',
    0x1B3: 'The native summer tournament still has its final Sunday ahead; do not announce completion.',
    0x1B7: 'Native fireworks are every Saturday in August at 7 p.m., not July 4th or a station anniversary.',
    0x1BA: 'Retain the native lakeside venue and complete field-two lunar date.',
    0x1BC: 'Retain the second moon-viewing event and its independent field-three lunar date.',
    0x1BD: 'The native postal speaker is Pelly, not Pete.',
    0x1C5: 'Retain the native warning about cold damage to grass and flowers.',
    0x1C7: 'The native heavy-snow forecast explicitly concerns tomorrow.',
    0x1C8: 'Retain Christmas Eve, the native mailbox reminder, and not interrupting Jingle at work.',
}


def reviewed_templates(native, catalog):
    native = verified_rom(native)
    if verify_registered(catalog)['catalog'] != 4: raise ValueError('Seasonal text requires glyph catalogue four')
    code = by_vrom(native)[CODE_VROM].extract(native)
    for lo, hi, digest in GUARDS:
        if sha256(code[lo-CODE_RAM:hi-CODE_RAM]) != digest:
            raise ValueError('Changed native seasonal schedule or field helper')
    source = {b.name: b.entries() for b in banks(native) if b.name in ('super', 'mail', 'ps')}
    reference = parse(catalog)[1]
    dates = struct.unpack_from('>39H', code, 0x8010B4B0-CODE_RAM)
    result = []
    for number, donor in zip(IDS, REFERENCES, strict=True):
        before = b'' if donor is None else reference['mail'][donor]
        if donor is not None and (reference['super'][donor] != b'\xcd' or reference['ps'][donor]):
            raise ValueError('Unexpected seasonal reference header/footer')
        body = WRITTEN.get(number, before)
        for old, new in EDITS.get(number, ()):
            if body.count(old) != 1: raise ValueError(f'Changed seasonal adaptation span {number:04X}')
            body = body.replace(old, new, 1)
        fields = tuple(sorted(template_fields(source['mail'][number])))
        if tuple(sorted(template_fields(body, extended_glyphs=True))) != fields:
            raise ValueError(f'Seasonal fields changed meaning at {number:04X}')
        if not body or len(body) > 1024: raise ValueError('Invalid complete seasonal body')
        unchanged = body == before
        result.append({'template': number, 'reference': donor, 'fields': fields,
                       'source_sha256': sha256(source['mail'][number]),
                       'reference_encoded_sha256': sha256(before) if donor is not None else None,
                       'body_sha256': sha256(body), 'body': body.hex(),
                       'reference_unchanged': unchanged,
                       'provenance': 'supplied English reference' if unchanged else
                                     'original translation' if donor is None else 'native-specific reference adaptation',
                       'reason': REASONS.get(number, 'Retain the native shrine venue.' if not unchanged else
                                            'Matched native meaning; retain complete supplied wording and manual layout.'),
                       'posting_month_day': dates[number-IDS[0]] if number < 0x1CB else None})
    return result


def complete_body(record, approved):
    pack(record)
    if (record.catalog != 4 or record.kind or record.templates != (approved['template'],)
            or tuple(i for i, _ in record.fields) != tuple(approved['fields'])):
        raise ValueError('Changed seasonal saved identity or fields')
    for index, field in record.fields:
        limit = 6 if index == 0 else 16 if index == 1 else 14
        if (field.article or not 1 <= len(field.text) <= limit or not field.text.rstrip(b' ')
                or any(c in field.text for c in (0x7F, 0x80, 0xCD))):
            raise ValueError('Invalid complete seasonal field')
    body = bytes.fromhex(approved['body'])
    if sha256(body) != approved['body_sha256']: raise ValueError('Changed reviewed seasonal body')
    letter = format_letter(record, Templates(4, 0, record.templates*3, (b'\xcd', body, b'')))
    if letter.header or letter.footer: raise ValueError('Unexpected seasonal mail sections')
    return letter.body


def audit(native, catalog):
    templates = reviewed_templates(native, catalog)
    samples = {0: Field(b'TownXX'), 1: Field(b'ABCDEFGHIJKLMNOP'),
               2: Field(b'September 30th'), 3: Field(b'September 30th'), 4: Field(b'October 14th')}
    cases = []
    for entry in templates:
        for capital in (False, True):
            value = Record(4, 0, (entry['template'],), tuple((i, samples[i]) for i in entry['fields']), capital)
            wire = pack(value)
            if unpack(wire, expected_catalog=4) != value: raise ValueError('Seasonal record loses complete fields')
            body = complete_body(value, entry)
            cases.append({'template': entry['template'], 'capital': int(capital),
                          'wire': wire.hex(), 'body': body.hex(), 'body_bytes': len(body)})
    return {'templates': templates, 'cases': cases, 'installed': False,
            'status': 'Complete reviewed wording and source-model records; native creation, dates, reader, and publication remain'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-seasonal/review.json')
    args = parser.parse_args()
    result = audit((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                   (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'reviewed_bodies': len(result['templates']), 'complete_model_cases': len(result['cases']),
                      'unchanged_reference_bodies': sum(e['reference_unchanged'] for e in result['templates']),
                      'original_bodies': sum(e['reference'] is None for e in result['templates']), 'installed': False}))


if __name__ == '__main__': main()
