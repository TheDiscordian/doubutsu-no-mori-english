"""Complete rig resources, real bank owners, retained imports, and checked readers."""
import copy
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
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,sha256
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
import v3_equipment_runtime as equipment
import v3_optional_composition as composer

OUTPUT=ROOT/'build/v3-equipment-rigs-02'


class RigReaderTests(unittest.TestCase):
    def test_original_and_expanded_readers_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-rig-readers-') as directory:
            for capacity in (None,5248,7168):
                target=str(Path(directory)/str(capacity))
                flags=['-DAF_V3_PLAYER_MOTION','-DAF_V3_EQUIPMENT_KINDS']
                if capacity:flags+=['-DAF_V3_EQUIPMENT_RIGS',f'-DAF_V3_EQUIPMENT_CAPACITY={capacity}u']
                subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',*flags,
                    str(ROOT/'tests/v3_equipment_resources_test.c'),'-o',target],
                    check=True,capture_output=True,timeout=30)
                subprocess.run([target],check=True,capture_output=True,timeout=10)


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current rig cartridge required')
class RigCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUTPUT/'build-lock.json')
        cls.before,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.old_files=by_vrom(cls.image),by_vrom(cls.before)
        cls.equipment=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old_blob=cls.old_files[BLOB].extract(cls.before)

    def test_complete_rigs_all_original_resources_and_native_kind_bindings(self):
        source=equipment.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        rigs=self.equipment['animated_rigs']
        assets,rows,evidence=equipment.prepared_rigs(source,ROOT/rigs['evidence']['art_directory'])
        self.assertEqual(evidence,rigs['evidence']);self.assertEqual(len(rows),8)
        installed={r['source_index']:r for r in self.equipment['records']}
        self.assertEqual(len(installed),38)
        for old in self.old['records']:
            self.assertEqual(installed[old['source_index']],old)
            at=old['blob_offset'];self.assertEqual(self.blob[at:at+old['bytes']],self.old_blob[at:at+old['bytes']])
        module=self.blob[self.equipment['blob_offset']:self.equipment['blob_offset']+self.equipment['bytes']]
        for row in rows:
            actual=installed[row['source_index']]
            self.assertEqual(row,{k:v for k,v in actual.items() if k not in ('vrom','blob_offset')})
            at=actual['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],assets[row['source_index']])
            self.assertEqual(struct.unpack_from('>4I',module,equipment.TABLE+16+row['source_index']*16),
                tuple(actual[k] for k in ('vrom','bytes','pointer','type')))
        changes=0
        for before,after in zip(self.old['kind_readers']['rows'],self.equipment['kind_readers']['rows']):
            if before==after:continue
            changes+=1;self.assertFalse(after['selectable']);self.assertFalse(after['player_actions_installed'])
            self.assertTrue(after['shape_installed'] and after['resource_ready'])
            shape,animation=(installed[after[k]] for k in ('shape','animation'))
            self.assertEqual(after['fields'][2:4],[shape['index'],animation['index']])
            self.assertEqual(after['combined_bank_bytes'],shape['bytes']+animation['bytes'])
            self.assertLessEqual(after['combined_bank_bytes'],5248)
        self.assertEqual(changes,8)
        self.assertEqual(self.equipment['player_actions'],self.old['player_actions'])
        self.assertEqual(self.equipment['inventory_preview'],self.old['inventory_preview'])

    def test_native_bank_growth_exact_references_and_unrelated_resources(self):
        allocation=self.equipment['animated_rigs']['allocation']
        self.assertEqual((allocation['bank_bytes'],allocation['banks'],allocation['additional_scene_bytes']),
                         (5248,2,1728))
        self.assertEqual(allocation['inventory_bank_bytes'],15584)
        core=bytearray(self.files[CODE_VROM].extract(self.image));old_core=self.old_files[CODE_VROM].extract(self.before)
        for patch in allocation['patches']:
            at=patch['address']-CODE_RAM;after=bytes.fromhex(patch['after']);before=bytes.fromhex(patch['before'])
            self.assertEqual(core[at:at+len(after)],after);self.assertEqual(old_core[at:at+len(before)],before)
            core[at:at+len(before)]=before
        for hooks in (self.equipment['hooks'],self.equipment['player_motion']['hooks']):
            for hook in hooks:
                at=hook['entry']-CODE_RAM
                self.assertEqual(core[at:at+8].hex(),hook['after']);core[at:at+8]=bytes.fromhex(hook['before'])
        self.assertEqual(core,old_core)
        owner=bytearray(self.files[equipment.PLAYER_VROM].extract(self.image))
        for patch in self.equipment['animated_rigs']['owner_patches']:
            at=patch['address']-equipment.PLAYER_RAM
            self.assertEqual(owner[at:at+4].hex(),patch['after']);owner[at:at+4]=bytes.fromhex(patch['before'])
        for hooks in (self.equipment['player_motion']['owner_hooks'],self.equipment['kind_readers']['owner_hooks']):
            for hook in hooks:
                at=hook['entry']-equipment.PLAYER_RAM;n=hook['end']-hook['entry']
                self.assertEqual(owner[at:at+n].hex(),hook['after']);owner[at:at+n]=bytes.fromhex(hook['before'])
        self.assertEqual(owner,self.old_files[equipment.PLAYER_VROM].extract(self.before))
        changed={CODE_VROM,MODULE,BLOB,equipment.PLAYER_VROM,0x19D40}
        self.assertEqual(set(self.files),set(self.old_files))
        for v in set(self.files)-changed:
            self.assertEqual(self.files[v].extract(self.image),self.old_files[v].extract(self.before),hex(v))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        damaged=bytearray(old_core);damaged[0x800C6628-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'bank owner'):
            equipment.grow_banks(original,damaged,owner,5248)
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.image)

    def test_reservation_guards_state_and_future_tail_reuse(self):
        current=self.equipment;old=self.old
        module=bytearray(self.blob[current['blob_offset']:current['blob_offset']+current['bytes']])
        before=self.old_blob[old['blob_offset']:old['blob_offset']+old['bytes']]
        self.assertEqual(current['bytes'],old['bytes']);self.assertEqual(sha256(module),current['sha256'])
        self.assertEqual(zlib.crc32(module),current['crc32'])
        self.assertEqual(struct.unpack_from('>4I',module,len(module)-16),(equipment.GUARD,)*4)
        module[:equipment.KIND_TABLE]=before[:equipment.KIND_TABLE]
        for row in current['records']:
            if row['type']==1:
                at=equipment.TABLE+16+row['source_index']*16;module[at:at+16]=before[at:at+16]
        for row in current['kind_readers']['rows']:
            if row['shape'] in {r['source_index'] for r in current['records'] if r['type']==1}:
                at=equipment.KIND_TABLE+16+row['source_kind']*equipment.KIND_STRIDE
                module[at:at+equipment.KIND_STRIDE]=before[at:at+equipment.KIND_STRIDE]
        self.assertEqual(module,before)
        for key in ('save_runtime','furniture','translation_baseline','translation_updates'):
            self.assertEqual(self.report[key],self.prior[key])
        stripped,_=reuse_resource_tail(self.image,self.report,self.blob)
        self.assertGreaterEqual(len(stripped),current['blob_offset']+current['bytes'])

    def test_optional_choices_profiles_and_translation_only_remain_unchanged(self):
        pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json')
            catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),112)
            self.assertFalse(any(f'GAFE01-r0/item/{i:04X}' in catalog for i in range(0x224C,0x2254)))
            empty=composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]
            self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])
            all_items=composer.resolve(catalog,list(catalog))
            self.assertEqual(composer.compose(self.image,self.report,catalog,all_items)[0],self.image)
            self.assertEqual(all_items['profile_hex'],self.prior['save_runtime']['profile_hex'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


EXPANDED=ROOT/'build/v3-rig-capacity-03'


@unittest.skipUnless((EXPANDED/'build-lock.json').is_file(),'Expanded rig cartridge required')
class ExpandedRigCategoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(EXPANDED/'build-lock.json')
        cls.before,cls.prior=inputs(EXPANDED/'base-lock.json')
        cls.files,cls.old_files=by_vrom(cls.image),by_vrom(cls.before)
        cls.current=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.blob=cls.files[BLOB].extract(cls.image);cls.old_blob=cls.old_files[BLOB].extract(cls.before)
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()

    def test_complete_categories_and_every_retained_resource(self):
        source=equipment.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        extension=self.current['animated_rigs']['extensions'][-1]
        assets,rows,evidence=equipment.prepared_rigs(source,ROOT/extension['evidence']['art_directory'],
            categories=tuple(extension['source_categories']),joint_work_vectors=8)
        self.assertEqual(evidence,extension['evidence']);self.assertEqual(len(rows),12)
        installed={r['source_index']:r for r in self.current['records']}
        self.assertEqual(set(installed),set(range(50)))
        self.assertEqual(sum(r['type']==1 for r in installed.values()),20)
        for old in self.old['records']:
            self.assertEqual(installed[old['source_index']],old)
            at=old['blob_offset'];self.assertEqual(self.blob[at:at+old['bytes']],self.old_blob[at:at+old['bytes']])
        for row in rows:
            actual=installed[row['source_index']];at=actual['blob_offset']
            self.assertEqual(row,{k:v for k,v in actual.items() if k not in ('vrom','blob_offset')})
            self.assertEqual(self.blob[at:at+row['bytes']],assets[row['source_index']])
        self.assertEqual(self.current['inventory_preview'],self.old['inventory_preview'])
        for key in ('save_runtime','furniture','translation_baseline','translation_updates'):
            self.assertEqual(self.report[key],self.prior[key])

    def test_exact_bank_player_growth_and_unrelated_cartridge_retention(self):
        allocation=self.current['animated_rigs']['allocation'];old=self.old['animated_rigs']['allocation']
        self.assertEqual((allocation['bank_bytes'],allocation['incremental_scene_bytes']),(7168,3840))
        self.assertEqual((allocation['scene_arena_bytes'],allocation['additional_scene_bytes']),(0x949C0,5568))
        core=bytearray(self.files[CODE_VROM].extract(self.image))
        old_core=self.old_files[CODE_VROM].extract(self.before)
        for patch,prior in zip(allocation['patches'],old['patches']):
            self.assertEqual(patch['address'],prior['address']);at=patch['address']-CODE_RAM
            self.assertEqual(core[at:at+len(bytes.fromhex(patch['after']))].hex(),patch['after'])
            core[at:at+len(bytes.fromhex(prior['after']))]=bytes.fromhex(prior['after'])
        work=self.current['player_joint_work']
        self.assertEqual((work['vectors'],work['joint_offset'],work['morph_offset'],work['player_bytes']),
                         (8,0x1310,0x1340,0x1370))
        self.assertEqual(struct.unpack_from('>I',core,0x8010BCEC-CODE_RAM)[0],work['player_bytes'])
        struct.pack_into('>I',core,0x8010BCEC-CODE_RAM,work['previous_player_bytes'])
        self.assertEqual(core,old_core)
        owner=bytearray(self.files[equipment.PLAYER_VROM].extract(self.image))
        for patch in work['patches']:
            at=patch['address']-equipment.PLAYER_RAM
            self.assertEqual(struct.unpack_from('>I',owner,at)[0],patch['after'])
            struct.pack_into('>I',owner,at,patch['before'])
        self.assertEqual(owner,self.old_files[equipment.PLAYER_VROM].extract(self.before))
        self.assertEqual(len(work['patches']),4)
        self.assertFalse(work['save_format_changed'] or work['inventory_joint_work_changed'])
        self.assertEqual(set(self.files),set(self.old_files))
        for v in set(self.files)-{CODE_VROM,MODULE,BLOB,equipment.PLAYER_VROM,0x19D40}:
            self.assertEqual(self.files[v].extract(self.image),self.old_files[v].extract(self.before),hex(v))
        self.assertEqual(apply_ups(self.native,(EXPANDED/'asset-loader.ups').read_bytes()),self.image)

    def test_checked_player_growth_rejects_changed_consumers_and_can_extend_again(self):
        owner=self.old_files[equipment.PLAYER_VROM].extract(self.before)
        core=self.old_files[CODE_VROM].extract(self.before)
        rel=self.old_files[equipment.PLAYER_RELOC].extract(self.before)
        allocation=self.old['held_rig_actions']['player_allocation']
        actual=equipment.grow_player_joint_work(self.native,bytearray(core),bytearray(owner),rel,allocation,8)
        self.assertEqual(actual,self.current['player_joint_work'])
        for where in ('profile','initializer','extra-reference'):
            c,o=bytearray(core),bytearray(owner)
            if where=='profile':c[0x8010BCE0-CODE_RAM]^=1
            if where=='initializer':o[0x808BD934-equipment.PLAYER_RAM]^=1
            if where=='extra-reference':struct.pack_into('>I',o,0,0x26240A88)
            with self.assertRaises(ValueError):equipment.grow_player_joint_work(self.native,c,o,rel,allocation,8)
        c=bytearray(self.files[CODE_VROM].extract(self.image));o=bytearray(self.files[equipment.PLAYER_VROM].extract(self.image))
        bigger=equipment.grow_player_joint_work(self.native,c,o,rel,
            self.current['held_rig_actions']['player_allocation'],9,actual)
        self.assertEqual((bigger['joint_offset'],bigger['morph_offset'],bigger['array_bytes'],bigger['player_bytes']),
                         (0x1310,0x1346,54,0x1380))

    def test_reuses_only_hash_bound_retired_space_and_keeps_current_module(self):
        reuse=self.current['animated_rigs']['extensions'][-1]['retired_module_reuse']
        self.assertEqual(equipment.retired_module_space(self.before,self.prior,self.old_blob,46976),reuse)
        at=reuse['blob_offset'];size=reuse['bytes']
        self.assertEqual(sha256(self.old_blob[at:at+size]),reuse['retired_module_sha256'])
        self.assertEqual((len(self.blob),self.current['blob_offset'],self.current['bytes']),
                         (len(self.old_blob),self.old['blob_offset'],self.old['bytes']))
        mutated=bytearray(self.old_blob);mutated[at]^=1
        other=equipment.retired_module_space(self.before,self.prior,mutated,46976)
        self.assertTrue(other is None or other['blob_offset']!=at)
        changed=copy.deepcopy(self.prior);changed['new_live_resource']={'blob_offset':at,'bytes':size}
        other=equipment.retired_module_space(self.before,changed,self.old_blob,46976)
        self.assertTrue(other is None or other['blob_offset']!=at)
        changed=copy.deepcopy(self.prior);changed['shared_runtime_refresh']['base']['report_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'predecessor'):equipment.retired_module_space(self.before,changed,self.old_blob,46976)
        module_at=self.current['blob_offset'];module=bytearray(self.blob[module_at:module_at+self.current['bytes']])
        old=self.old_blob[module_at:module_at+self.old['bytes']]
        self.assertEqual(sha256(module),self.current['sha256'])
        self.assertEqual(zlib.crc32(module),self.current['crc32'])
        self.assertEqual(self.current['code']['symbols'],self.old['code']['symbols'])
        self.assertEqual(struct.unpack_from('>4I',module,len(module)-16),(equipment.GUARD,)*4)
        module[:equipment.KIND_TABLE]=old[:equipment.KIND_TABLE]
        added=set(self.current['animated_rigs']['extensions'][-1]['source_indices'])
        for i in added:
            at=equipment.TABLE+16+i*16;module[at:at+16]=old[at:at+16]
        for row in self.current['kind_readers']['rows']:
            if row['shape'] in added:
                at=equipment.KIND_TABLE+16+row['source_kind']*equipment.KIND_STRIDE
                module[at:at+equipment.KIND_STRIDE]=old[at:at+equipment.KIND_STRIDE]
                self.assertFalse(row['selectable'] or row['player_actions_installed'])
        self.assertEqual(module,old)

    def test_optional_profile_and_translation_only_stay_unchanged(self):
        pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        try:
            composer.use_build_lock(EXPANDED/'build-lock.json')
            catalogue=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalogue),120)
            empty=composer.compose(self.image,self.report,catalogue,composer.resolve(catalogue,[]))[0]
            self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])
            selection=composer.resolve(catalogue,list(catalogue))
            self.assertEqual(selection['profile_hex'],self.prior['save_runtime']['profile_hex'])
            self.assertEqual(composer.compose(self.image,self.report,catalogue,selection)[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


if __name__=='__main__':unittest.main()
