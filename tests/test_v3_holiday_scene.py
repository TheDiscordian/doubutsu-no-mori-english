"""Focused announcement/connected installation checks; no native fixture replay."""
import os
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from textbanks import Bank
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_holiday_scene import contract,convert,FIRST
from v3_holiday_native import identities
from v3_event_text import MESSAGE,TABLE
from v3_password_policy import function

BASE=ROOT/'build/v3-diary-category-work-01/tortimer-state-05/build-lock.json'
CURRENT=ROOT/os.environ.get('V3_HOLIDAY_SCENE_BUILD','build/v3-diary-category-work-01/reserved-installed-01')


class HolidaySceneTests(unittest.TestCase):
    def test_groundhog_complete_ceremony(self):
        with tempfile.TemporaryDirectory(prefix='v3-holiday-groundhog-') as temp:
            executable=str(Path(temp)/'check')
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(ROOT/'overlays/v3'),
                'tests/v3_holiday_groundhog_test.c','overlays/v3/holiday_groundhog.c','-o',executable]
            for cmd in (command,[executable]):
                r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                if r.stdout:print(r.stdout.strip())

    def test_additional_installed_demo_connections(self):
        import zlib
        from v3_asset_loader import BLOB
        from v3_holiday_scene import DEMO_RAM,DEMO_END,DEMO_STATE,DEMO_HOOKS
        directory=ROOT/os.environ.get('V3_HOLIDAY_DEMO_BUILD',
            'build/v3-diary-category-work-01/event-scene-services-01')
        image,r=inputs(directory/'build-lock.json');base,prior=inputs(directory/'base-lock.json')
        e=r['equipment_resources'];stage=e['npc_extra']['events']['demo'];packet=e['holiday_state']['packet']
        self.assertTrue(stage['installed']);self.assertFalse(stage['event_owners_enabled'])
        self.assertFalse(stage['saved_format_changed']);self.assertEqual(stage['additional_resident_bytes'],0)
        self.assertEqual(stage['types'],{'eventmsg2':14,'speech':15})
        self.assertEqual(packet,e['holiday_fishing']['packet'])
        raw=image[packet['physical']:packet['physical']+packet['bytes']]
        old=base[packet['physical']:packet['physical']+packet['bytes']]
        a,b=DEMO_RAM-packet['ram'],DEMO_END-packet['ram']
        self.assertEqual(raw[:a],old[:a]);self.assertEqual(raw[b:],old[b:])
        self.assertEqual(sha256(raw),packet['sha256']);self.assertEqual(zlib.crc32(raw),packet['crc32'])
        self.assertEqual(sha256(raw[a:a+stage['code']['bytes']]),stage['code']['sha256'])
        self.assertLessEqual(DEMO_RAM+stage['code']['bytes'],DEMO_STATE)
        self.assertEqual(raw[DEMO_STATE-packet['ram']:b],bytes(64))
        files=by_vrom(image);before=by_vrom(base);core=bytearray(files[CODE_VROM].extract(image))
        self.assertEqual(len(stage['hooks']),len(DEMO_HOOKS))
        for hook,(address,name) in zip(stage['hooks'],DEMO_HOOKS,strict=True):
            self.assertEqual(hook['address'],address)
            self.assertEqual(hook['symbol'],'af_holiday_demo_'+name)
            at=address-CODE_RAM
            self.assertEqual(core[at:at+8],bytes.fromhex(hook['after']))
            self.assertEqual(u32(core,at),0x08000000|(stage['code']['symbols'][hook['symbol']]>>2&0x3FFFFFF))
            core[at:at+8]=bytes.fromhex(hook.get('previous',hook['before']))
        self.assertEqual(core,before[CODE_VROM].extract(base))
        # Original tables still own the original modes and official announcement reader.
        self.assertEqual(core[0x80104A74-CODE_RAM:0x80104B58-CODE_RAM],
            before[CODE_VROM].extract(base)[0x80104A74-CODE_RAM:0x80104B58-CODE_RAM])
        blob=files[BLOB].extract(image);symbols=e['surface_bootstrap']['code']['symbols']
        at=e['blob_offset']+symbols['packets']-e['ram']+17*20
        dest,address,size,crc,clear=struct.unpack_from('>5I',blob,at)
        self.assertEqual((dest,address,size,clear),(packet['ram'],packet['physical']|0x80000000,packet['bytes'],0))
        self.assertEqual(u32(blob,e['blob_offset']+crc-e['ram']),packet['crc32'])
        self.assertEqual(r['save_codec']['format_version'],prior['save_codec']['format_version'])
        self.assertEqual(r['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertEqual(files[MESSAGE].extract(image),before[MESSAGE].extract(base))
        self.assertEqual(files[0x30A0000].extract(image),before[0x30A0000].extract(base))
        if stage.get('groundhog'):
            g=stage['groundhog']
            self.assertEqual(len(g['source_functions']),15)
            self.assertFalse(g['actor_services_bound'])
            self.assertEqual((g['states'],g['source_updates_per_native_frame']),(9,2))
            self.assertEqual(g['clip_pointer_ram'],DEMO_STATE+24)
            self.assertEqual(stage['bindings']['af_hg_live'],g['clip_pointer_ram'])
            for name in ('begin','end','step','signal','read','commit'):
                self.assertIn('af_holiday_groundhog_'+name,stage['code']['symbols'])
            if stage.get('scene_services'):
                self.assertFalse(g['required_for_diary_attendance'])
                self.assertEqual(g['scope_schedule_rows'],{
                    '7':['020200070202000800000007'],'81':['020200090202001000000051']})
        if stage.get('scene_services'):
            live=stage['scene_services'];self.assertTrue(live['installed'])
            self.assertFalse(live['native_execution_verified'])
            self.assertFalse(live['present_demo_imported']);self.assertFalse(live['ceremony_owner_in_scope'])
            self.assertEqual(live['room_console_request_offset'],0x47C)
            self.assertEqual(live['current_acre_offsets'],[0xE4,0xE5])
            for name in ('read','commit','tempo','climate','bind'):
                self.assertIn('af_holiday_scene_'+name,stage['code']['symbols'])
            room=files[0x82D7F0].extract(image)
            for a,b,digest in live['room_functions']:
                self.assertEqual(sha256(room[a-0x80936710:b-0x80936710]),digest)
            self.assertEqual(room,before[0x82D7F0].extract(base))

    def test_additional_announcement_speech_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='v3-holiday-demo-') as temp:
            out=Path(temp)
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(ROOT/'overlays/v3'),
                'tests/v3_holiday_demo_test.c','overlays/v3/holiday_demo.c','-o',str(out/'check')]
            for cmd in (command,[str(out/'check')]):
                r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                if r.stdout:print(r.stdout.strip())

    def test_complete_source_and_host_reader(self):
        base,_=inputs(BASE)
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        checked=contract(base,source);packet,payload,table,report=convert(base,checked)
        self.assertEqual((report['added'],report['reused']),(4,28))
        old=by_vrom(base)
        before=Bank('message',0,0,old[MESSAGE].extract(base),old[TABLE].extract(base)).entries()
        after=Bank('message',0,0,payload,table).entries()
        self.assertEqual(len(after),FIRST+4);self.assertEqual(before,after[:FIRST])
        # Compile the actual donor switch, not a second copy of the parser's map.
        header=(ROOT/'local/ac-decomp/include/m_event.h').read_text()
        enum=re.search(r'enum event_table\s*\{[^{}]+\}\s*;',header)[0]
        body=function((ROOT/'local/ac-decomp/src/game/m_demo.c').read_text(),'get_title_no_for_event')
        ids,_=identities()
        fixture='typedef short s16;\n'+enum+'\n'+body+'\n'
        fixture+='static const unsigned short message_ids[]={'+','.join(str(r['id']) for r in report['rows'])+'};\n'
        for name,data in (('af_holiday_scene_titles',packet),('af_holiday_native_ids',ids[:128]),
                          ('af_holiday_source_ids',ids[128:])):
            fixture+='const unsigned char '+name+'[]={'+','.join(map(str,data))+'};\n'
        with tempfile.TemporaryDirectory(prefix='v3-holiday-scene-') as temp:
            out=Path(temp);write_new(out/'holiday-scene-data.h',fixture.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections',
                '-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'overlays/v3'),'-I'+str(out),
                'tests/v3_holiday_scene_test.c','overlays/v3/holiday_scene.c','overlays/v3/holiday_native.c',
                '-o',str(out/'check')]
            for cmd in (command,[str(out/'check')]):
                r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                if r.stdout:print(r.stdout.strip())

    def test_connected_installed_resources_and_callers(self):
        base,prior=inputs(BASE);image,r=inputs(CURRENT/'build-lock.json')
        old=prior['equipment_resources'];e=r['equipment_resources'];npc=e['npc_extra']
        stage=npc['events']['reserved'];scene=stage['native']['scene'];s=e['holiday_state']
        self.assertTrue(stage['installed']);self.assertFalse(stage['actor_owners_installed'])
        self.assertEqual(r['save_codec']['format_version'],12)
        self.assertEqual(r['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertFalse(r['shared_runtime_refresh']['saved_format_changed'])
        self.assertEqual(r['shared_runtime_refresh']['additional_resident_bytes'],0)
        files=by_vrom(image);core=files[CODE_VROM].extract(image)
        hook=scene['native_init_pointer_hook']
        self.assertEqual(u32(core,hook['address']-CODE_RAM),scene['code']['symbols']['af_holiday_scene_demo_init'])
        original=by_vrom(base)[CODE_VROM].extract(base)
        self.assertEqual(core[0x8007C484-CODE_RAM:0x8007C570-CODE_RAM],
                         original[0x8007C484-CODE_RAM:0x8007C570-CODE_RAM])
        for hook in scene['text']['hooks']:self.assertEqual(u32(core,hook['address']-CODE_RAM),hook['after'])
        for row in scene['text']['resources']:
            self.assertEqual(sha256(files[row['vrom']].extract(image)),row['sha256'])
        # Preserve every byte outside the explicitly changed modules/resources.
        for name,p,oldp,changes in (
            ('npc',npc['packet'],old['npc_extra']['packet'],[(0x8900,0x9800),(0xDC00,0xFFF0)]),
            ('state',s['packet'],old['holiday_state']['packet'],[(0,0x7F80)])):
            data=image[p['physical']:p['physical']+p['bytes']]
            before=base[oldp['physical']:oldp['physical']+oldp['bytes']]
            self.assertEqual(sha256(data),p['sha256'])
            allowed=set(i for a,b in changes for i in range(a,b))
            self.assertFalse(any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(data,before))),name)
        p=s['packet'];data=image[p['physical']:p['physical']+p['bytes']]
        for row in stage['resources']:
            at=row['ram']-p['ram'];self.assertEqual(sha256(data[at:at+row['bytes']]),row['sha256'])
        native=stage['native'];self.assertEqual(native['bindings']['af_holiday_native_unable_wade'],0x800B21D0)
        self.assertIn(struct.pack('>I',0x0C000000|(0x800B21D0>>2&0x3FFFFFF)),data[0x4800:0x7200])
        place=npc['events']['placement']
        self.assertEqual(place['bindings']['af_holiday_native_game'],0x8010EF90)
        for name,row in native['placement_callers_to_relink'].items():
            self.assertEqual(place['code']['symbols'][name],row['prepared'])
            caller=place['owner_bindings'] if name in place['owner_bindings'] else s['bindings']
            self.assertEqual(caller[name],row['prepared'])
        for oldcode,newcode,bindings in ((old['holiday_state']['code'],s['code'],s['bindings']),
            (old['npc_extra']['events']['placement']['owner_code'],place['owner_code'],place['owner_bindings'])):
            for name,address in oldcode['symbols'].items():
                if name.startswith('af_') and name not in bindings:self.assertEqual(newcode['symbols'][name],address)
        p=npc['packet'];at=p['physical']+npc['record']['flags_offset']
        self.assertEqual(image[at:at+4],bytes(4))
        # Native acre locking and every actual player consumer are unchanged.
        self.assertEqual(files[0x7AC420].extract(image),by_vrom(base)[0x7AC420].extract(base))
        self.assertEqual(core[0x800B21D0-CODE_RAM:0x800B21F0-CODE_RAM],
                         original[0x800B21D0-CODE_RAM:0x800B21F0-CODE_RAM])
        # Both changed packets are actually loaded and checked by startup.
        from v3_asset_loader import BLOB
        boot=e['surface_bootstrap'];ram=boot['ram'];compiled=boot['code']
        at=e['blob_offset']+ram-e['ram'];blob=files[BLOB].extract(image)
        code=blob[at:at+compiled['bytes']]
        self.assertEqual(sha256(code),compiled['sha256'])
        table=compiled['symbols']['packets']-ram
        rows=[struct.unpack_from('>5I',code,table+i*20) for i in range(18)]
        for p,name in ((npc['packet'],'npc_extra_crc'),(s['packet'],'holiday_state_crc')):
            address=compiled['symbols'][name]
            self.assertEqual(u32(code,address-ram),p['crc32'])
            self.assertIn((p['ram'],p['physical']|0x80000000,p['bytes'],address,0),rows)


if __name__=='__main__':unittest.main()
