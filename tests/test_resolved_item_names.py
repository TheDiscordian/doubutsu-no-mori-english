"""Explicit paper IDs and native carried identities resolve complete item names."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, verified_rom
from build import apply_translations
from extended_items import resource, VROM
from item_aliases import ordinary_item
from item_identity_sheet import identity_queue, sheet_rows, SHEET_SHA
from item_matches import load_matches, reference_rows, validate_candidate, RESOLVED_APPROVALS
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/resolved-items-pilot'
PREVIOUS = ROOT/'build/sheet-items-pilot'
APPROVED = json.loads(RESOLVED_APPROVALS.read_text())
KEYS = {r['id'] for r in APPROVED}


class ResolvedApprovalTests(unittest.TestCase):
    def test_exact_conversion_family_and_existing_carried_approval_are_required(self):
        matches = load_matches()
        previous = load_matches(include_resolved=False)
        self.assertEqual((len(APPROVED), len(KEYS), len(matches)-len(previous)), (30, 30, 30))
        self.assertTrue(all(matches[k] == row for k, row in previous.items()))
        reverse = [r for r in APPROVED if 'native_carried_id' in r]
        self.assertEqual(len(reverse), 8)
        for row in reverse:
            number = 0x1000+int(row['id'].split(':')[1], 16)
            converted = ordinary_item(number)
            self.assertEqual(row['native_carried_id'], f'item_{converted >> 8:02X}:{converted & 255:04X}')
            donor = matches[row['native_carried_id']]
            for field in ('source_sha256', 'native_name', 'reference_id', 'reference_sha256'):
                self.assertEqual(row[field], donor[field])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'approvals.json'
            all_rows = list(matches.values())
            target = next(i for i, r in enumerate(all_rows) if r['id'] == 'item_10:0A5C')
            for field, value in (('native_carried_id', 'item_24:00AD'),
                                 ('native_carried_id', None), ('reference_id', 'furniture:0297'),
                                 ('reference_id', 'item_24:00AD'), ('source_sha256', '0'*64),
                                 ('reference_sha256', '0'*64), ('native_name', 'different')):
                changed = deepcopy(all_rows); changed[target][field] = value
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError, msg=field): load_matches(path)
            for changed in ([r for r in all_rows if r['id'] != 'item_24:00AC'],
                            [{k: v for k, v in r.items() if k != 'native_carried_id'}
                             if r['id'] == 'item_10:0A5C' else r for r in all_rows]):
                path.write_text(json.dumps(changed))
                with self.assertRaises(ValueError): load_matches(path)


@unittest.skipUnless((ROOT/'build/item-identity-megasheet.xlsx').is_file(), 'Local identity snapshot required')
class ResolvedEvidenceTests(unittest.TestCase):
    def test_paper_quantity_ids_pattern_references_and_individual_dot_exceptions(self):
        snapshot = ROOT/'build/item-identity-megasheet.xlsx'
        self.assertEqual(sha256(snapshot.read_bytes()), SHEET_SHA)
        cells = dict(sheet_rows(snapshot, 'Items'))
        queue = {r['id']: r for r in identity_queue(snapshot, ROOT/'build/inventory',
                  ROOT/'build/gamecube/names', ROOT/'build/sheet-items-resource')}
        papers = [r for r in APPROVED if r['id'].startswith('item_20:')]
        poles = [r for r in APPROVED if r['id'] in {'item_10:013C', 'item_10:0140', 'item_10:0144', 'item_10:0148'}]
        self.assertEqual((len(papers), len(poles)), (17, 4))
        for row in papers+poles:
            evidence = cells[row['identity_sheet']['row']]
            self.assertEqual(row['identity_sheet']['sha256'], SHEET_SHA)
            self.assertEqual(row['identity_sheet']['item'], evidence['A'])
            actual = queue[row['id']]
            self.assertEqual(actual['reference_id'], row['reference_id'])
            self.assertEqual(actual['reference_sha256'], row['reference_sha256'])
            if row in papers:
                self.assertEqual(evidence['H'], row['native_name'])
                self.assertEqual(actual['reason'], 'same_stationery_pattern_requires_model_review')
                self.assertEqual(actual['visual_changes'], ['CG'])
                self.assertEqual(evidence['CJ'], evidence['CX'])
                self.assertEqual(evidence['E'], '20'+row['id'][-2:])
            else:
                self.assertEqual(actual['reason'], 'native_name_differs_from_sheet')
                self.assertEqual(evidence['H'].replace('･', '・'), row['native_name'])
                self.assertNotEqual(evidence['H'], row['native_name'])
                self.assertEqual(actual['visual_changes'], [])
        self.assertEqual(queue['item_20:0003']['reason'], 'missing_or_ambiguous_complete_reference')
        self.assertNotIn('item_20:0003', KEYS)


@unittest.skipUnless((ROOT/'build/resolved-items-resource/names.json').is_file(), 'Local generated names required')
class ResolvedNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(ROM.read_bytes())
        cls.info = module_command_info(cls.native)
        cls.source = {b.name: b.entries() for b in banks(cls.native)}
        cls.matches = load_matches()
        cls.old, cls.new = [json.loads((ROOT/f'build/{kind}-items-resource/names.json').read_text())
                            for kind in ('sheet', 'resolved')]
        cls.selected = [r for r in cls.new['edits'] if r.get('item_reference_match') in KEYS]

    def test_complete_names_rotations_and_preserved_prior_english(self):
        old, new = [{r['id']: r for r in report['edits']} for report in (self.old, self.new)]
        self.assertEqual((len(old), len(new), len(self.selected)), (4397, 4462, 66))
        self.assertEqual(new.keys()-old.keys(), {r['id'] for r in self.selected}-{'item_2D:0005'})
        for key in old:
            self.assertEqual(old[key]['translation'], new[key]['translation'])
            if key != 'item_2D:0005': self.assertEqual(old[key], new[key])
        for row in self.selected: validate_candidate(row, self.source, self.info, self.matches)
        data = (ROOT/'build/resolved-items-resource/names.bin').read_bytes()
        self.assertEqual(resource(self.native, self.new['edits']), data)
        self.assertEqual(len(data), len((ROOT/'build/sheet-items-resource/names.bin').read_bytes()))
        refs = {r['id']: r for r in reference_rows(ROOT/'build/gamecube/names', 'item_10', self.matches)}
        for approval in APPROVED:
            if 'native_carried_id' not in approval: continue
            carried = approval['native_carried_id']
            self.assertEqual(new[carried]['translation'], refs[approval['reference_id']]['text'])
            base = int(approval['id'].split(':')[1], 16)
            for offset in range(4):
                row = new[f'item_10:{base+offset:04X}']
                self.assertEqual(row['translation'], new[carried]['translation'])
                self.assertEqual(row['provenance']['reference_id'], approval['reference_id'])

    def test_removed_metadata_shortening_and_actual_carried_source_mutation_fail(self):
        for row in self.selected:
            for remove in (False, True):
                changed = deepcopy(row)
                if remove: changed.pop('item_reference_match')
                changed['translation'] = changed['translation'][:-1]
                changed['provenance']['reference_sha256'] = sha256(encode(changed['translation'], self.info).ljust(16, b' '))
                with self.assertRaisesRegex(ValueError, 'complete exact'):
                    validate_candidate(changed, self.source, self.info, self.matches)
        placed = next(r for r in self.selected if r['id'] == 'item_10:0A5C')
        source = {**self.source, 'item_24': list(self.source['item_24'])}
        source['item_24'][0xAC] = b'wrong     '
        with self.assertRaisesRegex(ValueError, 'carried identity or source'):
            validate_candidate(placed, source, self.info, self.matches)

    def test_complete_short_candidates_and_both_builders_reject_changed_wording(self):
        old, new = [{r['id']: r for r in json.loads((ROOT/f'build/{kind}-items-candidates/translations.json').read_text())}
                    for kind in ('sheet', 'resolved')]
        self.assertEqual((len(old), len(new)), (13710, 13745))
        self.assertTrue(all(new[k] == value for k, value in old.items()))
        added = [new[k] for k in new.keys()-old.keys()]
        self.assertTrue(all(r.get('item_reference_match') in KEYS for r in added))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'
            path.write_text(json.dumps(added))
            self.assertEqual(apply_translations(self.native, {}, path)[0], 35)
            changed = deepcopy(next(r for r in added if r['id'] == 'item_10:0A5C'))
            changed.pop('item_reference_match'); changed['translation'] = 'No. shirt'
            changed['provenance']['reference_sha256'] = sha256(b'No. shirt'.ljust(16, b' '))
            path.write_text(json.dumps([changed]))
            with self.assertRaisesRegex(ValueError, 'complete exact'): apply_translations(self.native, {}, path)
            with self.assertRaisesRegex(ValueError, 'complete exact'): resource(self.native, [changed])


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Completed resolved-name ROM required')
class ResolvedCartridgeTests(unittest.TestCase):
    def test_installed_payload_changes_and_ups_retain_all_other_text_and_code(self):
        native = verified_rom(ROM.read_bytes())
        old, new = [(path/'animal-forest-halfwidth.z64').read_bytes() for path in (PREVIOUS, BUILD)]
        a, b = by_vrom(old), by_vrom(new)
        self.assertEqual(a.keys(), b.keys())
        self.assertEqual({key for key in a if a[key].extract(old) != b[key].extract(new)},
                         {0x010F4000, VROM, 0x02800000, 0x03200000})
        resident_a, resident_b = a[0x02800000].extract(old), b[0x02800000].extract(new)
        self.assertEqual(resident_a[:0x60], resident_b[:0x60])
        self.assertEqual(resident_a[0x64:], resident_b[0x64:])
        self.assertEqual(b[VROM].extract(new), (ROOT/'build/resolved-items-resource/names.bin').read_bytes())
        self.assertEqual(sha256(new), json.loads((BUILD/'build.json').read_text())['output_sha256'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), new)

    def test_total_accounting_credits_only_65_previously_japanese_fields(self):
        from translation_progress import measure
        native = verified_rom(ROM.read_bytes())
        old, new = [measure(native, (path/'animal-forest-halfwidth.z64').read_bytes(),
                            json.loads((path/'build.json').read_text())) for path in (PREVIOUS, BUILD)]
        a, b = [{k for k, r in ledger.rows.items() if r['replacements']} for ledger in (old, new)]
        self.assertTrue(a <= b)
        names = json.loads((ROOT/'build/resolved-items-resource/names.json').read_text())
        expected = {r['id'] for r in names['edits'] if r.get('item_reference_match') in KEYS}-{'item_2D:0005'}
        self.assertEqual(len(expected), 65)
        self.assertEqual(b-a, expected)
        self.assertEqual(old.summary()['total_source_characters'], new.summary()['total_source_characters'])


if __name__ == '__main__': unittest.main()
