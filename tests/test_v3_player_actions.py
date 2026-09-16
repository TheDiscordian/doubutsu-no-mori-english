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
