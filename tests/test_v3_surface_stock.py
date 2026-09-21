"""Source-bound surface stock lists and selected-only native-category helpers."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_surface_stock import goods,list_items,SOURCES
import v3_optional_composition as composer

OUT=ROOT/'build/v3-surface-stock-runtime-01'


class SurfaceStockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json');cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.old=by_vrom(cls.base)
        cls.core=cls.files[CODE_VROM].extract(cls.image);cls.before=cls.old[CODE_VROM].extract(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old_blob=cls.old[BLOB].extract(cls.base)
        cls.surface=cls.report['room_surfaces'];cls.stock=cls.surface['stock'];cls.items=cls.surface['items']

    def test_actual_c_under_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-surface-stock-') as directory:
            binary=Path(directory)/'test'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_surface_stock_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_complete_source_resources_and_native_bindings(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        resources,pending=goods(self.base,self.before,self.surface,source)
        self.assertEqual(pending,self.stock['pending']);self.assertEqual(len(pending),4)
        for (data,expected),row in zip(resources,self.stock['resources']):
            for key,value in expected.items():self.assertEqual(row[key],value)
            at=row['blob_offset'];self.assertEqual(self.blob[at:at+len(data)],data)
            self.assertEqual(row['bytes'],272)
            self.assertEqual(self.files[row['original_vrom']].extract(self.image),self.old[row['original_vrom']].extract(self.base))
            pointers=struct.unpack_from('>11I',data,0x94)
            for changed in row['lists']:
                self.assertEqual(list_items(data,pointers[changed['group']]&0xFFFFFF),
                    changed['original_items']+[int(v,16) for v in changed['added_items']])
            off=row['descriptor']-CODE_RAM
            self.assertEqual(self.core[off:off+12],bytes.fromhex(row['descriptor_after']))
        allowed=set()
        for row in self.stock['consumer_patches']:
            at=row['address']-CODE_RAM;allowed.update(range(at,at+8))
            self.assertEqual(self.core[at:at+8],bytes.fromhex(row['after']))
        for row in self.stock['resources']:
            at=row['descriptor']-CODE_RAM;allowed.update(range(at,at+12))
        self.assertTrue(all(i in allowed or x==y for i,(x,y) in enumerate(zip(self.core,self.before))))
        code=self.stock['code'];at=self.items['blob_offset']+self.stock['code_offset']
        self.assertEqual(self.blob[at:at+code['bytes']],(OUT/'surface_stock/code.bin').read_bytes())
        bridge=0x804BFFD0-0x804BC000+self.items['blob_offset']
        self.assertEqual(self.blob[bridge:bridge+16],bytes.fromhex('27BDFFE0AFBF00140802FE3C00000000'))
        bad=bytearray(self.before);bad[0x8010DAC4-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'resource/descriptor'):goods(self.base,bad,self.surface,source)
        self.assertEqual(self.stock['max_additional_temporary_bytes'],80)
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)

    def test_unchanged_profiles_packet_and_composition(self):
        for key in ('save_runtime','save_codec','hra','catalogue','fire_sound'):
            self.assertEqual(self.report[key],self.prior[key])
        for key in ('rows','banks','application','save','menu','scoring','sound'):
            self.assertEqual(self.surface[key],self.prior['room_surfaces'][key])
        for path in SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.surface['sources'][path])
        self.assertFalse(self.report['saved_format_changed'])
        at=self.items['blob_offset'];packet=self.blob[at:at+self.items['bytes']]
        self.assertEqual(sha256(packet),self.items['sha256']);self.assertEqual(zlib.crc32(packet),self.items['crc32'])
        self.assertEqual(packet[:0x3E00],self.old_blob[at:at+0x3E00]);self.assertEqual(packet[-16:],self.old_blob[at+0x3FF0:at+0x4000])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');choices=composer.catalogue(self.image,self.report)
            self.assertEqual(len(choices),141)
            self.assertEqual(composer.compose(self.image,self.report,choices,composer.resolve(choices,list(choices)))[0],self.image)
            self.assertEqual(sha256(composer.compose(self.image,self.report,choices,composer.resolve(choices,[]))[0]),self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
