"""Complete donor labels within the native notice window's original allocation."""
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from notice_artwork import ROWS,VROM,NATIVE_SHA,commands,patch_assets,build,expected_load,QUAD_LEFT
from texture_preview import decode
from title_assets import DATA_BASE


@unittest.skipUnless((ROOT/'build/notice-artwork-01/build.json').is_file(),'Local bulletin-board artwork required')
class NoticeArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/keyboard-grid-cursor-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/keyboard-grid-cursor-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.image=(ROOT/'build/notice-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/notice-artwork-01/build.json').read_text())
        cls.compiled={row[0]:(ROOT/'build/notice-artwork-commands'/f'{row[0]}.bin').read_bytes() for row in ROWS}

    def test_full_pixels_alpha_and_bounded_native_control_layout(self):
        data,profile=patch_assets(self.native,self.rel,self.symbols,self.compiled)
        self.assertEqual(profile,self.report['notice_artwork'])
        old=by_vrom(self.native)[VROM].extract(self.native)
        allowed=set(range(0x858,0x1858))
        for name,donor,width,_,target,load,quad,index in ROWS:
            source=self.rel[DATA_BASE+donor.gc:DATA_BASE+donor.gc+width*16]
            installed=data[target:target+width*16]
            self.assertEqual(decode(installed,width,16,'ia8'),decode(source,width,16,'ia8',gamecube=True))
            self.assertEqual(data[load:load+56],expected_load(target,width,True))
            before=list(struct.iter_unpack('>3hH2h4B',old[quad:quad+64]))
            after=list(struct.iter_unpack('>3hH2h4B',data[quad:quad+64]))
            self.assertEqual({v[0] for v in after},{QUAD_LEFT[name],QUAD_LEFT[name]+width*7//8})
            self.assertEqual({v[4] for v in after},{0,width*32})
            self.assertEqual({v[5] for v in after},{0,512})
            for a,b in zip(before,after):self.assertEqual((a[1:4],a[6:]),(b[1:4],b[6:]))
            allowed.update(range(load,load+56));allowed.update(range(quad,quad+64))
        self.assertEqual(data[0x1358:0x1458],bytes(256))
        for quad,left in ((0x180,-142),(0x140,-27)):
            for at in range(quad,quad+64,16):
                self.assertEqual(data[at+2:at+16],old[at+2:at+16])
                self.assertIn(struct.unpack_from('>h',data,at)[0],(left,left+14))
            allowed.update(range(quad,quad+64))
        self.assertEqual(len(data),52896)
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(old,data)) if i not in allowed))

    def test_independent_native_gbi_and_reject_unknown_sources_commands(self):
        with tempfile.TemporaryDirectory(prefix='af-notice-artwork-') as directory:
            self.assertEqual(commands(Path(directory)),self.compiled)
        for rel,symbols in ((self.rel[:-1],self.symbols),(self.rel,self.symbols+b'\n')):
            with self.assertRaises(ValueError):patch_assets(self.native,rel,symbols,self.compiled)
        bad=dict(self.compiled);bad['latest']=bytes(56)
        with self.assertRaises(ValueError):patch_assets(self.native,self.rel,self.symbols,bad)

    def test_complete_resource_and_current_grid_retention_with_patch_recovery(self):
        image,patch,report=build(self.native,self.base,self.prior,self.rel,self.symbols,self.compiled)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,patch),image)
        old,new=by_vrom(self.base),by_vrom(image)
        self.assertEqual(len(image),len(self.base));self.assertEqual(set(old),set(new))
        for address,entry in old.items():
            self.assertEqual((entry.index,entry.size),(new[address].index,new[address].size))
            if address not in (VROM,0x19D40):self.assertEqual(entry.extract(self.base),new[address].extract(image))
        from keyboard_grid_overlay import verify_owned_parts
        verify_owned_parts(image,self.native,report['keyboard_grid'],report['apology_input'])
        from notice_overlay import verify_installation
        verify_installation(image,self.native,report['runtime_module'],report['noticeboard'])


if __name__=='__main__':unittest.main()
