"""The missing-glyph audit walks whole parts without interpreting arguments."""

from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from audit_mail_glyphs import missing_glyphs


class MailGlyphAuditTests(unittest.TestCase):
    def setUp(self):
        self.tables = {'CHAR_MAP':['a']*256,'CONT_SIZES':[2]*256}
        for code,glyph in ((0xD0,';'),(0xBF,'😃'),(0xAE,'/')): self.tables['CHAR_MAP'][code] = glyph

    def test_every_occurrence_is_reported_past_the_first_error(self):
        rows = missing_glyphs(bytes((0xD0,0xBF,0xD0,0xAE)),self.tables)
        self.assertEqual([r['offset'] for r in rows],[0,1,2,3])
        self.assertEqual([r['existing_separate_font_encoding'] for r in rows],['80d0',None,'80d0','80ae'])

    def test_commands_are_not_glyph_occurrences(self):
        self.tables['CHAR_MAP'][0x24] = ';'
        self.assertEqual(missing_glyphs(bytes.fromhex('7f247f747f75'),self.tables),[])
        self.assertEqual(missing_glyphs(bytes.fromhex('7f24d0'),self.tables)[0]['offset'],2)

    def test_changed_or_truncated_commands_reject(self):
        for data in (b'\x7f',b'\x7f\xd0'):
            with self.assertRaises(ValueError): missing_glyphs(data,self.tables)
        self.tables['CONT_SIZES'][0x24] = 3
        with self.assertRaises(ValueError): missing_glyphs(b'\x7f\x24',self.tables)


if __name__ == '__main__': unittest.main()
