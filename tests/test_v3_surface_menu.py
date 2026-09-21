"""Surface catalogue category, unchanged allocations, and native relocation."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,apply_ups
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_asset_loader import BLOB
from v3_catalogue import VROM,RELOC,RAM
from v3_furniture_install import inputs
from v3_surface_menu import patch_catalogue,retain_catalogue,SOURCES
import v3_optional_composition as composer

OUT=ROOT/'build/v3-surface-menu-runtime-03'


class SurfaceMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json');cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.before=by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old=cls.before[BLOB].extract(cls.base)
        cls.surface=cls.report['room_surfaces'];cls.items=cls.surface['items'];cls.menu=cls.surface['menu']

    def test_actual_c_routing_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-surface-menu-') as directory:
            binary=Path(directory)/'test'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_surface_menu_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)

    def test_complete_patch_relocation_and_future_rebuild_retention(self):
        old=self.before[VROM].extract(self.base);rel=self.before[RELOC].extract(self.base)
        data,fixed,cat=patch_catalogue(old,rel,self.prior['catalogue'],self.menu)
        self.assertEqual(data,self.files[VROM].extract(self.image));self.assertEqual(fixed,self.files[RELOC].extract(self.image))
        self.assertEqual(cat,self.report['catalogue'])
        self.assertEqual(retain_catalogue(self.report,self.image,old,rel,self.prior['catalogue']),(data,fixed,cat))
        for patch in cat['surface_menu']['patches']:
            bad=bytearray(old);bad[patch['address']-RAM]^=1
            with self.assertRaises(ValueError):patch_catalogue(bad,rel,self.prior['catalogue'],self.menu)
        for destination in (0x801A0010,0x802F8010,0x803D0010):
            load=relocate_verified_data(Image(RAM,len(data),struct.unpack_from('>5I',fixed)),data,fixed,destination)
            previous=relocate_verified_data(Image(RAM,len(old),struct.unpack_from('>5I',rel)),old,rel,destination)
            allowed={i for p in cat['surface_menu']['patches'] for i in range(p['address']-RAM,p['address']-RAM+len(bytes.fromhex(p['after'])))}
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(load,previous))))
            at=cat['code']['symbols']['af_v3_catalogue_bit']-RAM
            high,low=struct.unpack_from('>2I',load,at)
            target=((high&65535)<<16)+struct.unpack('>h',struct.pack('>H',low&65535))[0]
            self.assertEqual(target,destination+0x808A931C-RAM)
            for row in self.menu['tables']:
                self.assertEqual(struct.unpack_from('>2I',load,row['descriptor']-RAM),(row['ram'],64))
        self.assertEqual(len(data),len(old));self.assertEqual(len(fixed),len(rel))
        for key in ('conservative_pool_required','pool_reserved','capacity_expansion'):
            self.assertEqual(cat[key],self.prior['catalogue'][key])

    def test_packet_preserved_assets_profiles_and_exact_composition(self):
        p=self.items['blob_offset'];packet=self.blob[p:p+self.items['bytes']]
        self.assertEqual(sha256(packet),self.items['sha256']);self.assertEqual(zlib.crc32(packet),self.items['crc32'])
        self.assertEqual(packet[:0x3000],self.old[p:p+0x3000])
        self.assertEqual(packet[0x3000:0x3000+self.menu['code']['bytes']],(OUT/'surface_menu/code.bin').read_bytes())
        self.assertEqual(packet[-16:],self.old[p+self.items['bytes']-16:p+self.items['bytes']])
        for row in self.menu['tables']:
            table=packet[row['offset']:row['offset']+row['bytes']]
            self.assertEqual(sha256(table),row['sha256']);self.assertEqual(struct.unpack('>69H',table),tuple(range(64))+tuple(range(73,78)))
        for path in SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.surface['sources'][path])
        for key in ('rows','banks','application','save'):
            self.assertEqual(self.surface[key],self.prior['room_surfaces'][key])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.report['saved_format_changed'])
        for vrom in (0x846860,0x8476A0,0x3950000,0x3960000,0x7749C0,CODE_VROM):
            self.assertEqual(self.files[vrom].extract(self.image),self.before[vrom].extract(self.base))
        pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        try:
            composer.use_build_lock(OUT/'build-lock.json');choices=composer.catalogue(self.image,self.report)
            self.assertEqual(len(choices),141)
            self.assertEqual(composer.compose(self.image,self.report,choices,composer.resolve(choices,list(choices)))[0],self.image)
            self.assertEqual(sha256(composer.compose(self.image,self.report,choices,composer.resolve(choices,[]))[0]),self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
