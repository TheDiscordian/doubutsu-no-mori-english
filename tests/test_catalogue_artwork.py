"""Complete English catalogue labels, preserved arrows and prior cartridge data."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups
from catalogue_artwork import ROWS,VROM,commands,patch_assets,build,expected_load
from texture_preview import decode
from title_assets import DATA_BASE


@unittest.skipUnless((ROOT/'build/catalogue-artwork-01/build.json').is_file(),'Local catalogue artwork required')
class CatalogueArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/tune-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/tune-artwork-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.image=(ROOT/'build/catalogue-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/catalogue-artwork-01/build.json').read_text())
        cls.compiled={row[0]:(ROOT/'build/catalogue-artwork-commands'/f'{row[0]}.bin').read_bytes() for row in ROWS}

    def test_complete_pixels_alpha_and_native_geometry(self):
        data,profile=patch_assets(self.native,self.rel,self.symbols,self.compiled)
        self.assertEqual(profile,self.report['catalogue_artwork'])
        old=by_vrom(self.native)[VROM].extract(self.native);allowed=set()
        for name,donor,width,target,load,quad,left in ROWS:
            self.assertEqual(decode(data[target:target+width*16],width,16,'ia8'),
                decode(self.rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+width*16],width,16,'ia8',gamecube=True))
            self.assertEqual(data[target+width*16:target+1024],bytes(1024-width*16))
            self.assertEqual(data[load:load+56],expected_load(target,width,True))
            for at in range(quad,quad+64,16):
                a=struct.unpack_from('>3hH2h4B',old,at);b=struct.unpack_from('>3hH2h4B',data,at)
                self.assertEqual(b[0],left+(a[0]-left)*width//64)
                self.assertEqual(b[4],a[4]*width//64)
                self.assertEqual((a[1:4],a[5:]),(b[1:4],b[5:]))
            allowed.update(range(target,target+1024));allowed.update(range(load,load+56))
            allowed.update(range(quad,quad+64))
        self.assertEqual(data[0x540:0x5C0],old[0x540:0x5C0])
        self.assertEqual(data[0x7B8:0x9B8],old[0x7B8:0x9B8])
        self.assertEqual(len(data),len(old))
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,data)) if i not in allowed))

    def test_independent_compiled_commands_and_source_rejection(self):
        with tempfile.TemporaryDirectory(prefix='af-catalogue-artwork-') as directory:
            self.assertEqual(commands(Path(directory)),self.compiled)
        for rel,symbols in ((self.rel[:-1],self.symbols),(self.rel,self.symbols+b'\n')):
            with self.assertRaises(ValueError):patch_assets(self.native,rel,symbols,self.compiled)
        bad=dict(self.compiled);bad['top']=bytes(56)
        with self.assertRaises(ValueError):patch_assets(self.native,self.rel,self.symbols,bad)

    def test_complete_cartridge_and_all_previous_artwork_retained(self):
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
