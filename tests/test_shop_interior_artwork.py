"""Exact donor colours, room retention, source rejection, and installed text credit."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups, CODE_VROM
from texture_preview import decode, native_range
from title_assets import DATA_BASE
from textcodec import command_info
from translation_progress import CounterLedger
import shop_interior_artwork as shop


@unittest.skipUnless((ROOT/'build/shop-interior-artwork-01/build.json').is_file(),
                     'Local shop-interior candidate required')
class ShopInteriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/stall-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior = json.loads((ROOT/'build/stall-artwork-01/build.json').read_text())
        cls.image = (ROOT/'build/shop-interior-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((ROOT/'build/shop-interior-artwork-01/build.json').read_text())
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.info = command_info(by_vrom(cls.native)[CODE_VROM].extract(cls.native))

    def test_all_seven_complete_images_match_visible_donor_pixels(self):
        profile = shop.verify_installed(self.native, self.image, self.report, self.rel, self.symbols)
        self.assertEqual(len(profile['textures']), 7)
        self.assertEqual(len(profile['donor_pointers']), 21)
        for row in shop.SIGNS:
            installed = decode(native_range(self.image, row.owner+row.texture, row.size), row.width, row.height,
                               'ci4', native_range(self.image, row.owner+row.palette, 32))
            donor = decode(self.rel[DATA_BASE+row.gc:DATA_BASE+row.gc+row.size], row.width, row.height, 'ci4',
                           self.rel[DATA_BASE+row.gc_palette:DATA_BASE+row.gc_palette+32], gamecube=True)
            self.assertEqual(installed[3::4], donor[3::4], row.name)
            for at in range(0, len(installed), 4):
                if donor[at+3]:
                    self.assertEqual(installed[at:at+4], donor[at:at+4], row.name)
        for key in ('geometry_changed', 'commands_changed', 'code_changed', 'allocations_changed', 'save_layout_changed'):
            self.assertFalse(profile[key])

    def test_reconstruction_retains_every_unrelated_resource_and_room_byte(self):
        image, ups, report = shop.build(self.native, self.base, self.prior, self.rel, self.symbols)
        self.assertEqual(image, self.image)
        self.assertEqual(report, self.report)
        self.assertEqual(apply_ups(self.native, ups), image)
        old, new = by_vrom(self.base), by_vrom(image)
        self.assertEqual(set(old), set(new))
        for v, entry in old.items():
            self.assertEqual((entry.index, entry.size), (new[v].index, new[v].size))
            before, after = entry.extract(self.base), new[v].extract(image)
            if v in shop.OWNERS:
                allowed = {i for row in shop.SIGNS if row.owner == v
                           for i in range(row.texture, row.texture+row.size)}
                if v == 0x13CD000:
                    allowed.update((0x26AA, 0x26AB))
                self.assertTrue(all(a == b for i, (a, b) in enumerate(zip(before, after)) if i not in allowed))
            elif v != 0x19D40:
                self.assertEqual(before, after, f'{v:08X}')

    def test_prior_and_installed_text_use_same_source_weight(self):
        for image, report, credit in ((self.base, self.prior, 0), (self.image, self.report, 53)):
            ledger = CounterLedger(self.info)
            shop.measure_text(ledger, self.native, image, report)
            self.assertEqual(len(ledger.rows), 4)
            self.assertEqual(ledger.summary()['total_source_characters'], 53)
            self.assertEqual(ledger.summary()['replaced_source_characters'], credit)
        with self.assertRaises(ValueError):
            shop.measure_text(CounterLedger(self.info), self.native, self.base, self.report)

    def test_corrupt_texture_palette_reader_and_source_cannot_receive_credit(self):
        owner = by_vrom(self.image)[0x13CD000]
        self.assertEqual(owner.pend, 0)
        for offset in (0x4158, 0x26AA, 0x171C, 0x0000):
            bad = bytearray(self.image)
            bad[owner.pstart+offset] ^= 1
            with self.assertRaisesRegex(ValueError, 'not installed'):
                shop.verify_installed(self.native, bytes(bad), self.report, self.rel, self.symbols)
        report = deepcopy(self.report)
        report['shop_interior_artwork']['commands_changed'] = True
        with self.assertRaisesRegex(ValueError, 'profile'):
            shop.verify_installed(self.native, self.image, report, self.rel, self.symbols)
        for rel, symbols in ((self.rel[:-1], self.symbols), (self.rel, self.symbols+b'bad')):
            with self.assertRaises(ValueError):
                shop.assets(self.native, rel, symbols)
        with self.assertRaises(ValueError):
            shop.assets(self.native[:-1], self.rel, self.symbols)

    @unittest.skipUnless((ROOT/'build/title-shop-interior-combined-01/preview.json').is_file(),
                         'Combined shop-interior/title candidate required')
    def test_combined_title_retains_every_other_current_resource(self):
        prior = (ROOT/'build/title-stall-combined-01/animal-forest-title-preview.z64').read_bytes()
        current = (ROOT/'build/title-shop-interior-combined-01/animal-forest-title-preview.z64').read_bytes()
        report = json.loads((ROOT/'build/title-shop-interior-combined-01/preview.json').read_text())
        self.assertEqual(report['baseline_sha256'], sha256(self.image))
        self.assertEqual(report['memory']['required_ram_bytes'], 0x800000)
        self.assertEqual(report['memory']['ordinary_heap_end'], 0x80400000)
        shop.verify_installed(self.native, current, self.report, self.rel, self.symbols)
        old, new = by_vrom(prior), by_vrom(current)
        self.assertEqual(set(old), set(new))
        for v, entry in old.items():
            self.assertEqual((entry.index, entry.size), (new[v].index, new[v].size))
            if v not in {*shop.OWNERS, 0x19D40}:
                self.assertEqual(entry.extract(prior), new[v].extract(current), f'{v:08X}')
        self.assertEqual(prior[0x1060:0x19D40], current[0x1060:0x19D40])


if __name__ == '__main__':
    unittest.main()
