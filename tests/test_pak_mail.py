"""Controller Pak inventories preserve native bounds and complete records."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom
from pak_mail import (PAK_BYTES, PASSPORT_BYTES, LETTER_FILE_BYTES, PROBE_CODE,
                      CODE_GUARDS, evidence, passport_slots, letter_slots, fixture_records)
from test_retail import ROM_PATH
from pak_mail_smoke import exercise
from flash_mail import SAVE_RAM, SAVE_BYTES
from pak_mail import PAK_INFO


class PakMailTests(unittest.TestCase):
    def test_all_slots_and_page_labels_have_exact_distinct_native_bounds(self):
        passport,letters = passport_slots(),letter_slots()
        self.assertEqual(len(passport),17)
        self.assertEqual(sum(row['compact'] for row in passport),7)
        self.assertEqual(len(letters),160)
        self.assertEqual(letters[0]['offset'],2+8*10)
        self.assertEqual(letters[-1]['offset']+164,0x66D2)
        self.assertEqual(LETTER_FILE_BYTES-0x66D2,46)
        self.assertEqual(PASSPORT_BYTES+LETTER_FILE_BYTES,121*256)
        self.assertLess(PASSPORT_BYTES+LETTER_FILE_BYTES,PAK_BYTES)
        for slots,limit in ((passport,0x1100),(letters,LETTER_FILE_BYTES)):
            self.assertEqual(len({r['label'] for r in slots}),len(slots))
            self.assertTrue(all(r['offset']+r['bytes'] <= limit for r in slots))
            self.assertTrue(all(a['offset']+a['bytes'] <= b['offset'] for a,b in zip(slots,slots[1:])))
        for page in range(8):
            self.assertEqual(sum(row['label'].startswith(f'page:{page}:') for row in letters),20)

    def test_both_snapshot_kinds_preserve_every_non_text_byte_and_file_padding(self):
        cases = [{'wire':(bytes((value,))*122).hex()} for value in (17,33)]
        for size,slots in ((PASSPORT_BYTES,passport_slots()),(LETTER_FILE_BYTES,letter_slots())):
            original = bytes(i%256 for i in range(size))
            modified,records = fixture_records(original,slots,cases)
            self.assertEqual(len(modified),size)
            self.assertEqual(len(records),len(slots))
            changed = set()
            for index,(slot,record) in enumerate(zip(slots,records)):
                start = slot['offset']
                self.assertEqual(record['case'],index%2)
                self.assertEqual(record['label'],slot['label'])
                self.assertEqual(bytes.fromhex(record['data']),modified[start:start+slot['bytes']])
                if slot['compact']:
                    allowed = [0,4,*range(5,127)]
                    self.assertEqual(modified[start+5:start+127],bytes.fromhex(cases[index%2]['wire']))
                else:
                    allowed = range(38,164)
                    self.assertEqual(modified[start+42:start+164],bytes.fromhex(cases[index%2]['wire']))
                changed.update(start+i for i in allowed)
            self.assertTrue(all(before == after for i,(before,after) in enumerate(zip(original,modified))
                                if i not in changed))
        with self.assertRaises(ValueError): fixture_records(bytes(16),passport_slots(),cases)
        with self.assertRaises(ValueError): fixture_records(bytes(PASSPORT_BYTES),passport_slots(),[{'wire':'01'}]*2)

    def test_raw_reader_is_separate_original_test_code_with_only_native_read_calls(self):
        self.assertEqual(len(PROBE_CODE),144)
        words = [int.from_bytes(PROBE_CODE[i:i+4],'big') for i in range(0,len(PROBE_CODE),4)]
        calls = [0x80000000|((word&0x3FFFFFF)<<2) for word in words if word>>26 == 3]
        self.assertEqual(calls,[0x800D6A10,0x800391B0,0x800D6A44])
        self.assertIn(0x2E280400,words)  # Loop stops after 1,024 native block reads.

    def test_writer_refuses_nonempty_or_insufficient_paks_before_allocating_or_writing(self):
        import struct
        request = {'passport_slots':passport_slots(),'letter_slots':letter_slots(),'guards':{},
                   'cases':[{'wire':bytes(122).hex(),'output':bytes(1040).hex()}]*2}
        class Debug:
            def __init__(self,free,used): self.usage = struct.pack('>3I',free,16,used);self.calls = []
            def read_memory(self,address,size):
                if (address,size) == (SAVE_RAM,SAVE_BYTES): return bytes(size)
                if (address,size) == (PAK_INFO+0x2D4,12): return self.usage
                raise AssertionError('Unexpected memory read')
            def write_memory(self,*args): raise AssertionError('Refused Pak must not reach fixture RAM writes')
            def call(self,address,args,**kwargs):
                self.calls.append(int(address,16))
                allowed = {0x8007A070:PAK_INFO,0x800790C0:1,0x800D6A10:0x80144500,
                           0x80078F08:1,0x80078FE8:1,0x800D6A44:0}
                if int(address,16) not in allowed: raise AssertionError('Refused Pak must not reach allocation/I/O')
                return {'return_value':allowed[int(address,16)]}
        for free,used in ((31488,1),(512,0)):
            debug = Debug(free,used)
            with self.assertRaises(ValueError):
                exercise(debug,request,lambda row:None,export_directory=Path('unused-test-output'))
            self.assertEqual(debug.calls[-1],0x800D6A44)

    @unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
    def test_narrow_inline_search_retains_false_positive_candidates_and_its_limits(self):
        from audit_mail_storage import inline_candidates
        result = inline_candidates(ROM_PATH.read_bytes())
        self.assertEqual(len(result['candidates']),28)
        addresses = {r['address'] for r in result['candidates']}
        self.assertTrue({'800390A4','800392C4','800AB100','800CC01C','800CC3D8'} <= addresses)
        self.assertEqual(len(result['definition_sha256']),4)
        self.assertIn('not necessarily mail',result['limitation'])

    @unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
    def test_native_code_sizes_and_storage_overlay_are_guarded(self):
        rom = ROM_PATH.read_bytes()
        evidence(rom)
        entries = by_vrom(rom)
        class Entry:
            def __init__(self,data): self.data = data
            def extract(self,ignored): return self.data
        targets = [(vrom,address-base) for vrom,base,start,end,_ in CODE_GUARDS for address in (start,end-4)]
        targets += [(0x675720,0x80116808-0x80051A80),(0x675720,0x8011680C-0x80051A80),
                    (0x79E430,0),(0x79E430,len(entries[0x79E430].extract(rom))-4)]
        for vrom,offset in targets:
            changed = bytearray(entries[vrom].extract(rom));changed[offset] ^= 1
            with patch('pak_mail.by_vrom',return_value={**entries,vrom:Entry(changed)}):
                with self.assertRaises(ValueError): evidence(rom)


if __name__ == '__main__': unittest.main()
