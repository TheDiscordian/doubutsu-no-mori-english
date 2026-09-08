"""Source-bound actor limits, complete relocation inventory, and atomic install."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,replace_dma,sha256
from fortune_actor import (RAM,VROM,RELOCATION,NEW_VROM,NEW_RELOCATION,METADATA,PROFILE_SIZE,
                           INIT_SLOT,GIVE_SLOT,CALLBACKS,CHARGE_ARGUMENT,CHARGE_CALL,INSTANCE_BYTES,PREFIX_BYTES,native_sources,
                           validate,metadata,verify_installation,install,elf_inventory,
                           RECOVERY_CODE_GUARDS,verify_recovery_code)
from npc_mail_show import relocate_verified_data


@unittest.skipUnless((ROOT/'build/fortune-recovery-pilot/build.json').is_file(),
                     'Compiled installed Miko actor fixture required')
class FortuneActorInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.rom = (ROOT/'build/fortune-recovery-pilot/animal-forest-halfwidth.z64').read_bytes()
        cls.build = json.loads((ROOT/'build/fortune-recovery-pilot/build.json').read_text())
        cls.module = cls.build['runtime_module']
        cls.directory = ROOT/'build/fortune-recovery-actor'
        cls.data = (cls.directory/'overlay.bin').read_bytes()
        cls.reloc = (cls.directory/'relocation.bin').read_bytes()
        cls.report = json.loads((cls.directory/'overlay.json').read_text())
        # Reconstruct the preceding configured cartridge's replacement maps.
        baseline = ROOT/'build/fortune-slip-foundation-pilot'
        cls.previous = (baseline/'animal-forest-halfwidth.z64').read_bytes()
        previous_report = json.loads((baseline/'build.json').read_text())
        files = by_vrom(cls.previous)
        cls.moved = {int(k,16):int(v,16) for k,v in previous_report['vrom_relocations'].items()}
        cls.replacements = {int(k,16):files[cls.moved.get(int(k,16),int(k,16))].extract(cls.previous)
                            for k in previous_report['replacement_files']}
        cls.additions = {int(k,16):files[int(k,16)].extract(cls.previous) for k in previous_report['added_files']}

    def test_installed_actor_retains_dma_adjacency_and_native_pool_bounds(self):
        spec = verify_installation(self.rom,self.native,self.report,self.module)
        self.assertLessEqual(len(self.data),8192)
        # Native ovlmgr_Load owns separate relocation scratch; it is not part
        # of the NPC actor pool. The full loaded actor bound remains unchanged.
        self.assertLessEqual(len(self.reloc),4096)
        self.assertEqual(spec.resident_bytes,len(self.data))
        self.assertEqual(struct.unpack_from('>I',self.data,PROFILE_SIZE)[0],2400)
        self.assertEqual(elf_inventory((self.directory/'elf-relocations.txt').read_text()),self.report['elf_relocations'])
        files = by_vrom(self.rom)
        self.assertEqual(files[NEW_RELOCATION].index,files[NEW_VROM].index+1)
        for base in (0x801A0010,0x802F8010,0x803F0000):
            relocated = relocate_verified_data(spec,self.data,self.reloc,base)
            for offset,name in CALLBACKS.items():
                self.assertEqual(struct.unpack_from('>I',relocated,offset)[0],base+self.report['symbols'][name])
            self.assertEqual(struct.unpack_from('>I',relocated,CHARGE_ARGUMENT)[0],0x8FA40020)
            jump = struct.unpack_from('>I',relocated,CHARGE_CALL)[0]
            self.assertEqual(0x80000000|((jump&0x3FFFFFF)<<2),base+self.report['symbols']['af_miko_fortune_charge'])
            self.assertEqual(relocated[2992:PREFIX_BYTES],bytes(16))

    def test_bad_actor_sources_profile_pointers_bounds_and_imports_are_rejected(self):
        for key,value in (('bytes',len(self.data)+16),('instance_bytes',2401),('text_bytes',3008),
                          ('sources',{}),('imports',{}),('module_sha256','0'*64),('word_sha256','0'*64)):
            bad = deepcopy(self.report);bad[key] = value
            with self.assertRaises(ValueError): validate(self.native,self.data,self.reloc,bad,self.module)
        for offset in (0,PROFILE_SIZE,*CALLBACKS,CHARGE_ARGUMENT,CHARGE_CALL,2992,self.report['symbols']['af_fortune_words']):
            data = bytearray(self.data);data[offset] ^= 1
            bad = {**self.report,'overlay_sha256':sha256(data)}
            with self.assertRaises(ValueError): validate(self.native,bytes(data),self.reloc,bad,self.module)
        for vrom in (VROM,RELOCATION,0x8681F0):
            changed = bytearray(self.native);changed[by_vrom(self.native)[vrom].pstart] ^= 1
            with self.assertRaises(ValueError): native_sources(bytes(changed))
        changed = bytearray(by_vrom(self.native)[CODE_VROM].extract(self.native))
        changed[0x80057D3C-CODE_RAM] ^= 1
        with self.assertRaises(ValueError): native_sources(replace_dma(self.native,{CODE_VROM:bytes(changed)}))

    def test_missing_extra_bad_and_unpaired_relocations_are_rejected(self):
        for change in ('missing','extra','location','kind','target'):
            bad = deepcopy(self.report)
            if change == 'missing': bad['elf_relocations'].pop()
            elif change == 'extra': bad['elf_relocations'].append(bad['elf_relocations'][0])
            elif change == 'location': bad['elf_relocations'][0][0] = 0
            elif change == 'kind': bad['elf_relocations'][0][1] = 0
            elif change == 'target': bad['elf_relocations'][0][2] += 4
            with self.assertRaises(ValueError): validate(self.native,self.data,self.reloc,bad,self.module)
        for offset in (0,16,20,len(self.reloc)-1):
            reloc = bytearray(self.reloc);reloc[offset] ^= 1
            bad = {**self.report,'relocation_sha256':sha256(reloc)}
            with self.assertRaises(ValueError): validate(self.native,self.data,bytes(reloc),bad,self.module)
        # Even matching file/report hashes cannot bless a changed fixed address.
        at = next(row[0] for row in self.report['elf_relocations'] if row[1] == 6 and row[3] == 'af_miko_private')
        data = bytearray(self.data);data[at+3] ^= 4
        with self.assertRaises(ValueError):
            validate(self.native,bytes(data),self.reloc,{**self.report,'overlay_sha256':sha256(data)},self.module)
        for text in ('00000000 00000000 R_MIPS_GPREL16 00000000 symbol',
                     'not a supported R_MIPS_26 record'):
            with self.assertRaises(ValueError): elf_inventory(text)

    def test_payment_and_lifecycle_guards_reject_changed_helpers(self):
        original = by_vrom(self.native)[CODE_VROM].extract(self.native)
        verify_recovery_code(original)
        verify_recovery_code(by_vrom(self.rom)[CODE_VROM].extract(self.rom))
        for start,end,_ in RECOVERY_CODE_GUARDS:
            for at in (start,end-1):
                changed = bytearray(original);changed[at-CODE_RAM] ^= 1
                with self.assertRaises(ValueError): verify_recovery_code(changed)
        changed = bytearray(original);changed[RECOVERY_CODE_GUARDS[0][0]-CODE_RAM] ^= 1
        with self.assertRaises(ValueError): native_sources(replace_dma(self.native,{CODE_VROM:bytes(changed)}))
        installed = bytearray(by_vrom(self.rom)[CODE_VROM].extract(self.rom))
        installed[RECOVERY_CODE_GUARDS[-1][0]-CODE_RAM] ^= 1
        with self.assertRaises(ValueError):
            verify_installation(replace_dma(self.rom,{CODE_VROM:bytes(installed)}),
                                self.native,self.report,self.module)

    def test_atomic_install_matches_cartridge_and_missing_dependencies_retain_maps(self):
        replacements,additions,moved = dict(self.replacements),dict(self.additions),dict(self.moved)
        report = install(self.native,replacements,additions,moved,self.module,self.directory)
        self.assertEqual(report,self.build['fortune_actor'])
        self.assertEqual(additions,self.additions)
        self.assertEqual(moved,{**self.moved,VROM:NEW_VROM,RELOCATION:NEW_RELOCATION})
        self.assertEqual(replacements[VROM],self.data);self.assertEqual(replacements[RELOCATION],self.reloc)
        changed = [v for v in replacements if replacements[v] != self.replacements.get(v)]
        self.assertEqual(set(changed),{CODE_VROM,VROM,RELOCATION})
        for mutation in ('catalog','reader','occupied','native_metadata','payment_helper','module'):
            replacements,additions,moved = dict(self.replacements),dict(self.additions),dict(self.moved)
            module = deepcopy(self.module)
            if mutation == 'catalog': additions.pop(0x03050000)
            elif mutation == 'reader': replacements.pop(0x7908A0)
            elif mutation == 'occupied': additions[NEW_VROM] = b'occupied'
            elif mutation == 'native_metadata':
                value = bytearray(replacements[CODE_VROM]);value[METADATA-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(value)
            elif mutation == 'payment_helper':
                value = bytearray(replacements[CODE_VROM]);value[0x800B80B4-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(value)
            elif mutation == 'module': module['runtime_sources'] = {}
            before = dict(replacements),dict(additions),dict(moved),deepcopy(module)
            with self.assertRaises(ValueError): install(self.native,replacements,additions,moved,module,self.directory)
            self.assertEqual((replacements,additions,moved,module),before)


if __name__ == '__main__': unittest.main()
