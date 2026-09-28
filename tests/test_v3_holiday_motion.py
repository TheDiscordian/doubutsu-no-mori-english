"""One connected source/adapter check; no emulator fixture or old-build replay."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from v3_holiday_motion import REFERENCES,patch,VROM,RELOC,OWNER
from v3_furniture_install import inputs


class MotionTests(unittest.TestCase):
    def test_connected_motion(self):
        path='local/ac-decomp/src/actor/npc/ac_npc_think_wander.c_inc'
        raw=(ROOT/path).read_bytes();self.assertEqual(sha256(raw),REFERENCES[path])
        # Preserve the entire decision function verbatim. Its engine-dependent
        # geometry helpers are the native helpers in the actual installed path.
        begin=raw.index(b'static void aNPC_think_wander_decide_next(')
        end=raw.index(b'static void aNPC_think_wander_next_act(',begin)
        with tempfile.TemporaryDirectory(prefix='v3-holiday-motion-') as directory:
            out=Path(directory);(out/'reference-holiday-wander.inc').write_bytes(raw[begin:end])
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-implicit-fallthrough','-fno-pie','-no-pie','-fsanitize=address,undefined',
                '-fno-omit-frame-pointer','-I'+str(out),'-I'+str(ROOT/'overlays/v3'),
                'tests/v3_holiday_motion_test.c','overlays/v3/holiday_motion.c','-o',str(out/'check')]
            r=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr)
            r=subprocess.run([str(out/'check')],capture_output=True,text=True,timeout=30)
            self.assertEqual(r.returncode,0,r.stdout+r.stderr);print(r.stdout.strip())

    def test_installed_packet_and_hooks(self):
        lock=ROOT/os.environ.get('V3_HOLIDAY_MOTION_LOCK',
            'build/v3-diary-category-work-01/tortimer-services-03/build-lock.json')
        base,report=inputs(lock);npc=report['equipment_resources']['npc_extra'];motion=npc['motion']
        files=by_vrom(base);owner=bytearray(files[VROM].extract(base));rel=files[RELOC].extract(base)
        self.assertEqual(sha256(owner),motion['owner_sha256'])
        self.assertEqual(sha256(rel),motion['relocation_sha256'])
        for h in motion['hooks']:
            at=h['address']-OWNER;self.assertEqual(owner[at:at+len(bytes.fromhex(h['after']))],bytes.fromhex(h['after']))
        packet=npc['packet'];raw=base[packet['physical']:packet['physical']+packet['bytes']]
        code=motion['code'];self.assertEqual(sha256(raw[0x2000:0x2000+code['bytes']]),code['sha256'])
        self.assertFalse(any(raw[0x2000+code['bytes']:0xA000]))
        prior=(ROOT/'build/v3-diary-category-work-01/tortimer-installed-03/npc-registry/installed-packet.bin').read_bytes()
        self.assertEqual(sha256(prior),motion['previous_packet_sha256'])
        self.assertEqual(raw[:0x2000]+raw[0xA000:],prior[:0x2000]+prior[0xA000:])
        # The trampoline preserves a0-a3/ra and replays the exact native prefix,
        # resolving the continuation through the live clip, not the link address.
        at=code['symbols']['af_holiday_animation_original']-packet['ram']
        self.assertEqual(raw[at:at+28],bytes.fromhex(
            '3c1980138f396eec8f3901042739000827bdffb003200008afb0002c'))
        self.assertFalse(npc['actor_callbacks_bound']);self.assertFalse(npc['selectable'])
        self.assertFalse(motion['native_execution_verified'])
        self.assertEqual(raw[0xA000+20:0xA000+24],bytes(4))
        self.assertEqual(raw[-16:],b'AFNX'*4)
        cane=npc['record']['cane'];self.assertEqual(sha256(raw[cane['offset']:cane['offset']+cane['bytes']]),cane['sha256'])
        for path,digest in npc['sources'].items():
            self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
