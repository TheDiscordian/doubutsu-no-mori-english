"""Residual general translations retain full live consumers and every unrelated file."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups,sha256
from textbanks import banks
import residual_general as r

ROM=ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD=ROOT/'build/residual-general-pilot'


@unittest.skipUnless(ROM.is_file(),'Local retail source required')
class ResidualGeneralTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=ROM.read_bytes()

    def test_complete_reference_and_original_groups(self):
        original=r.originals(self.native);reference=r.reference(self.native)
        self.assertEqual(len(original),36)
        self.assertEqual(len(reference),104)
        self.assertFalse(set(original)&set(reference))
        self.assertEqual(len(r.IDS),140)
        self.assertEqual(reference[0],b'Test Line of text No.1')
        self.assertEqual(reference[0x49C],b'Sagittarius')
        self.assertEqual(reference[0x558],b"Nook's Cranny")
        self.assertEqual(reference[0x78],b'pweeen')
        self.assertEqual(original[3],b'yr')
        self.assertEqual(original[0xB],b'Tue')
        self.assertEqual(original[0x5D],b'meow')
        data=r.MANIFEST.read_bytes()
        for old,new in ((b'meow',b'TRANSLATE'),(b'string:005D',b'string:0010'),
                        (b'right?',b'{cmd:7F01}'),(b'"exact"',b'"presentation"')):
            with self.assertRaisesRegex(ValueError,'manifest'):
                r.originals(self.native,data.replace(old,new,1))

    @unittest.skipUnless((r.BASE/'build.json').is_file(),'Complete predecessor required')
    def test_all_rows_and_complete_installed_consumers(self):
        base,previous=r.baseline()
        updates,evidence=r.plan(self.native,base,previous)
        self.assertEqual(evidence['records'],140)
        self.assertEqual(evidence['changed_records'],127)
        self.assertEqual(evidence['runtime_changes'],0)
        self.assertEqual(evidence['saved_layout_changes'],0)
        bank=next(b for b in banks(self.native) if b.name=='string')
        files=by_vrom(base)
        old=replace(bank,data=files[r.DATA_VROM].extract(base),table=files[r.TABLE_VROM].extract(base)).entries()
        new=replace(bank,data=updates[r.DATA_VROM],table=updates[r.TABLE_VROM]).entries()
        values={**r.originals(self.native),**r.reference(self.native)}
        self.assertEqual(len(new),1562)
        for n,value in enumerate(new):
            self.assertEqual(value,values.get(n,old[n]))
        self.assertEqual(r.verify_empty_units(self.native,base,previous,new),r.EMPTY_IDS)
        self.assertEqual(len(r.EMPTY_IDS),30)
        changed=list(new);changed[0x593]=b' '
        with self.assertRaisesRegex(ValueError,'counter group'):
            r.verify_empty_units(self.native,base,previous,changed)

    @unittest.skipUnless((BUILD/'build.json').is_file(),'Installed residual-general build required')
    def test_complete_cartridge_patch_and_source_accounting(self):
        built=(BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report=json.loads((BUILD/'build.json').read_text())
        base,previous,empty=r.verify_installation(built,self.native,report)
        self.assertEqual(sha256(base),r.BASE_SHA)
        self.assertEqual(empty,r.EMPTY_IDS)
        self.assertEqual(apply_ups(self.native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),built)
        files,old=by_vrom(built),by_vrom(base)
        self.assertEqual(set(files),set(old))
        for v in files:
            self.assertEqual(files[v].index,old[v].index)
            if v not in (0x19D40,r.DATA_VROM,r.TABLE_VROM):
                self.assertEqual(files[v].extract(built),old[v].extract(base),hex(v))
        from translation_progress import measure
        ledger=measure(self.native,built,report)
        self.assertEqual(ledger.summary()['total_source_characters'],751284)
        self.assertEqual(ledger.summary()['replaced_source_characters'],750175)
        self.assertFalse([identity for identity,row in ledger.rows.items()
                          if identity.startswith('string:') and row['source_characters'] and not row['replacements']])
        for identity in empty:
            self.assertTrue(ledger.rows[identity]['replacements'][0]['intentional_omission'])
        bad=copy.deepcopy(report);bad['residual_general']['intentional_empty_ids']=[]
        with self.assertRaisesRegex(ValueError,'report'):
            r.verify_installation(built,self.native,bad)


if __name__=='__main__':unittest.main()
