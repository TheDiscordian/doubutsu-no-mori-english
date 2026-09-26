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
PROFILE_OUT=ROOT/os.environ.get('V3_ROOM_PROFILE_BUILD','build/v3-shared-room-profiles-02')


class CurrentImportedRigTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_IMPORTED_RIG_BUILD','build/v3-rolling-category-auto-02/cartridge')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.rows=cls.report['automatic_furniture']['imports']

    def test_imported_category_keeps_rig_audio_profiles_and_reuses_assets(self):
        from v3_furniture_rigs import HIT_CATEGORY,BILLBOARD_CATEGORY,ROLLING_CATEGORY
        from v3_furniture_pipeline import prepare
        from v3_furniture_install import profile
        r=self.report;e=r['equipment_resources'];rigs=e['room_rigs'];bindings=runtime.bind_profiles(self.source,self.image,r)
        self.assertTrue(self.rows)
        for row in self.rows:
            donor=row.get('donor_item_id',row['item_id']);descriptor=prepare(self.source,int(donor,16))[0]
            category=descriptor['callback_adapter']['category']
            self.assertIn(category,(HIT_CATEGORY,BILLBOARD_CATEGORY,ROLLING_CATEGORY))
            rig=next(x for x in rigs['rows'] if x['source_item_id']==donor)
            self.assertTrue(rig['parent_selectable'])
            if category==HIT_CATEGORY:
                sound=next(x for x in rigs['sound_rows'] if x['source_item_id']==donor)
                audio=next(x for x in e['furniture_audio']['furniture'] if x['item_id']==donor)
                self.assertEqual(rig['mode'],3)
                self.assertTrue(sound['profile_installed']);self.assertTrue(sound['parent_selectable'])
                self.assertEqual(audio['trigger'],json.loads(json.dumps(descriptor['callback_adapter']['trigger'])))
                self.assertEqual(audio['trigger']['sound_word'],sound['source_sound_word'])
            elif category==BILLBOARD_CATEGORY:
                audio=next(x for x in e['furniture_level_audio']['furniture'] if x['item_id']==donor)
                self.assertEqual(rig['mode'],4)
                self.assertEqual(audio['lifecycle'],descriptor['callback_adapter']['level_sound'])
                self.assertEqual(rigs['billboard_contract'],runtime.billboard_contract(self.image,r))
            else:
                self.assertEqual(rig['mode'],5)
                self.assertEqual(rigs['motion_contract'],runtime.motion_binding(self.source,self.image,r,rigs['rows']))
            self.assertEqual(row['object_sha256'],rig['sha256'])
            at=rig['blob_offset'];self.assertEqual(sha256(self.blob[at:at+rig['bytes']]),rig['sha256'])
            i=slot(int(row['item_id'],16));native=profile(row,rig['vrom'],limit=r['import_storage']['virtual_limit'])
            self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],
                struct.pack('>HHI',row['runtime_index'],int(row['item_id'],16),1)+native+bytes(4))
            self.assertFalse(bindings[donor]['staged'])
            self.assertIn(row['id']+'/name',{x['id'] for x in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']})
        ram,table,size=runtime.packet_layout(rigs)
        self.assertEqual(rigs['packet']['bytes'],size)
        self.assertLessEqual(rigs['code']['bytes'],table-ram)
        self.assertEqual(self.report['save_codec']['format_version'],4)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_private_browser_selection_matches_offline_and_keeps_translation_only(self):
        import v3_browser_composition as browser
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json')
            catalog=composer.catalogue(self.image,self.report);plan=browser.rules(self.image,self.report)
            keys=[r['id'] for r in self.rows];self.assertTrue(set(keys)<=catalog.keys())
            self.assertFalse(plan['web_patcher_enabled']);cases=[]
            for name,requested in (('none',[]),('all',list(catalog)),('new-category',keys),
                    ('existing-villager',['GAFE01-r0/villager/00EB'])):
                selection=composer.resolve(catalog,requested)
                image,_,blob=composer.compose(self.image,self.report,catalog,selection)
                if name=='none':self.assertEqual(sha256(image),self.report['translation_baseline']['sha256'])
                elif name=='all':self.assertEqual(image,self.image)
                if requested:
                    for row in self.rows:
                        i=slot(int(row['item_id'],16));active=row['id'] in selection['enabled']
                        self.assertEqual(struct.unpack_from('>I',blob,ROWS+i*80+4)[0],active)
                        self.assertEqual(bool(blob[0x40+i//8]&(1<<(i&7))),active)
                cases.append(dict(name=name,requested=requested,selection=selection,sha256=sha256(image)))
            with tempfile.TemporaryDirectory(prefix='v3-rig-composition-') as directory:
                path=Path(directory)/'fixture.json'
                path.write_bytes(composer.canonical(dict(plan=plan,cases=cases,
                    base=str(self.out/'animal-forest-v3-asset-loader.z64'),stable=str(composer.stable_reference(self.report)[0]))))
                result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(path)],
                    check=True,capture_output=True,text=True,timeout=90)
                self.assertEqual(len(json.loads(result.stdout)['passed']),4)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


class FixedClockIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'build/v3-shared-fixed-clock-profiles-01'
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-shared-translucent-imports-01/cartridge/build-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.old=by_vrom(cls.base)[BLOB].extract(cls.base)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_fixed_and_indexed_clocks_share_complete_semantics_and_reject_changes(self):
        from v3_furniture_rigs import CLOCK_CATEGORY
        source=self.source;profile=source.profile(0x32F0);a=profile['callback_adapter']
        self.assertEqual(a['category'],CLOCK_CATEGORY);self.assertEqual(a['pending_callbacks'],[])
        self.assertEqual(a['runtime_contract']['source_initial_speed'],.5)
        self.assertEqual(a['runtime_contract']['source_move_steps_per_native_update'],2)
        self.assertEqual(a['clock'],source.profile(0x30A8)['callback_adapter']['clock'])
        for row in [a['functions'][k] for k in ('move','destroy')]+[a['runtime_contract']['source_initializer']]:
            changed=copy.copy(source);changed.rel=bytearray(source.rel)
            changed.rel[source.sections[1][0]+row['offset']]^=1
            with self.assertRaises(ValueError):changed.profile(0x32F0)
        for at in (0,4,0x20,0x30):
            changed=copy.copy(source);changed.rel=bytearray(source.rel)
            changed.rel[source.sections[4][0]+at]^=1
            with self.assertRaisesRegex(ValueError,'repeat initialization'):changed.profile(0x32F0)
        changed=copy.copy(source);changed.code_relocations=dict(source.code_relocations)
        del changed.code_relocations[0xA24+0x0A]
        with self.assertRaisesRegex(ValueError,'repeat initialization'):changed.profile(0x32F0)

    def test_new_clock_reuses_complete_art_and_runtime_without_changing_other_records(self):
        from v3_furniture_pipeline import PreparedAssets,prepare
        art=ROOT/'build/v3-shared-fixed-clock-prepared-01';manifest=json.loads((art/'art.json').read_bytes())
        self.assertEqual(manifest['batch'],dict(objects=1,reused=1,compiled=0,compiler_containers=0))
        self.assertEqual([r['item_id'] for r in manifest['objects']],['32F0'])
        self.assertEqual(PreparedAssets(self.source,[ROOT/'build/v3-fixed-keyframe-rigs-prepared-01']).reuse(
            self.source,'32F0',prepare(self.source,0x32F0))[1]['object_sha256'],manifest['objects'][0]['object_sha256'])
        e=self.report['equipment_resources'];r=e['room_rigs'];old=self.prior['equipment_resources']['room_rigs']
        self.assertEqual(r['code']['sha256'],old['code']['sha256'])
        self.assertEqual(r['code']['bytes'],old['code']['bytes'])
        self.assertEqual(len(r['rows']),26);self.assertEqual(len(self.report['staged_furniture']['rows']),23)
        self.assertEqual([v for v in r['rows'] if v['source_item_id']!='32F0'],old['rows'])
        self.assertEqual([v for v in self.report['staged_furniture']['rows'] if v['item_id']!='32F0'],
                         self.prior['staged_furniture']['rows'])
        row=next(v for v in r['rows'] if v['source_item_id']=='32F0')
        self.assertEqual((row['mode'],row['first'],row['last'],row['joints'],row['shown']),(1,3,4,5,3))
        data=(art/manifest['objects'][0]['object_file']).read_bytes();at=row['blob_offset']
        self.assertEqual(self.blob[at:at+row['bytes']],data);self.assertEqual(len(data),3744)
        table=runtime.encode_packet(r['rows'],r['sound_rows']);packet=r['packet']
        self.assertEqual(self.blob[packet['blob_offset']+runtime.PACKET_TABLE-runtime.PACKET_RAM:
                                  packet['blob_offset']+packet['bytes']],table)
        from v3_import_storage import TABLE_END
        expected=bytearray(self.old[ROWS:TABLE_END]);i=slot(0x32F0)
        for first,size in ((ROWS+i*80,80),(ITEMS+i*32,32)):
            expected[first-ROWS:first-ROWS+size]=self.blob[first:first+size]
        self.assertEqual(self.blob[ROWS:TABLE_END],expected)
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)
        self.assertEqual(e['furniture_audio'],self.prior['equipment_resources']['furniture_audio'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_staged_readers_reach_acquisition_without_enabling_or_changing_composition(self):
        from v3_furniture_pipeline import prepare,metadata,identity_rows
        bindings=runtime.bind_profiles(self.source,self.image,self.report)
        self.assertIn('32F0',bindings)
        row=next(r for r in self.report['staged_furniture']['rows'] if r['item_id']=='32F0')
        self.assertTrue(row['profile_installed']);self.assertTrue(row['item_record_installed'])
        self.assertFalse(any(row[k] for k in ('selected','acquisition_installed','catalogue_installed','scoring_installed')))
        i=slot(0x32F0);self.assertFalse(self.blob[0x40+i//8]&(1<<(i&7)))
        self.assertEqual(self.blob[ROWS+i*80+4:ROWS+i*80+8],bytes(4))
        self.assertEqual(self.blob[ITEMS+i*32+8:ITEMS+i*32+24],b'harvest clock   ')
        ids=identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        with self.assertRaisesRegex(ValueError,'acquisition needs an adapter: ftr_listHarvest'):
            metadata(self.source,0x32F0,prepare(self.source,0x32F0)[0],ids[0x32F0])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),136);self.assertNotIn('GAFE01-r0/item/32F0',catalog)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


class ProfileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(PROFILE_OUT/'build-lock.json')
        cls.base,cls.prior=inputs(PROFILE_OUT/'base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.old=by_vrom(cls.base)[BLOB].extract(cls.base)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.rows=cls.report['staged_furniture']['rows']
        cls.bindings=runtime.bind_profiles(cls.source,cls.image,cls.report)

    def test_complete_inactive_batch_retains_every_previous_record_and_resource(self):
        from v3_import_storage import TABLE_END
        self.assertEqual(len(self.rows),22)
        self.assertEqual(sum(r['reused_asset'] for r in self.rows),17)
        expected=bytearray(self.old[ROWS:TABLE_END]);e=self.report['equipment_resources'];old=self.prior['equipment_resources']
        for r in self.rows:
            item=int(r['item_id'],16);i=slot(item);vrom=r['object_vrom'];at=vrom-BLOB;n=r['object_bytes']
            self.assertEqual(sha256(self.blob[at:at+n]),r['object_sha256'])
            if r['reused_asset']:self.assertEqual(self.blob[at:at+n],self.old[at:at+n])
            profile=self.blob[ROWS+i*80:ROWS+(i+1)*80];record=self.blob[ITEMS+i*32:ITEMS+(i+1)*32]
            self.assertEqual(profile,struct.pack('>HHI',r['runtime_index'],item,0)+bytes.fromhex(r['profile_hex'])+bytes(4))
            self.assertEqual(record,struct.pack('>HHHBB',r['runtime_index'],item,r['price'],r['size_code'],0)+r['name'].encode().ljust(16,b' ')+bytes(8))
            self.assertFalse(self.blob[0x40+i//8]&(1<<(i&7)))
            self.assertFalse(any(r[k] for k in ('selected','acquisition_installed','catalogue_installed','scoring_installed')))
            expected[i*80:(i+1)*80]=profile
            expected[ITEMS-ROWS+i*32:ITEMS-ROWS+(i+1)*32]=record
        self.assertEqual(self.blob[ROWS:TABLE_END],expected)
        self.assertEqual(self.blob[e['blob_offset']:e['blob_offset']+e['bytes']],self.old[old['blob_offset']:old['blob_offset']+old['bytes']])
        self.assertEqual(e['room_rigs']['packet'],old['room_rigs']['packet'])
        self.assertEqual(e['furniture_audio'],old['furniture_audio'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)
        from aflib import DMA_START
        files,previous=by_vrom(self.image),by_vrom(self.base)
        for v,entry in files.items():
            if v in (BLOB,MODULE):continue
            expected=bytearray(previous[v].extract(self.base))
            if entry.vstart<=DMA_START<entry.vend:
                for changed in [BLOB]+[r['vrom'] for r in self.report['shared_runtime_refresh']['unchanged_owner_moves']]:
                    e=files[changed];at=DMA_START+e.index*16-entry.vstart
                    struct.pack_into('>4I',expected,at,e.vstart,e.vend,e.pstart,e.pend)
            self.assertEqual(entry.extract(self.image),expected,hex(v))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(PROFILE_OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_current_metadata_advances_to_real_acquisition_gaps_and_promotes_without_copying(self):
        from v3_furniture_pipeline import prepare,metadata,identity_rows
        from v3_resource_capacity import checked_limit
        ids=identity_rows(ROOT/'build/item-identity-megasheet.xlsx');limit=checked_limit(self.image,self.report)
        rigs=self.report['equipment_resources']['room_rigs'];bindings={r['source_item_id']:r for r in rigs['rows']+rigs['sound_rows']}
        for r in self.rows:
            item=int(r['item_id'],16)
            with self.assertRaisesRegex(ValueError,'^acquisition needs an adapter:'):
                metadata(self.source,item,prepare(self.source,item)[0],ids[item])
            row={**bindings[r['item_id']]['source'],**r};at=r['object_vrom']-BLOB;asset=self.blob[at:at+r['object_bytes']]
            self.assertEqual(runtime.reuse_profile(self.source,row,asset,self.blob,limit=limit),
                (r['object_vrom'],bytes.fromhex(r['profile_hex'])))
        row=copy.deepcopy(row);row['room_runtime']['vtable']+=4
        with self.assertRaises(ValueError):runtime.reuse_profile(self.source,row,asset,self.blob,limit=limit)
        bad=copy.deepcopy(self.report);bad['staged_furniture']['rows'][0]['room_runtime']['vrom']+=16
        with self.assertRaises(ValueError):runtime.bind_profiles(self.source,self.image,bad)
        runtime.bind_profiles(self.source,self.image,self.report)

    def test_single_artwork_validator_still_accepts_current_installed_static_batch(self):
        from v3_furniture_install import checked_assets,provenance_patch
        rows,_=checked_assets(ROOT/self.report['automatic_furniture']['art_directory'],self.source,ROOT/'build/item-identity-megasheet.xlsx')
        self.assertTrue(rows)
        self.assertEqual(provenance_patch(self.rows),'')

    def test_composition_retains_choices_and_complete_translation_only_output(self):
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(PROFILE_OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),128)
            self.assertFalse({r['id'] for r in self.rows}&set(catalog))
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


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
            self.assertIn('dispatch, time, limits, sound, and actor guards',result.stdout)

    def test_billboard_category_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-billboards-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_room_billboards_test.c'),
                '-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('bounded immutable frames',result.stdout)

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
