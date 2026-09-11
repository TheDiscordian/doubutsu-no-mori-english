"""Private V2 archive checks; no emulator or historical build is run."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from package_v2 import (BASE_SHA, BUILD_REVISION, DOCUMENTS, PATCH_SHA, ROM_SHA,
                        git, prepare, verify_receipt)


class V2PackageTests(unittest.TestCase):
    def test_exact_private_archive_and_compatibility(self):
        archive, manifest, image = prepare(ROOT/'build/v2-keyboard-05',
            git('rev-parse', 'HEAD').decode().strip())
        self.assertEqual(sha256(image), ROM_SHA)
        self.assertEqual(manifest['label'], 'V2 Development')
        self.assertEqual(manifest['cartridge_source_revision'], BUILD_REVISION)
        self.assertEqual(manifest['baseline_sha256'], BASE_SHA)
        for key in ('public_release', 'original_hardware_verified', 'human_playthrough_complete',
                    'exact_output_gameplay_tested', 'fresh_full_chain_executed', 'save_format_changed'):
            self.assertFalse(manifest[key])
        self.assertFalse(manifest['save_compatibility']['migration_required'])
        for direction in ('forward', 'backward'):
            self.assertEqual(manifest['save_compatibility'][direction], 'expected, not independently verified')
        self.assertEqual(manifest['save_bytes'], 131072)
        self.assertEqual(manifest['required_ram_bytes'], 0x800000)
        self.assertTrue(manifest['rtc_required'])
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            self.assertEqual(set(bundle.namelist()), set(DOCUMENTS) |
                             {'animal-forest-english.ups', 'manifest.json', 'SHA256SUMS'})
            self.assertEqual(len(bundle.namelist()), 11)
            self.assertEqual(sha256(bundle.read('animal-forest-english.ups')), PATCH_SHA)
            self.assertEqual(json.loads(bundle.read('manifest.json')), manifest)
            for line in bundle.read('SHA256SUMS').decode().splitlines():
                digest, name = line.split('  ')
                self.assertEqual(sha256(bundle.read(name)), digest)
            for name, source in DOCUMENTS.items():
                self.assertEqual(manifest['bundled_source_sha256'][source], sha256(bundle.read(name)))
            self.assertIn(b'--output "Animal Forest English V2 Development.z64"', bundle.read('README.md'))
            self.assertIn(b'python3 tools/keyboard_v2.py', bundle.read('TOOLCHAIN.md'))
            self.assertIn(b'source/build/v1-final/', bundle.read('V1_SOURCE_BUILD.md'))

    def test_changed_receipt_rejected(self):
        original = json.loads((ROOT/'build/v2-keyboard-05/build.json').read_bytes())
        for key, value in (('output_sha256', BASE_SHA), ('public_release', True),
                           ('input_code_changed', True), ('save_format_changed', True)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                verify_receipt(json.dumps({**original, key: value}).encode())

    def test_changed_committed_cartridge_source_rejected(self):
        with patch('package_v2.git', return_value=b'changed source'):
            with self.assertRaisesRegex(ValueError, 'recorded revision'):
                verify_receipt((ROOT/'build/v2-keyboard-05/build.json').read_bytes())


if __name__ == '__main__':
    unittest.main()
