"""Shared native room lifecycle, stable destinations, and complete installation."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_furniture_install import inputs
from v3_asset_loader import BLOB,MODULE
from v3_equipment_runtime import RAM as EQUIPMENT_RAM,retired_module_space
from v3_import_storage import ROWS,ITEMS,slot
from v3_furniture_pipeline import Source
import v3_room_rig_runtime as runtime
import v3_optional_composition as composer
from v3_registry import furniture_representation_identity,LEGACY_ROOM_ALIASES,CLOTHING_DISPLAYS

OUT=ROOT/'build/v3-room-rigs-runtime-03'


class BehaviourTests(unittest.TestCase):
    def test_complete_source_movement_and_per_instance_bounds_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-rigs-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_room_rigs_test.c'),
                '-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('independent state, complete drawing, and bounds',result.stdout)

    def test_old_range_reservations_do_not_change_existing_furniture_or_garments(self):
        destinations=set()
        for donor in range(0x3000,0x33C8,4):
            index,item=furniture_representation_identity(donor)
            self.assertEqual((index,item),(1024+(donor-0x3000)//4,donor));destinations.add(item)
        destinations.update(v[1] for v in CLOTHING_DISPLAYS.values())
        for donor,expected in LEGACY_ROOM_ALIASES.items():
            index,item=furniture_representation_identity(donor)
            self.assertEqual((index,item),expected);self.assertNotIn(item,destinations)
            self.assertGreaterEqual(item,0x3C00);self.assertEqual(index,1024+slot(item));destinations.add(item)
        for bad in (True,0x1FEC,0x1FF1,0x4000):
            with self.assertRaises(ValueError):furniture_representation_identity(bad)


@unittest.skipUnless((OUT/'build-lock.json').is_file(),'Current room-rig cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json');cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files,cls.old_files=by_vrom(cls.image),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old_blob=cls.old_files[BLOB].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources'];cls.r=cls.e['room_rigs']

    def test_complete_resources_code_table_and_unused_identity_reservations(self):
        s=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        rows,assets,evidence=runtime.prepared(s,ROOT/self.r['source']['directory'])
        self.assertEqual(evidence,self.r['source'])
        self.assertEqual(len(rows),8)
        for row in self.r['rows']:
            source=next(r for r in rows if r['source_item_id']==row['source_item_id'])
            self.assertEqual({k:row[k] for k in source},source)
            at=row['blob_offset'];data=assets[row['source_item_id']]
            self.assertEqual(self.blob[at:at+len(data)],data)
            i=slot(int(row['item_id'],16))
            self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],bytes(80))
            self.assertEqual(self.blob[ITEMS+i*32:ITEMS+(i+1)*32],bytes(32))
            self.assertFalse(self.blob[32+i//8]&(1<<(i&7)))
        start=self.e['blob_offset'];module=self.blob[start:start+self.e['bytes']]
        expected=bytearray(self.old_blob[start:start+self.old['bytes']]);code=(OUT/'room_rigs/code.bin').read_bytes()
        at=runtime.RAM-EQUIPMENT_RAM;expected[at:at+len(code)]=code
        at=runtime.TABLE-EQUIPMENT_RAM;expected[at:runtime.VTABLE-EQUIPMENT_RAM]=runtime.encode(rows)
        at=runtime.VTABLE-EQUIPMENT_RAM;expected[at:at+20]=bytes.fromhex(self.r['vtable_hex'])
        self.assertEqual(module,expected)
        self.assertEqual(self.e['bytes'],self.old['bytes'])
        for row in self.e['records']:
            at,n=row['blob_offset'],row['bytes'];self.assertEqual(self.blob[at:at+n],self.old_blob[at:at+n])
        reuse=self.r['retired_space'];self.assertIsNotNone(reuse)
        self.assertEqual(retired_module_space(self.base,self.prior,self.old_blob,self.r['artwork_bytes']),reuse)
        self.assertEqual(self.r['artwork_bytes'],44400)
        for field in ('records','player_motion','player_joint_work','parent_readers','optional_selection','inventory_preview'):
            self.assertEqual(self.e[field],self.old[field])
        for v in set(self.files)-{BLOB,MODULE,0x19D40}:
            self.assertEqual(self.files[v].extract(self.image),self.old_files[v].extract(self.base),hex(v))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_existing_profiles_and_exact_empty_and_complete_outputs(self):
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),120)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
