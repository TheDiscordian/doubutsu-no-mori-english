"""The private RC3 package binds both corrections and keeps its acceptance limits."""
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
import package_v1rc3 as package

FOLDER=ROOT/'build/v1rc3-rebuild-01'

@unittest.skipUnless((FOLDER/'fixes.json').is_file(),'Complete RC3 replay required')
class V1RC3PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.evidence=[(ROOT/'build'/name/'results.json').read_bytes() for name in
            ('font-edges-native-02','transition-native-before-02','transition-native-after-02')]

    def test_patch_only_members_hashes_and_acceptance(self):
        data,manifest,image=package.prepare(FOLDER,self.source,'a'*40,*self.evidence)
        self.assertEqual(sha256(image),package.FINAL_SHA)
        self.assertEqual(manifest['label'],'V1RC3')
        self.assertEqual(len(manifest['corrected_findings']),18)
        self.assertEqual(manifest['required_ram_bytes'],0x800000)
        self.assertTrue(manifest['controlled_font_and_transition_checks_complete'])
        self.assertTrue(manifest['font_test_resources_retained'])
        self.assertNotEqual(manifest['font_native_test_rom_sha256'],manifest['output_sha256'])
        for key in ('public_release','complete_v1','original_hardware_verified','human_playthrough_complete',
                    'ordinary_save_restart_verified','full_regression_passed','save_layout_changed',
                    'v2_keyboard_redesign_included'):
            self.assertFalse(manifest[key])
        with zipfile.ZipFile(io.BytesIO(data)) as bundle:
            self.assertEqual(set(bundle.namelist()),{'animal-forest-english.ups','manifest.json','README.md',
                'SOURCES.md','LICENSE-tooling.txt','apply_translation.py','aflib.py','SHA256SUMS'})
            self.assertEqual(json.loads(bundle.read('manifest.json')),manifest)
            for row in bundle.read('SHA256SUMS').decode().splitlines():
                digest,name=row.split('  ',1);self.assertEqual(sha256(bundle.read(name)),digest)
            for name in bundle.namelist():
                if name.endswith(('.md','.py','.txt','.json')):
                    self.assertNotIn(b'/home/discordian',bundle.read(name))

    def test_bad_revision_stage_and_changed_evidence_reject(self):
        with patch.object(package,'STAGES',package.STAGES[:-1]),self.assertRaises(ValueError):
            package.prepare(FOLDER,self.source,'a'*40,*self.evidence)
        with self.assertRaises(ValueError):package.prepare(FOLDER,self.source,'uncommitted',*self.evidence)
        for i in range(3):
            altered=list(self.evidence);entries=json.loads(altered[i]);entries[0]['rom_sha256']='0'*64
            altered[i]=json.dumps(entries).encode()
            with self.assertRaises(ValueError):package.prepare(FOLDER,self.source,'a'*40,*altered)

if __name__=='__main__':unittest.main()
