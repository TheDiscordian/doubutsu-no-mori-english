"""Bounded shared GC stall graphics and reflected matrix/culling restoration."""
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
from fortune_booth_artwork import measure_text as measure_booth
from countdown_artwork import measure_text as measure_countdown
from stall_model_source import source,faces,reflected,TEXTURES
from title_assets import DATA_BASE
from texture_preview import decode
import stall_artwork as stall


@unittest.skipUnless((ROOT/'build/stall-artwork-01/build.json').is_file(),'Local shared stall candidate required')
class StallArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/countdown-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/countdown-artwork-01/build.json').read_text())
        cls.image=(ROOT/'build/stall-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/stall-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.obj=by_vrom(cls.image)[stall.NEW_OBJECT].extract(cls.image)
        cls.compiled={name:cls.obj[at:at+size] for name,at,size in
            (('left',stall.LEFT,56),('right',stall.RIGHT,56),('model',stall.MODEL,1392))}

    def trace(self,entry,mirror):
        state={'mode':0,'depth':0,'texture':None,'loaded':[]};result=[];steps=0
        reverse={value:key for key,value in stall.TEXTURE_OFFSETS.items()}
        def visit(at):
            nonlocal steps
            for i in range(200):
                steps+=1;self.assertLess(steps,200)
                a,b=struct.unpack_from('>II',self.obj,at+i*8);op=a>>24
                if op==0xDA:
                    self.assertEqual((a,b),(0xDA380000,0x6000000+stall.MATRIX));self.assertEqual(state['depth'],0)
                    state['depth']=1
                    high,low=struct.unpack_from('>16h',self.obj,stall.MATRIX),struct.unpack_from('>16H',self.obj,stall.MATRIX+32)
                    self.assertEqual(high,(-1,0,0,0,0,1,0,0,0,0,1,0,0,0,0,1));self.assertEqual(low,(0,)*16)
                elif op==0xD8:
                    self.assertEqual((a,b),(0xD8380002,64));self.assertEqual(state['depth'],1);state['depth']=0
                elif op==0xD9:state['mode']=(state['mode']&(a&0xFFFFFF))|b
                elif op==0xDE:
                    self.assertEqual((a,b),(0xDE000000,0x6000000+stall.MODEL));visit(b&0xFFFFFF)
                elif op==0xDF:return
                elif op==0xFD and a==0xFD500000:
                    self.assertEqual(b>>24,6);state['texture']=reverse[b&0xFFFFFF]
                elif op==1:
                    self.assertEqual(b>>24,6);count=(a>>12)&255;start=b&0xFFFFFF
                    self.assertEqual((a&255)//2,count);self.assertTrue(1<=count<=32)
                    self.assertGreaterEqual(start,stall.VERTEX_DATA);self.assertLessEqual(start+count*16,stall.MODEL)
                    state['loaded']=[self.obj[start+j*16:start+(j+1)*16] for j in range(count)]
                elif op in (5,6):
                    self.assertEqual(state['depth'],int(mirror))
                    self.assertEqual(state['mode']&0x600,0x200 if mirror else 0x400)
                    lit=bool(state['mode']&0x20000)
                    for word in ((a,b) if op==6 else (a,)):
                        indices=[word>>shift&127 for shift in (17,9,1)]
                        self.assertTrue(all(i<len(state['loaded']) for i in indices))
                        vs=[state['loaded'][i] for i in indices]
                        if mirror:vs=[reflected(v,lit) for v in vs][::-1]
                        result.append((state['texture'],lit,vs))
            self.fail('Unterminated native stall list')
        visit(entry);self.assertEqual(state['depth'],0);self.assertEqual(state['mode']&0x600,0x400)
        return result

    def test_independent_compilation_and_all_native_triangles_with_balanced_reflection(self):
        with tempfile.TemporaryDirectory(prefix='af-stall-gbi-',dir=ROOT/'build') as directory:
            compiled,profile=stall.compile_model(self.rel,self.symbols,Path(directory)/'out')
            self.assertEqual(compiled,self.compiled);self.assertEqual(profile['model_bytes'],1392)
        models,_=source(self.rel,self.symbols)
        for entry,mirror in ((stall.LEFT,False),(stall.RIGHT,True)):
            expected=[(material,lit,[v[:6]+b'\0\0'+v[8:] for v in vs]) for material,lit,vs in faces(models[0],mirror)]
            self.assertEqual(self.trace(entry,mirror),expected);self.assertEqual(len(expected),133)
        self.assertFalse(self.report['stall_artwork']['source_right_mesh_exact'])
        with self.assertRaises(ValueError):stall.assets(self.native,self.rel,self.symbols,{**self.compiled,'right':bytes(56)})

    def test_all_source_pixels_colours_and_prior_translation_profiles(self):
        for at,pal in ((0x5B9CC0,0x5B8FA0),(0x5B8FC0,0x5B8F60),(0x5B93C0,0x5B8F80),(0x5B9BC0,0x5B8F60)):
            w,h=TEXTURES[at];dest=stall.TEXTURE_OFFSETS[at];pdest=stall.PALETTE_OFFSETS[pal]
            a=decode(self.obj[dest:dest+w*h//2],w,h,'ci4',self.obj[pdest:pdest+32])
            b=decode(self.rel[DATA_BASE+at:DATA_BASE+at+w*h//2],w,h,'ci4',self.rel[DATA_BASE+pal:DATA_BASE+pal+32],gamecube=True)
            for i in range(0,len(a),4):
                self.assertEqual(a[i+3],b[i+3])
                if a[i+3]:self.assertEqual(a[i:i+4],b[i:i+4])
        ledger=CounterLedger(command_info(by_vrom(self.native)[CODE_VROM].extract(self.native)))
        for measure in (measure_nookington,measure_dump,measure_fishing,measure_booth,measure_countdown):
            measure(ledger,self.native,self.image,self.report)
        self.assertEqual(ledger.summary()['replaced_source_characters'],39)
        stall.verify_current(self.native,self.image,self.report)
        with self.assertRaises(ValueError):stall.verify_current(self.native,self.base,self.report)

    def test_complete_cartridge_and_patch_preserve_everything_outside_the_stall(self):
        image,ups,report=stall.build(self.native,self.base,self.prior,self.rel,self.symbols,self.compiled)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report);self.assertEqual(apply_ups(self.native,ups),image)
        self.assertEqual(report['stall_artwork']['building_ranges_checked'],92)
        before,after=by_vrom(self.base),by_vrom(image);self.assertEqual(set(before),set(after))
        for v,entry in before.items():
            self.assertEqual((entry.index,entry.size),(after[v].index,after[v].size))
            old,new=entry.extract(self.base),after[v].extract(image)
            if v in (stall.OBJECT,stall.NEW_OBJECT):
                self.assertEqual(old[:stall.START],new[:stall.START]);self.assertEqual(old[stall.END:],new[stall.END:])
            elif v!=0x19D40:self.assertEqual(old,new,f'{v:08X}')


if __name__=='__main__':unittest.main()
