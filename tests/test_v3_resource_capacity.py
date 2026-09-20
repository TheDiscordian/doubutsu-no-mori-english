"""Changed storage/readers and one complete bulk category beyond the old limit."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_RAM,CODE_VROM,DMA_START,DMA_END,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,profile
from v3_import_storage import END,ROWS,ITEMS,slot
import v3_resource_capacity as capacity
import v3_room_rig_runtime as rigs
import v3_optional_composition as composer

OUT=ROOT/'build/v3-clock-category-runtime-02'


class CapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.old,cls.prior=inputs(ROOT/'build/v3-room-categories-runtime-03/build-lock.json')
        cls.files,cls.old_files=by_vrom(cls.image),by_vrom(cls.old)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old_blob=cls.old_files[BLOB].extract(cls.old)

    def test_complete_text_readers_and_directory_identities_are_preserved(self):
        self.assertEqual(capacity.checked_limit(self.image,self.report),0x02800000)
        self.assertEqual(capacity.checked_limit(self.old,self.prior),END)
        self.assertEqual(len(self.files),len(self.old_files))
        self.assertEqual(self.image[DMA_END-16:DMA_END],bytes(16))
        expected=bytearray(self.old_files[CODE_VROM].extract(self.old))
        for row in self.report['resource_capacity']['resources']:
            old,new=row['old_vrom'],row['vrom'];a,b=self.old_files[old],self.files[new]
            self.assertNotIn(old,self.files)
            self.assertEqual((a.index,a.pstart,a.pend),(b.index,b.pstart,b.pend))
            self.assertEqual(a.size,row['source_bytes']);self.assertEqual(b.size,(a.size+15)&~15)
            self.assertEqual(a.extract(self.old)+bytes(b.size-a.size),b.extract(self.image))
            self.assertEqual(self.old_files[row['table_vrom']].extract(self.old),self.files[row['table_vrom']].extract(self.image))
            at=row['reader']-CODE_RAM;expected[at:at+8]=bytes.fromhex(row['after'])
        self.assertEqual(self.files[CODE_VROM].extract(self.image),expected)
        directory=bytearray(self.old_files[0x19D40].extract(self.old))
        struct.pack_into('>I',directory,16+self.old_files[BLOB].index*16+4,BLOB+len(self.blob))
        for row in self.report['shared_runtime_refresh']['unchanged_owner_moves']:
            struct.pack_into('>4I',directory,16+self.old_files[row['vrom']].index*16,
                             row['vrom'],row['vrom']+row['bytes'],row['physical'],0)
        for row in self.report['resource_capacity']['resources']:
            struct.pack_into('>2I',directory,16+row['directory_index']*16,row['vrom'],row['vrom']+row['bytes'])
        self.assertEqual(self.files[0x19D40].extract(self.image),directory)
        moved={row['vrom'] for row in self.report['resource_capacity']['resources']}
        for v,entry in self.files.items():
            if v not in moved|{BLOB,MODULE,CODE_VROM,0x19D40}:
                self.assertEqual(entry.extract(self.image),self.old_files[v].extract(self.old),hex(v))
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])

    def test_unknown_consumers_and_occupied_destinations_reject(self):
        core=self.old_files[CODE_VROM].extract(self.old)
        changed=bytearray(core);changed[capacity.TEXT[0][4]-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'complete text consumer'):capacity.expand(self.old,self.prior,changed)
        changed=bytearray(core);struct.pack_into('>I',changed,0,0x3C01025F)
        with self.assertRaisesRegex(ValueError,'Unreviewed text-base'):capacity.expand(self.old,self.prior,changed)
        forged=copy.deepcopy(self.prior);forged['import_storage']['virtual_limit']=capacity.LIMIT
        with self.assertRaisesRegex(ValueError,'Unknown import-storage'):capacity.checked_limit(self.old,forged)
        changed=bytearray(self.old);entry=self.old_files[MODULE]
        struct.pack_into('>2I',changed,DMA_START+entry.index*16,0x029E0000,0x029E0000+entry.size)
        with self.assertRaisesRegex(ValueError,'occupied relocation'):capacity.expand(changed,self.prior,bytearray(core))
        changed=bytearray(self.image);entry=self.files[CODE_VROM]
        changed[entry.pstart+capacity.TEXT[0][5]-CODE_RAM+3]^=1
        with self.assertRaisesRegex(ValueError,'relocated text/readers'):capacity.checked_limit(changed,self.report)

    def test_bulk_clock_batch_crosses_old_limit_with_complete_assets(self):
        current=self.report['equipment_resources']['room_rigs'];old=self.prior['equipment_resources']['room_rigs']
        self.assertEqual(current['code']['sha256'],old['code']['sha256'])
        self.assertEqual(len(current['rows']),25);self.assertEqual(current['additional_resident_bytes'],0)
        self.assertEqual(self.report['equipment_resources']['bytes'],self.prior['equipment_resources']['bytes'])
        old_rows={r['item_id']:r for r in old['rows']}
        clocks=[r for r in current['rows'] if r.get('mode')==1]
        self.assertEqual(len(clocks),15);self.assertTrue(any(r['vrom']+r['bytes']>END for r in clocks))
        for row in current['rows']:
            at,n=row['blob_offset'],row['bytes'];data=self.blob[at:at+n]
            if row['item_id'] in old_rows:
                self.assertEqual(row,old_rows[row['item_id']]);self.assertEqual(data,self.old_blob[at:at+n]);continue
            source=row['source'];self.assertEqual(data,(ROOT/'build/v3-indexed-clock-rigs-prepared-01'/source['object_file']).read_bytes())
            i=slot(int(row['item_id'],16));self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],bytes(80))
            self.assertEqual(self.blob[ITEMS+i*32:ITEMS+(i+1)*32],bytes(32))
            generated=copy.deepcopy(source);generated['room_runtime']=dict(vtable=rigs.VTABLE,vrom=row['vrom'])
            self.assertEqual(struct.unpack_from('>I',profile(generated,row['vrom'],limit=capacity.LIMIT),64)[0],rigs.VTABLE)
        packet=current['packet'];at=packet['blob_offset']
        self.assertEqual(self.blob[at+4096:at+8192],rigs.encode_packet(current['rows']))
        self.assertEqual(sha256(self.blob[at:at+8192]),packet['sha256'])
        self.assertGreater(self.report['import_storage']['remaining_bytes'],2_000_000)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_optional_composition_and_translation_only_output_remain_exact(self):
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),128)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                             self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
