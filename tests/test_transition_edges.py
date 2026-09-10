"""The edge correction preserves every byte outside one bound scale constant."""
import struct
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,apply_ups,by_vrom
from transition_edges import SCALE,NEW,build,projected_bounds

@unittest.skipUnless((ROOT/'build/v1-font-edges-03/animal-forest-font-edges.z64').is_file(),'Font-edge candidate required')
class TransitionEdgesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/v1-font-edges-03/animal-forest-font-edges.z64').read_bytes()
        cls.image,cls.patch,cls.report=build(cls.native,cls.base)

    def test_only_the_bound_constant_changes(self):
        old,new=by_vrom(self.base),by_vrom(self.image)
        self.assertEqual(set(old),set(new))
        for v,entry in old.items():
            before,after=entry.extract(self.base),new[v].extract(self.image)
            self.assertEqual(entry.index,new[v].index)
            if v==CODE_VROM:
                self.assertEqual(before[:SCALE],after[:SCALE])
                self.assertEqual(before[SCALE+4:],after[SCALE+4:])
                self.assertEqual(after[SCALE:SCALE+4],NEW)
            elif v!=0x19D40:self.assertEqual(before,after,hex(v))
        for key in ('transition_timing_changed','allocation_changed','save_format_changed'):
            self.assertFalse(self.report[key])

    def test_bounds_include_all_screen_edges_after_fixed_point_conversion(self):
        left,top,right,bottom=projected_bounds(struct.unpack('>f',NEW)[0])
        self.assertLess(left,-1);self.assertLess(top,-1)
        self.assertGreater(right,321);self.assertGreater(bottom,241)
        self.assertGreater(projected_bounds(0.019)[1],1)

    def test_complete_patch_and_source_rejection(self):
        self.assertEqual(apply_ups(self.native,self.patch),self.image)
        self.assertEqual(len(self.image),0x2000000)
        with self.assertRaises(ValueError):build(self.native,self.native)
        changed=bytearray(self.base);changed[-1]^=1
        with self.assertRaises(ValueError):build(self.native,changed)

if __name__=='__main__':unittest.main()
