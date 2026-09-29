"""Complete source-family conversion and shared handover transition checks."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
OUT=ROOT/os.environ.get('V3_REWARD_EVENTS','build/v3-reward-events-prepared-02')


class RewardEventTests(unittest.TestCase):
    def test_complete_family_and_explicit_unbound_services(self):
        report=json.loads((OUT/'prepared.json').read_text())
        self.assertEqual([r['name'] for r in report['family']],['present_demo','present_npc','npc_hem'])
        self.assertFalse(report['installed'])
        self.assertFalse(report['native_services_bound'])
        self.assertFalse(report['object']['linked'])
        self.assertTrue(report['unbound_services'])
        for name,digest in report['generated_sha256'].items():
            self.assertEqual(sha256((OUT/name).read_bytes()),digest,name)
        for family in report['family']:
            body=(OUT/(family['name']+'.c')).read_text()
            for function in family['functions']:
                self.assertIn(function['symbol']+'(',body)
        self.assertEqual(sha256((OUT/'reward-events.o').read_bytes()),report['object']['sha256'])

    def test_shared_gift_handover_is_a_single_transaction(self):
        with tempfile.TemporaryDirectory(prefix='v3-reward-events-') as temp:
            target=Path(temp)/'check'
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-unused-variable','-Wno-unused-but-set-variable',
                '-Wno-unused-function','-Wno-parentheses','-Wno-cast-function-type',
                '-ffunction-sections','-fdata-sections','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(OUT),'-Ioverlays/v3','-Wl,--gc-sections']
            for command in (['cc',*flags,'tests/v3_reward_event_test.c','-o',str(target)], [str(target)]):
                run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                if run.stdout:print(run.stdout.strip())


if __name__=='__main__':unittest.main()
