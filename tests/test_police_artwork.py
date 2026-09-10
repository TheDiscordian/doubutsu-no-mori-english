"""English police artwork retains native seasonal geometry and streamed bounds."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from police_artwork import (OBJECT,NEW_OBJECT,ROWS,LAYOUTS,TRIANGLES,commands,
    expected_commands,native_triangles,geometry,patch_assets,build)
from title_assets import DATA_BASE,untile,pack4
from keyboard_grid_labels import CORRECTED_SHA


@unittest.skipUnless((ROOT/'build/shop-signs-01/build.json').is_file(),'Local supplied sources required')
class PoliceArtworkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/shop-signs-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/shop-signs-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.files=by_vrom(cls.base);cls.prior=cls.files[OBJECT].extract(cls.base)
        with tempfile.TemporaryDirectory(prefix='af-police-gbi-') as directory:
            cls.compiled=commands(Path(directory))

    def test_lossless_pixels_and_only_documented_vertex_uv_topology_regions_change(self):
        changed,report=patch_assets(self.native,self.prior,self.rel,self.symbols,self.compiled)
        restored=bytearray(changed)
        for row in report['changes']:
            at,size=int(row['object_offset'],16),row['bytes']
            restored[at:at+size]=self.prior[at:at+size]
        self.assertEqual(restored,self.prior)
        self.assertEqual(len(report['changes']),8)
        self.assertEqual(self.compiled,expected_commands())
        self.assertEqual(native_triangles(self.compiled),list(TRIANGLES))
        for row in ROWS:
            pixels=pack4(untile(self.rel[DATA_BASE+row.gc:DATA_BASE+row.gc+2048],128,32,4))
            self.assertEqual(changed[row.native-OBJECT:row.native-OBJECT+2048],pixels)
        for name,at,count,tri,gc,mapping in LAYOUTS:
            old=[self.prior[at+i*16:at+(i+1)*16] for i in range(count)]
            new=[changed[at+i*16:at+(i+1)*16] for i in range(23)]
            donor=[self.rel[DATA_BASE+gc+i*16:DATA_BASE+gc+(i+1)*16] for i in range(48,71)]
            for index,(vertex,source) in enumerate(zip(new,donor)):
                self.assertEqual(vertex[:6]+vertex[8:12],source[:6]+source[8:12])
                self.assertEqual(vertex[:8]+vertex[12:],old[mapping[index]][:8]+old[mapping[index]][12:])
            retained=[t for t in native_triangles(self.prior[tri:tri+56]) if not set(t)&{4,5,6,7}]
            self.assertEqual(geometry(old,retained),geometry(new,TRIANGLES))
            self.assertEqual(changed[at+23*16:at+count*16],self.prior[at+23*16:at+count*16])
            self.assertEqual(changed[tri-8:tri],self.prior[tri-8:tri])
            self.assertEqual(changed[tri+56:tri+64],self.prior[tri+56:tri+64])

    def test_reject_wrong_sources_prior_region_and_compiled_commands(self):
        with self.assertRaises(ValueError):patch_assets(self.native,self.prior,self.rel[:-1],self.symbols,self.compiled)
        with self.assertRaises(ValueError):patch_assets(self.native,self.prior,self.rel,self.symbols+b'\n',self.compiled)
        wrong=bytearray(self.prior);wrong[0x4C000]^=1
        with self.assertRaisesRegex(ValueError,'unrelated changes'):
            patch_assets(self.native,bytes(wrong),self.rel,self.symbols,self.compiled)
        with self.assertRaisesRegex(ValueError,'Compiled police'):
            patch_assets(self.native,self.prior,self.rel,self.symbols,bytes(56))

    def test_complete_cartridge_actual_streamed_copy_and_all_previous_resources(self):
        before=copy.deepcopy(self.report)
        image,patch,report=build(self.native,self.base,self.report,self.rel,self.symbols,self.compiled)
        self.assertEqual(self.report,before)
        self.assertEqual(len(image),32*1024*1024)
        self.assertEqual(apply_ups(self.native,patch),image)
        self.assertEqual(report['police_artwork']['building_ranges_checked'],92)
        files=by_vrom(image)
        self.assertEqual(set(files),set(self.files))
        for v,entry in self.files.items():
            if v not in (OBJECT,NEW_OBJECT,0x19D40):
                self.assertEqual(files[v].extract(image),entry.extract(self.base),f'{v:08X}')
            self.assertEqual(files[v].index,entry.index)
            self.assertEqual(files[v].size,entry.size)
        expanded=files[NEW_OBJECT].extract(image)
        self.assertEqual(expanded[:len(self.prior)],files[OBJECT].extract(image))
        self.assertEqual(expanded[len(self.prior):],self.files[NEW_OBJECT].extract(self.base)[len(self.prior):])
        self.assertEqual(sha256(files[0x3940000].extract(image)),CORRECTED_SHA)
        for key,value in self.report.items():
            if key not in ('output_sha256','patch_sha256','release_status'):
                self.assertEqual(report[key],value,key)


if __name__=='__main__':unittest.main()
