"""NPC generation source contracts, native selection bounds, and field coverage."""

from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_RAM,CODE_VROM
from gc_names import rel_sections
from mail_catalog import parse,verify_registered
from npc_mail_generation import (FUNCTIONS,TABLES,GROUPS,BAD_BASES,REFERENCE_BASES,
    WORD_BASES,REFERENCE_COUNTS,CLASSIC,COMPOSITE,native_evidence,reference_evidence,
    composite_selection,classic_selection,field_coverage)
from test_retail import ROM_PATH

REL = ROOT/'build/gamecube/files/foresta.rel.szs.decoded'
SYMBOLS = ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt'
CATALOG = ROOT/'build/mail-catalog/catalog.bin'


class NpcMailSelectionTests(unittest.TestCase):
    def test_all_native_group_part_ranges_and_gift_halves(self):
        starts = set()
        for foreign in range(2):
            for looks in range(6):
                start = GROUPS[foreign][looks]
                starts.add(start)
                for gate in range(2):
                    for part in range(5):
                        results = set()
                        for value in range(16 if part == 2 else 32):
                            offsets = [0]*5;offsets[part] = value
                            result = composite_selection(foreign,looks,gate,offsets)
                            self.assertEqual(result,tuple(start+v+(gate*16 if i == 2 else 0)
                                                          for i,v in enumerate(offsets)))
                            results.add(result[part])
                        low = start+(gate*16 if part == 2 else 0)
                        self.assertEqual(results,set(range(low,low+(16 if part == 2 else 32))))
        self.assertEqual(starts,set(range(0,384,32)))

    def test_all_classic_replies_and_no_gap_spill(self):
        for foreign,base in enumerate(BAD_BASES):
            ids = {classic_selection(foreign,looks,offset) for looks in range(6) for offset in range(3)}
            self.assertEqual(ids,set(range(base,base+18)))
        self.assertNotIn(215,{classic_selection(f,l,o) for f in range(2) for l in range(6) for o in range(3)})

    def test_invalid_indices_offsets_and_gift_values_are_rejected(self):
        for foreign,looks in ((-1,0),(2,0),(0,-1),(0,6),(True,0),(0,True),(0,1.0)):
            with self.assertRaises(ValueError): composite_selection(foreign,looks,0,(0,)*5)
            with self.assertRaises(ValueError): classic_selection(foreign,looks,0)
        for gate in (-1,2,True,0.0):
            with self.assertRaises(ValueError): composite_selection(0,0,gate,(0,)*5)
        for offsets in (None,(),(0,)*4,(0,)*6,(-1,0,0,0,0),(32,0,0,0,0),
                        (0,0,16,0,0),(0,0,0,0,32),(True,0,0,0,0),(0.0,0,0,0,0)):
            with self.assertRaises(ValueError): composite_selection(0,0,0,offsets)
        for offset in (-1,3,True,0.0):
            with self.assertRaises(ValueError): classic_selection(0,0,offset)

    def test_field_coverage_distinguishes_unavailable_parts_and_uncaptured_fields(self):
        banks = {name:[b'']*(982 if name in CLASSIC else 384) for name in CLASSIC+COMPOSITE}
        # Local group 32 cannot supply visitor-only slot 14, and a genuinely
        # unavailable footer is different from a source with no substitutions.
        banks['maila'][32] = b'\x7f\x3a'
        banks['psz'][77] = None
        report = field_coverage(banks)
        self.assertEqual(report['summary'],{'composite_groups':24,'classic_selections':36,
                         'missing_field_parts':2,'unavailable_parts':[{'bank':'psz','id':77}]})
        holes = [row for row in report['composite_groups'] if row['missing_fields']]
        self.assertEqual({(row['foreign'],row['looks'],row['gift_gate']) for row in holes},{(0,0,0),(0,0,1)})
        self.assertEqual(holes[0]['missing_fields'],[{'bank':'maila','id':32,'fields':[14]}])
        for changed in ({},{**banks,'extra':[]},{**banks,'maila':[]}):
            with self.assertRaises(ValueError): field_coverage(changed)
        banks['maila'][32] = b'\x7f'
        with self.assertRaises(ValueError): field_coverage(banks)

    @unittest.skipUnless(CATALOG.is_file(),'Local registered mail catalog required')
    def test_current_catalog_covers_every_required_native_reply_field(self):
        data = CATALOG.read_bytes();verify_registered(data)
        report = field_coverage(parse(data)[1])
        self.assertEqual(report['summary'],{'composite_groups':24,'classic_selections':36,
                         'missing_field_parts':0,'unavailable_parts':[{'bank':'psz','id':77}]})
        self.assertTrue(all(row['provided_fields'] == list(range(16 if row['foreign'] else 14))
                            for row in report['composite_groups']+report['classic_selections']))


@unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
class NativeNpcMailGenerationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = ROM_PATH.read_bytes();cls.code = by_vrom(rom)[CODE_VROM].extract(rom)

    def test_original_functions_tables_and_failure_propagation_contract(self):
        report = native_evidence(self.code)
        self.assertEqual(len(report['functions']),7)
        self.assertEqual(len(report['tables']),6)
        self.assertEqual(report['received_status'],0)
        self.assertEqual(report['staging_mail_ram'],'80142F80')
        self.assertFalse(report['assembler_failure_propagated'])
        self.assertTrue(report['reply_pending_cleared_only_after_delivery_success'])

    def test_changed_function_boundaries_tables_and_truncation_are_rejected(self):
        for start,end,_ in FUNCTIONS.values():
            for address in (start,end-1):
                code = bytearray(self.code);code[address-CODE_RAM] ^= 1
                with self.assertRaises(ValueError): native_evidence(code)
        for address,values in TABLES.values():
            for offset in (0,len(values)*4-1):
                code = bytearray(self.code);code[address-CODE_RAM+offset] ^= 1
                with self.assertRaises(ValueError): native_evidence(code)
        with self.assertRaises(ValueError): native_evidence(self.code[:0x800A9360-CODE_RAM])


@unittest.skipUnless(REL.is_file() and SYMBOLS.is_file(),'Local English executable and symbols required')
class ReferenceNpcMailGenerationTests(unittest.TestCase):
    def test_reference_ranges_preserve_native_selection_but_need_word_id_mapping(self):
        report = reference_evidence(REL.read_bytes(),SYMBOLS.read_text())
        self.assertEqual(len(report['functions']),5)
        self.assertFalse(report['word_family_id_mapping_approved'])
        self.assertEqual([i+3 for i,(a,b) in enumerate(zip(WORD_BASES,REFERENCE_BASES)) if a != b],[6,7])
        self.assertEqual([i+3 for i,n in enumerate(REFERENCE_COUNTS) if n != 32],[6,7])

    def test_changed_reference_function_and_word_table_are_rejected(self):
        rel = REL.read_bytes();symbols = SYMBOLS.read_text()
        sections = rel_sections(rel)
        for at in (sections[1][0]+0x5D430,sections[5][0]+0xDDF4,sections[5][0]+0xDE20):
            edited = bytearray(rel);edited[at] ^= 1
            with self.assertRaises(ValueError): reference_evidence(edited,symbols)
        with self.assertRaises(ValueError): reference_evidence(rel,'')


if __name__ == '__main__': unittest.main()
