import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from v3_import_progress import canonical_item, candidate_rows, installed_rows, summarise


class ImportProgressTests(unittest.TestCase):
    def test_states_are_not_extra_items(self):
        self.assertEqual({canonical_item(0x2003+i*64) for i in range(4)}, {0x2003})
        self.assertEqual(canonical_item(0x223F), 0x2201)
        self.assertEqual(canonical_item(0x252F), 0x2523)
        self.assertEqual(canonical_item(0x2D2C), 0x2D28)

    def test_all_categories_and_exclusions(self):
        def row(item, **fields):
            return dict(E=item, C='-', H='-', CG='-', CJ='-', HG='1', HR='Stationery', J='sample', **fields)
        rows = [(2, row('2003')), (3, row('2043')), (4, row('3000')),
                (5, row('3004')), (6, dict(row('2004'), C='2004')),
                (7, dict(row('2005'), HG='0')), (8, row('2006'))]
        result = candidate_rows(rows, {0x3000}, {0x3004})
        self.assertEqual(set(result), {'GAFE01-r0/item/2003', 'GAFE01-r0/item/2006'})
        self.assertEqual(result['GAFE01-r0/item/2003']['kind'], 'stationery')

    def test_artwork_alone_is_not_completion(self):
        report = dict(staged_furniture=dict(rows=[dict(id='art', profile_installed=False,
                      item_record_installed=True, room_runtime={'vrom': 123}),
                      dict(id='bound', profile_installed=True, item_record_installed=True,
                           room_runtime={'vrom': 456})]))
        self.assertEqual(set(installed_rows(report, {'active': {}})), {'active', 'bound'})

    def test_acquisition_does_not_block_surface_credit(self):
        report = dict(room_surfaces=dict(menu=dict(surface_options_enabled=True),
            save=dict(surface_options_enabled=True), sound=dict(runtime_installed=True),
            optional_selection=dict(pending={'ready': 'Harvest rewards', 'unfinished': 'drawing'})))
        self.assertEqual(set(installed_rows(report, {})), {'ready'})

    def test_unknown_staging_dependency_fails(self):
        with self.assertRaises(ValueError):
            installed_rows(dict(staged_furniture=dict(deferred_resources=['missing drawing'])), {})

    def test_combined_percentage_counts_content_not_categories(self):
        rows = {str(i): dict(id=str(i), kind='furniture' if i < 3 else 'villagers') for i in range(4)}
        result = summarise(rows, {'0': 'done', '1': 'done', '3': 'done'}, {'3': {}})
        self.assertEqual((result['percent'], result['remaining'], result['selectable']), (75.0, 1, 1))
        with self.assertRaises(ValueError):
            summarise(rows, {'unknown': 'done'}, {})


if __name__ == '__main__':
    unittest.main()
