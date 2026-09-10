"""Approved eight-MiB patch bundle, full reconstruction, and standalone patcher."""
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
import package_v1_playtest as package


@unittest.skipUnless((ROOT/'build/title-countdown-combined-01/preview.json').is_file(),
    'Local complete title/countdown candidate required')
class V1PlaytestPackageTests(unittest.TestCase):
    def test_actual_bundle_and_included_patcher_reconstruct_without_overwriting(self):
        source=ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
        data,manifest=package.prepare(ROOT/'build/title-countdown-combined-01',source.read_bytes(),'a'*40)
        self.assertEqual(manifest['label'],'v1-artwork-playtest-02')
        self.assertEqual(manifest['output_sha256'],package.ROM_SHA)
        self.assertEqual(manifest['required_ram_bytes'],0x800000)
        self.assertEqual(manifest['ordinary_heap_end'],0x80400000)
        self.assertTrue(manifest['expansion_pak_required'])
        for key in ('public_release','complete_v1','original_hardware_verified','human_playthrough_complete',
                    'ordinary_save_restart_verified','embedded_warning_native_drawing_verified'):
            self.assertFalse(manifest[key])
        with zipfile.ZipFile(io.BytesIO(data)) as archive,tempfile.TemporaryDirectory(prefix='af-v1-patch-') as directory:
            self.assertEqual(set(archive.namelist()),{'animal-forest-english.ups','manifest.json','README.md',
                'FEATURES.md','SOURCES.md','LICENSE-tooling.txt','apply_translation.py','aflib.py','SHA256SUMS'})
            self.assertEqual(json.loads(archive.read('manifest.json')),manifest)
            self.assertIn(b'min.',archive.read('FEATURES.md'))
            self.assertIn(b'fortune',archive.read('FEATURES.md'))
            self.assertIn(b'festival stall',archive.read('FEATURES.md'))
            for line in archive.read('SHA256SUMS').decode().splitlines():
                digest,name=line.split('  ',1);self.assertEqual(sha256(archive.read(name)),digest)
            for name in archive.namelist():
                self.assertFalse(name.endswith(('.z64','.n64','.v64','.iso','.flash','.pak','.rtc')))
                if name.endswith(('.md','.py','.txt','.json')):
                    self.assertNotIn(b'/home/discordian',archive.read(name))
            archive.extractall(directory)
            folder=Path(directory);output=folder/'English.z64'
            args=[sys.executable,str(folder/'apply_translation.py'),'--rom',str(source),'--output',str(output)]
            result=subprocess.run(args,cwd=folder,capture_output=True,text=True,check=True,timeout=60)
            self.assertEqual(json.loads(result.stdout)['sha256'],package.ROM_SHA)
            self.assertEqual(sha256(output.read_bytes()),package.ROM_SHA)
            again=subprocess.run(args,cwd=folder,capture_output=True,text=True,timeout=60)
            self.assertNotEqual(again.returncode,0)
            self.assertEqual(sha256(output.read_bytes()),package.ROM_SHA)
        self.assertEqual(sha256(source.read_bytes()),manifest['source_sha256'])

    def test_unknown_report_and_packaging_revision_are_rejected(self):
        source=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        directory=ROOT/'build/title-countdown-combined-01'
        with patch.object(package,'REPORT_SHA','0'*64),self.assertRaises(ValueError):
            package.prepare(directory,source,'a'*40)
        with self.assertRaises(ValueError):package.prepare(directory,source,'uncommitted')


if __name__=='__main__':unittest.main()
