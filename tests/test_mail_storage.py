"""Native storage evidence requires exact executable bytes and complete fields."""

from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom
from mail_storage import FUNCTIONS, QUEUE, QUEUE_COUNT, LEAFLETS, LEAFLET_FLAGS, evidence
from mail_storage import PELLY_VROM, PELLY_RAM, pelly_evidence
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
class MailStorageTests(unittest.TestCase):
    def test_exact_status_contract_and_storage_boundaries(self):
        result = evidence(ROM_PATH.read_bytes())
        self.assertEqual(result['unused_fonts'],[255])
        self.assertEqual(result['sendable_fonts'],[1])
        self.assertEqual(result['attachable_fonts'],[1,3,4])
        self.assertEqual(QUEUE+QUEUE_COUNT*164,LEAFLETS[0])
        self.assertEqual(LEAFLETS[0]+164,LEAFLETS[1])
        self.assertEqual(LEAFLETS[1]+164,LEAFLET_FLAGS)
        self.assertEqual(result['home_mailboxes']['slots'],10)
        self.assertEqual(result['home_mailboxes']['homes'],4)

    def test_each_selected_function_rejects_changes(self):
        rom = ROM_PATH.read_bytes()
        code = bytearray(by_vrom(rom)[CODE_VROM].extract(rom))
        class Entry:
            def extract(self,ignored): return code
        for name,(start,end,_) in FUNCTIONS.items():
            for offset in (start-CODE_RAM,end-CODE_RAM-4):
                code[offset+3] ^= 1
                with patch('mail_storage.by_vrom',return_value={CODE_VROM:Entry()}):
                    with self.assertRaisesRegex(ValueError,name): evidence(rom)
                code[offset+3] ^= 1

    def test_pelly_original_failure_path_is_bound_to_the_native_instructions(self):
        rom = ROM_PATH.read_bytes()
        self.assertIn('ignores receipt failure',pelly_evidence(rom)['status'])
        code = bytearray(by_vrom(rom)[PELLY_VROM].extract(rom))
        class Entry:
            def extract(self,ignored): return code
        for address in (0x809C47C0,0x809C47D4,0x809C480C,0x809C4828):
            code[address-PELLY_RAM+3] ^= 1
            with patch('mail_storage.by_vrom',return_value={PELLY_VROM:Entry()}):
                with self.assertRaisesRegex(ValueError,'Pelly'): pelly_evidence(rom)
            code[address-PELLY_RAM+3] ^= 1


if __name__ == '__main__': unittest.main()
