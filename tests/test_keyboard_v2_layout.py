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

OUT=ROOT/os.environ.get('AF_LAYOUT_BUILD','build/v2-keyboard-layout-09-final')


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
        self.assertIn(b'gDPFillRectangle(g++,px+edge,top,px+p[2]-edge,bottom)',panel)
        self.assertEqual(self.report['frame']['native_panel_bounds'],[52,128,236,204])

    def test_compiled_grips_and_button_letter_positions(self):
        symbols=self.report['editor']['symbols']
        def table(prefix,size):
            matches=[v for k,v in symbols.items() if k.startswith(prefix+'.')]
            self.assertEqual(len(matches),1)
            return self.data[matches[0]:matches[0]+size]
        sections=list(struct.iter_unpack('>5B',table('sections',35)))
        rounded,grip=table('rounded',16),table('grip',16)
        self.assertEqual(sections,[(42,112,62,24,0),(108,112,64,20,0),(176,112,62,24,0),
            (12,150,54,70,1),(228,115,76,50,0),(234,158,66,72,1),(87,198,148,36,1)])
        for x,y,w,h,taper in sections:
            for row in range(16):
                edge=(grip if taper else rounded)[row]*w//64
                self.assertTrue(0<=x+edge<x+w-edge<=320)
                self.assertTrue(0<=y+row*h//16<y+(row+1)*h//16<=240)
        letters=list(struct.iter_unpack('>HHBB2s',table('letters',32)))
        self.assertEqual(letters,[(0x20,107,115,0,b'L\0'),(0x10,215,206,0,b'R\0'),
            (0x8000,493,121,1,b'A\0'),(0x4000,518,143,1,b'B\0')])


if __name__=='__main__':unittest.main()
