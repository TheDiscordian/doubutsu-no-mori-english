"""Native-only designs and the herabuna keep complete, independently bound names."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from build import apply_translations
from extended_items import resource
from item_matches import load_matches, validate_candidate, DESIGN_APPROVALS
from native_item_names import load_names, DESIGN_PATH, SOURCE
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
NEW = ROOT/'build/design-items-resource'


@unittest.skipUnless((NEW/'names.json').is_file(), 'Local complete native-design names required')
class DesignNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(ROM.read_bytes())
        cls.info = module_command_info(cls.native)
        cls.source = {b.name: b.entries() for b in banks(cls.native)}
        cls.names = json.loads((NEW/'names.json').read_text())
        cls.old = json.loads((ROOT/'build/resolved-items-resource/names.json').read_text())
        cls.originals = load_names()
        cls.keys = {r['id'] for r in json.loads(DESIGN_PATH.read_text())}
        cls.matches = load_matches()
        cls.matched = {r['id'] for r in json.loads(DESIGN_APPROVALS.read_text())}
        cls.selected = [r for r in cls.names['edits'] if r.get('native_item_name') in cls.keys
                        or r.get('item_reference_match') in cls.matched]

    def test_74_new_fields_and_one_species_correction_preserve_every_other_name(self):
        old, new = [{r['id']: r for r in report['edits']} for report in (self.old, self.names)]
        self.assertEqual((len(self.keys), len(self.matched), len(self.selected)), (21, 4, 75))
        self.assertEqual((len(old), len(new)), (4462, 4536))
        self.assertEqual(new.keys()-old.keys(), {r['id'] for r in self.selected}-{'item_23:0001'})
        self.assertEqual([k for k in old if old[k]['translation'] != new[k]['translation']], ['item_23:0001'])
        self.assertEqual((old['item_23:0001']['translation'], new['item_23:0001']['translation']),
                         ('brook trout', 'herabuna'))
        self.assertTrue(all(new[k] == old[k] for k in old if k != 'item_23:0001'))
        self.assertEqual(resource(self.native, self.names['edits']), (NEW/'names.bin').read_bytes())
        for row in self.selected:
            validate_candidate(row, self.source, self.info, self.matches)
            if row.get('native_item_name') in self.keys:
                self.assertEqual(row['provenance']['source'], SOURCE)
                self.assertEqual(row['translation'], self.originals[row['native_item_name']]['translation'])
        self.assertEqual(new['item_24:0069']['translation'], new['item_10:0950']['translation'])
        self.assertEqual(new['item_23:0001']['translation'], new['item_10:0C2C']['translation'])
        self.assertEqual(new['item_10:07FC']['translation'], 'red sweats')
        self.assertEqual(new['item_24:0014']['translation'], 'red sweatsuit')
        self.assertEqual(new['item_10:0800']['translation'], 'blue sweats')
        self.assertEqual(new['item_24:0015']['translation'], 'blue sweatsuit')
        remaining = {r['id'] for p in NEW.glob('*remaining.jsonl') for r in map(json.loads, p.read_text().splitlines())}
        self.assertEqual(remaining, {*(f'item_10:{i:04X}' for i in range(0xA4C, 0xA50)),
                                    'item_24:00A8', 'item_25:0005', 'item_2A:0031', 'item_2A:0033'})

    def test_complete_source_and_provenance_reject_shortening_even_without_metadata(self):
        for row in self.selected:
            for removed in (False, True):
                changed = deepcopy(row)
                if removed:
                    changed.pop('native_item_name', None); changed.pop('item_reference_match', None)
                changed['translation'] = changed['translation'][:-1]
                changed['provenance']['reference_sha256'] = sha256(encode(changed['translation'], self.info).ljust(16, b' '))
                with self.assertRaises(ValueError): validate_candidate(changed, self.source, self.info, self.matches)
        for key in ('item_23:0001', 'item_10:0C2C'):
            row = deepcopy(next(r for r in self.selected if r['id'] == key))
            row.pop('native_item_name'); row['translation'] = 'brook trout'
            row['provenance']['reference_sha256'] = sha256(b'brook trout'.ljust(16, b' '))
            with self.assertRaises(ValueError): resource(self.native, [row])

    def test_all_18_short_fields_and_both_builders_keep_complete_names(self):
        selected = [r for r in self.selected if len(encode(r['translation'], self.info)) <= 10]
        self.assertEqual(len(selected), 18)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'; path.write_text(json.dumps(selected))
            self.assertEqual(apply_translations(self.native, {}, path)[0], 18)
            for row in selected:
                bad = deepcopy(row)
                bad.pop('native_item_name', None); bad.pop('item_reference_match', None)
                bad['translation'] = 'bad'
                bad['provenance']['reference_sha256'] = sha256(b'bad'.ljust(16, b' '))
                path.write_text(json.dumps([bad]))
                with self.assertRaises(ValueError): apply_translations(self.native, {}, path)
                with self.assertRaises(ValueError): resource(self.native, [bad])


if __name__ == '__main__': unittest.main()
