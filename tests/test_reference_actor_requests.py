"""Exact actor-request approvals retain the original native destination and value."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import sha256
from build import apply_translations
from gc_adapter import adapt_reference
from reference_actor_requests import (adapt_actor_request_reference,
                                      validate_actor_request_approval,
                                      validate_actor_request_candidate)
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode, tokenize
from textvalidate import validate_entry
from test_retail import ROM_PATH


class ReferenceActorRequestTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        for opcode in range(8, 13):
            self.info[opcode] = (5, 0)
        self.before = bytes.fromhex("7F0C050068")
        self.after = bytes.fromhex("7F0905006B")
        self.extra = bytes.fromhex("7F09020002")
        self.source = b"Native"+self.after+self.extra+b"\x7f\x01"
        self.raw = b"English\xcd"+self.before+self.extra+b"\x7f\x01"
        self.expected = b"English\xcd"+self.after+self.extra+b"\x7f\x01"
        self.reference = {"id": "message:0000", "sha256": sha256(self.raw), "text": decode(self.raw, self.info)}
        self.record = {"id": "message:0000", "reference_id": "message:0000",
                       "source_sha256": sha256(self.source), "reference_sha256": sha256(self.raw),
                       "native_actor_request": {"offset": 8, "reference_command": self.before.hex().upper(),
                                                "native_command": self.after.hex().upper(),
                                                "adapted_sha256": sha256(self.expected)}}

    def test_exact_replacement_retains_complete_native_requests_and_english(self):
        text, changes = adapt_actor_request_reference(self.reference, self.source, self.record, self.info)
        self.assertEqual(encode(text, self.info), self.expected)
        self.assertEqual(changes[0]["operation"], "preserve_approved_native_npc0_request")
        validate_actor_request_candidate(self.record["id"], self.source, self.expected,
                                         {self.record["id"]: self.record})
        validate_entry(self.source, self.expected, self.info, "message", "reference_layout")
        self.assertEqual(adapt_actor_request_reference(self.reference, self.source, None, self.info),
                         (self.reference["text"], []))

    def test_stale_source_reference_and_final_payload(self):
        for ref, source in ((self.reference, b"Other"),
                            ({**self.reference, "id": "message:0001"}, self.source),
                            ({**self.reference, "sha256": "0"*64}, self.source),
                            ({**self.reference, "text": "Other"}, self.source)):
            with self.assertRaisesRegex(ValueError, "Stale"):
                adapt_actor_request_reference(ref, source, self.record, self.info)
        for source, candidate in ((b"Other", self.expected), (self.source, self.raw),
                                  (self.source, self.expected+b" "),
                                  (self.source, self.expected.replace(b"\xcd", b" "))):
            with self.assertRaisesRegex(ValueError, "complete approval"):
                validate_actor_request_candidate(self.record["id"], source, candidate,
                                                 {self.record["id"]: self.record})

    def test_exact_unique_span_and_complete_actor_sequence(self):
        for rule in ({"offset": 7}, {"native_command": "7F09050069"}):
            record = deepcopy(self.record)
            record["native_actor_request"].update(rule)
            with self.assertRaisesRegex(ValueError, "uniquely present"):
                adapt_actor_request_reference(self.reference, self.source, record, self.info)
        for source, raw in ((self.source+self.after, self.raw), (self.source, self.raw+self.before)):
            record = {**self.record, "source_sha256": sha256(source), "reference_sha256": sha256(raw)}
            ref = {**self.reference, "sha256": sha256(raw), "text": decode(raw, self.info)}
            with self.assertRaisesRegex(ValueError, "uniquely present"):
                adapt_actor_request_reference(ref, source, record, self.info)
        for raw in (self.raw.replace(self.extra, bytes.fromhex("7F09020003")),
                    self.raw.replace(self.extra, b""), self.extra+self.raw):
            record = deepcopy(self.record)
            record["reference_sha256"] = sha256(raw)
            record["native_actor_request"]["offset"] = raw.index(self.before)
            ref = {**self.reference, "sha256": sha256(raw), "text": decode(raw, self.info)}
            with self.assertRaisesRegex(ValueError, "complete native actor command sequence"):
                adapt_actor_request_reference(ref, self.source, record, self.info)

    def test_approval_restricts_opcode_slot_offset_and_combination(self):
        for rule in ({"offset": True}, {"offset": -1}, {"offset": 1024},
                     {"adapted_sha256": None}, {"adapted_sha256": "A"*64},
                     {"native_command": "7F0C05006B"}, {"native_command": "7F0904006B"},
                     {"reference_command": "7F09050068"}, {"reference_command": []},
                     {"unapproved": True}):
            record = deepcopy(self.record)
            record["native_actor_request"].update(rule)
            with self.assertRaises(ValueError):
                validate_actor_request_approval(record)
        for change in ({"controller": {}}, {"native_choices": {}}, {"id": "select:0000"},
                       {"native_actor_request": None}):
            with self.assertRaises(ValueError):
                validate_actor_request_approval({**self.record, **change})

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/text/message.jsonl").is_file(),
                         "Retail and English reference inputs remain local")
    def test_all_reviewed_retail_requests_and_independent_builder_guard(self):
        rom = ROM_PATH.read_bytes()
        info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == "message").entries()
        refs = {r["id"]: r for r in map(json.loads, (ROOT/"build/gamecube/text/message.jsonl").read_text().splitlines())}
        matches = load_matches(ROOT/"translations/reference_matches.json")
        approved = [r for r in matches.values() if "native_actor_request" in r]
        self.assertEqual(len(approved), 25)
        for record in approved:
            source = sources[int(record["id"].split(":")[1], 16)]
            text, _ = adapt_actor_request_reference(refs[record["reference_id"]], source, record, info)
            text, _ = adapt_reference(text, source, info, "reference_layout", resident_runtime=True)
            output = encode(text, info)
            validate_actor_request_candidate(record["id"], source, output, matches)
            validate_entry(source, output, info, "message", "reference_layout", resident_runtime=True)
            def actors(data):
                return [t.data for t in tokenize(data, info) if t.kind == "cmd" and 8 <= t.data[1] <= 12]
            self.assertEqual(actors(output), actors(source))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"unadapted.json"
            record = matches["message:02B8"]
            path.write_text(json.dumps([{"id": record["id"], "source_sha256": record["source_sha256"],
                                         "translation": refs[record["id"]]["text"], "control_policy": "reference_layout"}]))
            with self.assertRaisesRegex(ValueError, "Native actor-request candidate"):
                apply_translations(rom, {}, path)


if __name__ == "__main__":
    unittest.main()
