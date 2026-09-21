"""Changed shared room actions, complete installation, and saved payload."""
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
from v3_asset_loader import BLOB,MODULE,MODULE_RAM
from v3_furniture_install import inputs
from v3_surface_application import OWNER,RELOC,OWNER_RAM,patch_owner,SOURCES
from v3_surface_items import RAM,SIZE,TABLE,BOOT,BOOT_END,metadata
import v3_optional_composition as composer

OUT=ROOT/'build/v3-surface-application-runtime-01'


class SurfaceApplicationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.oldfiles=by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old=cls.oldfiles[BLOB].extract(cls.base)
        cls.surface=cls.report['room_surfaces'];cls.items=cls.surface['items']

    def test_complete_owner_and_preserved_save_writers(self):
        data=self.oldfiles[OWNER].extract(self.base);rel=self.oldfiles[RELOC].extract(self.base)
        want,patches=patch_owner(data,rel,self.items['code']['symbols'])
        self.assertEqual(self.files[OWNER].extract(self.image),want)
        self.assertEqual(self.files[RELOC].extract(self.image),rel)
        self.assertEqual(self.surface['application']['patches'],patches)
        self.assertEqual(sha256(want),self.surface['owners'][0]['sha256'])
        for patch in patches:
            bad=bytearray(data);bad[patch['address']-OWNER_RAM]^=1
            with self.assertRaisesRegex(ValueError,'complete native'):patch_owner(bad,rel,self.items['code']['symbols'])
        # Exact installed native full-byte stores; all surrounding code retained.
        for address,word in ((0x8095251C,0xA02CA43D),(0x80952610,0xA02DA43C)):
            self.assertEqual(struct.unpack_from('>I',want,address-OWNER_RAM)[0],word)
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.surface['application']['saved_payload_bytes'],0xF980)

    def test_current_packet_hooks_bootstrap_and_sources(self):
        at=self.items['blob_offset'];packet=self.blob[at:at+SIZE];code=self.items['code']
        self.assertEqual(sha256(packet),self.items['sha256']);self.assertEqual(zlib.crc32(packet),self.items['crc32'])
        self.assertEqual(packet[:code['bytes']],(OUT/'surface_items/code.bin').read_bytes())
        self.assertFalse(any(packet[code['bytes']:TABLE]))
        self.assertEqual(packet[TABLE:],self.old[at+TABLE:at+SIZE])
        self.assertEqual(metadata(self.surface['rows'])[0],packet[TABLE:TABLE+self.items['table_bytes']])
        ep=self.report['equipment_resources'];old=self.prior['equipment_resources'];ea=ep['blob_offset']
        a,b=BOOT-ep['ram'],BOOT_END-ep['ram'];p=self.blob[ea:ea+ep['bytes']];q=self.old[ea:ea+old['bytes']]
        self.assertEqual((ep['ram'],ep['bytes'],ea),(old['ram'],old['bytes'],old['blob_offset']))
        self.assertEqual(p[:a],q[:a]);self.assertEqual(p[b:],q[b:])
        self.assertEqual(sha256(p),ep['sha256']);self.assertEqual(zlib.crc32(p),ep['crc32'])
        flags=self.report['startup']['flags']
        self.assertIn(f'-DAF_V3_EQUIPMENT_CRC=0x{ep["crc32"]:08X}u',flags)
        self.assertIn('-DAF_V3_FURNITURE_INIT=0x804A8D40u',flags)
        self.assertLessEqual(self.report['startup']['bytes'],992)
        for h in self.items['hooks']+[self.surface['application']['floor_hook']]:
            v,ram=(MODULE,MODULE_RAM) if h['address']>=MODULE_RAM else (CODE_VROM,CODE_RAM)
            offset=h['address']-ram
            self.assertEqual(self.files[v].extract(self.image)[offset:offset+8].hex(),h['after'])
            self.assertEqual(self.oldfiles[v].extract(self.base)[offset:offset+8].hex(),h['before'])
        for p in SOURCES:self.assertEqual(self.surface['sources'][p],sha256((ROOT/p).read_bytes()),p)
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)

    def test_actual_room_and_payload_c_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-surface-application-') as directory:
            for source in ('v3_surface_application_test.c','v3_surface_save_test.c'):
                executable=Path(directory)/source[:-2]
                command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                    '-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1',
                    str(ROOT/'tests'/source),'-o',str(executable)]
                result=subprocess.run(command,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stderr)
                result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,0,result.stderr)

    def test_retained_artwork_optional_profiles_and_patch(self):
        for key in ('secondary_owners','banks','rows'):
            self.assertEqual(self.surface[key],self.prior['room_surfaces'][key])
        for row in self.surface['rows']:
            a=row['blob_offset'];n=row['bytes'];self.assertEqual(self.blob[a:a+n],self.old[a:a+n])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),141)
            self.assertFalse({r['id'] for r in self.items['rows']}&set(catalog))
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
