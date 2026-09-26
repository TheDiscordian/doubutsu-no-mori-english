"""Shared indexed room-rig discovery, complete conversion, and install boundary."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
import v3_furniture_pipeline as pipeline
import v3_furniture_rigs as rigs
import v3_keyframes as keyframes
import v3_furniture_install as install
from tests import test_v3_furniture_pipeline as furniture_tests

OUTPUT = ROOT/'build/v3-indexed-room-rigs-prepared-01'
CLOCK_OUTPUT = ROOT/'build/v3-indexed-clock-rigs-prepared-01'
STORAGE_OUTPUT = ROOT/'build/v3-storage-rigs-prepared-01'
FIXED_OUTPUT = ROOT/'build/v3-fixed-keyframe-rigs-prepared-01'


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.aliases = [r for r in pipeline.room_aliases(cls.source)['rows'] if r['category']=='balloon']

    def test_complete_category_crosses_source_ranges_without_native_identity_assignment(self):
        self.assertEqual(len(self.aliases),8)
        profiles = [self.source.profile(int(r['display_item_id'],16)) for r in self.aliases]
        self.assertEqual({r['callback_adapter']['selected_index'] for r in profiles},set(range(8)))
        self.assertEqual({r['callback_adapter']['index_origin'] for r in profiles},{1020})
        for row in profiles:
            self.assertEqual(row['kind'],'animated-room-model')
            adapter = row['callback_adapter']
            self.assertEqual(adapter['category'],rigs.CATEGORY)
            self.assertEqual((row['skeleton']['joints'],row['skeleton']['shown_joints']),(6,5))
            self.assertEqual(adapter['animation']['duration'],61)
            self.assertFalse(adapter['runtime_installed'])
            self.assertEqual(set(adapter['functions']),{'create','move','draw','destroy'})
            self.assertEqual(len(adapter['joint_callbacks']),2)
            self.assertEqual(len(row['models']),5)
        worksheet = ROOT/'build/item-identity-megasheet.xlsx'
        defaults = pipeline.identity_rows(worksheet)
        self.assertNotIn(0x1FF0,defaults)
        extra = {int(r['display_item_id'],16) for r in self.aliases}
        identities = pipeline.identity_rows(worksheet,extra_items=extra)
        self.assertEqual(set(identities)-set(defaults),{0x1FF0,0x1FF4,0x1FF8,0x1FFC})
        for alias in self.aliases:
            item = int(alias['display_item_id'],16)
            name = pipeline.name_metadata(self.source,item,identities[item])
            self.assertEqual(name['name'],alias['parent_name'])
            self.assertEqual(name['name_sha256'],alias['parent_name_sha256'])
            with self.assertRaises(pipeline.ReviewRequired):
                pipeline.metadata(self.source,item,self.source.profile(item),identities[item])
        for bad in (True,0x1FF1,0x2000,0x2FFC,0x33C8):
            with self.assertRaises(ValueError):pipeline.furniture_source_index(bad)

    def test_full_callback_code_and_relocated_dependencies_are_required(self):
        profile = self.source.profile(0x1FF0); adapter = profile['callback_adapter']
        for role,row in adapter['functions'].items():
            source = copy.copy(self.source); source.rel = bytearray(source.rel)
            source.rel[source.sections[1][0]+row['offset']] ^= 1
            with self.subTest(role=role), self.assertRaises(ValueError):source.profile(0x1FF0)
        for role,row in adapter['functions'].items():
            source = copy.copy(self.source); source.code_relocations = dict(source.code_relocations)
            source.code_relocations[row['offset']+2] = (4,1,5,0)
            with self.subTest(dependencies=role), self.assertRaises(ValueError):source.profile(0x1FF0)
        for row in adapter['joint_callbacks']:
            source = copy.copy(self.source); source.rel = bytearray(source.rel)
            source.rel[source.sections[1][0]+row['offset']+3] = 0
            with self.assertRaisesRegex(ValueError,'joint callback'):source.profile(0x1FF0)
        for constant in adapter['constants'].values():
            source = copy.copy(self.source); source.rel = bytearray(source.rel)
            source.rel[source.sections[constant['section']][0]+constant['offset']] ^= 1
            with self.assertRaisesRegex(ValueError,'speed constant'):source.profile(0x1FF0)
        for table in adapter['tables'].values():
            source = copy.copy(self.source); source.relocations = dict(source.relocations)
            del source.relocations[table['offset']+4]
            source.relocation_addresses = sorted(source.relocations)
            with self.assertRaisesRegex(ValueError,'incomplete rig table'):source.profile(0x1FF0)
        for index in (1019,1028):
            with self.assertRaisesRegex(ValueError,'selector index'):
                self.source.callback_models(profile['profile_offset'],index)

    def test_animation_suffix_offsets_keep_complete_arrays_and_native_pointers(self):
        motion = self.source.profile(0x1FF0)['callback_adapter']['animation']
        plain,original = keyframes.compile_animations(self.source,[motion])
        shifted,report = keyframes.compile_animations(self.source,[motion],start=0x2000)
        expected = bytearray(plain)
        for r in original['relocations']:
            struct.pack_into('>I',expected,r['offset'],0x06002000+r['target_offset'])
        self.assertEqual(shifted,expected)
        self.assertEqual(len(shifted),len(plain))
        for a,b in zip(original['arrays']+original['headers'],report['arrays']+report['headers']):
            self.assertEqual(b['native_offset'],a['native_offset']+0x2000)
            self.assertEqual(b['source_sha256'],a['source_sha256'])
        for bad in (-16,1,0x1000000,True):
            with self.assertRaises(ValueError):keyframes.compile_animations(self.source,[motion],start=bad)


class HitResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_shared_source_category_keeps_complete_motion_models_and_audio(self):
        from v3_sound_programs import furniture_trigger
        for item,joints,sound in ((0x3350,2,0x176),(0x3354,3,0x175)):
            row=pipeline.prepare(self.source,item);profile=row[0];adapter=profile['callback_adapter']
            self.assertEqual(adapter['category'],rigs.HIT_CATEGORY)
            self.assertEqual(profile['skeleton']['joints'],joints)
            self.assertEqual(len(profile['models']),joints)
            self.assertEqual(adapter['animation']['joints'],joints)
            self.assertEqual(adapter['trigger']['sound_word'],sound)
            self.assertEqual(furniture_trigger(self.source,profile),adapter['trigger'])
            self.assertEqual(set(adapter['functions']),{'create','move','draw'})
            self.assertTrue(adapter['constructor']['clears_switch_pulse'])
            with self.assertRaisesRegex(ValueError,'Animated room lifecycle'):
                pipeline.metadata(self.source,item,profile,None)

    def test_changed_code_constants_sound_and_paired_resources_reject(self):
        adapter=self.source.profile(0x3354)['callback_adapter']
        for row in adapter['functions'].values():
            changed=copy.copy(self.source);changed.rel=bytearray(changed.rel)
            changed.rel[changed.sections[1][0]+row['offset']]^=1
            with self.assertRaises(ValueError):changed.profile(0x3354)
        for row in adapter['constants'].values():
            changed=copy.copy(self.source);changed.rel=bytearray(changed.rel)
            changed.rel[changed.sections[row['section']][0]+row['offset']]^=1
            with self.assertRaises(ValueError):changed.profile(0x3354)
        for section,offset in ((1,0x934),(4,0),(4,4),(4,0x20),(4,0x30)):
            changed=copy.copy(self.source);changed.rel=bytearray(changed.rel)
            changed.rel[changed.sections[section][0]+offset]^=1
            with self.assertRaisesRegex(ValueError,'source stop initializer'):changed.profile(0x3354)
        changed=copy.copy(self.source);changed.rel=bytearray(changed.rel)
        changed.rel[changed.sections[1][0]+adapter['functions']['move']['offset']+0xEB]^=1
        with self.assertRaisesRegex(ValueError,'sound word'):changed.profile(0x3354)
        changed=copy.copy(self.source);changed.code_relocations=dict(changed.code_relocations)
        del changed.code_relocations[adapter['functions']['create']['offset']+0x12]
        with self.assertRaises(ValueError):changed.profile(0x3354)


class CategoryPlanTests(unittest.TestCase):
    def test_dependency_plan_skips_installed_stages_and_keeps_item_selection(self):
        def row(item,category,**fields):
            return dict(item_id=item,asset_ready=True,installed=False,categories=[category],
                profile=dict(callback_adapter=dict(category=category,**({'trigger':{'sound_word':0x175}}
                    if category==rigs.HIT_CATEGORY else {}))),**fields)
        inventory=dict(rows=[row('3354',rigs.HIT_CATEGORY),row('32F0',rigs.CLOCK_CATEGORY),
                             row('3300',rigs.STORAGE_CATEGORY)])
        report=dict(equipment_resources=dict(room_rigs=dict(rows=[{'source_item_id':'32F0'}])))
        self.assertEqual(pipeline.rig_import_plan(inventory,report,{}),dict(
            resources=['3300','3354'],audio=['3354'],profiles=['32F0','3300','3354']))
        report['equipment_resources']['room_rigs']['rows'].append({'source_item_id':'3354'})
        report['equipment_resources']['furniture_audio']={'furniture':[{'item_id':'3354'}]}
        self.assertEqual(pipeline.rig_import_plan(inventory,report,{},category=rigs.HIT_CATEGORY),
            dict(resources=[],audio=[],profiles=['3354']))
        self.assertEqual(pipeline.rig_import_plan(inventory,report,{'3354':{}},selected=['3354']),
            dict(resources=[],audio=[],profiles=[]))
        inventory['rows'][0]['installed']=True
        self.assertEqual(pipeline.rig_import_plan(inventory,report,{},category=rigs.HIT_CATEGORY),
            dict(resources=[],audio=[],profiles=[]))


class FixedResourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_shared_constructor_and_draw_discover_complete_rigs_without_gameplay_claims(self):
        for item,mode,speed,joints,shown,frames in ((0x1FC4,'stop',0,2,2,101),
                (0x3018,'repeat',0,3,2,100),(0x32F0,'repeat',.5,5,3,13),(0x33B8,'stop',.5,7,4,10)):
            profile=self.source.profile(item);adapter=profile['callback_adapter']
            self.assertEqual(adapter['category'],rigs.CLOCK_CATEGORY if item==0x32F0 else rigs.FIXED_CATEGORY)
            self.assertEqual((profile['skeleton']['joints'],profile['skeleton']['shown_joints']),(joints,shown))
            self.assertEqual(adapter['animation']['duration'],frames)
            self.assertEqual(adapter['constructor']['mode'],mode)
            self.assertEqual(adapter['constructor']['initial_speed']['value'],speed)
            self.assertTrue(adapter['constructor']['initial_play_before_speed'])
            self.assertFalse(adapter['runtime_installed'])
            self.assertEqual(adapter['pending_callbacks'],[] if item==0x32F0 else ['move'])
            self.assertEqual(len(profile['models']),shown)
            if item==0x32F0:
                self.assertEqual((adapter['clock']['hour_joint'],adapter['clock']['minute_joint']),(3,4))
                self.assertEqual(len(adapter['joint_callbacks']),2)
            self.source.runtime_profiles={}
            with self.assertRaisesRegex(ValueError,'Animated room lifecycle' if item==0x32F0 else 'move/destroy behaviour'):
                pipeline.metadata(self.source,item,profile,None)
        self.assertNotIn(rigs.FIXED_CATEGORY,rigs.RIG_CATEGORIES)
        # Same-sized existing constructors keep their real implemented category.
        for item in (0x3300,0x3308):
            self.assertEqual(self.source.profile(item)['callback_adapter']['category'],rigs.STORAGE_CATEGORY)

    def test_unknown_constructor_drawing_bindings_and_clock_effects_reject(self):
        for item in (0x1FC4,0x32F0):
            adapter=self.source.profile(item)['callback_adapter']
            for row in [adapter['functions'][r] for r in ('create','draw')]+adapter['joint_callbacks']:
                source=copy.copy(self.source);source.rel=bytearray(source.rel)
                source.rel[source.sections[1][0]+row['offset']]^=1
                with self.subTest(item=item,code=row['symbol']),self.assertRaises(ValueError):source.profile(item)
            for role,offset in (('create',0x1A),('draw',next(iter(adapter['functions']['draw']['relocations'])))):
                source=copy.copy(self.source);source.code_relocations=dict(source.code_relocations)
                del source.code_relocations[adapter['functions'][role]['offset']+offset]
                with self.assertRaises(ValueError):source.profile(item)
            speed=adapter['constructor']['initial_speed'];source=copy.copy(self.source);source.rel=bytearray(source.rel)
            struct.pack_into('>I',source.rel,source.sections[4][0]+speed['offset'],0x7FC00000)
            with self.assertRaisesRegex(ValueError,'invalid initial speed'):source.profile(item)
        # Pending move code is recorded, never silently certified as understood.
        source=copy.copy(self.source);source.rel=bytearray(source.rel)
        before=source.profile(0x1FC4)['callback_adapter']['functions']['move']
        source.rel[source.sections[1][0]+before['offset']]^=1
        changed=source.profile(0x1FC4)
        self.assertNotEqual(changed['callback_adapter']['functions']['move']['sha256'],before['sha256'])
        with self.assertRaisesRegex(ValueError,'move/destroy behaviour'):
            pipeline.metadata(source,0x1FC4,changed,None)
        with self.assertRaises(ValueError):self.source.profile(0x3264)  # Additional billboard/fire drawing.

    def test_bulk_compiled_models_motion_and_cache_keep_unfinished_records_disabled(self):
        from v3_room_rig_runtime import prepared_categories,VTABLE
        report=json.loads((FIXED_OUTPUT/'art.json').read_bytes())
        self.assertEqual(report['batch'],dict(objects=4,compiled=4,reused=0,compiler_containers=1))
        self.assertEqual({r['item_id'] for r in report['objects']},{'1FC4','3018','32F0','33B8'})
        self.assertEqual(sum(r['object_bytes'] for r in report['objects']),15776)
        cache=pipeline.PreparedAssets(self.source,[FIXED_OUTPUT])
        furniture_tests.DonorTests.check_complete_artwork(self,FIXED_OUTPUT,report)
        for row in report['objects']:
            prepared=pipeline.prepare(self.source,int(row['item_id'],16));profile=prepared[0]
            asset=(FIXED_OUTPUT/row['object_file']).read_bytes();receipt=row['rig']
            self.assertFalse(row['import_ready']);self.assertIn('move/destroy behaviour',row['pending_reason'])
            self.assertEqual(cache.reuse(self.source,row['item_id'],prepared)[1]['object_sha256'],row['object_sha256'])
            self.assertEqual(receipt['skeleton']['joints'],profile['skeleton']['joints'])
            for r in receipt['skeleton']['relocations']+receipt['animations']['relocations']:
                self.assertEqual(struct.unpack_from('>I',asset,r['offset'])[0],0x06000000+r['target_offset'])
            for r in receipt['animations']['arrays']:
                at,n,src=r['native_offset'],r['bytes'],r['donor_offset']
                self.assertEqual(asset[at:at+n],self.source.data[src:src+n])
            forged=copy.deepcopy(row);forged['room_runtime']=dict(vtable=VTABLE,vrom=0x02500000)
            with self.assertRaisesRegex(ValueError,'no implemented native lifecycle'):install.profile(forged,0x02500000)
        self.assertEqual(install.provenance_patch(report['objects']),'')
        with self.assertRaisesRegex(ValueError,'Unimplemented additional room-rig category'):
            prepared_categories(self.source,[FIXED_OUTPUT])
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            install.checked_assets(FIXED_OUTPUT,self.source,ROOT/'build/item-identity-megasheet.xlsx')


class StorageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SourceTests.setUpClass.__func__(cls)

    def test_storage_category_preserves_source_limits_and_interactions(self):
        for item,joints,shown,end,flags in ((0x3300,5,3,12,2),(0x3308,3,2,10,1)):
            profile=self.source.profile(item);adapter=profile['callback_adapter']
            self.assertEqual(profile['kind'],'animated-room-model')
            self.assertEqual(adapter['category'],rigs.STORAGE_CATEGORY)
            self.assertEqual((profile['skeleton']['joints'],profile['skeleton']['shown_joints']),(joints,shown))
            self.assertEqual(adapter['animation']['duration'],end)
            self.assertEqual({k:v['value'] for k,v in adapter['constants'].items()},
                             dict(initial_speed=0,start_frame=1,end_frame=end))
            self.assertEqual(int(profile['scalar_hex'][-4:],16),flags)
            self.assertEqual(adapter['room_callback']['clip_offset'],0x2608C)
            self.assertEqual(adapter['room_callback']['callback_offset'],0x34)
            self.assertTrue(adapter['room_callback']['nullable'])
            self.assertFalse(adapter['runtime_installed'])
            for row in adapter['functions'].values():
                source=copy.copy(self.source);source.rel=bytearray(source.rel)
                source.rel[source.sections[1][0]+row['offset']]^=1
                with self.subTest(item=item,function=row['symbol']),self.assertRaises(ValueError):source.profile(item)
            for constant in adapter['constants'].values():
                source=copy.copy(self.source);source.rel=bytearray(source.rel)
                at=source.sections[constant['section']][0]+constant['offset']
                struct.pack_into('>I',source.rel,at,0x7FC00000)
                with self.assertRaisesRegex(ValueError,'non-finite'):source.profile(item)
            source=copy.copy(self.source);source.code_relocations=dict(source.code_relocations)
            del source.code_relocations[adapter['functions']['move']['offset']+0x36]
            with self.assertRaises(ValueError):source.profile(item)

    def test_complete_storage_artwork_and_motion_reuse_without_enabling(self):
        report=json.loads((STORAGE_OUTPUT/'art.json').read_bytes())
        self.assertEqual(report['batch'],dict(objects=2,compiled=2,reused=0,compiler_containers=1))
        self.assertEqual({r['item_id'] for r in report['objects']},{'3300','3308'})
        cache=pipeline.PreparedAssets(self.source,[STORAGE_OUTPUT])
        for row in report['objects']:
            prepared=pipeline.prepare(self.source,int(row['item_id'],16))
            profile,body,_,_,_,_,sections=prepared
            asset=(STORAGE_OUTPUT/row['object_file']).read_bytes()
            start=(len(body)+sum(n for _,n in sections)+15)&~15
            suffix,receipt=rigs.suffix(self.source,profile,row['model_offsets'],start=start)
            self.assertEqual(asset[start:],suffix)
            self.assertEqual(row['rig'],json.loads(json.dumps(receipt)))
            self.assertFalse(row['import_ready'])
            self.assertIn('lifecycle',row['pending_reason'])
            self.assertEqual(cache.reuse(self.source,row['item_id'],prepared)[1]['object_sha256'],row['object_sha256'])
            for r in receipt['skeleton']['relocations']+receipt['animations']['relocations']:
                self.assertEqual(struct.unpack_from('>I',asset,r['offset'])[0],0x06000000+r['target_offset'])
            for r in receipt['animations']['arrays']:
                at,n,source=r['native_offset'],r['bytes'],r['donor_offset']
                self.assertEqual(asset[at:at+n],self.source.data[source:source+n])
        furniture_tests.DonorTests.check_complete_artwork(self,STORAGE_OUTPUT,report)
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            install.checked_assets(STORAGE_OUTPUT,self.source,ROOT/'build/item-identity-megasheet.xlsx')


class ClockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SourceTests.setUpClass.__func__(cls)

    def test_shared_clock_category_retains_three_rigs_and_fifteen_palettes(self):
        profiles=[self.source.profile(item) for item in range(0x30A8,0x30E4,4)]
        adapters=[p['callback_adapter'] for p in profiles]
        self.assertEqual({a['selected_index'] for a in adapters},set(range(15)))
        self.assertEqual({a['index_origin'] for a in adapters},{1066})
        self.assertEqual(len({a['skeleton']['header']['donor_offset'] for a in adapters}),3)
        self.assertEqual(len({a['animation']['header']['donor_offset'] for a in adapters}),3)
        self.assertEqual(len({a['palette']['donor_offset'] for a in adapters}),15)
        for profile,adapter in zip(profiles,adapters,strict=True):
            self.assertEqual(profile['kind'],'animated-room-model')
            self.assertEqual(adapter['category'],rigs.CLOCK_CATEGORY)
            self.assertEqual(adapter['entries'],16)
            self.assertEqual(adapter['clock'],dict(common_symbol='common_data',hour_joint=3,minute_joint=4,
                hour_offset=0x2612A,minute_offset=0x26128,axis='z',operation='subtract'))
            self.assertEqual(adapter['constants']['repeat_speed']['hex'],'3f000000')
            self.assertFalse(adapter['runtime_installed'])
            for table in adapter['tables'].values():
                self.assertEqual(len(table['targets']),16)
                self.assertEqual(table['targets'][14],table['targets'][15])

    def test_changed_clock_behaviour_speed_and_table_bindings_reject(self):
        profile=self.source.profile(0x30A8);adapter=profile['callback_adapter']
        for row in list(adapter['functions'].values())+adapter['joint_callbacks']:
            source=copy.copy(self.source);source.rel=bytearray(source.rel)
            source.rel[source.sections[1][0]+row['offset']]^=1
            with self.subTest(function=row['symbol']),self.assertRaises(ValueError):source.profile(0x30A8)
        for table in adapter['tables'].values():
            source=copy.copy(self.source);source.relocations=dict(source.relocations)
            del source.relocations[table['offset']+4]
            source.relocation_addresses=sorted(source.relocations)
            with self.assertRaisesRegex(ValueError,'incomplete selector table'):source.profile(0x30A8)
        source=copy.copy(self.source);source.rel=bytearray(source.rel)
        constant=adapter['constants']['repeat_speed']
        source.rel[source.sections[constant['section']][0]+constant['offset']]^=1
        with self.assertRaisesRegex(ValueError,'repeat speed'):source.profile(0x30A8)
        for index in (1065,1082):
            with self.assertRaisesRegex(ValueError,'selector escapes'):
                self.source.callback_models(profile['profile_offset'],index)

    def test_prepared_clock_objects_retain_complete_motion_and_reuse_without_enabling(self):
        report=json.loads((CLOCK_OUTPUT/'art.json').read_bytes())
        self.assertEqual(report['batch'],dict(objects=15,compiled=15,reused=0,compiler_containers=1))
        cache=pipeline.PreparedAssets(self.source,[CLOCK_OUTPUT])
        self.assertEqual(len(report['objects']),15)
        for row in report['objects']:
            item=int(row['item_id'],16);prepared=pipeline.prepare(self.source,item)
            profile,body,_,_,_,_,sections=prepared
            asset=(CLOCK_OUTPUT/row['object_file']).read_bytes()
            start=(len(body)+sum(n for _,n in sections)+15)&~15
            suffix,receipt=rigs.suffix(self.source,profile,row['model_offsets'],start=start)
            self.assertEqual(asset[start:],suffix)
            self.assertEqual(len(asset),start+rigs.estimated_suffix(self.source,profile,start))
            self.assertEqual(row['rig'],json.loads(json.dumps(receipt)))
            self.assertFalse(row['import_ready'])
            self.assertIn('lifecycle',row['pending_reason'])
            self.assertEqual(cache.reuse(self.source,row['item_id'],prepared)[1]['object_sha256'],row['object_sha256'])
            for r in receipt['skeleton']['relocations']+receipt['animations']['relocations']:
                self.assertEqual(struct.unpack_from('>I',asset,r['offset'])[0],0x06000000+r['target_offset'])
            for r in receipt['animations']['arrays']:
                at,n,source=r['native_offset'],r['bytes'],r['donor_offset']
                self.assertEqual(asset[at:at+n],self.source.data[source:source+n])
        furniture_tests.DonorTests.check_complete_artwork(self,CLOCK_OUTPUT,report)
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            install.checked_assets(CLOCK_OUTPUT,self.source,ROOT/'build/item-identity-megasheet.xlsx')


@unittest.skipUnless((OUTPUT/'art.json').is_file(),'Current room-rig conversion required')
class PreparedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SourceTests.setUpClass.__func__(cls)

    def test_complete_models_rigs_and_animations_match_real_source(self):
        report = json.loads((OUTPUT/'art.json').read_bytes())
        inventory = json.loads((OUTPUT/'inventory.json').read_bytes())
        self.assertEqual(report['format'],'AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1')
        self.assertFalse(report['runtime_installed'])
        self.assertEqual({r['item_id'] for r in report['objects']},{r['display_item_id'] for r in self.aliases})
        for row in report['objects']:
            item = int(row['item_id'],16)
            asset = (OUTPUT/row['object_file']).read_bytes()
            profile,body,_,_,_,_,sections = pipeline.prepare(self.source,item)
            artwork_size = (len(body)+sum(n for _,n in sections)+15)&~15
            suffix,receipt = rigs.suffix(self.source,profile,row['model_offsets'],start=artwork_size)
            self.assertEqual(asset[artwork_size:],suffix)
            self.assertEqual(len(asset),artwork_size+rigs.estimated_suffix(self.source,profile,artwork_size))
            self.assertEqual(row['rig'],json.loads(json.dumps(receipt)))
            self.assertEqual(row['profile'],json.loads(json.dumps(profile)))
            self.assertEqual(sha256(asset),row['object_sha256'])
            self.assertLessEqual(len(asset),9216)
            self.assertFalse(row['import_ready']);self.assertTrue(row['pending_reason'])
            self.assertTrue(row['room_alias']['room_placement_uses_display'])
            for r in receipt['skeleton']['relocations']+receipt['animations']['relocations']:
                self.assertEqual(struct.unpack_from('>I',asset,r['offset'])[0],0x06000000+r['target_offset'])
            for r in receipt['animations']['arrays']:
                at,n,source = r['native_offset'],r['bytes'],r['donor_offset']
                self.assertEqual(asset[at:at+n],self.source.data[source:source+n])
            scanned = next(r for r in inventory['rows'] if r['item_id']==row['item_id'])
            self.assertTrue(scanned['asset_ready']);self.assertEqual(scanned['status'],'review')
            self.assertNotIn('static-materials',scanned['categories'])
            self.assertNotIn('static-ci4',scanned['categories'])
        furniture_tests.DonorTests.check_complete_artwork(self,OUTPUT,report)
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            install.checked_assets(OUTPUT,self.source,ROOT/'build/item-identity-megasheet.xlsx')
