"""Reject malformed relocations, stale artifacts, and overlapping mail hooks."""

import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_grading import RAM, SIZE, RELOC_SIZE, VROM, RELOC_VROM, install, load_prefixes, relocate
from test_retail import ROM_PATH


def relocation(records, text=0x300, rodata=16, bss=0):
    return (struct.pack('>5I',text,0,rodata,bss,len(records))
            +struct.pack('>'+str(len(records))+'I',*records)).ljust(RELOC_SIZE-4,b'\0')+struct.pack('>I',RELOC_SIZE)


class MailRelocationTests(unittest.TestCase):
    def setUp(self):
        self.data = bytearray(SIZE)
        for offset in (0,8,0x24C):
            struct.pack_into('>I',self.data,offset,0x08000000|(((RAM+0x280)&0x0FFFFFFF)>>2))
        address = RAM+0x308
        struct.pack_into('>2I',self.data,0x260,
                         0x3C020000|((address+0x8000)>>16),0x24420000|(address&0xFFFF))
        self.records = [0x44000000,0x44000008,0x4400024C,0x45000260,0x46000264]

    def test_jumps_and_paired_addresses_relocate_at_multiple_heap_bases(self):
        for base in (0x80000000,0x801A0000,0x802F8010,0x803FE000):
            result = relocate(self.data,relocation(self.records),base)
            for offset in (0,8,0x24C):
                jump = struct.unpack_from('>I',result,offset)[0]
                self.assertEqual(0x80000000|((jump&0x3FFFFFF)<<2),base+0x280)
            high,low = struct.unpack_from('>2I',result,0x260)
            self.assertEqual(((high&0xFFFF)<<16)+(low&0xFFFF)-(0x10000 if low&0x8000 else 0),base+0x308)
            self.assertEqual(result[0x300:],self.data[0x300:])

    def test_missing_entries_or_high_low_partners_are_rejected(self):
        for index in range(5):
            with self.assertRaises(ValueError):
                relocate(self.data,relocation(self.records[:index]+self.records[index+1:]),0x801A0000)
        with self.assertRaises(ValueError): relocate(self.data,relocation([]),0x801A0000)

    def test_record_type_order_section_and_instruction_guards(self):
        for bad in (0x04000000,0x84000000,0x41000000,0x44000001,0x44000300,0x45000000,0x46000000):
            with self.assertRaises(ValueError):
                relocate(self.data,relocation([bad]+self.records[1:]),0x801A0000)
        with self.assertRaises(ValueError):
            relocate(self.data,relocation(self.records+[self.records[-1]]),0x801A0000)
        for offset,word in ((0,0), (0,0x08000000), (0x260,0),
                            (0x260,0x3C028040), (0x264,0x24210000), (0x264,0x34424DC8)):
            data = bytearray(self.data)
            struct.pack_into('>I',data,offset,word)
            with self.assertRaises(ValueError): relocate(data,relocation(self.records),0x801A0000)

    def test_allocation_header_padding_and_ram_guards(self):
        valid = relocation(self.records)
        for base in (0,0x7FFFFFF0,0x801A0001,0x80400000-SIZE+16):
            with self.assertRaises(ValueError): relocate(self.data,valid,base)
        for size in (0,SIZE-1,SIZE+1):
            with self.assertRaises(ValueError): relocate(bytes(size),valid,0x801A0000)
        for size in (0,RELOC_SIZE-1,RELOC_SIZE+1):
            with self.assertRaises(ValueError): relocate(self.data,bytes(size),0x801A0000)
        for offset,word in ((0,0),(0,0x301),(0,SIZE),(12,16),(16,143),(RELOC_SIZE-4,128),(100,1)):
            data = bytearray(valid)
            struct.pack_into('>I',data,offset,word)
            with self.assertRaises(ValueError): relocate(self.data,data,0x801A0000)

    def test_prefix_inputs_require_complete_reference_hashes(self):
        with self.assertRaisesRegex(ValueError,'reference'): load_prefixes(b'', '')


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/runtime-module/module.json').is_file()
                     and (ROOT/'build/mail-grading/overlay.json').is_file(),
                     'Local original ROM and built mail/runtime modules required')
class MailGradingInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from runtime_module import add_runtime_module
        cls.rom = ROM_PATH.read_bytes()
        cls.replacements = {}
        cls.additions,cls.module = add_runtime_module(cls.rom,cls.replacements,ROOT/'build/runtime-module')
        cls.directory = ROOT/'build/mail-grading'
        cls.files = by_vrom(cls.rom)

    def run_install(self, replacements=None, additions=None, module=None, directory=None):
        replacements = dict(self.replacements) if replacements is None else replacements
        return install(self.rom,replacements,dict(self.additions) if additions is None else additions,
                       self.module if module is None else module,directory or self.directory)

    def test_exact_fixed_size_install_changes_only_the_native_entry_in_main_code(self):
        replacements = dict(self.replacements)
        report = self.run_install(replacements=replacements)
        self.assertEqual(len(replacements[VROM]),SIZE)
        self.assertEqual(len(replacements[RELOC_VROM]),RELOC_SIZE)
        before,after = self.replacements[CODE_VROM],replacements[CODE_VROM]
        offset = 0x800A86C4-CODE_RAM
        self.assertEqual(before[:offset]+before[offset+8:],after[:offset]+after[offset+8:])
        self.assertEqual(after[offset:offset+8],struct.pack('>2I',
                          0x08000000|((int(report['target_ram'],16)&0x0FFFFFFF)>>2),0))

    def test_source_and_overlapping_hook_rejection_leaves_plan_unchanged(self):
        for vrom in (VROM,RELOC_VROM,CODE_VROM):
            replacements = dict(self.replacements)
            if vrom == CODE_VROM:
                data = bytearray(replacements[vrom])
                data[0x800A86C4-CODE_RAM+3] ^= 1
                replacements[vrom] = bytes(data)
            else: replacements[vrom] = b''
            before = dict(replacements)
            with self.assertRaisesRegex(ValueError,'Overlapping'): self.run_install(replacements=replacements)
            self.assertEqual(before,replacements)
        for vrom in (VROM,RELOC_VROM,CODE_VROM):
            files = dict(self.files)
            data = bytearray(files[vrom].extract(self.rom))
            data[0x800A86C4-CODE_RAM if vrom == CODE_VROM else 0] ^= 1
            class Entry:
                def extract(self, ignored): return data
            files[vrom] = Entry()
            with patch('mail_grading.by_vrom',return_value=files):
                with self.assertRaisesRegex(ValueError,'Unexpected native'): self.run_install()

    def test_missing_stale_or_unbounded_resident_module_is_rejected(self):
        with self.assertRaises(ValueError): self.run_install(module={})
        with self.assertRaises(ValueError): self.run_install(additions={})
        from runtime_module import MODULE_VROM
        additions = dict(self.additions)
        additions[MODULE_VROM] = additions[MODULE_VROM][:-1]+b'!'
        with self.assertRaises(ValueError): self.run_install(additions=additions)
        for target in ('00000000','801948E0','8019C8E0','80195001'):
            module = copy.deepcopy(self.module)
            module['symbols']['af_mail_grade_native'] = target
            with self.assertRaisesRegex(ValueError,'outside'): self.run_install(module=module)

    def test_stale_metadata_artifacts_abi_and_relocations_are_rejected(self):
        originals = {name:(self.directory/name).read_bytes()
                     for name in ('overlay.json','overlay.bin','relocation.bin')}
        for mutation in ('source','sources','native','overlay','relocation','abi','entries'):
            with tempfile.TemporaryDirectory() as temporary:
                directory = Path(temporary)
                for name,data in originals.items(): (directory/name).write_bytes(data)
                report = json.loads(originals['overlay.json'])
                if mutation in ('source','sources','native'):
                    report[{'source':'source_sha256','sources':'sources','native':'native_grade_sha256'}[mutation]] = None
                elif mutation in ('overlay','abi'):
                    data = bytearray(originals['overlay.bin'])
                    data[16] ^= 1
                    (directory/'overlay.bin').write_bytes(data)
                    if mutation == 'abi': report['overlay_sha256'] = sha256(data)
                else:
                    data = bytearray(originals['relocation.bin'])
                    data[20:24] = b'\0'*4
                    (directory/'relocation.bin').write_bytes(data)
                    if mutation == 'entries': report['relocation_sha256'] = sha256(data)
                (directory/'overlay.json').write_text(json.dumps(report))
                before = dict(self.replacements)
                replacements = dict(before)
                with self.assertRaises(ValueError): self.run_install(replacements=replacements,directory=directory)
                self.assertEqual(replacements,before)


if __name__ == '__main__': unittest.main()
