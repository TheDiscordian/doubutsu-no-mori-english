"""The expanded name resource and treasure grammar remain coupled exactly."""

import json
import unittest

import test_item_articles as legacy
from item_articles import NAMES_HASH, SHEET_NAMES_HASH, SHEET_DATA_HASH, SIZE, verify, verify_names
from npc_mail_capture import source_report_matches

ROOT = legacy.ROOT


@unittest.skipUnless((ROOT/'build/sheet-items-articles/articles.bin').is_file(), 'Expanded local articles required')
class SheetItemArticleTests(legacy.ItemArticleTests):
    directory = ROOT/'build/sheet-items-articles'
    names_directory = ROOT/'build/sheet-items-resource'
    data_hash, names_hash, known_slots = SHEET_DATA_HASH, SHEET_NAMES_HASH, 4397

    def test_valid_profiles_cannot_be_cross_installed_or_forged(self):
        old = (ROOT/'build/noticeboard-treasure/articles/articles.bin').read_bytes()
        old_names = (ROOT/'build/native-items-resource/names.bin').read_bytes()
        self.assertEqual(verify(old), NAMES_HASH)
        self.assertEqual(verify(self.data), SHEET_NAMES_HASH)
        for data, expected in ((old_names, SHEET_NAMES_HASH), (self.names, NAMES_HASH), (self.names, '0'*64)):
            with self.assertRaises(ValueError): verify_names(data, 0x02A00000, expected)
        with self.assertRaises(ValueError): verify(old[:16]+self.data[16:48]+old[48:])
        with self.assertRaises(ValueError): verify(self.data[:16]+old[16:48]+self.data[48:])

    def test_previous_generator_provenance_is_limited_to_its_actual_immutable_profile(self):
        old = json.loads((ROOT/'build/noticeboard-seasonal/creator/overlay.json').read_text())['sources']
        current = {**old, 'tools/item_articles.py': legacy.sha256((ROOT/'tools/item_articles.py').read_bytes())}
        self.assertTrue(source_report_matches(current, current, article_names=SHEET_NAMES_HASH))
        self.assertTrue(source_report_matches(old, current, article_names=NAMES_HASH))
        self.assertFalse(source_report_matches(old, current, article_names=SHEET_NAMES_HASH))
        self.assertFalse(source_report_matches(old, current))
        broken = {**old, 'overlays/mail_generation/notice_owner.c': '0'*64}
        self.assertFalse(source_report_matches(broken, current, article_names=NAMES_HASH))


@unittest.skipUnless((ROOT/'build/sheet-items-creator/overlay.json').is_file(), 'Complete expanded creator required')
class SheetCreatorArtifactTests(unittest.TestCase):
    def test_only_compiled_article_data_changes_in_complete_creator(self):
        previous, current = [ROOT/'build'/name for name in ('noticeboard-seasonal/creator', 'sheet-items-creator')]
        old, new = [json.loads((directory/'overlay.json').read_text()) for directory in (previous, current)]
        self.assertEqual(old['symbols'], new['symbols'])
        self.assertEqual((new['bytes'], new['relocation_bytes']), (58144, 848))
        a, b = [(directory/'overlay.bin').read_bytes() for directory in (previous, current)]
        at = old['symbols']['af_item_article_data']
        self.assertEqual(a[:at], b[:at])
        self.assertEqual(a[at+SIZE:], b[at+SIZE:])
        self.assertEqual(b[at:at+SIZE], (ROOT/'build/sheet-items-articles/articles.bin').read_bytes())
        self.assertEqual((previous/'relocation.bin').read_bytes(), (current/'relocation.bin').read_bytes())
        self.assertEqual(new['item_articles_sha256'], SHEET_DATA_HASH)
        self.assertEqual(new['item_names_sha256'], SHEET_NAMES_HASH)


if __name__ == '__main__': unittest.main()
