"""RC1 keyboard regression: real ink, donor corners, page controls, and retention."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM, by_vrom, sha256, apply_ups
from catalogue_names import Image
from font import FONT_VROM, ATLAS_OFFSET, ATLAS_SIZE, WIDTH_TABLE, pixels, get_glyph
from keyboard_background_fix import donor
from keyboard_grid_labels import LABELS, encode_label
from keyboard_rc1_fix import (BASE_SHA, VROM, RELOC, OWNER, PREFIX, RAM, SPEC, TABLE,
    PAGE_WORDS, HINTS, source_hashes, recover, combined_symbols, metrics, build, core_source)
from npc_mail_show import relocate_verified_data

BASE=ROOT/'build/v1rc1-text-hud-fix-01/animal-forest-title-preview.z64'
OUT=ROOT/'build/v1rc1-keyboard-fix-01'


@unittest.skipUnless(BASE.is_file(),'Checked text/HUD follow-up required')
class KeyboardRC1Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=BASE.read_bytes(); cls.files=by_vrom(cls.base)
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        with tempfile.TemporaryDirectory(prefix='af-rc1-keyboard-') as temp:
            cls.image,cls.patch,cls.report=build(cls.native,cls.base,cls.rel,cls.symbols,Path(temp))
        cls.installed=by_vrom(cls.image)
        cls.data=cls.installed[VROM].extract(cls.image); cls.relocation=cls.installed[RELOC].extract(cls.image)
        cls.prefix,cls.prior_rel=recover(cls.files[VROM].extract(cls.base),cls.files[RELOC].extract(cls.base))

    def test_independent_build_matches_and_retains_native_font_and_sound(self):
        self.assertEqual(self.image,(OUT/'animal-forest-title-preview.z64').read_bytes())
        self.assertEqual(self.report,json.loads((OUT/'fixes.json').read_text()))
        self.assertEqual(self.report['sources'],source_hashes())
        self.assertEqual(apply_ups(self.native,self.patch),self.image)
        self.assertEqual(len(self.image),0x2000000)
        self.assertEqual(set(self.installed),set(self.files))
        for v,e in self.files.items():
            self.assertEqual(e.index,self.installed[v].index)
            if v not in (VROM,RELOC,OWNER,0x19D40):
                self.assertEqual(e.extract(self.base),self.installed[v].extract(self.image),hex(v))
        expected=bytearray(self.files[OWNER].extract(self.base))
        struct.pack_into('>4I',expected,SPEC['owner_at'],VROM,VROM+len(self.data),RAM,RAM+len(self.data))
        self.assertEqual(bytes(expected),self.installed[OWNER].extract(self.image))
        self.assertEqual(self.report['additional_pool_bytes'],0)
        self.assertLessEqual(self.report['shared_growth_bytes'],8192)
        self.assertFalse(self.report['save_format_changed'])

    def test_complete_prior_editor_is_preserved_at_two_runtime_addresses(self):
        allowed=set(self.report['editor']['touched_offsets'])
        expected=set(range(0x808882D8-RAM,0x808882DC-RAM)) | set(range(TABLE+320,TABLE+400))
        for at,old,new in PAGE_WORDS:
            expected.update(range(at,at+4))
            self.assertEqual(struct.unpack_from('>I',self.data,at)[0],new)
            self.assertEqual(struct.unpack_from('>I',self.prefix,at)[0],old)
        self.assertEqual(allowed,expected)
        for address in (0x80200010,0x80378010):
            before=relocate_verified_data(Image(RAM,PREFIX,struct.unpack_from('>5I',self.prior_rel)),
                self.prefix,self.prior_rel,address)
            after=relocate_verified_data(Image(RAM,len(self.data),struct.unpack_from('>5I',self.relocation)),
                self.data,self.relocation,address)
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,after))))
            target=address+self.report['editor']['symbols']['af_bg_editor_draw']
            self.assertEqual(struct.unpack_from('>I',after,0x808882D8-RAM)[0],0x0C000000|(target>>2&0x3FFFFFF))

    def test_one_symbol_page_preserves_every_supported_character_and_restriction(self):
        page,codes=combined_symbols(self.prefix)
        self.assertEqual(self.data[TABLE+320:TABLE+400],page)
        original=struct.unpack('>80H',self.prefix[TABLE+320:TABLE+480])
        self.assertEqual(set(codes),set(original)); self.assertEqual(len(set(codes)-{0xFFFF}),24)
        self.assertEqual(codes[29],0xCD); self.assertEqual(codes[39],0x20)
        with tempfile.TemporaryDirectory(prefix='af-rc1-page-host-') as temp:
            out=Path(temp); (out/'core.c').write_bytes(core_source())
            (out/'keys.bin').write_bytes(self.data[TABLE:TABLE+480])
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(ROOT/'overlays/keyboard_grid'),
                str(out/'core.c'),str(ROOT/'tests/keyboard_rc1_check.c'),'-o',str(out/'check')],
                check=True,capture_output=True,timeout=30)
            subprocess.run([str(out/'check'),str(out/'keys.bin')],check=True,capture_output=True,timeout=10)

    def test_shared_optical_placement_keeps_every_supported_glyph_inside_its_key(self):
        raw,profiles=metrics(self.base)
        at=self.report['editor']['symbols']['af_key_origins']
        self.assertEqual(self.data[at:at+len(raw)],raw)
        codes=set(struct.unpack('>240H',self.data[TABLE:TABLE+480]))-{0xFFFF,0xCD,0x20}
        codes.add(ord('_')); codes.add(ord('-'))
        for c in codes:
            p=profiles[str(c)]; left,top,right,bottom=p['bounds']; x,y=p['origin']
            self.assertGreaterEqual(left+x,1); self.assertLessEqual(right+x,14)
            self.assertGreaterEqual(top+y,0); self.assertLess(bottom+y,16)
            self.assertLessEqual(abs(x+p['ink_centre_x']-7.5),0.126)
        self.assertGreater(profiles['48']['origin'][0],5) # 0 moves right.
        self.assertLess(profiles['49']['origin'][0],5) # 1 moves left.
        self.assertLess(profiles['95']['origin'][1],0) # _ no longer spills below its key.
        self.assertGreater(profiles['95']['bounds'][1]+profiles['95']['origin'][1],10)

    def test_donor_frames_and_complete_hint_ink_stay_inside_visible_background(self):
        frames,unused=donor(self.rel,self.symbols)
        for name,frame in zip(('af_bg_frame_a','af_bg_frame_b'),frames):
            at=self.report['editor']['symbols'][name]
            self.assertEqual(self.data[at:at+1024],frame)
        # Independent geometry model: lower-left, upper-right, lower-right,
        # upper-left. Native emitted commands are checked in the focused probe.
        quads=[(42,170,160,227,0,0,555,575,1),(160,111,278,168,2048,1024,-555,-575,1),
               (160,168,278,225,2048,1024,-555,-575,0),(42,113,160,170,0,0,555,575,0)]
        def alpha(x,y):
            for left,top,right,bottom,s,t,ds,dt,texture in quads:
                if left<=x<right and top<=y<bottom:
                    tx=max(0,min(31,int(s/32+(x-left)*ds/1024)))
                    ty=max(0,min(31,int(t/32+(y-top)*dt/1024)))
                    return frames[texture][ty*32+tx]&15
            return 0
        font=self.files[FONT_VROM].extract(self.base)
        atlas=pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
        cuts=self.files[CODE_VROM].extract(self.base)[WIDTH_TABLE:WIDTH_TABLE+256]
        for value,y in zip(HINTS,(200,212)):
            value=encode_label(value); x=160-sum(12-cuts[c] for c in value)*.375
            self.assertEqual(self.data[PREFIX:].count(value+b'\0'),1)
            for c in value:
                for gy,row in enumerate(get_glyph(atlas,c)):
                    for gx,v in enumerate(row):
                        if v:
                            self.assertGreaterEqual(alpha(x+(gx+.5)*.75,y+(gy+.5)*.75),8)
                x+=(12-cuts[c])*.75
        self.assertEqual(self.report['artwork']['right_pair_y_offset'],-2)
        self.assertEqual(self.report['artwork']['lower_right_direction'],[-1,-1])

    def test_unknown_inputs_and_changed_prefix_do_not_patch(self):
        self.assertEqual(sha256(self.base),BASE_SHA)
        with self.assertRaises(ValueError): recover(self.files[VROM].extract(self.base)[:-1],self.prior_rel)
        with self.assertRaises(ValueError): combined_symbols(bytes(PREFIX))
        with tempfile.TemporaryDirectory(prefix='af-rc1-reject-') as temp:
            with self.assertRaises(ValueError):
                build(self.native,self.native,self.rel,self.symbols,Path(temp))


if __name__=='__main__': unittest.main()
