"""Complete character dialogue admits only individually supported expressions."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from reference_sequences import (commands, load_sequences, reference_payloads,
                                 reference_sequence_edits, validate_sequences)
from runtime_module import module_command_info
from sequence_test_scenario import CONTEXTUAL_ACTOR_GROUPS
from textbanks import banks
from textcodec import encode
from textvalidate import expanded_bound, validate_entry
from test_retail import ROM_PATH

IDENTITIES = ('0785', '240A', '240D', '2AC9', '2AD4')
SUPPORT = (('0786', ('17',)), ('240E', ('17',)), ('240E', ('17',)),
           ('2AD2', ('1D', 'FE')), ('2ACD', ('1F',)))


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Supplied native/English ROM data stays local')
class ContextualActorRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.refs = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.groups = {n: load_sequences()[n] for n in CONTEXTUAL_ACTOR_GROUPS}
        cls.edits, cls.permits = reference_sequence_edits(cls.refs, cls.source, cls.info, cls.groups)

    def test_all_five_complete_references_and_bounds(self):
        self.assertEqual([e['id'][8:] for e in self.edits], list(IDENTITIES))
        self.assertEqual([expanded_bound(encode(e['translation'], self.info), self.info)
                          for e in self.edits], [211, 479, 487, 237, 444])
        for edit, group in zip(self.edits, self.groups.values()):
            self.assertEqual(len(group['members']), 1)
            raw = encode(edit['translation'], self.info); ref = self.refs[edit['id']]
            self.assertEqual(raw, encode(ref['text'], self.info))
            self.assertEqual(sha256(raw), ref['sha256'])
            native = self.source[int(edit['id'][8:], 16)]
            validate_entry(native, raw, self.info, 'message', 'reviewed_sequence',
                           sequence_permit=self.permits[edit['id']])

    def test_only_exact_same_character_support_is_declared(self):
        for group, (number, expressions) in zip(self.groups.values(), SUPPORT):
            self.assertEqual(group['actor_sources'], [{'id': 'message:'+number,
                'source_sha256': sha256(self.source[int(number, 16)]),
                'commands': ['7F090000'+value for value in expressions]}])
            native = commands(self.source[int(group['members'][0]['id'][8:], 16)], self.info)
            translated = commands(reference_payloads(group, self.refs, self.info)[0], self.info)
            added = {c for c in translated if 8 <= c[1] <= 12}-set(native)
            self.assertEqual(added, {bytes.fromhex('7F090000'+value) for value in expressions})
            self.assertEqual([c for c in native if 8 <= c[1] <= 12 and c[:3] != b'\x7f\x09\x00'],
                             [c for c in translated if 8 <= c[1] <= 12 and c[:3] != b'\x7f\x09\x00'])

    def test_basic_and_full_payloads_match_and_reference_mutations_fail(self):
        full, _ = reference_sequence_edits(self.refs, self.source, self.info, self.groups,
                                           resident_runtime=True)
        self.assertEqual(full, self.edits)
        for group in self.groups.values():
            ref_id = group['members'][0]['id']; refs = deepcopy(self.refs)
            refs[ref_id]['text'] += 'Changed'
            with self.assertRaisesRegex(ValueError, 'exact complete'):
                reference_sequence_edits(refs, self.source, self.info, {group['id']: group})

    def test_support_is_required_and_stale_or_extra_requests_fail(self):
        for name, group in self.groups.items():
            selected = [e for e in self.edits if e['reference_sequence'] == name]
            altered = deepcopy(group); altered.pop('actor_sources')
            with self.assertRaisesRegex(ValueError, 'actor argument'):
                validate_sequences(selected, self.source, self.info, {name: altered})
            altered = deepcopy(group); altered['actor_sources'][0]['source_sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'Stale'):
                validate_sequences(selected, self.source, self.info, {name: altered})
            for command in ('7F09090001', '7F09020001', '7F0C030012'):
                altered = deepcopy(group); altered['actor_sources'][0]['commands'] = [command]
                with self.assertRaisesRegex(ValueError, 'speaker emotion'):
                    validate_sequences(selected, self.source, self.info, {name: altered})

    def test_native_name_entry_and_final_endings_remain(self):
        parts = {e['id'][8:]: encode(e['translation'], self.info) for e in self.edits}
        self.assertEqual([c for c in commands(parts['2AC9'], self.info)
                          if c[:3] != b'\x7f\x09\x00' and c[1] not in (2, 3, 4)],
                         [bytes.fromhex(c) for c in ('7F09090001', '7F55', '7F01')])
        for number, raw in parts.items():
            self.assertEqual(raw[-2:], b'\x7f\x01' if number == '2AC9' else b'\x7f\x00')
        self.assertIn(b'\x7f\x2f', parts['2AD4'])


if __name__ == '__main__':
    unittest.main()
