"""Current-cartridge dependency selection, bounded writes, and save profiles."""
import ctypes as c
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, n64_checksum, sha256
import v3_optional_composition as composer
from v3_save_clothing import PROFILE, STATE
from tests.test_v3_save_clothing import reference_pack

MAELLE, PUNCHY, CHERI = (f'GAFE01-r0/villager/{index:04X}' for index in (216,235,232))


class OptionalCompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base, cls.report = composer.inputs()
        cls.catalog = composer.catalogue(cls.base, cls.report)
        cls.temp = tempfile.TemporaryDirectory(prefix='v3-optional-composition-')
        library = Path(cls.temp.name)/'codec.so'
        subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',
            '-DAF_V3_CLOTHING_PROFILE=1',str(ROOT/'overlays/v3/save_codec.c'),'-o',str(library)],
            check=True, capture_output=True, text=True)
        cls.codec = c.CDLL(str(library))
        cls.codec.af_v3_save_check.argtypes = (c.c_void_p,c.c_uint,c.c_void_p,c.c_void_p)

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def select(self, *selected):
        return composer.resolve(self.catalog, list(selected))

    def test_actual_house_and_outfit_dependencies_not_just_names(self):
        self.assertEqual(len(self.catalog),26)
        self.assertEqual(self.select(PUNCHY)['required'],
                         ['GAFE01-r0/item/24BF','GAFE01-r0/item/3350'])
        self.assertEqual(self.select(CHERI)['required'],
                         ['GAFE01-r0/item/3224','GAFE01-r0/item/32B8'])
        self.assertEqual(self.select(MAELLE)['required'],['GAFE01-r0/item/241A'])
        self.assertEqual(self.select('GAFE01-r0/item/24BF')['required'],[])
        profile = bytes.fromhex(self.select(PUNCHY)['profile_hex'])
        self.assertEqual(len(profile),192)
        self.assertTrue(profile[183]&0x80)  # Cherry clothing.
        self.assertTrue(profile[119]&0x80)  # Its placed mannequin.
        self.assertTrue(profile[58]&0x10)   # Speed bag, not unrelated barrels.
        self.assertFalse(profile[49]&2)

    def test_order_duplicates_and_removal_resolve_from_requested_set(self):
        self.assertEqual(self.select(PUNCHY,MAELLE,PUNCHY),self.select(MAELLE,PUNCHY))
        both = self.select(PUNCHY,MAELLE)
        only = self.select(MAELLE)
        self.assertNotIn('GAFE01-r0/item/3350',only['enabled'])
        self.assertIn('GAFE01-r0/item/3350',both['enabled'])
        for key in only['enabled']:
            self.assertEqual(self.catalog[key]['id'],key)
        for bad in ('GAFE01-r0/item/3AFC','GAFE01-r0/item/3352','GAFE01-r0/villager/00EC',
                    'GAFE01-r0/item/1234','GAFE01-r1/villager/00EB'):
            with self.assertRaises(ValueError): self.select(bad)
        with self.assertRaises(ValueError): composer.resolve(self.catalog,'all')

    def test_subset_toggles_actual_native_enable_fields_and_nothing_else(self):
        selection = self.select(MAELLE,PUNCHY)
        result,writes,blob = composer.compose(self.base,self.report,self.catalog,selection)
        self.assertEqual(blob[0x20:0xE0].hex(),selection['profile_hex'])
        for key,row in self.catalog.items():
            at,width = row['enable_offset'],row['enable_bytes']
            self.assertEqual(int.from_bytes(blob[at:at+width],'big'),key in selection['enabled'])
            if row['kind']=='villager':
                self.assertEqual(blob[row['town_flag_offset']],key in selection['enabled'])
            if row['kind']=='clothing':
                self.assertEqual(struct.unpack_from('>I',blob,row['display_enable_offset'])[0],
                                 key in selection['enabled'])
        files = by_vrom(result)
        module = files[composer.MODULE].extract(result)
        self.assertEqual(struct.unpack_from('>4I',module,composer.CONFIG),
                         (composer.BLOB,0xC000,zlib.crc32(blob[:0xC000]),60))
        self.assertEqual(struct.unpack_from('>2I',result,0x10),n64_checksum(result))
        self.assertEqual(len(result),len(self.base))
        reverse = [{**row,'before':row['after'],'after':row['before']} for row in writes]
        self.assertEqual(composer.apply_writes(result,reverse),self.base)
        base_files = by_vrom(self.base)
        self.assertEqual(files,base_files)  # No directory, allocation, or ID changes.
        self.assertEqual(blob[0xC000:],base_files[composer.BLOB].extract(self.base)[0xC000:])
        self.assertEqual(composer.compose(self.base,self.report,self.catalog,
                         self.select(PUNCHY,MAELLE))[0],result)

    def test_all_and_empty_reproduce_exact_pinned_cartridges(self):
        full = self.select(*self.catalog)
        result,writes,_ = composer.compose(self.base,self.report,self.catalog,full)
        self.assertEqual(result,self.base)
        self.assertEqual(writes,[])
        self.assertEqual(full['profile_hex'],self.report['save_runtime']['profile_hex'])
        result,writes,blob = composer.compose(self.base,self.report,self.catalog,self.select())
        self.assertEqual(sha256(result),composer.STABLE_SHA)
        self.assertEqual(writes,[])
        self.assertIsNone(blob)

    def test_bad_overlapping_and_tampered_writes_fail_without_source_changes(self):
        source = b'12345678'
        row = {'offset':2,'before':b'34'.hex(),'after':b'AB'.hex()}
        self.assertEqual(composer.apply_writes(source,[row]),b'12AB5678')
        for edits in ([row,row],[{**row,'offset':-1}],[{**row,'offset':8}],
                      [{**row,'before':'ffff'}],[{**row,'after':'00'}]):
            with self.assertRaises(ValueError): composer.apply_writes(source,edits)
        self.assertEqual(source,b'12345678')
        tampered = self.select(PUNCHY);tampered['enabled'].remove('GAFE01-r0/item/3350')
        with self.assertRaises(ValueError):
            composer.compose(self.base,self.report,self.catalog,tampered)

    def test_actual_codec_equal_superset_and_missing_dependency_profiles(self):
        source = (ROOT/'local/rc2-save-report-g3O4lU/test.flash').read_bytes()[:65536]
        profile = bytes.fromhex(self.select(PUNCHY)['profile_hex'])
        state = profile+bytes(STATE-PROFILE)
        packed = bytes(reference_pack(source,state))
        def buffer(data): return (c.c_ubyte*len(data)).from_buffer_copy(data)
        for wanted,expected in ((profile,1),
                (bytes.fromhex(self.select(PUNCHY,MAELLE)['profile_hex']),1),
                (bytes.fromhex(self.select(MAELLE)['profile_hex']),-7),
                (bytes.fromhex(self.select('GAFE01-r0/item/24BF')['profile_hex']),-7)):
            bank,current,out = buffer(packed),buffer(wanted),buffer(b'\xA5'*STATE)
            self.assertEqual(self.codec.af_v3_save_check(bank,len(packed),current,out),expected)
            self.assertEqual(bytes(bank),packed)
            self.assertEqual(bytes(current),wanted)
            self.assertEqual(bytes(out),wanted+bytes(STATE-PROFILE) if expected==1 else b'\xA5'*STATE)
