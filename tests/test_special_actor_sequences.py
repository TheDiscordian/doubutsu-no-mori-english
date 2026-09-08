"""Full special-actor references retain exact actions and validated continuations."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, verified_rom
from code_sections import code_segments
from reference_sequences import (commands, load_sequences, message_targets, reference_payloads,
                                 reference_sequence_edits, validate_sequences)
from runtime_module import module_command_info
from sequence_test_scenario import SPECIAL_ACTOR_GROUPS
from textbanks import banks
from textcodec import encode
from textvalidate import expanded_bound, validate_entry
from test_retail import ROM_PATH

ROOT_IDS = '0723 0789 078D 07AA 09C8 2401 2402 2403 240B 2ACF 2ADD'.split()
BOUNDS = ([490], [684], [546, 539], [844], [177], [658, 600], [691, 375],
          [942], [264], [472], [517])
CUTS = {'078D': (523, 528), '2401': (635, 640), '2402': (668, 673)}


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Supplied native/English ROM data stays local')
class SpecialActorRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.refs = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.groups = {n: load_sequences()[n] for n in SPECIAL_ACTOR_GROUPS}
        cls.edits, cls.permits = reference_sequence_edits(cls.refs, cls.source, cls.info, cls.groups)

    def test_all_eleven_full_references_reconstruct_without_lost_words_or_presentation(self):
        self.assertEqual([g['members'][0]['id'][8:] for g in self.groups.values()], ROOT_IDS)
        self.assertEqual(len(self.edits), 14)
        for (name, group), bounds in zip(self.groups.items(), BOUNDS):
            number = group['members'][0]['id'][8:]; reference = self.refs['message:'+number]
            full = encode(reference['text'], self.info); parts = reference_payloads(group, self.refs, self.info)
            self.assertEqual(sha256(full), reference['sha256'])
            self.assertEqual([expanded_bound(p, self.info) for p in parts], list(bounds))
            if number in CUTS:
                begin, end = CUTS[number]
                self.assertEqual(full[begin:end], bytes.fromhex('7F04CD7F02'))
                self.assertEqual([m['reference_slice'] for m in group['members']], [[0, begin], [end, len(full)]])
                self.assertEqual(parts[0][:-7]+full[begin:end]+parts[1], full)
            else:
                self.assertEqual(parts, [full])
            for member, raw in zip(group['members'], parts):
                source = self.source[int(member['id'][8:], 16)]
                validate_entry(source, raw, self.info, 'message', 'reviewed_sequence',
                               sequence_permit=self.permits[member['id']])
                self.assertEqual(sha256(raw), member['encoded_sha256'])

    def test_all_existing_sequences_retain_exact_non_expression_requests(self):
        actions = lambda data: [c for c in commands(data, self.info)
                                if 8 <= c[1] <= 12 and c[:3] != b'\x7f\x09\x00']
        for group in load_sequences().values():
            native = self.source[int(group['members'][0]['id'][8:], 16)]
            parts = reference_payloads(group, self.refs, self.info)
            self.assertEqual(actions(native), [c for part in parts for c in actions(part)], group['id'])
        for group in self.groups.values():
            self.assertNotIn('actor_sources', group)
            native = commands(self.source[int(group['members'][0]['id'][8:], 16)], self.info)
            for part in reference_payloads(group, self.refs, self.info):
                self.assertTrue(all(c in native for c in commands(part, self.info) if 8 <= c[1] <= 12))

    def test_three_reserved_slots_have_no_native_script_code_or_data_reference(self):
        slots = {int(g['members'][1]['id'][8:], 16) for g in self.groups.values() if len(g['members']) > 1}
        self.assertEqual(slots, {0x2B02, 0x2B03, 0x2B07})
        for number in slots:
            self.assertEqual(self.source[number], encode('よび\n{cmd:7F00}', self.info))
        self.assertFalse(slots & {n for raw in self.source for n in message_targets(raw, self.info)})
        files = by_vrom(self.rom); hits = []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files: continue
            data = files[vrom].extract(self.rom)
            for offset in range(0, len(data)-3, 4):
                word = struct.unpack_from('>I', data, offset)[0]
                if segment.is_text(offset) and word & 0xFFFF in slots and word >> 26 in (8, 9, 10, 11, 12, 13, 14):
                    hits.append((segment.name, offset))
            for offset in range(0, len(data)-1, 2):
                if not segment.is_text(offset) and int.from_bytes(data[offset:offset+2], 'big') in slots:
                    hits.append((segment.name, offset))
        self.assertEqual(hits, [])

    def test_complete_basic_and_full_parts_are_identical_and_partial_groups_fail(self):
        full, _ = reference_sequence_edits(self.refs, self.source, self.info, self.groups, resident_runtime=True)
        self.assertEqual(full, self.edits)
        for group in self.groups.values():
            if len(group['members']) == 1: continue
            selected = [e for e in self.edits if e['reference_sequence'] == group['id']]
            with self.assertRaisesRegex(ValueError, 'Partial'):
                validate_sequences(selected[:1], self.source, self.info, self.groups)
            selected = deepcopy(selected); selected[-1]['translation'] += 'Changed'
            with self.assertRaisesRegex(ValueError, 'translated bytes changed'):
                validate_sequences(selected, self.source, self.info, self.groups)

    def test_native_external_links_sound_actions_and_gulliver_endings_remain(self):
        parts = {g['members'][0]['id'][8:]: reference_payloads(g, self.refs, self.info) for g in self.groups.values()}
        self.assertTrue(parts['0723'][-1].endswith(bytes.fromhex('7F0E072ACD7F01')))
        self.assertTrue(parts['09C8'][-1].endswith(bytes.fromhex('7F0E09CACD7F01')))
        sound = commands(parts['09C8'][0], self.info)
        for raw in ('7F17007400750076', '7F0D', '7F09090001', '7F090000FD', '7F2E'):
            self.assertIn(bytes.fromhex(raw), sound)
        for number in ('2401', '2402', '2403'):
            self.assertTrue(parts[number][-1].endswith(b'\x7f\x01'))
        for number in ('0789', '078D', '07AA', '240B', '2ACF', '2ADD'):
            self.assertTrue(parts[number][-1].endswith(b'\x7f\x00'))


if __name__ == '__main__':
    unittest.main()
