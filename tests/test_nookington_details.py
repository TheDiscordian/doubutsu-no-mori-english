"""Complete banner lettering, actual streamed copies, and unrelated resource retention."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups,CODE_VROM,sha256
from font import FONT_VROM,ATLAS_OFFSET,ATLAS_SIZE,pixels,get_glyph
from title_assets import DATA_BASE,untile
from textcodec import command_info
from translation_progress import CounterLedger
import nookington_details as details


@unittest.skipUnless((ROOT/'build/nookington-details-01/build.json').is_file(),'Local Nookington detail candidate required')
class NookingtonDetailsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/gyroid-service-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/gyroid-service-01/build.json').read_text())
        cls.image=(ROOT/'build/nookington-details-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/nookington-details-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_all_letters_donor_pixels_and_unchanged_red_offer_in_both_seasons(self):
        files=by_vrom(self.base);font=files[FONT_VROM].extract(self.base)
        converted,profile=details.textures(self.native,font,self.rel,self.symbols)
        atlas=pixels(font[ATLAS_OFFSET:ATLAS_OFFSET+ATLAS_SIZE]);columns=[]
        for i,ch in enumerate('CLEARANCE'):
            glyph=get_glyph(atlas,ord(ch));ink=[x for x in range(12) if any(row[x] for row in glyph)]
            if i:columns.append([0]*16)
            columns.extend([[row[x] for row in glyph] for x in range(min(ink),max(ink)+1)])
        self.assertEqual(len(columns),53)
        donor=untile(self.rel[DATA_BASE+0x58C7C0:DATA_BASE+0x58CFC0],128,32,4)
        original=details.source(self.native)
        for data,row,(_,old,*_) in zip(converted,profile['textures'],details.SEASONS):
            before=pixels(original[old+details.TEXTURE:old+details.TEXTURE+2048]);after=pixels(data)
            for v in range(32):
                for u in range(128):
                    if 29<=u<38 and 3<=v<29:self.assertEqual(after[v*128+u],donor[v*128+u])
                    elif 73<=u<127 and 17<=v<30:
                        x,y=126-u,v-17
                        alpha=columns[x][y+2] if x<53 and y<12 else 0
                        self.assertEqual(after[v*128+u],row['intensity_palette_indices'][alpha])
                    else:self.assertEqual(after[v*128+u],before[v*128+u])
            self.assertNotEqual(after,before)
        for key in ('geometry_changed','palettes_changed','cpu_code_changed','allocation_changed','saved_formats_changed'):
            self.assertFalse(profile[key])
        self.assertEqual(set(profile['donor_bindings']),{'0058C5FC','0058EBFC','0058C61C','0058EC1C'})
        with self.assertRaises(ValueError):details.textures(self.native,font[:-1],self.rel,self.symbols)

    def test_installed_and_pending_source_weights_require_actual_readers(self):
        info=command_info(by_vrom(self.native)[CODE_VROM].extract(self.native))
        for image,report,credit in ((self.image,self.report,12),(self.base,self.prior,0)):
            ledger=CounterLedger(info);details.measure_text(ledger,self.native,image,report)
            self.assertEqual(ledger.summary()['total_source_characters'],12)
            self.assertEqual(ledger.summary()['replaced_source_characters'],credit)
            self.assertEqual(set(ledger.rows),{'art_nookington_clearance:summer','art_nookington_clearance:winter'})
        with self.assertRaises(ValueError):details.measure_text(CounterLedger(info),self.native,self.base,self.report)
        with patch.dict(details.READERS,{details.TABLE:'0'*64}),self.assertRaises(ValueError):
            details.measure_text(CounterLedger(info),self.native,self.image,self.report)

    def test_complete_cartridge_preserves_every_other_resource_and_all_streamed_bounds(self):
        image,ups,report=details.build(self.native,self.base,self.prior,self.rel,self.symbols)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,ups),image)
        self.assertEqual(report['nookington_details']['building_ranges_checked'],92)
        old,new=by_vrom(self.base),by_vrom(image);self.assertEqual(set(old),set(new))
        allowed={details.OBJECT:set(),details.NEW_OBJECT:set()}
        for _,original,streamed,*_ in details.SEASONS:
            for resource,offset in ((details.OBJECT,original),(details.NEW_OBJECT,original),(details.NEW_OBJECT,streamed)):
                allowed[resource].update(range(offset+details.TEXTURE,offset+details.TEXTURE+2048))
        for v,entry in old.items():
            self.assertEqual((entry.index,entry.size),(new[v].index,new[v].size))
            before,after=entry.extract(self.base),new[v].extract(image)
            if v in allowed:self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(before,after)) if i not in allowed[v]))
            elif v!=0x19D40:self.assertEqual(before,after,f'{v:08X}')
        expanded=new[details.NEW_OBJECT].extract(image)
        self.assertEqual(report['nookington_sign']['object_sha256'],sha256(expanded))
        for row,(_,_,offset,*_) in zip(report['nookington_sign']['seasons'],details.SEASONS):
            self.assertEqual(row['sha256'],sha256(expanded[offset:offset+details.NEW_SIZE]))


if __name__=='__main__':unittest.main()
