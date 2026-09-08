"""Native-only topics, complete meal-greeting emphasis, and connected answers."""

from copy import deepcopy
from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from build import apply_translations
from contextual_choices import canonical_candidate, display_candidate, load_contextual_choices, unique_menu
from font import make_halfwidth
from gc_adapter import adapt_reference
from reference_candidates import select_drafts, record_candidate, record_contextual_candidates
from reference_content import adapt_content_reference, validate_content_candidate
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from topic_gap_test_scenario import combine_checkpoints
from test_retail import ROM_PATH

IDS = '0B69 11FC 1D47 2006 2018 204B 246C 25E6 25EB 25FD'.split()
BOUNDS = (117, 340, 153, 209, 361, 267, 106, 211, 228, 235)
SHOUTS = {'25E6': "Let's eat!", '25EB': 'Thanks for the meal!'}


class TopicSelectionTests(unittest.TestCase):
    def test_batched_scenarios_keep_all_assertions_and_restore_only_once(self):
        prefix = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]
        restore = [{'load_state': True}, {'resume': True}, {'wait': 2}]
        read = {'read': ['8019B000', 4], 'expect': '00000000'}
        one = prefix+[{'read': ['8019C8D0', 4], 'expect': 'AF32C0DE'}]+restore+[read]
        two = prefix+[{'read': ['8019B900', 4], 'expect': '00000000'}]+restore+[read]
        result = combine_checkpoints([one, two])
        self.assertEqual(result, prefix+[one[3], two[3]]+restore+[read])
        for parts in ([], [one, two[1:]], [one, two+[{'resume': True}]],
                      [one, two[:-1]+[{**read, 'expect': '01000000'}]],
                      [one, two[:-1]+[{'read': ['8019B001', 1], 'expect': '01'}]],
                      [one, two[:-1]+[{**read, 'expect': '00'}]],
                      [one, prefix+[{'resume': True}]+restore+[read]]):
            with self.assertRaises(ValueError): combine_checkpoints(parts)

    def test_all_complete_originals_remain_available_in_basic_generation(self):
        rows = json.loads((ROOT/'translations/n64-topic-gaps.json').read_text())
        self.assertEqual([r['id'][8:] for r in rows], IDS)
        self.assertEqual(select_drafts(rows), (rows, []))
        self.assertTrue(all(r['status'] == 'draft' for r in rows))

    def test_contextual_originals_are_not_counted_as_reference_imports(self):
        info = [(2, 0)]*0x61
        ref = dict(id='message:0000', translation='English{cmd:7F00}', control_policy='exact')
        original = dict(id='message:0001', translation='Original{cmd:7F00}', status='draft')
        before = {e['id']: e for e in (ref, original)}
        manifests, counts = [], Counter(original_draft_override=1)
        record_candidate(ref, info, {}, 'message', [], manifests, counts)
        changed = [{**e, 'adaptations': [{'operation': 'use_reviewed_contextual_choice_labels'}]}
                   for e in (ref, original)]
        result = record_contextual_candidates(before, changed, list(before), set(), info, {},
                                               manifests, counts)
        self.assertEqual(len(result), 2)
        self.assertEqual(counts['accepted_candidates'], 1)
        self.assertEqual(counts['original_draft_override'], 1)
        self.assertEqual(counts['contextual_original_draft_candidates'], 1)
        self.assertEqual(counts['contextual_choice_candidates'], 2)
        # A missing label dependency removes the original draft, not a reference.
        counts = Counter(original_draft_override=1, accepted_candidates=1)
        result = record_contextual_candidates(before, [ref], [], {'message:0001'}, info, {},
                                               manifests, counts)
        self.assertEqual(result, manifests)
        self.assertEqual(counts['accepted_candidates'], 1)
        self.assertEqual(counts['original_draft_override'], 0)


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM stays local')
class NativeTopicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.sources = {b.name: b.entries() for b in banks(cls.rom)}
        cls.rows = json.loads((ROOT/'translations/n64-topic-gaps.json').read_text())
        cls.text = {r['id'][8:]: r['translation'] for r in cls.rows}
        cls.matches = load_matches(ROOT/'translations/reference_matches.json')
        cls.contextual = load_contextual_choices(cls.matches)
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k, 16): v for k, v in font['advance_by_glyph'].items()}

    def test_exact_native_controls_with_only_complete_shout_formatting_changes(self):
        controls = lambda data: [t.data for t in tokenize(data, self.info) if t.kind == 'cmd']
        for row, bound in zip(self.rows, BOUNDS):
            id = row['id'][8:]; source = self.sources['message'][int(id, 16)]
            raw = encode(row['translation'], self.info)
            self.assertEqual(sha256(source), row['source_sha256'])
            original, translated = controls(source), controls(raw)
            if id in SHOUTS:
                self.assertEqual([c for c in original if c[1] not in (0x50, 0x54)],
                                 [c for c in translated if c[1] not in (0x50, 0x54)])
                self.assertEqual([c for c in original if c[1] == 0x50], [bytes.fromhex('7F50E11ED708')])
                self.assertEqual([c for c in translated if c[1] == 0x50],
                                 [bytes.fromhex('7F50E11ED7')+bytes([len(SHOUTS[id])])])
                self.assertEqual([c for c in original if c[1] == 0x54], [bytes.fromhex('7F542D')]*8)
                self.assertEqual([c for c in translated if c[1] == 0x54],
                                 [bytes.fromhex('7F542D')]*len(SHOUTS[id]))
            else:
                self.assertEqual(original, translated, id)
            self.assertEqual(expanded_bound(raw, self.info), bound)
            validate_entry(source, raw, self.info, 'message', row.get('control_policy', 'exact'))

    def test_layout_and_every_complete_english_shout_character_remains_emphasised(self):
        for id, text in self.text.items():
            raw = encode(text, self.info)
            self.assertEqual(layout_issues(raw, self.info, self.advances),
                             ['explicit_layout_command_needs_review'] if id in SHOUTS else [], id)
            if id in SHOUTS:
                phrase = SHOUTS[id]
                expected = bytes.fromhex('7F50E11ED7')+bytes([len(phrase)])
                expected += b''.join(bytes.fromhex('7F542D')+encode(c, self.info) for c in phrase)
                self.assertEqual(raw.count(expected+b'\xcd'), 1)
                width = sum(self.advances[c] for c in encode(phrase, self.info))*45/32
                self.assertLessEqual(width, 168)

    def test_native_topics_and_complete_connected_greeting_correction(self):
        for phrase in ('net', 'sneaking', 'ninja', 'insects'):
            self.assertIn(phrase, self.text['2006'])
        self.assertNotIn('Game Boy', self.text['2006'])
        for phrase in ('shovel', 'fill those holes', 'surrounded', 'all night'):
            self.assertIn(phrase, self.text['2018'])
        self.assertNotIn('island', self.text['2018'])
        self.assertIn('unless you take the train', self.text['11FC'])
        self.assertIn('some excuse', self.text['11FC'])
        self.assertIn('This season', self.text['1D47']); self.assertNotIn('September', self.text['1D47'])
        self.assertIn('really precious to you?', self.text['204B'])
        self.assertIn('{cmd:7F16011E0128}', self.text['204B'])
        self.assertIn('{cmd:7F0F2059}{cmd:7F102058}', self.text['204B'])
        self.assertIn('"hello"', self.text['25FD'])
        self.assertIn('Thanks for reminding me', self.text['25FD'])
        self.assertNotIn('mom', self.text['25FD'])
        self.assertIn('{cmd:7F0F25FD}{cmd:7F1025FE}', self.text['25E6'])
        self.assertIn('{cmd:7F0F25FF}{cmd:7F102600}', self.text['25EB'])

    def test_original_quiz_context_changes_only_labels_not_answers_or_words(self):
        original_rules = {id: row for id, row in self.contextual.items()
                          if row.get('source_kind') == 'native_original'}
        self.assertEqual(set(original_rules), {'message:0B69', 'message:246C'})
        for id, row in original_rules.items():
            self.assertNotIn(id, self.matches)
            source = self.sources['message'][int(id[8:], 16)]
            base = encode(self.text[id[8:]], self.info)
            output = display_candidate(id, source, base, self.contextual, self.info)
            self.assertEqual(canonical_candidate(id, source, output, self.contextual, self.info), base)
            menu = unique_menu(base, self.info)
            self.assertEqual(output[:menu.offset], base[:menu.offset])
            self.assertEqual(output[menu.offset+6:], base[menu.offset+6:])
            validate_entry(source, base, self.info, 'message', 'exact')
        self.assertEqual(original_rules['message:0B69']['display_command'], '7F1600250026')
        self.assertEqual(original_rules['message:246C']['display_command'], '7F1600250051')
        self.assertIn('Pon Curry', self.text['0B69'])
        self.assertIn('{cmd:7F0F0B65}{cmd:7F100B64}', self.text['0B69'])
        self.assertIn('row six', self.text['246C'])
        self.assertIn('{cmd:7F102476}{cmd:7F0F2472}', self.text['246C'])

    def test_builder_cannot_skip_original_context_binding_by_omitting_metadata(self):
        id = 'message:0B69'; source = self.sources['message'][0x0B69]
        base = encode(self.text['0B69'], self.info)
        output = display_candidate(id, source, base, self.contextual, self.info)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'
            for text in (self.text['0B69'], self.text['0B69']+'x',
                         self.text['0B69'].replace('7F1600CD00CE', '7F1600250026')):
                path.write_text(json.dumps([dict(id=id, source_sha256=sha256(source),
                                                translation=text, control_policy='reference_layout')]))
                with self.assertRaisesRegex(ValueError, 'contextual display approval|complete English labels'):
                    apply_translations(self.rom, {}, path)
        changed = deepcopy(self.contextual); row = changed[id]
        broken = base.replace(bytes.fromhex('7F0F0B65'), bytes.fromhex('7F0F0B64'))
        row['candidate_sha256'] = sha256(broken)
        with self.assertRaisesRegex(ValueError, 'changes a native command'):
            display_candidate(id, source, broken, changed, self.info)

    @unittest.skipUnless((ROOT/'build/gamecube/text/message.jsonl').is_file(), 'English disc stays local')
    def test_complete_snow_ending_matches_the_connected_gamecube_localisation(self):
        refs = {r['id']: r for r in map(json.loads,
                (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        parent = self.sources['message'][0x207A]
        branches = [t.data for t in tokenize(parent, self.info) if t.kind == 'cmd' and 0x0F <= t.data[1] <= 0x12]
        self.assertEqual(branches, [bytes.fromhex(c) for c in ('7F0F2771', '7F102772', '7F112773')])
        self.assertIn('all girls', refs['message:207A']['text'])
        self.assertIn('fluffy', refs['message:2771']['text'])
        self.assertIn('But girls are!', refs['message:2772']['text'])
        self.assertIn('resident_animations', self.matches['message:2772'])
        record = self.matches['message:2773']; source = self.sources['message'][0x2773]
        text, _ = adapt_content_reference(refs['message:2773'], source, record, self.info)
        text, _ = adapt_reference(text, source, self.info, 'reference_layout', True)
        self.assertEqual(text.replace('{cmd:7F09020001}{cmd:7F09080001}', '', 1), refs['message:2773']['text'])
        self.assertIn('{cmd:7F02}{cmd:7F09020001}{cmd:7F09080001}{cmd:7F0900000A}', text)
        raw = encode(text, self.info)
        validate_content_candidate(record['id'], source, raw, self.matches)
        validate_entry(source, raw, self.info, 'message', 'reference_layout')
        self.assertEqual(expanded_bound(raw, self.info), 281)
