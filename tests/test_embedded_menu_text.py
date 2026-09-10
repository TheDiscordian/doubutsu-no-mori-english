"""Complete embedded English, unchanged actions, relocated strings, and pool bounds."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups,CODE_VROM,CODE_RAM
import embedded_warnings as warning
import editor_confirmation as confirmation
import submenu_text as menus
from textcodec import command_info,decode,has_japanese
from translation_progress import CounterLedger
from catalogue_names import Image
from npc_mail_show import relocate_verified_data


@unittest.skipUnless((ROOT/'build/submenu-text-01/build.json').is_file(),'Local embedded English candidate required')
class EmbeddedMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/controller-pak-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/controller-pak-artwork-01/build.json').read_text())
        cls.image=(ROOT/'build/submenu-text-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/submenu-text-01/build.json').read_text())
        cls.rel,cls.symbols=menus.references()
        cls.info=command_info(by_vrom(cls.native)[CODE_VROM].extract(cls.native))

    def test_exact_confirmation_and_native_selection_layout(self):
        old,reloc=confirmation.source(self.native)
        data,profile=confirmation.patch_owner(self.native,self.image,self.rel,self.symbols)
        self.assertEqual(profile,self.report['editor_confirmation'])
        allowed=set(range(0xBF4,0xC18))|set(range(0x6B0,0x6B4))|set(range(0x700,0x704))
        for i,(offset,length,capacity,donor,text) in enumerate(confirmation.ROWS):
            self.assertEqual(data[offset:offset+capacity],text+bytes(capacity-len(text)))
            self.assertFalse(has_japanese(text,self.info))
            if i:
                at=0xC18+(i-1)*8
                self.assertEqual(struct.unpack_from('>2I',data,at),(confirmation.RAM+offset,len(text)))
                allowed.update(range(at+4,at+8))
        self.assertEqual(data[0x6B0:0x6B4],bytes.fromhex('3C0142EE'))
        self.assertEqual(data[0x700:0x704],bytes.fromhex('2406000B'))
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,data)) if i not in allowed))
        self.assertEqual(len(data),len(old));self.assertEqual(profile['prompt_x']+profile['prompt_width']/2,150)

    def test_full_warning_groups_relocate_without_changing_handlers_or_bss(self):
        for owner,texts in ((warning.WARNING,warning.WARNING_TEXT),(warning.PAK,warning.PAK_TEXT)):
            old,oldrel=warning.source(self.native,owner)
            data,reloc,profile=warning.patch_owner(self.native,self.image,owner)
            self.assertEqual(data[:owner.sections[0]],old[:owner.sections[0]])
            self.assertEqual(data[len(old):len(old)+16],bytes(16))
            self.assertEqual(len(reloc),len(oldrel));self.assertEqual(struct.unpack_from('>5I',reloc),(len(data),0,0,0,owner.sections[4]))
            oldgroups=warning.line_groups(old,owner);allowed=set()
            for i,((sx,sy,rows),lines) in enumerate(zip(oldgroups,texts)):
                table=owner.table+i*16
                self.assertEqual(data[table:table+8],old[table:table+8])
                self.assertEqual(data[table+12:table+16],old[table+12:table+16])
                allowed.update(range(table+8,table+12))
                for n,((at,x,y,ptr,count),text) in enumerate(zip(rows,lines)):
                    nx,ny,newptr,newlen=struct.unpack_from('>ffII',data,at)
                    self.assertEqual(ny,y);self.assertEqual(newlen,len(text))
                    self.assertEqual(decode(data[newptr-owner.ram:newptr-owner.ram+newlen],self.info),text)
                    self.assertGreaterEqual(newptr,owner.ram+len(old)+16)
                    self.assertLessEqual(newptr+newlen,owner.ram+len(data))
                    if owner==warning.PAK and i>=11 or owner==warning.WARNING and i==0 and n>=2:
                        self.assertEqual(nx,x)
                    allowed.update(range(at,at+4));allowed.update(range(at+8,at+16))
            self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,data)) if i not in allowed))
            rows=list(struct.unpack_from('>'+str(owner.sections[4])+'I',reloc,20))
            flat=[]
            for word in struct.unpack_from('>'+str(owner.sections[4])+'I',oldrel,20):
                section=word>>30;offset=word&0xFFFFFF
                offset+=(0,owner.sections[0],sum(owner.sections[:2]))[section-1]
                flat.append(0x40000000|word&0x3F000000|offset)
            self.assertEqual(rows,flat)
            spec=Image(owner.ram,len(data),struct.unpack_from('>5I',reloc))
            for address in (0x801A0010,0x802F8010,0x803F0010):
                loaded=relocate_verified_data(spec,data,reloc,address)
                for row in profile['rows']:
                    ptr,n=struct.unpack_from('>2I',loaded,row['offset']+8)
                    self.assertEqual(ptr,address+row['english_offset'])
                    self.assertEqual(loaded[ptr-address:ptr-address+n],row['text'].encode())
        self.assertIn('50,000',warning.WARNING_TEXT[2][1])
        self.assertIn('may erase its data.',warning.PAK_TEXT[9])

    def test_complete_cartridge_shared_verifiers_and_source_credit(self):
        image,patch,report=menus.build(self.native,self.base,self.prior)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,patch),image)
        parts=menus.verify_shared_parts(image,self.native,report['submenu_text'],report['editor_confirmation'])
        allocation=parts['allocation']
        self.assertEqual(allocation['combined_pool_bytes'],257152)
        self.assertEqual(allocation['additional_required_bytes'],960)
        self.assertLessEqual(allocation['conservative_required_bytes'],allocation['combined_pool_bytes'])
        old,new=by_vrom(self.base),by_vrom(image)
        moves={v:n for o in warning.OWNERS for v,n in ((o.vrom,o.new_vrom),(o.relocation,o.new_relocation))}
        changed=set(moves)|{confirmation.VROM,menus.PARENT,CODE_VROM,0x19D40}
        for v,entry in old.items():
            target=new[moves.get(v,v)];self.assertEqual(target.index,entry.index)
            if v not in changed:self.assertEqual(target.extract(image),entry.extract(self.base))
        a=old[CODE_VROM].extract(self.base);b=new[CODE_VROM].extract(image);at=menus.POOL_PATCH-CODE_RAM
        self.assertEqual(a[:at],b[:at]);self.assertEqual(a[at+4:],b[at+4:]);self.assertEqual(b[at:at+4],bytes.fromhex('25CE3220'))
        for rom,report,done in ((image,report,True),(self.base,self.prior,False)):
            ledger=CounterLedger(self.info);menus.measure_text(ledger,self.native,rom,report)
            summary=ledger.summary();self.assertGreater(summary['total_source_characters'],500)
            self.assertEqual(summary['replaced_source_characters'],summary['total_source_characters'] if done else 0)
        with self.assertRaises(ValueError):menus.verify_shared_parts(self.base,self.native)
        with self.assertRaises(ValueError):menus.verify_shared_parts(image,self.native,{'version':1})


if __name__=='__main__':unittest.main()
