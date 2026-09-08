"""Full event, birthday, goodbye, and Christmas creation plus earlier contracts."""

import ctypes as C
from dataclasses import replace
import struct
import unittest

import test_departed_letters as departed_tests
from audit_mail_templates import template_fields
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field,Record,pack
from test_mail_format import CText
from villager_event_letters import EVENT,BIRTHDAY,GOODBYE,CHRISTMAS,COMPLETE


class VillagerEventCreatorTests(departed_tests.DepartedLetterTests):
    extra_sources = (*departed_tests.DepartedLetterTests.extra_sources,
                     'overlays/mail_generation/villager_event_creator.c','tests/villager_event_creator_mock.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_villager_event_mail_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create','af_system_mail_create','af_departed_mail_create'):
            setattr(cls.lib,name,cls.lib.af_villager_event_mail_create)

    def setUp(self):
        super().setUp()
        for name in ('calls','id','fail'): C.c_uint.in_dll(self.lib,'af_event_card_item_'+name).value = 0
        self.item_name = (C.c_ubyte*16).in_dll(self.lib,'af_event_card_item_name')
        self.item_name[:] = b'abcdefghijklmnop'

    def event_fixture(self,number=0x60,capital=0,npc=0,paper=63,gift=0x11FC):
        fixture = self.fixture(foreign=1,good=0,capital=capital)
        fixture[2].session.animal = None
        first = 0x60 if number in EVENT else 0xEA if number in BIRTHDAY else 0x20E
        identity = bytes(12) if number in CHRISTMAS else struct.pack('>HH',0xE000+npc,0x3002)+b'AWAY  '+bytes((13,(number-first)//3))
        descriptor = identity+struct.pack('>HH',number,0 if number in GOODBYE else gift)+bytes((252,22 if number in CHRISTMAS else paper))
        C.memmove(fixture[5],descriptor,18)
        C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value = 0
        C.c_uint.in_dll(self.lib,'af_departed_calls').value = 0
        return fixture

    def event_invoke(self,fixture,success=True):
        memory,address,capture,player,animal,request,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,animal.raw,request.raw
        self.assertEqual(self.lib.af_villager_event_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw,animal.raw,request.raw),before[2:])
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(bytes(self.words_memory),self.words);self.assertEqual(bytes(self.alias_memory),self.aliases)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2]);return
        number = int.from_bytes(request.raw[12:14],'big')
        fields = ()
        if number not in CHRISTMAS:
            npc = int.from_bytes(request.raw[:2],'big')-0xE000
            name = next(row.name for row in self.alias_rows if row.npc_index == npc)
            fields = ((0,Field(player.raw[:6])),(6 if number in EVENT else 1,Field(name)))
            if number in GOODBYE: fields += ((3,Field(b'HERE  ')),)
            if number in (0xEF,0xF1,0xF4,0xFB): fields += ((2,Field(bytes(self.item_name))),)
        record = Record(2,0,(number,),fields,bool(before[1]))
        parts = templates(self.catalog,record)
        needed = set().union(*(template_fields(p) for p in parts.parts))
        record = replace(record,fields=tuple(sorted((i,v) for i,v in fields if i in needed)))
        expected = bytearray(164);expected[:16] = player.raw
        if number in CHRISTMAS:
            expected[18:30] = b' '*12;expected[30:35] = b'\xff'*5
        else:
            expected[18:24] = b'NATIVE';expected[24:30] = request.raw[4:10]
            expected[30:35] = bytes((npc,request.raw[10],request.raw[2],request.raw[3],1))
        expected[36:38] = request.raw[14:16]
        expected[39:42] = bytes((128,int(number in CHRISTMAS),request.raw[17]));expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,parts);output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        calls = C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value
        self.assertEqual(calls,int(number in (0xEF,0xF1,0xF4,0xFB)))
        if calls: self.assertEqual(C.c_uint.in_dll(self.lib,'af_event_card_item_id').value,int.from_bytes(request.raw[14:16],'big'))

    def test_every_complete_letter_both_capitals_and_all_villager_names(self):
        self.assertEqual(len(COMPLETE),54)
        for number in COMPLETE:
            for capital in (0,1):
                with self.subTest(number=f'{number:04X}',capital=capital):
                    self.event_invoke(self.event_fixture(number,capital,paper=number%64))
        for npc in range(216):
            for number in (0x61,0xEF,0x214): self.event_invoke(self.event_fixture(number,npc%2,npc=npc))

    def test_unused_item_loads_do_not_block_other_birthday_letters(self):
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 1
        for number in BIRTHDAY:
            self.event_invoke(self.event_fixture(number,1),number not in (0xEF,0xF1,0xF4,0xF6,0xFB))
        for number in (0x61,0x214,0xD7): self.event_invoke(self.event_fixture(number,1))

    def test_catalogue_failures_and_unavailable_semicolon_retain_complete_destination(self):
        reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
        self.event_invoke(self.event_fixture(0xEF));count = reads.value
        for index in range(1,count+1):
            reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
            self.event_invoke(self.event_fixture(0xEF,1),False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
        self.event_invoke(self.event_fixture(0xF6,1),False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0
        for number in (0x61,0xEF,0x214,0xD7): self.event_invoke(self.event_fixture(number,1),False)

    def test_descriptor_and_control_aliases_reject_without_partial_publication(self):
        for field,value in (('player',None),('condition',1),('foreign',0),('animal',1)):
            fixture = self.event_fixture(capital=1);setattr(fixture[2].session,field,value)
            self.event_invoke(fixture,False)
        for offset,value in ((0,0),(1,216),(11,6),(12,255),(13,255),(16,6),(17,64)):
            fixture = self.event_fixture(capital=1);C.c_ubyte.from_address(C.addressof(fixture[5])+offset).value = value
            self.event_invoke(fixture,False)
        for number in (0x60,0x20E,0xD7):
            fixture = self.event_fixture(number,1);C.c_ubyte.from_address(C.addressof(fixture[5])+14).value ^= 1
            if number != 0x20E:
                C.memset(C.addressof(fixture[5])+14,0,2)
            self.event_invoke(fixture,False)
        for field in ('player','animal','remail'):
            fixture = self.event_fixture(capital=1);old = getattr(fixture[2].session,field)
            for pointer in (C.addressof(self.active),C.addressof(fixture[-1]),fixture[1]+512,C.addressof(fixture[6])+16):
                setattr(fixture[2].session,field,pointer);self.event_invoke(fixture,False)
            setattr(fixture[2].session,field,old)


if __name__ == '__main__': unittest.main()
