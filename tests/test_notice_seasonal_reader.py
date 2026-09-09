"""Complete seasonal reader pages plus retained initial/treasure behaviour."""

import ctypes as C
from dataclasses import replace
import unittest

import test_notice_treasure_reader as treasure
from test_notice_reader import ROOT, initial_body
from mail_record import Field, Record
from notice_record import pack
from notice_seasonal import compiled_resource, complete_body


class SeasonalReaderTests(treasure.NoticeTreasureReaderTests):
    reader_source = 'overlays/notice/reader_seasonal.c'
    extra_sources = ('runtime/notice/treasure.c', 'runtime/notice/seasonal.c')

    def cached(self, slot=4):
        # A changed slot can have an older snapshot in the other cache. Match
        # the same complete identity that the real reader uses, not just its pointer.
        return next(c for c in self.cache if c.status
                    and c.source == C.addressof(self.posts)+slot*104
                    and bytes(c.saved) == bytes(self.posts[slot*104:slot*104+96]))

    @classmethod
    def generated_compile_flags(cls, directory):
        resource = compiled_resource((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                     (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes())
        (directory/'seasonal_data.h').write_text(resource['header'])
        cls.entries = {e['template']: e for e in resource['templates']}
        return ['-I'+str(directory)]

    def seasonal_record(self, number, capital=False):
        samples = {0: Field(b'TownXX'), 1: Field(b"Nookington's    "),
                   2: Field(b'September 30th'), 3: Field(b'October 31st'), 4: Field(b'October 14th')}
        return Record(4, 0, (number,), tuple((i, samples[i]) for i in self.entries[number]['fields']), capital)

    def seasonal_complete(self, value):
        self.put(4, pack(value))
        saved = bytes(self.posts)
        self.lib.af_notice_construct(1)
        collected = self.draw(4)
        cache = self.cached()
        expected = complete_body(value, self.entries[value.templates[0]])
        self.assertEqual(cache.status, 2)
        self.assertEqual(bytes(cache.body.text), expected.ljust(1024, b'\0'))
        self.assertEqual(cache.body.length, len(expected))
        for page in range(1, cache.layout.total):
            self.control(0x10)
            self.assertEqual(cache.page, page)
            collected += self.draw(4)
        self.assertEqual(b''.join(collected), expected.replace(b'\xcd', b''))
        self.control(0x10)
        self.assertEqual(cache.page, cache.layout.total-1)
        self.assertEqual(bytes(self.posts), saved)

    def test_all_41_seasonal_bodies_and_capitals_have_complete_reachable_pages(self):
        for number in self.entries:
            for capital in (False, True): self.seasonal_complete(self.seasonal_record(number, capital))
        self.assertEqual(self.number('af_mail_catalog_reads').value, 0)
        self.assertEqual(self.number('af_notice_allocations').value, self.number('af_notice_releases').value)

    def test_manual_and_all_three_automatic_types_share_cache_without_editing_saved_bytes(self):
        values = [Record(4, 0, (0x21,), ()), self.record(0x1F4), self.seasonal_record(0x1BC)]
        expected = [initial_body(values[0], self.banks), treasure.body(values[1], self.banks),
                    complete_body(values[2], self.entries[0x1BC])]
        for value, body in zip(values, expected):
            self.put(4, pack(value)); self.put(5, b'Manual post'.ljust(96, b' '))
            before = bytes(self.posts)
            self.draw(4)
            self.assertEqual(bytes(self.cached().body.text[:len(body)]), body)
            self.assertEqual(self.draw(5), [b'Manual post'])
            self.assertEqual(bytes(self.posts), before)

    def test_seasonal_allocation_failure_retains_record_and_reopen_recovers(self):
        for number in (0x1A4, 0x1A8, 0x1BA, 0x1BC, 0x1BE):
            value = self.seasonal_record(number, True)
            self.put(4, pack(value)); self.lib.af_notice_construct(1)
            saved = bytes(self.posts)
            self.number('af_notice_fail_allocate').value = 1
            error = [b'Unable to read this post.', b'Close and reopen to retry.']
            self.assertEqual(self.draw(4), error)
            self.number('af_notice_fail_allocate').value = 0
            self.assertEqual(self.draw(4), error)
            self.assertEqual(bytes(self.posts), saved)
            self.seasonal_complete(value)

    def test_wrong_seasonal_field_mask_and_date_control_never_draw_raw_saved_envelope(self):
        value = self.seasonal_record(0x1BC)
        for bad in (replace(value, fields=()), replace(value, templates=(0x1CD,)),
                    replace(value, fields=((3, Field(b'\xCD')),)),
                    replace(value, fields=((3, Field(b'October 31st', 1)),))):
            self.put(4, pack(bad)); self.lib.af_notice_construct(1)
            before = bytes(self.posts)
            self.assertEqual(self.draw(4), [b'Unable to read this post.', b'Close and reopen to retry.'])
            self.assertEqual(bytes(self.posts), before)


if __name__ == '__main__': unittest.main()
