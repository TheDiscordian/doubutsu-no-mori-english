"""Explicit item identities retain whole names in both bounded resources."""

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
from extended_items_test_scenario import combine_load_scenarios
from item_candidates import item_candidates
from item_matches import identity_key, load_matches, validate_candidate, verify_source
from runtime_module import module_command_info
from textbanks import Bank, banks
from textcodec import encode
from test_retail import ROM_PATH


class ItemScenarioCompositionTests(unittest.TestCase):
    def test_both_loader_bodies_share_one_setup_and_restoration(self):
        prefix = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]
        suffix = [{'guard': True}, {'load_state': True}, {'resume': True}, {'wait': 2}, {'restored': True}]
        wide, native = prefix+[{'wide': i} for i in range(3)]+suffix, prefix+[{'native': i} for i in range(4)]+suffix
        joined = combine_load_scenarios(wide, native)
        self.assertEqual(joined, prefix+wide[3:-5]+native[3:-5]+suffix)
        self.assertEqual(sum('save_state' in x for x in joined), 1)
        self.assertEqual(sum('load_state' in x for x in joined), 1)

    def test_different_checkpoint_or_incomplete_scenarios_fail(self):
        original = [{'step': i} for i in range(9)]
        for index in (0, 2, 4, 8):
            changed = deepcopy(original); changed[index] = {'changed': True}
            with self.assertRaisesRegex(ValueError, 'setup and restoration'):
                combine_load_scenarios(original, changed)
        with self.assertRaises(ValueError): combine_load_scenarios([], original)


class ItemMatchTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.native = encode('あみ', self.info).ljust(10, b' ')
        self.bank = Bank('item_22', 0, None, self.native*2, None, fixed_size=10)
        self.source = {'item_22': self.bank.entries()}
        self.rows = [{'id': f'item_22:{i:04X}', 'source_sha256': sha256(self.native),
                      'legacy_entry_id': f'item_22:{i:04X}', 'legacy': 'different wording'} for i in range(2)]
        self.refs = [{'id': f'item_22:{i:04X}', 'text': 'net' if i else 'long named net',
                      'source_sha256': sha256((b'net' if i else b'long named net').ljust(16, b' '))}
                     for i in range(2)]
        self.match = {'id': 'item_22:0000', 'native_name': 'あみ',
                      'source_sha256': sha256(self.native), 'reference_id': 'item_22:0001',
                      'reference_sha256': self.refs[1]['source_sha256'],
                      'evidence': 'Synthetic independently reviewed cross-index name identity'}
        self.matches = {self.match['id']: self.match}

    def generate(self, matches=None, width=10):
        return item_candidates(self.bank, self.rows, self.refs, self.info, capacity=width,
                               matches=self.matches if matches is None else matches)

    def test_explicit_cross_index_match_does_not_relax_unreviewed_legacy_names(self):
        self.assertEqual(self.generate(matches={})[0], [])
        edits, _, remaining, report = self.generate()
        self.assertEqual(len(edits), 1)
        self.assertEqual(edits[0]['translation'], 'net')
        self.assertEqual(edits[0]['provenance']['reference_id'], 'item_22:0001')
        self.assertEqual(edits[0]['provenance']['legacy_entry_id'], 'item_22:0000')
        self.assertEqual(edits[0]['item_reference_match'], 'item_22:0000')
        self.assertEqual(report['reviewed_identity_candidates'], 1)
        self.assertEqual(remaining[0]['reason'], 'item_identity_not_confirmed_by_legacy')
        validate_candidate(edits[0], self.source, self.info, self.matches)

    def test_complete_long_names_remain_withheld_at_ten_and_fit_at_sixteen(self):
        self.match.update(reference_id='item_22:0000', reference_sha256=self.refs[0]['source_sha256'])
        self.assertEqual(self.generate()[0], [])
        self.assertEqual(self.generate()[2][0]['reason'], 'full_reference_name_exceeds_native_ten_bytes')
        edit = self.generate(width=16)[0][0]
        self.assertEqual(edit['translation'], 'long named net')
        validate_candidate(edit, self.source, self.info, self.matches)
        for text in ('long named', 'net', 'LONG NAMED NET'):
            with self.assertRaisesRegex(ValueError, 'complete exact'):
                validate_candidate({**edit, 'translation': text}, self.source, self.info, self.matches)

    def test_source_reference_and_native_wording_are_independently_bound(self):
        for field, value in (('source_sha256', '0'*64), ('native_name', 'スコップ'),
                             ('reference_sha256', '0'*64), ('reference_id', 'item_22:0002')):
            matches = deepcopy(self.matches); matches[self.match['id']][field] = value
            with self.assertRaises(ValueError): self.generate(matches)
        edit = self.generate()[0][0]
        for field, value in (('reference_id', 'item_22:0000'), ('reference_sha256', '0'*64)):
            changed = deepcopy(edit); changed['provenance'][field] = value
            with self.assertRaisesRegex(ValueError, 'complete exact'):
                validate_candidate(changed, self.source, self.info, self.matches)
        changed = deepcopy(edit); changed['item_reference_match'] = 'item_22:FFFF'
        with self.assertRaisesRegex(ValueError, 'Unknown item'):
            validate_candidate(changed, self.source, self.info, self.matches)
        for value in (None, [], True):
            with self.assertRaisesRegex(ValueError, 'named approval'):
                validate_candidate({**edit, 'item_reference_match': value}, self.source, self.info, self.matches)
        # Removing the metadata does not bypass an approval for the actual ID.
        changed = deepcopy(edit); changed.pop('item_reference_match'); changed['translation'] = 'bad'
        with self.assertRaisesRegex(ValueError, 'complete exact'):
            validate_candidate(changed, self.source, self.info, self.matches)

    def test_schema_rejects_partial_rotation_wrong_family_duplicate_and_bad_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'matches.json'
            path.write_text(json.dumps([self.match]))
            self.assertEqual(load_matches(path), self.matches)
            variants = [[self.match, self.match], {},
                        [{**self.match, 'id': 'item_10:0001', 'reference_id': 'furniture:0000'}],
                        [{**self.match, 'reference_id': 'item_23:0000'}],
                        [{**self.match, 'reference_sha256': 'bad'}],
                        [{**self.match, 'native_name': ''}], [{**self.match, 'evidence': ''}]]
            for rows in variants:
                path.write_text(json.dumps(rows))
                with self.assertRaises(ValueError): load_matches(path)
        self.assertEqual(identity_key('item_10:0123'), 'item_10:0120')

    def test_native_alias_needs_the_exact_conversion_donor_source_and_full_name(self):
        native = encode('ふく', self.info).ljust(10, b' ')
        match = {**self.match, 'id': 'item_10:07AC', 'native_name': 'ふく',
                 'source_sha256': sha256(native), 'reference_id': 'furniture:01EB'}
        matches = {match['id']: match}
        source = {'item_10': [b' '*10]*0x7AC+[native]*4, 'item_24': [native]}
        edit = {'id': 'item_24:0000', 'source_sha256': sha256(native), 'translation': 'net',
                'item_reference_match': match['id'], 'provenance': {
                    'reference_id': match['reference_id'], 'reference_sha256': match['reference_sha256'],
                    'match_basis': 'native_placed_conversion_and_identical_source_name',
                    'native_equivalent_id': 'item_10:07AC', 'native_item_id': '17AC', 'converted_item_id': '2400'}}
        validate_candidate(edit, source, self.info, matches)
        for field, value in (('native_item_id', '17AD'), ('converted_item_id', '2401'),
                             ('native_equivalent_id', 'item_10:07B0')):
            changed = deepcopy(edit); changed['provenance'][field] = value
            with self.assertRaisesRegex(ValueError, 'alias'):
                validate_candidate(changed, source, self.info, matches)
        source['item_10'][0x7AF] = b'changed   '
        with self.assertRaisesRegex(ValueError, 'rotation names'):
            validate_candidate(edit, source, self.info, matches)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/names/furniture.jsonl').is_file(),
                     'Retail ROM and English names stay local')
class ItemMatchRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.banks = {b.name: b for b in banks(cls.rom)}
        cls.source = {name: b.entries() for name, b in cls.banks.items()}
        cls.matches = load_matches()
        cls.rows = list(map(json.loads, (ROOT/'build/inventory/item_10.jsonl').read_text().splitlines()))
        cls.refs = list(map(json.loads, (ROOT/'build/gamecube/names/furniture.jsonl').read_text().splitlines()))

    def test_all_reviewed_names_rotations_hashes_and_precise_capacity_totals(self):
        self.assertEqual(len(self.matches), 179)
        refs = {r['id']: r for r in self.refs}
        for key, match in self.matches.items():
            first = int(key.split(':')[1], 16)
            self.assertEqual(first % 4, 0)
            self.assertEqual(match['reference_id'], f'furniture:{first//4:04X}')
            verify_source(match, self.source['item_10'][first], self.info)
            self.assertEqual(self.source['item_10'][first:first+4], [self.source['item_10'][first]]*4)
            reference = refs[match['reference_id']]
            self.assertEqual(sha256(encode(reference['text'], self.info).ljust(16, b' ')), match['reference_sha256'])
        for width, delta in ((10, 212), (16, 716)):
            old = item_candidates(self.banks['item_10'], self.rows, self.refs, self.info, capacity=width)[0]
            new, _, remaining, report = item_candidates(self.banks['item_10'], self.rows, self.refs,
                                                       self.info, capacity=width, matches=self.matches)
            self.assertEqual(len(new)-len(old), delta)
            by_id = {r['id']: r for r in new}
            self.assertTrue(all(by_id[r['id']] == r for r in old))
            self.assertEqual(report['reviewed_identity_candidates'], delta)
            for edit in new: validate_candidate(edit, self.source, self.info, self.matches)
            for match in self.matches.values():
                short = len(refs[match['reference_id']]['text']) <= width
                first = int(match['id'].split(':')[1], 16)
                self.assertEqual([f'item_10:{first+i:04X}' in by_id for i in range(4)], [short]*4)

    def test_ambiguous_art_species_names_and_unused_prefixes_remain_unapproved(self):
        excluded = [0x18, 0x27, 0x2C, 0x2D, *range(0x45, 0x4B), *range(0x4F, 0x53),
                    *range(0xAB, 0xBA), 0xF0, 0xFA, 0xFC, 0x103, 0x10A, 0x120]
        self.assertTrue(all(f'item_10:{i*4:04X}' not in self.matches for i in excluded))
        # Exact complete unused-name references remain valid, without dropping the warning.
        for group in (0xBC, 0xC5):
            key = f'item_10:{group*4:04X}'
            self.assertIn(key, self.matches)
            self.assertIn('しようふか', self.matches[key]['native_name'])

    def test_independent_rom_builder_rejects_incomplete_or_mislabelled_names(self):
        edits = item_candidates(self.banks['item_10'], self.rows, self.refs, self.info, matches=self.matches)[0]
        chosen = next(r for r in edits if 'item_reference_match' in r)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'
            path.write_text(json.dumps([chosen]))
            replacements = {}; count, _ = apply_translations(self.rom, replacements, path)
            self.assertEqual(count, 1)
            for altered in ({**chosen, 'translation': chosen['translation'][:-1]},
                            {k: v for k, v in {**chosen, 'translation': 'bad'}.items() if k != 'item_reference_match'}):
                path.write_text(json.dumps([altered]))
                with self.assertRaisesRegex(ValueError, 'complete exact'):
                    apply_translations(self.rom, {}, path)

    def test_full_resource_retains_long_names_and_rejects_rehashed_shortening(self):
        edits = item_candidates(self.banks['item_10'], self.rows, self.refs, self.info,
                                capacity=16, matches=self.matches)[0]
        chosen = next(r for r in edits if 'item_reference_match' in r and len(r['translation']) > 10)
        complete = resource(self.rom, [chosen]); original = resource(self.rom, [])
        index = int(chosen['id'].split(':')[1], 16)
        offset = 32+(sum(len(v) for k, v in self.source.items() if k.startswith('item_') and k != 'item_10')+index)*16
        self.assertEqual(complete[:offset], original[:offset])
        self.assertEqual(complete[offset:offset+16], encode(chosen['translation'], self.info).ljust(16, b' '))
        self.assertEqual(complete[offset+16:], original[offset+16:])
        changed = deepcopy(chosen); changed['translation'] = changed['translation'][:10]
        changed['provenance']['reference_sha256'] = sha256(encode(changed['translation'], self.info).ljust(16, b' '))
        with self.assertRaisesRegex(ValueError, 'complete exact'):
            resource(self.rom, [changed])


if __name__ == '__main__':
    unittest.main()
