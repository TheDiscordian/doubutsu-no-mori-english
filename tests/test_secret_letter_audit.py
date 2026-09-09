"""Source-approved complete secret letters remain separate from installation."""

import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_secret_letters import audit,snapshots,TEMPLATES
from mail_record import unpack


@unittest.skipUnless((ROOT/'build/mail-glyph-catalog/catalog.bin').is_file(),'Local complete reference inputs required')
class SecretLetterAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.catalog = (ROOT/'build/mail-glyph-catalog/catalog.bin').read_bytes()

    def test_all_fifteen_templates_and_thirty_fixed_snapshots(self):
        data,report = snapshots(self.native,self.catalog)
        self.assertEqual(report,json.loads(json.dumps(report)));self.assertFalse(report['installed'])
        self.assertEqual(report['templates'],list(TEMPLATES));self.assertEqual(len(report['parts']),45)
        self.assertTrue(all(not part['fields'] for part in report['parts']))
        self.assertEqual(len(data),600);self.assertEqual(len(report['cases']),30)
        for index,case in enumerate(report['cases']):
            row = data[index*20:(index+1)*20];number,capital,reserved = struct.unpack('>HBB',row[:4])
            self.assertEqual((number,capital,reserved),(case['template'],bytes.fromhex(case['text'])[14],0))
            wire = row[4:]+bytes(106);self.assertEqual(wire,bytes.fromhex(case['wire']))
            record = unpack(wire,expected_catalog=4)
            self.assertEqual(record.templates,(number,));self.assertEqual(record.fields,())
            self.assertEqual(record.initial_capital,bool(case['capital']))

    def test_changed_inputs_and_incomplete_plain_catalogue_rejected(self):
        with self.assertRaises(ValueError): audit(self.native,(ROOT/'build/mail-catalog/catalog.bin').read_bytes())
        with self.assertRaises(ValueError): snapshots(self.native[:-1],self.catalog)
        changed = bytearray(self.catalog);changed[-1] ^= 1
        with self.assertRaises(ValueError): snapshots(self.native,bytes(changed))
        with self.assertRaises(ValueError): snapshots(self.native,(ROOT/'build/mail-catalog/catalog.bin').read_bytes())


if __name__=='__main__': unittest.main()
