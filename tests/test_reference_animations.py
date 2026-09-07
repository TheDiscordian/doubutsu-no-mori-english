"""Animation approval never becomes a general actor/field/control exemption."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, CODE_VROM
from gc_adapter import adapt_reference, remove_redundant_article_suppression
from reference_animations import (ResidentAnimationPermit, animation_permit, verify_animation_reference,
                                  validate_animation_approval, verify_native_consumer, NPC_VROM,
                                  NPC_RELOCATION, ALLOWED_VALUES)
from reference_fields import ReferenceFieldPermit
from reference_matches import load_matches
from runtime_module import module_command_info
from textcodec import encode, tokenize
from textbanks import banks
from textvalidate import validate_entry
from test_retail import ROM_PATH


class AnimationApprovalTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[9] = self.info[12] = (5, 0)
        self.info[3] = (3, 0)
        self.source = bytes.fromhex('417F090000157F00')
        self.output = bytes.fromhex('427F0900000B7F090000157F00')

    def permit(self, output=None, source=None):
        return ResidentAnimationPermit(sha256(source or self.source), sha256(output or self.output),
                                       'native_resident_talk')

    def check(self, output=None, source=None, **kwargs):
        validate_entry(source or self.source, output or self.output, self.info,
                       'message', 'reference_layout', resident_runtime=True,
                       animation_permit=self.permit(output, source), **kwargs)

    def test_only_approved_animation_delivery_changes(self):
        self.check()
        with self.assertRaisesRegex(ValueError, 'Control signature'):
            validate_entry(self.source, self.output, self.info, 'message', 'reference_layout', resident_runtime=True)
        for command in ('7F09010001', '7F0C000001', '7F09020005', '7F19'):
            with self.assertRaisesRegex(ValueError, 'Control signature'):
                self.check(output=self.output[:-2]+bytes.fromhex(command)+self.output[-2:])
        with self.assertRaisesRegex(ValueError, 'field absent'):
            self.check(output=self.output[:-2]+bytes.fromhex('7F1A')+self.output[-2:])

    def test_values_context_hash_and_combined_permits_are_bounded(self):
        for value in (0, 24, 42, 253, 254, 256, 65535):
            with self.assertRaisesRegex(ValueError, 'standing-expression'):
                self.check(output=b'B\x7f\x09\x00'+value.to_bytes(2, 'big')+b'\x7f\x00')
        self.check(output=bytes.fromhex('427F090000FF7F00'))
        with self.assertRaisesRegex(ValueError, 'changed expression sequence'):
            self.check(output=self.source)
        for permit in (None, {}, self.permit(b'changed'),
                       ResidentAnimationPermit(sha256(self.source), sha256(self.output), 'event_actor')):
            with self.assertRaises(ValueError):
                validate_entry(self.source, self.output, self.info, 'message', 'reference_layout',
                               resident_runtime=True, animation_permit=permit)
        with self.assertRaisesRegex(ValueError, 'resident-context'):
            self.check(field_permit=ReferenceFieldPermit(sha256(self.source), sha256(self.output), frozenset({0x1A})))
        with self.assertRaisesRegex(ValueError, 'resident-context'):
            validate_entry(self.source, self.output, self.info, 'message', 'reference_layout',
                           animation_permit=self.permit())

    def test_reference_animation_option_keeps_values_without_weakening_validation(self):
        source = bytes.fromhex('417F090000157F00')
        reference = 'B{cmd:7F0900000B}{cmd:7F00}'
        default, _ = adapt_reference(reference, source, self.info, 'reference_layout', True)
        retained, _ = adapt_reference(reference, source, self.info, 'reference_layout', True,
                                      retain_resident_animations=True)
        self.assertEqual(encode(default, self.info), source.replace(b'A', b'B'))
        self.assertEqual(retained, reference)
        with self.assertRaisesRegex(ValueError, 'Control signature'):
            validate_entry(source, encode(retained, self.info), self.info, 'message', 'reference_layout', resident_runtime=True)

    def test_complete_record_schema_and_reference_binding(self):
        reference = {'id': 'message:0000', 'text': 'B{cmd:7F0900000B}{cmd:7F09000015}{cmd:7F00}',
                     'sha256': sha256(self.output)}
        record = {'id': 'message:0000', 'reference_id': reference['id'], 'source_sha256': sha256(self.source),
                  'reference_sha256': reference['sha256'], 'resident_animations': {
                      'context': 'native_resident_talk', 'adapted_sha256': sha256(self.output)}}
        verify_animation_reference(reference, self.source, record, self.info)
        self.assertEqual(animation_permit(record['id'], self.source, self.output, {record['id']: record}), self.permit())
        for key in ('controller', 'native_choices', 'native_actor_request', 'available_fields',
                    'speaker_catchphrase', 'native_equivalent_id'):
            with self.assertRaisesRegex(ValueError, 'approval'):
                validate_animation_approval({**record, key: {}})
        for change in ({'context': 'event'}, {'adapted_sha256': '0'}, {'extra': True}):
            altered = deepcopy(record); altered['resident_animations'].update(change)
            with self.assertRaisesRegex(ValueError, 'approval'): validate_animation_approval(altered)
        with self.assertRaisesRegex(ValueError, 'Stale'):
            verify_animation_reference({**reference, 'text': 'changed'}, self.source, record, self.info)
        with self.assertRaisesRegex(ValueError, 'complete approval'):
            animation_permit(record['id'], self.source, b'changed', {record['id']: record})
        self.assertIsNone(animation_permit('message:0001', self.source, self.output, {record['id']: record}))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains local')
class RetailAnimationApprovalTests(unittest.TestCase):
    def test_exact_native_indexed_base_and_exclusive_end_relocations(self):
        from types import SimpleNamespace
        from npc_mail_show import relocate_verified_data
        from reference_animations import NPC_RAM, SECTIONS, RELOCATION_CONSTANTS
        data, reloc = verify_native_consumer(ROM_PATH.read_bytes())
        spec = SimpleNamespace(ram=NPC_RAM, file_bytes=sum(SECTIONS[:3]), sections=SECTIONS,
                               resident_bytes=sum(SECTIONS[:4]))
        for base in (0x801A0000, 0x802F8010):
            with self.assertRaisesRegex(ValueError, 'outside'):
                relocate_verified_data(spec, data, reloc, base)
            output = relocate_verified_data(spec, data, reloc, base, address_constants=RELOCATION_CONSTANTS)
            self.assertEqual(len(output), spec.resident_bytes)
            self.assertEqual(output[spec.file_bytes:], bytes(SECTIONS[3]))
        for item in (0xD01E, 0xD03A, 0xD03B, 0xD03C):
            self.assertTrue(NPC_RAM+SECTIONS[0] <= RELOCATION_CONSTANTS[0]+2*item < NPC_RAM+spec.file_bytes)
        self.assertEqual(RELOCATION_CONSTANTS[1], NPC_RAM+spec.resident_bytes)

    def test_all_approved_references_retain_complete_english_and_other_controls(self):
        rom = ROM_PATH.read_bytes(); info = module_command_info(rom)
        source = next(b for b in banks(rom) if b.name == 'message').entries()
        gc_path = ROOT/'build/gamecube/text/message.jsonl'
        if not gc_path.is_file(): self.skipTest('English disc extraction remains local')
        gc = {r['id']: r for r in map(json.loads, gc_path.read_text().splitlines())}
        matches = load_matches(ROOT/'translations/reference_matches.json')
        approved = [r for r in matches.values() if 'resident_animations' in r]
        self.assertEqual(len(approved), 83)
        article_adaptations = set()
        for record in approved:
            original = source[int(record['id'][8:], 16)]
            reference = gc[record['reference_id']]
            verify_animation_reference(reference, original, record, info)
            text, _ = adapt_reference(reference['text'], original, info, 'reference_layout', True,
                                      retain_resident_animations=True)
            output = encode(text, info)
            self.assertEqual(text, remove_redundant_article_suppression(reference['text'])[0], record['id'])
            if text != reference['text']:
                article_adaptations.add(record['id'])
            validate_entry(original, output, info, 'message', 'reference_layout', resident_runtime=True,
                           animation_permit=animation_permit(record['id'], original, output, matches))
        self.assertEqual(article_adaptations, {'message:0156', 'message:0158', 'message:2373', 'message:2580'})

    def test_native_consumer_tables_and_installed_source_are_unchanged(self):
        import struct
        from aflib import by_vrom
        from reference_animations import TABLES, NPC_RAM
        rom = ROM_PATH.read_bytes()
        data, reloc = verify_native_consumer(rom)
        self.assertEqual(len(data), 66400)
        for table in TABLES:
            values = struct.unpack_from('>42i', data, table-NPC_RAM)
            self.assertEqual(values[0], -1)
            self.assertTrue(all(0 <= values[i] < 232 for i in ALLOWED_VALUES if i != 255))
        for vrom, raw in ((NPC_VROM, data), (NPC_RELOCATION, reloc),
                          (CODE_VROM, by_vrom(rom)[CODE_VROM].extract(rom))):
            changed = bytearray(raw)
            changed[0 if vrom != CODE_VROM else 0x8007B44C-0x80051A80] ^= 1
            with self.assertRaises(ValueError): verify_native_consumer(rom, {vrom: bytes(changed)})

    def test_builder_rejects_changed_approved_text_independently(self):
        from build import apply_translations
        matches = load_matches(ROOT/'translations/reference_matches.json')
        record = matches['message:04D3']
        edit = {'id': record['id'], 'source_sha256': record['source_sha256'],
                'translation': 'Changed{cmd:7F00}', 'control_policy': 'reference_layout'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'
            path.write_text(json.dumps([edit]))
            with self.assertRaisesRegex(ValueError, 'differs from its complete approval'):
                apply_translations(ROM_PATH.read_bytes(), {}, path)


if __name__ == '__main__':
    unittest.main()
