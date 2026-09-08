"""Complete native travel instructions retain their pages and original controls."""

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
from font import make_halfwidth
from gc_text import plain
from native_sequences import audit_native_translation, native_reference, validate_native_group
from reference_sequences import (commands, load_sequences, message_targets, reference_payloads,
                                 reference_sequence_edits, validate_sequences)
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

GROUP = 'native_normal_travel_advice'
GAP = bytes.fromhex('7F04CD7F02')


class NativeSequenceTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        for code, size in ((3, 3), (9, 5), (14, 4), (80, 6)):
            self.info[code] = (size, 0)
        native = 'あ{cmd:7F0304}{cmd:7F1A}{cmd:7F504BA00002}い{cmd:7F04}\n{cmd:7F02}う{cmd:7F00}'
        self.source = [encode(native, self.info), encode('よび\n{cmd:7F00}', self.info)]
        text = 'Hello{cmd:7F0304}{cmd:7F1A}{cmd:7F504BA00004}Ruby{cmd:7F04}\n{cmd:7F02}Bye{cmd:7F00}'
        self.group = {'id': 'native_test', 'source_kind': 'native_original', 'evidence': 'Synthetic fixture',
                      'original_translation': {'id': 'message:0000', 'text': text, 'sha256': '0'*64},
                      'colour_lengths': [{'command_index': 2, 'original': '7F504BA00002',
                                          'replacement': '7F504BA00004'}],
                      'members': [{'id': f'message:{i:04X}', 'source_sha256': sha256(raw),
                                   'reference_id': 'message:0000', 'reference_sha256': '0'*64,
                                   'reference_slice': [0, 1], 'encoded_sha256': '0'*64}
                                  for i, raw in enumerate(self.source)]}
        self.bind(self.group)

    def bind(self, group):
        whole = encode(group['original_translation']['text'], self.info)
        cut = whole.index(GAP)
        group['original_translation']['sha256'] = sha256(whole)
        for member, span in zip(group['members'], ([0, cut], [cut+5, len(whole)])):
            member['reference_sha256'] = sha256(whole)
            member['reference_slice'] = span
        for member, part in zip(group['members'], reference_payloads(group, {}, self.info)):
            member['encoded_sha256'] = sha256(part)

    def generate(self, group=None, source=None):
        group = self.group if group is None else group
        return reference_sequence_edits({}, self.source if source is None else source,
                                        self.info, {group['id']: group})

    def test_complete_native_source_and_honest_provenance_without_a_disc_reference(self):
        edits, permits = self.generate()
        parts = [encode(e['translation'], self.info) for e in edits]
        self.assertEqual(parts[0][:-7]+GAP+parts[1], encode(self.group['original_translation']['text'], self.info))
        self.assertEqual(len(permits), 2)
        for edit, part, original in zip(edits, parts, self.source):
            self.assertEqual(edit['status'], 'draft')
            self.assertEqual(edit['provenance']['native_id'], 'message:0000')
            self.assertNotIn('reference_id', edit['provenance'])
            self.assertNotIn('disc', edit['provenance']['source'])
            validate_entry(original, part, self.info, 'message', 'reviewed_sequence',
                           sequence_permit=permits[edit['id']])
        donor = {'message:0000': {'text': 'Unrelated disc text', 'sha256': '0'*64}}
        self.assertEqual(reference_payloads(self.group, donor, self.info), parts)

    def test_changed_complete_text_hash_and_member_payload_fail(self):
        group = deepcopy(self.group)
        group['original_translation']['text'] += 'Lost text'
        with self.assertRaisesRegex(ValueError, 'exact complete original'):
            self.generate(group)
        edits, _ = self.generate()
        edits[1]['translation'] = edits[1]['translation'].replace('Bye', 'Short')
        with self.assertRaisesRegex(ValueError, 'translated bytes changed'):
            validate_sequences(edits, self.source, self.info, {self.group['id']: self.group})
        # Re-hashing only the approved part cannot omit text from the full draft.
        group = deepcopy(self.group)
        group['members'][1]['encoded_sha256'] = sha256(encode(edits[1]['translation'], self.info))
        with self.assertRaisesRegex(ValueError, 'reconstruct the complete'):
            validate_sequences(edits, self.source, self.info, {group['id']: group})

    def test_native_commands_are_checked_even_if_all_english_hashes_are_rebound(self):
        text = self.group['original_translation']['text']
        mutations = [text.replace('7F0304', '7F0308'),
                     text.replace('{cmd:7F1A}', '{cmd:7F1C}'),
                     text.replace('Bye', '{cmd:7F09000015}Bye'),
                     text.replace('Bye', '{cmd:7F0E0002}Bye'),
                     text.replace('{cmd:7F1A}', '').replace('Bye', '{cmd:7F1A}Bye'),
                     text.replace('{cmd:7F00}', '{cmd:7F01}')]
        for changed in mutations:
            group = deepcopy(self.group)
            group['original_translation']['text'] = changed
            self.bind(group)
            with self.assertRaisesRegex(ValueError, 'Complete native translation changed'):
                self.generate(group)

    def test_only_explicit_original_colour_lengths_can_change(self):
        for field, value in (('replacement', '7F504BA00104'), ('replacement', '7F504BA00000'),
                             ('replacement', '7F504BA00002'), ('command_index', True),
                             ('command_index', -1)):
            group = deepcopy(self.group); group['colour_lengths'][0][field] = value
            with self.assertRaisesRegex(ValueError, 'Native colour'):
                validate_native_group(group)
        group = deepcopy(self.group); group['colour_lengths'] *= 2
        with self.assertRaisesRegex(ValueError, 'unique indexed'):
            validate_native_group(group)
        for index in (0, 999):
            group = deepcopy(self.group); group['colour_lengths'][0]['command_index'] = index
            with self.assertRaisesRegex(ValueError, 'original command'):
                self.generate(group)
        group = deepcopy(self.group); group['colour_lengths'] = []
        with self.assertRaisesRegex(ValueError, 'Complete native translation changed'):
            self.generate(group)

    def test_original_kind_cannot_borrow_disc_or_actor_permissions(self):
        for kind in ('unknown', 'gamecube'):
            group = deepcopy(self.group); group['source_kind'] = kind
            with self.assertRaises(ValueError): validate_native_group(group)
        for mutate in (lambda g: g.pop('original_translation'),
                       lambda g: g['members'][1].update(reference_id='message:0002'),
                       lambda g: g['members'][1].update(remove_redundant_cutarticle=False),
                       lambda g: g.update(actor_sources=[{'commands': ['7F09000015']}])):
            group = deepcopy(self.group); mutate(group)
            with self.assertRaises(ValueError): validate_native_group(group)

    def test_partial_stale_and_incoming_native_slots_stay_rejected(self):
        edits, _ = self.generate(); groups = {self.group['id']: self.group}
        with self.assertRaisesRegex(ValueError, 'Partial'):
            validate_sequences(edits[:1], self.source, self.info, groups)
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.generate(source=[self.source[0], self.source[1]+b'!'])
        with self.assertRaisesRegex(ValueError, 'targets a reserved'):
            self.generate(source=self.source+[bytes.fromhex('7F0E00017F01')])

    def test_slices_cannot_drop_words_or_cut_controls(self):
        for side, shift in ((0, -1), (1, 1)):
            group = deepcopy(self.group)
            group['members'][side]['reference_slice'][1 if side == 0 else 0] += shift
            with self.assertRaises(ValueError): reference_payloads(group, {}, self.info)
        group = deepcopy(self.group); group['members'][0]['reference_slice'][0] = 1
        with self.assertRaisesRegex(ValueError, 'complete reference'):
            reference_payloads(group, {}, self.info)


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains local')
class NativeTravelRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.group = load_sequences()[GROUP]
        cls.drafts = json.loads((ROOT/'translations/n64-travel-advice.json').read_text())
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k, 16): v for k, v in font['advance_by_glyph'].items()}

    def test_complete_travel_split_and_both_runtime_modes(self):
        self.assertEqual([m['id'] for m in self.group['members']], ['message:0848', 'message:0A27'])
        whole = encode(native_reference(self.group, self.info)['text'], self.info)
        self.assertEqual((len(whole), expanded_bound(whole, self.info)), (818, 1134))
        for runtime in (False, True):
            edits, permits = reference_sequence_edits({}, self.source, self.info, {GROUP: self.group},
                                                     resident_runtime=runtime)
            parts = [encode(e['translation'], self.info) for e in edits]
            self.assertEqual([expanded_bound(p, self.info) for p in parts], [663, 489])
            self.assertEqual(parts[0][:-7]+GAP+parts[1], whole)
            self.assertTrue(parts[1].startswith(b'When you visit another town,'))
            for edit, payload in zip(edits, parts):
                validate_entry(self.source[int(edit['id'][8:], 16)], payload, self.info,
                               'message', 'reviewed_sequence', resident_runtime=runtime,
                               sequence_permit=permits[edit['id']])

    def test_three_drafts_have_only_exact_native_colour_length_changes(self):
        self.assertEqual({r['id'] for r in self.drafts}, {'message:0866', 'message:0870', 'message:087A'})
        for row in self.drafts:
            source = self.source[int(row['id'][8:], 16)]; output = encode(row['translation'], self.info)
            self.assertEqual(sha256(source), row['source_sha256'])
            expected = [c[:-1]+bytes([{2: 7, 9: 14}[c[-1]]])
                        if c[1] == 0x50 and c[2:5] in (bytes.fromhex('4BA000'), bytes.fromhex('198CDC'))
                        else c for c in commands(source, self.info)]
            self.assertEqual(commands(output, self.info), expected, row['id'])
            validate_entry(source, output, self.info, 'message', 'reference_layout', resident_runtime=True)
            self.assertLessEqual(expanded_bound(output, self.info), 1024)
        jock = next(r['translation'] for r in self.drafts if r['id'] == 'message:0866')
        self.assertIn('{cmd:7F504B5F9B02}--?', jock)
        self.assertIn('adventure,{cmd:7F04}\nhead to the', jock)

    def test_whole_native_command_pages_and_layout_are_retained(self):
        audit_native_translation(self.group, self.source[0x0848], self.info)
        texts = [r['translation'] for r in self.drafts]+[self.group['original_translation']['text']]
        warned = []
        for text in texts:
            output = encode(text, self.info)
            warned.append(bool(layout_issues(output, self.info, self.advances, resident_runtime=True)))
            bounded = encode(text.replace('{cmd:7F2F}', 'ア'*6), self.info)
            self.assertEqual(layout_issues(bounded, self.info, self.advances, resident_runtime=True), [])
        self.assertEqual(warned, [True, False, True, True])

    def test_complete_native_topics_and_no_gamecube_memory_card_rules(self):
        rows = {r['id'][8:]: plain(r['translation']) for r in self.drafts}
        rows['0848'] = plain(self.group['original_translation']['text'])
        topics = {'0848': ['friends', 'visit', 'boring', 'station', 'Controller Pak',
                           'Please remember', 'bulletin board', 'later', 'read', 'same way'],
                  '0866': ['guy needs', 'adventure', 'familiar ground', 'Meeting new people',
                           "man's romance", 'station', "can't board", 'essential'],
                  '0870': ['friends', 'barge', 'come visit', "world's", 'one town', 'station', 'forget'],
                  '087A': ['frog in a well', 'sea', 'superior', 'country bumpkin',
                           'world outside', 'mistaken', 'train', 'made it to this town']}
        for short, text in rows.items():
            for word in topics[short]: self.assertIn(word, text, short)
            self.assertIn('Controller Pak', text)
            self.assertNotIn('Memory Card', text)
            self.assertNotIn('town data', text)

    def test_reserve_has_no_native_message_instruction_or_data_reference(self):
        self.assertEqual(self.source[0x0A27], encode('おてがみ みせる よび\n{cmd:7F00}', self.info))
        for raw in self.source:
            self.assertNotIn(0x0A27, message_targets(raw, self.info))
        files = by_vrom(self.rom); hits = []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files: continue
            data = files[vrom].extract(self.rom)
            for offset in range(0, len(data)-3, 4):
                word = struct.unpack_from('>I', data, offset)[0]
                if segment.is_text(offset) and word >> 26 in range(8, 16) and word & 0xFFFF == 0x0A27:
                    hits.append((segment.name, segment.ram+offset))
            for offset in range(0, len(data)-1, 2):
                if not segment.is_text(offset) and data[offset:offset+2] == bytes.fromhex('0A27'):
                    hits.append((segment.name, segment.ram+offset))
        self.assertEqual(hits, [])


if __name__ == '__main__':
    unittest.main()
