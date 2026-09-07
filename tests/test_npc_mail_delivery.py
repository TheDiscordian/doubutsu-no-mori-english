"""Only three guarded instructions change in the NPC submission failure gate."""

from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom
from npc_mail_delivery import START,END,CREATOR_CALL,FAILURE_BRANCH,ARGUMENT_MOVE,FAILURE_RETURN,patch,creator_fixture
from test_retail import ROM_PATH


class CreatorFixtureTests(unittest.TestCase):
    def test_o32_fixture_records_all_six_arguments_and_poisons_v1(self):
        data = creator_fixture(0x802F8010)
        words = struct.unpack('>16I',data)
        self.assertEqual(words[:2],(0x3C08802F,0x35088010))
        self.assertEqual(words[2:6],(0xAD040000,0xAD050004,0xAD060008,0xAD07000C))
        self.assertEqual(words[6:10],(0x8FA90010,0xAD090010,0x8FA90014,0xAD090014))
        self.assertEqual(words[10:],(0x8D090018,0x25290001,0xAD090018,0x8D02001C,0x03E00008,0x34035A5A))
        for address in (0,True,-1,0x80200001,0x803FFFF0,0x80400000,0xA0200000):
            with self.assertRaises(ValueError): creator_fixture(address)


@unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
class NativeNpcDeliveryGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = ROM_PATH.read_bytes()
        code = by_vrom(rom)[CODE_VROM].extract(rom)
        cls.original = code[START-CODE_RAM:END-CODE_RAM]

    def test_exact_three_changes_and_failure_return_skips_stale_v1(self):
        for creator in (0x80194B00,0x802F8010,0x803FFFFC):
            changed = patch(self.original,creator)
            self.assertEqual(len(changed),len(self.original))
            touched = {START+i for i in range(0,len(changed),4) if changed[i:i+4] != self.original[i:i+4]}
            self.assertEqual(touched,{CREATOR_CALL,FAILURE_BRANCH,ARGUMENT_MOVE})
            word = struct.unpack_from('>I',changed,CREATOR_CALL-START)[0]
            self.assertEqual(word>>26,3)
            self.assertEqual(0x80000000|((word&0x3FFFFFF)<<2),creator)
            word = struct.unpack_from('>I',changed,FAILURE_BRANCH-START)[0]
            self.assertEqual(word>>16,0x1040)
            self.assertEqual(FAILURE_BRANCH+4+(word&0xFFFF)*4,FAILURE_RETURN)
            self.assertEqual(FAILURE_RETURN,0x800A917C)
            self.assertEqual(struct.unpack_from('>I',changed,ARGUMENT_MOVE-START)[0],0x00402025)

    def test_whole_original_function_and_creator_address_are_required(self):
        for at in range(len(self.original)):
            changed = bytearray(self.original);changed[at] ^= 1
            with self.assertRaises(ValueError): patch(changed,0x80200000)
        for data in (b'',self.original[:-1],self.original+b'\0'):
            with self.assertRaises(ValueError): patch(data,0x80200000)
        for target in (None,True,-1,0,0x80200001,START,END-4,0x80400000,0xA0200000):
            with self.assertRaises(ValueError): patch(self.original,target)


if __name__ == '__main__': unittest.main()
