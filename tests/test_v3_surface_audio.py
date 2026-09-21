"""Complete donor floor sounds, native dispatch, and retained import contracts."""
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_sound_programs import installed_resource
from v3_surface_audio import prepare,patch_consumers,program,SOURCES
import v3_optional_composition as composer

OUT=ROOT/'build/v3-surface-audio-runtime-01'


class SurfaceAudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json');cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.old=by_vrom(cls.base)
        cls.core=cls.files[CODE_VROM].extract(cls.image);cls.before=cls.old[CODE_VROM].extract(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old_blob=cls.old[BLOB].extract(cls.base)
        cls.surface=cls.report['room_surfaces'];cls.sound=cls.surface['sound'];cls.items=cls.surface['items']

    def test_complete_program_category_and_original_dispatch(self):
        resources,receipt,audio=prepare(self.base,self.prior)
        for key,value in receipt.items():self.assertEqual(value,self.sound[key])
        sequence,_,_=installed_resource(self.image,self.core,'seq',199)
        old,_,_=installed_resource(self.base,self.before,'seq',199)
        self.assertEqual(sequence,resources['sequence']);self.assertEqual(len(sequence)-len(old),176)
        allowed={0x188,0x189}
        for row in self.sound['footstep_bindings']:
            at=0x2F6A+row['index']*2;allowed.update((at,at+1))
            self.assertEqual(old[row['before']],255)
            self.assertNotEqual(old[row['after']],255)
        original_selectors=struct.unpack_from('>73H',self.before,0x80113A64-CODE_RAM)
        original_variants={0x2E6+selector+9*variant for selector in original_selectors for variant in range(8)}
        added_variants={0x300+row['index'] for row in self.sound['footstep_bindings']}
        self.assertFalse(original_variants&added_variants)
        for sid in original_variants:
            at=0x2F6A+(sid&255)*2
            self.assertEqual(sequence[at:at+2],old[at:at+2])
        self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(sequence,old))))
        for row in self.sound['selectors']:
            self.assertEqual(len(row['walking']),8)
            for sound in row['walking']+[row['movement']]:
                sid=sound['native_sound_id'];table=struct.unpack_from('>H',sequence,0x188+2*(sid>>8))[0]
                at=struct.unpack_from('>H',sequence,table+2*(sid&255))[0]
                self.assertEqual(at,sound['native_offset'])
                raw,desc=program(sequence,at)
                self.assertEqual(sha256(raw),sound['program_sha256'])
                self.assertEqual((desc['selector'],desc['instrument']),
                    (sound['native_selector'],sound['native_instrument']))
                self.assertEqual(desc['events'],sound['source_program']['events'])
        self.assertEqual([r['native_movement_sound'] for r in self.sound['imports']], [30,80,28,32,32])
        self.assertEqual(self.sound['additional_instruments'],0)
        for kind,index in [('bank',139),('bank',140),('bank',141),('wave',5)]:
            self.assertEqual(installed_resource(self.image,self.core,kind,index)[0],
                installed_resource(self.base,self.before,kind,index)[0])

    def test_all_consumers_bounds_and_memory_budget(self):
        patched=bytearray(self.before);contracts,patches=patch_consumers(patched)
        self.assertEqual(contracts,self.sound['native_consumers']);self.assertEqual(patches,self.sound['consumer_patches'])
        for row in patches:
            at=row['address']-CODE_RAM
            self.assertEqual(self.core[at:at+4],bytes.fromhex(row['after']))
        # Other changes in the core are exactly recorded resource headers/heap arguments.
        allowed=set()
        for row in patches+self.sound['heap_patches']:
            at=row['address']-CODE_RAM;allowed.update(range(at,at+len(bytes.fromhex(row['after']))))
        for row in self.report['fire_sound']['resources'].values():
            at=row['header_address']-CODE_RAM;allowed.update(range(at,at+16))
        self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(self.core,self.before))))
        bad=bytearray(self.before);bad[0x800F8E24-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'complete native'):patch_consumers(bad)
        old_table=self.before[0x80113A64-CODE_RAM:0x80113A64-CODE_RAM+146]
        for row in self.sound['tables']:
            at=self.items['blob_offset']+row['offset'];data=self.blob[at:at+row['bytes']]
            self.assertEqual(sha256(data),row['sha256']);self.assertEqual(data[:146],old_table)
            self.assertEqual(len(data),256*2);self.assertEqual(struct.unpack_from('>H',data,510)[0],27)
        self.assertEqual(self.sound['audio_heap_growth'],1024)
        self.assertEqual(self.sound['after_budget']['conservative_spare'],896)
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],1024)
        a=self.items['blob_offset'];packet=self.blob[a:a+self.items['bytes']]
        self.assertEqual(sha256(packet),self.items['sha256']);self.assertEqual(zlib.crc32(packet),self.items['crc32'])
        self.assertEqual(packet[:0x3A00],self.old_blob[a:a+0x3A00])
        self.assertEqual(packet[0x3E00:],self.old_blob[a+0x3E00:a+0x4000])

    def test_unchanged_profiles_resources_and_composition(self):
        for key in ('save_runtime','save_codec','hra','catalogue'):self.assertEqual(self.report[key],self.prior[key])
        for key in ('rows','banks','application','save','menu','scoring'):
            self.assertEqual(self.surface[key],self.prior['room_surfaces'][key])
        for path in SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.surface['sources'][path])
        self.assertFalse(self.report['saved_format_changed'])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');choices=composer.catalogue(self.image,self.report)
            self.assertEqual(len(choices),141)
            self.assertEqual(composer.compose(self.image,self.report,choices,composer.resolve(choices,list(choices)))[0],self.image)
            self.assertEqual(sha256(composer.compose(self.image,self.report,choices,composer.resolve(choices,[]))[0]),self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),(OUT/'asset-loader.ups').read_bytes()),self.image)


if __name__=='__main__':unittest.main()
