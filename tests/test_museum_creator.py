"""Complete museum letters retain canonical sender identity and earlier creators."""

import ctypes as C
import struct
import unittest

import test_post_office_creator as postal_tests
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Record,pack
from test_mail_format import CText

FOSSILS = (0x10E,0x110,0x10F,0x111,0x113,0x112,0x114,0x116,0x115,
           0x117,0x119,0x118,0x11A,0x11B,0x11C,0x11D,0x11E,0x11F,
           0x120,0x121,0x126,0x125,0x123,0x124,0x122)


class MuseumCreatorTests(postal_tests.PostOfficeCreatorTests):
    extra_sources = (*postal_tests.PostOfficeCreatorTests.extra_sources,
                     'overlays/mail_generation/museum_creator.c','tests/museum_creator_mock.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_museum_mail_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create','af_system_mail_create','af_departed_mail_create',
                     'af_villager_event_mail_create','af_academy_mail_create','af_academy_score_mail_create',
                     'af_post_office_mail_create'):
            setattr(cls.lib,name,cls.lib.af_museum_mail_create)

    def museum_fixture(self,number=0xBD,capital=0,gift=0):
        fixture = self.fixture(good=0,capital=capital)
        C.memmove(fixture[4],struct.pack('>4sHH4B',b'AFMU',number,gift,24,0,0,248),12)
        C.c_uint.in_dll(self.lib,'af_museum_sender_calls').value = 0
        return fixture

    def museum_invoke(self,fixture,success=True,preflight=False):
        memory,address,capture,player,request,remail,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,request.raw,remail.raw
        before_work = memory.raw
        calls = self.calls.value,self.clear_calls.value,C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value
        self.assertEqual(self.lib.af_museum_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value);self.assertEqual((player.raw,request.raw,remail.raw),before[2:])
        self.assertEqual((self.calls.value,self.clear_calls.value,C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value),calls)
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        lead = address-C.addressof(memory);self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2])
            if preflight:
                self.assertEqual(memory.raw,before_work)
                self.assertEqual(C.c_uint.in_dll(self.lib,'af_museum_sender_calls').value,0)
            return
        _,number,gift,_,_,_,_ = struct.unpack('>4sHH4B',request.raw)
        record = Record(self.catalog_id,0,(number,),(),bool(before[1]))
        expected = bytearray(164);expected[:16] = player.raw
        expected[18:24] = bytes.fromhex('1907F81105C3');expected[24:30] = b' '*6
        expected[30:34] = b'\xff'*4;expected[34] = 2
        expected[36:38] = gift.to_bytes(2,'big');expected[39:42] = bytes((128,0,24));expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,templates(self.catalog,record));output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))

    def test_museum_all_notices_fossils_variants_and_initial_capitals(self):
        for capital in (0,1):
            for number in (0xBD,0xBE): self.museum_invoke(self.museum_fixture(number,capital))
            for index,number in enumerate(FOSSILS):
                for variant in range(4): self.museum_invoke(self.museum_fixture(number,capital,0x1E3C+index*4+variant))

    def test_museum_invalid_descriptors_and_inputs_retain_outputs(self):
        for number,gift in ((0xBC,0),(0xBF,0),(0x10D,0x1E3C),(0x127,0x1E9F),
                            (0xBD,1),(0xBE,0x1E3C),(0x10E,0),(0x10E,0x1E3B),(0x10E,0x1EA0),
                            *((number,0x1E3C+((index+1)%25)*4) for index,number in enumerate(FOSSILS))):
            self.museum_invoke(self.museum_fixture(number,1,gift),False,True)
        for offset in (0,1,2,3,8,9,10):
            fixture = self.museum_fixture(capital=1);C.c_ubyte.from_address(C.addressof(fixture[4])+offset).value ^= 1
            self.museum_invoke(fixture,False,True)
        for field,value in (('player',None),('player',1),('animal',1),('condition',1),('foreign',1)):
            fixture = self.museum_fixture(capital=1);setattr(fixture[2].session,field,value)
            self.museum_invoke(fixture,False,True)
        for field in ('player','animal','remail'):
            for where in ('active','capital','work','destination'):
                fixture = self.museum_fixture(capital=1)
                pointer = {'active':C.addressof(self.active),'capital':C.addressof(fixture[-1]),
                           'work':fixture[1]+512,'destination':C.addressof(fixture[6])+16}[where]
                setattr(fixture[2].session,field,pointer);self.museum_invoke(fixture,False,True)

    def test_museum_catalogue_failures_retry_and_unused_item_resource(self):
        for number,gift in ((0xBD,0),(0xBE,0),(0x126,0x1E8C)):
            reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
            self.museum_invoke(self.museum_fixture(number,1,gift));count = reads.value
            for index in range(1,count+1):
                reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
                self.museum_invoke(self.museum_fixture(number,1,gift),False)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
            fixture = self.museum_fixture(number,1,gift)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0;self.museum_invoke(fixture,False)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1;self.museum_invoke(fixture)
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 1
        self.museum_invoke(self.museum_fixture(0x10E,1,0x1E3C))


if __name__=='__main__': unittest.main()
