"""Complete seasonal creation and retained earlier dispatcher contracts."""

import ctypes as C
import struct
import unittest

import test_notice_owner as owner_tests
from mail_record import Field, Record
from notice_record import pack
from notice_seasonal import IDS, compiled_resource, complete_body
from test_mail_format import CText
from test_npc_mail_creator import ROOT


class SeasonalCreatorTests(owner_tests.NoticeOwnerTests):
    extra_sources = (*owner_tests.NoticeOwnerTests.extra_sources, 'runtime/notice/seasonal.c',
                     'overlays/mail_generation/notice_seasonal_creator.c', 'tests/notice_seasonal_creator_mock.c')

    @classmethod
    def generated_compile_flags(cls, directory):
        cls.seasonal_resource = compiled_resource((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                                  (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes())
        (directory/'seasonal_data.h').write_text(cls.seasonal_resource['header'])
        return ['-I'+str(directory)]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_notice_seasonal_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create', 'af_system_mail_create', 'af_departed_mail_create',
                     'af_villager_event_mail_create', 'af_academy_mail_create', 'af_academy_score_mail_create',
                     'af_post_office_mail_create', 'af_museum_mail_create', 'af_shop_notice_mail_create',
                     'af_quest_reply_mail_create', 'af_notice_treasure_create', 'af_notice_owner_create'):
            setattr(cls.lib, name, cls.lib.af_notice_seasonal_create)
        cls.seasonal_entries = {e['template']: e for e in cls.seasonal_resource['templates']}

    def seasonal_value(self, name, value=None):
        scalar = C.c_uint.in_dll(self.lib, 'af_seasonal_'+name)
        if value is not None: scalar.value = value
        return scalar.value

    def seasonal_fixture(self, number=0x1A4, capital=0, year=2001, level=0, weekday=0):
        value = self.fixture(foreign=0, good=0, capital=capital)
        C.memmove(value[4], struct.pack('>4sHHBBBB', b'AFNS', number, year, 0, 0, 0, 243), 12)
        for name, scalar in (('level', level), ('shop_calls', 0), ('lunar_calls', 0), ('weekday_calls', 0),
                             ('lunar_mode', 1), ('month', 9), ('day', 30), ('weekday_value', weekday)):
            self.seasonal_value(name, scalar)
        return value

    def seasonal_invoke(self, fixture, success=True, preflight=False):
        memory, address, capture, player, request, unused, destination, capital = fixture
        before = memory.raw, destination.raw, capital.value, player.raw, request.raw
        self.assertEqual(self.lib.af_notice_seasonal_create(address, C.byref(destination, 16),
                                                           C.byref(self.active), C.byref(capital)), int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw, request.raw), before[3:])
        self.assertEqual(destination.raw[:16]+destination.raw[-16:], b'!'*32)
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:], b'!'*64)
        self.assertEqual((self.calls.value, self.clear_calls.value), (0, 0))
        if not success:
            self.assertEqual((destination.raw, capital.value), before[1:3])
            if preflight: self.assertEqual(memory.raw, before[0])
            return
        number, year = struct.unpack('>HH', request.raw[4:8])
        entry = self.seasonal_entries[number]
        fields = []
        for index in entry['fields']:
            if index == 0: text = b'Town  '
            elif index == 1: text = self.seasonal_resource['shops'][self.seasonal_value('level')]
            else:
                if index == 4:
                    week = self.seasonal_value('weekday_value')
                    month, day = 10, 15-week if week else 8
                    self.assertEqual(list((C.c_uint*3).in_dll(self.lib, 'af_seasonal_weekday_input')), [year, 10, 14])
                else:
                    native = [year, 8 if index == 2 else 9, 15 if index == 2 else 13]
                    self.assertEqual(list((C.c_uint*3).in_dll(self.lib, 'af_seasonal_lunar_input')), native)
                    month, day = (self.seasonal_value('month'), self.seasonal_value('day')) \
                        if self.seasonal_value('lunar_mode') else native[1:]
                months = 'January February March April May June July August September October November December'.split()
                suffix = 'th' if 11 <= day <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
                text = f'{months[month-1]} {day}{suffix}'.encode()
            fields.append((index, Field(text)))
        record = Record(4, 0, (number,), tuple(fields), bool(before[2]))
        self.assertEqual(destination.raw[16:180], pack(record)+bytes(68))
        text = CText.from_address(address+self.text)
        self.assertEqual(bytes(text.text[text.offsets[1]:text.offsets[1]+text.lengths[1]]), complete_body(record, entry))
        self.assertEqual((text.lengths[0], text.lengths[2]), (0, 0))
        self.assertEqual(capital.value, before[2])
        for name, count in (('shop_calls', int(1 in entry['fields'])),
                            ('lunar_calls', int(bool(set(entry['fields']) & {2, 3}))),
                            ('weekday_calls', int(4 in entry['fields']))):
            self.assertEqual(self.seasonal_value(name), count)
        return record

    def test_seasonal_all_41_bodies_both_capitals_and_every_shop_level(self):
        for number in IDS:
            for capital in (0, 1):
                for level in (range(4) if 1 in self.seasonal_entries[number]['fields'] else (0,)):
                    self.seasonal_invoke(self.seasonal_fixture(number, capital, level=level))

    def test_seasonal_full_months_ordinals_both_lunar_inputs_and_native_fallback(self):
        for number in (0x1BA, 0x1BC):
            for month in range(1, 13):
                for day in (1, 2, 3, 4, 11, 12, 13, 21, 22, 23, 30, 31):
                    fixture = self.seasonal_fixture(number, 1)
                    self.seasonal_value('month', month); self.seasonal_value('day', day)
                    self.seasonal_invoke(fixture)
            for year in (1, 2001, 2033, 65535):
                fixture = self.seasonal_fixture(number, 1, year=year)
                self.seasonal_value('lunar_mode', 0)
                self.seasonal_invoke(fixture)
        for weekday in range(7):
            self.seasonal_invoke(self.seasonal_fixture(0x1BE, 1, weekday=weekday))

    def test_seasonal_bad_calendar_or_shop_values_leave_output_then_retry(self):
        for number, name, value in ((0x1A8, 'level', 4), (0x1AF, 'level', 0xFFFFFFFF),
                                     (0x1BA, 'month', 0), (0x1BC, 'month', 13),
                                     (0x1BA, 'day', 0), (0x1BC, 'day', 32),
                                     (0x1BE, 'weekday_value', 7), (0x1BE, 'weekday_value', 0xFFFFFFFF)):
            fixture = self.seasonal_fixture(number, 1)
            self.seasonal_value(name, value)
            self.seasonal_invoke(fixture, False)
            self.seasonal_invoke(self.seasonal_fixture(number, 1))

    def test_seasonal_descriptor_control_and_overlap_fail_before_mutation(self):
        for offset, value in ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0xA3),
                              (8, 1), (9, 1), (10, 1)):
            fixture = self.seasonal_fixture(capital=1)
            C.c_ubyte.from_address(C.addressof(fixture[4])+offset).value = value
            self.seasonal_invoke(fixture, False, True)
        self.seasonal_invoke(self.seasonal_fixture(year=0), False, True)
        for field, value in (('player', None), ('player', 1), ('animal', 1), ('condition', 1), ('foreign', 1)):
            fixture = self.seasonal_fixture(capital=1)
            setattr(fixture[2].session, field, value)
            self.seasonal_invoke(fixture, False, True)
        for field in ('player', 'animal'):
            for where in ('work', 'destination', 'capital', 'active'):
                fixture = self.seasonal_fixture(capital=1)
                pointer = {'work': fixture[1]+512, 'destination': C.addressof(fixture[6])+16,
                           'capital': C.addressof(fixture[-1]), 'active': C.addressof(self.active)}[where]
                setattr(fixture[2].session, field, pointer)
                self.seasonal_invoke(fixture, False, True)


if __name__ == '__main__': unittest.main()
