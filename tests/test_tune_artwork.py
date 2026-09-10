"""Full English tune labels without changing the native controls or stored notes."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups
from tune_artwork import ROWS,OKAY,OKAY_LOAD,VROM,commands,patch_assets,build
from texture_preview import decode
from title_assets import DATA_BASE


@unittest.skipUnless((ROOT/'build/tune-artwork-01/build.json').is_file(),'Local town-tune artwork required')
class TuneArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/notice-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/notice-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.image=(ROOT/'build/tune-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/tune-artwork-01/build.json').read_text())
        cls.compiled={'okay':(ROOT/'build/tune-artwork-commands/okay.bin').read_bytes()}

    def test_complete_pixels_alpha_and_retained_control_icons_geometry(self):
        data,profile=patch_assets(self.native,self.rel,self.symbols,self.compiled)
        self.assertEqual(profile,self.report['tune_artwork'])
        old=by_vrom(self.native)[VROM].extract(self.native)
        allowed=set(range(0x43C8,0x45C8))|set(range(0x4118,0x4150))|set(range(0x3650,0x3690))
        for name,donor,target,load,quad in ROWS:
            self.assertEqual(decode(data[target:target+1024],64,16,'ia8'),
                decode(self.rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+1024],64,16,'ia8',gamecube=True))
            self.assertEqual(data[load:load+72],old[load:load+72])
            self.assertEqual(data[quad:quad+64],old[quad:quad+64])
            allowed.update(range(target,target+1024))
        self.assertEqual(decode(data[0x43C8:0x44C8],32,16,'i4'),
            decode(self.rel[DATA_BASE+OKAY.gc:DATA_BASE+OKAY.gc+256],32,16,'i4',gamecube=True))
        self.assertEqual(data[0x44C8:0x45C8],bytes(256))
        self.assertEqual(data[0x4118:0x4150],OKAY_LOAD)
        for at in range(0x3650,0x3690,16):
            a=struct.unpack_from('>3hH2h4B',old,at);b=struct.unpack_from('>3hH2h4B',data,at)
            self.assertEqual(b[0],90 if a[0]==75 else 120)
            self.assertEqual(b[4],a[4]//2)
            self.assertEqual((a[1:4],a[5:]),(b[1:4],b[5:]))
        self.assertEqual(len(data),len(old))
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,data)) if i not in allowed))

    def test_independent_compiled_load_and_rejected_sources(self):
        with tempfile.TemporaryDirectory(prefix='af-tune-artwork-') as directory:
            self.assertEqual(commands(Path(directory)),self.compiled)
        for rel,symbols in ((self.rel[:-1],self.symbols),(self.rel,self.symbols+b'\n')):
            with self.assertRaises(ValueError):patch_assets(self.native,rel,symbols,self.compiled)
        with self.assertRaises(ValueError):patch_assets(self.native,self.rel,self.symbols,{'okay':bytes(56)})

    def test_complete_cartridge_prior_notice_and_corrected_grid_retained(self):
        image,patch,report=build(self.native,self.base,self.prior,self.rel,self.symbols,self.compiled)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,patch),image)
        old,new=by_vrom(self.base),by_vrom(image)
        self.assertEqual(set(old),set(new));self.assertEqual(len(image),len(self.base))
        for address,entry in old.items():
            self.assertEqual((entry.index,entry.size),(new[address].index,new[address].size))
            if address not in (VROM,0x19D40):self.assertEqual(entry.extract(self.base),new[address].extract(image))
        from keyboard_grid_overlay import verify_owned_parts
        verify_owned_parts(image,self.native,report['keyboard_grid'],report['apology_input'])


if __name__=='__main__':unittest.main()
