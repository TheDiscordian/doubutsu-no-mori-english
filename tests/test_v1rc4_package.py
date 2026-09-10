"""RC4 packaging requires the corrected cartridge and actual native evidence."""
import io
import json
from pathlib import Path
import re
import sys
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from apply_translation import apply_bundle
from package_v1rc4 import prepare
from rebuild_v1rc4 import FINAL_SHA


@unittest.skipUnless((ROOT/'build/v1rc4-rebuild-01/fixes.json').is_file(),'Committed RC4 replay required')
class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/v1rc3/Animal Forest English V1RC3.z64').read_bytes()
        cls.parent=(ROOT/'build/v1rc3/manifest.json').read_bytes()
        cls.directory=ROOT/'build/v1rc4-rebuild-01'
        cls.revision=json.loads((cls.directory/'fixes.json').read_text())['source_revision']

    def test_complete_patch_archive_and_scoped_save_evidence(self):
        package,manifest,image=prepare(self.directory,self.native,self.base,self.revision,self.parent)
        self.assertEqual(sha256(image),FINAL_SHA)
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            self.assertFalse(any(name.endswith(('.z64','.fla','.flash','.bs1')) for name in archive.namelist()))
            self.assertEqual(apply_bundle(self.native,archive.read('animal-forest-english.ups'),manifest),image)
            self.assertEqual(json.loads(archive.read('manifest.json')),manifest)
            self.assertIn(
                f'https://github.com/TheDiscordian/doubutsu-no-mori-english/blob/{self.revision}/docs/TOOLCHAIN.md',
                archive.read('SOURCES.md').decode())
            for name in ('README.md', 'SOURCES.md'):
                for target in re.findall(r'\]\(([^)]+)\)', archive.read(name).decode()):
                    if not target.startswith(('https://', 'http://', '#')):
                        self.assertIn(target.split('#', 1)[0], archive.namelist())
            checksums = archive.read('SHA256SUMS').decode().splitlines()
            self.assertEqual(len(checksums), len(archive.namelist())-1)
            for line in checksums:
                digest, name = line.split('  ', 1)
                self.assertEqual(sha256(archive.read(name)), digest)
        self.assertEqual(manifest['native_loading_movement_memory_evidence']['load']['scene_free_bytes'],25216)
        self.assertFalse(manifest['ordinary_save_restart_verified'])
        self.assertEqual(manifest['save_compatibility']['forward'],'unverified')
        self.assertEqual(manifest['save_compatibility']['backward'],'unverified')
        self.assertFalse(manifest['save_layout_changed'])

    def test_unknown_parent_or_cartridge_cannot_be_packaged(self):
        for base,parent in ((self.native,self.parent),(self.base,self.parent+b' ')):
            with self.assertRaises(ValueError):
                prepare(self.directory,self.native,base,self.revision,parent)

    def test_missing_native_evidence_blocks_handoff(self):
        with patch('package_v1rc4.verify_native',side_effect=ValueError('Missing checked native load')):
            with self.assertRaisesRegex(ValueError,'Missing checked native load'):
                prepare(self.directory,self.native,self.base,self.revision,self.parent)


if __name__=='__main__':unittest.main()
