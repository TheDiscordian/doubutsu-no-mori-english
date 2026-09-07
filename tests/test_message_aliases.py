"""Exact native aliases reject conflicting English and stale source evidence."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from aflib import sha256
from message_aliases import confirmed_message_aliases
from textcodec import decode


class MessageAliasTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.source = [b"Native\x7f\x00"]*3
        self.raw = b"English\xcdtext\x7f\x00"
        self.reference = {"id": "message:0000", "text": decode(self.raw, self.info), "sha256": sha256(self.raw)}
        self.edit = {"id": "message:0000", "source_sha256": sha256(self.source[0]),
                     "translation": self.reference["text"], "control_policy": "presentation",
                     "provenance": {"reference_id": self.reference["id"], "reference_sha256": self.reference["sha256"]},
                     "status": "mechanically_validated_candidate_not_reviewed", "adaptations": []}

    def aliases(self, edits=None, source=None, refs=None, **kw):
        return confirmed_message_aliases(self.source if source is None else source,
            [self.edit] if edits is None else edits, {self.reference["id"]: self.reference} if refs is None else refs,
            self.info, **kw)

    def test_exact_source_and_complete_output_are_retained(self):
        aliases, conflicts = self.aliases()
        self.assertEqual([r["id"] for r in aliases], ["message:0001", "message:0002"])
        self.assertEqual(conflicts, [])
        self.assertTrue(all(r["translation"] == self.edit["translation"] for r in aliases))
        self.assertTrue(all(r["status"] == self.edit["status"] for r in aliases))
        self.assertEqual(len(self.aliases(skip_ids={"message:0001"})[0]), 1)
        self.assertEqual(self.aliases(source=[self.source[0], self.source[0]+b" "])[0], [])

    def test_different_english_for_identical_source_is_withheld(self):
        raw = b"Different\x7f\x00"
        ref = {"id": "message:0001", "text": decode(raw, self.info), "sha256": sha256(raw)}
        edit = {**self.edit, "id": ref["id"], "translation": ref["text"],
                "provenance": {"reference_id": ref["id"], "reference_sha256": ref["sha256"]}}
        aliases, conflicts = self.aliases(edits=[self.edit, edit], refs={self.reference["id"]: self.reference, ref["id"]: ref})
        self.assertEqual(aliases, [])
        self.assertEqual([r["id"] for r in conflicts], ["message:0002"])

    def test_stale_sources_references_and_adapted_payloads_fail(self):
        for change in ({"source_sha256": "0"*64}, {"translation": self.edit["translation"]+" "}):
            with self.assertRaises(ValueError):
                self.aliases(edits=[{**self.edit, **change}])
        for change in ({"sha256": "0"*64}, {"text": "Changed"}):
            with self.assertRaises(ValueError):
                self.aliases(refs={self.reference["id"]: {**self.reference, **change}})
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.aliases(edits=[self.edit, self.edit])

    def test_drafts_and_sequence_permits_are_not_transferred(self):
        for change in ({"status": "draft"}, {"control_policy": "reviewed_sequence"},
                       {"provenance": "Original translation"}):
            self.assertEqual(self.aliases(edits=[{**self.edit, **change}]), ([], []))


if __name__ == "__main__":
    unittest.main()
