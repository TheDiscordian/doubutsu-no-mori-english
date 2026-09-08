"""Invoice splits preserve full references and the native renovation actions."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from build import apply_translations
from code_sections import code_segments
from font import make_halfwidth
from reference_candidates import select_drafts
from reference_sequences import load_sequences, reference_sequence_edits, validate_sequences
from runtime_module import module_command_info
from sequence_prices import adapt_reference_price, audit_native_price, validate_price_group
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

GROUP = 'nook_first_renovation_invoice'


class SequencePriceTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.info[3] = (3, 0)
        self.source = encode('Pay 49800 Bells!{cmd:7F00}', self.info)
        self.text = 'Pay 148,000 Bells!{cmd:7F04}\n{cmd:7F02}Thank you!{cmd:7F00}'
        self.group = {'members': [{'id': 'message:0000', 'source_sha256': sha256(self.source)}],
                      'native_price': {'source_offset': 4, 'reference_offset': 4,
                                       'before': '148,000', 'after': '49,800',
                                       'adapted_reference_sha256': sha256(encode(
                                           self.text.replace('148,000', '49,800'), self.info))}}

    def test_only_the_exact_numeric_span_changes(self):
        audit_native_price(self.group, self.source, self.info)
        self.assertEqual(adapt_reference_price(self.group, self.text, self.info),
                         self.text.replace('148,000', '49,800'))

    def test_schema_rejects_non_numeric_and_combined_permissions(self):
        for key, value in [('after', '49,80'), ('after', '049,800'), ('after', '49\n800'),
                           ('after', '{cmd:7F00}'), ('after', '148,000'), ('before', ''),
                           ('source_offset', True), ('reference_offset', -1),
                           ('adapted_reference_sha256', '0')]:
            group = deepcopy(self.group); group['native_price'][key] = value
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_price_group(group)
        for change in ('native_original', 'article', 'other_reference'):
            group = deepcopy(self.group)
            if change == 'native_original': group['source_kind'] = change
            elif change == 'article': group['members'][0]['remove_redundant_cutarticle'] = False
            else: group['members'][0]['reference_id'] = 'message:0001'
            with self.assertRaises(ValueError): validate_price_group(group)

    def test_native_whole_amount_not_substring_or_command_data(self):
        for source in ('Pay 149800 Bells!{cmd:7F00}', 'Pay 498001 Bells!{cmd:7F00}',
                       'Pay 49801 Bells!{cmd:7F00}', 'Pay 49800,000 Bells!{cmd:7F00}'):
            group = deepcopy(self.group); raw = encode(source, self.info)
            group['members'][0]['source_sha256'] = sha256(raw)
            if '149800' in source: group['native_price']['source_offset'] += 1
            with self.assertRaisesRegex(ValueError, 'complete native amount'):
                audit_native_price(group, raw, self.info)
        raw = b'\x7f\x03'+encode('4', self.info)+b'\x7f\x00'
        group = deepcopy(self.group); group['members'][0]['source_sha256'] = sha256(raw)
        group['native_price'].update(source_offset=2, after='4')
        with self.assertRaisesRegex(ValueError, 'complete native amount'):
            audit_native_price(group, raw, self.info)

    def test_reference_whole_amount_and_complete_output_hash(self):
        for text in (self.text.replace('148,000', '1,148,000'),
                     self.text.replace('148,000', '148,000,000'), self.text+'Oops'):
            group = deepcopy(self.group)
            if '1,148,000' in text: group['native_price']['reference_offset'] += 2
            with self.assertRaises(ValueError): adapt_reference_price(group, text, self.info)
        group = deepcopy(self.group)
        group['native_price'].update(before='0304', after='0305', reference_offset=0)
        with self.assertRaises(ValueError): validate_price_group(group)
        # A valid numeric substring in a command tag must not alter its argument.
        text = '{cmd:7F0310}'; group = deepcopy(self.group)
        group['native_price'].update(before='7', after='8', reference_offset=5)
        with self.assertRaisesRegex(ValueError, 'Token kind/length mismatch'):
            adapt_reference_price(group, text, self.info)
        group['native_price'].update(before='1', after='2', reference_offset=7)
        with self.assertRaisesRegex(ValueError, 'changes a command'):
            adapt_reference_price(group, '{cmd:7F1A}', self.info)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Retail inputs stay local')
class NookRenovationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.refs = {r['id']: r for r in map(json.loads,
                    (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.group = load_sequences()[GROUP]
        cls.edits, cls.permits = reference_sequence_edits(cls.refs, cls.source, cls.info,
                                                         {GROUP: cls.group})
        cls.drafts = json.loads((ROOT/'translations/n64-renovations.json').read_text())

    def test_full_invoice_reconstruction_and_both_capacity_bounds(self):
        parts = [encode(e['translation'], self.info) for e in self.edits]
        whole = encode(self.refs['message:107E']['text'].replace('148,000', '49,800'), self.info)
        self.assertEqual(parts[0][:-7]+bytes.fromhex('7F04CD7F02')+parts[1], whole)
        self.assertEqual(parts[0][-7:], bytes.fromhex('7F0E083FCD7F01'))
        self.assertEqual([expanded_bound(p, self.info) for p in parts], [574, 483])
        self.assertEqual(expanded_bound(whole, self.info), 1039)
        for edit, payload in zip(self.edits, parts):
            validate_entry(self.source[int(edit['id'][8:], 16)], payload, self.info,
                           'message', 'reviewed_sequence', sequence_permit=self.permits[edit['id']])

    def test_builder_requires_complete_approved_parts_and_native_amount(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'; path.write_text(json.dumps(self.edits+self.drafts))
            count, _ = apply_translations(self.rom, {CODE_VROM: by_vrom(self.rom)[CODE_VROM].extract(self.rom)}, path)
            self.assertEqual(count, 4)
            for edits in (self.edits[:1], [dict(e, translation=e['translation']+'x') for e in self.edits]):
                path.write_text(json.dumps(edits))
                with self.assertRaises(ValueError): apply_translations(self.rom, {}, path)
        group = deepcopy(self.group); group['native_price']['after'] = '49,801'
        with self.assertRaisesRegex(ValueError, 'complete native amount'):
            validate_sequences(self.edits, self.source, self.info, {GROUP: group})

    def test_reserved_slot_scan_is_not_a_dialogue_pointer(self):
        files = by_vrom(self.rom); immediates, data_hits = [], []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files: continue
            data = files[vrom].extract(self.rom)
            for offset in range(0, len(data)-3, 4):
                word = struct.unpack_from('>I', data, offset)[0]
                if (segment.is_text(offset) and word & 0xffff == 0x083f
                        and word >> 26 in (8, 9, 10, 11, 12, 13, 14)):
                    immediates.append((segment.name, segment.ram+offset))
            for offset in range(0, len(data)-1, 2):
                if not segment.is_text(offset) and data[offset:offset+2] == b'\x08\x3f':
                    data_hits.append((segment.name, segment.ram+offset))
        self.assertEqual(immediates, [])
        self.assertEqual(data_hits, [('boot', 0x8003C644)])
        # Complete sequence validation also scans all incoming native script links.
        self.assertEqual(len(validate_sequences(self.edits, self.source, self.info, {GROUP: self.group})), 2)

    def test_original_drafts_preserve_every_native_command_and_fit(self):
        self.assertEqual(select_drafts(self.drafts), (self.drafts, []))
        _, font = make_halfwidth(self.rom)
        advances = {int(k, 16): v for k, v in font['advance_by_glyph'].items()}
        controls = lambda data: [t.data for t in tokenize(data, self.info) if t.kind == 'cmd']
        for draft, bound in zip(self.drafts, (421, 322)):
            source = self.source[int(draft['id'][8:], 16)]; raw = encode(draft['translation'], self.info)
            self.assertEqual(sha256(source), draft['source_sha256'])
            self.assertEqual(controls(raw), controls(source))
            self.assertEqual(expanded_bound(raw, self.info), bound)
            validate_entry(source, raw, self.info, 'message')
            self.assertEqual(layout_issues(raw, self.info, advances), [])
            self.assertNotIn('basement', draft['translation'])
        self.assertIn('cost quite a bit', self.drafts[0]['translation'])
        self.assertIn("even if you don't pay", self.drafts[1]['translation'])
        self.assertIn('colour roof', self.drafts[1]['translation'])
