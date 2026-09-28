"""Saved designs and museum scenery cannot masquerade as fixed item imports."""
import copy
from collections import Counter
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import v3_furniture_pipeline as pipeline
import v3_room_representations as representations
from v3_import_catalog import item_rows
from gc_text import decoder_tables


class RoomRepresentationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.catalogue = representations.discover(cls.source)

    def test_complete_saved_design_ranges_and_museum_consumers(self):
        rows = self.catalogue['rows']
        self.assertEqual(Counter(r['category'] for r in rows),
                         {'saved-player-design':16,'museum-placeholder':9})
        for kind, first in (('mannequin',0x1BA8),('umbrella',0x1D88)):
            designs = [r for r in rows if r.get('form') == kind]
            self.assertEqual([r['item_id'] for r in designs],[f'{first+4*i:04X}' for i in range(8)])
            self.assertEqual([r['design_slot'] for r in designs],list(range(8)))
            self.assertTrue(all((r['texture_bytes'],r['palette_bytes'],r['saved_record_bytes']) ==
                                (512,32,544) for r in designs))
        scenery = [r for r in rows if r['category']=='museum-placeholder']
        specimens = [s['specimen_item_id'] for r in scenery for s in r['specimens']]
        self.assertEqual(sorted(specimens),[f'{0x1EEC+4*i:04X}' for i in range(25)])
        dummy = next(r for r in scenery if r['item_id']=='1F9C')
        self.assertEqual([s['specimen_item_id'] for s in dummy['specimens']],
                         ['1F3C','1F40','1F44','1F48','1F4C'])
        self.assertTrue(all(not r['independently_selectable'] and not r['runtime_installed'] for r in rows))

    def test_changed_code_table_profiles_and_bindings_reject(self):
        for consumer in self.catalogue['consumers'].values():
            for function in (consumer[k] for k in ('draw','dma','function') if k in consumer):
                changed = copy.copy(self.source); changed.rel = bytearray(self.source.rel)
                changed.rel[self.source.sections[1][0]+function['offset']] ^= 1
                with self.assertRaisesRegex(ValueError,'room-representation consumer'):
                    representations.discover(changed)
        for symbol, offset in (('mMmd_museum_fossil_data',0),('iam_myfmanekin',46)):
            changed = copy.copy(self.source); changed.data = bytearray(self.source.data)
            changed.data[self.source.symbol(symbol)[0]+offset] ^= 1
            with self.assertRaises(ValueError):
                representations.discover(changed)
        changed = copy.copy(self.source); changed.quality = copy.deepcopy(self.source.quality)
        changed.quality[1][self.source.names['furniture_quality'][1][0]+746*4] += 4
        with self.assertRaisesRegex(ValueError,'tables disagree'):
            representations.discover(changed)

    def test_inventory_scan_and_browser_share_the_same_classification(self):
        tables = decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')
        items = item_rows(self.source.raw('ftrName_table'),tables,base=0x1000,furniture=True)
        items += item_rows(self.source.raw('ftrName2_table'),tables,base=0x3000,furniture=True)
        representations.annotate_inventory(items,self.catalogue)
        representations.annotate_inventory(items,self.catalogue)
        selected = tuple(r['item_id'] for r in self.catalogue['rows'])
        inventory = pipeline.scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=selected)
        self.assertEqual(inventory['room_representations'],self.catalogue)
        self.assertEqual(len(inventory['rows']),25)
        by_id = {r['donor_item_id']:r for r in items}
        for row in inventory['rows']:
            self.assertFalse(row['asset_ready'])
            self.assertEqual(row['room_representation'],by_id[row['item_id']]['room_representation'])
            self.assertEqual(row['status'],by_id[row['item_id']]['status'])
        import v3_browser_composition as browser
        with patch.object(pipeline,'scan',return_value=inventory):
            review = browser.review_catalogue(dict(options=[],base_sha256='0'*64),
                dict(furniture=dict(imports=[]),speed_bag=dict(id='GAFE01-r0/item/31A4')))
        self.assertEqual(len(review['unavailable']),25)
        self.assertTrue(all(not r['selectable'] and r['room_representation'] for r in review['unavailable']))
        # Installed parent selections also own their clothing/creature forms;
        # they must not appear again as supposedly unfinished furniture.
        linked=copy.deepcopy(inventory)
        for field in ('parent_representation','room_alias','profile'):
            relationship=dict(parent_id='GAFE01-r0/item/2320')
            linked['rows'].append(dict(item_id='1CEC',installed=False,name='frog',
                **{field:dict(creature_parent=relationship) if field=='profile' else relationship}))
        with patch.object(pipeline,'scan',return_value=linked):
            review=browser.review_catalogue(dict(options=[dict(id='GAFE01-r0/item/2320')],base_sha256='0'*64),
                dict(furniture=dict(imports=[]),speed_bag=dict(id='GAFE01-r0/item/31A4')))
        self.assertEqual(len(review['unavailable']),25)
        with tempfile.TemporaryDirectory() as directory:
            for item in ('1BA8','1D88','1F9C'):
                with self.assertRaisesRegex(ValueError,'Unsupported or filtered'):
                    pipeline.convert(self.source,ROOT/'build/item-identity-megasheet.xlsx',
                        Path(directory)/item,(item,),[],assets_only=True)


if __name__ == '__main__':
    unittest.main()
