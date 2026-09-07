"""Resident-speaker approvals cannot become general added-field permissions."""

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
from reference_fields import (SpeakerCatchphrasePermit, catchphrase_permit,
                              validate_catchphrase_approval, verify_catchphrase_reference)
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode
from textvalidate import validate_entry
from test_retail import ROM_PATH


class ReferenceCatchphraseTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[0x0E] = (4, 0)
        self.source = b"Native\x7f\x00"
        self.output = b"Hello,\xcd\x7f\x1c!\x7f\x00"
        self.record = {"id": "message:0000", "reference_id": "message:0000",
                       "source_sha256": sha256(self.source), "reference_sha256": sha256(self.output),
                       "speaker_catchphrase": {"context": "native_resident_talk",
                                               "adapted_sha256": sha256(self.output)}}
        self.reference = {"id": self.record["id"], "sha256": sha256(self.output),
                          "text": decode(self.output, self.info)}

    def permit(self, record=None, source=None, output=None):
        return catchphrase_permit(self.record["id"], self.source if source is None else source,
                                  self.output if output is None else output,
                                  {self.record["id"]: self.record if record is None else record})

    def test_exact_approval_and_default_rejection(self):
        verify_catchphrase_reference(self.reference, self.source, self.record, self.info)
        permit = self.permit()
        self.assertIsInstance(permit, SpeakerCatchphrasePermit)
        validate_entry(self.source, self.output, self.info, "message", "reference_layout",
                       resident_runtime=True, catchphrase_permit=permit)
        with self.assertRaisesRegex(ValueError, "field absent"):
            validate_entry(self.source, self.output, self.info, "message", "reference_layout", resident_runtime=True)
        self.assertIsNone(catchphrase_permit("message:0001", self.source, self.output, {}))

    def test_stale_source_reference_and_output_rejected(self):
        for ref, source in ((self.reference, b"Other"),
                            ({**self.reference, "id": "message:0001"}, self.source),
                            ({**self.reference, "sha256": "0"*64}, self.source),
                            ({**self.reference, "text": "Other"}, self.source)):
            with self.assertRaisesRegex(ValueError, "Stale"):
                verify_catchphrase_reference(ref, source, self.record, self.info)
        for source, output in ((b"Other", self.output), (self.source, self.output+b" "),
                               (self.source, self.output.replace(b"\xcd", b" "))):
            with self.assertRaisesRegex(ValueError, "complete approval"):
                self.permit(source=source, output=output)

    def test_complete_reference_includes_article_prefix(self):
        source = b"Native \x7f\x2f\x7f\x00"
        raw = b"Hello \x7f\x74\x7f\x2f, \x7f\x1c!\x7f\x00"
        record = {**self.record, "source_sha256": sha256(source), "reference_sha256": sha256(raw)}
        reference = {**self.reference, "sha256": sha256(raw), "text": decode(raw, self.info)}
        info = list(self.info)
        info[0x74] = (0, 0)
        verify_catchphrase_reference(reference, source, record, info)
        with self.assertRaisesRegex(ValueError, "Stale"):
            verify_catchphrase_reference({**reference, "text": reference["text"].replace("{cmd:7F74}", "")},
                                         source, record, info)

    def test_schema_requires_only_the_reviewed_resident_context(self):
        for change in ({"context": "actorless"}, {"context": None}, {"context": ["native_resident_talk"]},
                       {"adapted_sha256": "A"*64}, {"adapted_sha256": None}, {"commands": ["1C"]}):
            record = deepcopy(self.record)
            record["speaker_catchphrase"].update(change)
            with self.assertRaises(ValueError):
                validate_catchphrase_approval(record)
        for change in ({"id": "select:0000"}, {"speaker_catchphrase": None},
                       {"controller": {}}, {"native_choices": {}}, {"native_actor_request": {}},
                       {"available_fields": {}}):
            with self.assertRaises(ValueError):
                validate_catchphrase_approval({**self.record, **change})

    def test_type_hash_policy_runtime_and_combined_permits_rejected(self):
        permit = self.permit()
        for invalid in ({}, {"context": "native_resident_talk"}, replace(permit, context="actorless"),
                        replace(permit, source_sha256="0"*64), replace(permit, encoded_sha256="0"*64)):
            with self.assertRaisesRegex(ValueError, "complete reviewed"):
                validate_entry(self.source, self.output, self.info, "message", "reference_layout",
                               resident_runtime=True, catchphrase_permit=invalid)
        for bank, policy, runtime in (("select", "reference_layout", True),
                                     ("message", "reference_text", True), ("message", "exact", True),
                                     ("message", "reference_layout", False)):
            with self.assertRaisesRegex(ValueError, "complete reviewed"):
                validate_entry(self.source, self.output, self.info, bank, policy,
                               resident_runtime=runtime, catchphrase_permit=permit)
        with self.assertRaisesRegex(ValueError, "complete reviewed"):
            validate_entry(self.source, self.output, self.info, "message", "reference_layout",
                           resident_runtime=True, catchphrase_permit=permit, sequence_permit=object())

    def test_no_other_fields_and_no_redundant_permission(self):
        for output in (self.output.replace(b"\x7f\x1c", b"\x7f\x1a"),
                       self.output.replace(b"\x7f\x1c", b"\x7f\x1c\x7f\x2f"),
                       self.output.replace(b"\x7f\x1c", b"")):
            permit = replace(self.permit(), encoded_sha256=sha256(output))
            with self.assertRaisesRegex(ValueError, "exact reviewed catchphrase"):
                validate_entry(self.source, output, self.info, "message", "reference_layout",
                               resident_runtime=True, catchphrase_permit=permit)
        source = self.source+b"\x7f\x1c"
        permit = replace(self.permit(), source_sha256=sha256(source))
        with self.assertRaisesRegex(ValueError, "exact reviewed catchphrase"):
            validate_entry(source, self.output, self.info, "message", "reference_layout",
                           resident_runtime=True, catchphrase_permit=permit)

    def test_flow_and_capacity_checks_remain(self):
        for output, reason in ((self.output.replace(b"\x7f\x00", b"\x7f\x0e\x00\x01\x7f\x00"), "signature"),
                               (b"a"*1000+self.output, "1024")):
            permit = replace(self.permit(), encoded_sha256=sha256(output))
            with self.assertRaisesRegex(ValueError, reason):
                validate_entry(self.source, output, self.info, "message", "reference_layout",
                               resident_runtime=True, catchphrase_permit=permit)

    @unittest.skipUnless(ROM_PATH.is_file() and (ROOT/"build/gamecube/text/message.jsonl").is_file(),
                         "Retail and English reference inputs remain local")
    def test_all_retail_approvals_and_independent_builder_rejection(self):
        rom = ROM_PATH.read_bytes()
        info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == "message").entries()
        refs = {r["id"]: r for r in map(json.loads, (ROOT/"build/gamecube/text/message.jsonl").read_text().splitlines())}
        matches = load_matches(ROOT/"translations/reference_matches.json")
        approved = [r for r in matches.values() if "speaker_catchphrase" in r]
        expected_ids = "036A 039A 03BB 03BF 0428 042D 0439 0524 084A 0AE2 0F30 129D 16CA 1AEC 1E24 1F6F 202D 2227 258B 25B9 25BA 25BC 2610 2703 271F 282B 2840".split()
        self.assertEqual({r["id"] for r in approved}, {"message:"+id for id in expected_ids})
        for record in approved:
            source = sources[int(record["id"].split(":")[1], 16)]
            reference = refs[record["reference_id"]]
            verify_catchphrase_reference(reference, source, record, info)
            text, _ = adapt_reference(reference["text"], source, info, "reference_layout", resident_runtime=True)
            output = encode(text, info)
            permit = catchphrase_permit(record["id"], source, output, matches)
            validate_entry(source, output, info, "message", "reference_layout",
                           resident_runtime=True, catchphrase_permit=permit)
            with self.assertRaisesRegex(ValueError, "field absent"):
                validate_entry(source, output, info, "message", "reference_layout", resident_runtime=True)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/"changed.json"
            record = matches["message:036A"]
            path.write_text(json.dumps([{"id": record["id"], "source_sha256": record["source_sha256"],
                                         "translation": refs[record["id"]]["text"]+" ",
                                         "control_policy": "reference_layout", "speaker_catchphrase": True}]))
            with self.assertRaisesRegex(ValueError, "Reviewed catchphrase candidate"):
                apply_translations(rom, {}, path)


if __name__ == "__main__":
    unittest.main()
