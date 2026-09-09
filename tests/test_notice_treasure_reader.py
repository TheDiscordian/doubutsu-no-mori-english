"""Combined reader routes, complete treasure pages, caching, and failure recovery."""

import ctypes as C
from dataclasses import replace
import unittest

import test_notice_reader as reader
from mail_record import Record, Field
from notice_record import pack
from notice_treasure import IDS, body, fields_for


class NoticeTreasureReaderTests(reader.NoticeReaderTests):
    reader_source = 'overlays/notice/reader_treasure.c'
    extra_sources = ('runtime/notice/treasure.c',)

    def record(self, number, capital=False, article=1):
        samples = {1: Field(b'ABCDEFGHIJKLMNOP'), 2: Field(b'abcdefghijklmnop', article),
                   3: Field(b'6'), 4: Field(b'5'), 5: Field(b'town  ')}
        return Record(4, 0, (number,), tuple((i, samples[i]) for i in fields_for(number)), capital)

    def cached(self, slot=4):
        return next(c for c in self.cache if c.status and c.source == C.addressof(self.posts)+slot*104)

    def complete(self, value):
        self.put(4, pack(value))
        saved = bytes(self.posts)
        collected = self.draw(4)
        cache = self.cached()
        self.assertEqual(cache.status, 2)
        expected = body(value, self.banks)
        self.assertEqual(bytes(cache.body.text), expected.ljust(1024, b'\0'))
        self.assertEqual(cache.body.length, len(expected))
        reads = self.number('af_mail_catalog_reads').value
        for page in range(1, cache.layout.total):
            self.control(0x10)
            self.assertEqual(cache.page, page)
            collected += self.draw(4)
        self.assertEqual(b''.join(collected), expected.replace(b'\xcd', b''))
        self.draw(4)
        self.control(0x10)
        self.assertEqual(cache.page, cache.layout.total-1)
        self.assertEqual(self.number('af_mail_catalog_reads').value, reads)
        self.assertEqual(bytes(self.posts), saved)

    def test_all_treasure_bodies_capitals_and_articles_have_complete_reachable_pages(self):
        for number in IDS:
            for capital in (False, True):
                for article in range(5):
                    with self.subTest(number=number, capital=capital, article=article):
                        # Some templates do not use the article; reopening makes
                        # each test begin at page zero without changing its text.
                        self.lib.af_notice_construct(1)
                        self.complete(self.record(number, capital, article))
        self.assertEqual(self.number('af_notice_allocations').value, self.number('af_notice_releases').value)

    def test_initial_and_treasure_posts_share_two_caches_without_reloading(self):
        initial = Record(4, 0, (0x21,), ())
        treasure = self.record(0x1F4)
        self.put(4, pack(initial))
        self.put(5, pack(treasure))
        for _ in range(3):
            self.draw(4)
            self.draw(5)
        self.assertEqual(self.number('af_notice_allocations').value, 2)
        for slot, expected in ((4, reader.initial_body(initial, self.banks)), (5, body(treasure, self.banks))):
            cache = self.cached(slot)
            self.assertEqual(bytes(cache.body.text[:cache.body.length]), expected)
        self.assertEqual(body(treasure, self.banks).split(b'\xcd')[2], b'')
        self.assertNotIn(b'abcdefghijklmnop', body(treasure, self.banks))

    def test_each_treasure_read_failure_shows_error_and_reopen_recovers_without_save_edits(self):
        value = self.record(0x1F4, True)
        self.complete(value)
        count = self.number('af_mail_catalog_reads').value
        self.assertGreater(count, 0)
        error = [b'Unable to read this post.', b'Close and reopen to retry.']
        saved = bytes(self.posts)
        for failure in range(1, count+1):
            self.lib.af_notice_construct(1)
            self.number('af_mail_catalog_reads').value = 0
            self.number('af_mail_catalog_fail_read').value = failure
            self.assertEqual(self.draw(4), error)
            self.assertEqual(bytes(self.posts), saved)
            self.number('af_mail_catalog_fail_read').value = 0
            self.assertEqual(self.draw(4), error)
            self.lib.af_notice_construct(1)
            self.complete(value)
        self.assertEqual(self.number('af_notice_allocations').value, self.number('af_notice_releases').value)

    def test_unapproved_treasure_fields_and_templates_never_become_raw_text(self):
        value = self.record(0x1F4)
        error = [b'Unable to read this post.', b'Close and reopen to retry.']
        for changed in (replace(value, templates=(0x1A4,)),
                        replace(value, fields=tuple(sorted(value.fields+((2, Field(b'revealed item')),)))),
                        replace(value, fields=((1, Field(b'name')), (3, Field(b'A')), (5, Field(b'town'))))):
            self.put(4, pack(changed))
            saved = bytes(self.posts)
            self.assertEqual(self.draw(4), error)
            self.assertEqual(bytes(self.posts), saved)


if __name__ == '__main__': unittest.main()
