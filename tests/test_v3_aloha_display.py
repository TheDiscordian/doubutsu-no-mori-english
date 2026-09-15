"""Full imported-shirt consumers and current bounded cartridge installation."""
import ctypes as c
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,DMA_START,apply_ups,by_vrom,n64_checksum,sha256
from v3_aloha_display import BASE,BASE_SHA,BLOB,CONFIG,DISPLAY_ROWS,MODULE,STARTUP,clothing_table
from v3_clothing_display import MODEL
from v3_import_catalog import read_donor
import v3_catalogue as catalogue

OUTPUT=ROOT/'build/v3-aloha-display-03'


class AlohaDisplayLogic(unittest.TestCase):
    def test_complete_shared_consumer_pipeline(self):
        with tempfile.TemporaryDirectory(prefix='v3-aloha-display-') as directory:
            executable=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=undefined',
                '-fno-sanitize-recover=all',str(ROOT/'tests/v3_aloha_display_test.c'),'-o',str(executable)],
                check=True,capture_output=True)
            result=subprocess.run([str(executable)],check=True,capture_output=True,text=True)
            self.assertIn('all three mannequins',result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(),'Current aloha display cartridge required')
class AlohaDisplayCartridge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.r=json.loads((OUTPUT/'build.json').read_text())
        cls.base=(BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior=json.loads((BASE/'build.json').read_text())
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.previous=cls.old[BLOB].extract(cls.base)
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()

    def test_exact_installed_helpers_profiles_and_retained_resources(self):
        expected=bytearray(self.previous)
        ranges={'furniture_expanded':(0x5800,0x6000),'furniture_tables':(0xA000,0xA200),
                'display_items':(0x6C00,0x6F00),'display_conversion':(0x6270,0x6380),
                'display_roster':(0x6380,0x6540)}
        for part,(at,end) in ranges.items():
            code=(OUTPUT/part/'code.bin').read_bytes()
            self.assertLessEqual(len(code),end-at)
            self.assertEqual(sha256(code),self.r['aloha_display']['code'][part]['sha256'])
            expected[at:end]=code+bytes(end-at-len(code))
        for row in self.r['aloha_display']['hooks']:
            if row['location']=='blob':
                at=row['offset'];self.assertEqual(expected[at:at+8].hex(),row['before'])
                expected[at:at+8]=bytes.fromhex(row['after'])
        for item,at in DISPLAY_ROWS.items():
            row=next(r for r in self.r['aloha_display']['rows'] if r['donor_item_id']==f'{item:04X}')
            packed=struct.pack('>HHI',row['runtime_index'],int(row['item_id'],16),1)+self.previous[0x6608:0x664C]+bytes(4)
            expected[at:at+80]=packed
            self.assertEqual(row['profile_ram'],f'{0x80460000+at+8:08X}')
        expected[0x20+99]|=12;struct.pack_into('>I',expected,4,58)
        for row in self.r['aloha_display']['resource_moves']:
            expected.extend(bytes(row['blob_offset']-len(expected)))
            expected.extend(self.files[row['vrom']].extract(self.rom))
        self.assertEqual(expected,self.blob)
        # Metadata, defaults, accessory/audio code/data, and every original model stay intact.
        for at,end in ((0x2820,0x2900),(0x2C00,0x2E80),(0x70000,0x7F000),(0x80000,len(self.previous))):
            self.assertEqual(self.blob[at:end],self.previous[at:end])
        self.assertEqual(self.files[MODEL].extract(self.rom),self.old[MODEL].extract(self.base))

    def test_complete_catalogue_matches_actual_donor_and_retains_native_order(self):
        stable=(ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        donor=read_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        table,report=clothing_table(stable,donor['rel'],symbols,self.prior)
        cat=self.r['catalogue'];data=self.files[catalogue.VROM].extract(self.rom)
        at=cat['clothing']['table_address']-catalogue.RAM
        self.assertEqual(data[at:at+len(table)],table)
        self.assertEqual(cat['clothing']['imports'],report['imports'])
        self.assertEqual(len(table),496)
        self.assertEqual(cat['clothing']['total_rows'],248)
        self.assertEqual([r['donor_position'] for r in report['imports']],[183,18,19])
        self.assertEqual(struct.unpack_from('>I',data,0x808AF7C0-catalogue.RAM)[0],248)
        self.assertEqual(cat['total_rows'],439)
        self.assertEqual(cat['additional_pool_allocation'],0)
        self.assertLessEqual(cat['conservative_pool_required'],cat['pool_reserved'])
        self.assertFalse(cat['clothing']['aloha_ordinary_shop_stock_added'])

    def test_profile_changes_are_only_two_display_dependencies(self):
        before=bytearray.fromhex(self.prior['save_runtime']['profile_hex']);before[99]|=12
        self.assertEqual(self.blob[0x20:0xE0],before)
        self.assertEqual(bytes.fromhex(self.r['save_runtime']['profile_hex']),before)
        self.assertEqual(self.r['save_runtime']['profile_sha256'],sha256(before))
        self.assertFalse(self.r['aloha_display']['saved_format_changed'])
        self.assertFalse(self.r['aloha_display']['older_builds_accept_new_saves'])
        self.assertEqual(self.blob[0xF400:0x10000],self.previous[0xF400:0x10000])

    def test_actual_codec_accepts_older_profiles_and_rejects_missing_displays_without_writes(self):
        from tests.test_v3_save_clothing import fixture,reference_pack
        from v3_save_clothing import PROFILE,STATE
        source,_=fixture()
        old=bytes.fromhex(self.prior['save_runtime']['profile_hex'])
        current=bytes.fromhex(self.r['save_runtime']['profile_hex'])
        buffer=lambda data:(c.c_ubyte*len(data)).from_buffer_copy(data)
        with tempfile.TemporaryDirectory(prefix='v3-aloha-profile-') as directory:
            library=Path(directory)/'codec.so'
            subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',
                '-DAF_V3_CLOTHING_PROFILE=1',str(ROOT/'overlays/v3/save_codec.c'),'-o',str(library)],
                check=True,capture_output=True)
            api=c.CDLL(str(library))
            api.af_v3_save_check.argtypes=(c.c_void_p,c.c_uint,c.c_void_p,c.c_void_p)
            for stored,selected,wanted in ((old,current,1),(current,current,1),(current,old,-7)):
                bank=reference_pack(source,stored+bytes(STATE-PROFILE))
                image,profile,out=buffer(bank),buffer(selected),buffer(b'\xA5'*STATE)
                self.assertEqual(api.af_v3_save_check(image,len(bank),profile,out),wanted)
                self.assertEqual(bytes(image),bank)
                self.assertEqual(bytes(out),selected+bytes(STATE-PROFILE) if wanted==1 else b'\xA5'*STATE)

    def test_only_declared_physical_changes_and_complete_patch(self):
        expected=bytearray(self.base)
        for vrom in (BLOB,CODE_VROM,MODULE,catalogue.PARENT):
            entry=self.files[vrom];self.assertEqual(entry.pstart,self.old[vrom].pstart)
            expected[entry.pstart:entry.pstart+entry.size]=entry.extract(self.rom)
        for vrom in (BLOB,catalogue.VROM,catalogue.RELOC):
            at=DMA_START+self.files[vrom].index*16;expected[at:at+16]=self.rom[at:at+16]
        expected[0x10:0x18]=self.rom[0x10:0x18]
        self.assertEqual(expected,self.rom)
        for vrom,entry in self.files.items():
            if vrom not in (BLOB,catalogue.VROM,catalogue.RELOC):self.assertEqual(entry,self.old[vrom])
        core=bytearray(self.old[CODE_VROM].extract(self.base))
        for row in self.r['aloha_display']['hooks']:
            if row['location']=='core':
                at=row['offset'];self.assertEqual(core[at:at+8].hex(),row['before'])
                core[at:at+8]=bytes.fromhex(row['after'])
        self.assertEqual(core,self.files[CODE_VROM].extract(self.rom))
        module=self.files[MODULE].extract(self.rom)
        old=bytearray(self.old[MODULE].extract(self.base));old[STARTUP:CONFIG+16]=module[STARTUP:CONFIG+16]
        self.assertEqual(old,module)
        self.assertEqual(struct.unpack_from('>4I',module,CONFIG),(BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),58))
        self.assertEqual(sha256(self.base),BASE_SHA)
        self.assertEqual(n64_checksum(self.rom),struct.unpack_from('>2I',self.rom,0x10))
        self.assertEqual(apply_ups(self.native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)


if __name__=='__main__':unittest.main()
