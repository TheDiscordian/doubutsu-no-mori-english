"""Shared handheld ownership, source catalogue classification, and cartridge retention."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
import v3_held_collection as adapter
from tests import test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_HELD_COLLECTION_BUILD','build/v3-held-collection-02')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_actual_selection_collection_and_codec(self):
        self.sanitized('v3_held_collection_test.c',
            ('overlays/v3/collection.c','overlays/v3/save_codec.c'),
            ('-DAF_V3_CLOTHING_PROFILE=1',
             '-Daf_v3_catalogue_record=af_v3_prior_catalogue_record',
             '-Daf_v3_catalogue_owned=af_v3_prior_catalogue_owned'))

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current collection cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old=cls.before[BLOB].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['collection']

    def test_complete_source_context_and_umbrella_membership(self):
        source=adapter.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        table,receipt=adapter.source_records(source,self.prior['equipment_resources'])
        for k,v in json.loads(json.dumps(receipt)).items():self.assertEqual(v,self.r[k])
        self.assertEqual(len(receipt['rows']),8)
        for row in receipt['rows']:
            self.assertEqual(row['catalogue']['category'],'umbrella')
            self.assertEqual(row['room_drop_item_id'],row['item_id'])
        at=self.e['blob_offset']+self.e['parent_readers']['table_offset']
        self.assertEqual(self.blob[at:at+len(table)],table)
        address=source.symbol('mCL_item_idx_data')[0]+4*8
        source.relocations[address]=(1,True,5,0)
        with self.assertRaises(ValueError):adapter.source_records(source,self.prior['equipment_resources'])

    def test_complete_code_and_unchanged_acquisition_art_profile_and_saves(self):
        at=self.e['blob_offset'];old=self.old[at:at+self.e['bytes']]
        module=self.blob[at:at+self.e['bytes']];restored=bytearray(module)
        for start,end in ((0x3000,0x3800),(adapter.CODE,self.e['bytes']-16)):
            restored[start:end]=old[start:end]
        self.assertEqual(restored,old)
        previous=self.prior['equipment_resources']['parent_readers']['code']['bytes']
        self.assertEqual(module[0x3000:0x3000+previous],old[0x3000:0x3000+previous])
        self.assertEqual(sha256(module),self.e['sha256']);self.assertEqual(zlib.crc32(module),self.e['crc32'])
        self.assertEqual(module[adapter.CODE:adapter.CODE+self.r['code']['bytes']],
            (OUTPUT/'held_collection/code.bin').read_bytes())
        self.assertEqual(module[0x3000:0x3000+self.r['identity_code']['bytes']],
            (OUTPUT/'held_items/code.bin').read_bytes())
        restored=bytearray(self.blob[:len(self.old)])
        for a,b in ((4,8),(0xF8,0xFC),(0x6C00,0x6F00),(0x99C0,0x99C8),
                    (0x9AD4,0x9ADC),(at,at+self.e['bytes'])):
            restored[a:b]=self.old[a:b]
        self.assertEqual(restored,self.old)
        for v in self.files.keys()-{BLOB,MODULE,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),f'{v:08X}')
        for k in ('collection','save_runtime','save_codec','furniture','catalogue','display_aliases'):
            self.assertEqual(self.report[k],self.prior[k])
        self.assertFalse(self.r['catalogue_rows_installed']);self.assertFalse(self.r['saved_format_changed'])

    def test_startup_patch_and_complete_source_receipts(self):
        module=self.files[MODULE].extract(self.rom)
        self.assertIn(f'-DAF_V3_EQUIPMENT_CRC=0x{self.e["crc32"]:08X}u',self.report['startup']['flags'])
        self.assertEqual(self.report['runtime_abi'],self.prior['runtime_abi']+1)
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        for path in adapter.SOURCES:
            self.assertEqual(sha256((ROOT/path).read_bytes()),self.report['sources'][path])

if __name__=='__main__':unittest.main()
