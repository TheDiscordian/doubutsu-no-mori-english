"""Complete item-reader accounting retains unresolved strings and source weight."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import item_name_readers as names


class ItemReaderGateTests(unittest.TestCase):
    def test_requires_every_display_and_letter_family(self):
        report = {key: {'installed': True} for key in names.REQUIRED}
        report.update({'text_extension': {'choices': {'installed': True}},
                       'inventory_english': {'overlay': {'descriptions': True}},
                       'extended_font': {'font': {'world_names': True}},
                       'noticeboard': {'treasure_owner': {'installed': True}}})
        self.assertTrue(names.complete(report))
        for key in (*names.REQUIRED, 'text_extension'):
            broken = copy.deepcopy(report); del broken[key]
            self.assertFalse(names.complete(broken), key)
        for parent, child in (('inventory_english', 'overlay'), ('extended_font', 'font'),
                              ('noticeboard', 'treasure_owner'), ('text_extension', 'choices')):
            broken = copy.deepcopy(report); broken[parent][child] = {}
            self.assertFalse(names.complete(broken), (parent, child))

    @unittest.skipUnless((ROOT/'build/letter-names-pilot/build.json').is_file(), 'Complete name cartridge required')
    def test_unconnected_and_non_item_sources_keep_their_pending_rules(self):
        from translation_progress import pending_name_consumers
        self.assertIn('extended_items', pending_name_consumers({'extended_items': {'installed': True}}))
        report = json.loads((ROOT/'build/letter-names-pilot/build.json').read_text())
        self.assertNotIn('extended_items', pending_name_consumers(report))
        self.assertIn('catchphrases', pending_name_consumers(report))
        report['catalogue_names'] = {}
        self.assertIn('extended_items', pending_name_consumers(report))


@unittest.skipUnless((ROOT/'build/letter-names-pilot/build.json').is_file(), 'Complete name cartridge required')
class ItemReaderCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (ROOT/'build/letter-names-pilot/animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((ROOT/'build/letter-names-pilot/build.json').read_text())

    def test_full_setter_catalogue_song_and_world_routes_verify(self):
        names.verify_additional_routes(self.built, self.native, self.report)
        for symbol in ('af_set_item_str', 'af_quest_set_item', 'af_copy_item_string'):
            changed = copy.deepcopy(self.report)
            changed['runtime_module']['symbols'][symbol] = '80196818'
            with self.assertRaises(ValueError): names.verify_additional_routes(self.built, self.native, changed)
        changed = copy.deepcopy(self.report); changed['catalogue_names']['overlay']['symbols']['af_catalog_draw'] += 4
        with self.assertRaises(ValueError): names.verify_additional_routes(self.built, self.native, changed)
        changed = copy.deepcopy(self.report); changed['extended_font']['font']['sha256'] = '0'*64
        with self.assertRaises(ValueError): names.verify_additional_routes(self.built, self.native, changed)

    def test_full_measurement_counts_items_once_but_not_missing_accents(self):
        from translation_progress import measure
        ledger = measure(self.native, self.built, self.report)
        weight = names.resource_only_weight(ledger)
        self.assertGreater(weight, 0)
        self.assertEqual(ledger.summary()['total_source_characters'], 751284)
        self.assertEqual(ledger.summary()['replaced_source_characters'],
                         720689+names.resource_only_weight(ledger, ('extended_items', 'display_names')))
        for key in ('item_24:00A8', 'item_25:0005', 'item_2A:0031', 'item_2A:0033'):
            self.assertFalse(ledger.rows[key]['replacements'], key)
        self.assertFalse(any(p['route'] == 'extended_items' for row in ledger.rows.values()
                             for p in row['pending_replacements']))
        self.assertTrue(any(p['route'] == 'catchphrases' for row in ledger.rows.values()
                            for p in row['pending_replacements']))


if __name__ == '__main__': unittest.main()
