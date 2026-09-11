"""RC5 archive contents, evidence scope, and refusal of an uncommitted replay."""
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from package_v1rc5 import FINAL_SHA, prepare


@unittest.skipUnless((ROOT/'build/rc4-menu-labels-03/fixes.json').is_file(), 'Committed RC5 replay required')
class RC5PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                                      capture_output=True, text=True).stdout.strip()

    def test_exact_members_checksums_and_bounded_evidence(self):
        package, manifest, image = prepare(ROOT/'build/rc4-menu-labels-03', self.native, self.revision)
        self.assertEqual(sha256(image), FINAL_SHA)
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            self.assertEqual(set(archive.namelist()), {'animal-forest-english.ups', 'manifest.json', 'README.md',
                'SOURCES.md', 'LICENSE-tooling.txt', 'apply_translation.py', 'aflib.py', 'SHA256SUMS'})
            for line in archive.read('SHA256SUMS').decode().splitlines():
                digest, name = line.split('  ')
                self.assertEqual(sha256(archive.read(name)), digest)
            self.assertEqual(json.loads(archive.read('manifest.json')), manifest)
            self.assertNotIn(b'](TOOLCHAIN.md)', archive.read('SOURCES.md'))
        self.assertFalse(manifest['public_release'])
        self.assertFalse(manifest['ordinary_menu_appearance_verified'])
        self.assertFalse(manifest['ordinary_save_restart_verified'])
        self.assertFalse(manifest['original_hardware_verified'])
        self.assertTrue(manifest['native_price_adapter_capture']['font_drawing_stubbed'])
        self.assertFalse(manifest['save_compatibility']['migration_required'])

    def test_rejects_uncommitted_cartridge_receipt_and_invalid_revision(self):
        with self.assertRaises(ValueError):
            prepare(ROOT/'build/rc4-menu-labels-02', self.native, self.revision)
        with self.assertRaises(ValueError):
            prepare(ROOT/'build/rc4-menu-labels-03', self.native, 'not-a-source-revision')


if __name__ == '__main__':
    unittest.main()
