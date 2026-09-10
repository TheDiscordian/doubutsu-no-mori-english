"""Whole native actor relocation, guarded ownership, and atomic installation."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256
from event_actor import (RAM,VROM,RELOCATION,NEW_VROM,NEW_RELOCATION,METADATA,PREFIX_BYTES,
                         CALLS,POINTERS,GATE,validate,verify_installation,install,elf_inventory,load)
from npc_mail_show import relocate_verified_data
from current_letter_actor_fixture import current_actor_fixture


@unittest.skipUnless((ROOT/'build/v0-hardware-fixes-02/build.json').is_file()
                     and (ROOT/'build/shop-notice-event/overlay.json').is_file(),
                     'Current combined cartridge and event actor required')
class EventActorInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = f = current_actor_fixture(ROOT,'event')
        cls.native,cls.rom,cls.build,cls.module = f.native,f.rom,f.build,f.module
        cls.directory,cls.data,cls.reloc,cls.report = f.directory,f.data,f.reloc,f.report
        cls.creator = f.creator
        cls.replacements,cls.additions,cls.moved = f.replacements,f.additions,f.moved

    def test_actual_combined_actor_keeps_final_accent_adapter(self):
        f = self.fixture
        spec = verify_installation(f.current,f.native,f.current_build['event_actor']['overlay'],f.module,f.creator)
        self.assertEqual(spec.sections,(38128,0,0,0,433))
        self.assertIn('accent_mail',f.current_build['event_actor']['overlay'])
        self.assertNotEqual(f.current,f.rom)  # Early-reader/pre-accent fixture only.

    def validate(self,data=None,reloc=None,report=None):
        return validate(self.native,self.data if data is None else data,self.reloc if reloc is None else reloc,
                        self.report if report is None else report,self.module,self.creator,self.report['creator'])

    def test_complete_native_rows_and_new_global_addresses_relocate_together(self):
        spec = verify_installation(self.rom,self.native,self.report,self.module,self.creator)
        self.assertEqual(elf_inventory((self.directory/'elf-relocations.txt').read_text()),self.report['elf_relocations'])
        self.assertEqual(spec.sections[:4],(len(self.data),0,0,0))
        for base in (0x801A0010,0x802F8010,0x803F0000):
            image = relocate_verified_data(spec,self.data,self.reloc,base)
            for address,_,name in CALLS:
                word = struct.unpack_from('>I',image,address-RAM)[0]
                self.assertEqual(0x80000000|((word&0x3FFFFFF)<<2),base+self.report['symbols'][name])
            for address,_,name in POINTERS:
                self.assertEqual(struct.unpack_from('>I',image,address-RAM)[0],base+self.report['symbols'][name])
            for address,_,after in GATE: self.assertEqual(struct.unpack_from('>I',image,address-RAM)[0],after)
            for at,kind,target,name in self.report['elf_relocations']:
                if kind!=4: continue
                original = struct.unpack_from('>I',self.data,at)[0]
                actual = struct.unpack_from('>I',image,at)[0]
                self.assertEqual(0x80000000|((actual&0x3FFFFFF)<<2),
                                 (0x80000000|((original&0x3FFFFFF)<<2))+base-RAM)
        self.assertEqual(self.data[0x6A80:PREFIX_BYTES],bytes(304))
        branch = struct.unpack_from('>I',self.data,0x8096191C-RAM)[0]
        self.assertEqual(0x80961920+(branch&65535)*4,0x80961934)

    def test_stale_sources_code_work_and_relocations_are_rejected(self):
        for key,value in (('bytes',0),('sources',{}),('imports',{}),('module_sha256','0'*64),
                          ('creator',{}),('text_bytes',len(self.data)),('creator_sha256','0'*64)):
            report = deepcopy(self.report);report[key] = value
            with self.assertRaises(ValueError): self.validate(report=report)
        for at in (0x398,0x7AC,0x7D0,0x6074,0x607C,0x6A50,PREFIX_BYTES,self.report['symbols']['af_event_work']):
            data = bytearray(self.data);data[at] ^= 1
            with self.assertRaises(ValueError): self.validate(data=bytes(data),report={**self.report,'overlay_sha256':sha256(data)})
        for mutation in ('remove','duplicate','location','kind','target'):
            report = deepcopy(self.report)
            if mutation=='remove': report['elf_relocations'].pop()
            elif mutation=='duplicate': report['elf_relocations'].append(report['elf_relocations'][0])
            elif mutation=='location': report['elf_relocations'][0][0] = 0
            elif mutation=='kind': report['elf_relocations'][0][1] = 2
            else: report['elf_relocations'][0][2] += 4
            with self.assertRaises(ValueError): self.validate(report=report)
        with self.assertRaises(ValueError): elf_inventory('00000000 00000000 R_MIPS_GPREL16 00000000 symbol')

    def test_install_reconstructs_integrated_rom_and_preserves_maps_on_failure(self):
        replacements,additions,moved = dict(self.replacements),dict(self.additions),dict(self.moved)
        report = install(self.native,replacements,additions,moved,self.module,self.directory)
        self.assertEqual(report,self.build['event_actor'])
        self.assertEqual(additions,self.additions)
        self.assertEqual({v for v in replacements if replacements[v]!=self.replacements.get(v)},
                         {CODE_VROM,VROM,RELOCATION})
        self.assertEqual(replace_dma(self.native,replacements,moved,additions),self.rom)
        for mutation in ('catalog','reader','occupied','metadata','helper','module','dates','relocation'):
            replacements,additions,moved = dict(self.replacements),dict(self.additions),dict(self.moved)
            module = deepcopy(self.module)
            if mutation=='catalog': additions.pop(0x03000000)
            elif mutation=='reader': replacements.pop(0x7908A0)
            elif mutation=='occupied': additions[NEW_VROM] = b'occupied'
            elif mutation in ('metadata','helper'):
                code = bytearray(replacements[CODE_VROM]);code[(METADATA if mutation=='metadata' else 0x800B6A3C)-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(code)
            elif mutation=='module': module['runtime_sources'] = {}
            elif mutation=='dates': replacements.pop(VROM)
            else: replacements[RELOCATION] = b'changed'
            before = deepcopy((replacements,additions,moved,module))
            with self.assertRaises(ValueError): install(self.native,replacements,additions,moved,module,self.directory)
            self.assertEqual((replacements,additions,moved,module),before)


if __name__ == '__main__': unittest.main()
