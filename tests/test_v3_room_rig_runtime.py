"""Shared native room lifecycle, stable destinations, and complete installation."""
import copy
import json
import os
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
PACKET_OUT=ROOT/os.environ.get('V3_ROOM_CATEGORY_BUILD','build/v3-room-categories-runtime-03')


class PacketTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(PACKET_OUT/'build-lock.json')
        cls.base,cls.prior=inputs(PACKET_OUT/'base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.old_blob=by_vrom(cls.base)[BLOB].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.r=cls.e['room_rigs']

    def test_complete_installed_packet_and_preserved_resources(self):
        r=self.r;p=r['packet'];packet=self.blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(packet),p['sha256'])
        code=(PACKET_OUT/'room_rigs_packet/code.bin').read_bytes()
        self.assertEqual(packet,code.ljust(4096,b'\0')+runtime.encode_packet(r['rows']))
        self.assertEqual(r['capacity'],128);self.assertEqual(len(r['rows']),10)
        old=self.prior['equipment_resources'];module=self.blob[self.e['blob_offset']:self.e['blob_offset']+self.e['bytes']]
        expected=bytearray(self.old_blob[old['blob_offset']:old['blob_offset']+old['bytes']])
        boot=(PACKET_OUT/'room_rigs_bootstrap/code.bin').read_bytes()
        expected[runtime.RAM-EQUIPMENT_RAM:runtime.TABLE-EQUIPMENT_RAM]=boot.ljust(runtime.TABLE-runtime.RAM,b'\0')
        expected[runtime.TABLE-EQUIPMENT_RAM:runtime.VTABLE-EQUIPMENT_RAM]=bytes(runtime.VTABLE-runtime.TABLE)
        expected[runtime.VTABLE-EQUIPMENT_RAM:runtime.VTABLE-EQUIPMENT_RAM+20]=bytes.fromhex(r['vtable_hex'])
        self.assertEqual(module,expected)
        old_rows={row['item_id']:row for row in old['room_rigs']['rows']}
        for row in r['rows']:
            at,n=row['blob_offset'],row['bytes'];data=self.blob[at:at+n]
            self.assertEqual(sha256(data),row['sha256'])
            if row['item_id'] in old_rows:
                self.assertEqual(row,old_rows[row['item_id']]);self.assertEqual(data,self.old_blob[at:at+n])
            else:
                self.assertEqual(row['mode'],2);i=slot(int(row['item_id'],16))
                self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],bytes(80))
                self.assertFalse(self.blob[32+i//8]&(1<<(i&7)))
                self.assertEqual(data,(ROOT/'build/v3-storage-rigs-prepared-01'/row['source']['object_file']).read_bytes())
        self.assertEqual(self.e['bytes'],old['bytes'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],8192)
        self.assertEqual(self.e['scenery'],old['scenery'])
        for v,entry in by_vrom(self.image).items():
            if v not in (BLOB,MODULE):self.assertEqual(entry.extract(self.image),by_vrom(self.base)[v].extract(self.base),hex(v))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(PACKET_OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_table_scales_across_categories_without_enabling_prepared_art(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        clocks,assets,_=runtime.prepared_categories(source,[ROOT/'build/v3-indexed-clock-rigs-prepared-01'])
        rows=sorted(self.r['rows']+clocks,key=lambda r:r['runtime_index'])
        data=runtime.encode_packet(rows)
        self.assertEqual(struct.unpack_from('>4I',data),(runtime.PACKET_MAGIC,25,24,0))
        self.assertEqual(len(assets),15)
        for r in clocks:self.assertEqual((r['mode'],r['first'],r['last']),(1,3,4))
        for changes in ({'last':0x7FC00000},{'first':0x41400000,'last':0x3F800000},{'mode':3}):
            row=copy.deepcopy(next(r for r in rows if r.get('mode')==2));row.update(changes)
            with self.assertRaises(ValueError):runtime.encode_packet([row])
        with self.assertRaises(ValueError):runtime.encode_packet(rows+rows)

    def test_composition_retains_existing_choices_and_translation_only_output(self):
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(PACKET_OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),128)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin

    def test_new_non_parent_rigs_preserve_parent_aliases_and_native_profiles(self):
        import v3_display_aliases as aliases
        from v3_furniture_install import profile
        self.assertEqual(aliases.records(self.report,self.blob),aliases.records(self.prior,self.old_blob))
        for row in self.r['rows']:
            if row.get('mode')!=2:continue
            generated=copy.deepcopy(row['source'])
            generated['room_runtime']=dict(vtable=runtime.VTABLE,vrom=row['vrom'])
            native=profile(generated,row['vrom'])
            self.assertEqual(native[16:48],bytes(32))
            self.assertEqual(native[48:64],bytes.fromhex(generated['native_profile_scalar_hex']))
            self.assertEqual(struct.unpack_from('>I',native,64)[0],runtime.VTABLE)
            del generated['room_runtime']
            with self.assertRaises(ValueError):profile(generated,row['vrom'])


class BehaviourTests(unittest.TestCase):
    def test_extended_categories_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-categories-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_room_categories_test.c'),
                '-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('dispatch, time, limits, and actor guards',result.stdout)

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
