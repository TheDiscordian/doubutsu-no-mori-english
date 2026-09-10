"""Gyroid English preserves its callback, native actions, and complete prices."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups,CODE_VROM
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from translation_progress import CounterLedger
from textcodec import command_info,decode
import gyroid_service as gyroid


@unittest.skipUnless((ROOT/'build/gyroid-service-01/build.json').is_file(),'Local gyroid English candidate required')
class GyroidServiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/submenu-text-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/submenu-text-01/build.json').read_text())
        cls.image=(ROOT/'build/gyroid-service-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/gyroid-service-01/build.json').read_text())
        cls.info=command_info(by_vrom(cls.native)[CODE_VROM].extract(cls.native))

    def test_complete_native_state_mapping_and_preserved_code(self):
        old,oldrel=gyroid.source(self.native)
        data,reloc,parent,profile=gyroid.patch_owner(self.native,self.image,*gyroid.references())
        self.assertEqual(profile,self.report['gyroid_service'])
        self.assertEqual(len(reloc),len(oldrel))
        self.assertEqual(struct.unpack_from('>5I',reloc),(len(data),0,0,0,42))
        allowed=set(range(gyroid.TABLE,gyroid.TABLE+12*8))
        for address,before,after in profile['patches']:
            at=address-gyroid.RAM
            self.assertEqual(struct.unpack_from('>I',old,at)[0],before)
            self.assertEqual(struct.unpack_from('>I',data,at)[0],after)
            allowed.update(range(at,at+4))
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,data)) if i not in allowed))
        self.assertEqual(data[gyroid.STATE:gyroid.STATE+80],bytes(80))
        self.assertEqual(data[0xDCC:0xDD8],old[0xDCC:0xDD8])
        # The existing interrupt callback store stays at state +2C, not inside
        # the new +30 buffer. No sales or item selection code is replaced.
        self.assertEqual(data[0x8088D9A4-gyroid.RAM:0x8088D9A8-gyroid.RAM],bytes.fromhex('AD48002C'))
        self.assertEqual(struct.unpack_from('>4I',parent),
            (gyroid.NEW_VROM,gyroid.NEW_VROM+len(data),gyroid.RAM,gyroid.RAM+len(data)))
        for i,(_,text) in enumerate(gyroid.ROWS):
            ptr,n=struct.unpack_from('>2I',data,gyroid.TABLE+i*8)
            self.assertEqual(data[ptr-gyroid.RAM:ptr-gyroid.RAM+n],text)
            self.assertEqual(decode(text,self.info),text.decode())
        # Complete native unsigned-16-bit prices retain every digit, both gaps,
        # and Bells, with no truncation and without writing the callback.
        for price in range(65536):
            value=gyroid.PREFIX+str(price).encode()+gyroid.ROWS[11][1]
            self.assertLessEqual(len(value),22)
            self.assertEqual(int(value[5:-6]),price)
            state=bytearray(b'S'*80);state[48:70]=value.ljust(22,b' ')
            self.assertEqual(state[:48],b'S'*48);self.assertEqual(state[70:],b'S'*10)

    def test_all_relocation_sites_and_english_bounds(self):
        old,oldrel=gyroid.source(self.native)
        data,reloc,_,profile=gyroid.patch_owner(self.native,self.image,*gyroid.references())
        expected=[]
        for row in struct.unpack_from('>42I',oldrel,20):
            at=(row&0xFFFFFF)+(0,3616,3856)[(row>>30)-1]
            expected.append(0x40000000|(row&0x3F000000)|at)
        self.assertEqual(list(struct.unpack_from('>42I',reloc,20)),expected)
        spec=Image(gyroid.RAM,len(data),struct.unpack_from('>5I',reloc))
        for base in (0x801A0010,0x802F8010,0x803F0010):
            loaded=relocate_verified_data(spec,data,reloc,base)
            for row in profile['rows']:
                ptr,n=struct.unpack_from('>2I',loaded,gyroid.TABLE+8*row['state'])
                self.assertGreaterEqual(ptr,base+gyroid.STATE+80)
                self.assertLessEqual(ptr+n,base+len(data))
                self.assertEqual(loaded[ptr-base:ptr-base+n],row['text'].encode())
            self.assertEqual(loaded[gyroid.STATE:gyroid.STATE+80],bytes(80))
        allocation=profile['allocation']
        self.assertEqual(allocation['additional_required_bytes'],256)
        self.assertEqual(allocation['combined_reserved_bytes']-allocation['combined_required_bytes'],3200)

    def test_complete_cartridge_shared_owner_and_translation_credit(self):
        image,patch,report=gyroid.build(self.native,self.base,self.prior)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,patch),image)
        gyroid.verify_shared_parts(image,self.native,report['gyroid_service'])
        before,after=by_vrom(self.base),by_vrom(image)
        for v,entry in before.items():
            if v not in (gyroid.VROM,gyroid.RELOC,gyroid.PARENT,0x19D40):
                self.assertEqual(after[v].extract(image),entry.extract(self.base))
        for rom,report,complete in ((image,report,True),(self.base,self.prior,False)):
            ledger=CounterLedger(self.info);gyroid.measure_text(ledger,self.native,rom,report)
            summary=ledger.summary();self.assertEqual(len(ledger.rows),13)
            self.assertEqual(summary['total_source_characters'],103)
            self.assertEqual(summary['replaced_source_characters'],103 if complete else 0)
        with self.assertRaises(ValueError):gyroid.verify_shared_parts(self.base,self.native)
        with self.assertRaises(ValueError):gyroid.verify_shared_parts(image,self.native,{'version':1})


if __name__=='__main__':unittest.main()
