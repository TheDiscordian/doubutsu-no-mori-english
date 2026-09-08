"""An existing native plus glyph must not be confused with its English byte code."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from gc_adapter import adapt_reference
from gc_text import decoder_tables, decode_gc
from reference_content import adapt_content_reference, validate_content_approval, validate_content_candidate
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import Bank, banks
from textcodec import encode
from textvalidate import validate_entry, expanded_bound
from test_retail import ROM_PATH


class ReferencePlusTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77; self.info[3] = (3, 0)
        self.source = encode('Native{cmd:7F00}', self.info)
        self.text = 'A+B{cmd:7F0306}\n{cmd:7F00}'
        self.native = encode(self.text, self.info)
        self.english = self.native[:1]+b'\xb4'+self.native[2:]
        self.reference = {'id': 'message:0000', 'text': self.text, 'sha256': sha256(self.english)}
        self.record = {'id': self.reference['id'], 'reference_id': self.reference['id'],
                       'source_sha256': sha256(self.source), 'reference_sha256': sha256(self.english),
                       'complete_reference': {'adapted_sha256': sha256(self.native), 'gamecube_plus_offsets': [1]}}

    def test_original_english_hash_and_native_plus_keep_complete_text(self):
        self.assertNotEqual(sha256(self.english), sha256(self.native))
        self.assertEqual(adapt_content_reference(self.reference, self.source, self.record, self.info), (self.text, []))
        validate_content_candidate(self.record['id'], self.source, self.native, {self.record['id']: self.record})
        with self.assertRaises(ValueError):
            validate_content_candidate(self.record['id'], self.source, self.english, {self.record['id']: self.record})

    def test_schema_rejects_offsets_and_combined_permissions(self):
        for offsets in ([], None, [True], [-1], [1024], [1, 1], [2, 1], ['1']):
            record = deepcopy(self.record); record['complete_reference']['gamecube_plus_offsets'] = offsets
            with self.assertRaises(ValueError): validate_content_approval(record)
        for key in ('spans', 'native_random', 'native_mood', 'omit_startup_storage_location'):
            record = deepcopy(self.record); record['complete_reference'][key] = {}
            with self.assertRaises(ValueError): validate_content_approval(record)

    def test_non_plus_and_command_argument_offsets_are_rejected(self):
        for offset in (0, 2, 4, 100):
            record = deepcopy(self.record); record['complete_reference']['gamecube_plus_offsets'] = [offset]
            with self.assertRaisesRegex(ValueError, 'complete native plus glyph'):
                adapt_content_reference(self.reference, self.source, record, self.info)
        text = 'A{cmd:7F035C}+{cmd:7F00}'
        reference = {**self.reference, 'text': text}
        record = deepcopy(self.record); record['complete_reference']['gamecube_plus_offsets'] = [3]
        with self.assertRaisesRegex(ValueError, 'complete native plus glyph'):
            adapt_content_reference(reference, self.source, record, self.info)

    def test_complete_hashes_still_reject_omitted_or_altered_text(self):
        for reference in ({**self.reference, 'text': self.text+'!'},
                          {**self.reference, 'sha256': sha256(self.native)}):
            with self.assertRaisesRegex(ValueError, 'Stale'):
                adapt_content_reference(reference, self.source, self.record, self.info)
        with self.assertRaisesRegex(ValueError, 'Stale'):
            adapt_content_reference(self.reference, self.source+b' ', self.record, self.info)
        record = deepcopy(self.record); del record['complete_reference']['gamecube_plus_offsets']
        with self.assertRaisesRegex(ValueError, 'Stale'):
            adapt_content_reference(self.reference, self.source, record, self.info)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/files/forest_2nd.arc.unpacked/data/message_data.bin').is_file(),
                     'Supplied native/English input data stays local')
class ReferencePlusRetailTests(unittest.TestCase):
    def test_actual_english_data_maps_only_one_plus_and_preserves_full_controller_tip(self):
        rom = verified_rom(ROM_PATH.read_bytes()); info = module_command_info(rom)
        source = next(b for b in banks(rom) if b.name == 'message').entries()[0x14FD]
        root = ROOT/'build/gamecube/files/forest_2nd.arc.unpacked/data'
        original = Bank('message', 0, 0, (root/'message_data.bin').read_bytes(),
                        (root/'message_data_table.bin').read_bytes()).entries()[0x14FD]
        reference = next(r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())
                         if r['id'] == 'message:14FD')
        decoder = decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')
        self.assertEqual(decode_gc(original, decoder), reference['text'])
        self.assertEqual(sha256(original), reference['sha256'])
        self.assertEqual(decoder['CHAR_MAP'][0xB4], '+')
        matches = load_matches(ROOT/'translations/reference_matches.json'); record = matches[reference['id']]
        text, changes = adapt_content_reference(reference, source, record, info)
        self.assertEqual(text, reference['text']); self.assertEqual(changes, [])
        final, _ = adapt_reference(text, source, info, 'reference_layout', True)
        self.assertEqual(final, text); output = encode(final, info)
        self.assertEqual(len(output), 254); self.assertEqual(len(original), len(output))
        self.assertEqual([(i, a, b) for i, (a, b) in enumerate(zip(original, output)) if a != b], [(112, 0xB4, 0x5C)])
        self.assertEqual(expanded_bound(output, info), 300)
        for resident in (False, True):
            validate_entry(source, output, info, 'message', 'reference_layout', resident_runtime=resident)
        validate_content_candidate(reference['id'], source, output, matches)
