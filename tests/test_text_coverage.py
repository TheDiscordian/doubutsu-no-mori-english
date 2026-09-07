"""Blank records, placeholders, and unreviewed candidates remain distinct."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from aflib import sha256
from textcodec import encode
from text_coverage import classify, coverage_rows, index_edits, summarise


class TextCoverageTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61

    def classification(self, text):
        return classify(encode(text, self.info), self.info)

    def test_blank_dynamic_records_are_not_unreachable(self):
        row = coverage_rows("message", [b"\x7f\x1a\xcd \x7f\x00"], {}, self.info)[0]
        self.assertEqual(row["source"]["category"], "no_visible_static_text")
        self.assertTrue(row["source"]["has_dynamic_insertions"])
        self.assertTrue(row["control_flow_audit_required"])
        self.assertEqual(row["reachability"], "not_established")
        self.assertFalse(row["review_complete"])
        self.assertEqual(summarise([row])["without_candidate_dynamic_only"], 1)

    def test_unknown_glyphs_and_truncated_commands_are_not_blank(self):
        for raw in (b"\x7f", b"\x7f\xff", b"\x80"):
            self.assertEqual(classify(raw, self.info)["category"], "undecodable_requires_review")
        self.assertEqual(classify(b"\x80\x00\x7f\x00", self.info)["category"],
                         "unmapped_visible_glyph_requires_review")

    def test_only_exact_placeholder_text_is_classified(self):
        for text in ("ダミー", "ダミー12\n", " ダミー 2{cmd:7F00}"):
            self.assertEqual(self.classification(text)["category"], "development_placeholder_text")
        for text in ("ダミー12です", "ダミーのもじ", "あいうえお"):
            self.assertEqual(self.classification(text)["category"], "japanese_static_text")
        self.assertEqual(self.classification("English{cmd:7F00}")["category"], "latin_static_text")
        self.assertEqual(self.classification("123 ♪♥")["category"], "numbers_or_symbols_only")
        dash = self.classification("An Englishーaside")
        self.assertEqual(dash["category"], "latin_static_text")
        self.assertEqual(dash["non_ascii_static_codepoints"], ["U+30FC"])

    def test_candidate_provenance_does_not_imply_completion(self):
        source = encode("あいう{cmd:7F00}", self.info)
        edit = {"id": "message:0000", "source_sha256": sha256(source),
                "translation": "Hello{cmd:7F00}", "status": "draft",
                "provenance": "Original translation"}
        for provenance in (edit["provenance"], {"reference_id": "message:0001", "match_basis": "test"}):
            edits = index_edits([{**edit, "provenance": provenance}])
            rows = coverage_rows("message", [source], edits, self.info)
            summary = summarise(rows)
            self.assertEqual(summary["candidate_records"], 1)
            self.assertEqual(summary["review_complete_records"], 0)
            self.assertFalse(rows[0]["review_complete"])
            self.assertEqual(rows[0]["candidate"]["category"], "latin_static_text")
        with self.assertRaisesRegex(ValueError, "Stale"):
            coverage_rows("message", [source+b" "], index_edits([edit]), self.info)
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            index_edits([edit, edit])


if __name__ == "__main__":
    unittest.main()
