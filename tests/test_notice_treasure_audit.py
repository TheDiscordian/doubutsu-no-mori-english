"""Treasure source matching must preserve native clues and complete fields."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from audit_notice_treasure import audit, IDS
from notice_record import unpack


@unittest.skipUnless((ROOT/'build/mail-glyph-resources/glyph-catalog.bin').is_file(),
                     'Supplied local reference resources required')
class NoticeTreasureAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.catalog = (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes()
        cls.result = audit(cls.native, cls.catalog)

    def test_all_sources_bound_and_hidden_item_clue_not_revealed(self):
        result = self.result
        self.assertEqual(result['templates'], list(IDS))
        self.assertEqual(len(result['parts']), 54)
        self.assertEqual(result['reference_approved'], [i for i in IDS if i != 0x1F4])
        change = result['native_adaptations'][0]
        self.assertEqual((change['template'], change['native_fields'], change['reference_fields']),
                         (0x1F4, [1, 3, 5], [1, 2, 3]))
        self.assertFalse(result['installed'])

    def test_all_34_full_field_snapshots_and_numeric_acres(self):
        self.assertEqual([(c['template'], c['capital']) for c in self.result['cases']],
                         [(i, capital) for i in IDS if i != 0x1F4 for capital in (0, 1)])
        for case in self.result['cases']:
            value = unpack(bytes.fromhex(case['wire']), expected_catalog=4)
            fields = dict(value.fields)
            for field, expected in ((1, b'ABCDEFGHIJKLMNOP'), (2, b'abcdefghijklmnop'),
                                    (3, b'5'), (4, b'4'), (5, b'TownXX')):
                if field in fields: self.assertEqual(fields[field].text, expected)
            body = bytes.fromhex(case['body'])
            self.assertEqual(case['body_bytes'], len(body))
            self.assertLessEqual(len(body), 1024)
            self.assertGreater(len(body), 96)

    def test_changed_inputs_rejected(self):
        changed = bytearray(self.native)
        changed[-1] ^= 1
        with self.assertRaises(ValueError): audit(bytes(changed), self.catalog)
        changed = bytearray(self.catalog)
        changed[-1] ^= 1
        with self.assertRaises(ValueError): audit(self.native, bytes(changed))


if __name__ == '__main__': unittest.main()
