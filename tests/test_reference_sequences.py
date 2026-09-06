"""Reviewed sequence identity cannot bypass flow, completeness, or size guards."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import CODE_VROM, by_vrom, sha256
from reference_sequences import (audit_sequence, load_sequences, message_targets,
                                 reference_sequence_edits, validate_sequences)
from textbanks import banks
from textcodec import command_info, encode
from textvalidate import validate_entry
from test_retail import ROM_PATH


class ReferenceSequenceTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        for code in range(0x0E, 0x13):
            self.info[code] = (4, 0)
        self.info[0x09] = (5, 0)
        self.info[0x13], self.info[0x14], self.info[0x15] = (6, 0), (8, 0), (10, 0)
        self.original = b"A\x7f\x1a\x7f\x09\x00\x00\x03\x7f\x10\x00\x07\x7f\x0f\x00\x08\x7f\x01"
        self.source = [self.original, b"Reserved\x7f\x00"]
        self.texts = ["First{cmd:7F0E0001}{cmd:7F01}",
                      "Second{cmd:7F1A}{cmd:7F09000003}{cmd:7F0F0008}{cmd:7F100007}{cmd:7F01}"]
        self.references = {f"message:{i:04X}": {"id": f"message:{i:04X}", "text": text,
                                               "sha256": sha256(encode(text, self.info))}
                           for i, text in enumerate(self.texts)}
        self.groups = {"test_sequence": {"id": "test_sequence", "evidence": "Synthetic flow test",
                                        "members": [{"id": f"message:{i:04X}",
                                                     "source_sha256": sha256(self.source[i]),
                                                     "encoded_sha256": ref["sha256"],
                                                     "reference_sha256": ref["sha256"]}
                                                    for i, ref in enumerate(self.references.values())]}}
        self.edits, self.permits = reference_sequence_edits(self.references, self.source, self.info, self.groups)

    def test_complete_sequence_with_reordered_branch_assignments(self):
        for i, edit in enumerate(self.edits):
            validate_entry(self.source[i], encode(edit["translation"], self.info), self.info,
                           "message", "reviewed_sequence", sequence_permit=self.permits[edit["id"]])

    def test_partial_unknown_and_spurious_sequence_requests(self):
        for edits in (self.edits[:1], [{**self.edits[0], "reference_sequence": "unknown"}],
                      [{**self.edits[0], "control_policy": "exact"}],
                      [*self.edits, self.edits[0]],
                      [*self.edits, {**self.edits[0], "id": "message:0002"}]):
            with self.assertRaises(ValueError):
                validate_sequences(edits, self.source, self.info, self.groups)
        with self.assertRaisesRegex(ValueError, "complete hash-bound"):
            validate_entry(self.source[0], encode(self.texts[0], self.info), self.info,
                           "message", "reviewed_sequence")

    def test_changed_sources_references_and_payloads(self):
        for key, value in (("translation", "Changed{cmd:7F01}"), ("source_sha256", "0"*64)):
            edits = deepcopy(self.edits)
            edits[1][key] = value
            with self.assertRaises(ValueError):
                validate_sequences(edits, self.source, self.info, self.groups)
        with self.assertRaisesRegex(ValueError, "placeholder"):
            validate_sequences(self.edits, [self.original, b"Other"], self.info, self.groups)
        with self.assertRaisesRegex(ValueError, "reference"):
            reference_sequence_edits({}, self.source, self.info, self.groups)

    def test_native_incoming_branches_reserve_slots(self):
        for command in ("7F0E0001", "7F1300090001", "7F14000900080001", "7F150009000800070001"):
            data = bytes.fromhex(command)+b"\x7f\x01"
            self.assertIn(1, list(message_targets(data, self.info)))
            with self.assertRaisesRegex(ValueError, "reserved sequence slot"):
                validate_sequences(self.edits, [*self.source, data], self.info, self.groups)

    def test_structural_audit_independent_of_hashes(self):
        parts = [encode(text, self.info) for text in self.texts]
        for before, after in ((b"\x7f\x0f\x00\x08", b"\x7f\x0f\x00\x09"),
                              (b"\x7f\x1a", b"\x7f\x1b"),
                              (b"\x7f\x09\x00\x00\x03", b"\x7f\x09\x00\x00\x07"),
                              (b"\x7f\x01", b"\x7f\x00")):
            with self.assertRaises(ValueError):
                audit_sequence(self.original, [parts[0], parts[1].replace(before, after)], [0, 1], self.info)
        with self.assertRaisesRegex(ValueError, "continuation"):
            audit_sequence(self.original, [parts[0].replace(b"\x0e\x00\x01", b"\x0e\x00\x02"), parts[1]],
                           [0, 1], self.info)

    def test_capacity_guard_still_applies(self):
        refs, groups = deepcopy(self.references), deepcopy(self.groups)
        refs["message:0000"]["text"] = "A"*1024+self.texts[0]
        digest = sha256(encode(refs["message:0000"]["text"], self.info))
        refs["message:0000"]["sha256"] = digest
        groups["test_sequence"]["members"][0].update(reference_sha256=digest, encoded_sha256=digest)
        edits, permits = reference_sequence_edits(refs, self.source, self.info, groups)
        with self.assertRaisesRegex(ValueError, "1024"):
            validate_entry(self.source[0], encode(edits[0]["translation"], self.info), self.info,
                           "message", "reviewed_sequence", sequence_permit=permits["message:0000"])

    def test_approval_schema(self):
        record = self.groups["test_sequence"]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"sequences.json"
            path.write_text(json.dumps([record]))
            self.assertEqual(load_sequences(path), self.groups)
            for records in ({}, [record, record], [{**record, "members": []}],
                            [{**record, "evidence": ""}]):
                path.write_text(json.dumps(records))
                with self.assertRaises(ValueError):
                    load_sequences(path)

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/text/message.jsonl").is_file(),
                         "Retail ROM and English text extraction are local-only test inputs")
    def test_home_explanation_retail_slots_and_reference(self):
        rom = ROM_PATH.read_bytes()
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
        entries = next(b for b in banks(rom) if b.name == "message").entries()
        references = {row["id"]: row for row in map(json.loads, (ROOT/"build/gamecube/text/message.jsonl").read_text().splitlines())}
        edits, permits = reference_sequence_edits(references, entries, info)
        self.assertEqual(len(edits), 4)
        for edit in edits:
            original = entries[int(edit["id"].split(":")[1], 16)]
            validate_entry(original, encode(edit["translation"], info), info, "message", "reviewed_sequence",
                           sequence_permit=permits[edit["id"]])
