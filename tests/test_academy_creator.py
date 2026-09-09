"""Complete HRA advice/welcome generation and all inherited letter contracts."""

import ctypes as C
import struct
import unittest

import test_villager_event_creator as event_tests
from academy_letters import TEMPLATES
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Record,pack
from test_mail_format import CText


class AcademyCreatorTests(event_tests.VillagerEventCreatorTests):
    extra_sources = (*event_tests.VillagerEventCreatorTests.extra_sources,
                     'overlays/mail_generation/academy_creator.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_academy_mail_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create','af_system_mail_create','af_departed_mail_create','af_villager_event_mail_create'):
            setattr(cls.lib,name,cls.lib.af_academy_mail_create)

    def academy_fixture(self,number=0x1DC,capital=0):
        fixture = self.fixture(foreign=1,good=0,capital=capital)
        fixture[2].session.animal = None
        C.memmove(fixture[5],bytes(12)+struct.pack('>HHBB',number,0,251,51),18)
        return fixture

    def academy_invoke(self,fixture,success=True):
        memory,address,capture,player,animal,request,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,animal.raw,request.raw
        self.assertEqual(self.lib.af_academy_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw,animal.raw,request.raw),before[2:])
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(bytes(self.words_memory),self.words);self.assertEqual(bytes(self.alias_memory),self.aliases)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2]);return
        number = int.from_bytes(request.raw[12:14],'big')
        record = Record(self.catalog_id,0,(number,),(),bool(before[1]))
        expected = bytearray(164);expected[:16] = player.raw
        expected[18:30] = b' '*12;expected[30:35] = b'\xff'*5
        expected[39:42] = bytes((128,6,51));expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,templates(self.catalog,record));output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value,0)

    def test_all_twenty_complete_letters_both_capitals(self):
        self.assertEqual(len(TEMPLATES),20)
        for number in TEMPLATES:
            for capital in (0,1):
                with self.subTest(number=f'{number:04X}',capital=capital):
                    self.academy_invoke(self.academy_fixture(number,capital))

    def test_each_catalogue_read_failure_and_resource_recovery(self):
        reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
        self.academy_invoke(self.academy_fixture());count = reads.value
        for index in range(1,count+1):
            reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
            self.academy_invoke(self.academy_fixture(0x1EF,1),False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
        enabled = C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled');enabled.value = 0
        fixture = self.academy_fixture(0x1EF,1);self.academy_invoke(fixture,False)
        enabled.value = 1;self.academy_invoke(fixture)

    def test_descriptor_bounds_and_reserved_bytes_reject_intact(self):
        for number in (0,0x34,0x1DB,0x1F0,0x220,65535):
            self.academy_invoke(self.academy_fixture(number,1),False)
        for offset in (*range(12),14,15,16,17):
            fixture = self.academy_fixture(0x1EF,1)
            C.c_ubyte.from_address(C.addressof(fixture[5])+offset).value ^= 1
            self.academy_invoke(fixture,False)
        for field,value in (('player',None),('condition',1),('foreign',0),('animal',1)):
            fixture = self.academy_fixture(capital=1);setattr(fixture[2].session,field,value)
            self.academy_invoke(fixture,False)

    def test_input_control_aliases_reject_before_writes(self):
        for field in ('player','animal','remail'):
            fixture = self.academy_fixture(capital=1);old = getattr(fixture[2].session,field)
            for pointer in (C.addressof(self.active),C.addressof(fixture[-1]),fixture[1]+512,C.addressof(fixture[6])+16):
                setattr(fixture[2].session,field,pointer);self.academy_invoke(fixture,False)
            setattr(fixture[2].session,field,old)


if __name__ == '__main__': unittest.main()
