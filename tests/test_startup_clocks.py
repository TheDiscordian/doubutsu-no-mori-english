"""Opening RTC greetings omit only the unsupported GC storage-location clause."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from reference_candidates import draft_module_commands, select_drafts
from reference_content import (STARTUP_STORAGE_SPANS, adapt_content_reference,
                               validate_content_approval, validate_content_candidate)
from reference_matches import load_matches
from runtime_module import MODULE_COMMANDS, module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import expanded_bound, validate_entry
from test_retail import ROM_PATH


class DraftCommandSelectionTests(unittest.TestCase):
    def test_each_implemented_extension_requires_the_module(self):
        for code, (size, _) in MODULE_COMMANDS.items():
            text = 'Text{cmd:7F'+f'{code:02X}'+'00'*(size-2)+'}{cmd:7F00}'
            draft = {'id': 'message:0000', 'translation': text}
            self.assertEqual(select_drafts([draft]), ([], [
                {'id': draft['id'], 'reason': 'resident_runtime_unavailable',
                 'module_commands': [f'7F{code:02X}']}]))
            self.assertEqual(select_drafts([draft], resident_runtime=True), ([draft], []))

    def test_native_tokens_and_glyph_arguments_do_not_require_the_module(self):
        text = 'Native{glyph:8076}{cmd:7F0376}{cmd:7F00}'
        self.assertEqual(draft_module_commands(text), [])
        draft = {'id': 'message:0000', 'translation': text}
        self.assertEqual(select_drafts([draft]), ([draft], []))

    def test_unknown_and_wrong_size_extensions_are_not_withheld_as_valid(self):
        for token in ('7F61', '7F74', '7F77', '7F67', '7F7600', '7F670000'):
            for enabled in (False, True):
                with self.subTest(token=token, enabled=enabled), self.assertRaises(ValueError):
                    select_drafts([{'id': 'message:0000', 'translation': '{cmd:'+token+'}'}],
                                  resident_runtime=enabled)

    def test_date_and_module_requirements_are_independent(self):
        draft = {'id': 'message:0000', 'translation': '{cmd:7F21}{cmd:7F76}{cmd:7F00}',
                 'runtime_requirements': ['ordinary_dialogue_dates']}
        self.assertEqual(select_drafts([draft], resident_runtime=True)[0], [])
        self.assertEqual(select_drafts([draft], english_dialogue_dates=True)[0], [])
        self.assertEqual(select_drafts([draft], resident_runtime=True,
                                     english_dialogue_dates=True), ([draft], []))


class StorageOmissionTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[0x50] = (6, 0)
        self.source = encode('Clock'+''.join('{cmd:7F'+f'{c:02X}'+'}'
                             for c in (0x1c, 0x2f, 0x1d, 0x1e, 0x20, 0x21, 0x22)), self.info)
        before, after = STARTUP_STORAGE_SPANS['message:13F2']
        self.reference = {'id': 'message:13F2', 'text': 'Now '+before+'\n{cmd:7F2F}.{cmd:7F01}'}
        self.reference['sha256'] = sha256(encode(self.reference['text'], self.info))
        self.record = {'id': self.reference['id'], 'reference_id': self.reference['id'],
                       'source_sha256': sha256(self.source), 'reference_sha256': self.reference['sha256'],
                       'complete_reference': {'adapted_sha256': sha256(encode('Now in\n{cmd:7F2F}.{cmd:7F01}', self.info)),
                           'omit_startup_storage_location': True,
                           'spans': [{'offset': 4, 'before': before, 'after': after}]}}

    def adapt(self, record=None, source=None, reference=None):
        return adapt_content_reference(reference or self.reference, source or self.source,
                                       record or self.record, self.info)

    def test_exact_clause_omission_keeps_town_and_line(self):
        text, changes = self.adapt()
        self.assertEqual(text, 'Now in\n{cmd:7F2F}.{cmd:7F01}')
        self.assertEqual(changes[0]['operation'], 'omit_startup_storage_location')
        validate_content_candidate(self.record['id'], self.source, encode(text, self.info),
                                   {self.record['id']: self.record})
        record = deepcopy(self.record)
        del record['complete_reference']['omit_startup_storage_location']
        with self.assertRaisesRegex(ValueError, 'changes delivery'):
            self.adapt(record)

    def test_flag_is_exact_and_restricted_to_six_same_id_greetings(self):
        for value in (False, 1, None, 'true'):
            record = deepcopy(self.record)
            record['complete_reference']['omit_startup_storage_location'] = value
            with self.assertRaisesRegex(ValueError, 'storage-location'):
                validate_content_approval(record)
        for key, value in (('id', 'message:0000'), ('reference_id', 'message:141A')):
            with self.assertRaisesRegex(ValueError, 'storage-location'):
                validate_content_approval({**self.record, key: value})

    def test_omission_cannot_authorise_other_wording_or_control_changes(self):
        for after in ('in\n', 'in{cmd:7F21}', 'in{cmd:7F04}', 'in{cmd:7F28}', 'in a different town'):
            record = deepcopy(self.record)
            record['complete_reference']['spans'][0]['after'] = after
            with self.assertRaisesRegex(ValueError, 'storage-location'):
                self.adapt(record)
        for spans in ([], self.record['complete_reference']['spans']*2):
            record = deepcopy(self.record); record['complete_reference']['spans'] = spans
            with self.assertRaises(ValueError): self.adapt(record)

    def test_native_storage_or_missing_clock_fields_reject_even_with_updated_hash(self):
        for source in (self.source+b'\x7f\x28', self.source.replace(b'\x7f\x21', b'')):
            record = {**self.record, 'source_sha256': sha256(source)}
            with self.assertRaisesRegex(ValueError, 'native clock fields'):
                self.adapt(record, source)

    def test_second_storage_field_and_stale_sources_or_payloads_reject(self):
        reference = {**self.reference, 'text': self.reference['text']+'{cmd:7F28}'}
        reference['sha256'] = sha256(encode(reference['text'], self.info))
        record = {**self.record, 'reference_sha256': reference['sha256']}
        with self.assertRaisesRegex(ValueError, 'native clock fields'):
            self.adapt(record, reference=reference)
        with self.assertRaisesRegex(ValueError, 'Stale'):
            self.adapt(source=self.source+b' ')
        with self.assertRaisesRegex(ValueError, 'reviewed payload'):
            validate_content_candidate(self.record['id'], self.source, b'Changed',
                                       {self.record['id']: self.record})


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Retail ROM and English extraction stay local')
class RetailStartupClockTests(unittest.TestCase):
    def test_builder_rejects_changed_payload_and_uninstalled_module(self):
        from build import apply_translations
        rom = verified_rom(ROM_PATH.read_bytes())
        info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == 'message').entries()
        references = {r['id']: r for r in map(json.loads,
            (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        matches = load_matches(ROOT/'translations/reference_matches.json')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'
            for id in STARTUP_STORAGE_SPANS:
                record = matches[id]
                source = sources[int(id[8:], 16)]
                text, _ = adapt_content_reference(references[id], source, record, info)
                for translation, error in (('Changed{cmd:7F01}', 'reviewed payload'),
                                           (text, 'Unsupported command 7F76')):
                    path.write_text(json.dumps([{'id': id, 'source_sha256': sha256(source),
                        'translation': translation, 'control_policy': 'reference_layout'}]))
                    with self.subTest(id=id, error=error), self.assertRaisesRegex(ValueError, error):
                        apply_translations(rom, {}, path)

    def test_all_six_complete_references_keep_delivery_fields_and_native_links(self):
        rom = verified_rom(ROM_PATH.read_bytes()); info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == 'message').entries()
        references = {r['id']: r for r in map(json.loads,
            (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        matches = load_matches(ROOT/'translations/reference_matches.json')
        approved = {id: r for id, r in matches.items()
                    if r.get('complete_reference', {}).get('omit_startup_storage_location')}
        self.assertEqual(set(approved), set(STARTUP_STORAGE_SPANS))
        for id, record in approved.items():
            with self.subTest(id=id):
                source = sources[int(id[8:], 16)]; reference = references[id]
                text, _ = adapt_content_reference(reference, source, record, info)
                output = encode(text, info)
                validate_content_candidate(id, source, output, matches)
                validate_entry(source, output, info, 'message', 'reference_layout', resident_runtime=True)
                before, after = STARTUP_STORAGE_SPANS[id]
                self.assertEqual(text, reference['text'].replace(before, after))
                delivery = lambda raw: [t.data for t in tokenize(raw, info)
                    if (t.kind == 'cmd' and t.data[1] not in (0x28, 0x50)) or t.data == b'\xcd']
                self.assertEqual(delivery(output), delivery(encode(reference['text'], info)))
                self.assertNotIn(b'\x7f\x28', output)
                self.assertEqual(output.count(b'\x7f\x76'), 1)
                self.assertLess(output.index(b'\x7f\x21'), output.index(b'\x7f\x76'))
                link = b'\x7f\x0e'+(int(id[8:],16)+2).to_bytes(2,'big')
                self.assertIn(link, source); self.assertIn(link, output)
                self.assertEqual(output[-2:], b'\x7f\x01')
                self.assertLessEqual(expanded_bound(output, info), 1024)
                with self.assertRaises(ValueError):
                    encode(text, info[:0x61])


if __name__ == '__main__':
    unittest.main()
