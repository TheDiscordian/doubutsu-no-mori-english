"""Shared program conversion and current per-frame cartridge integration."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,n64_checksum,sha256
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
import v3_player_actions as actions
import v3_sound_programs as sounds

OUTPUT=ROOT/os.environ.get('V3_PLAYER_FRAME_BUILD','build/v3-player-frame-sound-01')


class ProgramTests(unittest.TestCase):
    def loop_program(self, long=True, loop_mode=False):
        # Synthetic attack/hold envelope and timed sustained note.
        data=bytearray.fromhex('880004ffc607cb0000e0c466')
        data.extend(bytes((0x81,0x20)) if long else bytes((12,)))
        data.extend(bytes((50,0xFB,0,10 if loop_mode else 11)))
        data.extend(bytes(len(data)&1));struct.pack_into('>H',data,7,len(data))
        data.extend(struct.pack('>4h',12,24000,-1,0))
        return data

    def test_sustained_loop_and_short_envelope_relocate_without_changing_timing(self):
        for long in (False,True):
            for mode in (False,True):
                raw=self.loop_program(long,mode);desc=sounds.looping_layer(raw,0)
                self.assertEqual(desc['duration'],288 if long else 12)
                self.assertEqual(desc['loop'],10 if mode else 11)
                bound=sounds.bind_loop(raw,desc,0x5000,12)
                actual=sounds.looping_layer(bound,0x5000,prefix=True)
                for key in ('note','duration','velocity','decay','envelope_bytes'):
                    self.assertEqual(actual[key],desc[key])
                self.assertEqual(actual['loop'],desc['loop']+4)
                restored=bytearray(bound[4:]);restored[5]=raw[5]
                for at in desc['pointers']:restored[at:at+2]=raw[at:at+2]
                self.assertEqual(restored,raw)

    def test_incomplete_loop_envelope_pointer_and_zero_time_reject(self):
        raw=self.loop_program();desc=sounds.looping_layer(raw,0)
        for size in range(len(raw)):
            with self.subTest(size=size),self.assertRaises(ValueError):sounds.looping_layer(raw[:size],0)
        for at,value in ((0,0x89),(2,6),(4,0xC5),(5,126),(6,0xCA),(8,255),(10,0xC3),
                         (11,0x80),(14,128),(15,0xFA),(17,12),(22,0),(25,1)):
            bad=raw.copy();bad[at]=value
            with self.subTest(at=at),self.assertRaises(ValueError):sounds.looping_layer(bad,0)
        zero=raw.copy();zero[12:14]=bytes((0x80,0))
        with self.assertRaises(ValueError):sounds.looping_layer(zero,0)
        for offset,index in ((1,7),(65530,7),(0,126)):
            with self.assertRaises(ValueError):sounds.bind_loop(raw,desc,offset,index)

    def test_mode_before_envelope_retains_the_actual_loop_restart(self):
        for target in (6,7,11):
            # Alternate compiler layout: sustain before envelope setup.
            raw=self.loop_program();raw[6:11]=bytes((0xC4,0xCB,0,18,224))
            raw[17]=target
            description=sounds.looping_layer(raw,0)
            self.assertEqual(description['pointers'],[1,8,16])
            bound=sounds.bind_loop(raw,description,0x4100,12,1)
            actual=sounds.looping_layer(bound,0x4100,prefix=True)
            self.assertEqual(actual['loop'],target+4)
            self.assertEqual(bound[:4],bytes((0xEB,1,12,0xC4)))
            for key in ('note','duration','velocity','decay','envelope_bytes'):
                self.assertEqual(actual[key],description[key])
            restored=bytearray(bound[4:]);restored[5]=raw[5]
            for at in description['pointers']:restored[at:at+2]=raw[at:at+2]
            self.assertEqual(restored,raw)
            bad=raw.copy();bad[17]=8
            with self.assertRaisesRegex(ValueError,'Loop target'):sounds.looping_layer(bad,0)

    def program(self,sweep=True,long=False):
        # Original synthetic sequence, not copied donor artwork/audio.
        result=bytearray.fromhex('eb0102880007ffcb0000e0')
        if sweep:result.extend(bytes((0xC7,0x82,40,32)))
        result.append(0x60)
        result.extend(bytes((0x81,0x20)) if long else bytes((12,)))
        result.extend(bytes((90,255)));result.extend(bytes(len(result)%2))
        struct.pack_into('>H',result,8,len(result))
        result.extend(struct.pack('>6h',4,20000,20,4000,-1,0))
        return result

    def test_complete_plain_and_pitch_swept_notes_relocate_only_bindings(self):
        for sweep in (False,True):
            for long in (False,True):
                raw=self.program(sweep,long);desc=sounds.single_layer(raw,0,len(raw))
                self.assertEqual(desc['duration'],288 if long else 12)
                self.assertEqual(bool(desc['sweep']),sweep)
                bound=sounds.bind_program(raw,desc,0x3000,7)
                reparsed=sounds.single_layer(bytes(0x3000)+bound,0x3000,0x3000+len(bound))
                self.assertEqual(reparsed['instrument'],7)
                for key in ('note','sweep','duration','velocity','decay','envelope_bytes'):
                    self.assertEqual(reparsed[key],desc[key])
                restored=bytearray(bound);restored[2]=raw[2]
                for at in desc['pointers']:restored[at:at+2]=raw[at:at+2]
                self.assertEqual(restored,raw)

    def test_unsupported_or_incomplete_forms_fail(self):
        raw=self.program();desc=sounds.single_layer(raw,0,len(raw))
        for at,value in ((0,0xEC),(3,0x89),(5,8),(7,0xCA),(9,255),(12,1),(13,128),(14,0),(15,0x80)):
            broken=raw.copy();broken[at]=value
            with self.subTest(at=at),self.assertRaises(ValueError):sounds.single_layer(broken,0,len(broken))
        for offset,instrument in ((1,0),(65530,0),(0,126)):
            with self.assertRaises(ValueError):sounds.bind_program(raw,desc,offset,instrument)
        with self.assertRaises(ValueError):sounds.single_layer(raw[:-1],0,len(raw)-1)


@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current frame/sound cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.image),by_vrom(cls.base)
        cls.core=cls.files[CODE_VROM].extract(cls.image)
        cls.e=cls.report['equipment_resources'];cls.s=cls.e['sound_programs']

    def test_complete_shared_sound_registration_and_dependency_identity(self):
        blob,_=reuse_resource_tail(self.base,self.prior,self.before[BLOB].extract(self.base))
        code=bytearray(self.before[CODE_VROM].extract(self.base))
        ids=[r['source_sound_id'] for r in self.s['imports']]
        recreated=sounds.install(self.base,self.prior,blob,code,ids)
        self.assertEqual(recreated,self.s)
        actual,entry,physical=sounds.installed_resource(self.image,self.core,'seq',199)
        row=self.s['sequence'];self.assertEqual(sha256(actual),row['sha256'])
        self.assertEqual(physical,row['physical']);self.assertEqual(entry.hex(),row['header_after'])
        old,_,_=sounds.installed_resource(self.base,self.before[CODE_VROM].extract(self.base),'seq',199)
        restored=bytearray(actual[:len(old)])
        for r in self.s['imports']:
            index=r['native_sound_id']&255;at=0x4C30+2*index
            struct.pack_into('>H',restored,at,r['original_table_pointer'])
            self.assertEqual(struct.unpack_from('>H',actual,at)[0],r['offset'])
            self.assertFalse(r['new_instrument']);self.assertFalse(r['new_sample'])
            self.assertEqual(r['source_bank'],154);self.assertEqual(r['native_bank'],140)
            self.assertEqual(r['native_instrument'],12)
        self.assertEqual(restored,old)
        restored=bytearray(self.core);at=row['header_address']-CODE_RAM
        restored[at:at+16]=bytes.fromhex(row['header_before'])
        self.assertEqual(restored,self.before[CODE_VROM].extract(self.base))
        self.assertEqual(sounds.permanent_budget(self.core),self.s['after_budget'])
        self.assertEqual(self.s['after_budget']['conservative_spare'],224)
        self.assertFalse(self.s['after_budget']['heap_changed'])

    def test_occupied_slots_and_changed_interpreter_are_rejected(self):
        for ids in ([],[0x167,0x167],[0x167],[0x169],[0x200]):
            blob,_=reuse_resource_tail(self.image,self.report,self.files[BLOB].extract(self.image))
            with self.subTest(ids=ids),self.assertRaises(ValueError):
                sounds.install(self.image,self.report,blob,bytearray(self.core),ids)
        code=bytearray(self.core);code[0x800F3994-CODE_RAM]^=1
        with self.assertRaises(ValueError):sounds.install(self.image,self.report,bytearray(),code,[0x167])

    def test_per_frame_code_keeps_actions_disabled_and_all_existing_resources(self):
        old=self.prior['equipment_resources'];a=self.e['player_actions'];before=old['player_actions']
        blob=self.files[BLOB].extract(self.image);old_blob=self.before[BLOB].extract(self.base)
        at=self.e['blob_offset'];module=blob[at:at+self.e['bytes']]
        self.assertEqual(at,old['blob_offset']);self.assertEqual(self.e['bytes'],old['bytes'])
        self.assertEqual(module[:actions.CODE_OFFSET],old_blob[at:at+actions.CODE_OFFSET])
        self.assertEqual(module[actions.TABLE_OFFSET:],old_blob[at+actions.TABLE_OFFSET:at+old['bytes']])
        self.assertEqual(sha256(module),self.e['sha256']);self.assertEqual(zlib.crc32(module),self.e['crc32'])
        code=a['code'];self.assertIn('af_v3_player_fan_main',code['symbols'])
        self.assertEqual(sha256(module[actions.CODE_OFFSET:actions.CODE_OFFSET+code['bytes']]),code['sha256'])
        self.assertLessEqual(code['bytes'],actions.TABLE_OFFSET-actions.CODE_OFFSET)
        self.assertEqual(a['tables'],before['tables']);self.assertEqual(a['enabled_imported_actions'],[])
        self.assertFalse(a['fan_action_installed']);self.assertFalse(a['fan_frame_flow']['poll_hooks_installed'])
        self.assertEqual(a['fan_control_flow']['frame_speed'],1.0)
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        bindings=actions.control_bindings(source,self.files[actions.PLAYER_VROM].extract(self.image),
            self.core,original,old)
        self.assertEqual(json.loads(json.dumps(bindings)),a['fan_control_flow'])
        for key in ('save_runtime','furniture','catalogue','clothing_profile','hra','feng_shui'):
            self.assertEqual(self.report.get(key),self.prior.get(key))
        for v in self.files.keys()-{BLOB,MODULE,CODE_VROM,0x19D40}:
            self.assertEqual(self.files[v].extract(self.image),self.before[v].extract(self.base),f'{v:08X}')
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.image)
        self.assertEqual(struct.unpack_from('>2I',self.image,0x10),n64_checksum(self.image))


if __name__=='__main__':unittest.main()
