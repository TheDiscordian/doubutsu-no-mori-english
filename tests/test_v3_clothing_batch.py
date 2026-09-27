"""One source-format check covers every garment, including installed resources."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256
from v3_clothing import convert, garment, source_assets
import v3_clothing_batch as batch
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source, scan
from v3_villager_text import read_text_donor
from v3_villager_defaults import pixels
from title_assets import rgb5a3


class ClothingBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.first = read_text_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.worksheet = ROOT/'build/item-identity-megasheet.xlsx'
        cls.installed = inputs(ROOT/'build/v3-creature-insects-work-01/connected-04/build-lock.json')
        cls.assets = source_assets(cls.native, cls.first, cls.source.rel, cls.source.symbols.encode())
        cls.report, cls.data = batch.discover(cls.source, cls.native, cls.first,
            cls.worksheet, installed=cls.installed)
        cls.rows = {r['donor_item_id']: r for r in cls.report['rows']}

    def test_complete_category_keeps_parents_variants_and_every_original(self):
        self.assertEqual(self.report['counts'],
            {'native-appearance': 247, 'additive-appearance': 7, 'donor-variant': 1})
        self.assertEqual(set(self.rows), {f'{n:04X}' for n in range(0x2400, 0x24FF)})
        additions = {k for k, r in self.rows.items() if not r['native_candidates']}
        self.assertEqual(additions, {'241A', '241B', '244B', '2469', '24B6', '24BF', '24CB', '24E3'})
        self.assertEqual(self.report['new_resource_count'], 5)
        self.assertEqual(len(self.data), 8*544)
        for key, row in self.rows.items():
            self.assertEqual(row['parent_item_id'], key)
            self.assertEqual(row['display_item_id'], f'{0x17AC+(int(key,16)-0x2400)*4:04X}')
            self.assertFalse(row['independently_selectable_display'])
            self.assertFalse(row['runtime_integration_checked'])
            self.assertFalse(row['selectable'])
        variant = self.rows['24E3']
        self.assertEqual(variant['status'], 'donor-variant')
        self.assertEqual(variant['declared_native_item_id'], '24E3')
        self.assertIsNone(variant['native_item_id'])
        # The source display has a stale name in the external worksheet. The
        # actual carried name and binary conversion establish its identity.
        self.assertEqual(self.rows['244B']['name'], 'fish bone shirt')
        self.assertEqual(self.rows['244B']['display_item_id'], '18D8')

    def test_complete_pixels_and_palettes_match_independent_block_addressing(self):
        textures, palettes = self.assets[:2]
        for item in range(0x2400, 0x24FF):
            data, row = garment(self.assets, item); index=item-0x2400
            raw = textures[index*512:(index+1)*512]
            expected_palette = []
            for (word,) in struct.iter_unpack('>H', palettes[index*32:(index+1)*32]):
                r,g,b,a = rgb5a3(word)
                self.assertIn(a, (0,255))
                expected_palette.append((r>>3)<<11|(g>>3)<<6|(b>>3)<<1|bool(a))
            expected = []
            for y in range(32):
                for x in range(32):
                    at=((y//8)*4+x//8)*32+(y%8)*4+(x%8)//2
                    value=(raw[at]>>(0 if x&1 else 4))&15
                    expected.append(expected_palette[value])
            self.assertEqual(pixels(data[:512],data[512:]), tuple(expected))
            self.assertEqual(data[512:], struct.pack('>16H',*expected_palette))
            self.assertEqual(row['resource_sha256'], sha256(data))

    def test_installed_three_remain_identical_and_new_seasons_come_from_donor(self):
        image, report = self.installed; files=by_vrom(image)
        old_resources = set()
        for old in report['clothing']['imports']:
            item=int(old['donor_item_id'],16)
            data, record, row = convert(self.native,self.first,self.source.rel,
                self.source.symbols.encode(),donor_item=item)
            self.assertEqual(row['resource_sha256'],old['resource_sha256'])
            vrom=int(old['vrom'],16)
            owner=next(f for f in files.values() if f.vstart<=vrom<vrom+544<=f.vend)
            self.assertEqual(owner.extract(image)[vrom-owner.vstart:vrom-owner.vstart+544],data)
            self.assertEqual(sha256(record),old['metadata_sha256'])
            self.assertTrue(self.rows[old['donor_item_id']]['installed_resource'])
            old_resources.add(old['donor_item_id'])
        self.assertEqual(old_resources,{'241A','241B','24BF'})
        expected={'244B':('cloth_listC','all'), '2469':('cloth_listB','all'),
                  '24B6':('cloth_listB','all'), '24CB':('cloth_listA','summer'),
                  '24E3':('cloth_listA','all')}
        for key, (symbol,season) in expected.items():
            row=self.rows[key]
            self.assertEqual(len(row['stock']),1)
            self.assertEqual((row['stock'][0]['symbol'],row['stock'][0]['season']),(symbol,season))
            self.assertIsNotNone(row['catalogue_position'])
            self.assertFalse(row['installed_resource'])
            at=row['resource_offset']
            self.assertEqual(sha256(self.data[at:at+544]),row['resource_sha256'])

    def test_furniture_scan_routes_complete_mannequin_group_to_parent_category(self):
        forms=batch.representations(self.source)
        self.assertEqual(len(forms),255)
        selected=('1814','1818','18D8','1950','1A84','1AA8','1AD8')
        report=scan(self.source,self.worksheet,[],selected=selected)
        self.assertEqual(len(report['rows']),len(selected))
        for row in report['rows']:
            self.assertEqual(row['status'],'parent-representation')
            parent=forms[int(row['item_id'],16)]
            self.assertEqual(row['parent_representation'],parent)
            self.assertEqual(row['name'],self.rows[parent['parent_item_id']]['name'])
            self.assertFalse(row['asset_ready'])
            self.assertFalse(parent['independently_selectable'])
        self.assertNotIn(0x1BA8,forms)  # Custom designs are a separate source format.
        with self.assertRaisesRegex(ValueError,'independent furniture'):
            scan(self.source,self.worksheet,[0x18D8],selected=('18D8',))

    def test_changed_sources_and_prepared_content_reject(self):
        damaged=bytearray(self.first);damaged[-1]^=1
        with self.assertRaisesRegex(ValueError,'verified English donor'):
            source_assets(self.native,damaged,self.source.rel,self.source.symbols.encode())
        for item in (-1,0x23FF,0x24FF,0x2500,True):
            with self.assertRaisesRegex(ValueError,'outside.*category'):garment(self.assets,item)
        changed=copy.copy(self.source);changed.rel=bytearray(self.source.rel)
        changed.rel[self.source.sections[1][0]+batch.FUNCTIONS['place'][0]+0x50]^=1
        with self.assertRaisesRegex(ValueError,'placement/pickup'):batch.parent_contract(changed)
        with tempfile.TemporaryDirectory(prefix='v3-clothing-batch-') as temporary:
            output=Path(temporary)/'prepared'
            actual=batch.convert(self.source,self.native,self.first,self.worksheet,output,installed=self.installed)
            self.assertEqual(actual,self.report)
            checked,data=batch.checked(self.source,self.native,self.first,self.worksheet,output,installed=self.installed)
            self.assertEqual((checked,data),(self.report,self.data))
            # Generated test input only; production outputs are never changed.
            raw=bytearray((output/'clothing.bin').read_bytes());raw[-1]^=1
            (output/'clothing.bin').write_bytes(raw)
            with self.assertRaisesRegex(ValueError,'prepared clothing'):
                batch.checked(self.source,self.native,self.first,self.worksheet,output,installed=self.installed)


if __name__ == '__main__':unittest.main()
