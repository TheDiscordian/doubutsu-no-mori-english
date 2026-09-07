"""Reviewed identity overrides never bypass source or control validation."""

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"tools"))
from aflib import sha256
from reference_matches import load_matches, resolve_reference, verify_native_equivalents
from reference_candidates import load_drafts
from textbanks import Bank, banks
from textcodec import command_info, encode
from aflib import CODE_VROM, by_vrom
from textvalidate import validate_entry
from test_retail import ROM_PATH


class ReferenceMatchTests(unittest.TestCase):
    def setUp(self):
        self.source = b"source"
        self.row = {"id": "select:0001", "source_sha256": sha256(self.source), "legacy": "different"}
        self.reference = {"id": "select:0002", "sha256": sha256(b"Test"), "text": "Test"}
        self.match = {"id": self.row["id"], "reference_id": self.reference["id"],
                      "source_sha256": self.row["source_sha256"],
                      "reference_sha256": self.reference["sha256"], "evidence": "Synthetic test match"}

    def test_reviewed_match_and_changed_sources(self):
        references = {self.reference["id"]: self.reference}
        matches = {self.row["id"]: self.match}
        result, basis, reason = resolve_reference(self.row, references, matches, self.source)
        self.assertIs(result, self.reference)
        self.assertEqual(basis, "reviewed_identity")
        self.assertIsNone(reason)
        for source, refs in ((b"changed", references), (self.source, {}),
                             (self.source, {self.reference["id"]: {**self.reference, "sha256": "0"*64}})):
            with self.assertRaisesRegex(ValueError, "Stale"):
                resolve_reference(self.row, refs, matches, source)
        # Identity matching does not give permission to alter commands or limits.
        with self.assertRaisesRegex(ValueError, "signature"):
            validate_entry(b"A\x7f\x00", b"Test", [(2, 0)]*0x61, "select")

    def test_legacy_confirmation_is_unchanged(self):
        ref = {**self.reference, "id": self.row["id"]}
        refs = {ref["id"]: ref}
        self.assertEqual(resolve_reference(self.row, refs, {}, self.source)[2],
                         "same_id_not_confirmed_by_legacy")
        row = {**self.row, "legacy": "Test"}
        self.assertEqual(resolve_reference(row, refs, {}, self.source)[1], "same_id_confirmed_by_legacy")

    def test_match_file_rejects_bad_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/"matches.json"
            path.write_text(json.dumps([self.match]))
            self.assertEqual(load_matches(path)[self.row["id"]], self.match)
            for records in ([self.match, self.match], [{**self.match, "evidence": ""}],
                            [{**self.match, "reference_id": "mail:0002"}],
                            [{**self.match, "source_sha256": "invalid"}], {}):
                path.write_text(json.dumps(records))
                with self.assertRaises(ValueError):
                    load_matches(path)

    def test_repository_matches_have_explanations_and_hashes(self):
        self.assertIn("select:0013", load_matches(ROOT/"translations/reference_matches.json"))

    def test_native_equivalence_is_exact_and_bounded(self):
        bank = Bank("select", 0, None, b"AA", None, fixed_size=1)
        match = {**self.match, "source_sha256": sha256(b"A"), "native_equivalent_id": "select:0001"}
        verify_native_equivalents({"select:0000": match}, {"select": bank})
        for change in ({"source_sha256": sha256(b"B")}, {"native_equivalent_id": "select:0002"}):
            with self.assertRaisesRegex(ValueError, "native-equivalent"):
                verify_native_equivalents({"select:0000": {**match, **change}}, {"select": bank})

    @unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM is a local-only optional test input")
    def test_reviewed_native_equivalents_match_retail(self):
        matches = load_matches(ROOT/"translations/reference_matches.json")
        source = {b.name: b for b in banks(ROM_PATH.read_bytes())}
        verify_native_equivalents(matches, source)
        for match in matches.values():
            if "native_equivalent_id" in match:
                name, number = match["id"].split(":")
                self.assertEqual(sha256(source[name].entries()[int(number, 16)]), match["source_sha256"])

    def test_multiple_original_files_reject_duplicate_ids(self):
        opening = ROOT/"translations/opening.json"
        exercise = ROOT/"translations/n64-exercise.json"
        self.assertEqual(len(load_drafts([opening, exercise])), 8)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            load_drafts([opening, opening])

    @unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM is a local-only optional test input")
    def test_exercise_translations_preserve_every_native_command(self):
        rom = ROM_PATH.read_bytes()
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
        entries = next(bank for bank in banks(rom) if bank.name == "message").entries()
        for edit in load_drafts([ROOT/"translations/n64-exercise.json"]):
            original = entries[int(edit["id"].split(":")[1], 16)]
            self.assertEqual(sha256(original), edit["source_sha256"])
            translated = encode(edit["translation"], info)
            validate_entry(original, translated, info, "message")
            self.assertTrue(translated.endswith(b"\x7f\x00"))

    @unittest.skipUnless(ROM_PATH.is_file(), "Retail ROM is a local-only optional test input")
    def test_intro_job_drafts_preserve_native_fields_and_delivery(self):
        rom = ROM_PATH.read_bytes()
        info = command_info(by_vrom(rom)[CODE_VROM].extract(rom))
        entries = next(bank for bank in banks(rom) if bank.name == "message").entries()
        edits = load_drafts([ROOT/"translations/n64-intro-jobs.json"])
        self.assertEqual({r["id"] for r in edits}, {"message:07EB", "message:0821", "message:0822"})
        for edit in edits:
            original = entries[int(edit["id"].split(":")[1], 16)]
            self.assertEqual(sha256(original), edit["source_sha256"])
            translated = encode(edit["translation"], info)
            validate_entry(original, translated, info, "message")
            self.assertEqual(translated.count(b"\x7f\x02"), original.count(b"\x7f\x02"))
            self.assertEqual(translated[-2:], original[-2:])
            for unsupported in ("mayor", "wishing well", "shrine"):
                self.assertNotIn(unsupported, edit["translation"].lower())
