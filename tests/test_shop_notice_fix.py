"""Remove only the native hiring placard, matching the supplied English room."""
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256
from shop_notice_fix import OWNER, TRIANGLES, NOOP, build, in_triangle, patch_room
from map_artwork import compile_commands


class TriangleTests(unittest.TestCase):
    def test_background_membership_handles_edges_winding_and_degenerate_faces(self):
        triangle = [(0, 0), (10, 0), (0, 10)]
        for point in ((0, 0), (5, 0), (3, 3), (5, 5)):
            self.assertTrue(in_triangle(point, triangle))
            self.assertTrue(in_triangle(point, triangle[::-1]))
        for point in ((-1, 0), (6, 6), (0, 11)):
            self.assertFalse(in_triangle(point, triangle))
        self.assertFalse(in_triangle((5, 0), [(0, 0), (5, 0), (10, 0)]))


@unittest.skipUnless((ROOT/'build/v1rc1/Animal Forest English V1RC1.z64').is_file(),
                     'V1RC1 and supplied native/GC sources required')
class ShopNoticeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1rc1/Animal Forest English V1RC1.z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.original = by_vrom(cls.native)[OWNER].extract(cls.native)
        with tempfile.TemporaryDirectory(prefix='shop-notice-command-', dir=ROOT/'build') as output:
            cls.compiled = compile_commands(Path(output), ROOT/'overlays/fishing/artwork.c',
                                            (('remove', 8),))['remove']

    def test_only_two_notice_triangles_removed_and_matching_wall_retained(self):
        changed, evidence = patch_room(self.original, self.rel, self.symbols, NOOP)
        self.assertEqual(changed[:TRIANGLES], self.original[:TRIANGLES])
        self.assertEqual(changed[TRIANGLES+8:], self.original[TRIANGLES+8:])
        self.assertEqual(changed[TRIANGLES:TRIANGLES+8], NOOP)
        self.assertEqual(evidence['omitted_triangles'], [[0, 1, 2], [0, 2, 3]])
        self.assertEqual(evidence['english_wall_triangles'], 28)
        self.assertEqual(self.compiled, NOOP)

    def test_complete_patch_reconstructs_and_every_other_resource_is_retained(self):
        image, patch, report = build(self.native, self.base, self.rel, self.symbols, NOOP)
        self.assertEqual(sha256(image), '5ccd35ba077e3abf1d1ab90d919c095343ff404884b504ca14ea709a04ec1dfc')
        self.assertEqual(apply_ups(self.native, patch), image)
        self.assertEqual(len(image), 0x2000000)
        before, after = by_vrom(self.base), by_vrom(image)
        self.assertEqual(set(before), set(after))
        for v, old in before.items():
            self.assertEqual((old.index, old.size), (after[v].index, after[v].size))
            if v not in (OWNER, 0x19D40):
                self.assertEqual(old.extract(self.base), after[v].extract(image), f'{v:08X}')
        self.assertFalse(report['cpu_code_changed'])
        self.assertFalse(report['allocation_changed'])
        self.assertFalse(report['save_format_changed'])

    def test_changed_sources_predecessor_and_command_are_rejected(self):
        for original, rel, symbols, command in (
                (self.original[:-1], self.rel, self.symbols, NOOP),
                (self.original, self.rel[:-1], self.symbols, NOOP),
                (self.original, self.rel, self.symbols+b'\n', NOOP),
                (self.original, self.rel, self.symbols, bytes(8))):
            with self.assertRaises(ValueError): patch_room(original, rel, symbols, command)
        with self.assertRaises(ValueError):
            build(self.native, self.base[:-1], self.rel, self.symbols, NOOP)


if __name__ == '__main__': unittest.main()
