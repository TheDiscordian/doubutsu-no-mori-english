"""Complete score fields, all supported bodies, and inherited creator contracts."""

import ctypes as C
import struct
import unittest

import test_academy_creator as academy_tests
from academy_score_letters import COMPLETE,fields,references,series_resource
from mail_record import Record,Field,pack
from mail_format import format_letter
from mail_catalog import templates
from test_mail_format import CText
from pathlib import Path


class AcademyScoreCreatorTests(academy_tests.AcademyCreatorTests):
    extra_sources = (*academy_tests.AcademyCreatorTests.extra_sources,
                     'overlays/mail_generation/academy_score_creator.c','runtime/dateformat.c',
                     'tests/academy_score_creator_mock.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_academy_score_mail_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create','af_system_mail_create','af_departed_mail_create',
                     'af_villager_event_mail_create','af_academy_mail_create'):
            setattr(cls.lib,name,cls.lib.af_academy_score_mail_create)
        root = Path(__file__).resolve().parents[1]
        cls.score_references = references((root/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),cls.catalog)
        cls.series_data = series_resource(cls.score_references)

    def setUp(self):
        super().setUp()
        self.series_memory = (C.c_ubyte*1440).in_dll(self.lib,'af_academy_series_data')
        self.series_memory[:] = self.series_data

    def score_fixture(self,number=0x34,capital=0,series=0,points=123456,year=2000,month=9,day=17,item=0x11FC):
        fixture = self.fixture(foreign=1,good=0,capital=capital)
        C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value = 0
        C.memmove(fixture[4],self.series_data[series*26:series*26+10]+b'!!',12)
        C.memmove(fixture[5],struct.pack('>IHHHBBHHBB',points,item,0,year,month,day,number,0,250,51),18)
        return fixture

    def score_invoke(self,fixture,success=True):
        memory,address,capture,player,series,request,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,series.raw,request.raw
        self.assertEqual(self.lib.af_academy_score_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value);self.assertEqual((player.raw,series.raw,request.raw),before[2:])
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        lead = address-C.addressof(memory);self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(bytes(self.series_memory),self.series_data)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2]);return
        points,item,_,year,month,day,number,_,_,_ = struct.unpack('>IHHHBBHHBB',request.raw)
        suffix = 'th' if 11<=day<=13 else {1:'st',2:'nd',3:'rd'}.get(day%10,'th')
        months = ('January','February','March','April','May','June','July','August','September','October','November','December')
        values = {0:Field(f'{points:,}'.rjust(10).encode()),3:Field(str(year).encode()),
                  4:Field(months[month-1].ljust(9).encode()),5:Field(f'{day}{suffix}'.ljust(4).encode())}
        if number == 0x37: values[1] = Field(bytes(self.item_name))
        if number in (0x3A,0x3B):
            i = next(i for i in range(55) if self.series_data[i*26:i*26+10] == series.raw[:10])
            values[2] = Field(self.series_data[i*26+10:i*26+26])
        record = Record(2,0,(number,),tuple(sorted(values.items())),bool(before[1]))
        expected = bytearray(164);expected[:16] = player.raw;expected[18:30] = b' '*12;expected[30:35] = b'\xff'*5
        expected[39:42] = bytes((128,6,51));expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,templates(self.catalog,record));output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer));self.assertEqual(capital.value,int(letter.final_capital))
        calls = C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value;self.assertEqual(calls,int(number==0x37))
        if calls: self.assertEqual(C.c_uint.in_dll(self.lib,'af_event_card_item_id').value,item)

    def test_all_score_templates_both_capitals_all_series_and_point_boundaries(self):
        for number in COMPLETE:
            for cap in (0,1): self.score_invoke(self.score_fixture(number,cap))
        for i in range(55):
            for number in (0x3A,0x3B): self.score_invoke(self.score_fixture(number,i%2,series=i))
        for points in (0,1,999,1000,9999,10000,19999,20000,69999,70000,99999,100000,99999999,100000000,0x7FFFFFFF):
            self.score_invoke(self.score_fixture(points=points))

    def test_all_months_ordinal_days_and_valid_leap_dates(self):
        for month in range(1,13):
            for day in range(1,30 if month==2 else 31 if month in (4,6,9,11) else 32):
                self.score_invoke(self.score_fixture(0x34,day%2,month=month,day=day))

    def test_invalid_dates_descriptors_and_unused_names(self):
        for values in (dict(points=0x80000000),dict(number=0x33),dict(number=0x49),dict(number=0x3D),
                       dict(year=1900),dict(year=2100),dict(month=0),dict(month=13),dict(day=0),
                       dict(month=4,day=31),dict(month=2,day=30),dict(year=1901,month=2,day=29)):
            self.score_invoke(self.score_fixture(capital=1,**values),False)
        for offset in (6,7,14,15,17):
            fixture = self.score_fixture(capital=1);C.c_ubyte.from_address(C.addressof(fixture[5])+offset).value ^= 1
            self.score_invoke(fixture,False)
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 1
        for number in COMPLETE:
            fixture = self.score_fixture(number,1)
            if number not in (0x3A,0x3B): fixture[2].session.animal = None
            self.score_invoke(fixture,number!=0x37)
        for number in (0x3A,0x3B):
            fixture = self.score_fixture(number,1);C.memset(fixture[4],ord('!'),10);self.score_invoke(fixture,False)

    def test_every_catalogue_failure_and_control_aliases_retain_output(self):
        reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
        self.score_invoke(self.score_fixture(0x3A));count = reads.value
        for index in range(1,count+1):
            reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
            self.score_invoke(self.score_fixture(0x3A,1),False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
        fixture = self.score_fixture(0x3A,1)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0;self.score_invoke(fixture,False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1;self.score_invoke(fixture)
        for field in ('player','animal','remail'):
            fixture = self.score_fixture(capital=1);old = getattr(fixture[2].session,field)
            for pointer in (C.addressof(self.active),C.addressof(fixture[-1]),fixture[1]+512,C.addressof(fixture[6])+16):
                setattr(fixture[2].session,field,pointer);self.score_invoke(fixture,False)
            setattr(fixture[2].session,field,old)


if __name__ == '__main__': unittest.main()
