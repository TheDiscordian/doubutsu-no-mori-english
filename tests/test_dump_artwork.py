"""Exact GC dump images, installed seasonal readers, and whole-cartridge retention."""
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_VROM,apply_ups
from title_assets import DATA_BASE,untile,pack4
from texture_preview import native_range
from textcodec import command_info
from translation_progress import CounterLedger
from nookington_details import measure_text as measure_nookington
import dump_artwork as dump


@unittest.skipUnless((ROOT/'build/dump-artwork-01/build.json').is_file(),'Local dump artwork candidate required')
class DumpArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/nookington-details-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/nookington-details-01/build.json').read_text())
        cls.image=(ROOT/'build/dump-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/dump-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_complete_source_pixels_palettes_and_native_readers(self):
        textures,profile=dump.assets(self.native,self.rel,self.symbols)
        for row,evidence in zip(dump.ROWS,profile['textures']):
            expected=pack4(untile(self.rel[DATA_BASE+row.gc:DATA_BASE+row.gc+2048],128,32,4))
            self.assertEqual(textures[row.native],expected)
            for owner in (dump.OBJECT,dump.NEW_OBJECT):
                self.assertEqual(native_range(self.image,owner+row.native-dump.OBJECT,2048),expected)
            self.assertEqual(evidence['matched_vertex_uses'],44)
            self.assertEqual(native_range(self.image,row.native_palette,32),native_range(self.native,row.native_palette,32))
        self.assertEqual(len(profile['donor_texture_pointers']),2)
        for key in ('geometry_changed','palettes_changed','code_changed','allocation_changed',
                    'saved_formats_changed','collection_schedule_changed'):
            self.assertFalse(profile[key])
        dump.verify_readers(self.native,self.image)
        with self.assertRaises(ValueError):dump.assets(self.native,self.rel[:-1],self.symbols)

    def test_old_and_current_credit_and_retained_nookington_profile(self):
        info=command_info(by_vrom(self.native)[CODE_VROM].extract(self.native))
        for image,report,credit in ((self.base,self.prior,0),(self.image,self.report,8)):
            ledger=CounterLedger(info);dump.measure_text(ledger,self.native,image,report)
            self.assertEqual(ledger.summary()['total_source_characters'],8)
            self.assertEqual(ledger.summary()['replaced_source_characters'],credit)
        ledger=CounterLedger(info);measure_nookington(ledger,self.native,self.image,self.report)
        self.assertEqual(ledger.summary()['replaced_source_characters'],12)
        with self.assertRaises(ValueError):dump.measure_text(CounterLedger(info),self.native,self.base,self.report)
        with patch.dict(dump.READERS,{dump.TABLE:'0'*64}),self.assertRaises(ValueError):
            dump.measure_text(CounterLedger(info),self.native,self.image,self.report)

    def test_bitmap_kanji_count_uses_actual_transcription_not_a_fabricated_font_encoding(self):
        info=command_info(by_vrom(self.native)[CODE_VROM].extract(self.native))
        ledger=CounterLedger(info);source=native_range(self.native,dump.ROWS[0].native,2048)
        ledger.add_transcribed_artwork('bitmap','ゴミ\n月木',source)
        self.assertEqual(ledger.summary()['total_source_characters'],4)
        ledger.credit('bitmap',b'Dump','test')
        self.assertEqual(ledger.summary()['replaced_source_characters'],4)
        with self.assertRaises(ValueError):ledger.add_transcribed_artwork('bitmap','ゴミ',source)
        for text,pixels in (('Dump',source),('月',b''),('月\x00',source)):
            with self.assertRaises(ValueError):CounterLedger(info).add_transcribed_artwork('bad',text,pixels)

    def test_complete_build_patch_and_all_other_building_resources(self):
        image,ups,report=dump.build(self.native,self.base,self.prior,self.rel,self.symbols)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,ups),image)
        self.assertEqual(report['dump_artwork']['building_ranges_checked'],92)
        old,new=by_vrom(self.base),by_vrom(image);self.assertEqual(set(old),set(new))
        allowed={i for row in dump.ROWS for i in range(row.native-dump.OBJECT,row.native-dump.OBJECT+2048)}
        for v,entry in old.items():
            self.assertEqual((entry.index,entry.size),(new[v].index,new[v].size))
            before,after=entry.extract(self.base),new[v].extract(image)
            if v in (dump.OBJECT,dump.NEW_OBJECT):
                self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(before,after)) if i not in allowed))
            elif v!=0x19D40:self.assertEqual(before,after,f'{v:08X}')


if __name__=='__main__':unittest.main()
