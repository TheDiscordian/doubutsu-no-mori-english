"""English-GC fishing omissions preserve all remaining geometry and native event code."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_VROM,apply_ups
from texture_preview import native_range
from textcodec import command_info
from translation_progress import CounterLedger
from nookington_details import measure_text as measure_nookington
from dump_artwork import measure_text as measure_dump
from police_artwork import native_triangles
import fishing_artwork as fish


@unittest.skipUnless((ROOT/'build/fishing-artwork-01/build.json').is_file(),'Local fishing artwork candidate required')
class FishingArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/dump-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/dump-artwork-01/build.json').read_text())
        cls.image=(ROOT/'build/fishing-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/fishing-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_independent_noop_compilation_and_exact_six_retained_triangles(self):
        with tempfile.TemporaryDirectory(prefix='af-fishing-gbi-',dir=ROOT/'build') as directory:
            self.assertEqual(fish.commands(Path(directory)),fish.NOOP)
        changes,profile=fish.changes(self.native,self.rel,self.symbols,fish.NOOP)
        self.assertEqual(len(changes),6);self.assertEqual(len(profile['donor_texture_pointers']),4)
        self.assertEqual(len(profile['donor_vertex_pointers']),2)
        files=by_vrom(self.image);old=by_vrom(self.native)[fish.OBJECT].extract(self.native)
        for row in fish.ROWS:
            vtx,tri=row[7:9]
            for owner in (fish.OBJECT,fish.NEW_OBJECT):
                current=files[owner].extract(self.image)
                self.assertEqual(current[vtx:vtx+320],old[vtx:vtx+320])
                self.assertEqual(current[tri-8:tri],struct.pack('>II',0x01014028,0x6000000+vtx))
                self.assertEqual(current[tri+16:tri+24],fish.NOOP)
                actual=native_triangles(current[tri:tri+32])
                self.assertEqual(actual,[(0,1,2),(3,4,5),(6,7,8),(9,10,11),(16,17,18),(16,18,19)])
                self.assertFalse(set(range(12,16)) & {v for t in actual for v in t})
            self.assertEqual(changes[tri+16],fish.NOOP)
        with self.assertRaises(ValueError):fish.changes(self.native,self.rel,self.symbols,bytes(8))

    def test_exact_omission_credit_and_prior_building_profiles(self):
        info=command_info(by_vrom(self.native)[CODE_VROM].extract(self.native))
        for image,report,credit in ((self.base,self.prior,0),(self.image,self.report,8)):
            ledger=CounterLedger(info);fish.measure_text(ledger,self.native,image,report)
            self.assertEqual(ledger.summary()['total_source_characters'],8)
            self.assertEqual(ledger.summary()['replaced_source_characters'],credit)
            self.assertEqual(len(ledger.rows),4)
            if credit:
                self.assertTrue(all(row['replacements'][0]['intentional_gc_artwork_omission'] for row in ledger.rows.values()))
        ledger=CounterLedger(info);measure_nookington(ledger,self.native,self.image,self.report)
        measure_dump(ledger,self.native,self.image,self.report)
        self.assertEqual(ledger.summary()['replaced_source_characters'],20)
        with self.assertRaises(ValueError):fish.measure_text(CounterLedger(info),self.native,self.base,self.report)

    def test_complete_cartridge_changes_only_four_atlases_and_two_draw_commands(self):
        image,ups,report=fish.build(self.native,self.base,self.prior,self.rel,self.symbols,fish.NOOP)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,ups),image)
        self.assertEqual(report['fishing_artwork']['building_ranges_checked'],92)
        changes,_=fish.changes(self.native,self.rel,self.symbols,fish.NOOP)
        old,new=by_vrom(self.base),by_vrom(image);self.assertEqual(set(old),set(new))
        allowed={i for at,data in changes.items() for i in range(at,at+len(data))}
        for v,entry in old.items():
            self.assertEqual((entry.index,entry.size),(new[v].index,new[v].size))
            before,after=entry.extract(self.base),new[v].extract(image)
            if v in (fish.OBJECT,fish.NEW_OBJECT):
                self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(before,after)) if i not in allowed))
            elif v!=0x19D40:self.assertEqual(before,after,f'{v:08X}')
        for row in fish.ROWS:
            for i in (5,6):self.assertEqual(native_range(image,row[i],2048),native_range(image,fish.NEW_OBJECT+row[i]-fish.OBJECT,2048))


if __name__=='__main__':unittest.main()
