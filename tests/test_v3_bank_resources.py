"""Complete native bank relocation plan and its actual DMA/allocation consumers."""
import copy
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,DMA_START,by_vrom,sha256,u32
from v3_asset_loader import BLOB
from v3_bank_resources import PAIRS,PELLY_DESCRIPTOR,checked_link,relocate_owners
from v3_furniture_install import inputs
import v3_physical_resources as physical

LOCK=ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json'
LINKED=ROOT/'build/v3-post-office-bank-linked-04'


class BankResourcesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base,cls.prior=inputs(LOCK);cls.files=by_vrom(cls.base)
        cls.packet,cls.owners,cls.link=checked_link(cls.base,cls.prior,LINKED)
        cls.changes,cls.growth,cls.report=relocate_owners(cls.base,cls.prior,cls.owners,
            cls.link,blob_bytes=cls.files[BLOB].size)

    def test_native_loader_pairs_and_complete_resources_in_isolated_image(self):
        result=bytearray(self.base)
        for row in self.growth:
            vrom,target=row['vrom'],row.get('target_vrom',row['vrom'])
            at=row['physical'];n=row['bytes'];original=self.files[vrom]
            self.assertFalse(any(result[at:at+n]))
            self.assertFalse(physical.overlaps(self.prior['physical_resources'],at,at+n))
            self.assertEqual(sha256(self.changes[vrom]),row['sha256'])
            result[at:at+n]=self.changes[vrom]
            struct.pack_into('>4I',result,DMA_START+original.index*16,target,target+n,at,0)
        installed=by_vrom(result);directory={e.index:e for e in installed.values()}
        for body,reloc,target,target_rel,_ in PAIRS:
            # Mirror DmaMgr_GetOvlOffsets: the *next directory entry* supplies
            # relocation bounds, even when the physical allocations differ.
            entry=installed[target];following=directory[entry.index+1]
            self.assertEqual(following.vstart,target_rel)
            self.assertEqual(entry.index,self.files[body].index)
            self.assertEqual(following.index,self.files[reloc].index)
            self.assertEqual(entry.extract(result),self.changes[body])
            self.assertEqual(following.extract(result),self.changes[reloc])
            head=struct.unpack_from('>5I',following.extract(result))
            self.assertEqual(sum(head[:4]),entry.size)
            for original in (self.files[body],self.files[reloc]):
                end=original.pend or original.pstart+original.size
                self.assertEqual(result[original.pstart:end],self.base[original.pstart:end])
        for row in self.growth:
            self.assertEqual(installed[row.get('target_vrom',row['vrom'])].extract(result),self.changes[row['vrom']])
        physical.verify(result,self.prior['physical_resources'])
        self.assertEqual(len(result),len(self.base))
        self.assertFalse(self.report['installed']);self.assertFalse(self.report['native_execution_verified'])

    def test_actual_descriptors_full_pelly_allocation_and_retained_core(self):
        r=self.report;core=bytearray(self.changes[CODE_VROM]);at=PELLY_DESCRIPTOR-CODE_RAM
        descriptor=r['pelly_descriptor'];before=bytes.fromhex(descriptor['before'])
        after=bytes.fromhex(descriptor['after'])
        self.assertEqual(core[at:at+32],after)
        start,end,ram,limit,loaded,profile,name,allocation=struct.unpack('>8I',after)
        self.assertEqual((start,end),(PAIRS[1][2],PAIRS[1][2]+len(self.changes[PAIRS[1][0]])))
        self.assertEqual(limit-ram,len(self.changes[PAIRS[1][0]]))
        self.assertEqual(after[16:],before[16:]);self.assertEqual((loaded,name,allocation),(0,0,0))
        self.assertEqual(profile,0x809C5000)
        self.assertEqual(descriptor['additional_loaded_bytes'],64)
        core[at:at+32]=before;self.assertEqual(core,self.owners[CODE_VROM])
        menu=r['submenu_descriptor'];body=bytearray(self.changes[menu['vrom']]);at=menu['offset']
        self.assertEqual(body[at:at+32],bytes.fromhex(menu['after']))
        self.assertEqual(body[at+8:at+32],bytes.fromhex(menu['before'])[8:])
        body[at:at+32]=bytes.fromhex(menu['before']);self.assertEqual(body,self.owners[menu['vrom']])
        self.assertEqual(r['submenu_additional_pool_bytes'],64)
        self.assertEqual(u32(self.changes[CODE_VROM],0x800C4B10-CODE_RAM),0x25CEEA60+64)

    def test_complete_owner_mutations_and_partial_inputs_reject(self):
        for vrom in self.owners:
            changes=dict(self.owners);data=bytearray(changes[vrom]);data[-1]^=1;changes[vrom]=data
            with self.subTest(vrom=f'{vrom:08X}'),self.assertRaisesRegex(ValueError,'linked bank owners'):
                relocate_owners(self.base,self.prior,changes,self.link,blob_bytes=self.files[BLOB].size)
        changes=dict(self.owners);del changes[PAIRS[0][1]]
        with self.assertRaisesRegex(ValueError,'linked bank owners'):
            relocate_owners(self.base,self.prior,changes,self.link,blob_bytes=self.files[BLOB].size)
        for n in (-1,self.files[BLOB].size-1,len(self.base)):
            with self.subTest(blob_bytes=n),self.assertRaisesRegex(ValueError,'import-blob reservation'):
                relocate_owners(self.base,self.prior,self.owners,self.link,blob_bytes=n)
        changed=copy.deepcopy(self.link);changed['base_abi']+=1
        with self.assertRaisesRegex(ValueError,'linked bank owners'):
            relocate_owners(self.base,self.prior,self.owners,changed,blob_bytes=self.files[BLOB].size)


if __name__=='__main__':unittest.main()
