"""Native mail menu policy, immutable labels, and guarded relocation tests."""

from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mail_menu import (RAM,SIZE,BSS,SECTIONS,DEFINITIONS,READ,REWRITE,
                       source,definitions,select_type,cases,relocated)
from runtime_layout import MODULE_RAM,RESERVATION
from test_retail import ROM_PATH


class MailMenuPolicyTests(unittest.TestCase):
    def test_received_draft_unused_and_gift_decisions(self):
        for font in range(256):
            for gift in (0,0x2001):
                for field in (0,1):
                    with self.subTest(font=font,gift=gift,field=field):
                        if font == 255:
                            expected = 0
                        elif gift:
                            expected = 24 if font == 1 else 21
                        elif font == 1:
                            expected = 23 if field else 22
                        else:
                            expected = 20 if field or font in (0,3) else 19
                        self.assertEqual(select_type(font,gift,1,0,field),expected)
                        for menu in (11,17):
                            expected_storage = 0 if font == 255 else 20 if font in (0,3) else 19
                            self.assertEqual(select_type(font,gift,menu,0,field),expected_storage)
                        self.assertEqual(select_type(font,gift,1,7,field),30 if font == 1 else 0)

    def test_every_native_fixture_has_an_ordinary_and_marker_twin(self):
        rows = cases()
        self.assertEqual(len(rows),120)
        groups = {}
        for case in rows:
            key = tuple(case[field] for field in ('font','present','menu','mode','field'))
            groups.setdefault(key,[]).append(case)
        self.assertEqual(len(groups),60)
        for pair in groups.values():
            self.assertEqual({case['split'] for case in pair},{0,128})
            self.assertEqual(len({case['expected'] for case in pair}),1)
        received = [row for row in rows if row['font'] in (0,2,3,4) and row['mode'] == 0]
        self.assertTrue(received)
        self.assertTrue(all(row['expected'] in (19,20,21) for row in received))

    def test_invalid_case_inputs_are_rejected(self):
        for args in ((-1,0,1,0,0),(256,0,1,0,0),(0,0,2,0,0),
                     (0,0,1,1,0),(0,0,1,0,2)):
            with self.assertRaises(ValueError): select_type(*args)


@unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
class NativeMailMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data,cls.reloc = source(ROM_PATH.read_bytes())

    def test_static_definitions_and_mail_callbacks(self):
        rows = definitions(self.data)
        self.assertEqual(len(rows),44)
        self.assertEqual([row['type'] for row in rows],list(range(44)))
        for row in rows:
            self.assertEqual(row['count'],len(row['options']))
            self.assertLessEqual(row['max_length'],8)
        for index in (19,20,21): self.assertEqual(rows[index]['options'][0]['callback'],READ)
        for index in (22,23,24): self.assertEqual(rows[index]['options'][0]['callback'],REWRITE)

    def test_relocated_static_pointer_graph_and_unchanged_other_bytes(self):
        rows = definitions(self.data)
        starts = (0,0,SECTIONS[0],sum(SECTIONS[:2]))
        changed = set()
        for (entry,) in struct.iter_unpack('>I',self.reloc[20:20+SECTIONS[4]*4]):
            at = starts[entry>>30]+(entry&0xFFFFFF)
            changed.update(range(at,at+4))
        self.assertTrue(changed)
        for base in (MODULE_RAM+RESERVATION,0x801F8010,0x80300000):
            output = relocated(self.data,self.reloc,base)
            self.assertEqual(len(output),SIZE+BSS)
            self.assertEqual(output[SIZE:],bytes(BSS))
            self.assertEqual(bytes(v for i,v in enumerate(self.data) if i not in changed),
                             bytes(v for i,v in enumerate(output[:SIZE]) if i not in changed))
            for row in rows:
                pointer,count = struct.unpack_from('>2I',output,DEFINITIONS-RAM+row['type']*8)
                self.assertEqual(count,row['count'])
                if not count: continue
                self.assertEqual(pointer,base+row['pointer']-RAM)
                for i,option in enumerate(row['options']):
                    word = struct.unpack_from('>I',output,pointer-base+i*4)[0]
                    self.assertEqual(word,base+option['pointer']-RAM)
                    self.assertEqual(output[word-base:word-base+8],
                                     self.data[option['pointer']-RAM:option['pointer']-RAM+8])
                    callback = struct.unpack_from('>I',output,word-base+8)[0]
                    self.assertEqual(callback,base+option['callback']-RAM if option['callback'] else 0)

    def test_changed_overlay_or_relocation_is_rejected(self):
        for index in (0,SIZE-1,DEFINITIONS-RAM,READ-RAM):
            edited = bytearray(self.data);edited[index] ^= 1
            with self.assertRaises(ValueError): definitions(bytes(edited))
            with self.assertRaises(ValueError): relocated(bytes(edited),self.reloc,0x80200000)
        for index in (0,19,20,len(self.reloc)-1):
            edited = bytearray(self.reloc);edited[index] ^= 1
            with self.assertRaises(ValueError): relocated(self.data,bytes(edited),0x80200000)
        for data,reloc in ((b'',self.reloc),(self.data,b''),(self.data,self.reloc[:4])):
            with self.assertRaises(ValueError): relocated(data,reloc,0x80200000)

    def test_out_of_bounds_or_unaligned_test_destinations_are_rejected(self):
        for base in (0,True,MODULE_RAM,MODULE_RAM+RESERVATION-16,0x801A0001,
                     0x80400000-SIZE-BSS+16):
            with self.assertRaises(ValueError): relocated(self.data,self.reloc,base)


if __name__ == '__main__': unittest.main()
