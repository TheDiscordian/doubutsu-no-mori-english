"""Focused connected Harvest checks; native services remain recording doubles."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
OUT=ROOT/os.environ.get('V3_HARVEST_PREPARED','build/v3-harvest-connected-prepared-09')
LINKED=ROOT/os.environ.get('V3_HARVEST_LINKED','build/v3-harvest-connected-linked-05')


class HarvestTests(unittest.TestCase):
    def test_complete_source_resources_and_native_contract(self):
        report=json.loads((OUT/'prepared.json').read_bytes())
        self.assertEqual(len(report['family'][0]['functions']),39)
        self.assertEqual(len(report['rewards']),12)
        self.assertEqual(len(report['dialogue']['rows']),36)
        self.assertEqual(report['native_layout']['saved_bytes'],22)
        self.assertEqual(report['native_layout']['actor_bytes'],2420)
        self.assertFalse(report['acquisition_installed'])
        self.assertEqual(report['native_contract']['event_areas']['data_bytes'],40)
        self.assertEqual(len(report['native_contract']['native_services']),10)
        self.assertEqual(len(report['native_contract']['player_callbacks']),3)
        for name,digest in report['generated_sha256'].items():
            self.assertEqual(sha256((OUT/name).read_bytes()),digest,name)
        self.assertEqual([row['source_item'] for row in report['rewards'][-2:]],[0x2642,0x2742])
        self.assertEqual([row['item'] for row in report['rewards'][-2:]],[0x264D,0x274D])
        self.assertEqual(report['registry']['owner_count'],28)
        self.assertEqual(report['registry']['rows'][-1]['profile'],0xF5)
        self.assertEqual(report['shared_motions']['added'],[385])
        linked=json.loads((LINKED/'connected.json').read_bytes())
        self.assertEqual(linked['preparation'],report)
        self.assertFalse(linked['installed'])
        for file,key in (('harvest.bin','code'),('franklin-pool.bin','pool')):
            self.assertEqual(sha256((LINKED/file).read_bytes()),linked[key]['sha256'])
        self.assertEqual(linked['pool']['bytes'],2704)
        self.assertEqual(linked['npc']['actor_bytes'],2420)
        names=bytes.fromhex(linked['npc']['names_hex'])
        self.assertEqual(struct.unpack_from('>4I',names),(0x41464E49,1,9,16))
        self.assertEqual(names[-8:],b'Franklin')
        self.assertEqual(len(linked['npc']['identity_rebindings']),6)
        for row in linked['npc']['render_owners']:
            self.assertEqual(sha256((LINKED/row['file']).read_bytes()),row['sha256'])
        native=(LINKED/'npc-runtime.bin').read_bytes()
        self.assertEqual(sha256(native),linked['npc']['runtime_sha256'])
        at=linked['npc']['runtime']['symbols']['af_npc_identity_spawn']-0x806E4000
        self.assertEqual(struct.unpack_from('>I',native,at+0x4C)[0],0x2D41000A)

    def test_complete_actor_and_connected_native_adapters(self):
        with tempfile.TemporaryDirectory(prefix='v3-harvest-') as directory:
            target=Path(directory)/'check'
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-unused-variable','-Wno-unused-but-set-variable','-Wno-unused-parameter',
                '-Wno-parentheses','-Wno-cast-function-type','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(OUT),'-Ioverlays/v3']
            command=['cc',*flags,'tests/v3_harvest_event_test.c',
                'overlays/v3/harvest_state.c','overlays/v3/harvest_dialogue.c',
                'overlays/v3/harvest_world_native.c','overlays/v3/carried_handover.c',
                str(OUT/'dialogue.c'),str(OUT/'reward-map.c'),'-lm','-o',str(target)]
            for cmd in (command,[str(target)]):
                result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())


if __name__=='__main__':unittest.main()
