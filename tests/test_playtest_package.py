"""Patch-only packaging and exclusive, checksummed application."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import aflib
from apply_translation import apply_bundle, write_new
from package_v0 import archive_bytes, prepare, CANDIDATE_SHA256, HARDWARE_FIX_SHA256


class PatchApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source = bytearray(0x101000)
        source[:4] = bytes.fromhex('80371240')
        aflib.fix_checksum(source)
        target = bytearray(source)
        target[0x1000:0x1005] = b'TEST!'
        aflib.fix_checksum(target)
        cls.source, cls.target = bytes(source), bytes(target)
        cls.patch = aflib.make_ups(cls.source, cls.target)
        cls.manifest = {'format': 1, 'source_sha256': aflib.sha256(cls.source),
            'patch_sha256': aflib.sha256(cls.patch), 'output_sha256': aflib.sha256(cls.target),
            'output_bytes': len(cls.target)}

    def apply(self, source=None, ups=None, manifest=None):
        with patch('aflib.ROM_SHA256', self.manifest['source_sha256']), patch('apply_translation.ROM_SHA256', self.manifest['source_sha256']):
            return apply_bundle(self.source if source is None else source,
                                self.patch if ups is None else ups,
                                self.manifest if manifest is None else manifest)

    def test_all_three_rom_byte_orders_reconstruct_exact_target(self):
        swapped = bytearray(self.source)
        swapped[::2], swapped[1::2] = self.source[1::2], self.source[::2]
        reversed_words = bytearray(len(self.source))
        for i in range(4):
            reversed_words[i::4] = self.source[3-i::4]
        for source in (self.source, bytes(swapped), bytes(reversed_words)):
            self.assertEqual(self.apply(source), self.target)

    def test_source_patch_manifest_and_boot_checksum_fail_closed(self):
        with self.assertRaises(ValueError): self.apply(source=self.target)
        with self.assertRaises(ValueError): self.apply(ups=self.patch[:-1]+bytes([self.patch[-1]^1]))
        for key, value in (('format', 2), ('source_sha256', '0'*64), ('output_sha256', '0'*64), ('output_bytes', 0)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                self.apply(manifest={**self.manifest, key: value})
        bad = bytearray(self.target); bad[0x10] ^= 1
        ups = aflib.make_ups(self.source, bytes(bad))
        with self.assertRaisesRegex(ValueError, 'boot checksum'):
            self.apply(ups=ups, manifest={**self.manifest, 'patch_sha256': aflib.sha256(ups), 'output_sha256': aflib.sha256(bad)})

    def test_existing_file_and_symlink_are_never_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'output.z64'
            write_new(path, b'original')
            link = Path(directory)/'link.z64'; link.symlink_to(path)
            dangling = Path(directory)/'dangling.z64'; dangling.symlink_to(Path(directory)/'absent')
            for target in (path, link, dangling, Path(directory)):
                with self.assertRaises(OSError): write_new(target, b'changed')
            self.assertEqual(path.read_bytes(), b'original')
            self.assertFalse((Path(directory)/'absent').exists())

    def test_archive_is_deterministic_and_rejects_paths(self):
        members = {'b.txt': b'b', 'a.txt': b'a'}
        self.assertEqual(archive_bytes(members), archive_bytes(dict(reversed(list(members.items())))))
        with zipfile.ZipFile(io.BytesIO(archive_bytes(members))) as archive:
            self.assertEqual(archive.namelist(), ['a.txt', 'b.txt'])
        for name in ('../x', 'dir/x', 'dir\\x', '.', '..'):
            with self.assertRaises(ValueError): archive_bytes({name: b''})


@unittest.skipUnless((ROOT/'build/classic-letters-pilot/build.json').is_file(), 'Complete candidate required')
class CandidatePackageTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'build/v0-hardware-fixes-02/build.json').is_file(), 'Combined hardware fix required')
    def test_hardware_fix_package_has_its_own_revision_and_playtest_notes(self):
        source = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        package, manifest = prepare(ROOT/'build/v0-hardware-fixes-02', source, 'fix-revision')
        self.assertEqual(manifest['output_sha256'], HARDWARE_FIX_SHA256)
        self.assertEqual(manifest['cartridge_source_revision'], 'fix-revision')
        self.assertEqual(manifest['label'], 'v0-hardware-fixes-02')
        self.assertFalse(manifest['original_hardware_verified'])
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            self.assertEqual(archive.read('README.md'), (ROOT/'docs/V0_FIXES_PLAYTEST.md').read_bytes())
            self.assertFalse(any(name.endswith(('.z64', '.n64', '.v64')) for name in archive.namelist()))
            for line in archive.read('SHA256SUMS').decode().splitlines():
                digest, name = line.split('  ', 1)
                self.assertEqual(aflib.sha256(archive.read(name)), digest)

    def test_actual_package_reconstructs_candidate_and_contains_no_rom(self):
        source = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        package, manifest = prepare(ROOT/'build/classic-letters-pilot', source, 'test-revision')
        self.assertEqual(manifest['output_sha256'], CANDIDATE_SHA256)
        self.assertFalse(manifest['public_release'])
        with zipfile.ZipFile(io.BytesIO(package)) as archive:
            self.assertEqual(set(archive.namelist()), {'animal-forest-english.ups', 'manifest.json',
                'README.md', 'SOURCES.md', 'LICENSE-tooling.txt', 'apply_translation.py', 'aflib.py', 'SHA256SUMS'})
            self.assertEqual(json.loads(archive.read('manifest.json')), manifest)
            for line in archive.read('SHA256SUMS').decode().splitlines():
                digest, name = line.split('  ', 1)
                self.assertEqual(aflib.sha256(archive.read(name)), digest)


if __name__ == '__main__':
    unittest.main()
