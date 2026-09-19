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
from aflib import CODE_VROM,by_vrom,sha256,apply_ups,n64_checksum
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

    def test_selected_equipment_bounds_and_passive_permissions(self):
        self.sanitized('v3_held_selection_test.c')

    def test_parent_names_prices_and_bounded_writes(self):
        self.sanitized('v3_held_items_test.c')

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
