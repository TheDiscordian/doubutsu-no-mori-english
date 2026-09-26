"""Complete effect source/artwork and additive controller relocation checks."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,u32
from npc_mail_show import relocate_verified_data
from v3_furniture_pipeline import Source
from v3_player_actions import native_references
import v3_room_effects as effects
import tests.test_v3_equipment_runtime as shared


class EffectTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        rom=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();files=by_vrom(rom)
        cls.owner=files[effects.VROM].extract(rom);cls.reloc=files[effects.RELOC].extract(rom)
        cls.original_art=files[0x1410000].extract(rom)

    sanitized=shared.HostTests.sanitized

    def test_source_and_complete_sprite(self):
        receipt=effects.source_contract(self.source);art,row=effects.flash_art(self.source)
        self.assertEqual(len(receipt['functions']),8)
        self.assertEqual(art[:256],self.source.raw('ef_takurami01_1'))
        self.assertEqual(art[:256],self.original_art[0x11DD0:0x11ED0])
        self.assertEqual(art[256:320],self.source.raw('ef_takurami01_kira_v'))
        original=self.source.raw('ef_takurami01_kira_modelT');restored=bytearray(art[320:])
        for offset,pointer in ((0x3C,0x06000000),(0x7C,0x06000100)):
            self.assertEqual(u32(restored,offset),pointer);struct.pack_into('>I',restored,offset,0)
        self.assertEqual(restored,original);self.assertEqual(row['triangles'],2)
        changed=copy.copy(self.source);raw=bytearray(changed.rel)
        raw[changed.sections[1][0]+0x29B888+16]^=1;changed.rel=bytes(raw)
        with self.assertRaisesRegex(ValueError,'source flash'):effects.source_contract(changed)

    def test_appended_sprite_and_native_profile_packets(self):
        art,row=effects.flash_art(self.source)
        bank,receipt=effects.append_sprite(self.original_art,art,row)
        self.assertEqual(bank[:len(self.original_art)],self.original_art)
        self.assertEqual(receipt['graphics'],[0x06016C90,0x06016E68])
        self.assertEqual(receipt['model'],0x06016DD8)
        appended=bytearray(bank[len(self.original_art)+8:])
        for at,relative in ((320+0x3C,0),(320+0x7C,256)):
            self.assertEqual(u32(appended,at),0x06016C98+relative)
            struct.pack_into('>I',appended,at,0x06000000+relative)
        self.assertEqual(appended,art)
        symbols={}
        for number,prefix in enumerate(('af_v3_flash_','af_v3_flash_controller_')):
            for i,role in enumerate(('init','ct','mv','dw')):symbols[prefix+role]=0x804C8000+number*128+i*32
        for kind in (False,True):
            overlay=effects.profile_overlay(symbols,kind)
            self.assertEqual(len(overlay),64)
            self.assertEqual(struct.unpack_from('>5I',overlay,32),(0,32,0,0,0))
            self.assertEqual(u32(overlay,60),32)
            self.assertEqual(struct.unpack_from('>hhI',overlay,16),(-2,255,0xC47A0CFF))
        symbols['af_v3_flash_ct']=0x804CC000
        with self.assertRaisesRegex(ValueError,'escapes'):effects.profile_overlay(symbols)

    def test_controller_adds_without_replacing_and_relocates_state(self):
        additions=[dict(id=111,overlay=[0x2500000,0x2500020,0x80700000,0x80700020,0x80700000],
                        graphics=[0x06016C90,0x06016E68],unique=0),
                   dict(id=112,overlay=[0x2500040,0x2500060,0x80700100,0x80700120,0x80700100],
                        graphics=[0,0],unique=0)]
        owner,reloc,row=effects.extend_controller(self.owner,self.reloc,additions)
        self.assertEqual(row['count'],113);self.assertEqual(row['additional_scene_bytes'],3280)
        self.assertEqual(reloc[16:],self.reloc[16:])
        restored=bytearray(owner[:len(self.owner)])
        for patch in row['patches']:
            self.assertEqual(u32(restored,patch['offset']),patch['after'])
            struct.pack_into('>I',restored,patch['offset'],patch['before'])
        self.assertEqual(restored,self.owner)
        self.assertEqual(owner[len(self.owner):sum(effects.SECTIONS)],bytes(effects.SECTIONS[3]))
        for table in row['tables']:
            at,old,n=table['offset'],table['original_offset'],111*table['stride']
            self.assertEqual(owner[at:at+n],self.owner[old:old+n])
        def spec(sections):return SimpleNamespace(ram=effects.RAM,resident_bytes=sum(sections),
            sections=(*sections,struct.unpack_from('>I',reloc,16)[0]))
        for base in (0x80708000,0x8071F800):
            old=relocate_verified_data(spec(effects.SECTIONS),self.owner,self.reloc,base,memory_end=0x80800000)
            new=relocate_verified_data(spec(tuple(row['sections'])),owner,reloc,base,memory_end=0x80800000)
            groups,_,_,_,_=native_references(new,reloc,expected_sections=tuple(row['sections']))
            table_targets={base+t['original_offset']:base+t['offset'] for t in row['tables']}
            for hi,refs in effects.REFERENCES.items():
                self.assertEqual(groups[hi],[(lo,table_targets[base+target-effects.RAM]) for lo,target in refs])
            restore=bytearray(new[:len(old)])
            for p in row['patches']:restore[p['offset']:p['offset']+4]=old[p['offset']:p['offset']+4]
            self.assertEqual(restore,old)
        bad=copy.deepcopy(additions);bad[1]['id']=111
        with self.assertRaisesRegex(ValueError,'Non-additive'):effects.extend_controller(self.owner,self.reloc,bad)
        bad=copy.deepcopy(additions);bad[0]['overlay'][3]+=0xC00
        with self.assertRaisesRegex(ValueError,'loader bounds'):effects.extend_controller(self.owner,self.reloc,bad)

    def test_flash_runtime_under_sanitizers(self):
        self.sanitized('v3_room_effects_test.c')

    def test_profile_loader_under_sanitizers(self):
        self.sanitized('v3_effect_loader_test.c')

    def test_current_controller_retains_timed_lamp_and_installed_wall(self):
        from v3_furniture_install import inputs
        image,report=inputs(ROOT/'build/v3-idle-hit-category-auto-02/cartridge/build-lock.json')
        files=by_vrom(image);owner=files[effects.VROM].extract(image);reloc=files[effects.RELOC].extract(image)
        before=effects.checked_controller(owner,reloc)
        self.assertTrue(before['timed_lamp_retained'])
        art,row=effects.flash_art(self.source);_,bank=effects.append_sprite(self.original_art,art,row)
        additions=[dict(id=111,overlay=[0x2500000,0x2500020,0x80700000,0x80700020,0x80700000],
                        graphics=bank['graphics'],unique=0),
                   dict(id=112,overlay=[0x2500040,0x2500060,0x80700100,0x80700120,0x80700100],
                        graphics=[0,0],unique=0)]
        changed,fixed,receipt=effects.extend_controller(owner,reloc,additions)
        self.assertTrue(receipt['original']['timed_lamp_retained'])
        self.assertEqual(changed[0x36B0:0x36C0],owner[0x36B0:0x36C0])
        self.assertEqual(fixed[16:],reloc[16:])
        count=u32(reloc,16)
        for base in (0x80708000,0x8071F800):
            old_spec=SimpleNamespace(ram=effects.RAM,resident_bytes=sum(effects.SECTIONS),sections=(*effects.SECTIONS,count))
            new_spec=SimpleNamespace(ram=effects.RAM,resident_bytes=len(changed),sections=(*receipt['sections'],count))
            old=relocate_verified_data(old_spec,owner,reloc,base,memory_end=0x80800000)
            new=bytearray(relocate_verified_data(new_spec,changed,fixed,base,memory_end=0x80800000)[:len(old)])
            for p in receipt['patches']:new[p['offset']:p['offset']+4]=old[p['offset']:p['offset']+4]
            self.assertEqual(new,old)
        wall=effects.wall_binding(image,report)
        self.assertEqual((wall['source_index'],wall['index'],wall['pixels']),(65,76,8192))


OUTPUT=ROOT/os.environ.get('V3_EFFECTS_BUILD','build/v3-room-effects-runtime-02')


@unittest.skipUnless((OUTPUT/'build-lock.json').exists(),'Installed shared effects required')
class InstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from v3_furniture_install import inputs
        cls.image,cls.report=inputs(OUTPUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.old=by_vrom(cls.image),by_vrom(cls.base)
        cls.equipment=cls.report['equipment_resources'];cls.room=cls.equipment['room_rigs']
        cls.effects=cls.room['effects'];cls.blob=cls.files[0x2200000].extract(cls.image)

    def test_complete_controller_reconstruction_and_relocation(self):
        c=self.effects['controller'];loader=c['loader']
        data=(OUTPUT/'effect_loader/code.bin').read_bytes()
        owner,reloc,row=effects.extend_controller(self.old[effects.VROM].extract(self.base),
            self.old[effects.RELOC].extract(self.base),c['additions'],loader=(data,loader))
        self.assertEqual(owner,self.files[c['vrom']].extract(self.image))
        self.assertEqual(reloc,self.files[c['reloc']].extract(self.image))
        self.assertEqual(self.files[c['reloc']].index,self.files[c['vrom']].index+1)
        for base in (0x80200010,0x80328010):
            spec=SimpleNamespace(ram=effects.RAM,resident_bytes=len(owner),sections=struct.unpack_from('>5I',reloc))
            loaded=relocate_verified_data(spec,owner,reloc,base,memory_end=0x80800000)
            self.assertEqual(u32(loaded,0xF64)&0x3FFFFFF,(base+sum(effects.SECTIONS))>>2&0x3FFFFFF)
            self.assertEqual(loaded[0x36B0:0x36C0],owner[0x36B0:0x36C0])
            from catalogue_names import elf_inventory
            for at,kind,target,name in elf_inventory(loader['elf_relocations'],ram=effects.RAM):
                if kind==4:
                    dest=((effects.RAM+at)&0xF0000000)|(u32(owner,at)&0x3FFFFFF)<<2
                    expected=dest-effects.RAM+base if effects.RAM<=dest<effects.RAM+len(owner) else dest
                    self.assertEqual((u32(loaded,at)&0x3FFFFFF)<<2,expected&0xFFFFFFF)

    def test_bound_profiles_and_retained_resources(self):
        from aflib import CODE_RAM,CODE_VROM,apply_ups
        changed={effects.VROM,effects.RELOC,0x1410000,0x2200000,CODE_VROM,0x1A00000,0x19D40}
        from v3_asset_loader import MODULE
        changed.add(MODULE)
        for v,e in self.old.items():
            if v not in changed:self.assertEqual(e.extract(self.base),self.files[v].extract(self.image),f'{v:08X}')
        art=self.files[0x1410000].extract(self.image)
        self.assertEqual(art[:self.old[0x1410000].size],self.old[0x1410000].extract(self.base))
        self.assertEqual(len(art)-self.old[0x1410000].size,472)
        core=bytearray(self.files[CODE_VROM].extract(self.image));hook=self.effects['controller']['descriptor']
        at=hook['address']-CODE_RAM;self.assertEqual(core[at:at+32].hex(),hook['after'])
        core[at:at+32]=bytes.fromhex(hook['before'])
        self.assertEqual(core,self.old[CODE_VROM].extract(self.base))
        for p in self.effects['profiles']:
            actual=self.blob[p['blob_offset']:p['blob_offset']+64]
            self.assertEqual(actual,effects.profile_overlay(self.room['code']['symbols'],p['id']==112))
            self.assertEqual(u32(actual,24),zlib.crc32(actual[:24]))
        module=self.blob[self.equipment['blob_offset']:self.equipment['blob_offset']+self.equipment['bytes']]
        self.assertEqual(u32(module,effects.LOADER_BRIDGE-0x804A3000),self.effects['bootstrap_loader'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['furniture'],self.prior['furniture'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.image)

    def test_profiles_rebind_after_later_shared_compilation(self):
        blob=bytearray(self.blob);receipt=copy.deepcopy(self.effects);symbols=dict(self.room['code']['symbols'])
        for name in symbols:
            if name.startswith('af_v3_flash_'):symbols[name]+=4
        effects.rebind_profiles(receipt,blob,symbols)
        for p in receipt['profiles']:
            self.assertEqual(blob[p['blob_offset']:p['blob_offset']+64],effects.profile_overlay(symbols,p['id']==112))
        blob[receipt['profiles'][0]['blob_offset']]^=1
        with self.assertRaisesRegex(ValueError,'complete installed'):effects.rebind_profiles(receipt,blob,symbols)


if __name__=='__main__':unittest.main()
