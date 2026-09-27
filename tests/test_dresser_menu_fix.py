"""Bind the actual dresser menu to its native actions without other changes."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom, sha256, n64_checksum, apply_ups
import dresser_menu_fix as fix


@unittest.skipUnless((fix.BASE/(fix.NAME+'.z64')).is_file(), 'Private V2 build required')
class DresserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (fix.BASE/(fix.NAME+'.z64')).read_bytes()
        cls.image = (ROOT/'build/v2-dresser-14'/(fix.NAME+'.z64')).read_bytes()

    def test_only_menu_order_and_action_comparison_change(self):
        image,receipt = fix.patch(self.native,self.base)
        self.assertEqual(image,self.image)
        old,new = by_vrom(self.base),by_vrom(image)
        self.assertEqual(old,new)
        self.assertEqual(receipt['actions'],['remove','swap','cancel'])
        for v,e in old.items():
            a,b=e.extract(self.base),new[v].extract(image)
            differences=[i for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            if v==fix.ROOM:
                self.assertEqual(differences,[fix.DECISION-fix.ROOM_RAM+3])
                self.assertEqual(b[fix.DECISION-fix.ROOM_RAM:fix.DECISION-fix.ROOM_RAM+4],bytes.fromhex('24010002'))
            elif v==receipt['message_vrom']:
                self.assertEqual(len(differences),2)
                self.assertEqual(b[differences[0]],0xE9)
                self.assertEqual(b[differences[1]],0x0D)
            else:self.assertEqual(a,b,hex(v))

    def test_guards_reject_partial_or_changed_inputs(self):
        for v,offset in ((fix.ROOM,fix.DECISION-fix.ROOM_RAM), (fix.ROOM,fix.HANDLER-fix.ROOM_RAM)):
            changed=bytearray(self.base);entry=by_vrom(changed)[v]
            changed[entry.pstart+offset]^=1
            with self.assertRaises(ValueError):fix.patch(self.native,changed)
        with self.assertRaises(ValueError):fix.patch(self.native,self.image)
        with self.assertRaises(ValueError):fix.patch(bytes(len(self.native)),self.base)

    def test_current_checksum_receipt_and_patch(self):
        directory=ROOT/'build/v2-dresser-14'; report=json.loads((directory/'build.json').read_bytes())
        self.assertEqual(report['output_sha256'],sha256(self.image))
        self.assertFalse(report['dresser_menu']['saved_format_changed'])
        self.assertFalse(report['dresser_menu']['allocation_changed'])
        self.assertEqual(struct.unpack_from('>2I',self.image,16),n64_checksum(self.image))
        self.assertEqual(apply_ups(self.native,(directory/(fix.NAME+'.ups')).read_bytes()),self.image)


if __name__=='__main__':unittest.main()
