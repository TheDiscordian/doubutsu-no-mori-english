"""Source approval for complete Snowman wording and the twelve full gift names."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_snowman_letters import audit,GIFTS,GC_GIFTS
from extended_items import COUNTS


@unittest.skipUnless((ROOT/'build/mail-glyph-catalog/catalog.bin').is_file(),'Local reference inputs required')
class SnowmanAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.catalog = (ROOT/'build/mail-glyph-catalog/catalog.bin').read_bytes()
        cls.items = (ROOT/'build/interior-items-resource/names.bin').read_bytes()

    def test_complete_parts_and_exact_order_are_not_installation_credit(self):
        result = audit(self.rom,self.catalog,self.items)
        self.assertFalse(result['installed']);self.assertEqual(result['catalog'],4)
        self.assertEqual(len(result['parts']),36)
        self.assertEqual({p['id'] for p in result['parts']},
                         {f'{name}:{number:04X}' for name in ('super','mail','ps') for number in range(0x202,0x20E)})
        for part in result['parts']:
            self.assertEqual(part['fields'],[0] if part['id'].startswith('mail:') else [])
        self.assertEqual([g['native_gift'] for g in result['gifts']],list(GIFTS))
        self.assertEqual([g['reference_gift'] for g in result['gifts']],list(GC_GIFTS))

    def test_every_selected_gift_name_must_match_the_supplied_english(self):
        for gift in GIFTS:
            at = 32+(sum(COUNTS[:-1])+(gift&4095))*16 if gift>>12==1 else 32+(sum(COUNTS[:(gift>>8)-0x20])+(gift&255))*16
            changed = bytearray(self.items);changed[at] ^= 1
            with self.subTest(gift=gift),self.assertRaisesRegex(ValueError,'complete matching English item name'):
                audit(self.rom,self.catalog,bytes(changed))

    def test_wrong_source_and_malformed_resources_reject(self):
        changed = bytearray(self.rom);changed[-1] ^= 1
        with self.assertRaises(ValueError): audit(bytes(changed),self.catalog,self.items)
        with self.assertRaises(ValueError): audit(self.rom,self.catalog,self.items[:-1])
        with self.assertRaises(ValueError): audit(self.rom,self.catalog[:-1],self.items)


if __name__=='__main__': unittest.main()
