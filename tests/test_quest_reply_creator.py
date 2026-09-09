"""Complete quest replies and unchanged earlier creator dispatch contracts."""
import ctypes as C
import struct
import unittest

import test_shop_notice_creator as shop_tests
from audit_quest_reply_letters import ITEM_FIELDS,TEMPLATES,audit
from mail_catalog import templates
from mail_format import format_letter
from mail_record import Field,Record,pack
from test_mail_format import CText
from test_npc_mail_creator import ROOT


class QuestReplyCreatorTests(shop_tests.ShopNoticeCreatorTests):
    extra_sources = (*shop_tests.ShopNoticeCreatorTests.extra_sources,
                     'overlays/mail_generation/quest_reply_creator.c','tests/quest_reply_creator_mock.c')
    catalog_id = 4
    catalog_path = ROOT/'build/mail-glyph-catalog/catalog.bin'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_quest_reply_mail_create.argtypes = [C.c_void_p]*4
        for name in ('af_npc_mail_create','af_system_mail_create','af_departed_mail_create',
                     'af_villager_event_mail_create','af_academy_mail_create','af_academy_score_mail_create',
                     'af_post_office_mail_create','af_museum_mail_create','af_shop_notice_mail_create'):
            setattr(cls.lib,name,cls.lib.af_quest_reply_mail_create)

    def quest_fixture(self,number=0x8D,npc=0,capital=0,item=0x11FC):
        rank,looks = divmod(number-0x75,6)
        fixture = self.fixture(foreign=1,good=0,looks=looks,capital=capital)
        C.memmove(fixture[4],struct.pack('>HH6sBB',0xE000+npc,0x1234,b'AWAY  ',npc,looks),12)
        C.memmove(fixture[5],struct.pack('>4sBBH8sBB',b'AFQR',rank,0,item,bytes(8),246,0),18)
        for name in ('af_quest_reply_calls','af_quest_reply_errors','af_quest_reply_item',
                     'af_event_card_item_calls','af_departed_calls'):
            C.c_uint.in_dll(self.lib,name).value = 0
        (C.c_ubyte*200).in_dll(self.lib,'af_quest_reply_fields')[:] = b'!'*200
        return fixture

    def quest_invoke(self,fixture,success=True,preflight=False):
        memory,address,capture,player,animal,request,destination,capital = fixture
        before = destination.raw,capital.value,player.raw,animal.raw,request.raw
        before_work = memory.raw;old_calls,old_clears = self.calls.value,self.clear_calls.value
        self.assertEqual(self.lib.af_quest_reply_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw,animal.raw,request.raw),before[2:])
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(self.calls.value,old_calls)
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_quest_reply_errors').value,0)
        if not success:
            self.assertEqual((destination.raw,capital.value),before[:2])
            if preflight:
                self.assertEqual(memory.raw,before_work);self.assertEqual(self.clear_calls.value,old_clears)
                self.assertEqual(C.c_uint.in_dll(self.lib,'af_quest_reply_calls').value,0)
            return
        number = 0x75+request.raw[4]*6+animal.raw[11];item = int.from_bytes(request.raw[6:8],'big')
        npc = int.from_bytes(animal.raw[:2],'big')-0xE000
        name = next(r.name for r in self.alias_rows if r.npc_index==npc)
        fields = ((0,Field(bytes(self.item_name))),) if number in ITEM_FIELDS else ()
        fields += ((6,Field(name)),)
        record = Record(4,0,(number,),fields,bool(before[1]))
        expected = bytearray(164);expected[:16] = player.raw
        expected[18:24] = b'NATIVE';expected[24:30] = animal.raw[4:10]
        expected[30:35] = bytes((npc,animal.raw[10],animal.raw[2],animal.raw[3],1))
        expected[36:38] = request.raw[6:8];expected[39:42] = bytes((128,0,22));expected[42:] = pack(record)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        letter = format_letter(record,templates(self.catalog,record));output = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(output.text[o:o+n]) for o,n in zip(output.offsets,output.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        self.assertEqual(self.clear_calls.value,old_clears+1)
        count = 4 if item else 2
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_quest_reply_calls').value,count)
        self.assertEqual(list((C.c_uint*4).in_dll(self.lib,'af_quest_reply_log')[:count]),list(range(1,count+1)))
        self.assertEqual(bytes((C.c_ubyte*12).in_dll(self.lib,'af_quest_reply_animal')),animal.raw)
        expected_fields = bytearray(b'!'*200);expected_fields[60:70] = b'NATIVE    '
        if item: expected_fields[:10] = b'OLD ITEM  '
        self.assertEqual(bytes((C.c_ubyte*200).in_dll(self.lib,'af_quest_reply_fields')),bytes(expected_fields))
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_event_card_item_calls').value,int(number in ITEM_FIELDS))
        return record,letter

    def test_quest_source_binds_all_216_parts_and_exact_field_differences(self):
        report = audit((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),self.catalog)
        self.assertEqual(report['templates'],list(TEMPLATES));self.assertEqual(len(report['parts']),216)
        self.assertEqual([p['id'] for p in report['parts'] if p['fields']!=p['native_fields']],['mail:0098','mail:00B8'])
        self.assertFalse(report['installed'])

    def test_quest_all_ranks_personalities_capitals_complete_names_and_items(self):
        for number in TEMPLATES:
            for capital in (0,1):
                for item in ((0x11FC,) if number in ITEM_FIELDS else (0,0x11FC)):
                    for name in (b'abcdefghijklmnop',b'orange box      ',b'apple           '):
                        self.item_name[:] = name
                        self.quest_invoke(self.quest_fixture(number,capital=capital,item=item))
        for npc in range(216):
            self.quest_invoke(self.quest_fixture(0x75+npc%72,npc,npc%2))

    def test_quest_invalid_descriptors_and_identities_retain_outputs(self):
        for offset,value in ((0,0),(1,0),(2,0),(3,0),(4,12),(4,255),(5,1),(8,1),(9,1),
                             (10,1),(11,1),(12,1),(13,1),(14,1),(15,1),(17,1)):
            f = self.quest_fixture(capital=1);C.c_ubyte.from_address(C.addressof(f[5])+offset).value = value
            self.quest_invoke(f,False,True)
        for field,value in (('player',None),('player',1),('animal',None),('animal',1),('condition',1),('foreign',0)):
            f = self.quest_fixture(capital=1);setattr(f[2].session,field,value);self.quest_invoke(f,False,True)
        for offset,value in ((0,0),(1,216),(11,6),(11,255)):
            f = self.quest_fixture(capital=1);C.c_ubyte.from_address(C.addressof(f[4])+offset).value = value
            self.quest_invoke(f,False,True)
        for number in ITEM_FIELDS: self.quest_invoke(self.quest_fixture(number,item=0),False,True)
        for field in ('player','animal','remail'):
            for where in ('active','capital','work','destination'):
                f = self.quest_fixture(capital=1)
                pointer = {'active':C.addressof(self.active),'capital':C.addressof(f[-1]),
                           'work':f[1]+512,'destination':C.addressof(f[6])+16}[where]
                setattr(f[2].session,field,pointer);self.quest_invoke(f,False,True)

    def test_quest_catalogue_item_name_failures_and_retry(self):
        reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads')
        for number in TEMPLATES:
            reads.value = 0;self.quest_invoke(self.quest_fixture(number,capital=1));count = reads.value
            for index in range(1,count+1):
                reads.value = 0;C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
                self.quest_invoke(self.quest_fixture(number,capital=1),False)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = 0
        for resource in (self.words_memory,self.alias_memory):
            resource[-1] ^= 1;self.quest_invoke(self.quest_fixture(capital=1),False);resource[-1] ^= 1
        f = self.quest_fixture(capital=1)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0;self.quest_invoke(f,False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1
        self.quest_invoke(self.quest_fixture(capital=1))
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 1
        for number in ITEM_FIELDS: self.quest_invoke(self.quest_fixture(number,capital=1),False)
        for number in (0x75,0x98,0xB8): self.quest_invoke(self.quest_fixture(number,capital=1))
        C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value = 0
        self.item_name[:] = b'\x7f'+b'!'*15;self.quest_invoke(self.quest_fixture(capital=1),False)


if __name__=='__main__': unittest.main()
