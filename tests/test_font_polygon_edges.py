"""Glyph-border interiors, retained code, allocation bounds, and exact patch application."""
import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom
from font import FONT_VROM,ATLAS_OFFSET,ATLAS_SIZE,get_glyph,pixels
from font_polygon_edges import MODULE,VROM,PREFIX,build,inputs,padded_glyph
from textcodec import LATIN

@unittest.skipUnless((ROOT/'build/v1rc2/Animal Forest English V1RC2.z64').is_file(),'V1RC2 source required')
class FontEdgesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/v1rc2/Animal Forest English V1RC2.z64').read_bytes()
        with tempfile.TemporaryDirectory(prefix='af-font-edges-') as temp:
            cls.image,cls.patch,cls.report=build(cls.native,cls.base,Path(temp))
        cls.old=by_vrom(cls.base);cls.new=by_vrom(cls.image)

    def test_all_glyph_ink_is_unchanged_with_zero_filtering_border(self):
        _,previous,_,_,mapping,bank=inputs(self.base)
        atlas=pixels(self.old[FONT_VROM].extract(self.base)[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE])
        glyphs=[get_glyph(atlas,c) for c in sorted(LATIN)]
        glyphs += [get_glyph(pixels(previous[8992+64:8992+1600]),i) for i in range(16)]
        self.assertEqual(len(glyphs),97)
        for slot,glyph in enumerate(glyphs):
            copied=pixels(bank[slot*144:(slot+1)*144])
            self.assertEqual([copied[(y+1)*16+1:(y+1)*16+13] for y in range(16)],glyph)
            self.assertTrue(all(v==0 for i,v in enumerate(copied) if i//16 in (0,17) or i%16 not in range(1,13)))
        self.assertEqual({c for c,slot in enumerate(mapping) if slot!=255},LATIN)
        with self.assertRaises(ValueError): padded_glyph([[0]*11]*16)

    def test_configuration_crc_heap_bound_and_unchanged_prefix(self):
        old=self.old[MODULE].extract(self.base);new=self.new[MODULE].extract(self.image)
        changed=set(range(0x68,0x88))|set(range(0x1964,0x1968))
        self.assertTrue(all(a==b or i in changed for i,(a,b) in enumerate(zip(old,new))))
        self.assertEqual(struct.unpack_from('>I',new,0x1964)[0],0x2C427000)
        config=struct.unpack_from('>8I',new,0x68);blob=self.new[VROM].extract(self.image)
        self.assertEqual(config[1],len(blob));self.assertLessEqual(config[2],0x7000)
        self.assertEqual(config[6],zlib.crc32(blob));self.assertEqual(config[2]+config[3],len(blob))
        self.assertEqual(blob[8:PREFIX],self.old[VROM].extract(self.base)[8:PREFIX])
        self.assertEqual(self.report['allocation_growth_bytes'],len(blob)-12704)
        self.assertEqual(self.report['per_glyph_vertex_bytes'],64)
        self.assertEqual(self.report['per_glyph_display_commands'],9)

    def test_speech_advances_fonts_and_other_resources_remain(self):
        self.assertEqual(set(self.old),set(self.new))
        for v,entry in self.old.items():
            self.assertEqual(entry.index,self.new[v].index)
            if v not in (MODULE,VROM,0x19D40): self.assertEqual(entry.extract(self.base),self.new[v].extract(self.image),hex(v))
        self.assertEqual(self.old[CODE_VROM].extract(self.base),self.new[CODE_VROM].extract(self.image))
        self.assertFalse(self.report['save_format_changed'])

    def test_patch_and_source_rejection(self):
        self.assertEqual(apply_ups(self.native,self.patch),self.image)
        self.assertEqual(len(self.image),32*1024*1024)
        with self.assertRaises(ValueError): inputs(self.native)
        changed=bytearray(self.base);changed[-1]^=1
        with self.assertRaises(ValueError): inputs(changed)

if __name__=='__main__': unittest.main()
