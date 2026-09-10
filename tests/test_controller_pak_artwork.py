"""Controller Pak labels preserve complete glyphs, readers, and saved-data code."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups,CODE_VROM
from controller_pak_artwork import ASSET,OWNER,ROWS,patch_asset,build,measure_text
from font import FONT_VROM,ATLAS_OFFSET,ATLAS_SIZE,pixels,get_glyph
from textcodec import command_info
from translation_progress import CounterLedger


@unittest.skipUnless((ROOT/'build/controller-pak-artwork-01/build.json').is_file(),'Local Pak artwork required')
class ControllerPakArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/birthday-screen-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/birthday-screen-01/build.json').read_text())
        cls.image=(ROOT/'build/controller-pak-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/controller-pak-artwork-01/build.json').read_text())

    def test_complete_unscaled_glyphs_and_unchanged_graphics_readers(self):
        data,profile=patch_asset(self.native);files=by_vrom(self.native)
        self.assertEqual(profile,self.report['controller_pak_artwork'])
        old=files[ASSET].extract(self.native);font=files[FONT_VROM].extract(self.native)
        atlas=pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE]);allowed=set()
        for japanese,text,offset,width,load,quad in ROWS:
            actual=pixels(data[offset:offset+width*8]);columns=[]
            for i,ch in enumerate(text):
                glyph=get_glyph(atlas,ord(ch));ink=[x for x in range(12) if any(row[x] for row in glyph)]
                if i:columns.append([0]*16)
                columns.extend([[row[x] for row in glyph] for x in range(min(ink),max(ink)+1)])
            left=(width-len(columns))//2;self.assertGreaterEqual(left,0)
            for y in range(16):
                self.assertEqual(actual[y*width:(y+1)*width],
                    [0]*left+[column[y] for column in columns]+[0]*(width-left-len(columns)))
            self.assertEqual(data[load:load+72],old[load:load+72])
            self.assertEqual(data[quad:quad+64],old[quad:quad+64])
            self.assertEqual(struct.unpack_from('>I',data,load+4)[0],0x0C000000+offset)
            allowed.update(range(offset,offset+width*8))
        self.assertEqual(len(data),len(old))
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,data)) if i not in allowed))

    def test_installed_credit_rejects_changed_readers_and_pending_assets(self):
        info=command_info(by_vrom(self.native)[CODE_VROM].extract(self.native))
        for rom,report,replaced in ((self.image,self.report,12),(self.base,self.prior,0)):
            ledger=CounterLedger(info);measure_text(ledger,self.native,rom,report)
            self.assertEqual(ledger.summary()['total_source_characters'],12)
            self.assertEqual(ledger.summary()['replaced_source_characters'],replaced)
        with self.assertRaises(ValueError):measure_text(CounterLedger(info),self.native,self.base,self.report)
        bad=dict(self.report);bad['controller_pak_artwork']={}
        # A missing profile cannot claim any installed credit.
        ledger=CounterLedger(info);measure_text(ledger,self.native,self.image,bad)
        self.assertEqual(ledger.summary()['replaced_source_characters'],0)
        with self.assertRaises(ValueError):patch_asset(self.native[:-1])

    def test_complete_cartridge_retains_all_code_fonts_birthdays_and_prior_artwork(self):
        image,patch,report=build(self.native,self.base,self.prior)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,patch),image)
        old,new=by_vrom(self.base),by_vrom(image);self.assertEqual(set(old),set(new))
        for v,entry in old.items():
            self.assertEqual((entry.index,entry.size),(new[v].index,new[v].size))
            if v not in (ASSET,0x19D40):self.assertEqual(entry.extract(self.base),new[v].extract(image))
        self.assertEqual(old[OWNER].extract(self.base),new[OWNER].extract(image))


if __name__=='__main__':unittest.main()
