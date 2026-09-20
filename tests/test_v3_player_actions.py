"""Shared action metadata, owner relocation, native dispatch, and startup bounds."""
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,apply_ups,n64_checksum,u32
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs,reuse_resource_tail
from npc_mail_show import relocate_verified_data
import tests.test_v3_equipment_runtime as shared_tests
import v3_player_actions as actions

OUTPUT=ROOT/os.environ.get('V3_PLAYER_ACTIONS_BUILD','build/v3-player-action-tables-03')
CONTROLS=ROOT/os.environ.get('V3_PLAYER_CONTROLS_BUILD','build/v3-player-fan-controls-01')
HELD=ROOT/os.environ.get('V3_HELD_DISPATCH_BUILD','build/v3-held-item-dispatch-02')
ACTIVE=ROOT/os.environ.get('V3_FAN_ACTION_BUILD','build/v3-fan-action-dispatch-03')
SELECTION=ROOT/os.environ.get('V3_HELD_SELECTION_BUILD','build/v3-held-selection-01')
PARENTS=ROOT/os.environ.get('V3_HELD_PARENTS_BUILD','build/v3-held-parent-readers-01')
ICONS=ROOT/os.environ.get('V3_POCKET_ICONS_BUILD','build/v3-held-pocket-icons-01')
INVENTORY=ROOT/os.environ.get('V3_INVENTORY_EQUIPMENT_BUILD','build/v3-inventory-equipment-03')
TOOLS=ROOT/os.environ.get('V3_TOOL_CONTROLS_BUILD','build/v3-shared-tool-controls-02')
TOOL_MOTION=ROOT/os.environ.get('V3_TOOL_MOTION_BUILD','build/v3-shared-tool-motion-02')
TRANSITIONS=ROOT/os.environ.get('V3_TOOL_TRANSITIONS_BUILD','build/v3-shared-tool-transitions-01')
NET_CAPTURE=ROOT/os.environ.get('V3_NET_CAPTURE_BUILD','build/v3-shared-net-capture-01')


@unittest.skipUnless((NET_CAPTURE/'build-lock.json').is_file(),'Current net capture required')
class NetCaptureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(NET_CAPTURE/'build-lock.json')
        cls.base,cls.prior=inputs(NET_CAPTURE/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.capture=cls.e['player_actions']['net_capture']

    def test_native_math_retained_and_three_relocations_removed(self):
        owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        previous=self.before[actions.PLAYER_VROM].extract(self.base);restored=bytearray(owner)
        self.assertEqual(len(self.capture['patches']),5)
        for row in self.capture['patches']:
            at=row['address']-actions.PLAYER_RAM;n=len(bytes.fromhex(row['before']))
            self.assertEqual(owner[at:at+n].hex(),row['after']);self.assertEqual(previous[at:at+n].hex(),row['before'])
            restored[at:at+n]=bytes.fromhex(row['before'])
        self.assertEqual(restored,previous)
        for row in self.capture['native_consumers']:
            a,b=row['entry']-actions.PLAYER_RAM,row['end']-actions.PLAYER_RAM
            self.assertEqual(sha256(restored[a:b]),row['sha256'])
        rel=self.files[actions.PLAYER_RELOC].extract(self.rom);oldrel=self.before[actions.PLAYER_RELOC].extract(self.base)
        sections=struct.unpack_from('>5I',rel);oldsections=struct.unpack_from('>5I',oldrel)
        self.assertEqual(sections[:4],oldsections[:4]);self.assertEqual(sections[4],oldsections[4]-3)
        removed=self.capture['removed_relocations'];self.assertEqual(len(removed),3)
        oldrows=struct.unpack_from('>'+str(oldsections[4])+'I',oldrel,20)
        self.assertEqual(list(struct.unpack_from('>'+str(sections[4])+'I',rel,20)),[r for r in oldrows if r not in removed])
        for base in (0x80200010,0x80378010):
            moved=relocate_verified_data(SimpleNamespace(ram=actions.PLAYER_RAM,resident_bytes=len(owner),sections=sections),owner,rel,base)
            for row in self.capture['patches']:
                at=row['address']-actions.PLAYER_RAM
                self.assertEqual(moved[at:at+len(bytes.fromhex(row['after']))].hex(),row['after'])

    def test_existing_code_resources_profiles_and_allocations_retained(self):
        at=self.e['blob_offset'];start=at+actions.TOOL_MOTION_OFFSET;end=at+actions.PARENT_CODE_OFFSET
        old=self.before[BLOB].extract(self.base);new=self.files[BLOB].extract(self.rom)
        previous=self.old['player_actions']['tool_motion']['code'];current=self.capture['code']
        self.assertEqual(new[at:start+previous['bytes']],old[at:start+previous['bytes']])
        self.assertEqual(new[end:at+self.e['bytes']],old[end:at+self.old['bytes']])
        self.assertEqual(sha256(new[start:start+current['bytes']]),current['sha256'])
        for name,address in previous['symbols'].items():self.assertEqual(current['symbols'][name],address)
        for key in ('records','kind_readers','held_rig_actions','inventory_preview','room_rigs',
                    'optional_selection','parent_readers','pocket_icons','catalogue','event_acquisition'):
            self.assertEqual(self.e[key],self.old[key],key)
        self.assertEqual(self.e['bytes'],self.old['bytes']);self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.capture['logical_imports_added'],0)
        self.assertEqual((self.capture['normal_radius'],self.capture['normal_span'],
                          self.capture['golden_radius'],self.capture['golden_span']),(15,50,21,60))
        self.assertTrue(self.capture['golden_net_geometry_installed'])

    def test_ups_composition_and_unrelated_cartridge_resources(self):
        import v3_optional_composition as composer
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(NET_CAPTURE/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        for v in self.files.keys()-{BLOB,MODULE,actions.PLAYER_VROM,actions.PLAYER_RELOC}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(NET_CAPTURE/'build-lock.json');catalogue=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(catalogue),128)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,catalogue,composer.resolve(catalogue,[]))[0]),
                             self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.rom,self.report,catalogue,composer.resolve(catalogue,list(catalogue)))[0],self.rom)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


