"""Reserve labels stay distinct from dialogue and approved continuation pages."""

from collections import Counter
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from audit_placeholders import audit
from build import apply_translations
from font import make_halfwidth
from placeholder_text import label, native_label, placeholder_edit, validate_placeholder
from reference_candidates import native_placeholder_fallback
from reference_sequences import load_sequences, reference_sequence_edits
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from text_coverage import classify, coverage_rows, summarise
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

CORRECTED = {'message:'+id for id in '07DA 2AFF 2B00 2B01 2B02 2B03 2B04 2B42'.split()}
ALLOCATED = {'message:'+id for id in
             '0486 0838 0839 083A 083B 083C 083D 083E 083F 0921 0A26 0A27 2AE9 2AEA 2B05 2B06'.split()}


class PlaceholderTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.info[9] = (5, 0)
        self.info[0x0E] = (4, 0)

    def test_exact_wordings_and_numbers_not_substrings(self):
        for source, english in (
                ('ダミー７', 'Dummy 7'), ('ダミー 7', 'Dummy 7'), ('よび', 'Reserved'),
                ('きしゃのデモ\nよびのエリア', 'Train Demo\nExtra Area'),
                ('タカビーねえさんの\nトレード２のよび', 'Snooty woman\nTrade 2 reserve'),
                ('ふつうのおんなのこ\nいっぱんかいわよう\nよび１００',
                 'Normal girl\nGeneral chat reserve 100')):
            self.assertEqual(label(source).english, english)
        for text in ('よびとめて ごめん', 'ダミーです', 'よびだしました',
                     'まいにちが にちようび', 'ハロウィン よびメッセージ',
                     'ハロウィン よびメッセージ1です', 'オープニングの よびです'):
            self.assertIsNone(label(text), text)

    def test_only_known_complete_english_label_variants_are_accepted(self):
        for source, english in (('ダミー7', 'Dummy7'), ('ダミー7', 'Dummy 7'),
                                ('イベントこくち\nよび', 'extra'),
                                ('きしゃのデモ よびのエリア', 'Train Demo Extra Space')):
            validate_placeholder(encode(source+'{cmd:7F00}', self.info),
                                 encode(english+'{cmd:7F00}', self.info), self.info)
        source = encode('ダミー7{cmd:7F00}', self.info)
        for text in ('Dummy 8{cmd:7F00}', 'Good night!{cmd:7F00}',
                     'Dummy 7{cmd:7F1A}{cmd:7F00}', 'Dummy 7{cmd:7F01}',
                     'Dummy 7{cmd:7F04}{cmd:7F00}'):
            with self.assertRaisesRegex(ValueError, 'Native placeholder'):
                validate_placeholder(source, encode(text, self.info), self.info)

    def test_optional_native_expression_and_both_terminators_are_retained(self):
        for prefix in ('', '{cmd:7F090000FF}'):
            for ending in ('{cmd:7F00}', '{cmd:7F01}'):
                source = encode(prefix+'ダミー7\n'+ending, self.info)
                edit = placeholder_edit('message:0000', source, self.info)
                self.assertEqual(edit['translation'], prefix+'Dummy 7\n'+ending)
                self.assertEqual(edit['source_sha256'], sha256(source))
                self.assertEqual(edit['status'], 'draft')
                validate_entry(source, encode(edit['translation'], self.info), self.info, 'message')
        for text in ('よび', 'よび{cmd:7F00} ', 'よび{cmd:7F090000FF}{cmd:7F00}',
                     '{cmd:7F09000015}よび{cmd:7F00}', 'よび{cmd:7F0E0001}{cmd:7F00}'):
            with self.assertRaisesRegex(ValueError, 'Placeholder fallback'):
                placeholder_edit('message:0000', encode(text, self.info), self.info)

    def test_unknown_visible_data_is_not_hidden_by_label_recognition(self):
        for suffix in (bytes.fromhex('8000'), bytes.fromhex('7FFF'), b'\x80'):
            source = encode('よび', self.info)+suffix
            self.assertIsNone(native_label(source, self.info))
            self.assertIsNone(placeholder_edit('message:0000', source, self.info))

    def test_fallback_excludes_explicit_approvals_and_rejects_stale_inventory(self):
        source = encode('よび{cmd:7F00}', self.info)
        row = {'id': 'message:0000', 'source_sha256': sha256(source)}
        self.assertIsNone(native_placeholder_fallback(row, source, self.info, skip_ids={row['id']}))
        self.assertIsNotNone(native_placeholder_fallback(row, source, self.info, skip_ids=set()))
        with self.assertRaisesRegex(ValueError, 'Stale placeholder'):
            native_placeholder_fallback({**row, 'source_sha256': '0'*64}, source, self.info, skip_ids=set())

    def test_labels_do_not_establish_unreachable_or_reviewed_status(self):
        source = encode('よび{cmd:7F00}', self.info)
        edit = placeholder_edit('message:0000', source, self.info)
        rows = coverage_rows('message', [source], {edit['id']: edit}, self.info)
        self.assertEqual(rows[0]['source']['category'], 'development_placeholder_text')
        self.assertEqual(rows[0]['reachability'], 'not_established')
        self.assertTrue(rows[0]['control_flow_audit_required'])
        self.assertEqual(summarise(rows)['review_complete_records'], 0)

    def test_audit_retains_incoming_targets_and_reports_invalid_candidates(self):
        source = encode('よび{cmd:7F00}', self.info)
        caller = encode('Hello{cmd:7F0E0000}{cmd:7F01}', self.info)
        edit = placeholder_edit('message:0000', source, self.info)
        rows = audit([source, caller], {edit['id']: edit}, self.info)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['status'], 'english_label_candidate')
        self.assertEqual(rows[0]['native_message_script_incoming'], ['message:0001'])
        self.assertEqual(rows[0]['reachability'], 'not_established')
        bad = {**edit, 'translation': 'Wrong dialogue{cmd:7F00}'}
        self.assertEqual(audit([source, caller], {bad['id']: bad}, self.info)[0]['status'], 'invalid_candidate')
        self.assertEqual(audit([source, caller], {}, self.info)[0]['status'], 'missing_candidate')
        with self.assertRaisesRegex(ValueError, 'Stale placeholder'):
            audit([source, caller], {edit['id']: {**edit, 'source_sha256': '0'*64}}, self.info)


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains local')
class RetailPlaceholderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.labels = {f'message:{i:04X}': native_label(raw, cls.info)
                      for i, raw in enumerate(cls.source) if native_label(raw, cls.info)}
        cls.groups = load_sequences()
        cls.allocated = {m['id'] for g in cls.groups.values() for m in g['members']}
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k,16): v for k,v in font['advance_by_glyph'].items()}

    def test_entire_native_catalog_classification_and_allocations(self):
        self.assertEqual(Counter(p.kind for p in self.labels.values()),
                         {'dummy': 48, 'reserved': 207, 'train_demo_reserve': 10, 'numbered_reserve': 95})
        self.assertEqual(self.labels.keys() & self.allocated, ALLOCATED)
        for id in self.labels:
            self.assertEqual(classify(self.source[int(id[8:],16)], self.info)['category'],
                             'development_placeholder_text', id)
        self.assertEqual(len(self.labels.keys()-self.allocated), 344)

    def test_all_unallocated_labels_fit_and_preserve_exact_controls(self):
        prefixes, continuing = set(), set()
        commands = lambda raw: [t.data for t in tokenize(raw, self.info) if t.kind == 'cmd']
        for id in self.labels:
            source = self.source[int(id[8:],16)]
            row = {'id': id, 'source_sha256': sha256(source)}
            edit = native_placeholder_fallback(row, source, self.info, skip_ids=self.allocated)
            if id in self.allocated:
                self.assertIsNone(edit, id)
                continue
            output = encode(edit['translation'], self.info)
            self.assertEqual(commands(source), commands(output), id)
            self.assertEqual(layout_issues(output, self.info, self.advances), [], id)
            self.assertLessEqual(expanded_bound(output, self.info), 1024)
            self.assertEqual(classify(output, self.info)['category'], 'latin_static_text')
            if output.startswith(bytes.fromhex('7F090000FF')): prefixes.add(id)
            if output.endswith(bytes.fromhex('7F01')): continuing.add(id)
        self.assertEqual(prefixes, {f'message:{i:04X}' for i in (*range(0x24A8,0x24C9), *range(0x24F1,0x250F))})
        self.assertEqual(continuing, {f'message:{i:04X}' for i in (*range(0x1B42,0x1B4B), 0x19C3, 0x19C4)})

    def test_unrelated_gamecube_signs_are_rejected_independently_by_builder(self):
        path = ROOT/'build/gamecube/text/message.jsonl'
        if not path.is_file(): self.skipTest('English extraction stays local')
        gc = {r['id']: r for r in map(json.loads, path.read_text().splitlines())}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'
            for id in sorted(CORRECTED):
                source = self.source[int(id[8:],16)]
                self.assertEqual(native_label(source, self.info).english, 'Reserved')
                edit = {'id': id, 'source_sha256': sha256(source), 'translation': gc[id]['text'],
                        'control_policy': 'reference_layout', 'status': 'reviewed'}
                path.write_text(json.dumps([edit]))
                with self.assertRaisesRegex(ValueError, 'Native placeholder'):
                    apply_translations(self.rom, {}, path)
            edit['control_policy'] = 'reviewed_sequence'
            path.write_text(json.dumps([edit]))
            with self.assertRaisesRegex(ValueError, 'sequence'):
                apply_translations(self.rom, {}, path)

    def test_approved_sequences_keep_full_payloads_and_runtime_requirements(self):
        path = ROOT/'build/gamecube/text/message.jsonl'
        if not path.is_file(): self.skipTest('English extraction stays local')
        gc = {r['id']: r for r in map(json.loads, path.read_text().splitlines())}
        edits, permits = reference_sequence_edits(gc, self.source, self.info, resident_runtime=True)
        self.assertEqual(len(edits), 36)
        for edit in edits:
            source = self.source[int(edit['id'][8:],16)]; output = encode(edit['translation'], self.info)
            validate_entry(source, output, self.info, 'message', 'reviewed_sequence',
                           resident_runtime=True, sequence_permit=permits[edit['id']])
            if edit['id'] in ALLOCATED:
                with self.assertRaisesRegex(ValueError, 'Native placeholder'):
                    validate_entry(source, output, self.info, 'message', 'reference_layout', resident_runtime=True)
        basic, _ = reference_sequence_edits(gc, self.source, self.info)
        self.assertFalse({'message:083E','message:0A26'} & {e['id'] for e in basic})
        for id in ALLOCATED:
            source = self.source[int(id[8:],16)]
            self.assertIsNone(native_placeholder_fallback({'id': id, 'source_sha256': sha256(source)},
                              source, self.info, skip_ids=self.allocated))


if __name__ == '__main__':
    unittest.main()
