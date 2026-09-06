"""Reference formatting never relaxes sound, flow, actor, or buffer checks."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from gc_adapter import adapt_reference
from textcodec import encode
from textvalidate import FONT_PRESENTATION, layout_issues, validate_entry
from font_controls_test_scenario import scenario


class ReferenceLayoutTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        for code in (0x51, 0x52, 0x53, 0x54, 0x5A):
            self.info[code] = (3, 4)
        self.info[0x50] = (6, 5)
        self.info[0x09] = (5, 0)
        self.info[0x0E] = (4, 0)
        self.native = encode("A{cmd:7F09000003}{cmd:7F5101}{cmd:7F0E0008}{cmd:7F01}", self.info)
        self.reference = ("{cmd:7F5001020304}First{cmd:7F04}\n{cmd:7F02}"
                          "{cmd:7F528C}{cmd:7F5302}{cmd:7F5414}{cmd:7F5A14}Small"
                          "{cmd:7F09000007}{cmd:7F5101}{cmd:7F0E0008}{cmd:7F01}")

    def test_reference_layout_keeps_exact_english_formatting(self):
        text, edits = adapt_reference(self.reference, self.native, self.info, "reference_layout")
        self.assertEqual(text, self.reference.replace("7F09000007", "7F09000003"))
        self.assertEqual(edits[1]["gamecube"], ["7F5001020304", "7F528C", "7F5302", "7F5414", "7F5A14"])
        replacement = encode(text, self.info)
        validate_entry(self.native, replacement, self.info, "message", "reference_layout")
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_entry(self.native, replacement, self.info, "message", "reference_delivery")
        with self.assertRaisesRegex(ValueError, "only audited for dialogue"):
            validate_entry(self.native, replacement, self.info, "select", "reference_layout")

    def test_sound_flow_actor_and_fields_still_strict(self):
        text, _ = adapt_reference(self.reference, self.native, self.info, "reference_layout")
        for before, after in (("7F5101", "7F5100"), ("7F0E0008", "7F0E0009"),
                              ("7F09000003", "7F09000004"), ("7F01", "7F00"),
                              ("Small", "Small{cmd:7F1A}")):
            with self.assertRaises(ValueError):
                validate_entry(self.native, encode(text.replace(before, after), self.info), self.info,
                               "message", "reference_layout")
        self.assertNotIn(0x51, FONT_PRESENTATION)

    def test_unsafe_parameters_rejected_even_with_exact_policy(self):
        for command in ("7F5303", "7F53FF", "7F5400", "7F5A00"):
            data = encode("{cmd:"+command+"}{cmd:7F00}", self.info)
            with self.assertRaises(ValueError):
                validate_entry(data, data, self.info, "message")
        for command in ("7F5300", "7F5302", "7F5401", "7F54FF", "7F5A01", "7F5AFF"):
            data = encode("{cmd:"+command+"}{cmd:7F00}", self.info)
            validate_entry(data, data, self.info, "message")

    def test_capacity_and_layout_review_remain(self):
        with self.assertRaisesRegex(ValueError, "1024"):
            validate_entry(b"\x7f\x00", b"A"*1024+b"\x7f\x00", self.info,
                           "message", "reference_layout")
        self.assertEqual(layout_issues(bytes.fromhex("7F5101"), self.info, {}), [])
        self.assertIn("explicit_layout_command_needs_review",
                      layout_issues(bytes.fromhex("7F5414"), self.info, {}))

    def test_native_scenario_covers_real_dispatch_and_restores_checkpoint(self):
        actions = scenario()
        calls = [a["call"]["address"] for a in actions if "call" in a]
        self.assertEqual(calls.count("80091C98"), 19)
        self.assertIn("800913D4", calls)
        self.assertIn("80091470", calls)
        self.assertTrue(any(a.get("load_state") for a in actions))
