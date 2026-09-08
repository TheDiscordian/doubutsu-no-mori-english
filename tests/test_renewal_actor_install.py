"""Native actor ownership, complete relocation merge, and atomic cartridge integration."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256
from renewal_actor import (RAM,VROM,RELOCATION,NEW_VROM,NEW_RELOCATION,METADATA,PREFIX_BYTES,GATE,
                           native_sources,validate,verify_installation,install,elf_inventory,load,
                           CODE_GUARDS,verify_code)
from npc_mail_show import relocate_verified_data


@unittest.skipUnless((ROOT/'build/renewal-actor-pilot/build.json').is_file(),
                     'Compiled installed renewal actor fixture required')
class RenewalActorInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        pilot = ROOT/'build/renewal-actor-pilot'
        cls.rom = (pilot/'animal-forest-halfwidth.z64').read_bytes()
        cls.build = json.loads((pilot/'build.json').read_text());cls.module = cls.build['runtime_module']
        cls.directory = ROOT/'build/renewal-actor'
        cls.data,cls.reloc,cls.report,cls.creator_code = load(cls.directory)
        previous = ROOT/'build/leaflet-dates-pilot'
        cls.previous = (previous/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((previous/'build.json').read_text());files = by_vrom(cls.previous)
        cls.moved = {int(k,16):int(v,16) for k,v in report['vrom_relocations'].items()}
        cls.replacements = {int(k,16):files[cls.moved.get(int(k,16),int(k,16))].extract(cls.previous)
                            for k in report['replacement_files']}
        cls.additions = {int(k,16):files[int(k,16)].extract(cls.previous) for k in report['added_files']}

    def validate(self,data=None,reloc=None,report=None):
        return validate(self.native,self.data if data is None else data,self.reloc if reloc is None else reloc,
                        self.report if report is None else report,self.module,self.creator_code,self.report['creator'])

    def test_installed_actor_has_complete_native_relocation_and_unchanged_profile(self):
        spec = verify_installation(self.rom,self.native,self.report,self.module,self.creator_code)
        self.assertEqual(elf_inventory((self.directory/'elf-relocations.txt').read_text()),self.report['elf_relocations'])
        native,_ = native_sources(self.native)
        self.assertEqual(self.data[0xC90:PREFIX_BYTES],native[0xC90:])
        self.assertEqual(spec.sections[:4],(len(self.data),0,0,0))
        for base in (0x801A0010,0x802F8010,0x803F0000):
            data = relocate_verified_data(spec,self.data,self.reloc,base)
            for at,target in ((0,base+self.report['symbols']['af_renewal_deliver']),
                              (0x2F8,base),(0xCA0,base+0x6E8)):
                word = struct.unpack_from('>I',data,at)[0]
                if at == 0xCA0:  # Profile init pointer retains original relative address.
                    self.assertEqual(word,base+struct.unpack_from('>I',native,at)[0]-RAM)
                else: self.assertEqual(0x80000000|((word&0x3FFFFFF)<<2),target)
            for at,_,word in GATE: self.assertEqual(struct.unpack_from('>I',data,at)[0],word)
            # Actual branch target is the original return-address load, not its delay slot.
            branch = struct.unpack_from('>I',data,0x300)[0]
            self.assertEqual(0x304+(branch&65535)*4,0x33C)

    def test_stale_sources_prefix_creator_and_bounds_are_rejected(self):
        for key,value in (('bytes',len(self.data)+16),('sources',{}),('imports',{}),
                          ('module_sha256','0'*64),('creator',{}),('creator_sha256','0'*64)):
            report = deepcopy(self.report);report[key] = value
            with self.assertRaises(ValueError): self.validate(report=report)
        for at in (0,4,0x300,0x318,0xC90,PREFIX_BYTES,PREFIX_BYTES+100):
            data = bytearray(self.data);data[at] ^= 1
            with self.assertRaises(ValueError): self.validate(data=bytes(data),report={**self.report,'overlay_sha256':sha256(data)})
        for entry in (0,PREFIX_BYTES,0xFFFF,True):
            report = deepcopy(self.report);report['symbols']['af_renewal_deliver'] = entry
            with self.assertRaises(ValueError): self.validate(report=report)

    def test_relocations_and_fixed_data_instructions_are_exhaustively_bound(self):
        for change in ('missing','extra','location','kind','target'):
            report = deepcopy(self.report)
            if change == 'missing': report['elf_relocations'].pop()
            elif change == 'extra': report['elf_relocations'].append(report['elf_relocations'][0])
            elif change == 'location': report['elf_relocations'][0][0] = 0
            elif change == 'kind': report['elf_relocations'][0][1] = 2
            else: report['elf_relocations'][0][2] += 4
            with self.assertRaises(ValueError): self.validate(report=report)
        for at in (0,16,20,len(self.reloc)-1):
            reloc = bytearray(self.reloc);reloc[at] ^= 1
            with self.assertRaises(ValueError): self.validate(reloc=bytes(reloc),report={**self.report,'relocation_sha256':sha256(reloc)})
        at = next(row[0] for row in self.report['elf_relocations'] if row[1]==6 and row[3]=='af_mail_generation_capital')
        data = bytearray(self.data);data[at+3] ^= 4
        with self.assertRaises(ValueError): self.validate(data=bytes(data),report={**self.report,'overlay_sha256':sha256(data)})
        with self.assertRaises(ValueError): elf_inventory('00000000 00000000 R_MIPS_GPREL16 00000000 symbol')

    def test_every_ownership_and_mail_helper_is_guarded_in_original_and_installed_code(self):
        original = by_vrom(self.native)[CODE_VROM].extract(self.native)
        verify_code(original);verify_code(by_vrom(self.rom)[CODE_VROM].extract(self.rom))
        for start,end,_ in CODE_GUARDS:
            for at in (start,end-1):
                code = bytearray(original);code[at-CODE_RAM] ^= 1
                with self.assertRaises(ValueError): verify_code(code)

    def test_atomic_install_composes_with_dates_and_retains_maps_on_missing_dependencies(self):
        replacements,additions,moved = dict(self.replacements),dict(self.additions),dict(self.moved)
        report = install(self.native,replacements,additions,moved,self.module,self.directory)
        self.assertEqual(report,self.build['renewal_actor'])
        self.assertEqual(additions,self.additions)
        self.assertEqual(moved,{**self.moved,VROM:NEW_VROM,RELOCATION:NEW_RELOCATION})
        self.assertEqual({v for v in replacements if replacements[v] != self.replacements.get(v)},
                         {CODE_VROM,VROM,RELOCATION})
        self.assertEqual(replace_dma(self.native,replacements,moved,additions),self.rom)
        for mutation in ('catalog','reader','occupied','metadata','helper','module','dates','relocation'):
            replacements,additions,moved = dict(self.replacements),dict(self.additions),dict(self.moved)
            module = deepcopy(self.module)
            if mutation == 'catalog': additions.pop(0x03000000)
            elif mutation == 'reader': replacements.pop(0x7908A0)
            elif mutation == 'occupied': additions[NEW_VROM] = b'occupied'
            elif mutation in ('metadata','helper'):
                code = bytearray(replacements[CODE_VROM]);code[(METADATA if mutation=='metadata' else 0x80094C10)-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(code)
            elif mutation == 'module': module['runtime_sources'] = {}
            elif mutation == 'dates': replacements.pop(VROM)
            else: replacements[RELOCATION] = b'changed'
            before = deepcopy((replacements,additions,moved,module))
            with self.assertRaises(ValueError): install(self.native,replacements,additions,moved,module,self.directory)
            self.assertEqual((replacements,additions,moved,module),before)


if __name__ == '__main__': unittest.main()
