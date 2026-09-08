"""Complete English wording cannot change native random destinations or weights."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from gc_adapter import adapt_reference
from reference_content import adapt_content_reference, validate_content_approval, validate_content_candidate
from reference_matches import load_matches
from reference_random import restore, validate_rule
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry, expanded_bound
from test_retail import ROM_PATH

IDS = ('263E', '2646', '2650', '26C5')
BOUNDS = (58, 58, 59, 127)


class RandomReferenceTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[3], self.info[9], self.info[0x13], self.info[0x14] = (3, 0), (5, 0), (6, 0), (8, 0)
        self.source = encode('A{cmd:7F1311112222}\n{cmd:7F19}{cmd:7F01}', self.info)
        self.text = 'Full\nEnglish!{cmd:7F0306}{cmd:7F14111111112222}\n{cmd:7F19}{cmd:7F01}'
        self.rule = {'source_offset': 1, 'reference_offset': 16,
                     'native_command': '7F1311112222', 'reference_command': '7F14111111112222'}

    def test_exact_command_replacement_retains_all_english_and_presentation(self):
        expected = self.text.replace('7F14111111112222', '7F1311112222')
        text, changes = restore(self.text, self.source, self.rule, self.info)
        self.assertEqual(text, expected)
        self.assertEqual(changes[0]['operation'], 'retain_complete_native_random_branch')

    def test_schema_rejects_wrong_kinds_lengths_offsets_and_destination_sets(self):
        for change in ({'source_offset': True}, {'reference_offset': -1}, {'reference_offset': 1024},
                       {'native_command': None}, {'native_command': '7F1511112222'},
                       {'native_command': '7F131111'}, {'reference_command': '7F14111111113333'},
                       {'reference_command': '7F1311112222'}, {'extra': True}):
            with self.assertRaises(ValueError): validate_rule({**self.rule, **change})

    def test_exact_original_order_and_repeated_entries_are_preserved(self):
        source = encode('A{cmd:7F14222211112222}\n{cmd:7F19}{cmd:7F01}', self.info)
        rule = {**self.rule, 'native_command': '7F14222211112222'}
        text, _ = restore(self.text, source, rule, self.info)
        self.assertIn('{cmd:7F14222211112222}', text)
        self.assertNotIn('{cmd:7F14111111112222}', text)

    def test_missing_duplicate_or_wrong_token_offset_fails(self):
        for source, text, rule in (
                (self.source, self.text, {**self.rule, 'source_offset': 0}),
                (self.source, self.text, {**self.rule, 'reference_offset': 17}),
                (self.source+b'\x7f\x13\x11\x11\x22\x22', self.text, self.rule),
                (self.source, self.text+'{cmd:7F14111111112222}', self.rule),
                (self.source, self.text.replace('{cmd:7F14111111112222}', ''), self.rule)):
            with self.assertRaises(ValueError): restore(text, source, rule, self.info)

    def test_other_actor_quest_branch_or_ending_changes_fail_before_adaptation(self):
        for added in ('{cmd:7F09000001}', '{cmd:7F19}', '{cmd:7F0F}', '{cmd:7F0D}'):
            with self.assertRaises(ValueError):
                restore(self.text+added, self.source, self.rule, self.info)
        with self.assertRaises(ValueError):
            restore(self.text.replace('{cmd:7F19}', ''), self.source, self.rule, self.info)

    def test_full_source_reference_output_hashes_and_combination_guards(self):
        reference = {'id': 'message:0000', 'text': self.text,
                     'sha256': sha256(encode(self.text, self.info))}
        output = encode(restore(self.text, self.source, self.rule, self.info)[0], self.info)
        record = {'id': reference['id'], 'reference_id': reference['id'],
                  'source_sha256': sha256(self.source), 'reference_sha256': reference['sha256'],
                  'complete_reference': {'adapted_sha256': sha256(output), 'native_random': self.rule}}
        self.assertEqual(encode(adapt_content_reference(reference, self.source, record, self.info)[0], self.info), output)
        validate_content_candidate(record['id'], self.source, output, {record['id']: record})
        for changed in (output+b' ', output[:-1]):
            with self.assertRaises(ValueError):
                validate_content_candidate(record['id'], self.source, changed, {record['id']: record})
        for changed in ({**reference, 'text': self.text+'!'}, {**reference, 'id': 'message:0001'}):
            with self.assertRaises(ValueError): adapt_content_reference(changed, self.source, record, self.info)
        for key in ('spans', 'native_mood', 'omit_startup_storage_location'):
            changed = deepcopy(record); changed['complete_reference'][key] = {}
            with self.assertRaises(ValueError): validate_content_approval(changed)
        with self.assertRaises(ValueError): validate_content_approval({**record, 'reference_id': 'message:0001'})


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Supplied native/English ROM data stays local')
class RandomReferenceRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.references = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.matches = load_matches(ROOT/'translations/reference_matches.json')

    def test_every_complete_reference_retains_native_routes_and_all_english(self):
        records = [r for r in self.matches.values() if 'native_random' in r.get('complete_reference', {})]
        self.assertEqual([r['id'][8:] for r in records], list(IDS))
        for record, bound in zip(records, BOUNDS):
            source = self.sources[int(record['id'][8:], 16)]; reference = self.references[record['reference_id']]
            rule = record['complete_reference']['native_random']
            text, _ = adapt_content_reference(reference, source, record, self.info)
            self.assertEqual(text, reference['text'].replace('{cmd:'+rule['reference_command']+'}',
                                                            '{cmd:'+rule['native_command']+'}', 1))
            final, _ = adapt_reference(text, source, self.info, 'reference_layout', True)
            self.assertEqual(final, text)
            output = encode(final, self.info)
            validate_content_candidate(record['id'], source, output, self.matches)
            for resident in (False, True):
                validate_entry(source, output, self.info, 'message', 'reference_layout', resident_runtime=resident)
            self.assertEqual(expanded_bound(output, self.info), bound)
            controls = lambda data: [t.data for t in tokenize(data, self.info)
                                     if t.kind == 'cmd' and 8 <= t.data[1] <= 0x19]
            self.assertEqual(controls(source), controls(output))

    def test_builder_independently_rejects_changed_output_without_metadata(self):
        from build import apply_translations
        record = self.matches['message:263E']
        edit = {'id': record['id'], 'source_sha256': record['source_sha256'],
                'translation': 'Changed{cmd:7F01}', 'control_policy': 'reference_layout'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'; path.write_text(json.dumps([edit]))
            with self.assertRaisesRegex(ValueError, 'reviewed payload'):
                apply_translations(self.rom, {}, path)
