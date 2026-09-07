"""Added player/town fields need an exact approval, not a general relaxed policy."""

from copy import deepcopy
from dataclasses import replace
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
from reference_fields import (ReferenceFieldPermit, field_permit, validate_field_approval,
                              verify_field_reference)
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode
from textvalidate import validate_entry
from test_retail import ROM_PATH


class ReferenceFieldTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[0x0E] = (4, 0)
        self.source = b"Native\x7f\x00"
        self.output = b"Hello \x7f\x1a\xcdWelcome to \x7f\x2f.\x7f\x00"
        self.record = {"id": "message:0000", "reference_id": "message:0000",
                       "source_sha256": sha256(self.source), "reference_sha256": sha256(self.output),
                       "available_fields": {"commands": ["1A", "2F"], "adapted_sha256": sha256(self.output)}}
        self.reference = {"id": "message:0000", "sha256": sha256(self.output),
                          "text": decode(self.output, self.info)}

    def permit(self, record=None, source=None, candidate=None):
        return field_permit("message:0000", self.source if source is None else source,
                            self.output if candidate is None else candidate,
                            {"message:0000": self.record if record is None else record})

    def test_exact_payload_and_source_admit_only_approved_fields(self):
        verify_field_reference(self.reference, self.source, self.record, self.info)
        permit = self.permit()
        self.assertIsInstance(permit, ReferenceFieldPermit)
        self.assertEqual(permit.fields, frozenset({0x1A, 0x2F}))
        validate_entry(self.source, self.output, self.info, "message", "reference_layout",
                       resident_runtime=True, field_permit=permit)
        with self.assertRaisesRegex(ValueError, "field absent"):
            validate_entry(self.source, self.output, self.info, "message", "reference_layout", resident_runtime=True)
        self.assertIsNone(field_permit("message:0001", self.source, self.output, {}))

    def test_reference_hash_includes_redundant_article_prefix(self):
        raw = b"Here: \x7f\x74\x7f\x2f.\x7f\x00"
        record = {**self.record, "reference_sha256": sha256(raw)}
        reference = {**self.reference, "sha256": sha256(raw), "text": decode(raw, self.info)}
        native_info = list(self.info)
        native_info[0x74] = (0, 0)
        verify_field_reference(reference, self.source, record, native_info)
        with self.assertRaisesRegex(ValueError, "Stale"):
            verify_field_reference({**reference, "text": reference["text"].replace("{cmd:7F74}", "")},
                                   self.source, record, native_info)

    def test_changed_evidence_and_payloads_fail(self):
        for ref, source in ((self.reference, b"Other"),
                            ({**self.reference, "id": "message:0001"}, self.source),
                            ({**self.reference, "sha256": "0"*64}, self.source),
                            ({**self.reference, "text": "Other"}, self.source)):
            with self.assertRaisesRegex(ValueError, "Stale"):
                verify_field_reference(ref, source, self.record, self.info)
        for source, candidate in ((b"Other", self.output), (self.source, self.output+b" "),
                                  (self.source, self.output.replace(b"\xcd", b" "))):
            with self.assertRaisesRegex(ValueError, "complete approval"):
                self.permit(source=source, candidate=candidate)

    def test_schema_excludes_other_fields_and_combined_approvals(self):
        for rule in ({"commands": []}, {"commands": ["1C"]}, {"commands": ["25"]},
                     {"commands": ["1A", "1A"]}, {"commands": ["2F", "1A"]},
                     {"commands": [26]}, {"commands": "1A"}, {"commands": [None]},
                     {"adapted_sha256": "A"*64}, {"adapted_sha256": None}, {"extra": True}):
            record = deepcopy(self.record)
            record["available_fields"].update(rule)
            with self.assertRaises(ValueError):
                validate_field_approval(record)
        for change in ({"controller": {}}, {"native_choices": {}}, {"native_actor_request": {}},
                       {"id": "select:0000"}, {"available_fields": None}):
            with self.assertRaises(ValueError):
                validate_field_approval({**self.record, **change})

    def test_permit_type_hash_scope_and_exact_added_set_are_checked(self):
        permit = self.permit()
        for invalid in ({}, {"fields": [26, 47]}, replace(permit, source_sha256="0"*64),
                        replace(permit, encoded_sha256="0"*64), replace(permit, fields=frozenset()),
                        replace(permit, fields=frozenset({0x1C}))):
            with self.assertRaisesRegex(ValueError, "complete reviewed"):
                validate_entry(self.source, self.output, self.info, "message", "reference_layout",
                               resident_runtime=True, field_permit=invalid)
        for bank, policy, runtime in (("select", "reference_layout", True),
                                     ("message", "reference_text", True), ("message", "exact", True),
                                     ("message", "reference_layout", False)):
            with self.assertRaisesRegex(ValueError, "complete reviewed"):
                validate_entry(self.source, self.output, self.info, bank, policy,
                               resident_runtime=runtime, field_permit=permit)
        with self.assertRaisesRegex(ValueError, "exact reviewed"):
            validate_entry(self.source, self.output, self.info, "message", "reference_layout",
                           resident_runtime=True, field_permit=replace(permit, fields=frozenset({0x1A})))

    def test_flow_and_capacity_still_fail_even_with_matching_permit_hash(self):
        for output, reason in ((self.output.replace(b"\x7f\x00", b"\x7f\x0e\x00\x01\x7f\x00"), "signature"),
                               (b"a"*1000+self.output, "1024")):
            permit = replace(self.permit(), encoded_sha256=sha256(output))
            with self.assertRaisesRegex(ValueError, reason):
                validate_entry(self.source, output, self.info, "message", "reference_layout",
                               resident_runtime=True, field_permit=permit)

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/text/message.jsonl").is_file(),
                         "Retail and English reference inputs remain local")
    def test_all_retail_approvals_and_independent_builder_rejection(self):
        rom = ROM_PATH.read_bytes()
        info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == "message").entries()
        refs = {r["id"]: r for r in map(json.loads, (ROOT/"build/gamecube/text/message.jsonl").read_text().splitlines())}
        matches = load_matches(ROOT/"translations/reference_matches.json")
        approved = [r for r in matches.values() if "available_fields" in r]
        self.assertEqual(len(approved), 26)
        for record in approved:
            source = sources[int(record["id"].split(":")[1], 16)]
            verify_field_reference(refs[record["reference_id"]], source, record, info)
            text, _ = adapt_reference(refs[record["reference_id"]]["text"], source, info,
                                      "reference_layout", resident_runtime=True)
            output = encode(text, info)
            permit = field_permit(record["id"], source, output, matches)
            validate_entry(source, output, info, "message", "reference_layout",
                           resident_runtime=True, field_permit=permit)
            with self.assertRaisesRegex(ValueError, "field absent"):
                validate_entry(source, output, info, "message", "reference_layout", resident_runtime=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"changed.json"
            record = matches["message:02C5"]
            path.write_text(json.dumps([{"id": record["id"], "source_sha256": record["source_sha256"],
                                         "translation": refs[record["id"]]["text"]+" ",
                                         "control_policy": "reference_layout", "available_fields": ["2F"]}]))
            with self.assertRaisesRegex(ValueError, "Reviewed field candidate"):
                apply_translations(rom, {}, path)


if __name__ == "__main__":
    unittest.main()
