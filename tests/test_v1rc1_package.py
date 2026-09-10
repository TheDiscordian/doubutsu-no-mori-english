"""V1RC1 is an exact patch-only bundle with explicit testing limits."""
import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
import package_v1rc1 as package


@unittest.skipUnless((ROOT/'build/v1-fixes-rebuild-01/fixes.json').is_file(),'Complete correction replay required')
class V1RC1PackageTests(unittest.TestCase):
    def test_exact_patch_only_members_checksums_and_honest_limits(self):
        source=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        data,manifest,image=package.prepare(ROOT/'build/v1-fixes-rebuild-01',source,'a'*40)
        self.assertEqual(manifest['label'],'V1RC1');self.assertEqual(sha256(image),package.FINAL_SHA)
        self.assertEqual(manifest['required_ram_bytes'],0x800000)
        self.assertEqual(len(manifest['corrected_findings']),12)
        for key in ('public_release','complete_v1','original_hardware_verified','human_playthrough_complete',
                    'ordinary_save_restart_verified','keyboard_background_native_test_complete',
                    'embedded_warning_native_drawing_verified','save_layout_changed'):
            self.assertFalse(manifest[key])
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            self.assertEqual(set(bundle.namelist()),{'animal-forest-english.ups','manifest.json','README.md',
                'SOURCES.md','LICENSE-tooling.txt','apply_translation.py','aflib.py','SHA256SUMS'})
            self.assertEqual(json.loads(bundle.read('manifest.json')),manifest)
            for row in bundle.read('SHA256SUMS').decode().splitlines():
                digest,name=row.split('  ',1);self.assertEqual(sha256(bundle.read(name)),digest)
            for name in bundle.namelist():
                self.assertFalse(name.endswith(('.z64','.v64','.n64','.iso','.flash','.pak','.rtc')))
                if name.endswith(('.md','.py','.txt','.json')):
                    self.assertNotIn(b'/home/discordian',bundle.read(name))
            self.assertIn(b'not only the reported Limberg',bundle.read('README.md'))

    def test_unapproved_output_incomplete_stages_and_revision_fail(self):
        source=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        folder=ROOT/'build/v1-fixes-rebuild-01'
        with patch.object(package,'FINAL_SHA','0'*64),self.assertRaises(ValueError):
            package.prepare(folder,source,'a'*40)
        with patch.object(package,'STAGES',package.STAGES[:-1]),self.assertRaises(ValueError):
            package.prepare(folder,source,'a'*40)
        with self.assertRaises(ValueError):package.prepare(folder,source,'uncommitted')


if __name__=='__main__':unittest.main()
