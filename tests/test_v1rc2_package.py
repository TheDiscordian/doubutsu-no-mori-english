"""The combined RC2 package binds its replay and native evidence without a ROM."""
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
import package_v1rc2 as package

FOLDER=ROOT/'build/v1rc2-rebuild-01'


@unittest.skipUnless((FOLDER/'fixes.json').is_file(),'Complete RC2 replay required')
class V1RC2PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.evidence=(ROOT/'build/v1rc1-keyboard-native-02/results.json').read_bytes()

    def test_patch_only_contents_checksums_and_explicit_acceptance_limits(self):
        data,manifest,image=package.prepare(FOLDER,self.source,'a'*40,self.evidence)
        self.assertEqual(sha256(image),package.FINAL_SHA)
        self.assertEqual(manifest['label'],'V1RC2')
        self.assertEqual(len(manifest['corrected_findings']),16)
        self.assertEqual(manifest['required_ram_bytes'],0x800000)
        self.assertTrue(manifest['keyboard_background_native_test_complete'])
        for key in ('public_release','complete_v1','original_hardware_verified','human_playthrough_complete',
                    'ordinary_save_restart_verified','keyboard_ordinary_appearance_verified',
                    'full_regression_passed','save_layout_changed','v2_keyboard_redesign_included'):
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

    def test_missing_stages_bad_revision_and_incomplete_native_evidence_reject(self):
        with patch.object(package,'STAGES',package.STAGES[:-1]),self.assertRaises(ValueError):
            package.prepare(FOLDER,self.source,'a'*40,self.evidence)
        with self.assertRaises(ValueError):package.prepare(FOLDER,self.source,'uncommitted',self.evidence)
        evidence=json.loads(self.evidence);evidence[0]['rom_sha256']='0'*64
        with self.assertRaises(ValueError):
            package.prepare(FOLDER,self.source,'a'*40,json.dumps(evidence).encode())
        evidence=json.loads(self.evidence)
        evidence=[r for r in evidence if 'loaded_state' not in r]
        with self.assertRaises(ValueError):
            package.prepare(FOLDER,self.source,'a'*40,json.dumps(evidence).encode())


if __name__=='__main__':unittest.main()
