"""Whole native owners and relocation-aware entry/lifecycle connections."""
import copy
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_furniture_install import inputs
from v3_post_office_install import ENTRIES,native_entries


class PostOfficeEntriesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base,cls.prior=inputs(ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json')
        # Distinct fixture destinations test actual native consumer patching;
        # these are not linked code or a cartridge installation.
        cls.exports={name:0x807D9000+0x100*i for i,name in enumerate(ENTRIES)}

    def test_full_owners_shims_relocation_and_retained_menu_arena(self):
        changes,report=native_entries(self.base,self.exports,code_bounds=(0x807D9000,0x807DA000))
        files=by_vrom(self.base)
        self.assertFalse(report['installed']);self.assertTrue(report['resource_relocation_required'])
        self.assertEqual(report['arena']['additional_pool_bytes'],64)
        self.assertEqual(u32(changes[CODE_VROM],0x800C4B10-CODE_RAM),0x25CEEA60+64)
        original_core=files[CODE_VROM].extract(self.base);modified=bytearray(changes[CODE_VROM])
        struct.pack_into('>I',modified,0x800C4B10-CODE_RAM,0x25CEEA60)
        self.assertEqual(modified,original_core)
        for vrom,reloc,ram,key in ((0x79B120,0x79BF10,0x808979C0,'repayment'),
                (0x8A6C10,0x8A8A10,0x809C3420,'pelly')):
            old=files[vrom].extract(self.base);oldrel=files[reloc].extract(self.base)
            new,newrel=changes[vrom],changes[reloc]
            oldhead=struct.unpack_from('>5I',oldrel);newhead=struct.unpack_from('>5I',newrel)
            allowed={p['address']-ram+i for p in report[key]['patches'] for i in range(4)}
            expected=report[key]['entries']
            entries=expected if isinstance(expected,list) else list(expected.values())
            originals=([(5,0x80898688)],[(5,0x80898710)],[(5,0x80898520)]) if key=='repayment' else (
                [(6,0x809C3BE8)],[(5,0x809C4EA8),(6,0x809C3708)],[(6,0x809C3510)])
            names=ENTRIES[:3] if key=='repayment' else ENTRIES[3:]
            for load in (0x80200010,0x80348010):
                a=relocate_verified_data(Image(ram,sum(oldhead[:4]),oldhead),old,oldrel,load)
                b=relocate_verified_data(Image(ram,len(new),newhead),new,newrel,load)
                self.assertTrue(all(x==b[i] for i,x in enumerate(a) if i not in allowed))
                for entry,arguments,name in zip(entries,originals,names):
                    at=entry-ram
                    for index,(register,original) in enumerate(arguments):
                        arg=at+8*index
                        self.assertEqual(u32(b,arg)>>16&31,register)
                        address=((u32(b,arg)&65535)<<16)+struct.unpack_from('>h',b,arg+6)[0]
                        self.assertEqual(address,load+original-ram)
                    # Resident jumps do not move with the overlay, while every
                    # original function argument does, at both actual bases.
                    jump_at=at+8*len(arguments)
                    target=0x80000000|(u32(b,jump_at)&0x3FFFFFF)<<2
                    self.assertEqual(target,self.exports[name])
                    self.assertEqual(u32(b,jump_at+4),0)
            if not allowed:self.assertEqual(new[:len(old)],old)
        menu=bytearray(changes[0x7749C0]);descriptor=report['descriptor'];at=descriptor['offset']
        self.assertEqual(menu[at:at+32].hex(),descriptor['after'])
        menu[at:at+32]=bytes.fromhex(descriptor['before'])
        self.assertEqual(menu,files[0x7749C0].extract(self.base))

    def test_partial_or_unowned_entry_sets_reject(self):
        for variant in ('missing','unaligned','outside'):
            exports=copy.copy(self.exports)
            if variant=='missing':del exports[ENTRIES[0]]
            elif variant=='unaligned':exports[ENTRIES[0]]+=1
            else:exports[ENTRIES[0]]=0x80000000
            with self.assertRaisesRegex(ValueError,'complete linked entry set'):
                native_entries(self.base,exports,code_bounds=(0x807D9000,0x807DA000))


if __name__=='__main__':unittest.main()
