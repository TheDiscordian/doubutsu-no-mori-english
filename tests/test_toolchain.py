"""Registered image provenance does not relax native or metadata approvals."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
import toolchain as tc
import setup_toolchain as setup


def actual_public_report(value):
    if isinstance(value, dict):
        return {k: tc.PUBLIC_IMAGE if k == 'toolchain_image' else actual_public_report(v)
                for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [actual_public_report(child) for child in value]
    return value


class ToolchainTests(unittest.TestCase):
    def test_only_registered_field_is_compared_and_original_is_untouched(self):
        old = {'toolchain_image': tc.LEGACY_IMAGE, 'nested': [{'toolchain_image': tc.LEGACY_IMAGE}],
               'source': tc.LEGACY_IMAGE, 'sha256': 'native-code'}
        public = actual_public_report(old)
        before = deepcopy(public)
        self.assertEqual(tc.comparison_profile(public), old)
        self.assertEqual(tc.profile_sha256(public), tc.profile_sha256(old))
        self.assertNotEqual(sha256(json.dumps(public).encode()), sha256(json.dumps(old).encode()))
        self.assertEqual(public, before)
        changed = deepcopy(public)
        changed['source'] = tc.PUBLIC_IMAGE
        self.assertNotEqual(tc.profile_sha256(changed), tc.profile_sha256(public))

    def test_all_other_metadata_remains_bound(self):
        original = {'toolchain_image': tc.PUBLIC_IMAGE, 'code': 'hash', 'sources': {'file.c': 'hash'},
                    'flags': ['-Os'], 'symbols': {'entry': 32}, 'bytes': 64}
        for key, value in [('code', 'wrong'), ('sources', {}), ('flags', []), ('symbols', {'entry': 36}), ('bytes', 68)]:
            with self.subTest(field=key):
                altered = deepcopy(original)
                altered[key] = value
                self.assertNotEqual(tc.profile_sha256(original), tc.profile_sha256(altered))

    def test_unknown_or_missing_image_is_not_an_equivalent_profile(self):
        for value in ('arbitrary:latest', None, [], 1):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, 'Unknown compiler'):
                tc.profile_sha256({'toolchain_image': value})
        self.assertNotEqual(tc.profile_sha256({}), tc.profile_sha256({'toolchain_image': tc.PUBLIC_IMAGE}))

    def test_verifier_rejects_arbitrary_images_without_docker(self):
        with patch.object(setup.subprocess, 'run') as run:
            with self.assertRaisesRegex(ValueError, 'registered'):
                setup.verify('arbitrary:latest', pull=True)
            run.assert_not_called()

    def test_verifier_records_actual_image_and_rejects_changed_executables(self):
        inspected = [{'Id': 'actual-image-id', 'Architecture': 'amd64', 'Os': 'linux',
                      'RepoDigests': [tc.PUBLIC_IMAGE]}]
        inventory = ''.join(f'{digest}  /n64_toolchain/{name}\n' for name, digest in tc.EXECUTABLES.items())
        def results(hashes):
            return [subprocess.CompletedProcess([], 0, json.dumps(inspected), ''),
                    subprocess.CompletedProcess([], 0, hashes, ''),
                    subprocess.CompletedProcess([], 0, 'mips64-elf-gcc (GCC) 14.2.0\n', '')]
        with patch.object(setup.subprocess, 'run', side_effect=results(inventory)):
            report = setup.verify(tc.PUBLIC_IMAGE)
        self.assertEqual(report['toolchain_image'], tc.PUBLIC_IMAGE)
        self.assertEqual(report['inspected_image_id'], 'actual-image-id')
        with patch.object(setup.subprocess, 'run', side_effect=results(inventory.replace('ee547530', '00000000'))):
            with self.assertRaisesRegex(ValueError, 'executables differ'):
                setup.verify(tc.PUBLIC_IMAGE)


@unittest.skipUnless((ROOT/'build/classic-letters-candidate').is_dir(), 'Retained local profiles required')
class RetainedProfiles(unittest.TestCase):
    def test_accent_profiles_accept_known_image_only_with_unchanged_native_parts(self):
        from accent_mail_overlay_profile import wrap, validate
        for kind in ('creator', 'notice', 'event'):
            with self.subTest(kind=kind):
                directory = ROOT/'build/accent-mail-overlays'/kind
                extension = json.loads((directory/'overlay.json').read_text())
                data, reloc = [(directory/name).read_bytes() for name in ('overlay.bin', 'relocation.bin')]
                for metadata in (extension, actual_public_report(extension)):
                    validate(kind, data, reloc, wrap(metadata))
                    with self.assertRaises(ValueError):
                        validate(kind, b'\xFF'+data[1:], reloc, wrap(metadata))

    def test_classic_profiles_retain_previous_image_and_source_approvals(self):
        from classic_letter_profiles import wrap, validate
        for kind in ('font', 'creator'):
            with self.subTest(kind=kind):
                directory = ROOT/'build/classic-letters-candidate'/kind
                extension = json.loads((directory/'profile.json').read_text())
                data, reloc = [(directory/name).read_bytes() for name in ('image.bin', 'relocation.bin')]
                for metadata in (extension, actual_public_report(extension)):
                    validate(kind, data, reloc, wrap(metadata))
                    altered = deepcopy(metadata)
                    altered['symbols'] = {}
                    with self.assertRaises(ValueError):
                        validate(kind, data, reloc, wrap(altered))


if __name__ == '__main__':
    unittest.main()
