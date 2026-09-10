"""Full collection heading pixels fit native storage and preserve the rest of the game."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256
from collection_artwork import VROM, DONORS, ROWS, commands, patch_assets, build
from title_assets import DATA_BASE, pack4, untile


@unittest.skipUnless((ROOT/'build/time-setting-01/build.json').is_file(), 'Local supplied assets required')
class CollectionArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        baseline = ROOT/'build/time-setting-01'
        cls.base = (baseline/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((baseline/'build.json').read_text())
        cls.prior = by_vrom(cls.base)[VROM].extract(cls.base)
        with tempfile.TemporaryDirectory(prefix='af-collection-gbi-') as directory:
            cls.compiled = commands(Path(directory))

    def test_exact_pixels_and_source_sized_quads_with_native_frame_alignment(self):
        changed, profile = patch_assets(self.native, self.prior, self.rel, self.symbols, self.compiled)
        self.assertEqual(len(changed), len(self.prior))
        self.assertEqual(len(profile['donor_texture_pointers']), 2)
        restored = bytearray(changed)
        for row in profile['changes']:
            start, size = int(row['vrom'], 16)-VROM, row['bytes']
            restored[start:start+size] = self.prior[start:start+size]
        self.assertEqual(restored, self.prior)
        for donor, (label, width, texture, capacity, load, vertices, gc_vertices) in zip(DONORS, ROWS):
            pixels = pack4(untile(self.rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+width*8], width, 16, 4))
            self.assertEqual(changed[texture-VROM:texture-VROM+capacity], pixels+bytes(capacity-len(pixels)))
            quad = list(struct.iter_unpack('>3hH2h4B', changed[vertices-VROM:vertices-VROM+64]))
            old = list(struct.iter_unpack('>3hH2h4B', self.prior[vertices-VROM:vertices-VROM+64]))
            gc = list(struct.iter_unpack('>3hH2h4B', self.rel[DATA_BASE+gc_vertices:DATA_BASE+gc_vertices+64]))
            self.assertEqual({(v[0], v[1]+10, v[2], *v[4:6]) for v in quad}, {v[:3]+v[4:6] for v in gc})
            self.assertEqual([v[3:4]+v[6:] for v in quad], [v[3:4]+v[6:] for v in old])
            self.assertEqual(max(v[1] for v in quad), max(v[1] for v in old))
            self.assertEqual(changed[load-VROM+56:load-VROM+80], self.prior[load-VROM+56:load-VROM+80])
        for address in (0xA31728, 0xA3DA38):
            self.assertEqual(changed[address-VROM:address-VROM+512], self.prior[address-VROM:address-VROM+512])

    def test_native_load_shapes_and_rejection_of_unrelated_asset_changes(self):
        self.assertEqual(self.compiled['insects'][-8:], bytes.fromhex('F20000000013C03C'))
        self.assertEqual(self.compiled['fish'][-8:], bytes.fromhex('F2000000000FC03C'))
        for prior, rel, symbols in ((self.prior[:-1], self.rel, self.symbols),
                                    (self.prior, self.rel[:-1], self.symbols),
                                    (self.prior, self.rel, self.symbols+b'\n')):
            with self.assertRaises(ValueError): patch_assets(self.native, prior, rel, symbols, self.compiled)
        wrong = dict(self.compiled, insects=bytes(56))
        with self.assertRaisesRegex(ValueError, 'Compiled collection'):
            patch_assets(self.native, self.prior, self.rel, self.symbols, wrong)

    def test_complete_cartridge_retains_all_previous_english_and_fixes(self):
        report_before = copy.deepcopy(self.report)
        image, ups, report = build(self.native, self.base, self.report, self.rel, self.symbols, self.compiled)
        self.assertEqual(self.report, report_before)
        self.assertEqual(sha256(image), '27f840aaea2693ac96fbbc084981dd978f8e376cbf8d7a1259666160d29f5f7d')
        self.assertEqual(apply_ups(self.native, ups), image)
        self.assertEqual(len(image), 32*1024*1024)
        for key in ('time_setting', 'map_names', 'inventory_artwork', 'map_artwork', 'building_artwork',
                    'first_job_progression', 'runtime_module'):
            self.assertEqual(report[key], self.report[key])
        old, new = by_vrom(self.base), by_vrom(image)
        self.assertEqual(set(old), set(new))
        for vrom, entry in old.items():
            if vrom not in (VROM, 0x19D40):
                self.assertEqual(new[vrom].extract(image), entry.extract(self.base), f'{vrom:08X}')


if __name__ == '__main__':
    unittest.main()
