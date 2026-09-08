"""Complete special dialogue keeps native actions, cues, and timed endings."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, verified_rom, CODE_RAM, CODE_VROM
from code_sections import code_segments
from reference_sequences import (audit_sequence, commands, load_sequences, message_targets,
                                 reference_payloads, reference_sequence_edits, validate_sequences)
from runtime_module import module_command_info
from sequence_test_scenario import RESETTI_GULLIVER_GROUPS
from textbanks import banks
from textcodec import encode
from textvalidate import expanded_bound, validate_entry
from test_retail import ROM_PATH

ROOT_IDS = '1B3B 1B41 2362 23E8 2511 23FF'.split()
BOUNDS = ([896], [610], [672, 580], [842], [564, 523], [578, 487])
CUTS = {'2362': (619, 624), '2511': (511, 516), '23FF': (555, 560)}


class SoundTimedGuardTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        for code, size in ((3, 3), (9, 5), (0x0E, 4), (0x58, 3), (0x59, 3)):
            self.info[code] = (size, 0)

    def raw(self, text):
        return encode(text, self.info)

    def test_repetition_requires_permission_and_retains_actor_intervals(self):
        source = self.raw('{cmd:7F5905}A{cmd:7F090000FF}{cmd:7F5906}B{cmd:7F00}')
        english = self.raw('{cmd:7F5905}A{cmd:7F5905}\nB{cmd:7F090000FF}{cmd:7F5906}C{cmd:7F00}')
        with self.assertRaises(ValueError): audit_sequence(source, [english], [0], self.info)
        audit_sequence(source, [english], [0], self.info, retain_reference_sound_triggers=True)
        for bad in (english.replace(b'\x7f\x59\x05', b'\x7f\x59\x04', 1),
                    english.replace(b'\x7f\x59\x06', b''),
                    english.replace(b'\x7f\x09\x00\x00\xff\x7f\x59\x06',
                                    b'\x7f\x59\x06\x7f\x09\x00\x00\xff')):
            with self.assertRaises(ValueError):
                audit_sequence(source, [bad], [0], self.info, retain_reference_sound_triggers=True)

    def test_timed_end_is_explicit_exact_and_only_in_last_part(self):
        source = self.raw('Complete{cmd:7F5808}')
        parts = [self.raw('First{cmd:7F0E0001}\n{cmd:7F01}'), self.raw('Last{cmd:7F5808}')]
        with self.assertRaises(ValueError): audit_sequence(source, parts, [0, 1], self.info)
        audit_sequence(source, parts, [0, 1], self.info, timed_end='7F5808')
        for bad in ([parts[0], self.raw('Last{cmd:7F5807}')],
                    [parts[0], self.raw('Last{cmd:7F00}')],
                    [self.raw('Early{cmd:7F5808}')+parts[0], parts[1]]):
            with self.assertRaises(ValueError): audit_sequence(source, bad, [0, 1], self.info, timed_end='7F5808')
        with self.assertRaises(ValueError):
            audit_sequence(source, parts, [0, 1], self.info, timed_end='7F5807')

    def test_permission_schema_rejects_implicit_or_unreviewed_variants(self):
        base = deepcopy(load_sequences()['resetti_bath_farewell_complete'])
        for key, values in (('retain_reference_sound_triggers', (False, 1, 'true', None)),
                            ('timed_end', ('7F5807', '7F00', None))):
            for value in values:
                group = deepcopy(base); group[key] = value
                with patch.object(Path, 'read_text', return_value=json.dumps([group])):
                    with self.assertRaises(ValueError): load_sequences()
        base['source_kind'] = 'native_original'
        with patch.object(Path, 'read_text', return_value=json.dumps([base])):
            with self.assertRaisesRegex(ValueError, 'complete GameCube'):
                load_sequences()


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Supplied native/English inputs remain local')
class ResettiGulliverRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.refs = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.groups = {n: load_sequences()[n] for n in RESETTI_GULLIVER_GROUPS}
        cls.edits, cls.permits = reference_sequence_edits(cls.refs, cls.source, cls.info, cls.groups)

    def test_all_six_references_reconstruct_completely_and_fit(self):
        self.assertEqual([g['members'][0]['id'][8:] for g in self.groups.values()], ROOT_IDS)
        self.assertEqual(len(self.edits), 9)
        for group, bounds in zip(self.groups.values(), BOUNDS):
            number = group['members'][0]['id'][8:]; ref = self.refs['message:'+number]
            full = encode(ref['text'], self.info); parts = reference_payloads(group, self.refs, self.info)
            self.assertEqual(sha256(full), ref['sha256'])
            self.assertEqual([expanded_bound(p, self.info) for p in parts], bounds)
            if number in CUTS:
                begin, end = CUTS[number]
                self.assertEqual(full[begin:end], bytes.fromhex('7F04CD7F02'))
                self.assertEqual(parts[0][:-7]+full[begin:end]+parts[1], full)
            else:
                self.assertEqual(parts, [full])
            self.assertEqual([c for p in parts for c in commands(p, self.info) if c[1] == 0x59],
                             [c for c in commands(full, self.info) if c[1] == 0x59])
            for member, raw in zip(group['members'], parts):
                validate_entry(self.source[int(member['id'][8:], 16)], raw, self.info,
                               'message', 'reviewed_sequence', sequence_permit=self.permits[member['id']])

    def test_native_actions_support_and_timed_endings_are_not_removed(self):
        actions = lambda raw: [c for c in commands(raw, self.info)
                               if 8 <= c[1] <= 12 and c[:3] != b'\x7f\x09\x00']
        for group in self.groups.values():
            source = self.source[int(group['members'][0]['id'][8:], 16)]
            parts = reference_payloads(group, self.refs, self.info)
            self.assertEqual(actions(source), [c for part in parts for c in actions(part)])
            if group.get('timed_end'):
                self.assertTrue(source.endswith(bytes.fromhex('7F5808')))
                self.assertTrue(parts[-1].endswith(bytes.fromhex('7F5808')))
                self.assertEqual(sum(c[1] == 0x58 for p in parts for c in commands(p, self.info)), 1)
            if group.get('retain_reference_sound_triggers'):
                changed = deepcopy(group); del changed['retain_reference_sound_triggers']
                with self.assertRaises(ValueError):
                    reference_sequence_edits(self.refs, self.source, self.info, {changed['id']: changed})
        gulliver = self.groups['gulliver_shipmates_complete']
        self.assertEqual(gulliver['actor_sources'][0]['commands'], ['7F0900000F'])
        changed = deepcopy(gulliver); del changed['actor_sources']
        with self.assertRaisesRegex(ValueError, 'new actor'):
            reference_sequence_edits(self.refs, self.source, self.info, {changed['id']: changed})

    def test_basic_full_parity_and_payload_partial_rejection(self):
        full, _ = reference_sequence_edits(self.refs, self.source, self.info, self.groups, resident_runtime=True)
        self.assertEqual(full, self.edits)
        for group in self.groups.values():
            selected = [e for e in self.edits if e['reference_sequence'] == group['id']]
            if len(selected) > 1:
                with self.assertRaisesRegex(ValueError, 'Partial'):
                    validate_sequences(selected[:1], self.source, self.info, self.groups)
            changed = deepcopy(selected); changed[-1]['translation'] += '!'
            with self.assertRaisesRegex(ValueError, 'translated bytes changed'):
                validate_sequences(changed, self.source, self.info, self.groups)

    def test_reserves_have_no_native_script_code_or_data_hits(self):
        slots = {0x2B42, 0x2B43, 0x2B46}
        for number in slots:
            self.assertEqual(self.source[number], encode('よび\n{cmd:7F00}', self.info))
        self.assertFalse(slots & {n for raw in self.source for n in message_targets(raw, self.info)})
        files = by_vrom(self.rom); hits = []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files: continue
            data = files[vrom].extract(self.rom)
            for off in range(0, len(data)-3, 4):
                word = struct.unpack_from('>I', data, off)[0]
                if segment.is_text(off) and word & 0xFFFF in slots and word >> 26 in (8, 9, 10, 11, 12, 13, 14):
                    hits.append((segment.name, off))
            for off in range(0, len(data)-1, 2):
                if not segment.is_text(off) and int.from_bytes(data[off:off+2], 'big') in slots:
                    hits.append((segment.name, off))
        self.assertEqual(hits, [])

    def test_actual_native_timed_end_and_sound_consumers_are_pinned(self):
        code = by_vrom(self.rom)[CODE_VROM].extract(self.rom)
        for lo, hi, expected in (
                (0x800A1EA0, 0x800A1F1C, '395e37927e32cb473bd34086a0c01d37b977180885ef0fa9d99d0c0abcbde11e'),
                (0x800A1F1C, 0x800A1F7C, '904f9c1dc30f2a8548d425bdf5a631fea50b1581939418bc33471c843dee79aa'),
                (0x8009FC2C, 0x8009FC5C, 'f19a852038be3a2053f02f722fcb88a428ad21d33ac3ef11535617048f812567'),
                (0x8009E144, 0x8009E1A4, '59a2798915a28f7b6ef3c0870129fa2ebc0c3787021fa015b1bf736542772479')):
            self.assertEqual(sha256(code[lo-CODE_RAM:hi-CODE_RAM]), expected)
        self.assertEqual(code[0x80107CA4-CODE_RAM:0x80107CB2-CODE_RAM],
                         bytes.fromhex('1050012E012F0130013104270428'))
        self.assertEqual(code[0x80107CB8+0x58*4-CODE_RAM:0x80107CB8+0x5A*4-CODE_RAM],
                         bytes.fromhex('800A1EA0800A1F1C'))
        self.assertEqual(code[0x800A1EE0-CODE_RAM:0x800A1EE4-CODE_RAM], bytes.fromhex('0003C040'))


if __name__ == '__main__':
    unittest.main()
