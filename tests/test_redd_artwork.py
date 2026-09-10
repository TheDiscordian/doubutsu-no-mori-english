"""Redd's English reds affect only previously unused summer palette entries."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from artwork_chain import rebuild
from redd_artwork import OBJECT,NEW_OBJECT,PALETTES,DONOR,patch_assets,build
from title_assets import DATA_BASE,untile,pack4
from texture_preview import decode


@unittest.skipUnless((ROOT/'build/police-artwork-01/build.json').is_file(),'Local source assets required')
class ReddArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/police-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/police-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.files=by_vrom(cls.base);cls.prior=cls.files[OBJECT].extract(cls.base)

    def test_complete_donor_pixels_exact_reds_and_unchanged_existing_summer_colours(self):
        changed,pals,report=patch_assets(self.native,self.prior,self.rel,self.symbols)
        old_pals=self.files[PALETTES].extract(self.base)
        donor=self.rel[DATA_BASE+DONOR.gc:DATA_BASE+DONOR.gc+2048]
        gc_pal=self.rel[DATA_BASE+DONOR.gc_palette:DATA_BASE+DONOR.gc_palette+32]
        self.assertEqual(changed[0x10C8:0x18C8],pack4(untile(donor,128,32,4)))
        native_rgba=decode(changed[0x10C8:0x18C8],128,32,'ci4',pals[0xA48:0xA68])
        gc_rgba=decode(donor,128,32,'ci4',gc_pal,gamecube=True)
        for i in range(0,len(native_rgba),4):
            self.assertEqual(native_rgba[i+3],gc_rgba[i+3])
            # Preserve native hidden RGB, as required by the palette contract.
            if native_rgba[i+3]:self.assertEqual(native_rgba[i:i+4],gc_rgba[i:i+4])
        self.assertEqual(changed[:0x10C8],self.prior[:0x10C8])
        self.assertEqual(changed[0x18C8:],self.prior[0x18C8:])
        self.assertEqual(pals[:0xA62],old_pals[:0xA62])
        self.assertEqual(pals[0xA66:],old_pals[0xA66:])
        self.assertEqual(pals[0xA62:0xA66],bytes.fromhex('E04181CF'))
        for at in (0x8C8,0x10C8):
            pixels=self.prior[at:at+2048]
            self.assertEqual(decode(pixels,128,32,'ci4',old_pals[0xA48:0xA68]),
                             decode(pixels,128,32,'ci4',pals[0xA48:0xA68]))
        self.assertEqual(report['matched_vertex_uses'],31)
        self.assertTrue(report['winter_retained'])

    def test_reject_unrelated_source_region_changes_and_unknown_artwork_ownership(self):
        for rel,symbols in ((self.rel[:-1],self.symbols),(self.rel,self.symbols+b'\n')):
            with self.assertRaises(ValueError):patch_assets(self.native,self.prior,rel,symbols)
        wrong=bytearray(self.prior);wrong[0x900]^=1
        with self.assertRaisesRegex(ValueError,'region changed'):
            patch_assets(self.native,bytes(wrong),self.rel,self.symbols)
        for changes in ({}, {0x1060:bytes(16)}, {0x3F00000:bytes(16)}, {OBJECT:self.prior[:-16]}):
            with self.assertRaises(ValueError):rebuild(self.native,self.base,self.report,changes)

    def test_whole_cartridge_streamed_colour_texture_and_previous_resources(self):
        before=copy.deepcopy(self.report)
        image,patch,report=build(self.native,self.base,self.report,self.rel,self.symbols)
        self.assertEqual(self.report,before)
        self.assertEqual(len(image),32*1024*1024)
        self.assertEqual(apply_ups(self.native,patch),image)
        files=by_vrom(image)
        self.assertEqual(set(files),set(self.files))
        self.assertEqual(files[NEW_OBJECT].extract(image)[:len(self.prior)],files[OBJECT].extract(image))
        self.assertEqual(files[NEW_OBJECT].extract(image)[len(self.prior):],
                         self.files[NEW_OBJECT].extract(self.base)[len(self.prior):])
        for v,entry in self.files.items():
            if v not in (OBJECT,NEW_OBJECT,PALETTES,0x19D40):
                self.assertEqual(files[v].extract(image),entry.extract(self.base),f'{v:08X}')
            self.assertEqual(files[v].index,entry.index)
            self.assertEqual(files[v].size,entry.size)
        for key,value in self.report.items():
            if key not in ('output_sha256','patch_sha256','replacement_files','release_status'):
                self.assertEqual(report[key],value,key)


if __name__=='__main__':unittest.main()
