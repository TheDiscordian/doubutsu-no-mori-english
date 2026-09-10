"""Reserve translations stay source-bound and do not grant general capacity."""
import copy
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, apply_ups
from build import apply_translations
import reserve_strings as r
from textbanks import banks
from textcodec import command_info
from textvalidate import validate_entry

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD, PRIOR = (ROOT/'build'/n for n in ('reserve-strings-pilot','borrowed-catchphrases-pilot'))


@unittest.skipUnless(ROM.is_file(),'Local retail source required')
class ReserveCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.files = by_vrom(cls.native)
        cls.code = cls.files[CODE_VROM].extract(cls.native)
        cls.info = command_info(cls.code)
        cls.bank = next(b for b in banks(cls.native) if b.name == 'string')
        cls.edits = r.with_candidates(cls.native,[])

    def test_all_sources_and_exact_label_permissions(self):
        self.assertEqual(len(self.edits),77)
        self.assertEqual(len(set(r.IDS)),77)
        approvals = r.permits(self.native,self.edits)
        originals = self.bank.entries()
        for row in self.edits:
            value = row['translation'].encode()
            original = originals[int(row['id'][7:],16)]
            self.assertEqual(original,r.SOURCE)
            self.assertEqual(value,b'spare')
            validate_entry(original,value,self.info,'string',reserve_permit=approvals[row['id']])
            with self.assertRaisesRegex(ValueError,'entry budget'):
                validate_entry(original,value,self.info,'string')
        self.assertEqual(r.with_candidates(self.native,self.edits),self.edits)

    def test_changed_partial_duplicate_and_conflicting_candidates_reject(self):
        for edits in (self.edits[:-1],self.edits+[self.edits[0]]):
            with self.assertRaises(ValueError):r.permits(self.native,edits)
        for field,value in (('source_sha256','0'*64),('translation','book'),('control_policy','presentation')):
            edits=copy.deepcopy(self.edits);edits[0][field]=value
            with self.assertRaises(ValueError):r.with_candidates(self.native,edits)
        for bank,policy,source,value in (('message','exact',r.SOURCE,r.VALUE),
                ('string','presentation',r.SOURCE,r.VALUE),('string','exact',b'ab',r.VALUE),
                ('string','exact',r.SOURCE,b'book'),('string','exact',r.SOURCE,b'')):
            with self.assertRaisesRegex(ValueError,'Reserve capacity'):
                validate_entry(source,value,self.info,bank,policy,reserve_permit=r.ReservePermit())
        with self.assertRaisesRegex(ValueError,'Reserve capacity'):
            validate_entry(r.SOURCE,r.VALUE,self.info,'string',reserve_permit=r.ReservePermit(),
                           fortune_permit=object())

    def test_standalone_builder_changes_only_exact_bank_rows_and_relocation(self):
        replacements={CODE_VROM:self.code}
        count,relocations=apply_translations(self.native,replacements,None,english_reserve_strings=True)
        self.assertEqual(count,77)
        self.assertEqual(relocations,{self.bank.data_vrom:0x02600000})
        current=replace(self.bank,data=replacements[self.bank.data_vrom],table=replacements[self.bank.table_vrom])
        for n,(before,after) in enumerate(zip(self.bank.entries(),current.entries())):
            self.assertEqual(after,r.VALUE if n in r.NUMBERS else before)
        self.assertEqual(len(current.entries()),1562)
        r.planned(self.native,replacements)
        bad=dict(replacements);code=bytearray(bad[CODE_VROM]);code[r.START-CODE_RAM]^=1;bad[CODE_VROM]=bytes(code)
        with self.assertRaisesRegex(ValueError,'bounded string loader'):r.planned(self.native,bad)
        with self.assertRaisesRegex(ValueError,'relocated string bank'):r.planned(self.native,{})
        unchanged={CODE_VROM:self.code}
        self.assertEqual(apply_translations(self.native,unchanged,None),(0,{}))
        self.assertEqual(unchanged,{CODE_VROM:self.code})


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete reserve-label build required')
class ReserveCartridgeTests(unittest.TestCase):
    def test_complete_cartridge_retains_all_prior_resources_and_patch(self):
        native=ROM.read_bytes();built=(BUILD/'animal-forest-halfwidth.z64').read_bytes()
        old=(PRIOR/'animal-forest-halfwidth.z64').read_bytes()
        report=json.loads((BUILD/'build.json').read_text())
        evidence=r.verify_installation(built,native,report)
        self.assertEqual(len(evidence['ids']),77)
        self.assertEqual(apply_ups(native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),built)
        files,previous=by_vrom(built),by_vrom(old)
        self.assertEqual(set(files),set(previous))
        for vrom in files:
            if vrom not in (0x19D40,0x02600000,0x00D18000):
                self.assertEqual(files[vrom].extract(built),previous[vrom].extract(old),hex(vrom))
        from translation_progress import measure
        ledger=measure(native,built,report)
        self.assertEqual(ledger.summary()['total_source_characters'],751284)
        self.assertEqual(ledger.summary()['replaced_source_characters'],748328+154)
        for id in r.IDS:self.assertTrue(ledger.rows[id]['replacements'])
        bad=copy.deepcopy(report);bad['reserve_strings']['stored_bytes']=4
        with self.assertRaises(ValueError):r.verify_installation(built,native,bad)


if __name__=='__main__':unittest.main()
