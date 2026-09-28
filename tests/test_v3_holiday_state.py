"""Changed holiday state/save path, using the existing host device doubles."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_holiday_state import RAM,SIZE,TABLE,GUARD,contract
from v3_furniture_pipeline import Source
from v3_holiday_events import encode
from v3_holiday_native import identities

OUT=ROOT/os.environ.get('V3_HOLIDAY_STATE','build/v3-diary-category-work-01/tortimer-state-05')

class HolidayStateTests(unittest.TestCase):
    def test_connected_host_state_save_and_migration(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        days,_=contract(source)
        with tempfile.TemporaryDirectory(prefix='v3-holiday-state-') as temp:
            out=Path(temp)
            _,report=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-observers-01/build-lock.json')
            ids,_=identities();events=encode(report['equipment_resources']['npc_extra']['events']['contract'])
            arrays=(('af_holiday_harvest_days',days),('af_holiday_native_ids',ids[:128]),
                ('af_holiday_source_ids',ids[128:]),('af_holiday_event_data',events))
            write_new(out/'holiday-state-data.h',('\n'.join('const unsigned char '+name+'[]={'+
                ','.join(map(str,data))+'};' for name,data in arrays)+'\n').encode())
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections','-fdata-sections',
                '-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1','-DAF_V3_SURFACE_PROFILE=1',
                '-DAF_V3_CREATURE_PROFILE=1','-DAF_V3_INSECT_SEASONS=1','-DAF_V3_DIARY_STORAGE=1']
            commands=[['cc',*flags,'-Daf_v3_save_check=af_console_canonical_check',
                '-Daf_v3_save_pack=af_console_canonical_pack','-Daf_v3_save_collect=af_console_canonical_collect',
                '-c','overlays/v3/save_codec.c','-o',str(out/'codec.o')],
                ['cc',*flags,*(f'-Daf_v3_save_{s}=af_old_{s}' for s in
                    ('compress','expand','compress_diary','expand_diary','measure_diary')),
                 '-c','overlays/v3/save_compressed.c','-o',str(out/'legacy.o')],
                ['cc',*flags,'-DAF_V3_CONSOLE_STORAGE=1','-DAF_V3_HOLIDAY_STORAGE=1',
                 '-I'+str(out),'-Wl,--gc-sections','tests/v3_holiday_state_test.c',
                 *(f'overlays/v3/{s}.c' for s in ('save_runtime','console_storage','save_compressed',
                    'diary','diary_calendar','holiday_state','holiday_native','holiday_events')),
                 str(out/'codec.o'),str(out/'legacy.o'),
                 '-o',str(out/'check')],[str(out/'check')]]
            for command in commands:
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_current_cartridge_bindings_and_retained_callers(self):
        image,report=inputs(OUT/'build-lock.json');e=report['equipment_resources'];s=e['holiday_state'];p=s['packet']
        self.assertEqual((p['ram'],p['bytes']),(RAM,SIZE))
        data=image[p['physical']:p['physical']+SIZE]
        self.assertEqual(sha256(data),p['sha256']);self.assertEqual(data[-16:],GUARD)
        self.assertEqual(sha256(data[:s['code']['bytes']]),s['code']['sha256'])
        self.assertEqual(sha256(data[TABLE:TABLE+58]),s['contract']['harvest_sha256'])
        self.assertFalse(s['actor_active']);self.assertTrue(s['lifecycle_linked'])
        self.assertEqual(report['save_codec']['format_version'],12)
        before,prior=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-observers-01/build-lock.json')
        oldp=prior['equipment_resources']['diaries']['packets']['storage'];newp=e['diaries']['packets']['storage']
        old=before[oldp['physical']:oldp['physical']+oldp['bytes']]
        new=image[newp['physical']:newp['physical']+newp['bytes']];expected=bytearray(old)
        for row in s['redirects']:
            at=row['address']-oldp['ram'];self.assertEqual(old[at:at+8],bytes.fromhex(row['before']))
            expected[at:at+8]=bytes.fromhex(row['after'])
            self.assertEqual(u32(expected,at),0x08000000|(row['target']>>2&0x3FFFFFF))
            self.assertEqual(s['code']['symbols'][row['name']],row['target'])
        self.assertEqual(new,expected);self.assertEqual(sha256(new),newp['sha256'])
        npc=e['npc_extra']['packet'];oldnpc=prior['equipment_resources']['npc_extra']['packet']
        expected=bytearray(before[oldnpc['physical']:oldnpc['physical']+oldnpc['bytes']])
        for row in s['profile_fixups']:
            at=row['offset'];self.assertEqual(expected[at:at+4],bytes(4))
            expected[at:at+4]=row['target'].to_bytes(4,'big')
            self.assertEqual(row['target'],s['code']['symbols'][row['symbol']])
        self.assertEqual(image[npc['physical']:npc['physical']+npc['bytes']],expected)
        self.assertEqual(sha256(expected),npc['sha256'])
        f=e['npc_extra']['record']['flags_offset'];self.assertEqual(expected[f:f+4],bytes(4))
        original=by_vrom(before)[CODE_VROM].extract(before)
        actual=by_vrom(image)[CODE_VROM].extract(image);hook=s['calendar_hook']
        at=hook['address']-CODE_RAM
        self.assertEqual(original[at:at+8],bytes.fromhex(hook['before']))
        expected=bytearray(original[0x8007F358-CODE_RAM:0x8007F6A0-CODE_RAM])
        expected[0x8007F630-0x8007F358:0x8007F638-0x8007F358]=bytes.fromhex(hook['after'])
        self.assertEqual(actual[0x8007F358-CODE_RAM:0x8007F6A0-CODE_RAM],expected)
        self.assertTrue(s['native_schedule_caller_bound'])
        self.assertEqual(report['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        boot=e['surface_bootstrap']['code'];blob=by_vrom(image)[BLOB].extract(image)
        packet=e['surface_bootstrap']['ram'];offset=e['blob_offset']+packet-e['ram']
        native=blob[offset:offset+boot['bytes']]
        self.assertEqual(sha256(native),boot['sha256'])
        symbols=boot['symbols'];crc=symbols['holiday_state_crc']-packet
        self.assertEqual(u32(native,crc),p['crc32'])
        # Inspect the actual expanded descriptor loop's complete table.
        table=symbols['packets']-packet
        rows=[tuple(u32(native,table+i*20+j*4) for j in range(5)) for i in range(18)]
        self.assertEqual(rows[-1],(RAM,p['physical']|0x80000000,SIZE,symbols['holiday_state_crc'],0))

if __name__=='__main__':unittest.main()
