"""Whole-record hooks require both grading support and exact native trampolines."""

import copy
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_grading import VROM as GRADE_VROM, install as install_grading
from mail_npc import ENTRIES, POST_CALL, install
from runtime_module import MODULE_RAM, MODULE_VROM, add_runtime_module
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/runtime-module/module.json').is_file()
                     and (ROOT/'build/mail-grading/overlay.json').is_file(),
                     'Local ROM and current resident/scoring builds required')
class MailNpcPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.base = {}
        cls.additions,cls.module = add_runtime_module(cls.rom,cls.base,ROOT/'build/runtime-module')
        install_grading(cls.rom,cls.base,cls.additions,cls.module,ROOT/'build/mail-grading')

    def test_only_two_guarded_entries_change_and_original_frames_are_preserved(self):
        replacements = dict(self.base)
        report = install(self.rom,replacements,self.additions,self.module)
        before,after = self.base[CODE_VROM],replacements[CODE_VROM]
        allowed = set(range(POST_CALL-CODE_RAM,POST_CALL-CODE_RAM+4))
        for start,_,_,words,wrapper,trampoline in ENTRIES:
            offset = start-CODE_RAM
            allowed.update(range(offset,offset+8))
            target = int(self.module['symbols'][wrapper],16)
            self.assertEqual(after[offset:offset+8],struct.pack('>2I',0x08000000|((target&0x0FFFFFFF)>>2),0))
            bridge = int(self.module['symbols'][trampoline],16)-MODULE_RAM
            self.assertEqual(self.additions[MODULE_VROM][bridge:bridge+8],struct.pack('>2I',*words))
        self.assertTrue(all(i in allowed or a == b for i,(a,b) in enumerate(zip(before,after))))
        self.assertEqual((len(report['hooks']),report['scoped_context_bytes']),(2,16))
        self.assertEqual(after[POST_CALL-CODE_RAM:POST_CALL-CODE_RAM+4],
                         struct.pack('>I',0x0C000000|((int(report['post_send']['target'],16)&0x0FFFFFFF)>>2)))

    def test_missing_grade_overlay_or_ordinary_hook_is_rejected_without_changes(self):
        for key in (MODULE_VROM,GRADE_VROM,CODE_VROM):
            replacements,additions = dict(self.base),dict(self.additions)
            if key == MODULE_VROM: additions.pop(key)
            elif key == GRADE_VROM: replacements.pop(key)
            else:
                data = bytearray(replacements[key])
                data[0x800A86C4-CODE_RAM:0x800A86CC-CODE_RAM] = b'\0'*8
                replacements[key] = bytes(data)
            before = dict(replacements)
            with self.assertRaises(ValueError): install(self.rom,replacements,additions,self.module)
            self.assertEqual(replacements,before)

    def test_source_entry_and_overlap_mutations_fail_atomically(self):
        for start,*_ in ENTRIES:
            replacements = dict(self.base)
            changed = bytearray(replacements[CODE_VROM]); changed[start-CODE_RAM+3] ^= 1
            replacements[CODE_VROM] = bytes(changed)
            before = dict(replacements)
            with self.assertRaisesRegex(ValueError,'Overlapping'):
                install(self.rom,replacements,self.additions,self.module)
            self.assertEqual(replacements,before)
            files = by_vrom(self.rom)
            changed = bytearray(files[CODE_VROM].extract(self.rom)); changed[start-CODE_RAM+3] ^= 1
            class Entry:
                def extract(self,ignored): return changed
            files[CODE_VROM] = Entry()
            replacements = dict(self.base)
            with patch('mail_npc.by_vrom',return_value=files),self.assertRaisesRegex(ValueError,'Unexpected native'):
                install(self.rom,replacements,self.additions,self.module)
            self.assertEqual(replacements,self.base)

    def test_bad_link_targets_and_changed_trampolines_fail_independently_of_module_hash(self):
        for *_,wrapper,trampoline in ENTRIES:
            for name in (wrapper,trampoline):
                for address in ('00000000','801948E0','8019C8E0','80195001'):
                    module = copy.deepcopy(self.module)
                    module['symbols'][name] = address
                    with self.assertRaisesRegex(ValueError,'outside'):
                        install(self.rom,dict(self.base),self.additions,module)
            module = copy.deepcopy(self.module)
            additions = dict(self.additions)
            data = bytearray(additions[MODULE_VROM])
            at = int(module['symbols'][trampoline],16)-MODULE_RAM
            for offset in (0,4,8,12):
                data[at+offset+3] ^= 1
                additions[MODULE_VROM] = bytes(data)
                module['module_sha256'] = sha256(data)
                with self.assertRaisesRegex(ValueError,'trampoline mismatch'):
                    install(self.rom,dict(self.base),additions,module)
                data[at+offset+3] ^= 1

    def test_post_office_clear_hook_requires_its_exact_result_shim(self):
        replacements = dict(self.base)
        data = bytearray(replacements[CODE_VROM]); data[POST_CALL-CODE_RAM+3] ^= 1
        replacements[CODE_VROM] = bytes(data)
        before = dict(replacements)
        with self.assertRaisesRegex(ValueError,'Overlapping post-office'):
            install(self.rom,replacements,self.additions,self.module)
        self.assertEqual(replacements,before)
        for offset in range(0,24,4):
            module,additions = copy.deepcopy(self.module),dict(self.additions)
            data = bytearray(additions[MODULE_VROM])
            at = int(module['symbols']['af_mail_post_send'],16)-MODULE_RAM
            data[at+offset+3] ^= 1
            additions[MODULE_VROM] = bytes(data)
            module['module_sha256'] = sha256(data)
            with self.assertRaisesRegex(ValueError,'result shim'):
                install(self.rom,dict(self.base),additions,module)


if __name__ == '__main__': unittest.main()
