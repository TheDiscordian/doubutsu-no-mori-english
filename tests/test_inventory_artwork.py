"""English inventory art uses complete donor labels without changing pockets or saves."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups
from inventory_artwork import VROM, VERTICES, DONORS, TARGETS, commands, patch_assets, build
from title_assets import DATA_BASE, pack4, untile


@unittest.skipUnless((ROOT/'build/map-artwork-01/build.json').is_file(), 'Local supplied assets required')
class InventoryArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        baseline = ROOT/'build/map-artwork-01'
        cls.base = (baseline/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((baseline/'build.json').read_text())
        with tempfile.TemporaryDirectory(prefix='af-inventory-art-gbi-') as directory:
            cls.compiled = commands(Path(directory))

    def test_complete_labels_source_geometry_and_only_scoped_changes(self):
        data, profile = patch_assets(self.native, self.rel, self.symbols, self.compiled)
        original = by_vrom(self.native)[VROM].extract(self.native)
        self.assertEqual(len(data), 64544)
        self.assertEqual(len(profile['donor_texture_pointers']), 3)
        self.assertEqual(profile['labels'], ['Items', 'Letters', 'Bells'])
        for donor, (texture, vertices, index) in zip(DONORS, TARGETS):
            expected = pack4(untile(self.rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+512], 64, 16, 4))
            self.assertEqual(data[texture-VROM:texture-VROM+512], expected)
            new = list(struct.iter_unpack('>3hH2h4B', data[vertices-VROM:vertices-VROM+64]))
            old = list(struct.iter_unpack('>3hH2h4B', original[vertices-VROM:vertices-VROM+64]))
            gc = list(struct.iter_unpack('>3hH2h4B', self.rel[DATA_BASE+VERTICES+index*16:DATA_BASE+VERTICES+(index+4)*16]))
            self.assertEqual({v[:3]+v[4:6] for v in new}, {v[:3]+v[4:6] for v in gc})
            self.assertEqual([v[3:4]+v[6:] for v in new], [v[3:4]+v[6:] for v in old])
        for address in (0xA300B8, 0xA3AA00):
            self.assertEqual(data[address-VROM:address-VROM+256], bytes(256))
        self.assertEqual(data[0xA371A0-VROM:0xA371A8-VROM], bytes.fromhex('FA0000FF7878E1FF'))
        restored = bytearray(data)
        for row in profile['changes']:
            start, size = int(row['vrom'], 16)-VROM, row['bytes']
            self.assertEqual(sha256(data[start:start+size]), row['output_sha256'])
            restored[start:start+size] = original[start:start+size]
        self.assertEqual(restored, original)

    def test_native_load_and_wrong_sources_reject(self):
        self.assertEqual(len(self.compiled), 56)
        self.assertEqual(self.compiled[:8], bytes.fromhex('FD9000000C00AD00'))
        self.assertEqual(self.compiled[-8:], bytes.fromhex('F2000000000FC03C'))
        for n, r, s in ((self.native[:-1], self.rel, self.symbols),
                        (self.native, self.rel[:-1], self.symbols),
                        (self.native, self.rel, self.symbols+b'\n')):
            with self.assertRaises(ValueError): patch_assets(n, r, s, self.compiled)
        with self.assertRaisesRegex(ValueError, 'Compiled inventory'):
            patch_assets(self.native, self.rel, self.symbols, bytes(56))

    def test_complete_candidate_retains_all_prior_english_and_fixes(self):
        old_report = json.dumps(self.report, sort_keys=True)
        image, ups, report = build(self.native, self.base, self.report, self.rel, self.symbols, self.compiled)
        self.assertEqual(json.dumps(self.report, sort_keys=True), old_report)
        self.assertEqual(sha256(image), '15c7a2830f5a561a8470ba70bc4aaa907e65ab1ee5ebb921266df17e6b1cac3c')
        self.assertEqual(len(image), 32*1024*1024)
        self.assertEqual(apply_ups(self.native, ups), image)
        for key in ('map_names', 'map_artwork', 'building_artwork', 'first_job_progression', 'runtime_module'):
            self.assertEqual(report[key], self.report[key])
        files, previous = by_vrom(image), by_vrom(self.base)
        self.assertEqual(set(files), set(previous))
        for vrom, entry in previous.items():
            if vrom not in (VROM, 0x19D40):
                self.assertEqual(files[vrom].extract(image), entry.extract(self.base), f'{vrom:08X}')
        with self.assertRaisesRegex(ValueError, 'baseline'):
            build(self.native, self.base[:-1], self.report, self.rel, self.symbols, self.compiled)


if __name__ == '__main__':
    unittest.main()
