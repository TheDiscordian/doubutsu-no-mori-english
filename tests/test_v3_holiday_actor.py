"""One combined donor-source and connected actor/controller host check."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_furniture_pipeline import Source
from v3_holiday_actor import discover,native_contract,REFERENCES
from v3_furniture_install import inputs
from aflib import by_vrom,sha256


class ActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source(self):
        r=discover(self.source)
        self.assertEqual(len(r['functions']),37)
        self.assertEqual(len(r['states']),15)
        bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
        bad.rel[bad.sections[1][0]+0x1B55F8]^=1
        with self.assertRaisesRegex(ValueError,'complete holiday actor'):discover(bad)
        bad=copy.copy(self.source);bad.data=bytearray(self.source.data);bad.data[0x538E4+74]^=1
        with self.assertRaisesRegex(ValueError,'state table'):discover(bad)

    def test_connected_actor(self):
        p='src/actor/npc/event/ac_ev_soncho2_think.c_inc';raw=(ROOT/'local/ac-decomp'/p).read_bytes()
        self.assertEqual(sha256(raw),REFERENCES[p])
        with tempfile.TemporaryDirectory(prefix='v3-holiday-actor-') as directory:
            out=Path(directory);(out/'reference-holiday-think.inc').write_bytes(raw)
            cmd=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-unused-parameter','-Wno-unused-function','-Wno-pointer-to-int-cast',
                '-Wno-cast-function-type','-fno-pie','-no-pie','-fsanitize=address,undefined',
                '-fno-omit-frame-pointer','-I'+str(out),'-I'+str(ROOT/'overlays/v3'),
                'tests/v3_holiday_actor_test.c','overlays/v3/holiday_actor.c',
                'overlays/v3/holiday_talk.c','overlays/v3/holiday_rewards.c',
                'overlays/v3/diary.c','overlays/v3/diary_calendar.c','-o',str(out/'check')]
            r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            r=subprocess.run([str(out/'check'),str(ROOT/'build/v3-holiday-rewards-prepared-02/holiday-rewards.bin')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr);print(r.stdout.strip())

    def test_current_native_dependencies(self):
        base,_=inputs(ROOT/'build/v3-diary-category-work-01/catalogue-03/build-lock.json')
        r=native_contract(base)
        self.assertEqual((r['special_think'],r['special_schedule']),(8,5))
        self.assertEqual(r['npc_prefix'],0x93C)
        self.assertFalse(r['walking_only_schedule_bound'])
        entry=by_vrom(base)[0x8681F0];self.assertFalse(entry.pend)
        bad=bytearray(base);bad[entry.pstart+0x8097E74C-0x809735B0]^=1
        with self.assertRaisesRegex(ValueError,'native holiday actor dependency'):native_contract(bad)
