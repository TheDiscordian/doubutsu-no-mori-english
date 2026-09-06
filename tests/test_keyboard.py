"""Keyboard patches preserve native allocation sizes and name limits."""

from pathlib import Path
import struct
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from keyboard import english_editor, label_pixels


class KeyboardTests(unittest.TestCase):
    def test_default_mode_patch_is_guarded_and_local(self):
        original = bytearray(0x800)
        original[0x76C:0x774] = bytes.fromhex("A0600004A0600005")
        patched = english_editor(original)
        self.assertEqual(patched[:0x76C], original[:0x76C])
        self.assertEqual(patched[0x774:], original[0x774:])
        self.assertEqual(patched[0x76C:0x774], bytes.fromhex("24190300A4790004"))
        with self.assertRaisesRegex(ValueError, "initialisation"):
            english_editor(patched)

    def test_labels_reject_overflow_without_resizing(self):
        atlas = [15]*(192*256)
        rendered = label_pixels(atlas, "A", 16)
        self.assertEqual(len(rendered), 16*16)
        self.assertEqual(rendered[:16], [0, 0]+[15]*12+[0, 0])
        with self.assertRaisesRegex(ValueError, "does not fit"):
            label_pixels(atlas, "ABCDE", 48)
