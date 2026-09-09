"""Complete order/ticket letters, atomic failures, and earlier dispatch contracts."""

import ctypes as C
import struct
import unittest

import test_mail_glyph_creator as glyph_tests
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field,Record,pack
from test_mail_format import CText


class PostOfficeCreatorTests(glyph_tests.MailGlyphCreatorTests):
    extra_sources = (*glyph_tests.MailGlyphCreatorTests.extra_sources,
                     'overlays/mail_generation/post_office_creator.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_post_office_mail_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create','af_system_mail_create','af_departed_mail_create',
                     'af_villager_event_mail_create','af_academy_mail_create','af_academy_score_mail_create'):
            setattr(cls.lib,name,cls.lib.af_post_office_mail_create)

    def postal_fixture(self,number=0x49,capital=0,gift=0x11FC):
        fixture = self.fixture(good=0,capital=capital)
        C.memmove(fixture[4],struct.pack('>4sHH4B',b'AFPO',number,gift,55,0,0,249),12)
        C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value = 0
        return fixture

    def postal_invoke(self,fixture,success=True,preflight=False):
        memory,address,capture,player,request,remail,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,request.raw,remail.raw
        old_work = memory.raw;old_calls = self.calls.value,self.clear_calls.value
        self.assertEqual(self.lib.af_post_office_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw,request.raw,remail.raw),before[2:])
        self.assertEqual((self.calls.value,self.clear_calls.value),old_calls)
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(bytes(self.words_memory),self.words);self.assertEqual(bytes(self.alias_memory),self.aliases)
        self.assertEqual(bytes(self.series_memory),self.series_data)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2])
            if preflight: self.assertEqual(memory.raw,old_work)
            return
        _,number,gift,_,_,_,_ = struct.unpack('>4sHH4B',request.raw)
        months = ('January','February','March','April','May','June','July','August','September','October','November','December')
        fields = ((4,Field(months[(gift-0x2C00)//8].ljust(9).encode())),) if number==0x57 else ((0,Field(bytes(self.item_name))),)
        record = Record(self.catalog_id,0,(number,),fields,bool(before[1]))
        expected = bytearray(164);expected[:16] = player.raw
        expected[18:30] = b' '*12;expected[30:35] = b'\xff'*5
        expected[36:38] = gift.to_bytes(2,'big');expected[39:42] = bytes((128,7,55));expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,templates(self.catalog,record));output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        calls = C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value
        self.assertEqual(calls,int(number!=0x57))
        if calls: self.assertEqual(C.c_uint.in_dll(self.lib,'af_event_card_item_id').value,gift)

    def test_postal_all_shops_months_ticket_counts_and_capitals(self):
        for number in range(0x49,0x4D):
            for capital in (0,1):
                for name in (b'abcdefghijklmnop',b'orange box      ',b'apple           '):
                    self.item_name[:] = name
                    self.postal_invoke(self.postal_fixture(number,capital))
        for month in range(1,13):
            for count in range(1,6):
                for capital in (0,1): self.postal_invoke(self.postal_fixture(0x57,capital,0x2C00+(month-1)*8+count-1))

    def test_postal_bad_descriptors_and_aliases_retain_all_outputs(self):
        for number,gift in ((0x48,1),(0x4D,1),(0xFFFF,1),(0x49,0),
                            (0x57,0),(0x57,0x2BFF),(0x57,0x2C60),
                            *((0x57,0x2C00+month*8+count) for month in range(12) for count in (5,6,7))):
            self.postal_invoke(self.postal_fixture(number,1,gift),False,True)
        for offset in (0,1,2,3,8,9,10):
            fixture = self.postal_fixture(capital=1)
            C.c_ubyte.from_address(C.addressof(fixture[4])+offset).value ^= 1
            self.postal_invoke(fixture,False,True)
        for field,value in (('player',None),('player',1),('animal',1),('condition',1),('foreign',1)):
            fixture = self.postal_fixture(capital=1);setattr(fixture[2].session,field,value)
            self.postal_invoke(fixture,False,True)
        for field in ('player','animal','remail'):
            for where in ('active','capital','work','destination'):
                fixture = self.postal_fixture(capital=1)
                pointer = {'active':C.addressof(self.active),'capital':C.addressof(fixture[-1]),
                           'work':fixture[1]+512,'destination':C.addressof(fixture[6])+16}[where]
                setattr(fixture[2].session,field,pointer);self.postal_invoke(fixture,False,True)

    def test_postal_resource_failures_and_retry_do_not_lose_letter(self):
        for number,gift in ((0x49,0x11FC),(0x57,0x2C44)):
            reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
            self.postal_invoke(self.postal_fixture(number,1,gift));count = reads.value
            for index in range(1,count+1):
                reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
                self.postal_invoke(self.postal_fixture(number,1,gift),False)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
            fixture = self.postal_fixture(number,1,gift)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0;self.postal_invoke(fixture,False)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1
            C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value = 0;self.postal_invoke(fixture)
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 1
        for number in range(0x49,0x4D): self.postal_invoke(self.postal_fixture(number,1),False)
        self.postal_invoke(self.postal_fixture(0x57,1,0x2C44))
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 0
        self.item_name[:] = bytes.fromhex('7F')+b'!'*15
        self.postal_invoke(self.postal_fixture(capital=1),False)


if __name__ == '__main__': unittest.main()
