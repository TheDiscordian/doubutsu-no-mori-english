"""Checks for the new current package only; no old candidate or game execution."""
import io
import json
from pathlib import Path
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from package_v1_current import (BUILD_SHA, DOCUMENTS, FINAL_SHA, PREVIOUS_SHA,
    git, prepare, validate_documents, verify_build_report)


@unittest.skipUnless((ROOT/'build/v1-current-01/final/build.json').exists(),
                     'Completed current V1 build required')
class CurrentPackageTests(unittest.TestCase):
    def test_current_archive_and_offline_documents(self):
        archive, manifest, image = prepare(ROOT/'build/v1-current-01/final',
                                           git('rev-parse', 'HEAD').decode().strip())
        self.assertEqual(sha256(image), FINAL_SHA)
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            self.assertEqual(set(bundle.namelist()), set(DOCUMENTS) |
                {'animal-forest-english.ups', 'manifest.json', 'SHA256SUMS'})
            self.assertEqual(len(bundle.namelist()), 10)
            self.assertEqual(json.loads(bundle.read('manifest.json')), manifest)
            lines = bundle.read('SHA256SUMS').decode().splitlines()
            self.assertEqual(len(lines), 9)
            for line in lines:
                digest, name = line.split('  ')
                self.assertEqual(sha256(bundle.read(name)), digest)
            for name, source in DOCUMENTS.items():
                self.assertEqual(manifest['bundled_source_sha256'][source], sha256(bundle.read(name)))
            self.assertIn(b'](TOOLCHAIN.md)', bundle.read('SOURCES.md'))
            self.assertIn(b'--rom', bundle.read('README.md'))
            self.assertNotIn(b'https://github.com/TheDiscordian/', bundle.read('TOOLCHAIN.md'))
        self.assertEqual(manifest['build_report_sha256'], BUILD_SHA)
        self.assertEqual(manifest['previous_candidate_sha256'], PREVIOUS_SHA)
        self.assertEqual(manifest['new_findings'], ['V1-28'])
        self.assertFalse(manifest['save_compatibility']['migration_required'])
        for direction in ('forward', 'backward'):
            self.assertEqual(manifest['save_compatibility'][direction], 'expected, not independently verified')
        self.assertTrue(manifest['prior_human_acceptance']['ordinary_save_restart_reload_confirmed'])
        self.assertEqual(len(manifest['prior_human_acceptance']['confirmed_reported_findings']), 23)
        self.assertFalse(manifest['new_candidate_gameplay_run'])
        self.assertFalse(manifest['original_hardware_verified'])
        self.assertFalse(manifest['public_release'])

    def test_rejects_unrecorded_or_incomplete_build(self):
        original = (ROOT/'build/v1-current-01/final/build.json').read_bytes()
        for key, value in (('complete', False), ('source_revision', '0'*40),
                           ('output_sha256', PREVIOUS_SHA), ('save_format_changed', True)):
            report = json.loads(original)
            report[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_build_report(json.dumps(report).encode())
        with self.assertRaises(ValueError):
            verify_build_report(b'{}')

    def test_rejects_missing_offline_links_and_private_machine_paths(self):
        for raw in (b'[Guide](MISSING.md)', b'Input: /home/example/input.rom',
                    b'Save: /run/media/example/save.fla'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                validate_documents({'README.md': raw})


if __name__ == '__main__':
    unittest.main()
