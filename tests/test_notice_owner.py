"""Transactional burial and complete English publication through the real creator."""
import ctypes as C
import struct
import unittest

import test_notice_treasure_creator as treasure_tests
from mail_record import Field, Record
from notice_record import pack
from notice_treasure import body, fields_for
from test_mail_format import CText


class NoticeOwnerTests(treasure_tests.NoticeTreasureCreatorTests):
    extra_sources=(*treasure_tests.NoticeTreasureCreatorTests.extra_sources,
                   'overlays/mail_generation/notice_owner.c','tests/notice_owner_mock.c')

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.lib.af_notice_owner_create.argtypes=[C.c_void_p]*4
        for name in ('af_npc_mail_create','af_system_mail_create','af_departed_mail_create',
                     'af_villager_event_mail_create','af_academy_mail_create','af_academy_score_mail_create',
                     'af_post_office_mail_create','af_museum_mail_create','af_shop_notice_mail_create',
                     'af_quest_reply_mail_create','af_notice_treasure_create'):
            setattr(cls.lib,name,cls.lib.af_notice_owner_create)

    def scalar(self,name,value=None):
        field=C.c_uint.in_dll(self.lib,'af_notice_owner_'+name)
        if value is not None: field.value=value
        return field.value

    def owner_fixture(self,number=0x1F0,capital=0,item=0x11FC,acre=0,unit=0,hole=0):
        fixture=self.notice_fixture(number,capital)
        self.item_name[:]=b'pitfall         ' if item==0x2512 else b'abcdefghijklmnop'
        shell=C.create_string_buffer(b'!'*(32+224+352+32))
        # Match the assembly bridge's exact stack layout, including its parent.
        destination=C.addressof(shell)+64; request=C.addressof(shell)+232; frame=request+24
        C.memmove(request,struct.pack('>4sIBBBB',b'AFNR',frame&0xFFFFFFFF,1,0,0,244),12)
        C.memmove(frame+0x66,struct.pack('>H',item),2)
        C.memmove(frame+0x10,struct.pack('>I',number),4)
        rtc=bytes.fromhex('0010091e000807ea')
        C.memmove(frame+0xC8,rtc,8); C.memmove(frame+0x140,rtc,8)
        fixture[2].session.animal=request
        for name,value in (('acre',acre),('unit',unit),('hole',hole),('mode',0),
                           ('place_calls',0),('deposit_calls',0),('post_calls',0),('rtc_calls',0)):
            self.scalar(name,value)
        fg=(C.c_ubyte*15360).in_dll(self.lib,'af_notice_owner_foreground')
        flags=(C.c_ubyte*960).in_dll(self.lib,'af_notice_owner_buried')
        fg[:]=bytes.fromhex('2030')*7680; flags[:]=bytes.fromhex('aaaa')*480
        fg[acre*512+unit*2:acre*512+unit*2+2]=bytes(2)
        (C.c_ubyte*1560).in_dll(self.lib,'af_notice_owner_board')[:]=b'B'*1560
        (C.c_ubyte*8).in_dll(self.lib,'af_notice_owner_timestamp')[:]=b'T'*8
        return fixture,shell,destination,request,frame,fg,flags

    def owner_call(self,case,success=True):
        f,shell,destination,request,frame,fg,flags=case
        before=(C.string_at(destination,164),f[-1].value,C.string_at(request,12),f[3].raw)
        self.assertEqual(self.lib.af_notice_owner_create(f[1],destination,C.byref(self.active),C.byref(f[-1])),int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((C.string_at(request,12),f[3].raw),before[2:])
        self.assertEqual(shell.raw[:32],b'!'*32)
        self.assertEqual(shell.raw[32:64],b'!'*32)
        self.assertEqual(shell.raw[228:232],b'!'*4)
        self.assertEqual(shell.raw[244:256],b'!'*12)
        self.assertEqual(shell.raw[608:640],b'!'*32)
        if not success:
            self.assertEqual((C.string_at(destination,164),f[-1].value),before[:2])
        return C.string_at(destination,164)

    def prepare(self,case):
        before_fg, before_flags=bytes(case[5]),bytes(case[6])
        frame_before=C.string_at(case[4],352)
        self.assertEqual(self.owner_call(case),bytes(164))
        self.assertEqual((self.scalar('place_calls'),self.scalar('deposit_calls'),
                          self.scalar('post_calls'),self.scalar('rtc_calls')),(1,1,0,0))
        frame=bytearray(frame_before)
        acre,unit=self.scalar('acre'),self.scalar('unit')
        frame[0x5C:0x60]=struct.pack('>I',acre//5+1);frame[0x60:0x64]=struct.pack('>I',acre%5+1)
        fg_at=acre*512+unit*2;flags_at=acre*32+(unit//16)*2
        frame[0xD0:0xE0]=(struct.pack('>II',0x8012D148+fg_at,0x801362DC+flags_at)
            +before_fg[fg_at:fg_at+2]+before_flags[flags_at:flags_at+2]
            +bytes(case[5][fg_at:fg_at+2])+b'NT')
        self.assertEqual(C.string_at(case[4],352),frame)
        return before_fg,before_flags

    def rollback_like_bridge(self,case):
        # This models the four native load/store operations; native execution
        # and actual loader-allocation failure are separate acceptance evidence.
        undo=C.string_at(case[4]+0xD0,16)
        tile,flags=struct.unpack_from('>II',undo)
        case[5][tile-0x8012D148:tile-0x8012D148+2]=undo[8:10]
        case[6][flags-0x801362DC:flags-0x801362DC+2]=undo[10:12]

    def test_owner_all_acres_units_pitfall_shapes_and_exact_undo(self):
        for acre in range(30):
            for unit in (0,15,16,127,240,255):
                case=self.owner_fixture(acre=acre,unit=unit)
                before=self.prepare(case);self.rollback_like_bridge(case)
                self.assertEqual((bytes(case[5]),bytes(case[6])),before)
        for unit in range(256):
            case=self.owner_fixture(acre=29,unit=unit,item=0x2512,hole=unit%25)
            before=self.prepare(case);self.rollback_like_bridge(case)
            self.assertEqual((bytes(case[5]),bytes(case[6])),before)

    def test_owner_all_eighteen_posts_both_capitals_publish_only_complete_message(self):
        for number in range(0x1F0,0x202):
            for capital,item in ((0,0x11FC),(1,0x11FC),(0,0x2512),(1,0x2512)):
                case=self.owner_fixture(number,capital,item,acre=(number-0x1F0)%30,unit=255,hole=24)
                self.prepare(case); f,shell,destination,request,frame,fg,flags=case
                C.c_ubyte.from_address(request+8).value=2
                body_before,rtc=C.string_at(frame+0x68,96),C.string_at(frame+0xC8,8)
                result=self.owner_call(case)
                name=next(row.name for row in self.alias_rows if row.npc_index==0)
                values={1:Field(name),2:Field(bytes(self.item_name),1),
                        3:Field(str(self.scalar('acre')//5+1).encode()),
                        4:Field(str(self.scalar('acre')%5+1).encode()),5:Field(b'Town  ')}
                record=Record(4,0,(number,),tuple((i,values[i]) for i in fields_for(number)),bool(capital))
                self.assertEqual(result[:96],pack(record))
                text=CText.from_address(f[1]+self.text)
                self.assertEqual(bytes(text.text[text.offsets[1]:text.offsets[1]+text.lengths[1]]),body(record,self.banks))
                self.assertEqual(result[:4],bytes.fromhex('7f424e01'))
                self.assertEqual(result[96:],bytes(68))
                self.assertNotEqual(result[:96],body_before)
                self.assertEqual(C.string_at(frame+0x68,104),result[:96]+rtc)
                board=bytes((C.c_ubyte*1560).in_dll(self.lib,'af_notice_owner_board'))
                self.assertEqual(board,result[:96]+rtc+b'B'*(1560-104))
                self.assertEqual(bytes((C.c_ubyte*8).in_dll(self.lib,'af_notice_owner_timestamp')),rtc)
                self.assertEqual((self.scalar('place_calls'),self.scalar('deposit_calls'),
                                  self.scalar('post_calls'),self.scalar('rtc_calls')),(1,1,1,1))

    def test_owner_failed_or_unexpected_deposit_restores_acre_before_return(self):
        for mode in (1,2,3,4,5,6,8,9):
            case=self.owner_fixture(acre=29,unit=255)
            before=bytes(case[5]),bytes(case[6]),C.string_at(case[4]+0xD0,16)
            self.scalar('mode',mode);self.owner_call(case,False)
            self.assertEqual((bytes(case[5]),bytes(case[6]),C.string_at(case[4]+0xD0,16)),before)
            self.assertEqual((self.scalar('post_calls'),self.scalar('rtc_calls')),(0,0))
        for hole in (25,255):
            case=self.owner_fixture(item=0x2512,hole=hole)
            before=bytes(case[5]),bytes(case[6]);self.owner_call(case,False)
            self.assertEqual((bytes(case[5]),bytes(case[6])),before)
        case=self.owner_fixture()
        case[5][:2]=bytes.fromhex('1234')
        before=bytes(case[5]),bytes(case[6]);self.owner_call(case,False)
        self.assertEqual((bytes(case[5]),bytes(case[6])),before)

    def test_owner_creation_failure_keeps_post_timestamp_and_undo_for_bridge(self):
        for fault in ('catalogue','article','item','template'):
            case=self.owner_fixture(0x1F0,1,acre=15,unit=133)
            before=self.prepare(case);f,shell,destination,request,frame,fg,flags=case
            C.c_ubyte.from_address(request+8).value=2
            if fault=='catalogue': C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value=0
            if fault=='article': C.c_int.in_dll(self.lib,'af_notice_test_article').value=-1
            if fault=='item': C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value=1
            if fault=='template': C.memmove(frame+0x10,struct.pack('>I',0x1F3),4)
            frame_before=C.string_at(frame,352)
            self.owner_call(case,False)
            self.assertEqual(C.string_at(frame,352),frame_before)
            self.assertEqual(bytes((C.c_ubyte*1560).in_dll(self.lib,'af_notice_owner_board')),b'B'*1560)
            self.assertEqual(bytes((C.c_ubyte*8).in_dll(self.lib,'af_notice_owner_timestamp')),b'T'*8)
            self.rollback_like_bridge(case);self.assertEqual((bytes(fg),bytes(flags)),before)
            C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value=1
            C.c_uint.in_dll(self.lib,'af_event_card_item_fail').value=0

    def test_owner_invalid_request_and_parent_relationship_do_not_bury(self):
        for offset,value in ((0,0),(4,0),(8,0),(8,3),(9,1),(10,1)):
            case=self.owner_fixture();before=bytes(case[5]),bytes(case[6])
            field=C.c_ubyte.from_address(case[3]+offset)
            field.value=field.value^1 if offset==4 else value
            self.owner_call(case,False)
            self.assertEqual((bytes(case[5]),bytes(case[6])),before)
            self.assertEqual(self.scalar('place_calls'),0)


if __name__=='__main__': unittest.main()
