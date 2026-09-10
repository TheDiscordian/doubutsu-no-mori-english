"""Pelly failure handling preserves old records and rejects partial installation."""

import copy
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_grading import install as grading_install
from mail_npc import install as npc_install
from mail_storage import PELLY_VROM, PELLY_RAM
from mail_storage import TAG_VROM, TAG_RAM, TAG_SEND, pocket_send_evidence
from pelly_receipt import COUNT, DATA_VROM, TABLE_VROM, MESSAGES, LIMITS, RELOC_VROM, append_messages, install
from pelly_receipt_smoke import relocated_pelly
from runtime_module import MODULE_RAM, MODULE_VROM, add_runtime_module
from textbanks import Bank
from textcodec import tokenize
from runtime_module import module_command_info
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/notice-seasonal-runtime/module.json').is_file(),
                     'Local original ROM and current resident module required')
class PellyReceiptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.files = by_vrom(cls.rom)
        cls.base = {}
        cls.additions,cls.module = add_runtime_module(cls.rom,cls.base,ROOT/'build/notice-seasonal-runtime')
        grading_install(cls.rom,cls.base,cls.additions,cls.module,ROOT/'build/mail-grading')
        npc_install(cls.rom,cls.base,cls.additions,cls.module)

    def test_pocket_removal_uses_native_zero_status_and_retains_original_slot(self):
        evidence = pocket_send_evidence(self.rom)
        self.assertEqual(evidence['staged_font'],0)
        self.assertEqual(evidence['selected_slot_store'],'8087265C')
        data = bytearray(self.files[TAG_VROM].extract(self.rom))
        class Entry:
            def extract(self,rom): return data
        for offset in range(TAG_SEND[0]-TAG_RAM,TAG_SEND[1]-TAG_RAM,4):
            data[offset+3]^=1
            with patch('mail_storage.by_vrom',return_value={TAG_VROM:Entry()}):
                with self.assertRaisesRegex(ValueError,'pocket-send'): pocket_send_evidence(self.rom)
            data[offset+3]^=1

    def test_original_relocations_preserve_external_hooks_at_two_heap_addresses(self):
        result = dict(self.base)
        install(self.rom,result,self.additions,self.module)
        overlay,reloc = result[PELLY_VROM],self.files[RELOC_VROM].extract(self.rom)
        for base in (0x801A0000,0x802F8010):
            loaded = relocated_pelly(overlay,reloc,base)
            self.assertEqual(len(loaded),len(overlay))
            self.assertNotEqual(loaded,overlay)
            for start,end in ((0x809C3F30,0x809C3F54),(0x809C47C8,0x809C47D0),
                              (0x809C481C,0x809C4820),(0x809C4A98,0x809C4AA0)):
                self.assertEqual(loaded[start-PELLY_RAM:end-PELLY_RAM],overlay[start-PELLY_RAM:end-PELLY_RAM])
            # The original common message-change call relocates into loaded text.
            at = 0x809C3F54-PELLY_RAM
            target = base+0x809C35C0-PELLY_RAM
            self.assertEqual(struct.unpack_from('>I',loaded,at)[0],0x0C000000|((target&0xFFFFFFF)>>2))
        for base in (0,0x801948E0,0x801A0001,0x803FE210):
            with self.assertRaisesRegex(ValueError,'relocation input'): relocated_pelly(overlay,reloc,base)
        changed = bytearray(reloc);changed[20]^=1
        with self.assertRaisesRegex(ValueError,'relocation input'): relocated_pelly(overlay,changed,0x801A0000)

    def test_handback_initializer_and_complete_direct_reason_accesses_are_guarded(self):
        original = self.files[PELLY_VROM].extract(self.rom)
        data = bytearray(original)
        files = dict(self.files)
        class Entry:
            def extract(self,rom): return data
        files[PELLY_VROM] = Entry()
        for address in (0x809C4A74,0x809C4A98,0x809C4AA8,0x809C4AD0):
            data[address-PELLY_RAM+3]^=1
            with patch('pelly_receipt.by_vrom',return_value=files):
                with self.assertRaisesRegex(ValueError,'hand-back|reason readers'):
                    install(self.rom,dict(self.base),self.additions,self.module)
            data[:] = original
        # A newly introduced direct reader outside the patched functions cannot
        # silently inherit the new reason value without review.
        struct.pack_into('>I',data,0x1B00,0x90820949)
        with patch('pelly_receipt.by_vrom',return_value=files):
            with self.assertRaisesRegex(ValueError,'reason readers'):
                install(self.rom,dict(self.base),self.additions,self.module)

    def test_append_two_errors_without_changing_any_native_message(self):
        original,table = self.files[DATA_VROM].extract(self.rom),self.files[TABLE_VROM].extract(self.rom)
        data,changed = append_messages(original,table)
        old = Bank('message',DATA_VROM,TABLE_VROM,original,table).entries()
        entries = Bank('message',DATA_VROM,TABLE_VROM,data,changed).entries()
        self.assertEqual(entries,old+list(MESSAGES))
        self.assertEqual(len(changed),len(table))
        for message in MESSAGES:
            commands = [t.data for t in tokenize(message,module_command_info(self.rom)) if t.kind == 'cmd']
            self.assertEqual(commands,[bytes.fromhex('7F09090001'),bytes.fromhex('7F01')])
            self.assertLess(len(message),1024)
        for invalid in (table[:COUNT*4],table[:COUNT*4]+b'\1'+table[COUNT*4+1:]):
            with self.assertRaises(ValueError): append_messages(original,invalid)
        with self.assertRaisesRegex(ValueError,'tail'): append_messages(original+b'x',table)
        with self.assertRaises(ValueError): append_messages(data,changed)

    def test_only_guarded_instructions_and_appendix_are_changed(self):
        result = dict(self.base)
        report = install(self.rom,result,self.additions,self.module)
        self.assertEqual(report['appended_message_ids'],['2DE8','2DE9'])
        self.assertNotIn(RELOC_VROM,result)
        allowed = set()
        for address in LIMITS: allowed.update(range(address-CODE_RAM,address-CODE_RAM+4))
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(self.base[CODE_VROM],result[CODE_VROM]))))
        allowed = set(range(0x809C3F30-PELLY_RAM,0x809C3F54-PELLY_RAM))
        allowed.update(range(0x809C47C8-PELLY_RAM,0x809C47D0-PELLY_RAM))
        allowed.update(range(0x809C481C-PELLY_RAM,0x809C4820-PELLY_RAM))
        allowed.update(range(0x809C4A98-PELLY_RAM,0x809C4AA0-PELLY_RAM))
        original = self.files[PELLY_VROM].extract(self.rom)
        self.assertEqual(len(original),len(result[PELLY_VROM]))
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(original,result[PELLY_VROM]))))

    def test_missing_lower_guard_overlap_and_wrong_counts_fail_atomically(self):
        for variant in ('guard','overlay','reloc','pocket','limit','count'):
            result = dict(self.base)
            if variant=='guard': result[CODE_VROM]=self.files[CODE_VROM].extract(self.rom)
            if variant=='overlay': result[PELLY_VROM]=b'overlap'
            if variant=='reloc': result[RELOC_VROM]=b'overlap'
            if variant=='pocket': result[TAG_VROM]=b'overlap'
            if variant=='limit':
                code=bytearray(result[CODE_VROM]);code[min(LIMITS)-CODE_RAM+3]^=1;result[CODE_VROM]=bytes(code)
            if variant=='count':
                data=bytearray(self.files[TABLE_VROM].extract(self.rom));data[COUNT*4+3]=1;result[TABLE_VROM]=bytes(data)
            before = dict(result)
            with self.assertRaises(ValueError): install(self.rom,result,self.additions,self.module)
            self.assertEqual(result,before)

    def test_every_shim_word_and_data_target_is_bound_to_the_module(self):
        for name,size in (('af_pelly_receipt_result',32),('af_pelly_refusal_index',24),
                          ('af_pelly_handback_index',24),('af_pelly_refusal_messages',12)):
            for offset in range(0,size,4):
                module,additions = copy.deepcopy(self.module),dict(self.additions)
                data = bytearray(additions[MODULE_VROM])
                data[int(module['symbols'][name],16)-MODULE_RAM+offset+3]^=1
                additions[MODULE_VROM]=bytes(data);module['module_sha256']=sha256(data)
                with self.assertRaisesRegex(ValueError,'resident hook'): install(self.rom,dict(self.base),additions,module)
            for address in ('00000000','801948E0','8019C8E0','80195001'):
                module = copy.deepcopy(self.module);module['symbols'][name]=address
                with self.assertRaisesRegex(ValueError,'resident hook'): install(self.rom,dict(self.base),self.additions,module)


if __name__ == '__main__': unittest.main()
