"""Bound the complete GC fortune-table model without changing its native event."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_VROM,apply_ups
from textcodec import command_info
from translation_progress import CounterLedger
from nookington_details import measure_text as measure_nookington
from dump_artwork import measure_text as measure_dump
from fishing_artwork import measure_text as measure_fishing
from title_assets import DATA_BASE,rgb5a3,untile
from texture_preview import rgba5551
import fortune_booth_artwork as booth


@unittest.skipUnless((ROOT/'build/fortune-booth-artwork-01/build.json').is_file(),'Local fortune-booth candidate required')
class FortuneBoothArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/fishing-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/fishing-artwork-01/build.json').read_text())
        cls.image=(ROOT/'build/fortune-booth-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/fortune-booth-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        obj=by_vrom(cls.image)[booth.NEW_OBJECT].extract(cls.image)
        cls.compiled={'entry':obj[booth.ENTRY:booth.PACK],'model':obj[booth.MODEL:booth.MODEL+416]}

    def test_independent_native_commands_colours_pixels_and_vertices(self):
        with tempfile.TemporaryDirectory(prefix='af-mikuji-gbi-',dir=ROOT/'build') as directory:
            self.assertEqual(booth.commands(Path(directory)),self.compiled)
        data,profile=booth.package(self.native,self.rel,self.symbols,self.compiled)
        self.assertEqual(len(data),3856);self.assertEqual(profile['triangle_count'],30)
        for at,dst in ((0x53DBC0,0),(0x53DBA0,32)):
            for i in range(16):
                old=rgb5a3(struct.unpack_from('>H',self.rel,DATA_BASE+at+i*2)[0])
                new=rgba5551(struct.unpack_from('>H',data,dst+i*2)[0])
                self.assertEqual(old[3],new[3])
                if old[3]:self.assertEqual(old,new)
        for at,dst,w,h in ((0x53DDE0,64,64,64),(0x53DBE0,2112,32,32)):
            expected=untile(self.rel[DATA_BASE+at:DATA_BASE+at+w*h//2],w,h,4)
            actual=[n for b in data[dst:dst+w*h//2] for n in (b>>4,b&15)]
            self.assertEqual(actual,list(expected))
        for i in range(51):
            old=self.rel[DATA_BASE+0x53E5E0+i*16:DATA_BASE+0x53E5E0+(i+1)*16]
            self.assertEqual(data[2624+i*16:2624+(i+1)*16],old[:6]+b'\0\0'+old[8:])
        commands=list(struct.iter_unpack('>II',self.compiled['model']))
        pointers=[(a,b&0xFFFFFF) for a,b in commands if a>>24 in (0xFD,0x01)]
        self.assertEqual(pointers,[(0xFD100000,0x223A8),(0xFD500000,0x223E8),
            (0x0101B036,0x22DE8),(0xFD100000,0x223C8),(0xFD500000,0x22BE8),(0x01018030,0x22F98)])
        self.assertTrue(all(b>>24==6 for a,b in commands if a>>24 in (0xFD,0x01)))
        self.assertEqual(commands[-1],(0xDF000000,0))
        packed=self.rel[DATA_BASE+0x53E958:DATA_BASE+0x53E980]
        self.assertEqual(booth.packed_triangles(packed,27),booth.TRIANGLES[0])
        with self.assertRaises(ValueError):booth.packed_triangles(packed,26)
        with self.assertRaises(ValueError):booth.packed_triangles(packed[:-8],27)
        broken=bytearray(packed);broken[-8]|=0x80
        with self.assertRaises(ValueError):booth.packed_triangles(broken,27)
        with self.assertRaises(ValueError):booth.convert_palette(struct.pack('>16H',*[0x1111]*16))

    def test_exact_single_artwork_credit_and_prior_profiles(self):
        info=command_info(by_vrom(self.native)[CODE_VROM].extract(self.native))
        for image,report,credit in ((self.base,self.prior,0),(self.image,self.report,4)):
            ledger=CounterLedger(info);booth.measure_text(ledger,self.native,image,report)
            self.assertEqual(ledger.summary()['total_source_characters'],4)
            self.assertEqual(ledger.summary()['replaced_source_characters'],credit)
            self.assertEqual(len(ledger.rows),1)
            if credit:self.assertTrue(ledger.rows['art_fortune_booth:label']['replacements'][0]['intentional_gc_artwork_omission'])
        ledger=CounterLedger(info)
        for measure in (measure_nookington,measure_dump,measure_fishing):measure(ledger,self.native,self.image,self.report)
        self.assertEqual(ledger.summary()['replaced_source_characters'],28)
        with self.assertRaises(ValueError):booth.measure_text(CounterLedger(info),self.native,self.base,self.report)

    def test_complete_cartridge_only_changes_root_and_bounded_package(self):
        image,ups,report=booth.build(self.native,self.base,self.prior,self.rel,self.symbols,self.compiled)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,ups),image)
        self.assertEqual(report['fortune_booth_artwork']['building_ranges_checked'],92)
        before,after=by_vrom(self.base),by_vrom(image);self.assertEqual(set(before),set(after))
        for v,entry in before.items():
            self.assertEqual((entry.index,entry.size),(after[v].index,after[v].size))
            old,new=entry.extract(self.base),after[v].extract(image)
            if v in (booth.OBJECT,booth.NEW_OBJECT):
                self.assertEqual(old[:booth.ENTRY],new[:booth.ENTRY])
                self.assertEqual(old[0x232B8:],new[0x232B8:])
            elif v!=0x19D40:self.assertEqual(old,new,f'{v:08X}')


if __name__=='__main__':unittest.main()
