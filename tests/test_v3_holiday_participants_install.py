"""Connected current-cartridge check; no emulator or historical build replay."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import BLOB
from v3_furniture_install import inputs


class ParticipantInstallTests(unittest.TestCase):
    def test_changed_profile_loader(self):
        from tests.test_v3_equipment_runtime import HostTests
        HostTests.sanitized(self,'v3_effect_loader_test.c',defines=(
            '-DAF_EFFECT_COUNT=9u','-DAF_EFFECT_ROOM_COUNT=4u','-DAF_EFFECT_SKY_COUNT=4u',
            '-DAF_EFFECT_CODE_START=0x804D0000u','-DAF_EFFECT_CODE_END=0x804D8000u',
            '-DAF_EFFECT_SKY_START=0x80738000u','-DAF_EFFECT_SKY_END=0x80739C50u',
            '-DAF_EFFECT_PARTICIPANT_START=0x8073C010u','-DAF_EFFECT_PARTICIPANT_END=0x80745EE0u'))

    def test_current_connected_cartridge(self):
        from v3_event_text import install as install_text
        from v3_resource_capacity import checked_limit
        from v3_sound_programs import installed_resource,reuse_audio_storage
        from v3_room_effects import restore_controller,rebind_profiles
        directory=ROOT/os.environ.get('V3_PARTICIPANTS_BUILD','build/v3-diary-category-work-01/participants-installed-03')
        image,report=inputs(directory/'build-lock.json');base,prior=inputs(directory/'base-lock.json')
        files=by_vrom(image);original=by_vrom(base);core=files[CODE_VROM].extract(image)
        e=report['equipment_resources'];events=e['npc_extra']['events'];r=events['participants'];p=r['packet']
        prepared=ROOT/r['prepared'];blob=files[BLOB].extract(image)
        data=image[p['physical']:p['physical']+p['bytes']]
        self.assertEqual((sha256(data),zlib.crc32(data)),(p['sha256'],p['crc32']))
        previous=r['preserved_sky_packet'];n=previous['bytes']
        self.assertEqual(data[:n],base[previous['physical']:previous['physical']+n])
        code=r['code'];symbols=code['symbols'];body=data[n:]
        self.assertEqual(sha256(body),code['sha256']);self.assertEqual(body[-16:],b'AFHP'*4)
        lo,hi=code['bss_bounds'];start=r['loaded_code']['ram']
        self.assertFalse(any(body[lo-start:hi-start]));self.assertEqual(u32(body,symbols['af_hp_available']-start),0)
        self.assertEqual(e['holiday_state']['packet'],prior['equipment_resources']['holiday_state']['packet'])
        for row in r['installed_hooks']:
            owner=files[row['vrom']].extract(image);at=row['address']-row['ram'];want=bytes.fromhex(row['after'])
            self.assertEqual(owner[at:at+len(want)],want)
        self.assertEqual(len(r['installed_hooks']),21)
        # Check the actual linked failure guard and its native return target.
        # Success retains the original initialization; failure skips every
        # dereference and leaves the manager eligible for a later retry.
        at=symbols['af_hp_manager_alloc']-start
        self.assertEqual(struct.unpack_from('>10I',body,at),(
            0x14400007,0xAE020000,0x24080046,0xAE080004,0x2408FFFF,
            0xAE080008,0x00001821,0x27FF005C,0x03E00008,0))
        guard=next(h for h in r['installed_hooks'] if h['replacement']=='af_hp_manager_alloc')
        self.assertEqual(guard['address']+8+0x5C,guard['failure_return'])
        self.assertEqual(files[guard['relocation_vrom']].extract(image),original[guard['relocation_vrom']].extract(base))
        text=r['dialogue'];self.assertEqual((text['count'],text['choice_count']),(279,2))
        for row in text['resources']:
            self.assertEqual(files[row['vrom']].extract(image),(directory/row['file']).read_bytes())
        self.assertEqual(files[0x1FA0000].pstart,original[0x1FA0000].pstart)
        self.assertEqual(text['physical_relocation']['moved_bytes'],50976)
        for row in text['hooks']:self.assertEqual(u32(core,row['address']-CODE_RAM),row['after'])
        # The generic text installer also accepts an already split bank layout.
        repeat=copy.deepcopy(text)
        for row in repeat['resources']:row['original_sha256']=row['sha256']
        restored=install_text(bytearray(image),image,directory,repeat,relocate=True,
            physical_resources=report['physical_resources'],reserved_end=prior['resource_capacity']['reserved_physical_end'])
        self.assertEqual(restored,image)
        bad=bytearray(image);bad[files[0x1FA0000].pstart]^=1
        with self.assertRaisesRegex(ValueError,'already modified'):
            install_text(bad,image,directory,repeat,relocate=True)
        self.assertEqual(checked_limit(image,report),0x2800000)
        effects=e['room_rigs']['effects'];controller=effects['controller']
        self.assertEqual(controller['count'],120)
        old=prior['equipment_resources']['room_rigs']['effects']['controller']
        self.assertEqual(restore_controller(files[controller['vrom']].extract(image),files[controller['reloc']].extract(image),controller),
            restore_controller(original[old['vrom']].extract(base),original[old['reloc']].extract(base),old))
        retained=bytearray(blob)
        rebind_profiles(effects,retained,e['room_rigs']['code']['symbols'],code_bounds=(0x804D0000,0x804D8000))
        self.assertEqual(retained,blob)
        for k,kind,index in (('sequence','seq',199),('font','bank',140),('wave','wave',5)):
            actual,header,physical=installed_resource(image,core,kind,index);row=r['coin']['audio'][k]
            self.assertEqual((sha256(actual),physical,header.hex()),(row['sha256'],row['physical'],row['header_after']))
            self.assertEqual(actual,(prepared/f'coin-{k}.bin').read_bytes())
        # Reusing the same owned audio arenas is stable; corrupt allocation
        # receipts are rejected before any cartridge can be emitted.
        payloads={('seq',199):(prepared/'coin-sequence.bin').read_bytes(),('bank',140):(prepared/'coin-font.bin').read_bytes()}
        audio_blob=bytearray(blob);reuse_audio_storage(image,report,audio_blob,core,payloads)
        self.assertEqual(audio_blob,blob)
        altered=copy.deepcopy(report);altered['equipment_resources']['furniture_audio']['font']['allocation']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'allocation'):
            reuse_audio_storage(image,altered,bytearray(blob),core,payloads)
        # One startup row loads both sky and participants; the descriptor table
        # still fits the retained nineteen-entry startup reservation.
        boot=e['surface_bootstrap']['code'];at=boot['symbols']['packets']-e['ram']+e['blob_offset']
        rows=[struct.unpack_from('>5I',blob,at+i*20) for i in range(19)]
        self.assertEqual(sum(row[:3]==(p['ram'],p['physical']|0x80000000,p['bytes']) for row in rows),1)
        self.assertEqual(boot['bytes'],688)


if __name__=='__main__':unittest.main()
