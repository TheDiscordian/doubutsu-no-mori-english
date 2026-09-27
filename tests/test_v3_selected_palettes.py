"""Complete selected-palette resources; no installed roof-selector claim."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import (Source,prepare,PreparedAssets,SELECTED_PALETTE_CATEGORY,
    metadata,identity_rows)
from v3_furniture_install import profile
from v3_villager_art import native_palette


class SelectedPaletteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.art=ROOT/'build/v3-selected-palette-assets-01'
        cls.report=json.loads((cls.art/'art.json').read_bytes())
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_models_and_all_roof_palettes_in_one_batch(self):
        from tests.test_v3_furniture_pipeline import DonorTests
        self.assertEqual([r['item_id'] for r in self.report['objects']],['3024','3028'])
        self.assertEqual(self.report['batch'],dict(objects=2,compiled=2,reused=0,compiler_containers=1))
        DonorTests.check_complete_artwork(self,self.art,self.report)
        cache=PreparedAssets(self.source,[self.art])
        for row in self.report['objects']:
            parts=prepare(self.source,int(row['item_id'],16));adapter=parts[0]['callback_adapter']
            self.assertEqual(adapter['category'],SELECTED_PALETTE_CATEGORY)
            self.assertEqual(adapter['palette_count'],12)
            asset=(self.art/row['object_file']).read_bytes()
            magic,n,models,on,off,*rest=struct.unpack_from('>IHH6I',asset)
            self.assertEqual((magic,n,models,rest[-1]),(0x41465032,len(asset),3,12))
            self.assertEqual(rest[:3],[0x06000000+row['model_offsets'][label] for label in adapter['model_order']])
            for role,at in (('on',on),('off',off)):
                endpoint=adapter['endpoints'][role];source=endpoint['donor_offset']
                self.assertEqual(endpoint['bytes'],384)
                self.assertEqual(sha256(self.source.data[source:source+384]),endpoint['sha256'])
                for index in range(12):
                    expected=native_palette(self.source.data[source+index*32:source+(index+1)*32])
                    self.assertEqual(asset[at+index*32:at+(index+1)*32],expected)
            self.assertIsNotNone(cache.reuse(self.source,row['item_id'],parts))

    def test_complete_lifecycles_are_bound_but_cannot_install_without_selection(self):
        identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        for row in self.report['objects']:
            item=int(row['item_id'],16);descriptor=self.source.profile(item);adapter=descriptor['callback_adapter']
            self.assertEqual(adapter['pending_callbacks'],['create','move','draw','destroy'])
            self.assertFalse(row['import_ready'] or adapter['runtime_installed'])
            with self.assertRaisesRegex(ValueError,'house-colour selection'):
                metadata(self.source,item,descriptor,identities[item])
            with self.assertRaisesRegex(ValueError,'native lifecycle'):
                profile(row,0x02600000,model_capacity=12288)
            for receipt in [*adapter['functions'].values(),*adapter['selector'].values()]:
                bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
                bad.rel[self.source.sections[1][0]+receipt['offset']]^=1
                with self.assertRaises(ValueError,msg=receipt['symbol']):bad.profile(item)
            # A truncated endpoint table cannot quietly turn into one roof colour.
            endpoint=adapter['endpoints']['off'];bad=copy.copy(self.source)
            bad.by_start=copy.deepcopy(self.source.by_start)
            bad.by_start[endpoint['donor_offset']]=[(32,endpoint['symbol'])]
            with self.assertRaisesRegex(ValueError,'endpoint palette'):bad.profile(item)


if __name__=='__main__':unittest.main()
