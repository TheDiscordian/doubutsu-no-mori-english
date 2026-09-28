"""Connected world/reward checks; no native scenario or old-build replay."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_holiday_world import destinations,NATIVE
from v3_import_storage import ROWS,ITEMS
from v3_resource_capacity import checked_limit,text_records,LIMIT

OUT=ROOT/os.environ.get('V3_HOLIDAY_WORLD','build/v3-diary-category-work-01/tortimer-world-02')


class WorldTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.npc=cls.report['equipment_resources']['npc_extra'];cls.world=cls.npc['world']
        p=cls.npc['packet'];cls.packet=cls.image[p['physical']:p['physical']+p['bytes']]

    def test_installed_connected_world(self):
        w=self.world;p=self.packet;r=self.report
        self.assertEqual(sha256(p),self.npc['packet']['sha256'])
        for key in ('rewards','destinations'):
            row=w[key];data=p[row['offset']:row['offset']+row['bytes']]
            self.assertEqual(sha256(data),row['sha256'])
        mapping,rows=destinations(self.image,r,w['reward_contract'])
        self.assertEqual(mapping,p[0x3C80:0x3C80+536]);self.assertEqual(rows,w['destinations']['rows'])
        self.assertEqual(sha256(p[0x4000:0x4000+w['code']['bytes']]),w['code']['sha256'])
        self.assertLessEqual(w['code']['bytes'],0x6000)
        self.assertFalse(w['actor_active']);self.assertFalse(self.npc['record']['implemented'])
        self.assertEqual(p[self.npc['record']['flags_offset']:self.npc['record']['flags_offset']+4],bytes(4))
        for fixup in self.npc['record']['profile_fixups']:
            self.assertEqual(p[fixup['offset']:fixup['offset']+4],bytes(4))
        # Retain exact resources and earlier code; this is a comparison, not a replay.
        old,prior=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-dialogue-02/build-lock.json')
        q=prior['equipment_resources']['npc_extra']['packet'];before=old[q['physical']:q['physical']+q['bytes']]
        self.assertEqual(p[:0x3B00],before[:0x3B00]);self.assertEqual(p[0xA000:],before[0xA000:])
        self.assertEqual(r['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        core=by_vrom(self.image)[CODE_VROM].extract(self.image)
        for a,b,digest in NATIVE:self.assertEqual(sha256(core[a-CODE_RAM:b-CODE_RAM]),digest)

    def test_choice_manifest_and_tamper_guards(self):
        self.assertEqual(checked_limit(self.image,self.report),LIMIT)
        rows=text_records(self.image,self.report);self.assertEqual(rows[0]['entries'],515)
        self.assertEqual(rows,self.report['resource_capacity']['resources'])
        # The exact preceding receipt is accepted only via its declared append.
        legacy=copy.deepcopy(self.report)
        _,prior=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-dialogue-02/build-lock.json')
        legacy['resource_capacity']['resources']=prior['resource_capacity']['resources']
        self.assertEqual(text_records(self.image,legacy),rows)
        bad=copy.deepcopy(legacy);bad['resource_capacity']['resources'][0]['reader_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'complete appended choice reader'):checked_limit(self.image,bad)
        bad=bytearray(self.image);core=by_vrom(self.image)[CODE_VROM];self.assertFalse(core.pend)
        bad[core.pstart+0x80065550-CODE_RAM]^=1
        with self.assertRaises(ValueError):checked_limit(bad,self.report)
        choice=by_vrom(self.image)[rows[0]['vrom']];bad=bytearray(self.image);bad[choice.pstart]^=1
        with self.assertRaises(ValueError):checked_limit(bad,self.report)

    def test_connected_actual_state_and_inventory_bindings(self):
        with tempfile.TemporaryDirectory(prefix='v3-holiday-world-') as temp:
            d=Path(temp);w=self.world;p=self.packet
            headers=[]
            for key,name in (('rewards','af_holiday_reward_data'),('destinations','af_holiday_destination_data')):
                row=w[key];data=p[row['offset']:row['offset']+row['bytes']]
                headers.append('const unsigned char '+name+'[]={'+','.join(map(str,data))+'};')
            (d/'holiday-data.h').write_text('\n'.join(headers)+'\n')
            blob=by_vrom(self.image)[BLOB].extract(self.image)
            (d/'profiles.bin').write_bytes(blob[ROWS:ROWS+1024*80])
            (d/'metadata.bin').write_bytes(blob[ITEMS:ITEMS+1024*32])
            sources=('holiday_world','holiday_rewards','holiday_talk','holiday_actor','diary','diary_calendar','reward_state')
            flags=self.report['equipment_resources']['player_actions']['reward_state']['code']['flags']
            defines=[f for f in flags if f.startswith('-D')]
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I'+str(ROOT/'overlays/v3'),'-I'+str(d),
                *defines,'tests/v3_holiday_world_test.c',*(f'overlays/v3/{s}.c' for s in sources),'-o',str(d/'check')]
            for cmd in (command,[str(d/'check'),str(d/'profiles.bin'),str(d/'metadata.bin')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())


if __name__=='__main__':unittest.main()
