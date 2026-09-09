"""Reviewed bilingual names bind local sources; cached sheets never auto-approve."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, verified_rom
from build import apply_translations
from extended_items import resource, VROM
from item_identity_sheet import identity_queue, sheet_rows, SHEET_SHA
from item_matches import load_matches, validate_candidate, verify_source, SHEET_APPROVALS
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/sheet-items-pilot'
PREVIOUS = ROOT/'build/notice-seasonal-pilot'
APPROVED = json.loads(SHEET_APPROVALS.read_text())
KEYS = {r['id'] for r in APPROVED}


class SheetReaderTests(unittest.TestCase):
    def test_only_cached_values_are_read_and_sparse_columns_remain_addressed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'fixture.xlsx'
            with ZipFile(path, 'w') as archive:
                archive.writestr('xl/workbook.xml',
                    '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                    'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                    '<sheets><sheet name="Items" r:id="id1"/></sheets></workbook>')
                archive.writestr('xl/_rels/workbook.xml.rels',
                    '<Relationships><Relationship Id="id1" Target="worksheets/a.xml"/></Relationships>')
                archive.writestr('xl/sharedStrings.xml',
                    '<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    '<si><r><t>Test </t></r><r><t>name</t></r></si></sst>')
                archive.writestr('xl/worksheets/a.xml',
                    '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                    '<sheetData><row r="1"><c r="A1" t="s"><v>0</v></c>'
                    '<c r="CJ1" t="inlineStr"><is><t>Inline</t></is></c>'
                    '<c r="CX1"><f>untrusted_formula()</f><v>cached</v></c>'
                    '</row></sheetData></worksheet>')
            self.assertEqual(list(sheet_rows(path, 'Items')),
                             [(1, {'A': 'Test name', 'CJ': 'Inline', 'CX': 'cached'})])
            with self.assertRaises(ValueError): list(sheet_rows(path, 'Missing'))

    def test_approvals_are_explicit_unique_and_do_not_include_open_identity_conflicts(self):
        self.assertEqual((len(APPROVED), len(KEYS)), (327, 327))
        old, new = load_matches(include_sheet=False), load_matches(include_resolved=False)
        self.assertEqual(new.keys()-old.keys(), KEYS)
        self.assertTrue(all(new[key] == value for key, value in old.items()))
        for row in APPROVED:
            self.assertEqual(row['identity_sheet']['sha256'], SHEET_SHA)
            self.assertIn('Items row '+str(row['identity_sheet']['row']), row['evidence'])
            self.assertIn('native artwork and behaviour remain unchanged', row['evidence'])
        for key in ('item_10:07FC', 'item_10:0800', 'item_24:0014', 'item_24:0015',
                    'item_10:0A4C', 'item_10:0BBC', 'item_10:0264', 'item_20:0003',
                    'item_26:0012', 'item_26:001A', 'item_27:0012', 'item_27:001A',
                    'item_2A:0031', 'item_2A:0033', 'item_25:0005'):
            self.assertNotIn(key, new)


@unittest.skipUnless((ROOT/'build/item-identity-megasheet.xlsx').is_file(), 'Local cached identity sheet required')
class SheetEvidenceTests(unittest.TestCase):
    def test_every_approval_retains_its_exact_source_row_and_complete_reference(self):
        rows = identity_queue(ROOT/'build/item-identity-megasheet.xlsx', ROOT/'build/inventory',
                              ROOT/'build/gamecube/names', ROOT/'build/native-items-resource')
        indexed = {row['id']: row for row in rows}
        self.assertEqual(len(rows), 387)
        for approval in APPROVED:
            row = indexed[approval['id']]
            self.assertEqual(row['reason'], 'exact_bilingual_identity_requires_review')
            self.assertEqual(row['visual_changes'], [])
            for key in ('source_sha256', 'native_name', 'reference_id', 'reference_sha256'):
                self.assertEqual(row[key], approval[key])
            self.assertEqual(row['sheet_row'], approval['identity_sheet']['row'])
            self.assertEqual(row['sheet_item'], approval['identity_sheet']['item'])


@unittest.skipUnless(ROM.is_file() and (ROOT/'build/sheet-items-resource/names.json').is_file(),
                     'Local original ROM and generated item resources required')
class SheetNameResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(ROM.read_bytes())
        cls.info = module_command_info(cls.native)
        cls.source = {b.name: b.entries() for b in banks(cls.native)}
        cls.matches = load_matches(include_resolved=False)
        cls.names = json.loads((ROOT/'build/sheet-items-resource/names.json').read_text())
        cls.old = json.loads((ROOT/'build/native-items-resource/names.json').read_text())

    def test_all_834_new_slots_keep_exact_complete_english_and_earlier_edits(self):
        old, new = [{r['id']: r for r in rows['edits']} for rows in (self.old, self.names)]
        self.assertEqual((len(old), len(new)), (3563, 4397))
        self.assertTrue(all(new[key] == value for key, value in old.items()))
        self.assertEqual(new.keys()-old.keys(), {key for key in new if new[key].get('item_reference_match') in KEYS})
        refs = {r['id']: r for bank in ('furniture', 'item_22', 'item_24', 'item_25', 'item_26', 'item_27')
                for r in map(json.loads, (ROOT/f'build/gamecube/names/{bank}.jsonl').read_text().splitlines())}
        for approval in APPROVED:
            bank, index = approval['id'].split(':'); index = int(index, 16)
            verify_source(approval, self.source[bank][index], self.info)
            ref = refs[approval['reference_id']]
            raw = encode(ref['text'], self.info)
            self.assertLessEqual(len(raw), 16)
            self.assertEqual(sha256(raw.ljust(16, b' ')), approval['reference_sha256'])
            for offset in range(4 if bank == 'item_10' else 1):
                edit = new[f'{bank}:{index+offset:04X}']
                self.assertEqual(edit['translation'], ref['text'])
                validate_candidate(edit, self.source, self.info, self.matches)
        data = (ROOT/'build/sheet-items-resource/names.bin').read_bytes()
        self.assertEqual(data, resource(self.native, self.names['edits']))
        self.assertEqual(len(data), len((ROOT/'build/native-items-resource/names.bin').read_bytes()))

    def test_shortening_or_rehashed_reference_changes_fail_for_every_new_slot(self):
        selected = [r for r in self.names['edits'] if r.get('item_reference_match') in KEYS]
        self.assertEqual(len(selected), 834)
        for edit in selected:
            for removed in (False, True):
                bad = deepcopy(edit)
                if removed: bad.pop('item_reference_match')
                bad['translation'] = bad['translation'][:-1]
                bad['provenance']['reference_sha256'] = sha256(encode(bad['translation'], self.info).ljust(16, b' '))
                with self.assertRaisesRegex(ValueError, 'complete exact'):
                    validate_candidate(bad, self.source, self.info, self.matches)

    def test_112_new_short_fields_fit_without_replacing_earlier_candidates(self):
        old, new = [{r['id']: r for r in json.loads((ROOT/f'build/{folder}/translations.json').read_text())}
                    for folder in ('native-items-candidates', 'sheet-items-candidates')]
        self.assertEqual((len(old), len(new)), (13598, 13710))
        self.assertTrue(all(new[key] == value for key, value in old.items()))
        added = [new[key] for key in new.keys()-old.keys()]
        self.assertTrue(all(r.get('item_reference_match') in KEYS for r in added))
        self.assertTrue(all(len(encode(r['translation'], self.info)) <= 10 for r in added))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'
            path.write_text(json.dumps(added))
            self.assertEqual(apply_translations(self.native, {}, path)[0], 112)
            bad = deepcopy(added[0]); bad.pop('item_reference_match'); bad['translation'] = 'bad'
            bad['provenance']['reference_sha256'] = sha256(b'bad'.ljust(16, b' '))
            path.write_text(json.dumps([bad]))
            with self.assertRaisesRegex(ValueError, 'complete exact'): apply_translations(self.native, {}, path)
            with self.assertRaisesRegex(ValueError, 'complete exact'): resource(self.native, [bad])


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Completed local sheet-name cartridge required')
class SheetNameArtifactTests(unittest.TestCase):
    def test_complete_resource_and_only_name_article_and_configuration_changes_plus_ups(self):
        native = verified_rom(ROM.read_bytes())
        built, previous = [(directory/'animal-forest-halfwidth.z64').read_bytes() for directory in (BUILD, PREVIOUS)]
        report = json.loads((BUILD/'build.json').read_text())
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        old, new = by_vrom(previous), by_vrom(built)
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual({v for v in new if new[v].extract(built) != old[v].extract(previous)},
                         {0x010F4000, VROM, 0x02800000, 0x03200000})
        # Only the complete creator checksum changes inside the resident image.
        a, b = old[0x02800000].extract(previous), new[0x02800000].extract(built)
        self.assertEqual(a[:0x60], b[:0x60])
        self.assertEqual(a[0x64:], b[0x64:])
        names = json.loads((ROOT/'build/sheet-items-resource/names.json').read_text())
        self.assertEqual(new[VROM].extract(built), resource(native, names['edits']))

    def test_combined_counter_credits_exact_new_source_slots_without_losing_earlier_text(self):
        from translation_progress import measure
        native = verified_rom(ROM.read_bytes())
        before, after = [measure(native, (directory/'animal-forest-halfwidth.z64').read_bytes(),
                                 json.loads((directory/'build.json').read_text())) for directory in (PREVIOUS, BUILD)]
        old, new = [{key for key, value in ledger.rows.items() if value['replacements']}
                    for ledger in (before, after)]
        self.assertTrue(old <= new)
        names = json.loads((ROOT/'build/sheet-items-resource/names.json').read_text())
        self.assertEqual(new-old, {r['id'] for r in names['edits'] if r.get('item_reference_match') in KEYS})
        self.assertEqual(before.summary()['total_source_characters'], after.summary()['total_source_characters'])


if __name__ == '__main__': unittest.main()
