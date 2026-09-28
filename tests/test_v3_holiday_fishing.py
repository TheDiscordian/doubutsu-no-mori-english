"""Focused shared fishing-state check using the existing host compiler pattern."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from apply_translation import write_new
from v3_furniture_pipeline import Source
from v3_holiday_fishing import generate


class HolidayFishingTests(unittest.TestCase):
    def test_current_live_connections_and_text_growth(self):
        import os
        import struct
        import zlib
        from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
        from textbanks import Bank
        from v3_asset_loader import BLOB
        from v3_decoration_actor import SERVICES
        from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE
        from v3_furniture_install import inputs
        from v3_holiday_fishing import dialogue
        from v3_physical_resources import verify
        directory=ROOT/os.environ.get('V3_FISHING_LIVE_BUILD',
            'build/v3-diary-category-work-01/fishing-mail-installed-01')
        image,report=inputs(directory/'build-lock.json')
        base,prior=inputs(directory/'base-lock.json')
        equipment=report['equipment_resources'];fish=equipment['holiday_fishing']
        live=fish['live'];packet=fish['packet'];text=live['text']
        raw=image[packet['physical']:packet['physical']+packet['bytes']]
        old=base[packet['physical']:packet['physical']+packet['bytes']]
        self.assertEqual(sha256(raw),packet['sha256'])
        self.assertEqual(packet,equipment['holiday_state']['packet'])
        for row in (fish['loaded_code'],live['loaded_code']):
            at=row['ram']-packet['ram']
            self.assertEqual(sha256(raw[at:at+row['bytes']]),row['sha256'])
        self.assertEqual(raw[0x80730000-packet['ram']:0x80734000-packet['ram']],
                         old[0x80730000-packet['ram']:0x80734000-packet['ram']])
        for row in equipment['npc_extra']['events']['decorations']['controllers']['preserved']:
            at=row['ram']-packet['ram']
            self.assertEqual(sha256(raw[at:at+row['bytes']]),row['sha256'])
        sy=live['code']['symbols'];bindings=live['bindings']
        providers=[sy['af_hf_live_'+n] for n in ('event','size','npc_size','event_npc','name','random_name','record')]
        providers += [bindings['af_hf_native_window'],sy['af_hf_live_number'],bindings['af_hf_native_string']]
        providers += [sy['af_hf_live_'+n] for n in ('enter','leave','message')]
        self.assertEqual(struct.unpack_from('>13I',raw,SERVICES-packet['ram']+20),tuple(providers))
        self.assertEqual(u32(raw,SERVICES-packet['ram']+72),sy['af_hf_clip_lifecycle'])
        self.assertEqual(u32(raw,SERVICES-packet['ram']),7)
        pickup=equipment['holiday_items']['pickup'];at=pickup['ram']-packet['ram']
        self.assertEqual(sha256(raw[at:at+pickup['bytes']]),pickup['code']['sha256'])
        self.assertEqual(pickup['code']['symbols']['af_holiday_pickup_prior_resolve'],
                         equipment['npc_extra']['events']['decorations']['controllers']['code']['symbols']['af_decor_actor_resolve'])
        messages,choices,expected=dialogue(base)
        files=by_vrom(image);before=by_vrom(base)
        for v,table,first,extra in ((MESSAGE,TABLE,expected['first_id'],messages),
                (text['choice_vrom'],CHOICE_TABLE,expected['first_choice'],choices)):
            entries=Bank('test',0,0,files[v].extract(image),files[table].extract(image)).entries()
            previous=Bank('test',0,0,before[v].extract(base),before[table].extract(base)).entries()
            self.assertEqual(entries[:first],previous[:first])
            self.assertEqual(entries[first:],extra)
            if live.get('angler'):self.assertEqual(entries,previous)
        core=files[CODE_VROM].extract(image)
        for row in text['hooks']:self.assertEqual(u32(core,row['address']-CODE_RAM),row['after'])
        retired=live['retired_duplicate'];growth=text['physical_growth']
        self.assertEqual(growth['previous_end'],retired['physical'])
        self.assertLessEqual(growth['end'],retired['physical']+retired['bytes'])
        self.assertEqual(image[growth['end']:retired['physical']+retired['bytes']],
                         bytes(retired['physical']+retired['bytes']-growth['end']))
        if live.get('angler'):
            self.assertEqual(retired,prior['equipment_resources']['holiday_fishing']['live']['retired_duplicate'])
            self.assertEqual(image[retired['physical']:retired['physical']+retired['bytes']],
                             base[retired['physical']:retired['physical']+retired['bytes']])
        else:
            self.assertEqual(sha256(base[retired['physical']:retired['physical']+retired['bytes']]),retired['sha256'])
        self.assertNotIn(retired['id'],{r['id'] for r in report['physical_resources']})
        verify(image,report['physical_resources'])
        blob=files[BLOB].extract(image);boot=equipment['surface_bootstrap']['code']
        at=equipment['blob_offset']+boot['symbols']['packets']-equipment['ram']
        descriptors=[struct.unpack_from('>5I',blob,at+i*20) for i in range(18)]
        for _,address,size,_,_ in descriptors:
            if address&0x80000000:
                physical=address&0x7FFFFFFF
                self.assertFalse(physical<retired['physical']+retired['bytes'] and retired['physical']<physical+size)
        dest,address,size,crc,clear=descriptors[17]
        self.assertEqual((dest,address,size,clear),(packet['ram'],packet['physical']|0x80000000,packet['bytes'],0))
        self.assertEqual(u32(blob,equipment['blob_offset']+crc-equipment['ram']),zlib.crc32(raw))
        self.assertEqual(report['save_codec']['format_version'],prior['save_codec']['format_version'])
        self.assertEqual(report['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertFalse(live['actors_active']);self.assertFalse(live['service_admission'])
        connection=live['angler'];v=connection['vrom'];rv=connection['relocation_vrom'];ram=connection['ram']
        host=bytearray(files[v].extract(image));old_host=before[v].extract(base)
        self.assertEqual(len(connection['hooks']),8)
        for row in connection['hooks']:
            at=row['address']-ram
            self.assertEqual(u32(host,at),row['after'])
            self.assertEqual(row['after'],0x0C000000|((sy['af_hf_angler_'+row['name']]>>2)&0x3FFFFFF))
            struct.pack_into('>I',host,at,row.get('previous',row['before']))
        self.assertEqual(host,old_host)
        rel=files[rv].extract(image);old_rel=before[rv].extract(base)
        count=u32(rel,16);old_count=u32(old_rel,16)
        rebound=connection.get('rebound',False)
        self.assertEqual(count,old_count if rebound else old_count-1)
        words=struct.unpack_from('>'+str(old_count)+'I',old_rel,20)
        self.assertEqual(struct.unpack_from('>'+str(count)+'I',rel,20),
                         tuple(words) if rebound else tuple(w for w in words if w not in connection['removed_relocations']))
        self.assertEqual(connection['removed_relocations'],[0x44000000|(0x809D604C-ram)])
        from fishing_name import APPROVED,ALIASES_SHA
        names_at=APPROVED['symbols']['af_fishing_aliases'];at=sy['af_fishing_aliases']-packet['ram']
        self.assertEqual(raw[at:at+6368],files[0x3B40000].extract(image)[names_at:names_at+6368])
        self.assertEqual(sha256(raw[at:at+6368]),ALIASES_SHA)
        self.assertEqual(bindings['af_hf_native_clip'],0x80136F8C)
        self.assertEqual(bindings['af_hf_source_clip'],0x80705038)
        for pointer in struct.unpack_from('>4I',raw,sy['af_hf_bridge_clip']-packet['ram']):
            self.assertTrue(live['loaded_code']['ram']<=pointer<live['loaded_code']['ram']+live['loaded_code']['bytes'])
        if 'mail' in live:
            mail=live['mail'];hook=mail['hook']
            self.assertTrue(mail['installed']);self.assertFalse(mail['enabled'])
            self.assertEqual(u32(core,hook['address']-CODE_RAM),hook['after'])
            self.assertEqual(hook['after'],0x0C000000|((sy['af_hf_mail_notice']>>2)&0x3FFFFFF))
            self.assertEqual(u32(before[CODE_VROM].extract(base),hook['address']-CODE_RAM),hook['before'])
            self.assertEqual([g['name'] for g in mail['groups']],['ftr_listLottery','ftr_listEvent'])
            self.assertEqual(len(mail['prizes']),103)
            self.assertEqual([r['template'] for r in mail['letters']],list(range(0x23E,0x242)))
            at=sy['af_hf_prizes']-packet['ram']
            self.assertEqual(struct.unpack_from('>103H',raw,at),tuple(r['item'] for r in mail['prizes']))
            self.assertEqual(files[0x30A0000].extract(image),before[0x30A0000].extract(base))

    def test_live_record_name_size_and_text_bridge(self):
        self.run_live(False)

    def test_live_winner_mail_delivery(self):
        self.run_live(True)

    def run_live(self,mail):
        import json
        prepared=ROOT/('build/v3-diary-category-work-01/fishing-mail-installed-01/fishing-mail' if mail else
            'build/v3-diary-category-work-01/fishing-angler-installed-01/fishing-angler')
        report=json.loads((prepared/'prepared.json').read_bytes())
        self.assertEqual((report['text']['count'],report['text']['choice_count']),(74,7))
        self.assertEqual(len(report['text']['fish_messages']),40)
        self.assertLessEqual(report['text']['max_expanded_bytes'],1024)
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        with tempfile.TemporaryDirectory(prefix='v3-fishing-live-') as temp:
            out=Path(temp);generated,_=generate(source,out)
            local=out/'local-records.c'
            write_new(local,generated.read_bytes().replace(b'"/source/',('"'+str(ROOT)+'/').encode()))
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-ffunction-sections','-fdata-sections','-Wl,--gc-sections']
            commands=[['cc',*flags,'tests/v3_holiday_fishing_live_test.c',
                'overlays/v3/holiday_fishing.c','overlays/v3/holiday_fishing_live.c',
                'overlays/v3/holiday_fishing_angler.c','overlays/fishing/name.c',str(prepared/'legacy-names.c'),
                'overlays/v3/diary_calendar.c',str(local),str(prepared/'text-map.c'),
                '-o',str(out/'check')],[str(out/'check')]]
            if mail:
                from aflib import by_vrom
                from v3_furniture_install import inputs
                cartridge,_=inputs(prepared.parent/'build-lock.json')
                catalog=out/'catalog.bin';write_new(catalog,by_vrom(cartridge)[0x30A0000].extract(cartridge))
                commands[0][1:1]=['-DAF_TEST_FISHING_MAIL',str(prepared/'prizes.c'),
                    'overlays/v3/holiday_fishing_mail.c','runtime/mail/record.c','runtime/mail/catalog.c',
                    'runtime/mail/format.c','runtime/crc32.c','tests/mail_catalog_mock.c']
                commands[1].append(str(catalog))
            for command in commands:
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_controller_refresh_preserves_fishing_storage(self):
        import copy
        import os
        from unittest.mock import patch
        from aflib import sha256
        from v3_decoration_actor import install, END
        from v3_furniture_install import inputs
        directory=ROOT/os.environ.get('V3_FISHING_BUILD',
            'build/v3-diary-category-work-01/fishing-storage-installed-04')
        image,report=inputs(directory/'build-lock.json')
        equipment=report['equipment_resources'];packet=equipment['holiday_state']['packet']
        old=image[packet['physical']:packet['physical']+packet['bytes']]
        controller=equipment['npc_extra']['events']['decorations']['controllers']
        row=controller['loaded_code'];at=row['ram']-packet['ram']
        code=old[at:at+row['bytes']]
        def retained_code(base,prior,out):
            out.mkdir()
            return code,copy.deepcopy(controller)
        # Exercise the actual installer against the current cartridge, retaining
        # the already compiled unchanged controller rather than recompiling it.
        with tempfile.TemporaryDirectory(prefix='v3-fishing-refresh-') as temp:
            with patch('v3_decoration_actor.prepare',side_effect=retained_code):
                updated,changes,updates,writes=install(image,report,Path(temp))
        refreshed=updated['holiday_state']['packet'];raw=writes[0][1]
        self.assertEqual(refreshed,updated['holiday_fishing']['packet'])
        self.assertEqual(raw[END-packet['ram']:],old[END-packet['ram']:])
        self.assertEqual((refreshed['physical'],refreshed['bytes']),
                         (packet['physical'],packet['bytes']))
        self.assertEqual(refreshed['sha256'],sha256(raw))
        self.assertEqual(updated['npc_extra']['events']['decorations']['controllers']['packet_bytes'],
                         END-packet['ram'])
        self.assertEqual(updated['holiday_fishing']['redirects'],equipment['holiday_fishing']['redirects'])

    def test_current_cartridge_storage_connections(self):
        import json
        import os
        import struct
        import zlib
        from aflib import by_vrom,sha256,u32
        from v3_asset_loader import BLOB
        from v3_furniture_install import inputs
        from v3_holiday_fishing import RAM,SIZE,STATE,GUARD
        directory=ROOT/os.environ.get('V3_FISHING_BUILD',
            'build/v3-diary-category-work-01/fishing-storage-installed-04')
        image,report=inputs(directory/'build-lock.json')
        base,prior=inputs(directory/'base-lock.json')
        equipment=report['equipment_resources'];fish=equipment['holiday_fishing'];p=fish['packet']
        raw=image[p['physical']:p['physical']+p['bytes']]
        self.assertEqual(p,equipment['holiday_state']['packet'])
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(raw[-16:],GUARD)
        self.assertEqual(p['ram']+fish['preserved_prefix_bytes'],RAM)
        self.assertEqual(p['bytes'],fish['preserved_prefix_bytes']+SIZE)
        self.assertEqual(sha256(raw[RAM-p['ram']:RAM-p['ram']+fish['code']['bytes']]),fish['code']['sha256'])
        self.assertEqual(raw[RAM-p['ram']+fish['code']['bytes']:-16],
                         bytes(SIZE-fish['code']['bytes']-16))
        self.assertEqual(fish['bindings']['af_v3_fishing_state'],RAM+STATE)
        self.assertEqual(len(fish['redirects']),28)
        for owner,packet in (('holiday',p),('diary',equipment['diaries']['packets']['storage'])):
            old_packet=(prior['equipment_resources']['holiday_state']['packet'] if owner=='holiday'
                        else prior['equipment_resources']['diaries']['packets']['storage'])
            old=base[old_packet['physical']:old_packet['physical']+old_packet['bytes']]
            data=bytearray(image[packet['physical']:packet['physical']+len(old)])
            for row in fish['redirects']:
                if row['owner']!=owner:continue
                at=row['address']-packet['ram']
                self.assertEqual(data[at:at+8].hex(),row['after'])
                data[at:at+8]=bytes.fromhex(row['before'])
            self.assertEqual(data,old)  # Every non-redirect byte, including artwork, is retained.
        self.assertEqual(report['save_codec']['format_version'],13)
        self.assertEqual(equipment['diaries']['memory']['scratch'],dict(ram=0x80682000,bytes=120304))
        self.assertEqual(report['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertEqual(equipment['holiday_items']['ready_mask'],0)
        self.assertFalse(fish['live_event_bound']);self.assertFalse(fish['native_execution_verified'])
        blob=by_vrom(image)[BLOB].extract(image);boot=equipment['surface_bootstrap']['code']
        at=equipment['blob_offset']+boot['symbols']['packets']-equipment['ram']
        dest,address,size,crc,clear=struct.unpack_from('>5I',blob,at+17*20)
        self.assertEqual((dest,address,size,clear),(p['ram'],p['physical']|0x80000000,p['bytes'],0))
        self.assertEqual(u32(blob,equipment['blob_offset']+crc-equipment['ram']),zlib.crc32(raw))
        self.assertIn('format-12-or-earlier',report['save_warning'])

    def test_connected_storage_and_migration(self):
        with tempfile.TemporaryDirectory(prefix='v3-holiday-fishing-save-') as temp:
            out=Path(temp)
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections','-fdata-sections',
                '-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1','-DAF_V3_SURFACE_PROFILE=1',
                '-DAF_V3_CREATURE_PROFILE=1','-DAF_V3_INSECT_SEASONS=1','-DAF_V3_DIARY_STORAGE=1',
                '-DAF_V3_HOLIDAY_STORAGE=1']
            commands=[['cc',*flags,'-Daf_v3_save_check=af_console_canonical_check',
                '-Daf_v3_save_pack=af_console_canonical_pack','-Daf_v3_save_collect=af_console_canonical_collect',
                '-c','overlays/v3/save_codec.c','-o',str(out/'codec.o')],
                ['cc',*flags,*(f'-Daf_v3_save_{s}=af_old_{s}' for s in
                    ('compress','expand','compress_diary','expand_diary','measure_diary')),
                 '-c','overlays/v3/save_compressed.c','-o',str(out/'legacy.o')],
                ['cc',*flags,'-DAF_V3_CONSOLE_STORAGE=1','-DAF_V3_FISHING_STORAGE=1',
                 '-Wl,--gc-sections','tests/v3_holiday_fishing_storage_test.c',
                 *(f'overlays/v3/{s}.c' for s in ('save_runtime','console_storage','save_compressed',
                    'diary','diary_calendar','holiday_fishing')),
                 str(out/'codec.o'),str(out/'legacy.o'),'-o',str(out/'check')],[str(out/'check')]]
            for command in commands:
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_complete_record_lifecycle_and_serialization(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        with tempfile.TemporaryDirectory(prefix='v3-holiday-fishing-') as temp:
            out=Path(temp);generated,report=generate(source,out)
            self.assertEqual(report['source_functions'],19)
            self.assertEqual(report['record_count'],5)
            local=out/'local-records.c'
            write_new(local,generated.read_bytes().replace(b'"/source/',('"'+str(ROOT)+'/').encode()))
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections','-fdata-sections']
            commands=[['cc',*flags,'tests/v3_holiday_fishing_test.c','overlays/v3/holiday_fishing.c',
                'overlays/v3/diary_calendar.c',str(local),'-Wl,--gc-sections','-o',str(out/'check')],
                [str(out/'check')]]
            for command in commands:
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())


if __name__=='__main__':unittest.main()
