"""FlashRAM checks never confuse a raw checksum with complete save compatibility."""

from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from flash_mail import SAVE_RAM, SAVE_BYTES, BANK_BYTES, FLASH_BYTES, CODE_GUARDS, locations, checksum, validate_flash, evidence
from aflib import CODE_RAM, CODE_VROM, by_vrom
from test_retail import ROM_PATH


class FlashMailTests(unittest.TestCase):
    def test_all_native_mail_slots_are_distinct_and_inside_the_checksummed_payload(self):
        slots = locations()
        self.assertEqual(len(slots),192)
        for prefix,count in (('player',40),('home',40),('post_queue',5),('leaflet',2),('npc',105)):
            self.assertEqual(sum(row['label'].startswith(prefix+':') for row in slots),count)
        self.assertEqual(next(r['offset']+SAVE_RAM for r in slots if r['label']=='npc:0:0'),0x80130DF2)
        self.assertTrue(all(r['offset']+r['bytes'] <= SAVE_BYTES for r in slots))

    def test_both_full_payloads_require_identity_and_checksum_but_padding_is_not_interpreted(self):
        bank = bytearray(BANK_BYTES)
        bank[4:8] = b'NAFJ'
        bank[8:10] = bank[0x2F68:0x2F6A] = bytes.fromhex('302A')
        for slot in locations(): bank[slot['offset']+(4 if slot['compact'] else 39)] = 128
        bank[18:20] = ((-checksum(bank[:SAVE_BYTES]))&0xFFFF).to_bytes(2,'big')
        image = bytes(bank)*2
        self.assertEqual(validate_flash(image)['copies'],2)
        for offset in (4,8,18,0x2F68,SAVE_BYTES-1,BANK_BYTES+SAVE_BYTES-1):
            edited = bytearray(image);edited[offset] ^= 1
            with self.assertRaises(ValueError): validate_flash(bytes(edited))
        edited = bytearray(image);edited[SAVE_BYTES] = 99
        self.assertEqual(validate_flash(bytes(edited))['payload_sha256'],validate_flash(image)['payload_sha256'])
        for size in (0,SAVE_BYTES,FLASH_BYTES-1,FLASH_BYTES+1):
            with self.assertRaises(ValueError): validate_flash(bytes(size))
        with self.assertRaises(ValueError): checksum(b'x')

    @unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
    def test_native_flash_functions_and_dispatch_table_are_source_guarded(self):
        rom = ROM_PATH.read_bytes()
        evidence(rom)
        code = bytearray(by_vrom(rom)[CODE_VROM].extract(rom))
        class Entry:
            def extract(self,ignored): return code
        addresses = [p for start,end,_ in CODE_GUARDS for p in (start,end-4)]+[0x80106ACC,0x80106AE4]
        for address in addresses:
            code[address-CODE_RAM+3] ^= 1
            with patch('flash_mail.by_vrom',return_value={CODE_VROM:Entry()}):
                with self.assertRaises(ValueError): evidence(rom)
            code[address-CODE_RAM+3] ^= 1


if __name__ == '__main__': unittest.main()
