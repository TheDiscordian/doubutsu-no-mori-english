"""Complete shop notices, full item fields, and earlier dispatcher contracts."""

import ctypes as C
import struct
import unittest

import test_museum_creator as museum_tests
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field,Record,pack
from test_mail_format import CText


class ShopNoticeCreatorTests(museum_tests.MuseumCreatorTests):
    extra_sources = (*museum_tests.MuseumCreatorTests.extra_sources,
                     'overlays/mail_generation/shop_notice_creator.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_shop_notice_mail_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create','af_system_mail_create','af_departed_mail_create',
                     'af_villager_event_mail_create','af_academy_mail_create','af_academy_score_mail_create',
                     'af_post_office_mail_create','af_museum_mail_create'):
            setattr(cls.lib,name,cls.lib.af_shop_notice_mail_create)

    def shop_fixture(self,number=0x14,capital=0,item=0x11FC,recipient=1):
        fixture = self.fixture(good=0,capital=capital)
        C.memmove(fixture[4],struct.pack('>4sHH4B',b'AFSN',number,item,55,recipient,0,247),12)
        C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value = 0
        return fixture

    def shop_invoke(self,fixture,success=True,preflight=False):
        memory,address,capture,player,request,remail,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,request.raw,remail.raw
        before_work = memory.raw;calls = self.calls.value,self.clear_calls.value
        self.assertEqual(self.lib.af_shop_notice_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value);self.assertEqual((player.raw,request.raw,remail.raw),before[2:])
        self.assertEqual((self.calls.value,self.clear_calls.value),calls)
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        lead = address-C.addressof(memory);self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(bytes(self.words_memory),self.words);self.assertEqual(bytes(self.alias_memory),self.aliases)
        self.assertEqual(bytes(self.series_memory),self.series_data)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2])
            if preflight: self.assertEqual(memory.raw,before_work)
            return
        _,number,item,_,recipient,_,_ = struct.unpack('>4sHH4B',request.raw)
        fields = ((7,Field(bytes(self.item_name))),) if 0x14<=number<=0x17 else ()
        record = Record(self.catalog_id,0,(number,),fields,bool(before[1]))
        expected = bytearray(164);expected[:12] = b' '*12;expected[12:17] = b'\xff'*5
        if recipient: expected[:17] = player.raw+b'\0'
        expected[18:30] = b' '*12;expected[30:35] = b'\xff'*5
        expected[39:42] = bytes((128,2,55));expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,templates(self.catalog,record));output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value,int(bool(fields)))
        if fields: self.assertEqual(C.c_uint.in_dll(self.lib,'af_event_card_item_id').value,item)
        return record,letter

    def test_shop_all_templates_capitals_recipients_and_complete_item_names(self):
        for number in (*range(0x12,0x18),*range(0x1B,0x1E)):
            for capital in (0,1):
                for recipient in (0,1):
                    for name in (b'abcdefghijklmnop',b'orange box      ',b'apple           '):
                        self.item_name[:] = name
                        self.shop_invoke(self.shop_fixture(number,capital,0 if number>=0x1B else 0x11FC,recipient))

    def test_shop_bad_descriptors_and_aliases_retain_outputs(self):
        for number,item,recipient in ((0x11,1,1),(0x18,1,1),(0x1A,0,0),(0x1E,0,0),
                                      (0x14,0,1),(0x12,0,0),(0x1B,1,0),(0x1D,0xFFFF,1),(0x14,1,2)):
            self.shop_invoke(self.shop_fixture(number,1,item,recipient),False,True)
        for offset in (0,1,2,3,8,10):
            fixture = self.shop_fixture(capital=1);C.c_ubyte.from_address(C.addressof(fixture[4])+offset).value ^= 1
            self.shop_invoke(fixture,False,True)
        for field,value in (('player',None),('player',1),('animal',1),('condition',1),('foreign',1)):
            fixture = self.shop_fixture(capital=1);setattr(fixture[2].session,field,value)
            self.shop_invoke(fixture,False,True)
        for field in ('player','animal','remail'):
            for where in ('active','capital','work','destination'):
                fixture = self.shop_fixture(capital=1)
                pointer = {'active':C.addressof(self.active),'capital':C.addressof(fixture[-1]),
                           'work':fixture[1]+512,'destination':C.addressof(fixture[6])+16}[where]
                setattr(fixture[2].session,field,pointer);self.shop_invoke(fixture,False,True)

    def test_shop_every_catalogue_read_failure_and_item_failure_allow_retry(self):
        for number in (*range(0x12,0x18),*range(0x1B,0x1E)):
            item = 0 if number>=0x1B else 0x11FC
            reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
            self.shop_invoke(self.shop_fixture(number,1,item));count = reads.value
            for index in range(1,count+1):
                reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
                self.shop_invoke(self.shop_fixture(number,1,item),False)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
            fixture = self.shop_fixture(number,1,item)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0;self.shop_invoke(fixture,False)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1
            C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value = 0;self.shop_invoke(fixture)
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 1
        for number in range(0x14,0x18): self.shop_invoke(self.shop_fixture(number,1),False)
        for number in (0x12,0x13,0x1B,0x1C,0x1D):
            self.shop_invoke(self.shop_fixture(number,1,0 if number>=0x1B else 0x11FC))
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 0
        self.item_name[:] = b'\x7f'+b'!'*15;self.shop_invoke(self.shop_fixture(capital=1),False)

    def test_shop_reopening_single_preparation_preserves_repeated_capitalization(self):
        # No recipient field is captured. One complete reopening letter can be
        # prepared before any home publication, then receive native identities.
        for number in (0x1B,0x1C,0x1D):
            for initial in (0,1):
                first = self.shop_invoke(self.shop_fixture(number,initial,0,0))[1]
                capital = first.final_capital
                for _ in range(3):
                    current = self.shop_invoke(self.shop_fixture(number,int(capital),0,0))[1]
                    self.assertEqual((current.header,current.body,current.footer,current.final_capital),
                                     (first.header,first.body,first.footer,first.final_capital))
                    capital = current.final_capital


if __name__=='__main__': unittest.main()
