"""Original N64 advice/travel drafts preserve native commands and warning actions."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import sha256
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry
from test_retail import ROM_PATH


class NativeAdviceTravelTests(unittest.TestCase):
    @unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM remains a local test input")
    def test_complete_native_commands_and_full_controller_pak_highlights(self):
        rom = ROM_PATH.read_bytes()
        info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == "message").entries()
        drafts = json.loads((ROOT/"translations/n64-advice-travel.json").read_text())
        self.assertEqual({r["id"].split(":")[1] for r in drafts},
                         {"0945", "11F1", "147F", "14CF", "14FE", "1BD3", "1BD4"})
        before, after = bytes.fromhex("7F50198CDC09"), bytes.fromhex("7F50198CDC0E")
        for edit in drafts:
            source = sources[int(edit["id"].split(":")[1], 16)]
            output = encode(edit["translation"], info)
            self.assertEqual(edit["source_sha256"], sha256(source))
            self.assertEqual(edit["status"], "draft")
            expected = [after if t.data == before else t.data
                        for t in tokenize(source, info) if t.kind == "cmd"]
            actual = [t.data for t in tokenize(output, info) if t.kind == "cmd"]
            self.assertEqual(actual, expected, edit["id"])
            for t in tokenize(output, info):
                if t.kind == "cmd" and t.data == after:
                    self.assertEqual(output[t.offset+6:t.offset+20], b"Controller Pak")
            validate_entry(source, output, info, "message", edit.get("control_policy", "exact"),
                           resident_runtime=True)
            if edit["id"] == "message:0945":
                self.assertIn(bytes.fromhex("7F1600290062"), output)
                self.assertIn(bytes.fromhex("7F0F09467F1009477F19"), output)
                self.assertIn(b"will be erased", output)
            if edit["id"] == "message:1BD4":
                self.assertIn(bytes.fromhex("7F059696967F5100"), output)
                self.assertIn(bytes.fromhex("7F5101"), output)


if __name__ == "__main__":
    unittest.main()
