import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from prepare_inputs import store_input


class InputTests(unittest.TestCase):
    def test_existing_inputs_are_not_overwritten(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory)/"input"
            self.assertEqual(store_input(target, b"source"), "prepared")
            self.assertEqual(store_input(target, b"source"), "already_verified")
            with self.assertRaisesRegex(ValueError, "differs"):
                store_input(target, b"different")
            self.assertEqual(target.read_bytes(), b"source")
            link = Path(directory)/"link"
            link.symlink_to(target)
            with self.assertRaisesRegex(ValueError, "differs"):
                store_input(link, b"different")
            self.assertEqual(target.read_bytes(), b"source")
