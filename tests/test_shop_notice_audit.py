"""Source-bound complete shop notices do not imply installed translation."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_shop_notice_letters import audit,TEMPLATES


@unittest.skipUnless((ROOT/'build/mail-glyph-catalog/catalog.bin').is_file(),'Local reference inputs required')
class ShopNoticeAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()

    def test_all_nine_templates_complete_parts_and_native_selector_difference(self):
        for path in ('build/mail-catalog/catalog.bin','build/mail-glyph-catalog/catalog.bin'):
            report = audit(self.native,(ROOT/path).read_bytes())
            self.assertEqual(report,json.loads(json.dumps(report)))
            self.assertFalse(report['installed']);self.assertEqual(report['templates'],list(TEMPLATES))
            self.assertEqual(len(report['parts']),27)
            for part in report['parts']:
                name,number = part['id'].split(':')
                self.assertEqual(part['fields'],[7] if name=='mail' and 0x14<=int(number,16)<=0x17 else [])
            self.assertEqual(report['native_rare_table'],[18,18,19,19,21,20,23,22])
            self.assertEqual(report['native_reopening_table'],[29,27,28,29])
            self.assertEqual(report['reference_reopening_table'],[27,27,28,29])

    def test_changed_native_and_registered_catalogue_reject(self):
        catalog = (ROOT/'build/mail-glyph-catalog/catalog.bin').read_bytes()
        with self.assertRaises(ValueError): audit(self.native[:-1],catalog)
        changed = bytearray(catalog);changed[-1] ^= 1
        with self.assertRaises(ValueError): audit(self.native,bytes(changed))


if __name__=='__main__': unittest.main()