@unittest.skipUnless((TRANSITIONS/'build-lock.json').is_file(),'Current tool transitions required')
class ToolTransitionsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(TRANSITIONS/'build-lock.json')
        cls.base,cls.prior=inputs(TRANSITIONS/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.transitions=cls.e['player_actions']['tool_transitions']

    def test_six_complete_consumers_and_four_removed_call_relocations(self):
        owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        previous=self.before[actions.PLAYER_VROM].extract(self.base);restored=bytearray(owner)
        self.assertEqual(len(self.transitions['patches']),6)
        for row in self.transitions['patches']:
            at=row['address']-actions.PLAYER_RAM;n=len(bytes.fromhex(row['before']))
            self.assertEqual(owner[at:at+n].hex(),row['after']);self.assertEqual(previous[at:at+n].hex(),row['before'])
            restored[at:at+n]=bytes.fromhex(row['before'])
        self.assertEqual(restored,previous)
        for row in self.transitions['native_consumers']:
            a,b=row['entry']-actions.PLAYER_RAM,row['end']-actions.PLAYER_RAM
            self.assertEqual(sha256(restored[a:b]),row['sha256'])
        rel=self.files[actions.PLAYER_RELOC].extract(self.rom);oldrel=self.before[actions.PLAYER_RELOC].extract(self.base)
        sections=struct.unpack_from('>5I',rel);oldsections=struct.unpack_from('>5I',oldrel)
        self.assertEqual(sections[:4],oldsections[:4]);self.assertEqual(sections[4],oldsections[4]-4)
        removed=self.transitions['removed_relocations'];self.assertEqual(len(removed),4)
        oldrows=struct.unpack_from('>'+str(oldsections[4])+'I',oldrel,20)
        self.assertEqual(list(struct.unpack_from('>'+str(sections[4])+'I',rel,20)),[r for r in oldrows if r not in removed])
        for base in (0x80200010,0x80378010):
            spec=SimpleNamespace(ram=actions.PLAYER_RAM,resident_bytes=len(owner),sections=sections)
            moved=relocate_verified_data(spec,owner,rel,base)
            for row in self.transitions['patches']:
                at=row['address']-actions.PLAYER_RAM
                self.assertEqual(moved[at:at+len(bytes.fromhex(row['after']))].hex(),row['after'])

    def test_exact_old_motion_code_and_all_resources_retained(self):
        at=self.e['blob_offset'];start=at+actions.TOOL_MOTION_OFFSET;end=at+actions.PARENT_CODE_OFFSET
        old=self.before[BLOB].extract(self.base);new=self.files[BLOB].extract(self.rom)
        previous=self.old['player_actions']['tool_motion']['code'];current=self.transitions['code']
        self.assertEqual(new[at:start+previous['bytes']],old[at:start+previous['bytes']])
        self.assertEqual(new[end:at+self.e['bytes']],old[end:at+self.old['bytes']])
        self.assertEqual(sha256(new[start:start+current['bytes']]),current['sha256'])
        for name,address in previous['symbols'].items():self.assertEqual(current['symbols'][name],address)
        for key in ('records','kind_readers','held_rig_actions','inventory_preview','room_rigs',
                    'optional_selection','parent_readers','pocket_icons','catalogue','event_acquisition'):
            self.assertEqual(self.e[key],self.old[key],key)
        self.assertEqual(self.e['bytes'],self.old['bytes']);self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.transitions['logical_imports_added'],0)
        self.assertFalse(self.transitions['golden_effects_installed']);self.assertFalse(self.transitions['balloon_release_installed'])

    def test_ups_composition_and_unrelated_cartridge_resources(self):
        import v3_optional_composition as composer
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(TRANSITIONS/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        for v in self.files.keys()-{BLOB,MODULE,actions.PLAYER_VROM,actions.PLAYER_RELOC}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(TRANSITIONS/'build-lock.json');catalogue=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(catalogue),128)
            empty=composer.compose(self.rom,self.report,catalogue,composer.resolve(catalogue,[]))[0]
            self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.rom,self.report,catalogue,composer.resolve(catalogue,list(catalogue)))[0],self.rom)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


@unittest.skipUnless((TOOL_MOTION/'build-lock.json').is_file(),'Current shared tool motions required')
class ToolMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(TOOL_MOTION/'build-lock.json')
        cls.base,cls.prior=inputs(TOOL_MOTION/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.motion=cls.e['player_actions']['tool_motion']

    def test_exact_hooks_relocation_and_retained_drawers(self):
        owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        before=self.before[actions.PLAYER_VROM].extract(self.base);restored=bytearray(owner)
        self.assertEqual(len(self.motion['patches']),3)
        for row in self.motion['patches']:
            at=row['address']-actions.PLAYER_RAM;n=len(bytes.fromhex(row['before']))
            self.assertEqual(owner[at:at+n].hex(),row['after'])
            self.assertEqual(before[at:at+n].hex(),row['before'])
            restored[at:at+n]=bytes.fromhex(row['before'])
        self.assertEqual(restored,before)
        rel=self.files[actions.PLAYER_RELOC].extract(self.rom)
        self.assertEqual(rel,self.before[actions.PLAYER_RELOC].extract(self.base))
        for base in (0x80200010,0x80378010):
            spec=SimpleNamespace(ram=actions.PLAYER_RAM,resident_bytes=len(owner),sections=struct.unpack_from('>5I',rel))
            moved=relocate_verified_data(spec,owner,rel,base)
            for row in self.motion['patches']:
                at=row['address']-actions.PLAYER_RAM
                self.assertEqual(moved[at:at+len(bytes.fromhex(row['after']))].hex(),row['after'])
        for row in self.motion['native_consumers']:
            a,b=row['entry']-actions.PLAYER_RAM,row['end']-actions.PLAYER_RAM
            self.assertEqual(sha256(restored[a:b]),row['sha256'])

    def test_complete_rig_motions_without_changed_assets_or_profiles(self):
        a=self.e['blob_offset'];first=a+self.motion['code_offset'];end=a+actions.PARENT_CODE_OFFSET
        old=self.before[BLOB].extract(self.base);new=self.files[BLOB].extract(self.rom)
        self.assertEqual(new[a:first],old[a:first]);self.assertEqual(new[end:a+self.e['bytes']],old[end:a+self.old['bytes']])
        self.assertEqual(sha256(new[first:first+self.motion['code']['bytes']]),self.motion['code']['sha256'])
        self.assertLessEqual(self.motion['code']['bytes'],end-first)
        self.assertEqual([(r['native'],r['imported']) for r in self.motion['motion_map']],
            [(i,i+21) for i in range(2,9)]+[(i,i+22) for i in range(10,16)])
        self.assertEqual([(r['joints'],r['shown_joints']) for r in self.motion['rigs']],[(6,3)]*2+[(5,4)]*2)
        for key in ('records','kind_readers','held_rig_actions','inventory_preview','room_rigs','optional_selection',
                    'parent_readers','pocket_icons','catalogue','event_acquisition'):
            self.assertEqual(self.e[key],self.old[key],key)
        self.assertEqual(self.e['player_actions']['tool_controls'],self.old['player_actions']['tool_controls'])
        self.assertEqual(self.e['bytes'],self.old['bytes']);self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertFalse(self.motion['golden_effects_installed']);self.assertEqual(self.motion['logical_imports_added'],0)

    def test_patch_original_resources_and_composition(self):
        import v3_optional_composition as composer
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(TOOL_MOTION/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        for v in self.files.keys()-{BLOB,MODULE,actions.PLAYER_VROM}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(TOOL_MOTION/'build-lock.json')
            catalogue=composer.catalogue(self.rom,self.report);self.assertEqual(len(catalogue),128)
            empty=composer.compose(self.rom,self.report,catalogue,composer.resolve(catalogue,[]))[0]
            self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])
            full=composer.compose(self.rom,self.report,catalogue,composer.resolve(catalogue,list(catalogue)))[0]
            self.assertEqual(full,self.rom)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


