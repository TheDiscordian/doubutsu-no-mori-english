"""Approved button wording changes preserve the rest of the English reference."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_VROM, by_vrom, sha256
from build import apply_translations
from controller_adaptations import (AFTER, BEFORE, OPERATION, adapt_controller_reference,
                                    validate_approval, validate_controller_candidate)
from gc_adapter import adapt_reference
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import command_info, decode, encode
from textvalidate import validate_entry
from test_retail import ROM_PATH


class ControllerAdaptationTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.info[3], self.info[0x50] = (3, 0), (6, 4)
        self.source = b"Native instruction\x7f\x00"
        self.prefix, self.suffix = b"Press ", b"\x7f\x03\x08\xcdfollowing line\x7f\x04\xcd\x7f\x02next page\x7f\x00"
        self.raw = self.prefix+BEFORE+self.suffix
        self.expected = self.prefix+AFTER+self.suffix
        self.reference = {"id": "message:0001", "sha256": sha256(self.raw), "text": decode(self.raw, self.info)}
        self.record = {"id": self.reference["id"], "reference_id": self.reference["id"],
                       "source_sha256": sha256(self.source), "reference_sha256": sha256(self.raw),
                       "controller": {"operation": OPERATION, "offset": len(self.prefix),
                                      "adapted_sha256": sha256(self.expected)}}

    def test_only_approved_span_changes(self):
        text, changes = adapt_controller_reference(self.reference, self.source, self.record, self.info)
        self.assertEqual(encode(text, self.info), self.expected)
        self.assertEqual(changes[0]["operation"], OPERATION)
        validate_controller_candidate(self.record["id"], self.source, self.expected,
                                      {self.record["id"]: self.record})
        self.assertEqual(adapt_controller_reference(self.reference, self.source, None, self.info),
                         (self.reference["text"], []))

    def test_stale_sources_references_offsets_and_payloads_fail(self):
        for reference, source in ((self.reference, b"stale"),
                                  ({**self.reference, "sha256": "0"*64}, self.source),
                                  ({**self.reference, "text": "changed"}, self.source),
                                  ({**self.reference, "id": "message:0002"}, self.source)):
            with self.assertRaisesRegex(ValueError, "Stale"):
                adapt_controller_reference(reference, source, self.record, self.info)
        record = copy.deepcopy(self.record)
        record["controller"]["offset"] += 1
        with self.assertRaisesRegex(ValueError, "span"):
            adapt_controller_reference(self.reference, self.source, record, self.info)
        for output in (self.raw, self.expected+b" ", self.expected.replace(b"\xcd", b" ")):
            with self.assertRaisesRegex(ValueError, "complete approval"):
                validate_controller_candidate(self.record["id"], self.source, output,
                                              {self.record["id"]: self.record})

    def test_unknown_operations_and_malformed_approvals_fail(self):
        for change in ({"operation": "global_replace"}, {"offset": -1}, {"offset": True},
                       {"offset": 1024}, {"adapted_sha256": "bad"}, {"adapted_sha256": None},
                       {"extra": "unexpected"}):
            record = copy.deepcopy(self.record)
            record["controller"].update(change)
            with self.assertRaises(ValueError):
                validate_approval(record)
        for rule in (None, [], "bad"):
            with self.assertRaises(ValueError):
                validate_approval({**self.record, "controller": rule})

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/text/message.jsonl").is_file(),
                         "Retail and English-reference inputs remain local")
    def test_retail_clothing_instruction_keeps_gc_delivery(self):
        rom = ROM_PATH.read_bytes()
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
        source = next(b for b in banks(rom) if b.name == "message").entries()[0x07F3]
        reference = next(r for r in map(json.loads, (ROOT/"build/gamecube/text/message.jsonl").read_text().splitlines())
                         if r["id"] == "message:07F3")
        matches = load_matches(ROOT/"translations/reference_matches.json")
        text, _ = adapt_controller_reference(reference, source, matches[reference["id"]], info)
        text, _ = adapt_reference(text, source, info, "reference_layout", resident_runtime=True)
        output = encode(text, info)
        validate_controller_candidate(reference["id"], source, output, matches)
        validate_entry(source, output, info, "message", "reference_layout", resident_runtime=True)
        raw = encode(reference["text"], info)
        self.assertEqual(output, raw[:84]+AFTER+raw[84+len(BEFORE):])
        self.assertEqual(len(output), 382)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"unadapted.json"
            path.write_text(json.dumps([{"id": reference["id"], "source_sha256": sha256(source),
                                         "translation": reference["text"], "control_policy": "reference_layout"}]))
            with self.assertRaisesRegex(ValueError, "Controller-text candidate"):
                apply_translations(rom, {}, path)

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/text/message.jsonl").is_file(),
                         "Retail and English-reference inputs remain local")
    def test_retail_planting_instruction_keeps_pixel_spaces(self):
        rom = ROM_PATH.read_bytes()
        info = module_command_info(rom)
        source = next(b for b in banks(rom) if b.name == "message").entries()[0x07F8]
        reference = next(r for r in map(json.loads, (ROOT/"build/gamecube/text/message.jsonl").read_text().splitlines())
                         if r["id"] == "message:07F8")
        matches = load_matches(ROOT/"translations/reference_matches.json")
        text, _ = adapt_controller_reference(reference, source, matches[reference["id"]], info)
        text, _ = adapt_reference(text, source, info, "reference_layout", resident_runtime=True)
        output = encode(text, info)
        validate_controller_candidate(reference["id"], source, output, matches)
        validate_entry(source, output, info, "message", "reference_layout", resident_runtime=True)
        raw = encode(reference["text"], info)
        self.assertEqual(output, raw[:80]+AFTER+raw[80+len(BEFORE):])
        self.assertEqual(len(output), 438)
        self.assertEqual(output.count(bytes.fromhex("7F670A")), 2)


if __name__ == "__main__":
    unittest.main()
