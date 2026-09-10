"""Complete reference accents retain native identities, aliases, and capacities."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import accent_items as a
from aflib import sha256


class AccentItemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
        cls.base=(ROOT/'build/design-items-resource/names.bin').read_bytes()
        cls.report=json.loads((ROOT/'build/design-items-resource/names.json').read_text())

    def test_all_eight_complete_names_and_only_owned_rows_change(self):
        data,report=a.build(self.native,self.rel,self.symbols,self.base,self.report)
        self.assertEqual(len(data),72736);self.assertEqual(report['accent_candidate_slots'],8)
        self.assertFalse(report['installed']);self.assertEqual(report['previous_candidate_slots'],4536)
        offsets={a.offset(row['id']) for row in report['accent_edits']}
        for at in range(32,len(data),16):
            if at not in offsets:self.assertEqual(data[at:at+16],self.base[at:at+16])
        for row in report['accent_edits']:
            root=row['accent_item_name'];at=a.offset(row['id']);value=data[at:at+16]
            self.assertEqual(value,a.encoded(a.ROWS[root][0]))
            self.assertEqual(sha256(value),row['provenance']['encoded_sha256'])
            self.assertEqual(value.count(b'\x80'),1)
        self.assertEqual(a.encoded('Pokémon Pikachu').rstrip(),b'Pok\x80\x7Cmon Pikachu')
        self.assertEqual(a.encoded('Señor K.K.').rstrip(),b'Se\x80\x87or K.K.')
        # The ordinary resource installer still rejects these unconnected rows.
        from extended_items import resource
        with self.assertRaises(ValueError):resource(self.native,self.report['edits']+report['accent_edits'])

    def test_changed_sources_capacity_and_prior_resource_fail_closed(self):
        for rel,symbols in ((self.rel[:-1],self.symbols),(self.rel,self.symbols+'\n')):
            with self.assertRaises(ValueError):a.candidates(self.native,rel,symbols)
        changed=copy.deepcopy(self.report);changed['data_sha256']='0'*64
        with self.assertRaises(ValueError):a.build(self.native,self.rel,self.symbols,self.base,changed)
        for text in ('A'*17,'Café ☀','Señor{cmd:00}','Pokémon\nPikachu'):
            with self.assertRaises(ValueError):a.encoded(text)
        for id in ('item_24:00FF','item_10:0ECC','item_30:0000'):
            with self.assertRaises(ValueError):a.offset(id)


if __name__=='__main__':unittest.main()
