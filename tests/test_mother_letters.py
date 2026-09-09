"""Complete Mom snapshots and unchanged ordinary NPC dispatch."""

import ctypes as C
import struct
import unittest

import test_npc_mail_creator as npc_tests
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Record,pack
from mother_letters import TEMPLATES,COMPLETE
from test_mail_format import CText


class MotherLetterTests(npc_tests.NpcMailCreatorTests):
    extra_sources = ('overlays/mail_generation/mother_creator.c',)

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Run the entire ordinary creator contract through the new dispatcher.
        cls.lib.af_system_mail_create.argtypes = [C.c_void_p]*4
        cls.lib.af_npc_mail_create = cls.lib.af_system_mail_create

    def mother_fixture(self,number=0x12C,capital=0,paper=63,gift=0x11FC):
        fixture = self.fixture(good=0,capital=capital)
        descriptor = b'AFMO'+struct.pack('>HH',number,gift)+bytes((paper,0,0,254))
        C.memmove(fixture[4],descriptor,12)
        return fixture

    def mother_invoke(self,fixture,success=True):
        memory,address,capture,player,request,remail,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,request.raw,remail.raw
        calls,clears = self.calls.value,self.clear_calls.value
        self.assertEqual(self.lib.af_system_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw,request.raw,remail.raw),before[2:])
        self.assertEqual((self.calls.value,self.clear_calls.value),(calls,clears))
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2])
            return
        record = Record(self.catalog_id,0,(int.from_bytes(request.raw[4:6],'big'),),(),bool(before[1]))
        expected = bytearray(164);expected[:16] = player.raw
        expected[18:30] = b' '*12;expected[30:35] = b'\xff'*5
        expected[36:38] = request.raw[6:8]
        expected[39:42] = bytes((128,4,request.raw[8]));expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,templates(self.catalog,record))
        output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        self.assertEqual(capture.session.initial_capital,before[1])

    def test_every_supported_mom_letter_both_capitals_and_native_metadata(self):
        self.assertEqual((len(TEMPLATES),len(COMPLETE)),(114,113))
        for number in TEMPLATES if self.catalog_id==4 else COMPLETE:
            for capital in (0,1):
                with self.subTest(number=f'{number:04X}',capital=capital):
                    self.mother_invoke(self.mother_fixture(number,capital,paper=number%64,gift=number))

    def test_unavailable_glyph_invalid_descriptor_and_unused_native_ids_never_publish(self):
        self.mother_invoke(self.mother_fixture(0x136,1),self.catalog_id==4)
        for number in (0,0x12B,0x182,0x183,*range(0x186,0x18A),0x1A4,65535):
            self.mother_invoke(self.mother_fixture(number,1),False)
        for offset,value in ((0,0),(1,0),(2,0),(3,0),(8,64),(9,1),(10,1),(11,6)):
            fixture = self.mother_fixture(capital=1)
            C.c_ubyte.from_address(C.addressof(fixture[4])+offset).value = value
            self.mother_invoke(fixture,False)
        for field,value in (('player',None),('condition',1),('foreign',1)):
            fixture = self.mother_fixture();setattr(fixture[2].session,field,value)
            self.mother_invoke(fixture,False)
        fixture = self.mother_fixture();fixture[2].session.remail = C.addressof(fixture[5])
        self.mother_invoke(fixture,False)

    def test_mom_dma_failure_and_disabled_catalog_retain_the_whole_letter(self):
        reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
        self.mother_invoke(self.mother_fixture())
        count = reads.value
        for index in range(1,count+1):
            reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
            self.mother_invoke(self.mother_fixture(capital=1),False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0
        self.mother_invoke(self.mother_fixture(capital=1),False)

    def test_dispatch_rejects_input_aliases_before_reading_the_marker(self):
        fixture = self.mother_fixture(capital=1)
        before = fixture[0].raw,fixture[6].raw,fixture[-1].value
        for field in ('player','animal'):
            old = getattr(fixture[2].session,field)
            for pointer in (C.addressof(self.active),C.addressof(fixture[-1]),fixture[1]+512,C.addressof(fixture[6])+16):
                setattr(fixture[2].session,field,pointer)
                self.mother_invoke(fixture,False)
            setattr(fixture[2].session,field,old)
        self.assertEqual((fixture[0].raw,fixture[6].raw,fixture[-1].value),before)


if __name__ == '__main__': unittest.main()
