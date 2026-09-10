"""Shared-word identity, deferred publication, and both installed consumers."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, replace_dma, sha256
from build import apply_translations
from fortune_strings import STRING_RELOCATION, source_entries
from mail_catalog import VROM as CATALOG_VROM, install as install_catalog
from mail_view_patch import VROM as READER_VROM, RELOC_VROM, install as install_reader
from native_species import NATIVE_ID, NATIVE_SHA256, DONOR, ENGLISH, SOURCE
from npc_mail_capture import HOOKS, DESIGN_WORD_HASH, WORD_HASH
from npc_mail_delivery import CREATOR_CALL, FAILURE_BRANCH, ARGUMENT_MOVE
from npc_mail_loader import VROM as CREATOR_VROM, CONFIG_OFFSET, install as install_creator
from npc_mail_loader_test_scenario import scenario as loader_scenario
from npc_mail_words import unpack_words
from resident_words import candidates as resident_candidates, SPEC
from runtime_module import MODULE_VROM, add_runtime_module, module_command_info
from shared_npc_words import (IDS, IDENTITIES, ORDINARY_BASES, ENTRY_REFERENCES,
    candidates, validated_values, verify_values, caller_evidence, verify_consumers, install)
from textbanks import Bank, banks
from textcodec import encode
from resident_word_smoke import random_cases, RANDOM_BASES
from test_retail import ROM_PATH

MODULE = ROOT/'build/notice-seasonal-runtime'
CREATOR = ROOT/'build/shared-npc-capture-runtime-followup-01'
CATALOG = ROOT/'build/mail-catalog'


class SharedWordCommandTests(unittest.TestCase):
    def test_native_batch_covers_every_shared_ordinary_family_in_valid_item_slots(self):
        self.assertEqual(random_cases(), tuple(enumerate(RANDOM_BASES)))
        self.assertEqual({base for _, base in random_cases(True)}, set(RANDOM_BASES+ORDINARY_BASES))
        self.assertEqual(len(random_cases(True))*32, 288)
        self.assertTrue(all(0<=slot<5 for slot, _ in random_cases(True)))

    def test_missing_flags_reject_before_reading_inputs(self):
        for tool, extra in (('build.py', []), ('build.py', ['--english-resident-words', '--runtime-module', 'not-read']),
                            ('reference_candidates.py', []), ('reference_candidates.py', ['--runtime-module', 'not-read'])):
            result = subprocess.run([sys.executable, str(ROOT/'tools'/tool), '--rom', 'not-read.z64',
                '--english-shared-npc-words', *extra], capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)
            self.assertIn('--english-shared-npc-words requires', result.stderr)


@unittest.skipUnless(ROM_PATH.is_file() and all((p/name).is_file() for p, name in (
    (MODULE, 'module.json'), (CREATOR, 'overlay.json'), (CATALOG, 'catalog.json'),
    (ROOT/'build/gamecube/text', 'string.jsonl'), (ROOT/'build/inventory', 'string.jsonl'))),
    'Verified local ROM, English references, and compiled resources required')
class SharedWordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.info = module_command_info(cls.rom)
        cls.refs = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
        cls.inventory = {r['id']: r for r in map(json.loads, (ROOT/'build/inventory/string.jsonl').read_text().splitlines())}
        cls.edits = candidates(cls.rom, cls.refs, cls.inventory, cls.info)
        cls.resident = resident_candidates(cls.rom, cls.refs, cls.inventory, cls.info)
        cls.all_edits = list(cls.resident.values())+list(cls.edits.values())
        cls.originals = source_entries(cls.rom)
        cls.base = {}
        cls.additions, cls.module = add_runtime_module(cls.rom, cls.base, MODULE)
        with tempfile.TemporaryDirectory(prefix='af-shared-words-') as directory:
            path = Path(directory)/'edits.json'
            path.write_text(json.dumps(cls.all_edits))
            cls.count, cls.mapping = apply_translations(cls.rom, cls.base, path, runtime_module=MODULE,
                module_additions=cls.additions, english_resident_words=True, defer_shared_npc_words=True)
        install_reader(cls.rom, cls.base, cls.additions, cls.module, snapshots=True)
        install_catalog(cls.rom, cls.additions, cls.module, CATALOG)
        install_creator(cls.rom, cls.base, cls.additions, cls.module, CREATOR)

    def fixture(self):
        return dict(self.base), dict(self.additions), deepcopy(self.module)

    def bank(self, replacements):
        return Bank('string', 0xD16000, 0xD18000, replacements[0xD16000], replacements[0xD18000])

    def test_shared_bank_rejects_mismatched_valid_creator_word_profile(self):
        # Exercise the current source-built composition before later notice
        # configuration, not a historical cartridge rejected by source guards.
        replacements, additions, module = self.fixture()
        self.assertEqual(module['npc_mail_loader']['overlay']['word_sha256'], DESIGN_WORD_HASH)
        before = (dict(replacements), dict(additions), deepcopy(module))
        verify_consumers(self.rom, replacements, additions, module,
                         expected_word_hash=DESIGN_WORD_HASH)
        with self.assertRaisesRegex(ValueError, 'matching installed NPC word profile'):
            verify_consumers(self.rom, replacements, additions, module,
                             expected_word_hash=WORD_HASH)
        self.assertEqual((replacements, additions, module), before)

    def reject(self, fixture, edits=None):
        before = deepcopy(fixture)
        with self.assertRaises(ValueError):
            install(self.rom, *fixture, self.all_edits if edits is None else edits, self.info)
        self.assertEqual(fixture, before)

    def test_all_families_match_complete_resource_and_source_bound_species_correction(self):
        values = validated_values(self.rom, self.all_edits, self.info)
        resource = unpack_words((CREATOR/'words.bin').read_bytes(), DESIGN_WORD_HASH)
        self.assertEqual(len(values), 352)
        self.assertEqual(sum(len(v)>10 for v in values.values()), 82)
        self.assertEqual(len(ORDINARY_BASES)*32, 160)
        corrected = []
        for id, (native, reference, slot), word in zip(IDS, IDENTITIES, resource):
            self.assertEqual(values[id], word.text)
            donor = encode(self.refs[f'string:{reference:04X}']['text'], self.info)
            self.assertEqual(donor, encode(self.inventory[id]['legacy'], self.info))
            if native == NATIVE_ID:
                self.assertEqual(sha256(self.originals[native]), NATIVE_SHA256)
                self.assertEqual((donor, values[id]), (DONOR, ENGLISH))
                self.assertEqual(self.edits[id]['provenance']['source'], SOURCE)
                self.assertEqual(self.edits[id]['provenance']['match_basis'],
                                 'reviewed_native_species_correction')
                corrected.append(id)
            else:
                self.assertEqual(values[id], donor)
            self.assertEqual(self.edits[id]['provenance']['word_resource_sha256'], DESIGN_WORD_HASH)
            self.assertEqual((native, reference, slot), (word.native_id, word.reference_id, word.slot))
        self.assertEqual(corrected, ['string:021A'])
        self.assertEqual({reference-native for native, reference, _ in IDENTITIES}, {0, 0x488, 0x494})
        evidence = caller_evidence(self.rom)
        self.assertEqual(set(evidence['entry_references']), {f'{at:08X}' for at in ENTRY_REFERENCES})
        self.assertTrue(evidence['saved_catchphrase_and_special_name_ids_disjoint'])

    def test_partial_duplicate_stale_shortened_reordered_or_command_values_reject(self):
        edits = list(self.edits.values())
        for bad in (edits[:-1], edits+[edits[0]]):
            with self.assertRaisesRegex(ValueError, 'complete unique'):
                validated_values(self.rom, bad, self.info)
        for field, value in (('source_sha256', '0'*64), ('translation', 'short'),
                             ('control_policy', 'presentation'), ('translation', ''), ('translation', 'x'*17)):
            bad = deepcopy(edits); bad[0][field] = value
            with self.assertRaises(ValueError): validated_values(self.rom, bad, self.info)
        values = list(validated_values(self.rom, edits, self.info).values())
        for first in (b'\x7f\x02', b'\n', b'', b'x'*17):
            with self.assertRaises(ValueError): verify_values([first]+values[1:])
        values[0], values[1] = values[1], values[0]
        with self.assertRaises(ValueError): verify_values(values)

    def test_explicit_fish_insect_mapping_and_complete_agreement_are_required(self):
        for selected, id, field, value in (
                ('refs', 'string:06A1', 'text', 'short'), ('refs', 'string:0679', 'sha256', '0'*64),
                ('inventory', 'string:0219', 'legacy', 'short'),
                ('inventory', 'string:01E5', 'source_sha256', '0'*64)):
            refs, inventory = deepcopy(self.refs), deepcopy(self.inventory)
            (refs if selected=='refs' else inventory)[id][field] = value
            with self.assertRaises(ValueError): candidates(self.rom, refs, inventory, self.info)

    def test_deferred_bank_keeps_all_shared_words_native_until_final_publication(self):
        self.assertEqual(self.count, 136)
        self.assertEqual(self.mapping, {0xD16000: STRING_RELOCATION[0]})
        before = self.bank(self.base).entries()
        for native, _, _ in IDENTITIES: self.assertEqual(before[native], self.originals[native])
        replacements, additions, module = self.fixture()
        report = install(self.rom, replacements, additions, module, self.all_edits, self.info)
        entries = self.bank(replacements).entries()
        self.assertEqual(report['translation_edits'], 352)
        self.assertEqual(report['words_exceeding_ten_bytes'], 82)
        self.assertEqual(report['word_resource_sha256'], DESIGN_WORD_HASH)
        for index, value in enumerate(entries):
            id = f'string:{index:04X}'
            expected = encode(self.edits[id]['translation'], self.info) if id in self.edits else before[index]
            self.assertEqual(value, expected)
        self.assertEqual(len(entries), len(self.originals))
        self.assertEqual(additions, self.additions); self.assertEqual(module, self.module)
        self.assertEqual({key for key in replacements if replacements[key] != self.base[key]}, {0xD16000, 0xD18000})
        self.assertEqual(len(replacements[0xD16000]) % 16, 0)
        self.reject((replacements, additions, module))

    def test_missing_creator_reader_catalog_or_resident_dependency_rejects_atomically(self):
        for key in (CREATOR_VROM, CATALOG_VROM, MODULE_VROM, READER_VROM, RELOC_VROM, SPEC.vrom, 0xD16000, 0xD18000):
            fixture = self.fixture()
            target = fixture[0] if key in fixture[0] else fixture[1]
            target.pop(key)
            with self.subTest(resource=key): self.reject(fixture)
        for key, value in (('source_sha256', '0'*64), ('runtime_sources', {}), ('npc_mail_loader', {})):
            fixture = self.fixture(); fixture[2][key] = value; self.reject(fixture)

    def test_every_hook_failure_gate_and_native_function_is_required(self):
        for address in [at for at, _, _ in HOOKS]+[CREATOR_CALL, FAILURE_BRANCH, ARGUMENT_MOVE,
                0x800A92D0, 0x800A9028, STRING_RELOCATION[1]]:
            fixture = self.fixture(); code = bytearray(fixture[0][CODE_VROM])
            code[address-CODE_RAM] ^= 1; fixture[0][CODE_VROM] = bytes(code)
            with self.subTest(address=address): self.reject(fixture)

    def test_changed_config_resources_actor_or_resident_words_reject_without_publication(self):
        for key, offset in ((MODULE_VROM, CONFIG_OFFSET), (MODULE_VROM, 512), (MODULE_VROM, 68),
                            (CREATOR_VROM, -1), (CATALOG_VROM, -1), (READER_VROM, -1), (SPEC.vrom, 0)):
            fixture = self.fixture(); target = fixture[0] if key in fixture[0] else fixture[1]
            data = bytearray(target[key]); data[offset] ^= 1; target[key] = bytes(data)
            self.reject(fixture)
        fixture = self.fixture(); bank = self.bank(fixture[0]); entries = bank.entries(); entries[0x414] = b'short'
        fixture[0][0xD16000], fixture[0][0xD18000] = bank.rebuild(entries, allow_expand=True)
        self.reject(fixture)

    def test_no_global_capacity_exception_and_missing_deferral_dependencies_fail(self):
        with tempfile.TemporaryDirectory(prefix='af-shared-words-') as directory:
            path = Path(directory)/'edits.json'; path.write_text(json.dumps(self.all_edits))
            for flags in ({'defer_shared_npc_words': True},
                          {'defer_shared_npc_words': True, 'runtime_module': MODULE}):
                with self.assertRaisesRegex(ValueError, 'resident-word runtime'):
                    apply_translations(self.rom, {}, path, **flags)
            replacements = {}; additions, _ = add_runtime_module(self.rom, replacements, MODULE)
            with self.assertRaisesRegex(ValueError, 'entry budget'):
                apply_translations(self.rom, replacements, path, runtime_module=MODULE,
                                   module_additions=additions, english_resident_words=True)

    def test_cartridge_loader_fixture_reads_complete_relocated_bank(self):
        replacements, additions, module = self.fixture()
        install(self.rom, replacements, additions, module, self.all_edits, self.info)
        rom = replace_dma(self.rom, replacements, self.mapping, additions)
        actions = loader_scenario(rom, self.rom, module)
        request = actions[3]['test_npc_mail_loader']
        self.assertEqual(request['native_words'], [v.hex() for v in self.bank(replacements).entries()])
        self.assertGreater(len(replacements[0xD16000]), len(next(b for b in banks(self.rom) if b.name=='string').data))


if __name__ == '__main__': unittest.main()
