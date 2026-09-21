"""Current cartridge surface metadata/startup, without claiming item gameplay."""
import copy
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
from v3_surface_items import RAM,SIZE,TABLE,BOOT,BOOT_END,metadata,HOOKS
import v3_optional_composition as composer

OUT=ROOT/'build/v3-surface-items-runtime-03'


class SurfaceItemsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.oldfiles=by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old=cls.oldfiles[BLOB].extract(cls.base)
        cls.surface=cls.report['room_surfaces'];cls.items=cls.surface['items']

    def test_complete_source_metadata_and_disabled_records(self):
        table,rows=metadata(self.surface['rows']);self.assertEqual(rows,self.items['rows'])
        at=self.items['blob_offset'];packet=self.blob[at:at+SIZE]
        self.assertEqual(sha256(packet),self.items['sha256']);self.assertEqual(zlib.crc32(packet),self.items['crc32'])
        self.assertEqual(packet[TABLE:TABLE+len(table)],table)
        self.assertTrue(all(not r['enabled'] for r in rows))
        bad=copy.deepcopy(self.surface['rows']);bad[0]['name']='wrong'
        with self.assertRaisesRegex(ValueError,'name, price'):metadata(bad)
        with self.assertRaisesRegex(ValueError,'complete stable'):metadata(bad[1:])
        self.assertEqual(packet[:self.items['code']['bytes']],(OUT/'surface_items/code.bin').read_bytes())
        self.assertFalse(any(packet[self.items['code']['bytes']:TABLE]))
        self.assertFalse(any(packet[TABLE+len(table):-16]))
        self.assertEqual(packet[-16:],bytes.fromhex('AF5351DE')*4)

    def test_checked_existing_bootstrap_gap_and_native_entry_chain(self):
        new=self.report['equipment_resources'];old=self.prior['equipment_resources'];at=new['blob_offset']
        packet=self.blob[at:at+new['bytes']];before=self.old[at:at+old['bytes']]
        self.assertEqual((new['ram'],new['bytes'],new['blob_offset']),(old['ram'],old['bytes'],old['blob_offset']))
        first,last=BOOT-new['ram'],BOOT_END-new['ram'];code=(OUT/'surface_bootstrap/code.bin').read_bytes()
        self.assertFalse(any(before[first:last]));self.assertEqual(packet[first:first+len(code)],code)
        self.assertEqual(packet[:first],before[:first]);self.assertEqual(packet[first+len(code):],before[first+len(code):])
        self.assertEqual(sha256(packet),new['sha256']);self.assertEqual(zlib.crc32(packet),new['crc32'])
        flags=self.report['startup']['flags'];self.assertIn('-DAF_V3_FURNITURE_INIT=0x804A8D40u',flags)
        self.assertIn(f'-DAF_V3_EQUIPMENT_CRC=0x{new["crc32"]:08X}u',flags)
        self.assertLessEqual(self.report['startup']['bytes'],992)
        for h in self.items['hooks']:
            owner,base=(MODULE,MODULE_RAM) if h['address']>=MODULE_RAM else (CODE_VROM,CODE_RAM)
            offset=h['address']-base
            self.assertEqual(self.files[owner].extract(self.image)[offset:offset+8].hex(),h['after'])
            self.assertEqual(self.oldfiles[owner].extract(self.base)[offset:offset+8].hex(),h['before'])
        self.assertEqual(self.items['additional_resident_bytes'],4096)
        self.assertEqual(RAM,0x804BA000+0x2000);self.assertLessEqual(RAM+SIZE,0x80500000)

    def test_actual_c_and_startup_failures_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-surface-items-') as directory:
            executable=Path(directory)/'check'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_surface_items_test.c'),'-o',str(executable)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr);self.assertIn('checked startup pass',result.stdout)

    def test_retained_assets_save_profile_and_composition(self):
        self.assertEqual(self.items['enabled_items'],0)
        for key in ('save_runtime','staged_furniture'):
            self.assertEqual(self.report[key],self.prior[key])
        for key in ('owners','secondary_owners','banks','rows'):
            self.assertEqual(self.surface[key],self.prior['room_surfaces'][key])
        for record in self.surface['owners']+self.surface['secondary_owners']:
            for key in ('vrom','relocation_vrom'):
                v=record[key];self.assertEqual(self.files[v].extract(self.image),self.oldfiles[v].extract(self.base))
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
