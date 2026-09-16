"""Source-derived room aliases stay attached to their actual parent items."""
from collections import Counter
import copy
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from gc_text import decoder_tables
from v3_import_catalog import ITEM_GROUPS, item_rows
import v3_furniture_pipeline as pipeline
import v3_room_aliases as aliases


class RoomAliasesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.catalogue = aliases.discover(cls.source)
        cls.rows = {row['display_item_id']: row for row in cls.catalogue['rows']}

    def test_both_complete_functions_supply_all_ranges_rotations_and_parents(self):
        # Independent reference ranges from the reviewed source functions.
        expected = (
            ('balloon', 0x2244, 0x3FC, 8, False), ('diary', 0x2B00, 0x43F, 16, True),
            ('fan', 0x2254, 0x453, 8, True), ('pinwheel', 0x224C, 0x45B, 8, True),
            ('golden-tool', 0x2239, 0x44F, 4, True), ('tool', 0x2200, 0x463, 4, True))
        self.assertEqual(len(self.rows), 48)
        for kind, first, index, count, restricted in expected:
            for i in range(count):
                runtime = index+i
                display = 0x1000+runtime*4 if runtime < 1024 else 0x3000+(runtime-1024)*4
                row = self.rows[f'{display:04X}']
                self.assertEqual(row['category'], kind)
                self.assertEqual(row['parent_item_id'], f'{first+i:04X}')
                self.assertEqual(row['pickup_item_id'], row['parent_item_id'])
                self.assertEqual(row['rotation_ids'], [f'{display+r:04X}' for r in range(4)])
                self.assertEqual(row['suppressed_by_no_convert_tools'], restricted)
                self.assertFalse(row['runtime_installed'])
                self.assertEqual(row['native_identity'], 'unreviewed')
        self.assertEqual(Counter(r['category'] for r in self.rows.values()),
                         {kind: count for kind, _, _, count, _ in expected})
        # Four balloons live in the older furniture range; don't discard them.
        self.assertEqual(sum(int(k,16) < 0x3000 for k in self.rows), 4)

    def test_worn_axes_keep_the_actual_many_to_one_pickup_policy(self):
        axe = self.rows['3190']
        self.assertEqual(axe['placement_inputs'], ['2201']+[f'{i:04X}' for i in range(0x223D,0x2244)])
        self.assertEqual(axe['pickup_item_id'], '2201')
        self.assertTrue(axe['pickup_canonicalises_state'])
        self.assertEqual(sum(len(r['placement_inputs']) for r in self.rows.values()), 55)
        self.assertEqual(sum(bool(r.get('pickup_canonicalises_state')) for r in self.rows.values()), 1)

    def test_changed_complete_code_helpers_or_relocations_fail_closed(self):
        text = self.source.sections[1][0]
        for address, _, size, _ in aliases.FUNCTIONS.values():
            for offset in (0, size-1):
                changed = copy.copy(self.source); changed.rel = bytearray(self.source.rel)
                changed.rel[text+address+offset] ^= 1
                with self.assertRaisesRegex(ValueError, 'room-alias function'):
                    aliases.discover(changed)
            changed = copy.copy(self.source)
            changed.code_relocations = {**self.source.code_relocations, address:(10,0,1,0)}
            with self.assertRaisesRegex(ValueError, 'room-alias function'):
                aliases.discover(changed)

    def test_full_donor_inventory_links_parents_and_states_without_new_choices(self):
        tables = decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')
        rows = []
        for i, name in enumerate(ITEM_GROUPS):
            rows += item_rows(self.source.raw('itemName_'+name), tables, base=0x2000+i*256, furniture=False)
        for symbol, base in (('ftrName_table',0x1000), ('ftrName2_table',0x3000)):
            rows += item_rows(self.source.raw(symbol), tables, base=base, furniture=True)
        identities = [r['id'] for r in rows]
        aliases.annotate_inventory(rows, self.catalogue)
        aliases.annotate_inventory(rows, self.catalogue)
        self.assertEqual([r['id'] for r in rows], identities)
        self.assertTrue(all(not r['selectable'] and r['target_item_id'] is None for r in rows))
        by_id = {r['donor_item_id']: r for r in rows}
        for row in self.rows.values():
            display, parent = by_id[row['display_item_id']], by_id[row['parent_item_id']]
            self.assertEqual(display['room_alias'], row)
            self.assertEqual(parent['room_display_ids'], [row['display_item_id']])
            self.assertEqual(parent['name'], row['parent_name'])
        for state in range(0x223D, 0x2244):
            row = by_id[f'{state:04X}']
            self.assertEqual(row['status'], 'state_of_parent_item')
            self.assertEqual(row['canonical_parent_id'], 'GAFE01-r0/item/2201')
        damaged = copy.deepcopy(rows)
        next(r for r in damaged if r['donor_item_id']=='2201')['name_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'complete donor inventory'):
            aliases.annotate_inventory(damaged, self.catalogue)

    def test_shared_scan_keeps_artwork_gaps_but_rejects_standalone_alias_imports(self):
        inventory = pipeline.scan(self.source, ROOT/'build/item-identity-megasheet.xlsx', [])
        rows = [r for r in inventory['rows'] if 'room_alias' in r]
        self.assertEqual(len(rows), 44)
        self.assertTrue(all(r['status']=='review' and 'parent-item support' in r['reason'] for r in rows))
        self.assertEqual(inventory['room_aliases'], self.catalogue)
        self.assertIn('custom callbacks', next(r for r in rows if r['item_id']=='314C')['conversion_reason'])
        diary = next(r for r in rows if r['item_id']=='30FC')
        self.assertTrue(diary['asset_ready'])
        self.assertNotIn('conversion_reason', diary)
        identities = pipeline.identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        for row in rows:
            item = int(row['item_id'],16)
            with self.assertRaisesRegex(pipeline.ReviewRequired, 'parent-item support'):
                pipeline.metadata(self.source,item,{},identities[item])
        with tempfile.TemporaryDirectory(prefix='v3-alias-import-') as temporary:
            output = Path(temporary)/'not-created'
            with self.assertRaisesRegex(ValueError, 'Unsupported'):
                pipeline.convert(self.source, ROOT/'build/item-identity-megasheet.xlsx', output, ['30FC'])
            self.assertFalse(output.exists())
        with self.assertRaisesRegex(ValueError, 'incorrectly installed'):
            pipeline.scan(self.source, ROOT/'build/item-identity-megasheet.xlsx', [0x30FC])

    def test_current_revision_seven_assets_keep_the_complete_source_checks(self):
        import v3_optional_composition as composer
        import v3_furniture_install as install
        _, report = composer.inputs()
        art = ROOT/report['automatic_furniture']['art_directory']
        rows, _ = install.checked_assets(art, self.source, ROOT/'build/item-identity-megasheet.xlsx')
        self.assertEqual({r['item_id'] for r, _ in rows},
                         {r['item_id'] for r in report['automatic_furniture']['imports']})


if __name__ == '__main__':
    unittest.main()
