"""A command-compatible review row never becomes a translation approval."""

import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from resident_review_queue import review_rows
from textcodec import encode


class ResidentReviewQueueTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[9] = self.info[12] = (5, 0)
        self.source = encode('Native{cmd:7F09000015}{cmd:7F00}', self.info)
        self.reference = self.ref('English{cmd:7F0900000B}{cmd:7F09000015}{cmd:7F00}')

    def ref(self, text):
        return {'id': 'message:0000', 'text': text, 'sha256': sha256(encode(text, self.info))}

    def review(self, reference=None, source=None, installed=None):
        return review_rows([source if source is not None else self.source],
                           {'message:0000': reference or self.reference}, installed or {}, self.info)

    def test_complete_local_review_is_explicitly_unapproved(self):
        rows, excluded = self.review()
        self.assertEqual(excluded, {})
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertFalse(row['approved'])
        self.assertEqual(row['review_status'], 'native_actor_and_topic_review_required')
        self.assertNotIn('translation', row)
        self.assertNotIn('resident_animations', row)
        self.assertEqual(row['source_sha256'], sha256(self.source))
        self.assertEqual(row['adapted_text'], self.reference['text'])

    def test_stale_installed_and_reference_inputs_fail(self):
        installed = {'message:0000': {'source_sha256': sha256(self.source)}}
        self.assertEqual(self.review(installed=installed), ([], {'already_has_candidate': 1}))
        with self.assertRaisesRegex(ValueError, 'stale installed'):
            self.review(installed={'message:0000': {'source_sha256': '0'*64}})
        self.assertEqual(self.review({**self.reference, 'sha256': '0'*64}),
                         ([], {'reference_encoding_or_hash_requires_review': 1}))
        with self.assertRaisesRegex(ValueError, 'mismatched English'):
            self.review({**self.reference, 'id': 'message:0001'})

    def test_empty_native_and_empty_english_stay_out_of_the_pool(self):
        self.assertEqual(self.review(source=encode('{cmd:7F00}', self.info)),
                         ([], {'native_without_static_text_needs_flow_review': 1}))
        self.assertEqual(self.review(self.ref('{cmd:7F00}')),
                         ([], {'no_visible_same_id_reference': 1}))

    def test_other_actor_fields_values_and_capacity_are_not_relaxed(self):
        for command in ('{cmd:7F09050001}', '{cmd:7F0C000001}', '{cmd:7F1A}', '{cmd:7F090000FE}'):
            rows, excluded = self.review(self.ref(command+self.reference['text']))
            self.assertEqual(rows, [])
            self.assertEqual(sum(excluded.values()), 1)
        rows, excluded = self.review(self.ref('A'*1024+self.reference['text']))
        self.assertEqual(rows, [])
        self.assertEqual(excluded, {'Expanded message bound exceeds 1024 bytes': 1})

    def test_reference_article_command_is_hashed_before_adaptation(self):
        source = self.source[:-2]+bytes.fromhex('7F317F00')
        reference = self.ref(self.reference['text'][:-10]+'{cmd:7F74}{cmd:7F31}{cmd:7F00}')
        rows, excluded = self.review(reference, source)
        self.assertEqual(excluded, {})
        self.assertIn('{cmd:7F74}', rows[0]['reference_text'])
        self.assertNotIn('{cmd:7F74}', rows[0]['adapted_text'])
        self.assertEqual(rows[0]['reference_sha256'], reference['sha256'])
        self.assertNotEqual(rows[0]['candidate_sha256'], reference['sha256'])
