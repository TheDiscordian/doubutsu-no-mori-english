"""Run every native creator contract through the complete glyph variant."""

import ctypes as C
from pathlib import Path
import unittest

import test_academy_score_creator as score_tests


@unittest.skipUnless((Path(__file__).resolve().parents[1]/'build/mail-glyph-catalog/catalog.bin').is_file(),
                     'Complete local glyph catalogue required')
class MailGlyphCreatorTests(score_tests.AcademyScoreCreatorTests):
    catalog_id = 4
    catalog_path = Path(__file__).resolve().parents[1]/'build/mail-glyph-catalog/catalog.bin'

    def test_compiled_catalogue_identity_and_previously_missing_reply_footer(self):
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_npc_mail_catalog_id').value,4)
        # Local personality one owns composite group 0040..005F. Choose the
        # original unavailable 004D footer without changing the other draws.
        for capital in (0,1):
            fixture = self.fixture(looks=1,capital=capital)
            self.ids[4] = 0x4D
            result = self.invoke(fixture)
            self.assertEqual(result.templates[4],0x4D)


if __name__ == '__main__': unittest.main()
