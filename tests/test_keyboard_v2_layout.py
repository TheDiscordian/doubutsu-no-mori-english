"""Current compact keyboard layout, preserved bindings, and V2-08 corrections."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from catalogue_names import Image
import keyboard_v2_layout as layout
from keyboard_rc1_fix import metrics
from npc_mail_show import relocate_verified_data

OUT=ROOT/os.environ.get('AF_LAYOUT_BUILD','build/v2-keyboard-fit-11')
PREVIOUS=ROOT/'build/v2-keyboard-polish-10-final'
PREVIOUS_SHA='64335524d2159b5715a73f331c741e11ea12b9a98c67a5903905e406765ddb01'


class KeyboardLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(ROOT/'build/v2-performance-fix-08/Animal Forest English V2.z64').read_bytes()
        cls.rom=(OUT/'Animal Forest English V2.z64').read_bytes()
        cls.report=json.loads((OUT/'build.json').read_text())
        cls.old,cls.new=by_vrom(cls.base),by_vrom(cls.rom)
        cls.data=cls.new[layout.VROM].extract(cls.rom)
        cls.rel=cls.new[layout.RELOC].extract(cls.rom)

    def test_current_sources_output_and_original_rom_patch(self):
        self.assertEqual(sha256(self.base),layout.BASE_SHA)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(self.report['sources'],layout.sources())
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUT/'Animal Forest English V2.ups').read_bytes()),self.rom)

    def test_unrelated_resources_including_museum_and_credits_unchanged(self):
        self.assertEqual(set(self.old),set(self.new))
        for v,entry in self.old.items():
            self.assertEqual(entry.index,self.new[v].index)
            if v not in (layout.VROM,layout.RELOC,layout.OWNER,0x19D40):
                self.assertEqual(entry.extract(self.base),self.new[v].extract(self.rom),hex(v))
        owner=bytearray(self.old[layout.OWNER].extract(self.base))
        struct.pack_into('>4I',owner,layout.v2.SPEC['owner_at'],layout.VROM,
            layout.VROM+len(self.data),layout.RAM,layout.RAM+len(self.data))
        self.assertEqual(owner,self.new[layout.OWNER].extract(self.rom))
        previous=(PREVIOUS/'Animal Forest English V2.z64').read_bytes()
        self.assertEqual(sha256(previous),PREVIOUS_SHA)
        for v,entry in by_vrom(previous).items():
            if v not in (layout.VROM,0x19D40):
                self.assertEqual(entry.extract(previous),self.new[v].extract(self.rom),hex(v))

    def test_complete_editor_input_prefix_at_two_load_addresses(self):
        old=self.old[layout.VROM].extract(self.base); rel=self.old[layout.RELOC].extract(self.base)
        layout.recover(old,rel)
        for at in (0x80200010,0x80378010):
            before=relocate_verified_data(Image(layout.RAM,len(old),struct.unpack_from('>5I',rel)),old,rel,at)
            after=relocate_verified_data(Image(layout.RAM,len(self.data),struct.unpack_from('>5I',self.rel)),
                                        self.data,self.rel,at)
            self.assertEqual(before[:layout.CALL],after[:layout.CALL])
            self.assertEqual(before[layout.CALL+4:layout.PREFIX],after[layout.CALL+4:layout.PREFIX])
        broken=bytearray(old); broken[30000]^=1
        with self.assertRaises(ValueError):layout.recover(broken,rel)

    def test_key_metrics_native_buttons_and_hidden_shortcuts(self):
        values,_=metrics(self.base); symbols=self.report['editor']['symbols']
        at=symbols['af_key_origins']; self.assertEqual(self.data[at:at+len(values)],values)
        at=symbols['af_v2_icons']
        icons=list(struct.iter_unpack('>IIIHBBHHBBBB',self.data[at:at+264]))
        self.assertEqual([r[3] for r in icons],[0,0x20,0x2000,0x8000,0x4000,0x10,0x1000,8,2,1,4])
        for row in icons[1:]:self.assertNotEqual(row[0],row[1])
        positions={r[3]:r[6:8] for r in icons}
        for button,position in ((0x10,(180,118)),(0x2000,(104,206)),(0x1000,(170,208)),
                                (0x8000,(242,181)),(0x4000,(254,203)),(8,(255,119))):
            self.assertEqual(positions[button],position)
        for value in (b'L+A:',b'L+Z:',b'Alter'):
            self.assertNotIn(value,self.data[layout.PREFIX:])
        for flag in ('input_code_changed','save_format_changed','key_positions_changed',
                     'font_pixels_changed','sound_code_changed'):
            self.assertFalse(self.report[flag])
        self.assertTrue(self.report['combo_shortcuts_retained'])

    def test_existing_reservation_and_clipped_geometry(self):
        self.assertLessEqual(self.report['shared_growth_bytes'],8192)
        self.assertEqual(self.report['additional_pool_bytes'],0)
        helper,panel=layout.draw_source()
        self.assertIn(b'60+16*(i%10)+slide[i/10]+dx',helper)
        self.assertIn(b'52+x-42,128+y-113,184,76',panel)
        self.assertIn(b'x+width>320 || y+height>240',panel)
        self.assertIn(b'!space(graph,8192)',helper)
        self.assertNotIn(b'gDPFillRectangle',panel)
        self.assertIn(b'G_TF_BILERP',panel)
        self.assertEqual(self.report['frame']['native_panel_bounds'],[52,128,236,204])

    def test_compiled_grips_and_button_letter_positions(self):
        symbols=self.report['editor']['symbols']
        def table(prefix,size):
            matches=[v for k,v in symbols.items() if k.startswith(prefix+'.')]
            self.assertEqual(len(matches),1)
            return self.data[matches[0]:matches[0]+size]
        sections=list(struct.iter_unpack('>5B',table('sections',35)))
        self.assertEqual(sections,[(42,112,62,24,12),(108,112,64,20,10),(176,112,62,24,12),
            (12,150,54,70,24),(232,114,56,61,20),(228,175,76,56,22),(87,198,148,30,15)])
        for x,y,w,h,radius in sections:
            self.assertTrue(0<radius<=min(w,h)//2)
            self.assertTrue(0<=x<x+w<=320 and 0<=y<y+h<=240)
            xs,ys=[x,x+radius,x+w-radius,x+w],[y,y+radius,y+h-radius,y+h]
            self.assertEqual(sum((xs[c+1]-xs[c])*(ys[r+1]-ys[r])
                                 for r in range(3) for c in range(3)),w*h)
        letters=list(struct.iter_unpack('>HHBB2s',table('letters',32)))
        self.assertEqual(letters,[(0x20,107,115,0,b'L\0'),(0x10,371,115,0,b'R\0'),
            (0x8000,493,181,1,b'A\0'),(0x4000,518,203,1,b'B\0')])

    def test_antialiased_corner_and_unedited_gc_tray(self):
        symbols=self.report['editor']['symbols']; at=symbols['af_bg_corner']
        packed=self.data[at:at+128]
        self.assertEqual(packed,layout.corner_texture())
        self.assertEqual(sha256(packed),self.report['frame']['corner_sha256'])
        self.assertEqual(self.report['frame']['corner_format'],'I4')
        pixels=[alpha for p in packed for alpha in (p>>4,p&15)]
        self.assertTrue(any(0<p<15 for p in pixels))
        self.assertEqual(pixels[0],0)
        self.assertEqual(pixels[-1],15)
        self.assertTrue(all(pixels[y*16+x]==pixels[x*16+y] for x in range(16) for y in range(16)))
        old_dir=PREVIOUS
        old_report=json.loads((old_dir/'build.json').read_text())
        old_rom=(old_dir/'Animal Forest English V2.z64').read_bytes()
        old_data=by_vrom(old_rom)[layout.VROM].extract(old_rom)
        for name in ('af_bg_frame_a','af_bg_frame_b'):
            a,b=old_report['editor']['symbols'][name],symbols[name]
            self.assertEqual(old_data[a:a+1024],self.data[b:b+1024])

    def test_only_position_tables_change_from_previous_keyboard(self):
        previous=(PREVIOUS/'Animal Forest English V2.z64').read_bytes()
        before=by_vrom(previous)[layout.VROM].extract(previous)
        symbols=self.report['editor']['symbols']
        old_report=json.loads((PREVIOUS/'build.json').read_text())
        self.assertEqual(symbols,old_report['editor']['symbols'])
        self.assertEqual(len(before),len(self.data))
        allowed=set()
        for prefix,size in (('af_v2_icons',264),('labels.',64),('sections.',35)):
            addresses=[v for k,v in symbols.items() if k==prefix or k.startswith(prefix)]
            self.assertEqual(len(addresses),1)
            allowed.update(range(addresses[0],addresses[0]+size))
        changed={i for i,(a,b) in enumerate(zip(before,self.data)) if a!=b}
        self.assertTrue(changed)
        self.assertFalse(changed-allowed)


if __name__=='__main__':unittest.main()
