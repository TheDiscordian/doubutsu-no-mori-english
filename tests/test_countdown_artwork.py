"""Exact English countdown artwork retains timer code, digits, and animation."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_VROM,apply_ups
from textcodec import command_info
from translation_progress import CounterLedger
from nookington_details import measure_text as measure_nookington
from dump_artwork import measure_text as measure_dump
from fishing_artwork import measure_text as measure_fishing
from fortune_booth_artwork import measure_text as measure_booth
from texture_preview import native_range,decode
from title_assets import DATA_BASE
import countdown_artwork as count


@unittest.skipUnless((ROOT/'build/countdown-artwork-01/build.json').is_file(),'Local countdown candidate required')
class CountdownArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/fortune-booth-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/fortune-booth-artwork-01/build.json').read_text())
        cls.image=(ROOT/'build/countdown-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/countdown-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_exact_source_colours_pixels_bindings_and_native_uv_readers(self):
        converted,profile=count.assets(self.native,self.rel,self.symbols)
        self.assertEqual(len(profile['donor_pointers']),6)
        for row,details in zip(count.ROWS,profile['textures']):
            native=decode(converted[row.native],128,32,'ci4',native_range(self.native,row.native_palette,32))
            source=decode(self.rel[DATA_BASE+row.gc:DATA_BASE+row.gc+2048],128,32,'ci4',
                self.rel[DATA_BASE+row.gc_palette:DATA_BASE+row.gc_palette+32],gamecube=True)
            for i in range(0,len(native),4):
                self.assertEqual(native[i+3],source[i+3])
                if native[i+3]:self.assertEqual(native[i:i+4],source[i:i+4])
            self.assertEqual(details['matched_vertex_uses'],14)
            self.assertEqual(len(details['native_loads']),2)
        with self.assertRaises(ValueError):count.assets(self.native,self.rel,bytes(len(self.symbols)))

    def test_three_labels_share_seasonal_copies_and_prior_credit_is_retained(self):
        info=command_info(by_vrom(self.native)[CODE_VROM].extract(self.native))
        for image,report,replaced in ((self.base,self.prior,0),(self.image,self.report,7)):
            ledger=CounterLedger(info);count.measure_text(ledger,self.native,image,report)
            self.assertEqual(ledger.summary()['total_source_characters'],7)
            self.assertEqual(ledger.summary()['replaced_source_characters'],replaced)
            self.assertEqual(len(ledger.rows),3)
            if replaced:self.assertTrue(ledger.rows['art_countdown:prefix']['replacements'][0]['intentional_gc_artwork_omission'])
        ledger=CounterLedger(info)
        for measure in (measure_nookington,measure_dump,measure_fishing,measure_booth):measure(ledger,self.native,self.image,self.report)
        self.assertEqual(ledger.summary()['replaced_source_characters'],32)
        with self.assertRaises(ValueError):count.measure_text(CounterLedger(info),self.native,self.base,self.report)

    def test_full_cartridge_changes_only_two_atlases_and_recovers_from_patch(self):
        image,ups,report=count.build(self.native,self.base,self.prior,self.rel,self.symbols)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,ups),image)
        self.assertEqual(report['countdown_artwork']['building_ranges_checked'],92)
        before,after=by_vrom(self.base),by_vrom(image);self.assertEqual(set(before),set(after))
        for v,entry in before.items():
            self.assertEqual((entry.index,entry.size),(after[v].index,after[v].size))
            old,new=entry.extract(self.base),after[v].extract(image)
            if v in (count.OBJECT,count.NEW_OBJECT):
                self.assertEqual(old[:0x7A58],new[:0x7A58]);self.assertEqual(old[0x8A58:],new[0x8A58:])
                for row in count.ROWS:
                    at=row.native-count.OBJECT
                    self.assertEqual(new[at:at+2048],native_range(image,count.NEW_OBJECT+at,2048))
            elif v!=0x19D40:self.assertEqual(old,new,f'{v:08X}')


if __name__=='__main__':unittest.main()
