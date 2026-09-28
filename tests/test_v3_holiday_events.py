"""Focused shared event checks; no native fixture replay."""
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source
from v3_furniture_install import inputs
from v3_holiday_events import discover,encode,TYPES

OUT=ROOT/os.environ.get('V3_HOLIDAY_EVENTS','build/v3-diary-category-work-01/tortimer-events-02')


class EventTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.npc=cls.report['equipment_resources']['npc_extra'];cls.events=cls.npc['events']
        p=cls.npc['packet'];cls.packet=cls.image[p['physical']:p['physical']+p['bytes']]
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_and_installed_packet(self):
        contract=discover(self.source);data=encode(contract)
        self.assertEqual(json.loads(json.dumps(contract)),self.events['contract'])
        self.assertEqual(self.packet[0x9800:0x9800+len(data)],data)
        self.assertEqual(sha256(data),self.events['data']['sha256'])
        self.assertEqual(len(contract['rows']),49);self.assertEqual(len(contract['owners']),44)
        self.assertEqual({r['type'] for r in contract['rows']},TYPES)
        code=self.events['code'];self.assertEqual(sha256(self.packet[0x7400:0x7400+code['bytes']]),code['sha256'])
        self.assertLessEqual(code['bytes'],0x2400)
        self.assertEqual(sha256(self.packet),self.npc['packet']['sha256'])
        self.assertFalse(self.events['native_adapter_bound']);self.assertFalse(self.events['actor_active'])
        self.assertEqual(self.packet[self.npc['record']['flags_offset']:self.npc['record']['flags_offset']+4],bytes(4))
        # Compare the retained packet without running any predecessor test.
        old,prior=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-world-02/build-lock.json')
        p=prior['equipment_resources']['npc_extra']['packet'];before=old[p['physical']:p['physical']+p['bytes']]
        self.assertEqual(self.packet[:0x7400],before[:0x7400]);self.assertEqual(self.packet[0xA000:],before[0xA000:])
        self.assertEqual(self.report['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        bad=copy.copy(self.source);bad.data=bytearray(self.source.data);bad.data[0x441C+25*12]^=1
        with self.assertRaisesRegex(ValueError,'complete source holiday schedule'):discover(bad)

    def test_connected_calendar_owner_and_conversation(self):
        # Run unchanged complete donor priority and cleanup functions beside the
        # imported kernel. The host substitutes native actor/event I/O only.
        event_header=(ROOT/'local/ac-decomp/include/m_event.h').read_text()
        soncho_header=(ROOT/'local/ac-decomp/include/m_soncho.h').read_text()
        source=(ROOT/'local/ac-decomp/src/game/m_soncho.c').read_text()
        reference=re.search(r'enum event_table \{.*?\};',event_header,re.S)[0]+'\n'
        reference+='\n'.join(re.findall(r'^#define mEv_STATUS_.*$',event_header,re.M))+'\n'
        reference+=next(e for e in re.findall(r'enum \{.*?\};',soncho_header,re.S) if 'mSC_EVENT_NEW_YEARS_DAY' in e)+'\n'
        reference+=next(e for e in re.findall(r'enum \{.*?\};',soncho_header,re.S) if 'mSC_FIELD_EVENT_FOOT_RACE' in e)+'\n'
        reference+=source[source.index('static u8 event_table'):source.index('extern int mSC_trophy_get')]
        w=self.npc['world'];r=w['rewards'];reward=self.packet[r['offset']:r['offset']+r['bytes']]
        nature=w['reward_contract']['rows'][9]['source_items'][0]
        mapped=next(d for d in w['destinations']['rows'] if d['donor_item']==int(nature,16))['item']
        with tempfile.TemporaryDirectory(prefix='v3-holiday-events-') as temp:
            d=Path(temp);data=encode(self.events['contract'])
            header='\n'.join('static const unsigned char '+name+'[]={'+','.join(map(str,b))+'};'
                for name,b in (('event_data',data),('reward_data',reward)))
            header+=f'\nstatic const unsigned int nature_source_item=0x{nature},nature_native_item={mapped};\n'
            (d/'holiday-events-data.h').write_text(header)
            (d/'holiday-events-reference.inc').write_text(reference)
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-Wno-unused-variable',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(d),'tests/v3_holiday_events_test.c',
                *(f'overlays/v3/{s}.c' for s in ('holiday_events','holiday_talk','holiday_rewards','diary','diary_calendar')),
                '-o',str(d/'check')]
            for cmd in (command,[str(d/'check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())


if __name__=='__main__':unittest.main()
