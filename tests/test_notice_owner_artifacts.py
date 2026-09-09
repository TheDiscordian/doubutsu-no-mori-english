"""Bind MIPS treasure ownership to exact code, resources, and guarded native slots."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from npc_mail_capture import validate as validate_creator
from npc_mail_loader import configuration
from notice_treasure_owner import START,END,SYMBOLS,RANGES,expected,patch,validate

DIRECTORY=ROOT/'build/noticeboard-treasure'


@unittest.skipUnless((DIRECTORY/'owners/owners.json').is_file(),'Local compiled treasure owner required')
class NoticeOwnerArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.module=json.loads((ROOT/'build/notice-treasure-runtime/module.json').read_text())
        cls.data=(DIRECTORY/'owners/owners.bin').read_bytes()
        cls.report=json.loads((DIRECTORY/'owners/owners.json').read_text())
        cls.creator=(DIRECTORY/'owner-creator/overlay.bin').read_bytes()
        cls.reloc=(DIRECTORY/'owner-creator/relocation.bin').read_bytes()
        cls.creator_report=json.loads((DIRECTORY/'owner-creator/overlay.json').read_text())
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.code=by_vrom(cls.native)[CODE_VROM].extract(cls.native)

    def test_independent_bridges_and_complete_instruction_encoding(self):
        self.assertEqual((len(self.data),sha256(self.data)),
                         (176,'c9d5f554774e693859c185a28789458201c29edb6a7218dac1c17b0d653c5596'))
        self.assertEqual(self.data,expected(0x80197BB4))
        self.assertEqual(self.report['symbols'],SYMBOLS)
        validate(self.data,self.report,self.module)
        for name in ('owners.bin','owners.json'):
            self.assertEqual((DIRECTORY/'owners'/name).read_bytes(),(DIRECTORY/'owners-repeat'/name).read_bytes())

    def test_independent_complete_creator_and_actual_loader_entry(self):
        self.assertEqual((len(self.creator),sha256(self.creator)),
                         (48752,'d68503a283a0186402c70a4f1c6969702fb76a3b6ee9da01f82f6ff25cebd9a8'))
        self.assertEqual((len(self.reloc),sha256(self.reloc)),
                         (752,'434c01f2c661f8b6376485bbe50bb1ee54cb51e2d6fb95f51a5dd011e872df86'))
        for name in ('overlay.bin','relocation.bin','overlay.json'):
            self.assertEqual((DIRECTORY/'owner-creator'/name).read_bytes(),
                             (DIRECTORY/'owner-creator-repeat'/name).read_bytes())
        validate_creator(self.creator,self.reloc,self.creator_report,self.module)
        config=configuration(self.creator,self.reloc,self.creator_report,self.module)
        self.assertEqual(config[1:4],[49504,48752,752])
        self.assertEqual(config[4],self.creator_report['symbols']['af_notice_owner_create'])
        text,data,rodata,bss,_=struct.unpack_from('>5I',self.reloc)
        self.assertEqual((text+rodata,data,bss),(48752,0,0))

    def test_exact_native_changes_and_unchanged_original_deposit_rng_and_timing(self):
        result=patch(self.code,self.data,self.report,self.module)
        self.assertEqual(len(result),len(self.code))
        intervals=[(START,END),(0x800A6170,0x800A6174),(0x800A6214,0x800A6218),
                   (0x800A62A0,0x800A62A4),(0x800A62A8,0x800A62C0),
                   (0x8008EA8C,0x8008EA90),(0x8008EC44,0x8008EC48)]
        start=0
        for lo,hi in sorted(intervals):
            self.assertEqual(result[start:lo-CODE_RAM],self.code[start:lo-CODE_RAM])
            start=hi-CODE_RAM
        self.assertEqual(result[start:],self.code[start:])
        self.assertEqual(result[START-CODE_RAM:END-CODE_RAM],self.data)
        self.assertEqual(result[0x800A62A8-CODE_RAM:0x800A62C0-CODE_RAM],bytes(24))
        # The original store in the placement-entry delay slot must survive.
        self.assertEqual(struct.unpack_from('>I',result,0x8008EA90-CODE_RAM)[0],0xAFA5009C)
        with self.assertRaises(ValueError): patch(result,self.data,self.report,self.module)
        for lo,hi,digest in RANGES:
            source=bytearray(self.code);source[lo-CODE_RAM]^=1
            with self.assertRaises(ValueError): patch(source,self.data,self.report,self.module)

    def test_changed_code_manifest_loader_or_variant_is_rejected(self):
        for offset in range(0,len(self.data),4):
            data=bytearray(self.data);data[offset]^=1
            report=copy.deepcopy(self.report);report['sha256']=sha256(data)
            with self.assertRaises(ValueError): validate(data,report,self.module)
        for value in (False,1,'true'):
            report=copy.deepcopy(self.creator_report);report['notice_owner']=value
            with self.assertRaises(ValueError): validate_creator(self.creator,self.reloc,report,self.module)
        module=copy.deepcopy(self.module);module['symbols']['af_npc_mail_load']='80197BB8'
        report=copy.deepcopy(self.report);report['loader_ram']=0x80197BB8
        data=expected(0x80197BB8);report['sha256']=sha256(data)
        with self.assertRaises(ValueError): validate(data,report,module)

    def test_previous_complete_treasure_and_quest_creators_remain_verifiable(self):
        for directory in (DIRECTORY/'article-creator',ROOT/'build/quest-reply-creator'):
            validate_creator((directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes(),
                             json.loads((directory/'overlay.json').read_text()),self.module)


if __name__=='__main__': unittest.main()
