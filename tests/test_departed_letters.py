"""Complete departed letters plus the entire Mom and ordinary reply contract."""

import ctypes as C
from dataclasses import replace
import struct
import unittest

import test_mother_letters as mother_tests
from audit_mail_templates import template_fields
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field,Record,pack
from test_mail_format import CText


class DepartedLetterTests(mother_tests.MotherLetterTests):
    extra_sources = (*mother_tests.MotherLetterTests.extra_sources,
                     'overlays/mail_generation/departed_creator.c','tests/departed_creator_mock.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_departed_mail_create.argtypes = [C.c_void_p]*4
        cls.lib.af_system_mail_create = cls.lib.af_departed_mail_create
        cls.lib.af_npc_mail_create = cls.lib.af_departed_mail_create

    def setUp(self):
        super().setUp()
        for name in ('looks','calls','errors'): C.c_uint.in_dll(self.lib,'af_departed_'+name).value = 0
        C.c_uint.in_dll(self.lib,'af_departed_paper').value = 63
        C.c_float.in_dll(self.lib,'af_departed_draw').value = 0.0
        (C.c_ubyte*200).in_dll(self.lib,'af_departed_fields')[:] = b'!'*200

    def departed_fixture(self,npc=0,looks=0,choice=0,capital=0):
        fixture = self.fixture(good=0,capital=capital)
        C.memmove(fixture[4],b'DM'+struct.pack('>H',0xE000+npc)+b'AWAY  '+bytes((0,253)),12)
        C.c_uint.in_dll(self.lib,'af_departed_looks').value = looks
        C.c_float.in_dll(self.lib,'af_departed_draw').value = (choice+0.25)/3
        C.c_uint.in_dll(self.lib,'af_departed_calls').value = 0
        (C.c_ubyte*200).in_dll(self.lib,'af_departed_fields')[:] = b'!'*200
        return fixture

    def departed_invoke(self,fixture,success=True):
        memory,address,capture,player,request,remail,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,request.raw,remail.raw
        self.assertEqual(self.lib.af_departed_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw,request.raw,remail.raw),before[2:])
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_departed_errors').value,0)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2]);return
        npc = int.from_bytes(request.raw[2:4],'big')-0xE000
        name = next(row.name for row in self.alias_rows if row.npc_index == npc)
        looks = C.c_uint.in_dll(self.lib,'af_departed_looks').value
        draw = C.c_float.in_dll(self.lib,'af_departed_draw').value
        number = 0xFC+looks*3+int(C.c_float(draw*3).value)
        values = (Field(player.raw[:6]),Field(name),Field(request.raw[4:10]),Field(player.raw[6:12]))
        record = Record(2,0,(number,),tuple(enumerate(values)),bool(before[1]))
        parts = templates(self.catalog,record)
        needed = set().union(*(template_fields(p) for p in parts.parts))
        record = replace(record,fields=tuple((slot,value) for slot,value in record.fields if slot in needed))
        expected = bytearray(164);expected[:16] = player.raw
        expected[18:24] = b'NATIVE';expected[24:30] = request.raw[4:10]
        expected[30:35] = bytes((npc,npc,0x30,0,1));expected[39] = 128
        expected[41] = C.c_uint.in_dll(self.lib,'af_departed_paper').value;expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,parts);output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_departed_calls').value,9)
        self.assertEqual(tuple((C.c_uint*16).in_dll(self.lib,'af_departed_log')[:9]),(1,2,3,4,5,7,9,10,11))
        expected_fields = b''.join(v.ljust(10,b' ') for v in (player.raw[:6],b'NATIVE',request.raw[4:10],player.raw[6:12]))+b'!'*160
        self.assertEqual(bytes((C.c_ubyte*200).in_dll(self.lib,'af_departed_fields')),expected_fields)
        return record

    def test_all_eighteen_letters_both_capitals_and_every_villager_full_name(self):
        for looks in range(6):
            for choice in range(3):
                for capital in range(2): self.departed_invoke(self.departed_fixture(looks,looks,choice,capital))
        for npc in range(216): self.departed_invoke(self.departed_fixture(npc,npc%6,npc%3,npc%2))

    def test_all_catalogue_failures_and_invalid_native_results_retain_letter(self):
        reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
        self.departed_invoke(self.departed_fixture())
        count = reads.value
        for index in range(1,count+1):
            reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
            self.departed_invoke(self.departed_fixture(capital=1),False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0
        self.departed_invoke(self.departed_fixture(capital=1),False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1
        for key,value in (('looks',6),('paper',64)):
            fixture = self.departed_fixture();C.c_uint.in_dll(self.lib,'af_departed_'+key).value = value
            self.departed_invoke(fixture,False)
            C.c_uint.in_dll(self.lib,'af_departed_'+key).value = 0
        for value in (-0.1,1.0,float('nan')):
            fixture = self.departed_fixture();C.c_float.in_dll(self.lib,'af_departed_draw').value = value
            self.departed_invoke(fixture,False)

    def test_descriptor_fields_source_corruption_and_oversized_npc_ids_reject_before_rng(self):
        for offset,value in ((0,0),(1,0),(2,0),(3,216),(10,1),(11,6)):
            fixture = self.departed_fixture(capital=1)
            C.c_ubyte.from_address(C.addressof(fixture[4])+offset).value = value
            self.departed_invoke(fixture,False)
            self.assertEqual(C.c_uint.in_dll(self.lib,'af_departed_calls').value,0)
        for resource in (self.words_memory,self.alias_memory):
            fixture = self.departed_fixture(capital=1);resource[-1] ^= 1
            self.departed_invoke(fixture,False);resource[-1] ^= 1
            self.assertEqual(C.c_uint.in_dll(self.lib,'af_departed_calls').value,0)


if __name__ == '__main__': unittest.main()
