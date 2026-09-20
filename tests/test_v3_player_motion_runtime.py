"""Complete player motion, preserved native readers, and actual owner relocation."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest
import zlib
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,n64_checksum
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs,reuse_resource_tail
from npc_mail_show import relocate_verified_data
import v3_equipment_runtime as runtime
import tests.test_v3_equipment_runtime as shared_tests

OUTPUT=ROOT/os.environ.get('V3_PLAYER_MOTION_BUILD','build/v3-equipment-kinds-runtime-01')
REWARD=ROOT/os.environ.get('V3_REWARD_MOTION_BUILD','build/v3-shared-reward-motion-03')


class FaceHostTests(unittest.TestCase):
    sanitized=shared_tests.HostTests.sanitized
    def test_shared_face_sequence_bounds_and_native_fallback(self):
        self.sanitized('v3_equipment_resources_test.c',defines=('-DAF_V3_PLAYER_FACES=1',))


@unittest.skipUnless((REWARD/'build-lock.json').is_file(),'Current reward-motion proposal required')
class RewardMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(REWARD/'build-lock.json');cls.base,cls.prior=inputs(REWARD/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.motion=cls.e['player_motion'];cls.reward=cls.motion['reward_motion'];cls.faces=cls.motion['faces']
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.oldblob=cls.before[BLOB].extract(cls.base)
        at=cls.e['blob_offset'];cls.module=cls.blob[at:at+cls.e['bytes']]
        cls.oldmodule=cls.oldblob[at:at+cls.old['bytes']]
        cls.source=runtime.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_motions_and_face_timelines(self):
        from unittest.mock import patch
        assets,rows,evidence=runtime.reward_animation_sources(self.source)
        self.assertEqual(json.loads(json.dumps(evidence)),self.reward['source'])
        self.assertEqual([r['source_index'] for r in rows],[128,130])
        for expected,row in zip(rows,self.reward['records']):
            self.assertEqual(expected,{k:v for k,v in row.items() if k not in ('vrom','blob_offset','storage')})
            self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']],assets[row['source_index']])
            self.assertEqual(row['source']['duration'],53);self.assertLessEqual(row['bytes'],runtime.PLAYER_CAPACITY)
            self.assertEqual(struct.unpack_from('>4I',self.module,runtime.PLAYER_TABLE+16+16*row['source_index']),
                             (row['vrom'],row['bytes'],row['pointer'],row['type']))
        table,data,faces=runtime.player_face_sources(self.source,self.motion['records'])
        for key,value in json.loads(json.dumps(faces)).items():self.assertEqual(value,self.faces[key])
        self.assertEqual(self.module[runtime.FACE_TABLE:runtime.FACE_TABLE+len(table)],table)
        self.assertEqual(self.module[runtime.FACE_DATA:runtime.FACE_DATA+len(data)],data)
        self.assertEqual((len(table),len(data)),(1272,213))
        for row in faces['arrays']:
            at=row['ram']-runtime.RAM
            raw=self.source.data[row['donor_offset']:row['donor_offset']+row['bytes']]
            self.assertEqual(self.module[at:at+len(raw)],raw)
        original=self.source.function
        for at in (0x198334,0x69E7C,0x69EA8):
            def changed(entry):
                data,receipt=original(entry)
                return (bytes([data[0]^1])+data[1:],receipt) if entry==at else (data,receipt)
            with patch.object(self.source,'function',side_effect=changed),self.assertRaises(ValueError):
                if at==0x198334:runtime.reward_animation_sources(self.source)
                else:runtime.player_face_sources(self.source,self.motion['records'])

    def test_checked_reclaimed_storage_and_complete_existing_resources(self):
        import copy
        assets,rows,_=runtime.reward_animation_sources(self.source)
        core=self.before[CODE_VROM].extract(self.base)
        blob,_=reuse_resource_tail(self.base,self.prior,self.oldblob)
        actual=bytearray(blob)
        storage=runtime.store_player_assets(self.base,self.old,actual,core,assets,rows)
        self.assertEqual(storage,self.reward['storage']);self.assertEqual(rows,self.reward['records'])
        self.assertEqual([r['storage'] for r in rows],['retired-sequence-tail','appended'])
        self.assertEqual(len(self.blob)-len(self.oldblob),3072)
        for row in self.old['records']+self.old['player_motion']['records']:
            at=row['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],self.oldblob[at:at+row['bytes']])
        for mutation in ('occupied','sequence'):
            altered=bytearray(blob);old=copy.deepcopy(self.old)
            if mutation=='occupied':altered[storage['first']]=1
            if mutation=='sequence':altered[old['sound_programs']['sequence']['blob_offset']]^=1
            with self.assertRaises(ValueError):
                runtime.store_player_assets(self.base,old,altered,core,assets,copy.deepcopy(rows))
        occupied=copy.deepcopy(self.old);occupied['player_motion']['records'].append(
            dict(blob_offset=storage['first'],bytes=1024))
        safe=bytearray(blob);moved=copy.deepcopy(rows)
        runtime.store_player_assets(self.base,occupied,safe,core,assets,moved)
        self.assertEqual(safe[storage['first']:storage['first']+1024],blob[storage['first']:storage['first']+1024])
        for row in moved:
            self.assertFalse(row['blob_offset']<storage['first']+1024 and storage['first']<row['blob_offset']+row['bytes'])
        retained=bytearray(self.module)
        retained[runtime.FACE_CODE:runtime.FACE_END]=self.oldmodule[runtime.FACE_CODE:runtime.FACE_END]
        for row in rows:
            at=runtime.PLAYER_TABLE+16+16*row['source_index'];retained[at:at+16]=self.oldmodule[at:at+16]
        self.assertEqual(retained,self.oldmodule)
        self.assertEqual(self.e['bytes'],self.old['bytes']);self.assertEqual(self.e['additional_resident_bytes'],0)

    def test_only_face_hooks_change_and_original_tables_are_retained(self):
        core=bytearray(self.files[CODE_VROM].extract(self.rom));old=self.before[CODE_VROM].extract(self.base)
        for row in self.faces['hooks']:
            at=row['entry']-CODE_RAM
            self.assertEqual(core[at:at+8].hex(),row['after']);self.assertEqual(old[at:at+8].hex(),row['before'])
            self.assertEqual(sha256(old[at:at+row['native_bytes']]),row['native_sha256'])
            core[at:at+8]=old[at:at+8]
        self.assertEqual(core,old)
        for row in self.faces['retained_native']:
            at=row['entry']-CODE_RAM;self.assertEqual(sha256(core[at:at+row['bytes']]),row['sha256'])
        self.assertEqual(self.module[runtime.FACE_CODE:runtime.FACE_CODE+self.faces['code']['bytes']],
                         (REWARD/'player_faces/code.bin').read_bytes())
        for v in self.files.keys()-{BLOB,MODULE,CODE_VROM,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        for key in ('save_runtime','furniture','catalogue'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(self.e['optional_selection'],self.old['optional_selection'])
        self.assertFalse(self.reward['celebration_action_installed'])

    def test_exact_patch_and_optional_profiles(self):
        import v3_optional_composition as composer
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(REWARD/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(REWARD/'build-lock.json');choices=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(choices),128)
            self.assertEqual(composer.compose(self.rom,self.report,choices,composer.resolve(choices,list(choices)))[0],self.rom)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,choices,composer.resolve(choices,[]))[0]),
                             self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


class HostTests(unittest.TestCase):
    sanitized=shared_tests.HostTests.sanitized
    def test_actual_shared_equipment_and_player_readers(self):
        self.sanitized('v3_equipment_resources_test.c',
            defines=('-DAF_V3_PLAYER_MOTION=1','-DAF_V3_EQUIPMENT_KINDS=1'))


@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current player-motion cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.e=cls.report['equipment_resources']
        cls.motion=cls.e['player_motion'];cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.old_blob=cls.before[BLOB].extract(cls.base)

    def test_complete_source_motions_masks_and_buffer_limits(self):
        source=runtime.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        assets,records,mask,evidence=runtime.player_resources(source,original)
        self.assertEqual(json.loads(json.dumps(evidence)),self.motion['evidence']);self.assertEqual(len(records),8)
        module=self.blob[self.e['blob_offset']:self.e['blob_offset']+runtime.SIZE]
        self.assertEqual(module[runtime.PLAYER_MASK:runtime.PLAYER_MASK+27],mask)
        actual={r['source_index']:r for r in self.motion['records']}
        for expected in records:
            row=actual[expected['source_index']]
            self.assertEqual(expected,{k:v for k,v in row.items() if k not in ('vrom','blob_offset')})
            at=row['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],assets[row['source_index']])
            self.assertLessEqual(row['bytes'],runtime.PLAYER_CAPACITY)
            self.assertEqual(struct.unpack_from('>4I',module,runtime.PLAYER_TABLE+16+row['source_index']*16),
                             (row['vrom'],row['bytes'],row['pointer'],row['type']))
        for row in self.e['records']:
            at=row['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],self.old_blob[at:at+row['bytes']])
        self.assertEqual(self.e['records'],self.prior['equipment_resources']['records'])

    def test_shared_kind_source_fields_complete_motions_and_buffers(self):
        kind=self.e.get('kind_readers')
        if not kind:self.skipTest('Kind readers are not installed')
        from unittest.mock import patch
        source=runtime.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        bindings=runtime.kind_bindings(source)
        self.assertEqual(json.loads(json.dumps(bindings['functions'])),kind['source_functions'])
        self.assertEqual(json.loads(json.dumps(bindings['tables'])),kind['source_tables'])
        rows=kind['rows'];self.assertEqual(len(rows),79)
        module=self.blob[self.e['blob_offset']:self.e['blob_offset']+runtime.SIZE]
        self.assertEqual(struct.unpack_from('>4I',module,runtime.KIND_TABLE),(0x41464B44,1,79,12))
        resources={r['source_index']:r for r in self.e['records']}
        for source_row,row in zip(bindings['rows'],rows):
            for key,value in source_row.items():self.assertEqual(row[key],value)
            expected=[]
            for _,_,field,_ in runtime.KIND_ENTRIES:
                value=source_row[field]
                if field in ('player_animation','tumble','getup'):value+=130
                elif field in ('shape','animation'):value=value+17 if value in resources else -1
                expected.append(value)
            self.assertEqual(row['fields'],expected)
            self.assertEqual(struct.unpack_from('>6h',module,runtime.KIND_TABLE+16+12*row['source_kind']),tuple(expected))
            self.assertFalse(row['selectable']);self.assertFalse(row['player_actions_installed'])
            if row['combined_bank_bytes'] is not None:self.assertLessEqual(row['combined_bank_bytes'],runtime.CAPACITY)
        self.assertEqual({r['source_index'] for r in kind['new_player_motions']},{25,26,27,28})
        for row in kind['new_player_motions']:
            asset,compiled=runtime.compile_animations(source,[row['source']])
            at=row['blob_offset'];self.assertEqual(self.blob[at:at+row['bytes']],asset)
            self.assertEqual(row['compiled'],compiled);self.assertLessEqual(len(asset),runtime.PLAYER_CAPACITY)
            self.assertEqual(struct.unpack_from('>4I',module,runtime.PLAYER_TABLE+16+16*row['source_index']),
                (row['vrom'],row['bytes'],row['pointer'],row['type']))
        old_motion=self.prior['equipment_resources']['player_motion']['records']
        for row in old_motion:
            self.assertIn(row,self.motion['records']);at=row['blob_offset']
            self.assertEqual(self.blob[at:at+row['bytes']],self.old_blob[at:at+row['bytes']])
        # Verify the actual source guards reject changes, not just fixture counts.
        original_function=source.function
        for changed in (0x1708CC,0x177A14,0x178144):
            def mutate(address):
                raw,receipt=original_function(address)
                return (bytes([raw[0]^1])+raw[1:],receipt) if address==changed else (raw,receipt)
            with patch.object(source,'function',side_effect=mutate),self.assertRaises(ValueError):
                runtime.kind_bindings(source)

    def test_exact_owner_hooks_and_complete_relocation(self):
        vrom=self.motion['owner_vrom'];data=self.files[vrom].extract(self.rom)
        old=self.before[vrom].extract(self.base);restored=bytearray(data)
        hooks=self.motion['owner_hooks']+self.e.get('kind_readers',{}).get('owner_hooks',[])
        for row in hooks:
            at=row['entry']-runtime.PLAYER_RAM;n=row['end']-row['entry']
            self.assertEqual(data[at:at+n].hex(),row['after']);self.assertEqual(old[at:at+n].hex(),row['before'])
            restored[at:at+n]=old[at:at+n]
        self.assertEqual(restored,old)
        reloc=self.files[runtime.PLAYER_RELOC].extract(self.rom)
        self.assertEqual(reloc,self.before[runtime.PLAYER_RELOC].extract(self.base))
        spec=SimpleNamespace(ram=runtime.PLAYER_RAM,resident_bytes=len(data),sections=struct.unpack_from('>5I',reloc))
        for base in (0x80200000,0x80300000):
            actual=relocate_verified_data(spec,data,reloc,base)
            previous=relocate_verified_data(spec,old,reloc,base)
            for row in hooks:
                at=row['entry']-runtime.PLAYER_RAM
                for offset in row['retained_relocations']:
                    self.assertEqual(actual[at+offset:at+offset+4],previous[at+offset:at+offset+4])
                end=row['end']-runtime.PLAYER_RAM
                helper=row.get('helper','af_v3_equipment_kind_field')
                self.assertIn(struct.pack('>I',runtime.jump(self.e['code']['symbols'][helper])),actual[at:end])
        self.assertEqual(data[0x808BD3F8-runtime.PLAYER_RAM:0x808BD584-runtime.PLAYER_RAM],
                         old[0x808BD3F8-runtime.PLAYER_RAM:0x808BD584-runtime.PLAYER_RAM])

    def test_declared_core_module_and_other_owners(self):
        core=bytearray(self.files[CODE_VROM].extract(self.rom));old_core=self.before[CODE_VROM].extract(self.base)
        for row in self.e['hooks']+self.motion['hooks']:
            at=row['entry']-CODE_RAM
            self.assertEqual(core[at:at+8].hex(),row['after']);self.assertEqual(old_core[at:at+8].hex(),row['before'])
            core[at:at+8]=old_core[at:at+8]
        self.assertEqual(core,old_core)
        for v in self.files.keys()-{BLOB,CODE_VROM,MODULE,runtime.PLAYER_VROM,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),f'{v:08X}')
        old,tail=reuse_resource_tail(self.base,self.prior,self.old_blob)
        retained=bytearray(self.blob[:len(old)]);retained[4:8]=old[4:8]
        at=self.e['blob_offset'];retained[at:at+runtime.SIZE]=old[at:at+runtime.SIZE]
        self.assertEqual(retained,old)
        self.assertEqual(self.e['vrom'],self.prior['equipment_resources']['vrom'])
        self.assertEqual(self.e['additional_resident_bytes'],0)
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(self.report.get(key),self.prior.get(key))

    def test_checksums_startup_bridge_and_reconstructible_patch(self):
        e=self.e;module=self.blob[e['blob_offset']:e['blob_offset']+runtime.SIZE]
        self.assertEqual(sha256(module),e['sha256']);self.assertEqual(zlib.crc32(module),e['crc32'])
        self.assertLessEqual(e['code']['bytes'],runtime.PLAYER_BRIDGE)
        if e.get('kind_readers'):self.assertLessEqual(e['code']['bytes'],runtime.KIND_TABLE)
        self.assertEqual(sha256(module[:e['code']['bytes']]),e['code']['sha256'])
        self.assertEqual(module[runtime.PLAYER_BRIDGE:runtime.PLAYER_BRIDGE+16],
            bytes.fromhex('27BDFF80AFBF001C')+struct.pack('>II',runtime.jump(0x800B1DF0),0))
        resident=bytearray(self.files[MODULE].extract(self.rom));before=self.before[MODULE].extract(self.base)
        self.assertEqual(struct.unpack_from('>4I',resident,CONFIG),
            (BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),self.report['runtime_abi']))
        resident[STARTUP:CONFIG+16]=before[STARTUP:CONFIG+16];self.assertEqual(resident,before)
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)


if __name__=='__main__':unittest.main()
