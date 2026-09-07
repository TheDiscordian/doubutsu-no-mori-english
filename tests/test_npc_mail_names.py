"""Exact saved-name aliases preserve full names and reject guessed identities."""

from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from npc_mail_names import NPC_COUNT,aliases,pack_aliases,unpack_aliases,lookup,prepare
from test_retail import ROM_PATH

DISPLAY = ROOT/'build/display-names'


class NpcMailNameAliasTests(unittest.TestCase):
    def setUp(self):
        self.originals = tuple(f'J{i:05d}'.encode() for i in range(NPC_COUNT))
        self.names = tuple((f'N{i:05d}' if i%2 == 0 else f'Long{i:04d}').encode().ljust(8,b' ')
                           for i in range(NPC_COUNT))
        self.rows = aliases(self.originals,self.names)

    def test_complete_original_and_short_english_name_lookup_round_trips(self):
        self.assertEqual(len(self.rows),324)
        data = pack_aliases(self.rows)
        self.assertEqual(unpack_aliases(data,sha256(data)),self.rows)
        for index,(key,name) in enumerate(zip(self.originals,self.names)):
            found,field = lookup(self.rows,key)
            self.assertEqual((found,field.text,field.article),(index,name,0))
            if index%2 == 0:
                self.assertEqual(lookup(self.rows,name[:6]),(found,field))

    def test_unknown_case_changed_and_long_prefixes_do_not_identify_a_villager(self):
        for key in (b'      ',b'OTHER ',b'j00000',b'Long00',b'\x00'*6,b'\x80'*6):
            self.assertIsNone(lookup(self.rows,key))
        for key in (b'',b'abc',b'1234567','J00000',None):
            with self.assertRaises(ValueError): lookup(self.rows,key)

    def test_duplicate_and_cross_language_collisions_are_rejected(self):
        originals = list(self.originals);originals[1] = originals[0]
        with self.assertRaisesRegex(ValueError,'Ambiguous'): aliases(originals,self.names)
        names = list(self.names);names[1] = self.originals[0].ljust(8,b' ')
        with self.assertRaisesRegex(ValueError,'Ambiguous'): aliases(self.originals,names)
        with self.assertRaises(ValueError): aliases(self.originals[:-1],self.names)
        for name in (b'',b' '*8,b'\x7f'*8,b'\x80'*8,b'\xcd'*8):
            names = list(self.names);names[0] = name
            with self.assertRaises(ValueError): aliases(self.originals,names)

    def test_serialization_requires_complete_consistent_ordered_identities(self):
        for changes in ({'key':b'bad'},{'key':b'\x7f'*6},{'name':b'bad'},
                        {'npc_index':216},{'npc_index':True}):
            rows = list(self.rows);rows[0] = replace(rows[0],**changes)
            with self.assertRaises(ValueError): pack_aliases(rows)
        rows = list(self.rows);rows[0],rows[1] = rows[1],rows[0]
        with self.assertRaises(ValueError): pack_aliases(rows)
        rows = [row for row in self.rows if row.npc_index != 0]
        with self.assertRaisesRegex(ValueError,'every identity'): pack_aliases(rows)
        rows = list(self.rows)
        at = next(i for i,row in enumerate(rows) if row.key == b'N00000')
        rows[at] = replace(rows[at],name=b'Wrong   ')
        with self.assertRaisesRegex(ValueError,'disagree'): pack_aliases(rows)
        data = pack_aliases(self.rows)
        for at in (0,31,32,63,64,len(data)-1):
            changed = bytearray(data);changed[at] ^= 1
            with self.assertRaises(ValueError): unpack_aliases(changed,sha256(data))
        for data in (b'',data[:-1],data+b'\0'):
            with self.assertRaises(ValueError): unpack_aliases(data,sha256(data))


@unittest.skipUnless(ROM_PATH.is_file() and (DISPLAY/'names.json').is_file(),
                     'Original ROM and verified complete display-name resource required')
class RetailNpcMailNameAliasTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.names = (DISPLAY/'names.bin').read_bytes()
        cls.report = json.loads((DISPLAY/'names.json').read_text())

    def test_all_villagers_both_source_forms_and_full_eight_byte_outputs(self):
        data,report = prepare(self.rom,self.names,self.report)
        self.assertEqual((report['aliases'],report['villagers'],report['bytes']),(394,216,6368))
        self.assertEqual(report['data_sha256'],'a79b6bc3c5b36c7ce2bcea55932ccdf4ce694608e5dcfb896226a24d368bf5d6')
        rows = unpack_aliases(data,report['data_sha256'])
        native = by_vrom(self.rom)[0xE04000].extract(self.rom)
        for index in range(216):
            expected = self.names[32+index*8:40+index*8]
            found,field = lookup(rows,native[8+index*6:14+index*6])
            self.assertEqual((found,field.text),(index,expected))
            if len(expected.rstrip(b' ')) <= 6:
                self.assertEqual(lookup(rows,expected[:6]),(found,field))

    def test_modified_name_source_and_recomputed_report_hash_are_rejected(self):
        changed = bytearray(self.names);changed[32] ^= 1
        report = deepcopy(self.report);report['data_sha256'] = sha256(changed)
        with self.assertRaises(ValueError): prepare(self.rom,bytes(changed),report)
        for key in ('source_sha256','data_sha256'):
            report = deepcopy(self.report);report[key] = '0'*64
            with self.assertRaises(ValueError): prepare(self.rom,self.names,report)
        report = deepcopy(self.report);report['edits'][0]['source_sha256'] = '0'*64
        with self.assertRaises(ValueError): prepare(self.rom,self.names,report)


if __name__ == '__main__': unittest.main()
