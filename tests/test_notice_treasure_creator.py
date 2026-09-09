"""Full treasure creation and retention of every earlier creator dispatcher."""

import ctypes as C
import struct
import unittest
import test_quest_reply_creator as quest_tests
from mail_record import Field, Record
from notice_record import pack
from notice_treasure import body, fields_for
from mail_catalog import parse
from test_mail_format import CText


class NoticeTreasureCreatorTests(quest_tests.QuestReplyCreatorTests):
    extra_sources = (*quest_tests.QuestReplyCreatorTests.extra_sources,
                     'runtime/notice/record.c', 'runtime/notice/treasure.c',
                     'overlays/mail_generation/notice_treasure_creator.c',
                     'tests/notice_treasure_creator_mock.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_notice_treasure_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create', 'af_system_mail_create', 'af_departed_mail_create',
                     'af_villager_event_mail_create', 'af_academy_mail_create', 'af_academy_score_mail_create',
                     'af_post_office_mail_create', 'af_museum_mail_create', 'af_shop_notice_mail_create',
                     'af_quest_reply_mail_create'):
            setattr(cls.lib, name, cls.lib.af_notice_treasure_create)
        cls.banks = parse(cls.catalog)[1]

    def notice_fixture(self, number=0x1F0, capital=0, npc=0, article=1):
        looks = (number-0x1F0)//3
        fixture = self.fixture(foreign=0, good=0, looks=looks, capital=capital)
        C.memmove(fixture[3], struct.pack('>HH6sBB4s', 0xE000+npc, 0x1234, b'AWAY  ', npc, looks, bytes(4)), 16)
        C.memmove(fixture[4], struct.pack('>4sHHBBBB', b'AFNT', number, 0x11FC, 6, 5, 0, 245), 12)
        C.c_int.in_dll(self.lib, 'af_notice_test_article').value = article
        C.c_uint.in_dll(self.lib, 'af_notice_test_article_calls').value = 0
        C.c_uint.in_dll(self.lib, 'af_event_card_item_calls').value = 0
        return fixture

    def notice_invoke(self, fixture, success=True, preflight=False):
        memory, address, capture, animal, request, unused, destination, capital = fixture
        before = destination.raw, capital.value, animal.raw, request.raw, memory.raw
        self.assertEqual(self.lib.af_notice_treasure_create(address, C.byref(destination, 16),
                                                           C.byref(self.active), C.byref(capital)), int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((animal.raw, request.raw), before[2:4])
        self.assertEqual(destination.raw[:16]+destination.raw[-16:], b'!'*32)
        leading = address-C.addressof(memory)
        self.assertEqual(memory.raw[:leading]+memory.raw[leading+self.size:], b'!'*64)
        self.assertEqual((self.calls.value, self.clear_calls.value), (0, 0))
        if not success:
            self.assertEqual((destination.raw, capital.value), before[:2])
            if preflight: self.assertEqual(memory.raw, before[4])
            return
        number = int.from_bytes(request.raw[4:6], 'big')
        npc = int.from_bytes(animal.raw[:2], 'big')-0xE000
        name = next(row.name for row in self.alias_rows if row.npc_index == npc)
        values = {1: Field(name), 2: Field(bytes(self.item_name), C.c_int.in_dll(self.lib, 'af_notice_test_article').value),
                  3: Field(b'6'), 4: Field(b'5'), 5: Field(b'Town  ')}
        record = Record(4, 0, (number,), tuple((i, values[i]) for i in fields_for(number)), bool(before[1]))
        self.assertEqual(destination.raw[16:180], pack(record)+bytes(68))
        complete = CText.from_address(address+self.text)
        self.assertEqual(bytes(complete.text[complete.offsets[1]:complete.offsets[1]+complete.lengths[1]]),
                         body(record, self.banks))
        self.assertEqual(capital.value, before[1])
        self.assertEqual(C.c_uint.in_dll(self.lib, 'af_event_card_item_calls').value,
                         int(2 in fields_for(number)))
        self.assertEqual(C.c_uint.in_dll(self.lib, 'af_notice_test_article_calls').value,
                         int(2 in fields_for(number)))

    def test_notice_all_eighteen_templates_articles_capitals_and_full_names(self):
        for number in range(0x1F0, 0x202):
            for capital in (0, 1):
                for article in range(5):
                    self.item_name[:] = b'abcdefghijklmnop'
                    self.notice_invoke(self.notice_fixture(number, capital, article=article))
        for npc in range(216): self.notice_invoke(self.notice_fixture(0x1F0+npc%18, npc%2, npc))

    def test_notice_invalid_descriptor_identity_and_overlap_retain_output(self):
        for offset, value in ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0xEF),
                              (8, 0), (8, 7), (9, 0), (9, 6), (10, 1), (10, 5), (10, 255)):
            fixture = self.notice_fixture(capital=1)
            C.c_ubyte.from_address(C.addressof(fixture[4])+offset).value = value
            self.notice_invoke(fixture, False, True)
        for offset, value in ((0, 0), (1, 216), (11, 1), (11, 6)):
            fixture = self.notice_fixture(capital=1)
            C.c_ubyte.from_address(C.addressof(fixture[3])+offset).value = value
            self.notice_invoke(fixture, False, True)
        for field, value in (('player', None), ('player', 1), ('animal', 1), ('condition', 1), ('foreign', 1)):
            fixture = self.notice_fixture(capital=1)
            setattr(fixture[2].session, field, value)
            self.notice_invoke(fixture, False, True)
        for field in ('player', 'animal'):
            for where in ('active', 'capital', 'work', 'destination'):
                fixture = self.notice_fixture(capital=1)
                pointer = {'active': C.addressof(self.active), 'capital': C.addressof(fixture[-1]),
                           'work': fixture[1]+512, 'destination': C.addressof(fixture[6])+16}[where]
                setattr(fixture[2].session, field, pointer)
                self.notice_invoke(fixture, False, True)

    def test_notice_catalogue_and_item_failures_then_complete_retry(self):
        reads = C.c_uint.in_dll(self.lib, 'af_mail_catalog_reads')
        fail = C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read')
        for number in range(0x1F0, 0x202):
            reads.value = 0
            self.notice_invoke(self.notice_fixture(number, 1))
            count = reads.value
            for index in range(1, count+1):
                reads.value, fail.value = 0, index
                self.notice_invoke(self.notice_fixture(number, 1), False)
            fail.value = 0
            self.notice_invoke(self.notice_fixture(number, 1))
        C.c_uint.in_dll(self.lib, 'af_event_card_item_fail').value = 1
        for number in range(0x1F0, 0x202):
            self.notice_invoke(self.notice_fixture(number), 2 not in fields_for(number))
        C.c_uint.in_dll(self.lib, 'af_event_card_item_fail').value = 0
        self.notice_invoke(self.notice_fixture())

    def test_notice_article_failure_preserves_output_and_all_clue_only_posts(self):
        for number in range(0x1F0, 0x202):
            fixture = self.notice_fixture(number, article=-1)
            self.notice_invoke(fixture, 2 not in fields_for(number))
        self.notice_invoke(self.notice_fixture())


if __name__ == '__main__': unittest.main()
