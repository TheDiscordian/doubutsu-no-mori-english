"""Identity review exposes comparisons, not unchecked translation approvals."""

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from identity_review_queue import review_rows
from textcodec import encode


class IdentityReviewTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[9] = (5, 0)
        self.source = encode('Native{cmd:7F09000015}{cmd:7F00}', self.info)
        self.reference = self.ref('English{cmd:7F09000015}{cmd:7F00}')
        self.remaining = {'message:0000': 'same_id_not_confirmed_by_legacy'}

    def ref(self, text):
        return {'id': 'message:0000', 'text': text, 'sha256': sha256(encode(text, self.info))}

    def review(self, reference=None, source=None, installed=None, remaining=None):
        return review_rows([source if source is not None else self.source],
                           {'message:0000': reference or self.reference}, installed or {},
                           self.remaining if remaining is None else remaining, self.info)

    def test_queue_has_complete_hashes_but_no_installable_approval(self):
        rows, excluded = self.review()
        self.assertEqual(excluded, {})
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertFalse(row['approved'])
        self.assertEqual(row['review_status'], 'native_meaning_and_context_review_required')
        self.assertEqual(row['reference_sha256'], self.reference['sha256'])
        self.assertEqual(row['candidate_sha256'], self.reference['sha256'])
        for key in ('translation', 'complete_reference', 'resident_animations'):
            self.assertNotIn(key, row)

    def test_original_fallback_is_a_legitimate_rejected_reference(self):
        installed = {'message:0000': {'source_sha256': sha256(self.source), 'reference_fallback': True}}
        self.assertEqual(self.review(installed=installed),
                         ([], {'reference_rejection_has_original_fallback': 1}))
        for flag in (False, 1, 'true'):
            installed['message:0000']['reference_fallback'] = flag
            with self.assertRaisesRegex(ValueError, 'already has a candidate'):
                self.review(installed=installed)

    def test_stale_sources_and_unknown_ids_fail(self):
        for fallback in (True, False):
            with self.assertRaisesRegex(ValueError, 'Stale'):
                self.review(installed={'message:0000': {'source_sha256': '0'*64,
                                                       'reference_fallback': fallback}})
        with self.assertRaisesRegex(ValueError, 'Unknown'):
            self.review(remaining={'message:0001': 'same_id_not_confirmed_by_legacy'})
        with self.assertRaisesRegex(ValueError, 'Mismatched'):
            self.review({**self.reference, 'id': 'message:0001'})
        self.assertEqual(self.review({**self.reference, 'sha256': '0'*64}),
                         ([], {'reference_encoding_or_hash_requires_review': 1}))

    def test_other_rejections_and_installed_candidates_stay_out(self):
        self.assertEqual(self.review(remaining={'message:0000': 'Control signature changed'}), ([], {}))
        self.assertEqual(self.review(installed={'message:0000': {'source_sha256': sha256(self.source)}},
                                     remaining={}), ([], {}))
        self.assertEqual(self.review(self.ref('{cmd:7F00}')),
                         ([], {'no_visible_same_id_reference': 1}))
        self.assertEqual(self.review(source=encode('{cmd:7F00}', self.info)),
                         ([], {'native_without_static_text_needs_flow_review': 1}))

    def test_existing_policy_ladder_and_demo_restoration_are_preserved(self):
        rows, _ = self.review(self.ref('English{cmd:7F04}{cmd:7F02}{cmd:7F0900000B}{cmd:7F00}'))
        self.assertEqual(rows[0]['control_policy'], 'reference_delivery')
        self.assertIn('{cmd:7F09000015}', rows[0]['adapted_text'])
        self.assertIn('preserve_n64_demo_arguments', [c['operation'] for c in rows[0]['adaptations']])

    def test_fields_actor_sequence_and_capacity_stay_guarded(self):
        for text, error in (
                ('{cmd:7F1A}'+self.reference['text'], 'Reference requests a text field absent from the N64 message'),
                ('{cmd:7F09010001}'+self.reference['text'], 'Control signature changed'),
                ('A'*1024+self.reference['text'], 'Expanded message bound exceeds 1024 bytes')):
            self.assertEqual(self.review(self.ref(text)), ([], {error: 1}))

    def test_complete_article_reference_is_hashed_before_adaptation(self):
        source = self.source[:-2]+bytes.fromhex('7F317F00')
        reference = self.ref('English{cmd:7F09000015}{cmd:7F74}{cmd:7F31}{cmd:7F00}')
        rows, excluded = self.review(reference, source)
        self.assertEqual(excluded, {})
        self.assertIn('{cmd:7F74}', rows[0]['reference_text'])
        self.assertNotIn('{cmd:7F74}', rows[0]['adapted_text'])
        self.assertNotEqual(rows[0]['candidate_sha256'], reference['sha256'])
