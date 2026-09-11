"""Verify the committed Pages artifact without private game inputs."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from prepare_pages import FILES, OUTPUT_SHA, prepare


class PreparePagesTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='af-pages-')
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root/'web'
        shutil.copytree(ROOT/'web', self.source)
        self.output = self.root/'output'

    def test_public_artifact_has_only_reviewed_files(self):
        result = prepare(self.source, self.output, public=True)
        self.assertTrue(result['public_release'])
        self.assertEqual(result['output_sha256'], OUTPUT_SHA)
        self.assertEqual(
            {p.relative_to(self.output).as_posix() for p in self.output.rglob('*') if p.is_file()},
            set(FILES))
        self.assertTrue(json.loads((self.output/'release/manifest.json').read_text())['public_release'])
        self.assertFalse(json.loads((self.source/'release/manifest.json').read_text())['public_release'])

    def test_private_validation_does_not_mark_public(self):
        self.assertFalse(prepare(self.source, self.output)['public_release'])

    def test_unreviewed_file_and_symlink_are_rejected(self):
        (self.source/'private.txt').write_text('synthetic private fixture')
        with self.assertRaisesRegex(ValueError, 'exactly'):
            prepare(self.source, self.output)
        (self.source/'private.txt').unlink()
        (self.source/'outside').symlink_to(self.root)
        with self.assertRaisesRegex(ValueError, 'symbolic'):
            prepare(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_changed_patch_is_rejected(self):
        patch = self.source/'release/patch.afwp.gz'
        contents = bytearray(patch.read_bytes())
        contents[-1] ^= 1
        patch.write_bytes(contents)
        with self.assertRaisesRegex(ValueError, 'identity'):
            prepare(self.source, self.output)
        self.assertFalse(self.output.exists())

    def test_existing_output_is_preserved(self):
        self.output.mkdir()
        marker = self.output/'keep.txt'
        marker.write_text('keep')
        with self.assertRaisesRegex(ValueError, 'fresh'):
            prepare(self.source, self.output)
        self.assertEqual(marker.read_text(), 'keep')


if __name__ == '__main__':
    unittest.main()