@unittest.skipUnless((TOOLS/'build-lock.json').is_file(),'Current shared tool controls required')
class ToolControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(TOOLS/'build-lock.json')
        cls.base,cls.prior=inputs(TOOLS/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.controls=cls.e['player_actions']['tool_controls']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_complete_controller_functions_and_exact_relocation_changes(self):
        owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        previous=self.before[actions.PLAYER_VROM].extract(self.base)
        restored=bytearray(owner);controls=self.controls
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual(len(controls['patches']),6)
        for row,consumer,donor in zip(controls['patches'],controls['consumers'],controls['source_functions']):
            self.assertEqual(source.function(donor['offset'])[1],donor)
            at=row['offset'];self.assertEqual(u32(owner,at),actions.jump(controls['entry'],link=True))
            self.assertEqual(u32(previous,at),row['before'])
            self.assertEqual(consumer['call'],actions.PLAYER_RAM+at)
            a,b=consumer['entry']-actions.PLAYER_RAM,consumer['end']-actions.PLAYER_RAM
            self.assertEqual(sha256(previous[a:b]),consumer['sha256'])
            struct.pack_into('>I',restored,at,row['before'])
        self.assertEqual(restored,previous)
        rel=self.files[actions.PLAYER_RELOC].extract(self.rom)
        old_rel=self.before[actions.PLAYER_RELOC].extract(self.base)
        sections=struct.unpack_from('>5I',rel);old_sections=struct.unpack_from('>5I',old_rel)
        self.assertEqual(sections[:4],old_sections[:4]);self.assertEqual(len(rel),len(old_rel))
        self.assertEqual(sections[4],old_sections[4]-6)
        old_rows=struct.unpack_from('>'+str(old_sections[4])+'I',old_rel,20)
        rows=struct.unpack_from('>'+str(sections[4])+'I',rel,20)
        self.assertEqual(list(rows),[r for r in old_rows if r not in controls['removed_relocations']])
        spec=SimpleNamespace(ram=actions.PLAYER_RAM,resident_bytes=len(owner),sections=sections)
        for base in (0x80200010,0x80378010):
            loaded=relocate_verified_data(spec,owner,rel,base)
            for row in controls['patches']:self.assertEqual(u32(loaded,row['offset']),row['after'])
        self.assertEqual(sha256(owner),self.e['player_actions']['owner_sha256'])
        self.assertEqual(sha256(rel),self.e['player_motion']['reloc_sha256'])

    def test_old_code_resources_and_actual_kind_identities_are_retained(self):
        old=self.old['player_actions']['code'];new=self.e['player_actions']['code']
        at=self.e['blob_offset'];first=at+actions.CODE_OFFSET;last=at+actions.PARENT_CODE_OFFSET
        self.assertEqual(self.blob[first:first+old['bytes']],self.oldblob[first:first+old['bytes']])
        self.assertEqual(self.blob[at:first],self.oldblob[at:first])
        self.assertEqual(self.blob[last:at+self.e['bytes']],self.oldblob[last:at+self.old['bytes']])
        self.assertEqual(sha256(self.blob[first:first+new['bytes']]),new['sha256'])
        for name,value in old['symbols'].items():self.assertEqual(new['symbols'][name],value)
        self.assertEqual(new['symbols']['af_v3_player_control_kind'],self.controls['entry'])
        self.assertLessEqual(first+new['bytes'],last)
        for key in ('kind_readers','records','held_rig_actions','inventory_preview','room_rigs',
                    'optional_selection','parent_readers','pocket_icons','catalogue','event_acquisition'):
            self.assertEqual(self.e[key],self.old[key],key)
        for key in ('equipment_selection','tables','held_dispatch','fan_activation'):
            self.assertEqual(self.e['player_actions'][key],self.old['player_actions'][key])
        # Independent source-derived item-main categories agree with every
        # extended kind family; the hook never overwrites the real kind table.
        family={1:0,2:1,10:2,11:34,20:35,21:2,22:2,23:2}
        self.assertEqual(len(self.e['kind_readers']['rows']),79)
        for row in self.e['kind_readers']['rows']:
            kind=row['native_kind'];self.assertEqual(kind,36+row['source_kind'])
            expected=0 if kind<45 else 1 if kind<47 else 2 if kind<87 else 34 if kind<89 else 35 if kind<91 else 2
            self.assertEqual(family[row['item_main']],expected)

    def test_patch_profile_original_consumers_and_optional_composition(self):
        import v3_optional_composition as composer
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(TOOLS/'asset-loader.ups').read_bytes()),self.rom)
        for v in self.files.keys()-{BLOB,MODULE,CODE_VROM,actions.PLAYER_VROM,actions.PLAYER_RELOC}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        self.assertEqual(self.files[CODE_VROM].extract(self.rom),self.before[CODE_VROM].extract(self.base))
        self.assertEqual(self.e['bytes'],self.old['bytes'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_profile_changed'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.controls['golden_effects_installed'])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(TOOLS/'build-lock.json');catalog=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(catalog),128)
            for item in ('2239','223A','223B','223C'):self.assertNotIn('GAFE01-r0/item/'+item,catalog)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.rom,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.rom)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


@unittest.skipUnless((INVENTORY/'build.json').is_file(),'Current inventory-preview cartridge required')
class InventoryPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(INVENTORY/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((INVENTORY/'build.json').read_bytes())
        cls.base,cls.prior=inputs(INVENTORY/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.preview=cls.e['inventory_preview']
        cls.blob=cls.files[BLOB].extract(cls.rom)
        at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_actual_source_relationships_and_complete_native_tables(self):
        from v3_inventory_equipment import records,SELECTOR,COUNT,VROM,OWNER_RAM
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        selector,receipt=records(source,self.prior['equipment_resources'])
        self.assertEqual(self.module[SELECTOR:SELECTOR+len(selector)],selector)
        for k,v in receipt.items():self.assertEqual(self.preview[k],json.loads(json.dumps(v)))
        self.assertEqual(len(receipt['rows']),8)
        native=self.before[VROM].extract(self.base)
        for table in self.preview['tables']:
            at=table['offset'];values=struct.unpack_from('>'+str(COUNT)+'I',self.module,at)
            self.assertEqual(self.module[at:at+20],native[table['native']-OWNER_RAM:table['native']-OWNER_RAM+20])
            self.assertEqual(values[5],0)
            for row in receipt['rows']:
                expected=(self.preview['code']['symbols']['af_v3_inventory_static_draw']
                          if table['role']=='draw' else row['fields'][table['role']])
                self.assertEqual(values[row['preview_kind']],expected)
                self.assertFalse(self.blob[0x20+self.prior['equipment_resources']['parent_readers']['rows'][0]['profile_byte']]
                                 &self.prior['equipment_resources']['parent_readers']['rows'][0]['profile_mask'])
            self.assertEqual(sha256(self.module[at:at+table['bytes']]),table['sha256'])
        import copy
        bad=copy.deepcopy(self.prior['equipment_resources'])
        next(r for r in bad['records'] if r['index']==59)['type']=1
        with self.assertRaises(ValueError):records(source,bad)

    def test_declared_owner_edits_relocation_and_unchanged_prior_equipment(self):
        from v3_inventory_equipment import VROM,RELOC,OWNER_RAM,SECTIONS,CODE
        old=self.before[VROM].extract(self.base);new=self.files[VROM].extract(self.rom)
        restored=bytearray(new)
        for row in self.preview['patches']:
            at=row['address']-OWNER_RAM
            self.assertEqual(struct.unpack_from('>I',old,at)[0],row['before'])
            self.assertEqual(struct.unpack_from('>I',new,at)[0],row['after'])
            struct.pack_into('>I',restored,at,row['before'])
        self.assertEqual(restored,old)
        rel=self.files[RELOC].extract(self.rom);prior=self.before[RELOC].extract(self.base)
        self.assertEqual(len(rel),len(prior));self.assertEqual(struct.unpack_from('>5I',rel),(*SECTIONS,144))
        rows=struct.unpack_from('>160I',prior,20)
        self.assertEqual(list(struct.unpack_from('>144I',rel,20)),[r for r in rows if r not in self.preview['removed_relocations']])
        for base in (0x80200010,0x80378010):
            spec=SimpleNamespace(ram=OWNER_RAM,resident_bytes=sum(SECTIONS),sections=(*SECTIONS,144))
            loaded=relocate_verified_data(spec,new,rel,base)
            for row in self.preview['patches']:
                at=row['address']-OWNER_RAM
                self.assertEqual(struct.unpack_from('>I',loaded,at)[0],row['after'])
        before_blob=self.before[BLOB].extract(self.base);e=self.prior['equipment_resources'];at=e['blob_offset']
        self.assertEqual(before_blob[at:at+CODE],self.module[:CODE])
        self.assertEqual(self.e['records'],e['records']);self.assertEqual(self.e['player_motion'],e['player_motion'])
        self.assertEqual(self.e['player_actions'],e['player_actions'])
        self.assertEqual(sha256(self.module),self.e['sha256']);self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        self.assertEqual(self.e['bytes'],0x7000)

    def test_current_patch_profile_startup_and_unrelated_resources(self):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(INVENTORY/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        changed={CODE_VROM,BLOB,MODULE,0x785700,0x7898C0}
        self.assertEqual(self.before.keys(),self.files.keys())
        # The native directory records the new physical owner locations.
        # Check its declared entries instead of expecting its bytes unchanged.
        for v,file in self.before.items():
            self.assertEqual(file.index,self.files[v].index)
            if v not in changed|{0x19D40}:
                self.assertEqual(file.extract(self.base),self.files[v].extract(self.rom),hex(v))
        self.assertEqual(self.blob[0x20:0xE0],self.before[BLOB].extract(self.base)[0x20:0xE0])
        self.assertIn('-DAF_V3_EQUIPMENT_BYTES=0x7000u',self.report['startup']['flags'])
        self.assertLessEqual(self.report['startup']['bytes'],CONFIG-STARTUP)
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])


@unittest.skipUnless((ICONS/'build.json').is_file(),'Current shared pocket-icon cartridge required')
class PocketIconTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(ICONS/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((ICONS/'build.json').read_bytes())
        cls.base,cls.prior=inputs(ICONS/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.e=cls.report['equipment_resources']
        cls.icons=cls.e['pocket_icons'];at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_source_discovery_complete_pixels_and_selected_parent_relationships(self):
        from v3_handheld_items import pocket_icons
        from title_assets import untile,rgb5a3
        from texture_preview import rgba5551
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        data,receipt=pocket_icons(source,self.prior['equipment_resources'],0x804A6800,0x800)
        self.assertEqual(data,self.module[0x3800:0x3800+len(data)])
        for key,value in receipt.items():self.assertEqual(self.icons[key],json.loads(json.dumps(value)))
        self.assertEqual(len(receipt['rows']),8);self.assertEqual(len(receipt['resources']),2)
        palette,texture=receipt['resources']
        self.assertEqual([r['kind'] for r in receipt['resources']],['palette','texture'])
        native_pixels=bytes(v for b in data[texture['offset']:texture['offset']+512] for v in (b>>4,b&15))
        self.assertEqual(native_pixels,untile(source.raw(texture['symbol']),32,32,4))
        native_colours=[rgba5551(v) for (v,) in struct.iter_unpack('>H',data[palette['offset']:palette['offset']+32])]
        donor_colours=[rgb5a3(v) for (v,) in struct.iter_unpack('>H',source.raw(palette['symbol']))]
        self.assertEqual(native_colours,donor_colours)
        for row in receipt['rows']:
            self.assertEqual(row['menu_category'],2);self.assertEqual(row['source_type'],43)
            self.assertFalse(row['selectable'])
        slot=source.symbol('tool_tex_table$765')[0]+84*8
        source.relocations[slot]=(1,True,1,source.relocations[slot][3])
        with self.assertRaises(ValueError):pocket_icons(source,self.prior['equipment_resources'],0x804A6800,0x800)

    def test_only_declared_owner_words_relocations_and_module_region_change(self):
        from v3_furniture_icon import VROM,RELOC,RAM
        old=self.before[VROM].extract(self.base);new=self.files[VROM].extract(self.rom)
        at=self.icons['hook']['address']-RAM
        self.assertEqual(new[:at],old[:at]);self.assertEqual(new[at+8:],old[at+8:])
        self.assertEqual(new[at:at+8].hex(),self.icons['hook']['after'])
        rel=self.files[RELOC].extract(self.rom);prior=self.before[RELOC].extract(self.base)
        self.assertEqual(len(rel),len(prior))
        self.assertEqual(struct.unpack_from('>5I',rel),(8720,3232,64,67376,132))
        rows=struct.unpack_from('>134I',prior,20)
        self.assertEqual(list(struct.unpack_from('>132I',rel,20)),[r for r in rows if r not in self.icons['removed_relocations']])
        for base in (0x80200010,0x80378010):
            spec=SimpleNamespace(ram=RAM,resident_bytes=79392,sections=struct.unpack_from('>5I',rel))
            relocated=relocate_verified_data(spec,new,rel,base)
            self.assertEqual(relocated[at:at+8],new[at:at+8])
        before_blob=self.before[BLOB].extract(self.base);start=self.e['blob_offset']
        old_module=before_blob[start:start+self.e['bytes']]
        self.assertEqual(old_module[:0x3000],self.module[:0x3000])
        self.assertEqual(old_module[0x4000:],self.module[0x4000:])
        self.assertEqual(sha256(self.module),self.e['sha256'])
        self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        self.assertEqual(self.e['records'],self.prior['equipment_resources']['records'])
        self.assertEqual(self.e['bytes'],self.prior['equipment_resources']['bytes'])

    def test_patch_startup_crc_profile_and_unrelated_resources(self):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(ICONS/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        for v,file in self.before.items():
            self.assertEqual(file.index,self.files[v].index)
            if v not in (0x19D40,BLOB,MODULE,0x7749C0,0x7778B0):
                self.assertEqual(file.extract(self.base),self.files[v].extract(self.rom),hex(v))
        self.assertEqual(self.blob[0x20:0xE0],self.before[BLOB].extract(self.base)[0x20:0xE0])
        self.assertIn('-DAF_V3_EQUIPMENT_CRC=0x%08Xu'%self.e['crc32'],self.report['startup']['flags'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])


class SelectionHostTests(unittest.TestCase):
    sanitized=shared_tests.HostTests.sanitized

    def test_source_net_parameters(self):
        self.sanitized('v3_tool_net_test.c')

    def test_shared_tool_motion_mapping(self):
        self.sanitized('v3_tool_motion_test.c')

    def test_shared_tool_kind_predicates(self):
        self.sanitized('v3_tool_controls_test.c')

    def test_selected_equipment_bounds_and_passive_permissions(self):
        self.sanitized('v3_held_selection_test.c')

    def test_parent_names_prices_and_bounded_writes(self):
        self.sanitized('v3_held_items_test.c')

    def test_inventory_preview_selection_and_drawing(self):
        self.sanitized('v3_inventory_equipment_test.c')

    def test_native_probe_uses_original_switch_and_actual_permission_values(self):
        from v3_furniture_batch_smoke import original_equipment_kinds
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        kinds=original_equipment_kinds(original)
        self.assertEqual([kinds[i] for i in (0,1,2,35)],[1,0,35,33])
        self.assertEqual(sorted(kinds),list(range(36)))
        report=json.loads((SELECTION/'build.json').read_bytes());equipment=report['equipment_resources']
        rom=(SELECTION/'animal-forest-v3-asset-loader.z64').read_bytes();blob=by_vrom(rom)[BLOB].extract(rom)
        row=next(r for r in equipment['player_actions']['tables'] if r['native_entry']==0x808B63EC)
        values=blob[equipment['blob_offset']+row['offset']:equipment['blob_offset']+row['offset']+row['bytes']]
        self.assertEqual(set(values),{0,1,3})


@unittest.skipUnless((PARENTS/'build.json').is_file(),'Current parent-reader cartridge required')
class ParentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(PARENTS/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((PARENTS/'build.json').read_bytes())
        cls.base,cls.prior=inputs(PARENTS/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.e=cls.report['equipment_resources']
        cls.p=cls.e['parent_readers'];at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_source_metadata_and_single_provenance_catalogue(self):
        import copy
        from v3_handheld_items import parent_records
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        table,receipt=parent_records(source,self.prior['equipment_resources'])
        self.assertEqual(self.module[actions.PARENT_TABLE_OFFSET:actions.PARENT_TABLE_OFFSET+len(table)],table)
        for key,value in receipt.items():self.assertEqual(self.p[key],json.loads(json.dumps(value)))
        self.assertTrue(self.p['provenance_complete'])
        catalogue={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
        for row in self.p['rows']:
            locale=catalogue[row['id']+'/name']['locales']['en']
            self.assertEqual(locale['credit'],'official');self.assertEqual(locale['encoded_sha256'],row['name_sha256'])
            self.assertEqual(locale['source']['symbol'],'itemName_tool')
            self.assertEqual(locale['source']['index'],row['name_source_index'])
            self.assertFalse(self.blob[0x20+row['profile_byte']]&row['profile_mask'])
            self.assertEqual(row['source_type'],43)
        bad=copy.deepcopy(self.prior['equipment_resources'])
        bad['player_actions']['equipment_selection']['rows'][0]['item_id']='2253'
        with self.assertRaisesRegex(ValueError,'installed source-derived'):parent_records(source,bad)
        data=bytearray(source.data);data[source.symbol('tool_price_table')[0]]^=1;source.data=bytes(data)
        with self.assertRaisesRegex(ValueError,'complete parent table'):parent_records(source,self.prior['equipment_resources'])

    def test_complete_readers_preserve_actions_resources_and_profile(self):
        old_blob=self.before[BLOB].extract(self.base);at=self.e['blob_offset']
        old=old_blob[at:at+self.e['bytes']];restored=bytearray(self.module)
        for offset,n in ((actions.PARENT_CODE_OFFSET,self.p['code']['bytes']),
                         (actions.PARENT_TABLE_OFFSET,self.p['table_bytes'])):
            self.assertEqual(old[offset:offset+n],bytes(n));restored[offset:offset+n]=bytes(n)
        self.assertEqual(restored,old)
        self.assertEqual(self.e['player_actions'],self.prior['equipment_resources']['player_actions'])
        self.assertEqual(sha256(self.module),self.e['sha256']);self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        start=actions.PARENT_CODE_OFFSET
        self.assertEqual(sha256(self.module[start:start+self.p['code']['bytes']]),self.p['code']['sha256'])
        readers=self.report['clothing']['display']['readers'];self.assertTrue(readers['held_parent_readers'])
        self.assertLessEqual(readers['code']['bytes'],768)
        self.assertEqual(sha256(self.blob[0x6C00:0x6C00+readers['code']['bytes']]),readers['code']['sha256'])
        for row in readers['item_hooks']+readers['collection_hooks']:
            at=row['entry']-0x80460000
            self.assertEqual(self.blob[at:at+8],bytes.fromhex(row['after']))
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(self.report.get(key),self.prior.get(key))
        for v in self.files.keys()-{BLOB,MODULE,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),f'{v:08X}')
        self.assertFalse(self.report['shared_runtime_refresh']['resource_allocations_changed'])
        self.assertFalse(self.p['native_inventory_category_installed'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(PARENTS/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))


@unittest.skipUnless((SELECTION/'build.json').is_file(),'Current held-selection cartridge required')
class SelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(SELECTION/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((SELECTION/'build.json').read_bytes())
        cls.base,cls.prior=inputs(SELECTION/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.a=cls.e['player_actions'];cls.s=cls.a['equipment_selection']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old_blob=cls.before[BLOB].extract(cls.base)
        at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_source_records_bind_individual_profiles_without_enabling_inventory(self):
        from v3_handheld_items import selection_records
        import copy
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        table,receipt=selection_records(source,self.prior['equipment_resources'])
        self.assertEqual(self.module[actions.SELECTION_OFFSET:actions.SELECTION_OFFSET+len(table)],table)
        for key,value in receipt.items():self.assertEqual(self.s[key],json.loads(json.dumps(value)))
        self.assertEqual(len(self.s['rows']),8);self.assertEqual(self.s['profile_bits_enabled'],0)
        for row in self.s['rows']:
            item=int(row['item_id'],16);at=16+(item-0x2200)*8
            self.assertEqual(struct.unpack_from('>HbBHBB',table,at),
                (item,row['native_kind'],1,row['profile_byte'],row['profile_mask'],1))
            self.assertFalse(self.blob[0x20+row['profile_byte']]&row['profile_mask'])
            self.assertFalse(row['selectable']);self.assertFalse(row['room_placement_uses_display'])
        self.assertEqual(table[16:16+84*8],bytes(84*8))
        altered=copy.deepcopy(self.prior['equipment_resources'])
        altered['kind_readers']['rows'][-1]['combined_bank_bytes']=4377
        with self.assertRaisesRegex(ValueError,'dependency'):selection_records(source,altered)
        altered=copy.deepcopy(self.prior['equipment_resources'])
        altered['player_actions']['enabled_imported_actions']=[]
        with self.assertRaisesRegex(ValueError,'complete fan'):selection_records(source,altered)

    def test_native_switch_scene_rules_and_resident_jumps_survive_relocation(self):
        owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        old=self.before[actions.PLAYER_VROM].extract(self.base);restored=bytearray(owner)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        native=by_vrom(original)[actions.PLAYER_VROM].extract(original)
        prior_patches={r['offset']:r for r in self.prior['equipment_resources']['player_actions']['patches']}
        for row in self.a['patches']:
            at=row['offset'];self.assertEqual(struct.unpack_from('>I',owner,at)[0],row['after'])
            struct.pack_into('>I',restored,at,prior_patches.get(at,{}).get('after',row['before']))
        self.assertEqual(restored,old)
        at=0x808E0274-actions.PLAYER_RAM;self.assertEqual(owner[at:at+144],native[at:at+144])
        reloc=self.files[actions.PLAYER_RELOC].extract(self.rom)
        self.assertEqual(reloc,self.before[actions.PLAYER_RELOC].extract(self.base))
        spec=SimpleNamespace(ram=actions.PLAYER_RAM,resident_bytes=len(owner),sections=struct.unpack_from('>5I',reloc))
        for base in (0x80200000,0x80300000):
            live=relocate_verified_data(spec,owner,reloc,base)
            for hook in self.s['hooks']:
                self.assertEqual(struct.unpack_from('>2I',live,hook['entry']-actions.PLAYER_RAM),
                                 (actions.jump(hook['target']),0))
            for entry,*_ in actions.POLL_SITES:
                self.assertEqual(struct.unpack_from('>I',live,entry-actions.PLAYER_RAM)[0],
                    actions.jump(self.a['code']['symbols']['af_v3_player_handheld_poll'],link=True))
        self.assertEqual(sha256(owner),self.e['player_motion']['owner_sha256'])

    def test_callback_rebinding_resources_save_profile_and_patch(self):
        code=self.a['code'];at=actions.CODE_OFFSET
        self.assertEqual(sha256(self.module[at:at+code['bytes']]),code['sha256'])
        self.assertEqual(sha256(self.module),self.e['sha256']);self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        for row in self.a['tables']+self.a['held_dispatch']['tables']:
            self.assertEqual(sha256(self.module[row['offset']:row['offset']+row['bytes']]),row['sha256'])
        for row in self.a['fan_activation']['callbacks']:
            self.assertEqual(struct.unpack_from('>I',self.module,row['offset'])[0],row['target'])
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(self.report.get(key),self.prior.get(key))
        for key in ('records','sound_programs'):self.assertEqual(self.e[key],self.prior['equipment_resources'][key])
        for v in self.files.keys()-{BLOB,MODULE,actions.PLAYER_VROM,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),f'{v:08X}')
        self.assertEqual(sha256(self.blob),self.report['blob_sha256'])
        self.assertFalse(self.report['shared_runtime_refresh']['resource_allocations_changed'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(SELECTION/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))


@unittest.skipUnless((ACTIVE/'build.json').is_file(),'Current activated-action cartridge required')
class ActivationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(ACTIVE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((ACTIVE/'build.json').read_bytes())
        cls.base,cls.prior=inputs(ACTIVE/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.a=cls.e['player_actions'];cls.activation=cls.a['fan_activation']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old_blob=cls.before[BLOB].extract(cls.base)
        at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_only_complete_fan_callbacks_are_published(self):
        old=self.prior['equipment_resources'];before=self.old_blob[old['blob_offset']:old['blob_offset']+old['bytes']]
        restored=bytearray(self.module)
        self.assertEqual(len(self.activation['callbacks']),3)
        for row in self.activation['callbacks']:
            self.assertEqual(struct.unpack_from('>I',self.module,row['offset'])[0],row['target'])
            self.assertEqual(before[row['offset']:row['offset']+4],bytes(4))
            restored[row['offset']:row['offset']+4]=bytes(4)
        self.assertEqual(restored[actions.CODE_OFFSET:actions.CODE_OFFSET+80],before[actions.CODE_OFFSET:actions.CODE_OFFSET+80])
        restored[actions.CODE_OFFSET:actions.TABLE_OFFSET]=before[actions.CODE_OFFSET:actions.TABLE_OFFSET]
        draw=self.a['held_dispatch']['tables'][1]['offset']+23*4
        restored[draw:draw+4]=before[draw:draw+4]
        self.assertEqual(restored,before)
        self.assertEqual(self.a['enabled_imported_actions'],[109]);self.assertTrue(self.a['fan_action_installed'])
        self.assertFalse(self.activation['inventory_selection_installed']);self.assertEqual(self.activation['logical_imports_added'],0)
        for row in self.a['tables']:
            value=self.module[row['offset']:row['offset']+row['bytes']]
            self.assertEqual(sha256(value),row['sha256'])
            if row['width']==4:
                for index in self.a['disabled_indices']:self.assertEqual(value[index*4:index*4+4],bytes(4))
        code=self.a['code']
        self.assertEqual(sha256(self.module[actions.CODE_OFFSET:actions.CODE_OFFSET+code['bytes']]),code['sha256'])
        self.assertTrue(self.activation['crossed_release_events_preserved'])
        self.assertTrue(self.activation['wrapped_end_event_preserved'])
        self.assertEqual(self.e['sound_programs'],old['sound_programs'])
        self.assertEqual(zlib.crc32(self.module),self.e['crc32'])

    def test_poll_hooks_remove_only_their_native_call_relocations(self):
        owner=self.files[actions.PLAYER_VROM].extract(self.rom);restored=bytearray(owner)
        old=self.before[actions.PLAYER_VROM].extract(self.base)
        count=len(self.prior['equipment_resources']['player_actions']['patches'])
        patches=self.a['patches'][count:];self.assertEqual(len(patches),4)
        self.assertEqual({r['offset']+actions.PLAYER_RAM for r in patches},{r[0] for r in actions.POLL_SITES})
        for r in patches:
            self.assertEqual(struct.unpack_from('>I',owner,r['offset'])[0],r['after'])
            struct.pack_into('>I',restored,r['offset'],r['before'])
        self.assertEqual(restored,old)
        reloc=self.files[actions.PLAYER_RELOC].extract(self.rom)
        prior=self.before[actions.PLAYER_RELOC].extract(self.base)
        self.assertEqual(struct.unpack_from('>I',prior,16)[0]-struct.unpack_from('>I',reloc,16)[0],4)
        spec=SimpleNamespace(ram=actions.PLAYER_RAM,resident_bytes=len(owner),sections=struct.unpack_from('>5I',reloc))
        for base in (0x80200000,0x80300000):
            live=relocate_verified_data(spec,owner,reloc,base)
            for r in patches:self.assertEqual(struct.unpack_from('>I',live,r['offset'])[0],r['after'])
            self.assertEqual(struct.unpack_from('>I',live,0x808DCAA0-actions.PLAYER_RAM)[0],
                actions.jump(base+0x808B7DD8-actions.PLAYER_RAM,link=True))
        self.assertEqual(sha256(reloc),self.e['player_motion']['reloc_sha256'])

    def test_remaining_core_limits_and_unchanged_inventory_profile(self):
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        core=self.files[CODE_VROM].extract(self.rom);owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        audit=actions.fan_action_audit(source,owner,core,original)
        self.assertEqual(json.loads(json.dumps(audit)),self.activation['audit'])
        self.assertFalse(audit['core_changes_required'])
        self.assertEqual(audit['equipment_change_callback']['returns'],[-1,7,8,9,10])
        damaged=bytearray(core);struct.pack_into('>I',damaged,0,0x28420069)
        with self.assertRaisesRegex(ValueError,'inventory'):actions.fan_action_audit(source,owner,damaged,original)
        bindings=actions.control_bindings(source,owner,core,original,self.e)
        bindings.update(action_callbacks_installed=True,poll_hooks_installed=True)
        self.assertEqual(json.loads(json.dumps(bindings)),self.a['fan_control_flow'])
        self.assertEqual(sha256(self.blob),self.report['blob_sha256'])
        for v in self.files.keys()-{BLOB,MODULE,actions.PLAYER_VROM,actions.PLAYER_RELOC,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),f'{v:08X}')
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(self.report.get(key),self.prior.get(key))
        self.assertEqual(apply_ups(original,(ACTIVE/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))


@unittest.skipUnless((HELD/'build.json').is_file(),'Current held-dispatch cartridge required')
class HeldDispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(HELD/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((HELD/'build.json').read_bytes())
        cls.base,cls.prior=inputs(HELD/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.a=cls.e['player_actions'];cls.h=cls.a['held_dispatch']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old_blob=cls.before[BLOB].extract(cls.base)
        at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_complete_category_tables_preserve_original_callbacks(self):
        self.assertEqual(self.h['count'],24);self.assertEqual(self.h['native_count'],21)
        old=self.prior['equipment_resources'];a=old['player_actions'];at=old['blob_offset']
        self.assertEqual(self.module[actions.TABLE_OFFSET:actions.TABLE_OFFSET+a['table_bytes']],
            self.old_blob[at+actions.TABLE_OFFSET:at+actions.TABLE_OFFSET+a['table_bytes']])
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        for row,description in zip(self.h['tables'],actions.source_tables(source,actions.HELD_CATEGORIES,24)):
            value=self.module[row['offset']:row['offset']+row['bytes']]
            self.assertEqual(sha256(value),row['sha256']);self.assertEqual(sha256(value[:84]),row['native_sha256'])
            self.assertEqual(value[84:92],bytes(8))
            pointer=struct.unpack_from('>I',value,92)[0]
            self.assertEqual(pointer,self.h['native_zero_callback'] if row['native_entry']==0x808BF410
                else self.a['code']['symbols']['af_v3_player_draw_static_item'])
            self.assertEqual(row['consumer'],json.loads(json.dumps(description['consumer'])))
            self.assertEqual(row['source_callbacks'],json.loads(json.dumps(description['source_callbacks'])))
        self.assertEqual(self.h['net_reset']['angles_hex'],'000000b6e38f')
        self.assertFalse(self.h['net_reset']['installed']);self.assertEqual(self.a['enabled_imported_actions'],[])
        self.assertFalse(self.h['balloon_state_installed'])

    def test_actual_owner_relocations_and_only_declared_changes(self):
        owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        before=self.before[actions.PLAYER_VROM].extract(self.base);restored=bytearray(owner)
        prior_patches=self.prior['equipment_resources']['player_actions']['patches']
        new=self.a['patches'][len(prior_patches):]
        self.assertEqual(len(new),8)
        for row in new:
            self.assertEqual(struct.unpack_from('>I',owner,row['offset'])[0],row['after'])
            struct.pack_into('>I',restored,row['offset'],row['before'])
        self.assertEqual(restored,before)
        reloc=self.files[actions.PLAYER_RELOC].extract(self.rom)
        old=self.before[actions.PLAYER_RELOC].extract(self.base)
        self.assertEqual(struct.unpack_from('>I',old,16)[0]-struct.unpack_from('>I',reloc,16)[0],4)
        self.assertEqual(sha256(owner),self.a['owner_sha256']);self.assertEqual(sha256(reloc),self.a['relocation_sha256'])
        self.assertEqual(sha256(reloc),self.e['player_motion']['reloc_sha256'])
        spec=SimpleNamespace(ram=actions.PLAYER_RAM,resident_bytes=len(owner),sections=struct.unpack_from('>5I',reloc))
        for base in (0x80200000,0x80300000):
            live=relocate_verified_data(spec,owner,reloc,base)
            for row in self.h['tables']:
                for high,low in row['references']:
                    value=(struct.unpack_from('>I',live,high-actions.PLAYER_RAM)[0]&65535)<<16
                    value+=struct.unpack_from('>h',live,low-actions.PLAYER_RAM+2)[0]
                    self.assertEqual(value,row['ram'])
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        bindings=actions.control_bindings(source,owner,self.files[CODE_VROM].extract(self.rom),original,self.e)
        self.assertEqual(json.loads(json.dumps(bindings)),self.a['fan_control_flow'])

    def test_same_allocations_complete_blob_receipt_and_unchanged_sound_profile(self):
        old=self.prior['equipment_resources'];at=self.e['blob_offset']
        self.assertEqual(len(self.blob),len(self.old_blob));self.assertEqual(self.e['bytes'],old['bytes'])
        self.assertEqual(self.e['sound_programs'],old['sound_programs'])
        self.assertEqual(self.module[:actions.CODE_OFFSET],self.old_blob[at:at+actions.CODE_OFFSET])
        self.assertEqual(sha256(self.blob),self.report['blob_sha256'])
        self.assertEqual(sha256(self.module),self.e['sha256']);self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        restored=bytearray(self.blob);restored[at:at+self.e['bytes']]=self.old_blob[at:at+self.e['bytes']]
        restored[4:8]=self.old_blob[4:8]
        updates=self.report['shared_runtime_refresh']['in_place_owner_updates']
        self.assertEqual(len(updates),1);self.assertEqual(updates[0]['vrom'],actions.PLAYER_RELOC)
        for row in updates:
            p=row['blob_offset'];n=row['bytes']
            self.assertEqual(sha256(self.blob[p:p+n]),row['sha256'])
            restored[p:p+n]=self.old_blob[p:p+n]
        self.assertEqual(restored,self.old_blob)
        for v in self.files.keys()-{BLOB,MODULE,actions.PLAYER_VROM,actions.PLAYER_RELOC,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),f'{v:08X}')
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(self.report.get(key),self.prior.get(key))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(HELD/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))


class ControlTests(unittest.TestCase):
    sanitized=shared_tests.HostTests.sanitized

    def test_fan_controls_setup_and_end_transitions(self):
        self.sanitized('v3_player_actions_test.c')

    @unittest.skipUnless((CONTROLS/'build.json').is_file(),'Current control cartridge required')
    def test_in_place_controls_preserve_tables_artwork_owners_and_profile(self):
        rom=(CONTROLS/'animal-forest-v3-asset-loader.z64').read_bytes()
        report=json.loads((CONTROLS/'build.json').read_bytes())
        base,prior=inputs(CONTROLS/'base-lock.json');files,before=by_vrom(rom),by_vrom(base)
        e=report['equipment_resources'];old=prior['equipment_resources'];a=e['player_actions']
        blob=files[BLOB].extract(rom);old_blob=before[BLOB].extract(base)
        self.assertEqual(e['vrom'],old['vrom']);self.assertEqual(e['bytes'],old['bytes'])
        self.assertEqual(e['blob_offset'],old['blob_offset']);self.assertEqual(len(blob),len(old_blob))
        at=e['blob_offset'];module=blob[at:at+e['bytes']]
        self.assertEqual(sha256(module),e['sha256']);self.assertEqual(zlib.crc32(module),e['crc32'])
        code=a['code'];self.assertEqual(sha256(module[actions.CODE_OFFSET:actions.CODE_OFFSET+code['bytes']]),code['sha256'])
        self.assertLessEqual(code['bytes'],actions.TABLE_OFFSET-actions.CODE_OFFSET)
        restored=bytearray(blob);start=at+actions.CODE_OFFSET;end=at+actions.TABLE_OFFSET
        restored[start:end]=old_blob[start:end];restored[4:8]=old_blob[4:8]
        self.assertEqual(restored,old_blob)
        self.assertEqual(a['tables'],old['player_actions']['tables'])
        self.assertEqual(a['disabled_indices'],list(range(105,121)))
        self.assertFalse(a['fan_action_installed']);self.assertEqual(a['enabled_imported_actions'],[])
        refresh=report['shared_runtime_refresh']
        self.assertFalse(refresh['resource_allocations_changed']);self.assertEqual(refresh['additional_resident_bytes'],0)
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(report.get(key),prior.get(key))
        for v in files.keys()-{BLOB,MODULE,0x19D40}:
            self.assertEqual(files[v].extract(rom),before[v].extract(base),f'{v:08X}')
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        bindings=actions.control_bindings(source,files[actions.PLAYER_VROM].extract(rom),
            files[CODE_VROM].extract(rom),original,old)
        self.assertEqual(json.loads(json.dumps(bindings)),a['fan_control_flow'])
        owner=bytearray(files[actions.PLAYER_VROM].extract(rom));owner[0x808B4A44-actions.PLAYER_RAM]^=1
        with self.assertRaisesRegex(ValueError,'native player control API'):
            actions.control_bindings(source,owner,files[CODE_VROM].extract(rom),original,old)
        self.assertEqual(apply_ups(original,(CONTROLS/'asset-loader.ups').read_bytes()),rom)
        self.assertEqual(struct.unpack_from('>2I',rom,0x10),n64_checksum(rom))


class StartupTests(unittest.TestCase):
    sanitized=shared_tests.HostTests.sanitized

    def test_expanded_module_startup_and_failure_paths(self):
        self.sanitized('v3_equipment_startup_test.c',('runtime/crc32.c',),
                       ('-DAF_V3_EQUIPMENT_BYTES=24576',))

    def test_original_size_startup_contract(self):
        self.sanitized('v3_equipment_startup_test.c',('runtime/crc32.c',))


@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current action-table cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.e=cls.report['equipment_resources']
        cls.a=cls.e['player_actions'];cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old_blob=cls.before[BLOB].extract(cls.base)
        cls.module=cls.blob[cls.e['blob_offset']:cls.e['blob_offset']+cls.e['bytes']]
        cls.source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_tables_original_actions_and_disabled_missing_callbacks(self):
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();files=by_vrom(original)
        data,rows,patches,removed,*_=actions.expanded_tables(self.source,
            files[actions.PLAYER_VROM].extract(original),files[actions.PLAYER_RELOC].extract(original))
        self.assertEqual(self.module[actions.TABLE_OFFSET:actions.TABLE_OFFSET+len(data)],data)
        self.assertEqual(len(rows),27);self.assertEqual(len(removed),56)
        self.assertEqual(sum(r['width']==1 for r in rows),22)
        for row in rows:
            table=self.module[row['offset']:row['offset']+row['bytes']]
            self.assertEqual(sha256(table[:105*row['width']]),row['native_sha256'])
            self.assertEqual(len(table),121*row['width'])
            if row['width']==4:self.assertEqual(table[105*4:],bytes(16*4))
            else:self.assertEqual(table[105:],bytes.fromhex(row['source_hex'])[105:])
        # The fan's net callback is NOT null in the donor. Its dependency must
        # remain recorded rather than being silently omitted when enabling it.
        net=next(r for r in rows if r['native_entry']==0x808BE620)
        self.assertEqual(net['source_callbacks'][109]['symbol'],
                         'Player_actor_Item_net_CulcJointAngle_dummy_net_reset')
        self.assertEqual(self.a['disabled_indices'],list(range(105,121)))
        self.assertEqual(self.a['enabled_imported_actions'],[])
        self.assertFalse(self.a['fan_action_installed'])
        damaged=bytearray(files[actions.PLAYER_VROM].extract(original))
        struct.pack_into('>I',damaged,0x808B3388-actions.PLAYER_RAM,0x2862006A)
        with self.assertRaisesRegex(ValueError,'bound inventory'):
            actions.expanded_tables(self.source,damaged,files[actions.PLAYER_RELOC].extract(original))

    def test_only_declared_owner_instructions_and_relocations_change(self):
        owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        old=self.before[actions.PLAYER_VROM].extract(self.base);restored=bytearray(owner)
        self.assertEqual(sha256(owner),self.a['owner_sha256'])
        for row in self.a['patches']:
            at=row['offset'];self.assertEqual(struct.unpack_from('>I',owner,at)[0],row['after'])
            self.assertEqual(struct.unpack_from('>I',old,at)[0],row['before'])
            struct.pack_into('>I',restored,at,row['before'])
        self.assertEqual(restored,old)
        reloc=self.files[actions.PLAYER_RELOC].extract(self.rom)
        old_reloc=self.before[actions.PLAYER_RELOC].extract(self.base)
        self.assertEqual(len(reloc),len(old_reloc))
        self.assertEqual(sha256(reloc),self.a['relocation_sha256'])
        self.assertEqual(sha256(reloc),self.e['player_motion']['reloc_sha256'])
        old_sections=struct.unpack_from('>5I',old_reloc);sections=struct.unpack_from('>5I',reloc)
        self.assertEqual(sections[:4],old_sections[:4]);self.assertEqual(old_sections[4]-sections[4],56)
        spec=SimpleNamespace(ram=actions.PLAYER_RAM,resident_bytes=len(owner),sections=sections)
        for base in (0x80200000,0x80300000):
            live=relocate_verified_data(spec,owner,reloc,base)
            for row in self.a['tables']:
                for high,low in row['references']:
                    hi=struct.unpack_from('>I',live,high-actions.PLAYER_RAM)[0]&65535
                    lo=struct.unpack_from('>h',live,low-actions.PLAYER_RAM+2)[0]
                    self.assertEqual((hi<<16)+lo,row['ram'])
            hi,lo,target=actions.RETAINED_BOUNDARY
            value=(struct.unpack_from('>I',live,hi-actions.PLAYER_RAM)[0]&65535)<<16
            value+=struct.unpack_from('>h',live,lo-actions.PLAYER_RAM+2)[0]
            self.assertEqual(value,base+target-actions.PLAYER_RAM)
            for entry,register in actions.DISPATCH:
                helper='af_v3_player_action_t9' if register==25 else 'af_v3_player_action_v0'
                self.assertEqual(struct.unpack_from('>I',live,entry-actions.PLAYER_RAM)[0],
                    actions.jump(self.a['code']['symbols'][helper],link=True))

    def test_complete_module_artwork_profiles_and_other_resources_retained(self):
        old=self.prior['equipment_resources'];at=old['blob_offset']
        self.assertEqual(self.module[:actions.SIZE],self.old_blob[at:at+actions.SIZE])
        self.assertEqual(self.e['records'],old['records'])
        self.assertEqual(self.e['player_motion']['records'],old['player_motion']['records'])
        self.assertEqual(self.e['kind_readers'],old['kind_readers'])
        self.assertEqual(self.e['additional_resident_bytes'],0x4000)
        self.assertLessEqual(actions.RAM+len(self.module),self.report['furniture']['bank_pool']['start'])
        self.assertEqual(sha256(self.module),self.e['sha256'])
        self.assertEqual(zlib.crc32(self.module),self.e['crc32'])
        self.assertEqual(self.module[-16:],struct.pack('>4I',*([actions.GUARD]*4)))
        unchanged,tail=reuse_resource_tail(self.base,self.prior,self.old_blob)
        retained=bytearray(self.blob[:len(unchanged)]);retained[4:8]=unchanged[4:8]
        self.assertEqual(retained,unchanged)
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(self.report.get(key),self.prior.get(key))
        for v in self.files.keys()-{BLOB,MODULE,actions.PLAYER_VROM,actions.PLAYER_RELOC,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),f'{v:08X}')
        stripped,_=reuse_resource_tail(self.rom,self.report,self.blob)
        self.assertGreaterEqual(len(stripped),self.e['blob_offset']+len(self.module))
        self.assertEqual(self.report['shared_runtime_refresh']['changed_owner_moves'][0]['vrom'],actions.PLAYER_RELOC)

    def test_code_startup_crc_and_reconstructible_patch(self):
        code=self.a['code'];at=actions.CODE_OFFSET
        self.assertEqual(sha256(self.module[at:at+code['bytes']]),code['sha256'])
        self.assertLessEqual(code['bytes'],actions.TABLE_OFFSET-at)
        startup=self.report['startup'];self.assertLessEqual(startup['bytes'],CONFIG-STARTUP)
        self.assertIn('-DAF_V3_EQUIPMENT_BYTES=0x6000u',startup['flags'])
        resident=bytearray(self.files[MODULE].extract(self.rom));before=self.before[MODULE].extract(self.base)
        self.assertEqual(sha256(resident[STARTUP:STARTUP+startup['bytes']]),startup['sha256'])
        self.assertEqual(struct.unpack_from('>4I',resident,CONFIG),
            (BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),self.report['runtime_abi']))
        resident[STARTUP:CONFIG+16]=before[STARTUP:CONFIG+16];self.assertEqual(resident,before)
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)


if __name__=='__main__':unittest.main()
