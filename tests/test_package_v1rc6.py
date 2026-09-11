"""RC6 patch-only contents, two-stage provenance, and explicit evidence limits."""
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
from package_v1rc6 import FINAL_SHA, PREVIOUS_SHA, STAGES, prepare, verify_receipts


@unittest.skipUnless((ROOT/'build/menu-text-followup-01/fixes.json').exists(), 'Committed menu follow-up required')
class RC6PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.revision = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=ROOT, check=True,
                                      capture_output=True, text=True).stdout.strip()
        cls.raws = [(ROOT/'build'/folder/'fixes.json').read_bytes()
                    for folder in ('tune-confirmation-01', 'menu-text-followup-01')]

    def test_exact_members_hashes_and_no_inherited_execution_claim(self):
        archive, manifest, image = prepare(ROOT/'build/menu-text-followup-01', ROOT/'build/tune-confirmation-01',
                                           self.native, self.revision)
        self.assertEqual(sha256(image), FINAL_SHA)
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            self.assertEqual(set(bundle.namelist()), {'animal-forest-english.ups', 'manifest.json', 'README.md',
                'SOURCES.md', 'LICENSE-tooling.txt', 'apply_translation.py', 'aflib.py', 'SHA256SUMS'})
            self.assertEqual(len(bundle.namelist()), 8)
            self.assertEqual(json.loads(bundle.read('manifest.json')), manifest)
            sums = bundle.read('SHA256SUMS').decode().splitlines()
            self.assertEqual(len(sums), 7)
            for line in sums:
                digest, name = line.split('  ')
                self.assertEqual(sha256(bundle.read(name)), digest)
            self.assertNotIn(b'](TOOLCHAIN.md)', bundle.read('SOURCES.md'))
        for key in ('public_release', 'original_hardware_verified', 'ordinary_menu_appearance_verified',
                    'ordinary_save_restart_verified', 'native_execution_on_this_candidate_verified'):
            self.assertFalse(manifest[key])
        self.assertEqual(manifest['previous_candidate_sha256'], PREVIOUS_SHA)
        self.assertEqual(manifest['new_findings'], ['V1-24', 'V1-25'])
        self.assertEqual(manifest['save_compatibility']['previous_candidate'], 'V1RC5')
        self.assertFalse(manifest['save_compatibility']['migration_required'])
        self.assertEqual([s['builder'] for s in manifest['correction_stages']], [s[0] for s in STAGES])
        self.assertEqual([s['receipt_sha256'] for s in manifest['correction_stages']], [sha256(raw) for raw in self.raws])

    def test_rejects_incomplete_dirty_disconnected_or_unbound_receipts(self):
        with self.assertRaises(ValueError):
            verify_receipts(self.raws[:1])
        with self.assertRaises(ValueError):
            verify_receipts(self.raws[::-1])
        for index in range(2):
            for key, value in (('worktree_modified', True), ('source_builder_sha256', '0'*64),
                               ('saved_format_changed', True), ('baseline_sha256', '0'*64),
                               ('source_revision', 'invalid')):
                rows = self.raws.copy()
                report = json.loads(rows[index])
                report[key] = value
                rows[index] = json.dumps(report).encode()
                with self.subTest(stage=index, key=key), self.assertRaises(ValueError):
                    verify_receipts(rows)

    def test_allows_committed_replay_metadata_without_weakening_source_binding(self):
        rows = []
        for raw in self.raws:
            report = json.loads(raw)
            report['source_revision'] = self.revision
            rows.append(json.dumps(report, sort_keys=True).encode())
        stages = verify_receipts(rows)
        self.assertEqual([stage['source_revision'] for stage in stages], [self.revision]*2)
        self.assertEqual([stage['receipt_sha256'] for stage in stages], [sha256(raw) for raw in rows])
        with self.assertRaises(ValueError):
            prepare(ROOT/'build/menu-text-followup-01', ROOT/'build/tune-confirmation-01', self.native, 'invalid')


if __name__ == '__main__':
    unittest.main()
