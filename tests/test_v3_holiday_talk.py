"""One connected host comparison for the complete shared holiday conversation."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_furniture_pipeline import Source
from v3_holiday_talk import discover,REFERENCES,FUNCTIONS
from aflib import sha256


class TalkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_binding(self):
        report=discover(self.source)
        self.assertEqual(report['holiday_events'],28)
        self.assertFalse(report['runtime_installed'])
        self.assertFalse(report['actor_installed'])
        for address,_,size,_,_ in FUNCTIONS:
            bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
            bad.rel[bad.sections[1][0]+address+size-1]^=1
            with self.assertRaisesRegex(ValueError,'complete Tortimer'):discover(bad)

    def test_connected_donor_conversation_calendar_and_rewards(self):
        source_path='src/actor/npc/event/ac_ev_soncho2_talk.c_inc'
        source=(ROOT/'local/ac-decomp'/source_path).read_bytes()
        self.assertEqual(sha256(source),REFERENCES[source_path])
        with tempfile.TemporaryDirectory(prefix='v3-holiday-talk-') as directory:
            out=Path(directory)
            (out/'reference-holiday-talk.inc').write_bytes(source)
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-unused-parameter','-Wno-unused-function',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(out),'-I'+str(ROOT/'overlays/v3'),'tests/v3_holiday_talk_test.c',
                'overlays/v3/holiday_talk.c','overlays/v3/holiday_rewards.c',
                'overlays/v3/diary.c','overlays/v3/diary_calendar.c','-o',str(out/'check')]
            run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(out/'check'),str(ROOT/'build/v3-holiday-rewards-prepared-02/holiday-rewards.bin')],
                cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())
