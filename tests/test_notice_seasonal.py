"""Complete seasonal wording retains N64 identities, dates, speakers, and fields."""

from dataclasses import replace
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from audit_mail_templates import template_fields
from mail_catalog import parse
from mail_record import Field, Record
from notice_record import unpack
from notice_seasonal import IDS, REFERENCES, WRITTEN, EDITS, audit, reviewed_templates, complete_body
from notice_native_layout import rows
from textbanks import banks


@unittest.skipUnless((ROOT/'build/mail-glyph-resources/glyph-catalog.bin').is_file(),
                     'Local original and supplied English resources required')
class SeasonalNoticeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.catalog = (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes()
        cls.report = audit(cls.native, cls.catalog)
        cls.entries = {e['template']: e for e in cls.report['templates']}
        cls.reference = parse(cls.catalog)[1]

    def test_all_native_bodies_and_both_capital_states_are_complete(self):
        self.assertEqual(tuple(self.entries), IDS)
        self.assertEqual(len(self.report['cases']), 82)
        self.assertFalse(self.report['installed'])
        source = next(b for b in banks(self.native) if b.name == 'mail').entries()
        widths = [12]*256
        for code in range(32, 127): widths[code] = 4 if code in b"iIl'" else 6
        for case in self.report['cases']:
            value = unpack(bytes.fromhex(case['wire']), expected_catalog=4)
            entry = self.entries[case['template']]
            self.assertEqual(value.templates, (case['template'],))
            self.assertEqual(value.initial_capital, bool(case['capital']))
            self.assertEqual(entry['fields'], tuple(sorted(template_fields(source[case['template']]))))
            body = bytes.fromhex(case['body'])
            self.assertEqual(complete_body(value, entry), body)
            self.assertEqual(b''.join(line for _, line, _ in rows(body, widths)), body.replace(b'\xcd', b''))
            self.assertTrue(all(width <= 192 for _, _, width in rows(body, widths)))
            self.assertEqual(len(body), case['body_bytes'])
            self.assertTrue(0 < len(body) <= 1024)
        self.assertGreater(max(c['body_bytes'] for c in self.report['cases']), 96)

    def test_reference_matching_is_semantic_not_same_number(self):
        self.assertEqual(sum(e['reference_unchanged'] for e in self.entries.values()), 21)
        self.assertEqual({n for n, e in self.entries.items() if e['reference'] is None},
                         {0x1A8, 0x1A9, 0x1AA, 0x1AF, 0x1BC})
        expected = {0x1A6: 0x1A7, 0x1A7: 0x1A8, 0x1AB: 0x1AD, 0x1AC: 0x1AA,
                    0x1AD: 0x1AB, 0x1AE: 0x1AC, 0x1B1: 0x1B0, 0x1B2: 0x1B1,
                    0x1B3: 0x1C6, 0x1B5: 0x1B6, 0x1B6: 0x1B7, 0x1B7: 0x1B3,
                    0x1B8: 0x1B5, 0x1BD: 0x1BC, 0x1BE: 0x1BD, 0x1BF: 0x1BE,
                    0x1C0: 0x1BF, 0x1C1: 0x1C0, 0x1C2: 0x1C1, 0x1C3: 0x1C2, 0x1C4: 0x1C3}
        for native, donor in expected.items(): self.assertEqual(self.entries[native]['reference'], donor)
        self.assertFalse(set(REFERENCES) & {0x1A6, 0x1B8, 0x1C4, 0x1CD, 0x1CE})

    def test_supplied_layout_is_retained_outside_explicit_native_adaptations(self):
        for number, entry in self.entries.items():
            body = bytes.fromhex(entry['body'])
            if entry['reference_unchanged']:
                self.assertEqual(body, self.reference['mail'][entry['reference']])
            elif number in EDITS:
                before = self.reference['mail'][entry['reference']]
                self.assertEqual(body.count(b'\xcd'), before.count(b'\xcd'))
                for old, new in EDITS[number]:
                    self.assertEqual(before.count(old), 1)
                    before = before.replace(old, new, 1)
                self.assertEqual(body, before)
            else:
                self.assertEqual(body, WRITTEN[number])
                self.assertEqual(body.count(b'\xcd'), 6)

    def test_native_event_dates_venues_mailbox_and_speakers_are_retained(self):
        def body(number): return bytes.fromhex(self.entries[number]['body'])
        checks = {
            0x1A8: (b'Doll Festival', b'hinaningyo'), 0x1A9: (b'White Day', b'Pelly'),
            0x1AA: (b'70%', b'April 1st', b'the 5th'), 0x1AC: (b'aerobics', b'Copper'),
            0x1AD: (b'April 20th', b'shrine'), 0x1AF: (b"Children's Day", b'samurai suits'),
            0x1B0: (b'mid-June',), 0x1B3: (b'This Sunday', b'Summer Fishing Tourney'),
            0x1B7: (b'every Saturday', b'August', b'7:00 p.m.'),
            0x1BA: (b'lake', b'\x7f\x26', b'6:00 p.m.'),
            0x1BC: (b'Thirteenth-Night Moon', b'\x7f\x27', b'6:00 p.m.'),
            0x1BD: (b'Pelly',), 0x1BE: (b'shrine', b'\x7f\x28'),
            0x1C5: (b'Flowers and grass',), 0x1C7: (b'tomorrow',),
            0x1C8: (b'Christmas Eve', b'mailbox'), 0x1CA: (b'shrine',),
        }
        for number, words in checks.items():
            for text in words: self.assertIn(text, body(number))
        all_text = b''.join(body(number) for number in IDS)
        for text in (b'wishing well', b'vernal', b'Groundhog', b'Harvest Festival', b'Meteor Shower', b'July 4th'):
            self.assertNotIn(text, all_text)
        self.assertEqual(self.entries[0x1AC]['posting_month_day'], 0x0408)
        self.assertEqual(self.entries[0x1BF]['posting_month_day'], 0x0A07)
        for number in (0x1CB, 0x1CC): self.assertIsNone(self.entries[number]['posting_month_day'])

    def test_complete_field_bounds_are_rejected_without_truncation(self):
        for number, entry in self.entries.items():
            if not entry['fields']: continue
            index = entry['fields'][0]
            limit = 6 if index == 0 else 16 if index == 1 else 14
            record = Record(4, 0, (number,), ((index, Field(b'X'*limit)),))
            complete_body(record, entry)
            for text in (b'X'*(limit+1), b' ', b'A\xcdB', b'\x80\x2a', b'\x7f\x24'):
                with self.assertRaises(ValueError):
                    complete_body(replace(record, fields=((index, Field(text)),)), entry)
            with self.assertRaises(ValueError):
                complete_body(replace(record, fields=((index, Field(b'X', 1)),)), entry)
            with self.assertRaises(ValueError): complete_body(replace(record, fields=()), entry)

    def test_changed_sources_and_saved_id_are_rejected(self):
        wrong = bytearray(self.native); wrong[100] ^= 1
        with self.assertRaises(ValueError): reviewed_templates(bytes(wrong), self.catalog)
        wrong = bytearray(self.catalog); wrong[-1] ^= 1
        with self.assertRaises(ValueError): reviewed_templates(self.native, bytes(wrong))
        entry = self.entries[0x1A4]
        for record in (Record(4, 0, (0x1A5,), ()), Record(4, 0, (0x1A4,), ((0, Field(b'X')),))):
            with self.assertRaises(ValueError): complete_body(record, entry)
        value = Record(4, 0, (0x1A4,), ())
        with self.assertRaises(ValueError): complete_body(value, {**entry, 'body': '414243'})


if __name__ == '__main__': unittest.main()
