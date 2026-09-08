"""Complete references permit audited wording, not extra fields or game actions."""

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
from reference_content import (adapt_content_reference, validate_content_approval,
                               validate_content_candidate, verify_content_reference)
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry
from test_retail import ROM_PATH

IDS = set('050B 0670 08BF 0963 0ADE 0AE8 0B91 0B9E 1124 1126 118E 118F '
          '119A 11A5 11A7 11B0 13FC 1400 1406 1424 1428 142E 144C 1450 1456 '
          '1474 1478 147E 149C 14A0 14A6 14C4 14C8 14CE 14DB 16A4 16A5 '
          '1749 174D 17AF 17B5 17ED 17EE 17FA 20A8 20B0 2360 23E6 26EE '
          '26EF 26F8 26F9 2705 27B2 27BA 27BE 27E6 2806 2807 2812 287D '
          '2AE7 2AE8 2B69 2BC3 2BC5 2BC7 2BC9'.split())


class ContentApprovalTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[3], self.info[9], self.info[0x50] = (3, 0), (5, 0), (6, 0)
        self.source = encode('Native{cmd:7F00}', self.info)
        self.reference = {'id': 'message:0000', 'text': 'Visit the {cmd:7F504BA0000C}wishing well!{cmd:7F00}'}
        self.reference['sha256'] = sha256(encode(self.reference['text'], self.info))
        self.output = encode('Visit the {cmd:7F504BA00006}shrine!{cmd:7F00}', self.info)
        self.record = {'id': 'message:0000', 'reference_id': self.reference['id'],
                       'source_sha256': sha256(self.source), 'reference_sha256': self.reference['sha256'],
                       'complete_reference': {'adapted_sha256': sha256(self.output), 'spans': [
                           {'offset': 10, 'before': '{cmd:7F504BA0000C}wishing well',
                            'after': '{cmd:7F504BA00006}shrine'}]}}

    def adapt(self, record=None, reference=None):
        return adapt_content_reference(reference or self.reference, self.source, record or self.record, self.info)

    def test_only_explicit_span_changes_and_complete_output_is_bound(self):
        text, changes = self.adapt()
        self.assertEqual(encode(text, self.info), self.output)
        self.assertEqual(changes[0]['operation'], 'reviewed_native_wording_span')
        validate_content_candidate(self.record['id'], self.source, self.output, {self.record['id']: self.record})
        for source, output in ((b'wrong', self.output), (self.source, b'wrong')):
            with self.assertRaisesRegex(ValueError, 'reviewed payload'):
                validate_content_candidate(self.record['id'], source, output, {self.record['id']: self.record})

    def test_plain_complete_binding_changes_no_text(self):
        record = deepcopy(self.record)
        del record['complete_reference']['spans']
        self.assertEqual(self.adapt(record), (self.reference['text'], []))
        self.assertEqual(adapt_content_reference(self.reference, self.source, None, self.info),
                         (self.reference['text'], []))

    def test_complete_reference_hash_and_native_hash_are_checked(self):
        for reference in ({**self.reference, 'text': 'Changed{cmd:7F00}'},
                          {**self.reference, 'id': 'message:0001'},
                          {**self.reference, 'sha256': '0'*64}):
            with self.assertRaisesRegex(ValueError, 'Stale'): self.adapt(reference=reference)
        with self.assertRaisesRegex(ValueError, 'Stale'):
            verify_content_reference(self.reference, b'wrong', self.record, self.info)

    def test_schema_rejects_malformed_or_combined_permissions(self):
        for key in ('controller', 'native_choices', 'native_actor_request', 'available_fields',
                    'speaker_catchphrase', 'native_equivalent_id', 'resident_animations'):
            with self.assertRaisesRegex(ValueError, 'approval'):
                validate_content_approval({**self.record, key: {}})
        for update in ({'adapted_sha256': '0'}, {'extra': True}, {'spans': []},
                       {'spans': [{}]}, {'spans': [{'offset': True, 'before': 'A', 'after': 'B'}]}):
            record = deepcopy(self.record); record['complete_reference'].update(update)
            with self.assertRaises(ValueError): validate_content_approval(record)

    def test_spans_cannot_overlap_or_miss_their_original_position(self):
        for spans in ([{**self.record['complete_reference']['spans'][0], 'offset': 11}],
                      self.record['complete_reference']['spans']*2):
            record = deepcopy(self.record); record['complete_reference']['spans'] = spans
            with self.assertRaisesRegex(ValueError, 'span does not match'): self.adapt(record)

    def test_wording_cannot_add_controls_or_move_pauses_across_lines(self):
        for command in ('{cmd:7F1A}', '{cmd:7F09000001}', '{cmd:7F02}', '{cmd:7F0308}', '\n'):
            record = deepcopy(self.record)
            record['complete_reference']['spans'][0]['after'] += command
            with self.assertRaisesRegex(ValueError, 'changes delivery'): self.adapt(record)
        reference = {**self.reference, 'text': 'A{cmd:7F0308}\nB{cmd:7F00}'}
        reference['sha256'] = sha256(encode(reference['text'], self.info))
        record = deepcopy(self.record); record['reference_sha256'] = reference['sha256']
        record['complete_reference']['spans'] = [
            {'offset': 0, 'before': 'A{cmd:7F0308}\nB', 'after': 'A\n{cmd:7F0308}B'}]
        with self.assertRaisesRegex(ValueError, 'changes delivery'): self.adapt(record, reference)


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM stays local')
class RetailContentApprovalTests(unittest.TestCase):
    def test_every_complete_reference_preserves_full_delivery_and_native_controls(self):
        rom = verified_rom(ROM_PATH.read_bytes()); info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == 'message').entries()
        path = ROOT/'build/gamecube/text/message.jsonl'
        if not path.is_file(): self.skipTest('English disc extraction stays local')
        gc = {r['id']: r for r in map(json.loads, path.read_text().splitlines())}
        matches = load_matches(ROOT/'translations/reference_matches.json')
        approved = [r for r in matches.values() if 'complete_reference' in r
                    and not r['complete_reference'].get('omit_startup_storage_location')
                    and not r['complete_reference'].get('native_mood')]
        self.assertEqual({r['id'][8:] for r in approved}, IDS)
        changed = 0
        for record in approved:
            source = sources[int(record['id'][8:], 16)]; reference = gc[record['reference_id']]
            text, edits = adapt_content_reference(reference, source, record, info)
            changed += bool(edits)
            final, changes = adapt_reference(text, source, info, 'reference_layout', True)
            self.assertEqual(final, text, record['id'])
            output = encode(final, info)
            validate_content_candidate(record['id'], source, output, matches)
            validate_entry(source, output, info, 'message', 'reference_layout', resident_runtime=True)
            delivery = lambda raw: [t.data for t in tokenize(raw, info)
                                    if (t.kind == 'cmd' and t.data[1] != 0x50) or t.data == b'\xcd']
            self.assertEqual(delivery(output), delivery(encode(reference['text'], info)), record['id'])
            self.assertNotIn('wishing well', text.lower().replace('\n', ' '), record['id'])
            self.assertNotIn('Memory Card', text, record['id'])
            self.assertNotIn('Nintendo GameCube', text, record['id'])
        self.assertEqual(changed, 52)

    def test_builder_rejects_changed_complete_text_without_trusting_edit_metadata(self):
        from build import apply_translations
        record = load_matches(ROOT/'translations/reference_matches.json')['message:050B']
        edit = {'id': record['id'], 'source_sha256': record['source_sha256'],
                'translation': 'Changed{cmd:7F00}', 'control_policy': 'reference_layout'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'; path.write_text(json.dumps([edit]))
            with self.assertRaisesRegex(ValueError, 'reviewed payload'):
                apply_translations(ROM_PATH.read_bytes(), {}, path)
