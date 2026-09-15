"""Verify the current data-only credit correction without replaying old builds."""
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from textbanks import Bank
import credits_title_fix as fix

class CreditsTitleTests(unittest.TestCase):
    def test_current_v2_and_v3_outputs_change_one_string(self):
        for kind,out in (('v2','v2-official-credits-12'),('v3','v3-official-credits-01')):
            folder,name,digest=fix.BASES[kind]
            base=(ROOT/folder/(name+'.z64')).read_bytes()
            image=(ROOT/'build'/out/(name+'.z64')).read_bytes()
            self.assertEqual(sha256(base),digest); self.assertEqual(fix.patch(base),image)
            a,b=by_vrom(base),by_vrom(image)
            old=Bank('string',0,0,a[fix.DATA].extract(base),a[fix.TABLE].extract(base)).entries()
            new=Bank('string',0,0,b[fix.DATA].extract(image),b[fix.TABLE].extract(image)).entries()
            self.assertEqual(len(new),len(old));self.assertEqual(new[fix.TITLE],b'Animal Crossing')
            new[fix.TITLE]=old[fix.TITLE];self.assertEqual(new,old)
            self.assertEqual(b[fix.DATA].size,a[fix.DATA].size+2)
            self.assertEqual(b[fix.DATA].pstart,a[fix.DATA].pstart)

    def test_unknown_source_rejects(self):
        with self.assertRaises(ValueError):fix.patch(bytes(64))

if __name__=='__main__':unittest.main()
