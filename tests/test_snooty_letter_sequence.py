"""The complete long letter explanation retains reference presentation."""

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
from reference_animations import verify_native_consumer
from reference_sequences import (commands, load_sequences, message_targets,
                                 reference_payloads, reference_sequence_edits, validate_sequences)
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode
from textvalidate import expanded_bound, validate_entry
from test_retail import ROM_PATH

GROUP = 'resident_snooty_letter_advice'


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Supplied native and English data remains local')
class SnootyLetterRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.refs = {r['id']: r for r in map(json.loads,
            (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.group = load_sequences()[GROUP]
        cls.edits, cls.permits = reference_sequence_edits(cls.refs, cls.source, cls.info, {GROUP: cls.group})

    def test_complete_reference_reconstruction_bounds_and_original_punctuation(self):
        ref = self.refs['message:0912']; whole = encode(ref['text'], self.info)
        parts = reference_payloads(self.group, self.refs, self.info)
        self.assertEqual(sha256(whole), ref['sha256'])
        self.assertEqual(len(whole), 1226)
        self.assertEqual(expanded_bound(whole, self.info), 1362)
        self.assertEqual([m['id'] for m in self.group['members']], ['message:0912', 'message:2B47'])
        self.assertEqual(whole[659:664], bytes.fromhex('7F04CD7F02'))
        self.assertEqual(parts[0][-7:], bytes.fromhex('7F0E2B47CD7F01'))
        self.assertEqual(parts[0][:-7]+whole[659:664]+parts[1], whole)
        self.assertEqual([len(p) for p in parts], [666, 562])
        self.assertEqual([expanded_bound(p, self.info) for p in parts], [742, 638])
        self.assertEqual(sum(p.count(b'\x90') for p in parts), whole.count(b'\x90'))
        for edit, raw in zip(self.edits, parts):
            validate_entry(self.source[int(edit['id'][8:], 16)], raw, self.info,
                           'message', 'reviewed_sequence', sequence_permit=self.permits[edit['id']])

    def test_only_supported_standing_expression_is_added_and_native_actions_remain(self):
        verify_native_consumer(self.rom)
        self.assertEqual(self.group['actor_sources'], [{'id': 'message:0541',
            'source_sha256': sha256(self.source[0x0541]), 'commands': ['7F09000013']}])
        native = commands(self.source[0x0912], self.info)
        translated = [c for p in reference_payloads(self.group, self.refs, self.info)
                      for c in commands(p, self.info)]
        self.assertEqual({c for c in translated if 8 <= c[1] <= 12}-set(native),
                         {bytes.fromhex('7F09000013')})
        actions = lambda stream: [c for c in stream if 8 <= c[1] <= 12 and c[:3] != b'\x7f\x09\x00']
        self.assertEqual(actions(native), actions(translated))
        self.assertEqual([c for c in translated if 0x1A <= c[1] <= 0x3F], [b'\x7f\x1c']*4)
        for change in ('missing', 'stale', 'wrong_command'):
            group = deepcopy(self.group)
            if change == 'missing': del group['actor_sources']
            elif change == 'stale': group['actor_sources'][0]['source_sha256'] = '0'*64
            else: group['actor_sources'][0]['commands'] = ['7F09090001']
            with self.assertRaises(ValueError):
                validate_sequences(self.edits, self.source, self.info, {GROUP: group})

    def test_basic_full_parity_and_partial_or_changed_parts_fail(self):
        full, _ = reference_sequence_edits(self.refs, self.source, self.info,
                                           {GROUP: self.group}, resident_runtime=True)
        self.assertEqual(full, self.edits)
        for position in (0, 1):
            with self.assertRaisesRegex(ValueError, 'Partial'):
                validate_sequences([self.edits[position]], self.source, self.info, {GROUP: self.group})
            changed = deepcopy(self.edits); changed[position]['translation'] += '!'
            with self.assertRaisesRegex(ValueError, 'translated bytes changed'):
                validate_sequences(changed, self.source, self.info, {GROUP: self.group})
        refs = deepcopy(self.refs); refs['message:0912']['text'] += '!'
        with self.assertRaisesRegex(ValueError, 'exact complete'):
            reference_sequence_edits(refs, self.source, self.info, {GROUP: self.group})

    def test_reserve_has_no_native_script_code_or_data_hits(self):
        slot = 0x2B47
        self.assertEqual(self.source[slot], encode('よび\n{cmd:7F00}', self.info))
        self.assertNotIn(slot, {n for raw in self.source for n in message_targets(raw, self.info)})
        files = by_vrom(self.rom); hits = []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files: continue
            data = files[vrom].extract(self.rom)
            for off in range(0, len(data)-3, 4):
                word = struct.unpack_from('>I', data, off)[0]
                if segment.is_text(off) and word & 0xFFFF == slot and word >> 26 in (8, 9, 10, 11, 12, 13, 14):
                    hits.append((segment.name, off, 'code'))
            for off in range(0, len(data)-1, 2):
                if not segment.is_text(off) and int.from_bytes(data[off:off+2], 'big') == slot:
                    hits.append((segment.name, off, 'data'))
        self.assertEqual(hits, [])


if __name__ == '__main__':
    unittest.main()
