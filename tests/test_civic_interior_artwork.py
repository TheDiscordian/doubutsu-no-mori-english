"""Exact civic donor pixels, native room retention, and installed text credit."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups
from texture_preview import decode, native_range
from title_assets import DATA_BASE
from translation_progress import CounterLedger
import civic_interior_artwork as civic


@unittest.skipUnless((ROOT/'build/civic-interior-artwork-01/build.json').is_file(),
                     'Local civic-interior candidate required')
class CivicInteriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/shop-interior-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior = json.loads((ROOT/'build/shop-interior-artwork-01/build.json').read_text())
        cls.image = (ROOT/'build/civic-interior-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((ROOT/'build/civic-interior-artwork-01/build.json').read_text())
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_three_complete_images_match_donor_pixels_and_mapping(self):
        profile = civic.verify_installed(self.native, self.image, self.report, self.rel, self.symbols)
        self.assertEqual(len(profile['textures']), 3)
        self.assertEqual(len(profile['donor_pointers']), 7)
        self.assertEqual([r['triangle_count'] for r in profile['textures']], [2, 2, 6])
        for row in civic.MATERIALS:
            installed = decode(native_range(self.image, row.owner+row.texture, row.size), row.width, row.height,
                               'ci4', native_range(self.image, row.owner+row.palette, 32))
            donor = decode(self.rel[DATA_BASE+row.gc:DATA_BASE+row.gc+row.size], row.width, row.height, 'ci4',
                           self.rel[DATA_BASE+row.gc_palette:DATA_BASE+row.gc_palette+32], gamecube=True)
            self.assertEqual(installed[3::4], donor[3::4], row.name)
            for at in range(0, len(installed), 4):
                if donor[at+3]:
                    self.assertEqual(installed[at:at+4], donor[at:at+4], row.name)
        for key in ('palettes_changed', 'geometry_changed', 'commands_changed', 'code_changed',
                    'allocations_changed', 'save_layout_changed'):
            self.assertFalse(profile[key])

    def test_reconstruction_retains_every_other_resource_and_room_byte(self):
        image, ups, report = civic.build(self.native, self.base, self.prior, self.rel, self.symbols)
        self.assertEqual(image, self.image)
        self.assertEqual(report, self.report)
        self.assertEqual(apply_ups(self.native, ups), image)
        old, new = by_vrom(self.base), by_vrom(image)
        self.assertEqual(set(old), set(new))
        for v, entry in old.items():
            self.assertEqual((entry.index, entry.size), (new[v].index, new[v].size))
            before, after = entry.extract(self.base), new[v].extract(image)
            if v in civic.OWNERS:
                allowed = {i for row in civic.MATERIALS if row.owner == v
                           for i in range(row.texture, row.texture+row.size)}
                self.assertTrue(all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in allowed))
            elif v != 0x19D40:
                self.assertEqual(before, after, f'{v:08X}')

    def test_prior_and_installed_credit_share_nineteen_source_characters(self):
        for image, report, credit in ((self.base, self.prior, 0), (self.image, self.report, 19)):
            ledger = CounterLedger([(2, 0)]*0x77)
            civic.measure_text(ledger, self.native, image, report)
            self.assertEqual(len(ledger.rows), 3)
            self.assertEqual(ledger.summary()['total_source_characters'], 19)
            self.assertEqual(ledger.summary()['replaced_source_characters'], credit)
        with self.assertRaises(ValueError):
            civic.measure_text(CounterLedger([(2, 0)]*0x77), self.native, self.base, self.report)

    def test_changed_texture_palette_vertices_reader_profile_and_source_rejected(self):
        for row in civic.MATERIALS:
            owner = by_vrom(self.image)[row.owner]
            self.assertEqual(owner.pend, 0)
            for offset in (row.texture, row.palette, row.vertices, row.command+4):
                bad = bytearray(self.image)
                bad[owner.pstart+offset] ^= 1
                with self.assertRaisesRegex(ValueError, 'not installed'):
                    civic.verify_installed(self.native, bytes(bad), self.report, self.rel, self.symbols)
        report = deepcopy(self.report)
        report['civic_interior_artwork']['commands_changed'] = True
        with self.assertRaisesRegex(ValueError, 'profile'):
            civic.verify_installed(self.native, self.image, report, self.rel, self.symbols)
        for rel, symbols in ((self.rel[:-1], self.symbols), (self.rel, self.symbols+b'bad')):
            with self.assertRaises(ValueError):
                civic.assets(self.native, rel, symbols)
        with self.assertRaises(ValueError):
            civic.assets(self.native[:-1], self.rel, self.symbols)
        prior = deepcopy(self.prior)
        prior['replacement_files'] = []
        with self.assertRaisesRegex(ValueError, 'predecessor'):
            civic.build(self.native, self.base, prior, self.rel, self.symbols)

    @unittest.skipUnless((ROOT/'build/title-civic-interior-combined-01/preview.json').is_file(),
                         'Combined civic-interior/title candidate required')
    def test_combined_title_retains_all_other_current_resources(self):
        prior = (ROOT/'build/title-shop-interior-combined-01/animal-forest-title-preview.z64').read_bytes()
        current = (ROOT/'build/title-civic-interior-combined-01/animal-forest-title-preview.z64').read_bytes()
        report = json.loads((ROOT/'build/title-civic-interior-combined-01/preview.json').read_text())
        self.assertEqual(report['baseline_sha256'], sha256(self.image))
        self.assertEqual(report['memory']['required_ram_bytes'], 0x800000)
        self.assertEqual(report['memory']['ordinary_heap_end'], 0x80400000)
        civic.verify_installed(self.native, current, self.report, self.rel, self.symbols)
        old, new = by_vrom(prior), by_vrom(current)
        self.assertEqual(set(old), set(new))
        for v, entry in old.items():
            self.assertEqual((entry.index, entry.size), (new[v].index, new[v].size))
            if v not in {*civic.OWNERS, 0x19D40}:
                self.assertEqual(entry.extract(prior), new[v].extract(current), f'{v:08X}')
        self.assertEqual(prior[0x1060:0x19D40], current[0x1060:0x19D40])


if __name__ == '__main__':
    unittest.main()
