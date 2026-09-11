"""Final-package checks only; no old ROM, rebuild, or gameplay execution."""
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from package_v1_final import (DOCUMENTS, FINAL_SHA, LABEL, PATCH_SHA, PREVIOUS_SHA,
    RECEIPT_SHA, git, prepare, validate_documents, verify_final_receipt)


class FinalPackageTests(unittest.TestCase):
    def test_final_content_and_compatibility(self):
        archive, manifest, image = prepare(ROOT/'build/main-diagnostic-text-01',
            ROOT/'build/v1-current-01/final/build.json', git('rev-parse', 'HEAD').decode().strip())
        self.assertEqual(sha256(image), FINAL_SHA)
        self.assertEqual(manifest['label'], 'V1 Final')
        self.assertEqual(manifest['final_build_receipt_sha256'], RECEIPT_SHA)
        self.assertEqual(manifest['previous_candidate_sha256'], PREVIOUS_SHA)
        self.assertEqual(manifest['corrected_findings'], [f'V1-{i:02}' for i in range(1, 30)])
        self.assertEqual(manifest['new_findings'], ['V1-29'])
        self.assertEqual(manifest['new_japanese_strings_translated'], 13)
        self.assertEqual(manifest['new_unused_literals'], 1)
        self.assertFalse(manifest['save_compatibility']['migration_required'])
        self.assertEqual(manifest['save_compatibility']['previous_candidate'], 'V1RC8')
        for direction in ('forward', 'backward'):
            self.assertEqual(manifest['save_compatibility'][direction], 'expected, not independently verified')
        self.assertTrue(manifest['prior_human_acceptance']['ordinary_save_restart_reload_confirmed'])
        for key in ('original_hardware_verified', 'human_playthrough_complete',
                    'new_candidate_gameplay_run', 'public_release', 'fresh_full_chain_executed'):
            self.assertFalse(manifest[key])
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            self.assertEqual(set(bundle.namelist()), set(DOCUMENTS) |
                {'animal-forest-english.ups', 'manifest.json', 'SHA256SUMS'})
            self.assertEqual(len(bundle.namelist()), 10)
            self.assertEqual(sha256(bundle.read('animal-forest-english.ups')), PATCH_SHA)
            self.assertEqual(json.loads(bundle.read('manifest.json')), manifest)
            checksums = bundle.read('SHA256SUMS').decode().splitlines()
            self.assertEqual(len(checksums), 9)
            for line in checksums:
                digest, name = line.split('  ')
                self.assertEqual(sha256(bundle.read(name)), digest)
            for name, source in DOCUMENTS.items():
                self.assertEqual(manifest['bundled_source_sha256'][source], sha256(bundle.read(name)))
            self.assertIn(LABEL.encode(), bundle.read('README.md'))
            self.assertIn(b'--output "Animal Forest English V1 Final.z64"', bundle.read('README.md'))
            self.assertIn(b'source/build/v1-final/', bundle.read('TOOLCHAIN.md'))
            self.assertIn(b'109-stage', bundle.read('TOOLCHAIN.md'))
            self.assertNotIn(b'108-stage', bundle.read('TOOLCHAIN.md'))

    def test_rejects_changed_final_receipts(self):
        original = json.loads((ROOT/'build/main-diagnostic-text-01/fixes.json').read_bytes())
        for key, value in (('output_sha256', PREVIOUS_SHA), ('saved_format_changed', True),
                           ('worktree_modified', True), ('translated_records', 12)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_final_receipt(json.dumps({**original, key: value}).encode())
        with self.assertRaises(ValueError):
            verify_final_receipt(b'{}')

    def test_final_docs_reject_private_paths_and_missing_links(self):
        for raw in (b'[Guide](MISSING.md)', b'/home/example/rom.z64', b'/run/media/example/save.fla'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                validate_documents({'README.md': raw})


if __name__ == '__main__':
    unittest.main()
