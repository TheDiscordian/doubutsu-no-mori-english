"""Complete cross-bank references require their own native and output audit."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from build import apply_translations
from font import make_halfwidth
from reference_mail_fragments import (APPROVALS, POLICY, load_fragment_matches,
    reference_fragment_edits, validate_fragment_candidate, verify_fragment_source)
from reference_matches import load_matches
from textbanks import banks
from textcodec import command_info, encode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH


class FragmentGuardTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.source = encode('こんにちは {cmd:7F24}。{cmd:7F00}', self.info)
        self.donor = encode(' こんにちは {cmd:7F24}。\n', self.info)
        self.reference = {'id': 'maila:0000', 'text': 'Hello, {cmd:7F24}.\n'}
        self.reference['sha256'] = sha256(encode(self.reference['text'], self.info))
        self.output = encode(self.reference['text']+'{cmd:7F00}', self.info)
        self.record = {'id': 'message:0000', 'reference_id': 'maila:0000',
                       'source_sha256': sha256(self.source), 'native_reference_sha256': sha256(self.donor),
                       'reference_sha256': self.reference['sha256'], 'encoded_sha256': sha256(self.output),
                       'comparison': 'identical_body', 'evidence': 'Complete native body comparison.'}
        self.sources = {'message': [self.source], 'maila': [self.donor]}
        self.inventory = {'maila:0000': {'id': 'maila:0000', 'source_sha256': sha256(self.donor),
                                        'legacy': self.reference['text']}}

    def edits(self, record=None, reference=None, inventory=None):
        return reference_fragment_edits({'message:0000': record or self.record}, self.sources,
            {'maila:0000': reference or self.reference}, inventory or self.inventory, self.info)

    def test_complete_reference_keeps_every_space_line_and_native_ending(self):
        edit = self.edits()['message:0000']
        self.assertEqual(encode(edit['translation'], self.info), self.output)
        self.assertEqual(edit['control_policy'], POLICY)
        self.assertEqual(edit['adaptations'], [{'operation': 'append_native_dialogue_ending', 'command': '7F00'}])
        self.assertEqual(edit['provenance']['reference_id'], 'maila:0000')
        self.assertIn('not_reviewed', edit['status'])

    def test_source_donor_and_complete_english_hashes_are_enforced(self):
        for key in ('source_sha256', 'native_reference_sha256', 'reference_sha256', 'encoded_sha256'):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.edits(record={**self.record, key: '0'*64})
        for reference in ({**self.reference, 'text': 'Changed\n'},
                          {**self.reference, 'id': 'mailb:0000'}):
            with self.assertRaises(ValueError): self.edits(reference=reference)
        inventory = deepcopy(self.inventory); inventory['maila:0000']['legacy'] += ' '
        with self.assertRaisesRegex(ValueError, 'legacy agreement'): self.edits(inventory=inventory)

    def test_normalization_cannot_erase_internal_spacing_or_content(self):
        for donor in (self.donor.replace(b' ', b'  '), self.donor.replace(b'\x7f\x24', b'\x7f\x25')):
            record = {**self.record, 'native_reference_sha256': sha256(donor)}
            with self.assertRaisesRegex(ValueError, 'native (comparison|field sequence)'):
                verify_fragment_source(record, self.source, donor, self.info)
        with self.assertRaisesRegex(ValueError, 'native comparison'):
            self.edits(record={**self.record, 'comparison': 'reviewed_native_variation'})

    def test_reviewed_variation_remains_hash_bound_and_has_identical_native_fields(self):
        donor = self.donor.replace(b' ', b'  ')
        record = {**self.record, 'native_reference_sha256': sha256(donor),
                  'comparison': 'reviewed_native_variation'}
        verify_fragment_source(record, self.source, donor, self.info)
        with self.assertRaises(ValueError):
            verify_fragment_source(record, self.source, donor+b' ', self.info)

    def test_reference_cannot_add_fields_actions_or_non_english_glyphs(self):
        for text in ('Hi {cmd:7F25}\n', 'Hi {cmd:7F04}\n', 'Hi {cmd:7F00}\n',
                     'Hi {glyph:8001}\n', 'こんにちは\n', '\n'):
            reference = {**self.reference, 'text': text, 'sha256': sha256(encode(text, self.info))}
            record = {**self.record, 'reference_sha256': reference['sha256'],
                      'encoded_sha256': sha256(encode(text+'{cmd:7F00}', self.info))}
            inventory = deepcopy(self.inventory); inventory['maila:0000']['legacy'] = text
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.edits(record, reference, inventory)

    def test_candidate_cannot_change_wording_ending_or_policy(self):
        for data in (self.output+b' ', b'Changed\xcd\x7f\x00', self.output[:-1]+b'\x01'):
            with self.assertRaisesRegex(ValueError, 'complete approved reference'):
                validate_fragment_candidate(self.record['id'], self.source, data,
                    {self.record['id']: self.record}, self.sources, self.info, POLICY)
        with self.assertRaisesRegex(ValueError, 'complete approved reference'):
            validate_fragment_candidate(self.record['id'], self.source, self.output,
                {self.record['id']: self.record}, self.sources, self.info, 'reference_layout')

    def test_schema_is_separate_strict_and_rejects_duplicate_or_combined_approvals(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'approvals.json'
            path.write_text(json.dumps([self.record]))
            self.assertEqual(load_fragment_matches(path), {'message:0000': self.record})
            # The ordinary resolver must still reject arbitrary cross-bank IDs.
            with self.assertRaisesRegex(ValueError, 'Cross-bank'): load_matches(path)
            for records in ([self.record, self.record], [{**self.record, 'available_fields': {}}],
                            [{**self.record, 'id': 'select:0000'}],
                            [{**self.record, 'reference_id': 'message:0000'}],
                            [{**self.record, 'comparison': 'fuzzy'}],
                            [{**self.record, 'source_sha256': False}],
                            [{**self.record, 'evidence': ''}], {}):
                path.write_text(json.dumps(records))
                with self.assertRaises(ValueError): load_fragment_matches(path)


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM stays local')
class RetailFragmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = command_info(by_vrom(cls.rom)[CODE_VROM].extract(cls.rom))
        cls.sources = {b.name: b.entries() for b in banks(cls.rom)}
        cls.matches = load_fragment_matches()

    def all_edits(self):
        references, inventory = {}, {}
        for bank in ('maila', 'mailb', 'mailc'):
            path = ROOT/'build/gamecube/text'/(bank+'.jsonl')
            if not path.is_file(): self.skipTest('English disc extraction stays local')
            references.update({r['id']: r for r in map(json.loads, path.read_text().splitlines())})
            path = ROOT/'build/inventory'/(bank+'.jsonl')
            if not path.is_file(): self.skipTest('Native/legacy inventory stays local')
            inventory.update({r['id']: r for r in map(json.loads, path.read_text().splitlines())})
        return reference_fragment_edits(self.matches, self.sources, references, inventory, self.info), references

    def test_all_74_native_mappings_and_complete_reference_payloads(self):
        edits, references = self.all_edits()
        expected = set(range(0x1BFF, 0x1C3F)) | set(range(0x1C53, 0x1C5F))
        expected -= {0x1C18, 0x1C1D}
        self.assertEqual({int(id[8:], 16) for id in edits}, expected)
        self.assertEqual(sum(r['comparison']=='identical_body' for r in self.matches.values()), 66)
        variations = {id[8:] for id, r in self.matches.items() if r['comparison']=='reviewed_native_variation'}
        self.assertEqual(variations, set('1C01 1C07 1C22 1C29 1C2C 1C2E 1C33 1C3A'.split()))
        for id, edit in edits.items():
            ref = references[edit['provenance']['reference_id']]
            self.assertEqual(edit['translation'], ref['text']+'{cmd:7F00}', id)
            candidate = encode(edit['translation'], self.info)
            validate_entry(self.sources['message'][int(id[8:],16)], candidate, self.info, 'message', POLICY)
            self.assertLessEqual(expanded_bound(candidate, self.info), 136)

    def test_builder_checks_registered_payloads_without_provenance_metadata(self):
        edits, _ = self.all_edits()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'changed.json'
            for id in ('message:1C00', 'message:1C29', 'message:1C5E'):
                edit = {key: edits[id][key] for key in ('id', 'source_sha256', 'translation', 'control_policy')}
                edit['translation'] = 'Altered '+edit['translation']
                path.write_text(json.dumps([edit]))
                with self.assertRaisesRegex(ValueError, 'Mail-fragment candidate'):
                    apply_translations(self.rom, {}, path)

    def test_two_native_drafts_preserve_name_field_joke_and_all_controls(self):
        drafts = json.loads((ROOT/'translations/n64-letter-fragments.json').read_text())
        self.assertEqual({r['id'] for r in drafts}, {'message:1C18', 'message:1C1D'})
        _, font = make_halfwidth(self.rom)
        advances = {int(k,16): v for k,v in font['advance_by_glyph'].items()}
        for row in drafts:
            source = self.sources['message'][int(row['id'][8:],16)]
            candidate = encode(row['translation'], self.info)
            self.assertEqual(sha256(source), row['source_sha256'])
            commands = lambda raw: [t.data for t in tokenize(raw,self.info) if t.kind=='cmd']
            self.assertEqual(commands(source), commands(candidate))
            validate_entry(source, candidate, self.info, 'message', 'exact')
            self.assertEqual(layout_issues(candidate,self.info,advances), [])
            if row['id']=='message:1C18':
                self.assertIn("It's me, {cmd:7F24}",row['translation'])
                self.assertNotIn('{cmd:7F25}', row['translation'])
            else:
                self.assertIn('Only kidding!', row['translation'])


if __name__ == '__main__':
    unittest.main()
