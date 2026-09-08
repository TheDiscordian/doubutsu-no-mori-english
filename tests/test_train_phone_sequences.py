"""Complete train phone scripts preserve pacing and native cancellation state."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, CODE_RAM, CODE_VROM, sha256, verified_rom
from code_sections import code_segments
from reference_sequences import (commands, load_sequences, message_targets, reference_payloads,
                                 reference_sequence_edits, validate_sequences)
from runtime_module import module_command_info
from sequence_test_scenario import TRAIN_PHONE_GROUPS
from textbanks import banks
from textcodec import encode
from textvalidate import expanded_bound, validate_entry
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Supplied native/English ROM data stays local')
class TrainPhoneRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.refs = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.groups = {n: load_sequences()[n] for n in TRAIN_PHONE_GROUPS}
        cls.edits, cls.permits = reference_sequence_edits(cls.refs, cls.source, cls.info, cls.groups,
                                                        resident_runtime=True)

    def test_complete_references_cuts_and_capacity(self):
        for group, root, cut, full_bound, bounds in zip(self.groups.values(), ('2AD0','2ADE'),
                (460, 471), (1235, 1259), ((513, 740), (494, 783))):
            full = encode(self.refs['message:'+root]['text'], self.info)
            parts = reference_payloads(group, self.refs, self.info)
            self.assertEqual(expanded_bound(full, self.info), full_bound)
            self.assertEqual([expanded_bound(p, self.info) for p in parts], list(bounds))
            self.assertEqual([m['reference_slice'] for m in group['members']], [[0, cut], [cut+5, len(full)]])
            self.assertEqual(full[cut:cut+5], bytes.fromhex('7F04CD7F02'))
            self.assertEqual(parts[0][:-7]+full[cut:cut+5]+parts[1], full)
            for member, raw in zip(group['members'], parts):
                self.assertEqual(sha256(raw), member['encoded_sha256'])
                validate_entry(self.source[int(member['id'][8:], 16)], raw, self.info,
                    'message', 'reviewed_sequence', resident_runtime=True,
                    sequence_permit=self.permits[member['id']])

    def test_protected_intro_and_native_cancel_voice_order(self):
        for group in self.groups.values():
            first, last = reference_payloads(group, self.refs, self.info)
            first_commands = commands(first, self.info); last_commands = commands(last, self.info)
            self.assertEqual([c for c in first_commands if c[1] in (0x72, 0x73, 6, 7, 0x51)],
                [bytes.fromhex(c) for c in ('7F72','7F5100','7F5101','7F73','7F06')])
            self.assertEqual([c for c in last_commands if c[1] in (0x72, 0x73, 6, 7, 0x51)],
                             [b'\x7f\x07'])
            self.assertTrue(first.endswith(b'\xcd\x7f\x01'))
            self.assertTrue(last.endswith(b'\x7f\x00'))
            self.assertNotIn('actor_sources', group)

    def test_basic_omits_whole_groups_and_partial_or_stale_requests_fail(self):
        self.assertEqual(reference_sequence_edits(self.refs, self.source, self.info, self.groups), ([], {}))
        with self.assertRaisesRegex(ValueError, 'resident runtime'):
            validate_sequences(self.edits, self.source, self.info, self.groups)
        for group in self.groups.values():
            selected = [e for e in self.edits if e['reference_sequence'] == group['id']]
            with self.assertRaisesRegex(ValueError, 'Partial'):
                validate_sequences(selected[:1], self.source, self.info, self.groups, resident_runtime=True)
            stale = deepcopy(group); stale['members'][-1]['source_sha256'] = '0'*64
            with self.assertRaisesRegex(ValueError, 'source'):
                validate_sequences(selected, self.source, self.info, {group['id']: stale}, resident_runtime=True)
            selected = deepcopy(selected); selected[-1]['translation'] += 'Changed'
            with self.assertRaisesRegex(ValueError, 'translated bytes changed'):
                validate_sequences(selected, self.source, self.info, self.groups, resident_runtime=True)

    def test_reserves_have_no_native_script_code_or_data_reference(self):
        slots = {0x07DA, 0x2B1B}
        self.assertEqual({int(g['members'][1]['id'][8:],16) for g in self.groups.values()}, slots)
        for number in slots:
            self.assertEqual(self.source[number], encode('よび\n{cmd:7F00}', self.info))
        self.assertFalse(slots & {n for raw in self.source for n in message_targets(raw, self.info)})
        files = by_vrom(self.rom); hits = []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files: continue
            data = files[vrom].extract(self.rom)
            for offset in range(0, len(data)-3, 4):
                word = int.from_bytes(data[offset:offset+4], 'big')
                if segment.is_text(offset) and word & 0xFFFF in slots and word >> 26 in range(8,15):
                    hits.append((segment.name, offset))
            for offset in range(0, len(data)-1, 2):
                if not segment.is_text(offset) and int.from_bytes(data[offset:offset+2], 'big') in slots:
                    hits.append((segment.name, offset))
        self.assertEqual(hits, [])

    def test_actual_native_message_change_and_cancel_handlers_are_pinned(self):
        code = by_vrom(self.rom)[CODE_VROM].extract(self.rom)
        for start, end, digest in (
                (0x8009E658, 0x8009E6B8, '07a8d7b9126da0520717ee86468f4b230b7a823d2b02bf93ff2af6516dc9185c'),
                (0x8009E344, 0x8009E374, '4fe183363fb34b26fc1b128c18d7e2407f40734b62bc6031a17e4c3d33b84831'),
                (0x8009E374, 0x8009E388, '0a9a5025eeade42104ff89eed845b1f63fa886e6b51b6d7cd22a9e526fa5d513'),
                (0x800A0864, 0x800A08B0, '7c080c1757fb36a2f181d204231ae310fb44e193b0b418ba493ef249191217f9'),
                (0x800A08B0, 0x800A08F8, '90b182bfd0bc0aa8704b429f286d6dcaf18d40a39ea237fedd6d9e5bd3adb49d')):
            self.assertEqual(sha256(code[start-CODE_RAM:end-CODE_RAM]), digest)
        # Normal-page setup clears the current cancel, not cancellation-enabled.
        self.assertEqual(code[0x800A0540-CODE_RAM:0x800A054C-CODE_RAM], bytes.fromhex('AC8002BC03E0000800000000'))


if __name__ == '__main__':
    unittest.main()
