"""One family-level source/host/cartridge check; no emulator or old-build replay."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from apply_translation import write_new
from aflib import by_vrom,sha256
from v3_furniture_pipeline import Source,prepare_models
from v3_holiday_sky import generate,profile_packet,RAM,END,PACKET_END


class SkyTests(unittest.TestCase):
    def test_current_profile_loader_ranges(self):
        from tests.test_v3_equipment_runtime import HostTests
        HostTests.sanitized(self,'v3_effect_loader_test.c',defines=(
            '-DAF_EFFECT_COUNT=8u','-DAF_EFFECT_ROOM_COUNT=4u',
            '-DAF_EFFECT_CODE_START=0x804D0000u','-DAF_EFFECT_CODE_END=0x804D8000u',
            '-DAF_EFFECT_SKY_START=0x80738000u','-DAF_EFFECT_SKY_END=0x80739C80u'))

    def test_complete_source_and_host_lifecycles(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        generated,contract=generate(source)
        self.assertEqual([(r['source_id'],r['native_id'],r['unique']) for r in contract['profiles']],
            [(65,115,1),(116,116,1),(115,117,0),(117,118,0)])
        self.assertEqual(len(contract['functions']),22)
        with tempfile.TemporaryDirectory(prefix='v3-sky-') as temp:
            out=Path(temp);write_new(out/'sky-source.c',generated.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined,float-cast-overflow','-fno-omit-frame-pointer',
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(out),'tests/v3_holiday_sky_test.c','-lm','-o',str(out/'check')]
            for cmd in (command,[str(out/'check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_current_cartridge_family(self):
        from v3_furniture_install import inputs
        from v3_asset_loader import BLOB
        from v3_room_effects import restore_controller,rebind_profiles
        directory=ROOT/os.environ.get('V3_HOLIDAY_SKY_BUILD','build/v3-diary-category-work-01/sky-installed-05')
        image,report=inputs(directory/'build-lock.json');base,prior=inputs(directory/'base-lock.json')
        e=report['equipment_resources'];before=prior['equipment_resources'];events=e['npc_extra']['events'];sky=events['sky']
        files=by_vrom(image);old=by_vrom(base);effects=e['room_rigs']['effects'];native=effects['controller']
        self.assertEqual(native['count'],119);self.assertEqual([r['unique'] for r in native['additions'][4:]],[1,1,0,0])
        original,rel=restore_controller(files[native['vrom']].extract(image),files[native['reloc']].extract(image),native)
        previous=before['room_rigs']['effects']['controller']
        original_before,rel_before=restore_controller(old[previous['vrom']].extract(base),old[previous['reloc']].extract(base),previous)
        self.assertEqual((original,rel),(original_before,rel_before))
        p=sky['packet'];raw=image[p['physical']:p['physical']+p['bytes']]
        op=before['holiday_state']['packet'];prefix=base[op['physical']:op['physical']+op['bytes']]
        self.assertEqual(e['holiday_state']['packet'],op)
        self.assertEqual(image[op['physical']:op['physical']+op['bytes']],prefix);self.assertEqual(p['ram']+p['bytes'],PACKET_END)
        self.assertEqual(raw[-16:],b'AFSK'*4);self.assertEqual((sha256(raw),zlib.crc32(raw)),(p['sha256'],p['crc32']))
        at=RAM-p['ram'];self.assertEqual(sha256(raw[at:at+sky['code']['bytes']]),sky['code']['sha256'])
        self.assertFalse(any(raw[at+sky['code']['bytes']:END-p['ram']]))
        self.assertEqual(e['holiday_fishing']['packet'],op)
        blob=files[BLOB].extract(image)
        for row in effects['profiles']:
            data=blob[row['blob_offset']:row['blob_offset']+64]
            self.assertEqual(sha256(data),row['sha256'])
            if row['id']>=115:self.assertEqual(data,profile_packet(row['callbacks'],row['policy_hex']))
        retained=bytearray(blob);rebind_profiles(effects,retained,e['room_rigs']['code']['symbols'],code_bounds=(0x804D0000,0x804D8000))
        self.assertEqual(retained,blob)
        bank=files[effects['bank']['vrom']].extract(image);old_bank=old[before['room_rigs']['effects']['bank']['vrom']].extract(base)
        self.assertEqual(bank[:len(old_bank)],old_bank)
        for row in sky['artwork']['objects'].values():
            start=row['base']&0xFFFFFF
            self.assertEqual(sha256(bank[start:start+row['bytes']]),row['installed_sha256'])
            self.assertLessEqual(row['bytes'],3584)
        self.assertEqual(sky['loader_room_bounds'],[0x804D0000,0x804D8000])
        self.assertEqual(sky['loader_sky_bounds'],[RAM,RAM+sky['code']['bytes']])
        self.assertTrue(events['dispatch']['effects_bound']);self.assertFalse(events['active']['owner_services_bound'])
        self.assertEqual(report['save_codec'],prior['save_codec'])
        npc=e['npc_extra'];n=npc['packet'];start=n['physical']+npc['record']['flags_offset']
        self.assertEqual(image[start:start+4],bytes(4))
        boot=e['surface_bootstrap']['code'];offset=e['blob_offset']-e['ram']
        table=offset+boot['symbols']['packets'];rows=[struct.unpack_from('>5I',blob,table+20*i) for i in range(19)]
        row=next(row for row in rows if row[0]==p['ram'])
        self.assertEqual(row[1:3],(p['physical']|0x80000000,p['bytes']))
        self.assertEqual(struct.unpack_from('>I',blob,offset+row[3])[0],p['crc32'])


if __name__=='__main__':unittest.main()
