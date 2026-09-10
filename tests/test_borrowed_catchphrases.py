"""Canonical borrowed phrases preserve owners, saved bytes, and existing guards."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, apply_ups
import text_extension as t
import text_catchphrases as p

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
OUT, BUILD, PRIOR = (ROOT/'build'/n for n in ('text-catchphrases', 'borrowed-catchphrases-pilot', 'letter-names-pilot'))


class BorrowedHostTests(unittest.TestCase):
    def test_policy_real_loader_guards_retention_and_atomic_startup(self):
        with tempfile.TemporaryDirectory(prefix='af-borrowed-') as directory:
            target = str(Path(directory)/'check')
            sources = ('overlays/text_catchphrases/phrases.c', 'runtime/catchphrase.c',
                       'runtime/catchphrase_fields.c', 'tests/catchphrase_mock.c', 'tests/borrowed_catchphrases_check.c')
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I', str(ROOT/'runtime'),
                '-I', str(ROOT/'overlays/text_extension'), *[str(ROOT/n) for n in sources], '-o', target],
                check=True, capture_output=True, timeout=30)
            subprocess.run([target], check=True, capture_output=True, timeout=10)


@unittest.skipUnless((OUT/'extension.json').is_file(), 'Compiled borrowed-phrase variant required')
class BorrowedArtifactTests(unittest.TestCase):
    def test_complete_profile_and_all_preceding_variants(self):
        for name in ('text-extension', 'text-choices', 'text-names', 'text-catchphrases'):
            out = ROOT/'build'/name
            t.validate((out/'blob.bin').read_bytes(), (out/'loader.bin').read_bytes(),
                       json.loads((out/'extension.json').read_text()))
        artifact = json.loads((OUT/'extension.json').read_text())
        for change in ({'borrowed': False}, {'borrowed': 1}, {'choices': False}, {'identities': False}, {'imports': {}}):
            with self.assertRaises(ValueError):
                t.validate((OUT/'blob.bin').read_bytes(), (OUT/'loader.bin').read_bytes(), {**artifact, **change})
        self.assertEqual(artifact['blob_bytes']+15, 4047)
        self.assertEqual(p.SYMBOLS['af_text_names_init'],160)

    def test_resource_call_and_canonical_owner_are_bound(self):
        from runtime_module import MODULE_VROM
        built = (PRIOR/'animal-forest-halfwidth.z64').read_bytes(); files = by_vrom(built)
        report = json.loads((PRIOR/'build.json').read_text()); module = report['runtime_module']
        additions = {v: files[v].extract(built) for v in (MODULE_VROM,0x02E00000)}
        evidence = p.verify_dependencies(additions,module)
        self.assertEqual(evidence['canonical_english'],'zzzzzz')
        for at in (p.CALL-0x801948E0, p.CALL-0x801948E0+4):
            bad = bytearray(additions[MODULE_VROM]); bad[at] ^= 1
            with self.assertRaises(ValueError): p.verify_dependencies({**additions, MODULE_VROM:bytes(bad)},module)
        bad = bytearray(additions[0x02E00000]); bad[-1] ^= 1
        with self.assertRaises(ValueError): p.verify_dependencies({**additions,0x02E00000:bytes(bad)},module)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete borrowed-phrase cartridge required')
class BorrowedCartridgeTests(unittest.TestCase):
    def test_all_prior_payloads_and_ups_are_retained(self):
        native = ROM.read_bytes(); built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes(); report = json.loads((BUILD/'build.json').read_text())
        t.verify_installation(built,native,report)
        from letter_names import verify_installation
        verify_installation(built,native,report)
        self.assertEqual(apply_ups(native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),built)
        files, old = by_vrom(built), by_vrom(prior);self.assertEqual(set(files),set(old))
        for vrom in files:
            before, after = old[vrom].extract(prior), files[vrom].extract(built)
            if vrom in (0x19D40,t.VROM): continue
            if vrom == CODE_VROM:
                after = bytearray(after)
                after[t.SETTER-CODE_RAM:t.SETTER_END-CODE_RAM] = before[t.SETTER-CODE_RAM:t.SETTER_END-CODE_RAM]
            self.assertEqual(after,before,hex(vrom))
        self.assertEqual(report['text_extension']['borrowed']['new_saved_bytes'],0)

    def test_combined_counter_requires_the_installed_borrowed_variant(self):
        from translation_progress import measure,pending_name_consumers
        from item_name_readers import resource_only_weight
        native = ROM.read_bytes();built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text());ledger = measure(native,built,report)
        self.assertEqual(ledger.summary()['total_source_characters'],751284)
        self.assertEqual(ledger.summary()['replaced_source_characters'],720689+35+
                         resource_only_weight(ledger,('extended_items','display_names','catchphrases')))
        self.assertGreater(resource_only_weight(ledger,('catchphrases',)),0)
        self.assertEqual(pending_name_consumers(report),{})
        broken = copy.deepcopy(report);broken['text_extension']['borrowed']['canonical_owner']='E0C5'
        with self.assertRaises(ValueError): t.verify_installation(built,native,broken)


if __name__ == '__main__': unittest.main()
