"""Fast accounting checks; no ROM or donor assets required."""

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from textcodec import encode
from translation_progress import CounterLedger


class TranslationProgressTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.ledger = CounterLedger(self.info)

    def add(self, identity, text):
        self.ledger.add(identity, encode(text, self.info))

    def test_source_weight_and_duplicate_routes(self):
        self.add('string:0000', 'あいうえ')
        self.add('mail:0000', 'あい')
        self.ledger.credit('string:0000', b'A much longer English phrase', 'bank')
        self.ledger.credit('string:0000', b'English', 'name_resource')
        result = self.ledger.summary()
        self.assertEqual(result['total_source_characters'], 6)
        self.assertEqual(result['replaced_source_characters'], 4)
        self.assertEqual(result['percent'], 66.7)

    def test_japanese_candidate_is_not_english(self):
        self.add('mail:0000', 'あい')
        self.ledger.credit('mail:0000', encode('Aあ', self.info), 'mail', mail=True)
        self.assertEqual(self.ledger.summary()['percent'], 0)

    def test_letters_and_names_share_the_total(self):
        self.add('mail:0000', 'あいうえ')
        self.add('npc_names:0000', 'あい')
        self.ledger.credit('mail:0000', b'Letter\x7f\x74', 'npc_letters', mail=True)
        self.assertEqual(self.ledger.summary()['percent'], 66.7)
        self.ledger.credit('npc_names:0000', b'Name', 'display_names')
        self.assertEqual(self.ledger.summary()['percent'], 100)

    def test_source_ids_are_unique_and_donor_only_ids_cannot_count(self):
        self.add('mail:0000', 'あい')
        with self.assertRaises(ValueError):
            self.add('mail:0000', 'あい')
        with self.assertRaises(KeyError):
            self.ledger.credit('mail:FFFF', b'GC-only letter', 'mail', mail=True)

    def test_whitespace_latin_and_controls_do_not_expand_denominator(self):
        self.add('string:0000', ' あ い\n{cmd:7F24}')
        self.add('string:0001', 'Already English')
        self.assertEqual(self.ledger.summary()['total_source_characters'], 2)

    def test_development_labels_are_still_japanese_text(self):
        self.add('message:0000', 'ダミー')
        self.ledger.credit('message:0000', b'Dummy', 'bank')
        self.assertEqual(self.ledger.summary()['total_source_characters'], 3)
        self.assertEqual(self.ledger.summary()['percent'], 100)


if __name__ == '__main__':
    unittest.main()
