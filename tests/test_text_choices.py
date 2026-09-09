"""Focused choice substitution, installed dependency, and cartridge checks."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from runtime_module import MODULE_VROM
from extended_items import VROM as ITEMS_VROM
import text_extension as t
import text_choices as c

ARTIFACT, BUILD, PRIOR = (ROOT/'build'/name for name in
                         ('text-choices', 'text-choices-pilot', 'text-extension-pilot'))
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


class ChoiceHostTests(unittest.TestCase):
    def test_sanitized_complete_fields_and_token_padding(self):
        with tempfile.TemporaryDirectory(prefix='af-choice-fields-') as directory:
            obj, binary = str(Path(directory)/'fields.o'), str(Path(directory)/'choices')
            flags = ['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                     '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                     '-I', str(ROOT/'overlays/text_extension')]
            subprocess.run(flags+['-Daf_text_extension_init=af_text_fields_init', '-c',
                str(ROOT/'overlays/text_extension/fields.c'), '-o', obj], check=True, timeout=30)
            subprocess.run(flags+[str(ROOT/'overlays/text_choices/choices.c'),
                str(ROOT/'tests/text_choices_harness.c'), obj, '-o', binary], check=True, timeout=30)
            subprocess.run([binary], check=True, timeout=30)


@unittest.skipUnless(ROM.is_file() and (ARTIFACT/'extension.json').is_file(), 'Local artifacts required')
class ChoiceArtifactTests(unittest.TestCase):
    def test_approved_profile_relocations_and_independent_build(self):
        artifact = json.loads((ARTIFACT/'extension.json').read_text())
        blob, loader = ((ARTIFACT/name).read_bytes() for name in ('blob.bin', 'loader.bin'))
        t.validate(blob, loader, artifact)
        for name in ('extension.json', 'extension.bin', 'relocation.bin', 'blob.bin', 'loader.bin'):
            self.assertEqual((ARTIFACT/name).read_bytes(), (ROOT/'build/text-choices-rebuild'/name).read_bytes())
        for part in (0, c.SYMBOLS['valid'], len(blob)-1):
            changed = bytearray(blob); changed[part] ^= 1
            with self.assertRaises(ValueError): t.validate(changed, loader, artifact)
        for change in ({'choices': 1}, {'choices': False}, {'imports': {}}):
            with self.assertRaises(ValueError): t.validate(blob, loader, {**artifact, **change})

    def test_dependency_rejection_is_atomic(self):
        native = ROM.read_bytes()
        prior = (ROOT/'build/stall-choices-pilot/animal-forest-halfwidth.z64').read_bytes()
        module = json.loads((ROOT/'build/stall-choices-pilot/build.json').read_text())['runtime_module']
        files = by_vrom(prior)
        original = {v: files[v].extract(prior) for v in (CODE_VROM, *c.ACTOR_VROMS)}
        extra = {v: files[v].extract(prior) for v in (MODULE_VROM, ITEMS_VROM, 0x03400000, *c.RESOURCE_HASHES)}
        evidence = t.install(native, dict(original), dict(extra), {}, module, ARTIFACT)
        self.assertEqual(evidence['additional_system_allocation_bytes'], 3263)
        self.assertEqual(evidence['choices']['capacity'], 20)
        for vrom, offset in ((CODE_VROM, c.ENTRY-CODE_RAM), (CODE_VROM, 0x80102AF0-CODE_RAM),
                             (CODE_VROM, 0x8009F03C-CODE_RAM), (MODULE_VROM, 40),
                             (0x02C00000, 33), (0x02E00000, 39)):
            replacements, additions = dict(original), dict(extra)
            target = replacements if vrom in replacements else additions
            changed = bytearray(target[vrom]); changed[offset] ^= 1; target[vrom] = bytes(changed)
            before = copy.deepcopy((replacements, additions))
            with self.assertRaises(ValueError):
                t.install(native, replacements, additions, {}, module, ARTIFACT)
            self.assertEqual((replacements, additions), before)
        missing = dict(original); del missing[c.ACTOR_VROMS[0]]
        with self.assertRaises(ValueError): t.install(native, missing, dict(extra), {}, module, ARTIFACT)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete choice build required')
    def test_complete_cartridge_retains_all_preceding_payloads(self):
        native, prior, built = (ROM.read_bytes(), (PRIOR/'animal-forest-halfwidth.z64').read_bytes(),
                                (BUILD/'animal-forest-halfwidth.z64').read_bytes())
        report, old_report = (json.loads((folder/'build.json').read_text()) for folder in (BUILD, PRIOR))
        t.verify_installation(built, native, report)
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        old, new = by_vrom(prior), by_vrom(built)
        self.assertEqual(set(old), set(new))
        for vrom in old:
            self.assertEqual(old[vrom].index, new[vrom].index)
            if vrom in (0x19D40, t.VROM): continue
            before, after = old[vrom].extract(prior), new[vrom].extract(built)
            if vrom == CODE_VROM:
                after = bytearray(after)
                after[t.SETTER-CODE_RAM:t.SETTER_END-CODE_RAM] = before[t.SETTER-CODE_RAM:t.SETTER_END-CODE_RAM]
            self.assertEqual(after, before, f'{vrom:08X}')
        for key in ('runtime_module', 'translation_edits', 'extended_font', 'extended_items',
                    'display_names', 'catchphrases', 'npc_mail_loader', 'noticeboard', 'stall_choices'):
            self.assertEqual(report[key], old_report[key], key)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete choice build required')
    def test_combined_accounting_retains_independent_pending_consumers(self):
        from translation_progress import measure
        ledger = measure(ROM.read_bytes(), (BUILD/'animal-forest-halfwidth.z64').read_bytes(),
                         json.loads((BUILD/'build.json').read_text()))
        result = ledger.summary()
        self.assertEqual(result['total_source_characters'], 751256)
        self.assertEqual(result['replaced_source_characters'], 720661)
        self.assertGreater(result['pending_application_records'], 0)
        for row in ledger.rows.values():
            for pending in row['pending_replacements']:
                self.assertNotIn('Shared choices', str(pending))


if __name__ == '__main__': unittest.main()
