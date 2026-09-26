"""Complete effect source/artwork and additive controller relocation checks."""
import copy
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest

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


if __name__=='__main__':unittest.main()
