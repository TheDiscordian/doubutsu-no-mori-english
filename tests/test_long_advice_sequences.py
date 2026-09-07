"""Full English advice fits through approved pages without losing controls."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, verified_rom
from code_sections import code_segments
from reference_sequences import (audit_sequence, commands, load_sequences,
                                 reference_payloads, reference_sequence_edits, validate_sequences)
from runtime_module import module_command_info
from sequence_test_scenario import batch_scenario, LONG_ADVICE_GROUPS
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import expanded_bound, validate_entry
from test_retail import ROM_PATH


class SequencePresentationTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x76
        self.info[0x0E] = (4, 0)
        self.info[0x74] = (0, 0)
        self.raw_info = list(self.info)
        self.raw_info[0x74] = (2, 0)
        self.text = 'First{cmd:7F04}\n{cmd:7F02}The {cmd:7F74}{cmd:7F31}{cmd:7F00}'
        digest = sha256(encode(self.text, self.raw_info))
        self.refs = {'message:0000': {'text': self.text, 'sha256': digest}}
        self.group = {'id': 'article_test', 'evidence': 'Synthetic source binding', 'members': [
            {'id': 'message:0000', 'reference_id': 'message:0000', 'reference_sha256': digest,
             'source_sha256': '0'*64, 'encoded_sha256': '0'*64,
             'remove_redundant_cutarticle': True, 'reference_slice': [0, 5]},
            {'id': 'message:0001', 'reference_id': 'message:0000', 'reference_sha256': digest,
             'source_sha256': '0'*64, 'encoded_sha256': '0'*64,
             'remove_redundant_cutarticle': True, 'reference_slice': [10, 18]}]}

    def test_article_removal_preserves_complete_wording_and_page_boundary(self):
        parts = reference_payloads(self.group, self.refs, self.info)
        self.assertEqual(parts, [b'First\x7f\x0e\x00\x01\xcd\x7f\x01',
                                 encode('The {cmd:7F31}{cmd:7F00}', self.info)])
        whole = encode(self.text.replace('{cmd:7F74}', ''), self.info)
        self.assertEqual(parts[0][:-7]+bytes.fromhex('7F04CD7F02')+parts[1], whole)
        audit_sequence(b'Native\x7f\x31\x7f\x00', parts, [0, 1], self.info)
        with self.assertRaisesRegex(ValueError, 'unavailable text field'):
            audit_sequence(b'Native\x7f\x00', parts, [0, 1], self.info)

    def test_article_removal_requires_exact_source_and_actual_adjacent_string(self):
        stale = deepcopy(self.refs)
        stale['message:0000']['text'] = self.text.replace('First', 'Other')
        with self.assertRaisesRegex(ValueError, 'exact complete'):
            reference_payloads(self.group, stale, self.info)
        for text in (self.text.replace('{cmd:7F74}', ''),
                     self.text.replace('{cmd:7F74}{cmd:7F31}', '{cmd:7F74}not a field'),
                     self.text.replace('{cmd:7F31}', '{cmd:7F0E0002}')):
            refs, group = deepcopy(self.refs), deepcopy(self.group)
            digest = sha256(encode(text, self.raw_info))
            refs['message:0000'].update(text=text, sha256=digest)
            for member in group['members']: member['reference_sha256'] = digest
            with self.assertRaisesRegex(ValueError, 'requires a redundant CUTARTICLE'):
                reference_payloads(group, refs, self.info)
        group = deepcopy(self.group)
        group['members'][1]['remove_redundant_cutarticle'] = False
        with self.assertRaisesRegex(ValueError, 'Unsupported command'):
            reference_payloads(group, self.refs, self.info)

    def test_article_schema_rejects_truthy_non_boolean(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'sequences.json'
            path.write_text(json.dumps([self.group]))
            self.assertIn('article_test', load_sequences(path))
            for value in ('true', 1, [], None):
                group = deepcopy(self.group)
                group['members'][0]['remove_redundant_cutarticle'] = value
                path.write_text(json.dumps([group]))
                with self.assertRaisesRegex(ValueError, 'article-suppression'):
                    load_sequences(path)
                with self.assertRaisesRegex(ValueError, 'article-suppression'):
                    reference_payloads(group, self.refs, self.info)

    def test_capitalization_requires_runtime_and_does_not_admit_other_controls(self):
        native = b'Native\x7f\x1c\x7f\x00'
        parts = [b'First\x7f\x0e\x00\x01\xcd\x7f\x01', b'Last\x7f\x75\x7f\x1c\x7f\x00']
        audit_sequence(native, parts, [0, 1], self.info, resident_runtime=True)
        with self.assertRaisesRegex(ValueError, 'gameplay commands changed'):
            audit_sequence(native, parts, [0, 1], self.info)
        for command in (0x30, 0x56, 0x57, 0x72, 0x73):
            altered = [parts[0], parts[1].replace(b'\x7f\x75', bytes([0x7F, command]))]
            with self.assertRaisesRegex(ValueError, 'gameplay commands changed'):
                audit_sequence(native, altered, [0, 1], self.info, resident_runtime=True)

    def test_batch_uses_one_checkpoint_and_retains_every_group_body(self):
        prefix = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]
        suffix = [{'read': ['8019C8D0', 16], 'expect': 'AF32C0DE'*4},
                  {'load_state': True}, {'resume': True}, {'wait': 2},
                  {'read': ['8019B000', 4], 'expect': '00000000'}]
        def fixture(rom, name, module): return prefix+[{'group_test_body': name}]+suffix
        with patch('sequence_test_scenario.scenario', side_effect=fixture):
            result = batch_scenario(b'', list(LONG_ADVICE_GROUPS))
        self.assertEqual(result, prefix+[{'group_test_body': n} for n in LONG_ADVICE_GROUPS]+suffix)
        for names in ([], ['a', 'a']):
            with self.assertRaisesRegex(ValueError, 'distinct'):
                batch_scenario(b'', names)
        with patch('sequence_test_scenario.scenario', side_effect=[fixture(b'', 'a', None),
                   [{'wait': 9}]+fixture(b'', 'b', None)[1:]]):
            with self.assertRaisesRegex(ValueError, 'restoration differs'):
                batch_scenario(b'', ['a', 'b'])


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Retail ROM and supplied English extraction remain local-only')
class LongAdviceRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.refs = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.groups = {n: load_sequences()[n] for n in LONG_ADVICE_GROUPS}
        cls.edits, cls.permits = reference_sequence_edits(cls.refs, cls.source, cls.info,
                                                         cls.groups, resident_runtime=True)

    def test_every_full_reference_is_reconstructed_at_its_existing_page(self):
        expected = [(1049, [155, 912]), (1031, [535, 514]), (1259, [623, 654]),
                    (1053, [667, 404]), (1079, [541, 556])]
        for (name, group), (bound, part_bounds) in zip(self.groups.items(), expected):
            parts = reference_payloads(group, self.refs, self.info)
            root = group['members'][0]['id']
            text = self.refs[root]['text']
            if root == 'message:08FA':
                self.assertEqual(text.count('{cmd:7F74}{cmd:7F31}'), 1)
                text = text.replace('{cmd:7F74}{cmd:7F31}', '{cmd:7F31}')
            whole = encode(text, self.info)
            self.assertEqual(expanded_bound(whole, self.info), bound, name)
            self.assertEqual([expanded_bound(p, self.info) for p in parts], part_bounds, name)
            self.assertEqual(parts[0][:-7]+bytes.fromhex('7F04CD7F02')+parts[1], whole, name)
            for member, payload in zip(group['members'], parts):
                native = self.source[int(member['id'][8:], 16)]
                validate_entry(native, payload, self.info, 'message', 'reviewed_sequence',
                               resident_runtime=True, sequence_permit=self.permits[member['id']])
                self.assertEqual(sha256(payload), member['encoded_sha256'])

    def test_basic_generation_withholds_both_capitalization_sequence_members(self):
        edits, _ = reference_sequence_edits(self.refs, self.source, self.info, self.groups)
        self.assertEqual(len(edits), 8)
        self.assertFalse({'message:0910', 'message:0A26'} & {e['id'] for e in edits})
        with self.assertRaisesRegex(ValueError, 'requires the resident runtime'):
            validate_sequences(self.edits, self.source, self.info, self.groups)
        for group in self.groups.values():
            partial = [e for e in self.edits if e['id'] == group['members'][0]['id']]
            with self.assertRaisesRegex(ValueError, 'Partial'):
                validate_sequences(partial, self.source, self.info, self.groups, resident_runtime=True)

    def test_phone_mode_and_external_link_remain_whole(self):
        parts = reference_payloads(self.groups['rover_repeat_phone'], self.refs, self.info)
        self.assertFalse(any(c[1] in (6, 7) for c in commands(parts[0], self.info)))
        self.assertEqual([c[1] for c in commands(parts[1], self.info) if c[1] in (6, 7)], [6, 7])
        self.assertTrue(parts[1].endswith(bytes.fromhex('7F0E046FCD7F01')))
        letters = reference_payloads(self.groups['resident_cranky_letter_advice'], self.refs, self.info)
        self.assertNotIn(bytes.fromhex('7F75'), letters[0])
        self.assertEqual(letters[1].count(bytes.fromhex('7F757F1C')), 1)

    def test_five_reserved_slots_have_no_native_immediate_or_data_references(self):
        slots = {int(g['members'][1]['id'][8:], 16) for g in self.groups.values()}
        self.assertEqual(slots, {0x0486, 0x0921, 0x2B05, 0x2B06, 0x0A26})
        for number in slots:
            tokens = list(tokenize(self.source[number], self.info))
            self.assertEqual([t.data for t in tokens if t.kind == 'cmd'], [bytes.fromhex('7F00')])
        files = by_vrom(self.rom); hits = []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files: continue
            data = files[vrom].extract(self.rom)
            for offset in range(0, len(data)-3, 4):
                word = struct.unpack_from('>I', data, offset)[0]
                if (segment.is_text(offset) and word & 0xFFFF in slots
                        and word >> 26 in (8, 9, 10, 11, 12, 13, 14)):
                    hits.append((segment.name, segment.ram+offset, word))
            for offset in range(0, len(data)-1, 2):
                if not segment.is_text(offset) and int.from_bytes(data[offset:offset+2], 'big') in slots:
                    hits.append((segment.name, segment.ram+offset))
        self.assertEqual(hits, [])


if __name__ == '__main__':
    unittest.main()
