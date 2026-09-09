"""Reconstruct resolved-name grammar and retain code and immutable older profiles."""

import json
import unittest

import test_item_articles as legacy
from item_articles import RESOLVED_NAMES_HASH, RESOLVED_DATA_HASH, SHEET_NAMES_HASH, SIZE, verify, verify_names
from npc_mail_capture import source_report_matches

ROOT = legacy.ROOT


@unittest.skipUnless((ROOT/'build/resolved-items-articles/articles.bin').is_file(), 'Resolved local articles required')
class ResolvedItemArticleTests(legacy.ItemArticleTests):
    directory = ROOT/'build/resolved-items-articles'
    names_directory = ROOT/'build/resolved-items-resource'
    data_hash, names_hash, known_slots = RESOLVED_DATA_HASH, RESOLVED_NAMES_HASH, 4462

    def test_previous_generator_is_accepted_only_for_its_actual_profile(self):
        old = json.loads((ROOT/'build/sheet-items-creator/overlay.json').read_text())['sources']
        current = {**old, 'tools/item_articles.py': legacy.sha256((ROOT/'tools/item_articles.py').read_bytes())}
        self.assertTrue(source_report_matches(current, current, article_names=RESOLVED_NAMES_HASH))
        self.assertTrue(source_report_matches(old, current, article_names=SHEET_NAMES_HASH))
        self.assertFalse(source_report_matches(old, current, article_names=RESOLVED_NAMES_HASH))
        self.assertFalse(source_report_matches(old, current))
        changed = {**old, 'overlays/mail_generation/item_article.c': '0'*64}
        self.assertFalse(source_report_matches(changed, current, article_names=SHEET_NAMES_HASH))
        previous = (ROOT/'build/sheet-items-resource/names.bin').read_bytes()
        self.assertEqual(verify(self.data), RESOLVED_NAMES_HASH)
        with self.assertRaises(ValueError): verify_names(previous, 0x02A00000, RESOLVED_NAMES_HASH)
        with self.assertRaises(ValueError): verify_names(self.names, 0x02A00000, SHEET_NAMES_HASH)


@unittest.skipUnless((ROOT/'build/resolved-items-creator/overlay.json').is_file(), 'Complete resolved creator required')
class ResolvedCreatorTests(unittest.TestCase):
    def test_creator_code_symbols_relocations_and_other_data_remain_unchanged(self):
        old, new = [ROOT/'build'/name for name in ('sheet-items-creator', 'resolved-items-creator')]
        a, b = [json.loads((path/'overlay.json').read_text()) for path in (old, new)]
        self.assertEqual(a['symbols'], b['symbols'])
        self.assertEqual((b['bytes'], b['relocation_bytes']), (58144, 848))
        first, second = [(path/'overlay.bin').read_bytes() for path in (old, new)]
        at = a['symbols']['af_item_article_data']
        self.assertEqual(first[:at], second[:at])
        self.assertEqual(first[at+SIZE:], second[at+SIZE:])
        self.assertEqual(second[at:at+SIZE], (ROOT/'build/resolved-items-articles/articles.bin').read_bytes())
        self.assertEqual((old/'relocation.bin').read_bytes(), (new/'relocation.bin').read_bytes())
        self.assertEqual(b['item_articles_sha256'], RESOLVED_DATA_HASH)
        self.assertEqual(b['item_names_sha256'], RESOLVED_NAMES_HASH)


if __name__ == '__main__': unittest.main()
