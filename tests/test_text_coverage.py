"""Blank records, placeholders, and unreviewed candidates remain distinct."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"tools"))
from aflib import sha256
from textcodec import encode
from text_coverage import classify, coverage_rows, index_edits, summarise, text_volume


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
        for text in ("ダミー", "ダミー12\n", " ダミー 2{cmd:7F00}", 'よび',
                     'きしゃのデモ\nよびのエリア', 'ハロウィン\nよびメッセージ1'):
            self.assertEqual(self.classification(text)["category"], "development_placeholder_text")
        for text in ("ダミー12です", "ダミーのもじ", "あいうえお", 'よびとめて ごめん',
                     'きょうは げつようび', 'ハロウィン よびメッセージ1です'):
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

    def test_volume_weights_source_characters_not_longer_english_or_placeholders(self):
        source = [encode(text+'{cmd:7F00}', self.info) for text in
                  ('あい\n う', 'あいうえお', 'よび', 'Already English', '', '123')]
        edits = {'message:0000': {'source_sha256': sha256(source[0]),
                                 'translation': 'A much longer English sentence{cmd:7F00}'},
                 'message:0002': {'source_sha256': sha256(source[2]),
                                 'translation': 'Reserved{cmd:7F00}'}}
        rows = coverage_rows('message', source, edits, self.info)
        self.assertEqual(text_volume(rows), {'japanese_source_records': 2, 'english_candidate_records': 1,
                         'total_source_characters': 8, 'covered_source_characters': 3, 'coverage_percent': 37.5})
        self.assertEqual(summarise(rows)['japanese_text_volume'], text_volume(rows))

    def test_candidate_requires_decoded_static_replacement_and_allows_english_header_punctuation(self):
        source = encode('あいう{cmd:7F00}', self.info)
        for candidate in ('あいう{cmd:7F00}', '{cmd:7F00}', '{glyph:8000}{cmd:7F00}'):
            rows = coverage_rows('message', [source], {'message:0000': {
                   'source_sha256': sha256(source), 'translation': candidate}}, self.info)
            self.assertEqual(text_volume(rows)['covered_source_characters'], 0, candidate)
        rows = coverage_rows('message', [source], {'message:0000': {
               'source_sha256': sha256(source), 'translation': ',{cmd:7F00}'}}, self.info)
        self.assertEqual(text_volume(rows)['covered_source_characters'], 3)

    def test_empty_inventory_is_not_complete_and_identical_native_ids_count_separately(self):
        self.assertIsNone(text_volume([])['coverage_percent'])
        source = encode('あいう{cmd:7F00}', self.info)
        edits = {'message:0000': {'source_sha256': sha256(source), 'translation': 'Hello{cmd:7F00}'}}
        result = text_volume(coverage_rows('message', [source, source], edits, self.info))
        self.assertEqual(result['total_source_characters'], 6)
        self.assertEqual(result['covered_source_characters'], 3)
        self.assertEqual(result['coverage_percent'], 50.0)

    def test_known_dialogue_glyph_candidates_count_without_changing_native_classification(self):
        source = encode('あいう{cmd:7F00}', self.info)
        candidate = '☃Hello;{cmd:7F00}'
        rows = coverage_rows('message', [source], {'message:0000': {
            'source_sha256':sha256(source), 'translation':candidate}}, self.info)
        self.assertEqual(rows[0]['candidate']['category'], 'latin_static_text')
        self.assertEqual(text_volume(rows)['covered_source_characters'], 3)
        self.assertFalse(rows[0]['review_complete'])
        self.assertEqual(classify(b'\x80\xab',self.info)['category'], 'unmapped_visible_glyph_requires_review')
        self.assertEqual(classify(b'\x80\x42',self.info,extended_glyphs=True)['category'],
                         'unmapped_visible_glyph_requires_review')


if __name__ == "__main__":
    unittest.main()
