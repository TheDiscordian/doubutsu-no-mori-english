"""Source-bound map labels retain live selectors and use the complete GC acre layout."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups
from map_artwork import (VROM, VERTICES, QUADS, DONORS, compile_commands, port_quad,
                         patch_assets, build)
from title_assets import DATA_BASE, pack4, untile


class MapQuadTests(unittest.TestCase):
    def test_reorders_donor_corners_without_reversing_native_winding(self):
        old = b''.join(struct.pack('>3hH2h4B', x, y, 0, 0, s, t, 170, 170, 170, 170)
            for x, y, s, t in ((0, 0, 0, 512), (40, 0, 2048, 512), (40, 20, 2048, 0), (0, 20, 0, 0)))
        donor = b''.join(struct.pack('>3hH2h4B', x, y, 0, 1, s, t, 160, 160, 160, 160)
            for x, y, s, t in ((-98, 22, 0, 0), (-98, 8, 0, 512), (-70, 22, 1024, 0), (-70, 8, 1024, 512)))
        result = list(struct.iter_unpack('>3hH2h4B', port_quad(old, donor)))
        self.assertEqual([v[:2] for v in result], [(-980, 80), (-700, 80), (-700, 220), (-980, 220)])
        self.assertEqual([v[4:6] for v in result], [(0, 512), (1024, 512), (1024, 0), (0, 0)])
        self.assertTrue(all(v[3] == 0 and v[6:] == (170,)*4 for v in result))
        with self.assertRaises(ValueError): port_quad(old[:-1], donor)
        with self.assertRaises(ValueError): port_quad(bytes(64), donor)


@unittest.skipUnless((ROOT/'build/shop-artwork-02/build.json').is_file(), 'Local supplied assets required')
class MapArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        baseline = ROOT/'build/shop-artwork-02'
        cls.base = (baseline/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((baseline/'build.json').read_text())
        with tempfile.TemporaryDirectory(prefix='af-map-native-gbi-') as directory:
            cls.commands = compile_commands(Path(directory))

    def test_actual_donor_pixels_and_geometry_and_all_other_asset_bytes(self):
        data, profile = patch_assets(self.native, self.rel, self.symbols, self.commands)
        original = by_vrom(self.native)[VROM].extract(self.native)
        self.assertEqual(len(data), 51856)
        self.assertEqual(len(profile['donor_texture_pointers']), 2)
        for row, width, target in zip(DONORS, (64, 32), (0xAB4B60, 0xAB8460)):
            donor = self.rel[DATA_BASE+row.gc:DATA_BASE+row.gc+width*8]
            converted = pack4(untile(donor, width, 16, 4))
            self.assertEqual(data[target-VROM:target-VROM+512], converted+bytes(512-len(converted)))
        self.assertEqual(data[0xAB8260-VROM:0xAB8260-VROM+512], bytes(512))
        for address, index in QUADS:
            start = address-VROM
            out = list(struct.iter_unpack('>3hH2h4B', data[start:start+64]))
            old = list(struct.iter_unpack('>3hH2h4B', original[start:start+64]))
            gc = list(struct.iter_unpack('>3hH2h4B', self.rel[DATA_BASE+VERTICES+index*16:DATA_BASE+VERTICES+(index+4)*16]))
            self.assertEqual({v[:3]+v[4:6] for v in out}, {tuple(n*10 for n in v[:3])+v[4:6] for v in gc})
            self.assertEqual([v[3:4]+v[6:] for v in out], [v[3:4]+v[6:] for v in old])
            area = lambda q: (q[1][0]-q[0][0])*(q[2][1]-q[0][1])-(q[1][1]-q[0][1])*(q[2][0]-q[0][0])
            self.assertGreater(area(out)*area(old), 0)
        restored = bytearray(data)
        for change in profile['changes']:
            start, size = int(change['vrom'], 16)-VROM, change['bytes']
            self.assertEqual(sha256(data[start:start+size]), change['output_sha256'])
            restored[start:start+size] = original[start:start+size]
        self.assertEqual(restored, original)
        # Dynamic row/column image pointers and the enclosing caller's reset stay native.
        for start, size in ((0xAB4430, 8), (0xAB4838, 8), (0xAB4998, 0xA0)):
            self.assertEqual(data[start-VROM:start-VROM+size], original[start-VROM:start-VROM+size])

    def test_native_command_bounds_and_damaged_sources_reject(self):
        self.assertEqual(len(self.commands['acre']), 56)
        self.assertEqual(len(self.commands['dash']), 48)
        self.assertEqual(self.commands['dash'][-8:], bytes.fromhex('DF00000000000000'))
        for n, r, s in ((self.native[:-1], self.rel, self.symbols),
                        (self.native, self.rel[:-1], self.symbols),
                        (self.native, self.rel, self.symbols+b'\n')):
            with self.assertRaises(ValueError): patch_assets(n, r, s, self.commands)
        wrong = dict(self.commands, acre=bytes(56))
        with self.assertRaisesRegex(ValueError, 'Compiled native'):
            patch_assets(self.native, self.rel, self.symbols, wrong)

    def test_combined_image_preserves_shop_art_shrine_quests_and_complete_english(self):
        old_report = json.dumps(self.report, sort_keys=True)
        image, ups, report = build(self.native, self.base, self.report, self.rel, self.symbols, self.commands)
        self.assertEqual(json.dumps(self.report, sort_keys=True), old_report)
        self.assertEqual(len(image), len(self.base))
        self.assertEqual(sha256(image), '29576ea8bc82a55193a263b913a15ffe81554746a2cec5cdcff3bf84a26b6cdc')
        self.assertEqual(apply_ups(self.native, ups), image)
        for key in ('map_names', 'building_artwork', 'first_job_progression', 'runtime_module'):
            self.assertEqual(report[key], self.report[key])
        files, previous = by_vrom(image), by_vrom(self.base)
        self.assertEqual(set(files), set(previous))
        for vrom, entry in previous.items():
            if vrom not in (VROM, 0x19D40):
                self.assertEqual(files[vrom].extract(image), entry.extract(self.base), f'{vrom:08X}')
        with self.assertRaisesRegex(ValueError, 'baseline'):
            build(self.native, self.base[:-1], self.report, self.rel, self.symbols, self.commands)


if __name__ == '__main__':
    unittest.main()
