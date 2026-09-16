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
