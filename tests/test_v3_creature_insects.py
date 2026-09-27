"""One connected host check for all converted insect behaviour programs."""
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
from v3_creature_insects import PROGRAMS,rewrite


class CreatureInsectTests(unittest.TestCase):
    def test_complete_program_category(self):
        directory=ROOT/os.environ.get('V3_INSECT_PROGRAMS','build/v3-creature-insects-work-01/programs-03')
        report=json.loads((directory/'programs.json').read_text())
        self.assertEqual([r['source_index'] for r in report['rows']],list(range(32,40)))
        self.assertEqual(len(report['programs']),6)
        self.assertFalse(report['installed']);self.assertFalse(report['selectable'])
        self.assertEqual(report['native_abi']['stride'],0x280)
        self.assertEqual(report['native_abi']['slots'],3)
        for path,digest in report['sources'].items():
            self.assertEqual(sha256((ROOT/path).read_bytes()),digest,'Stale compiled source: '+path)
        self.assertEqual(sha256((directory/'programs.o').read_bytes()),report['compiled']['sha256'])
        inputs=[]
        for name,_,_,digest in PROGRAMS:
            donor=(ROOT/f'local/ac-decomp/src/actor/ac_ins_{name}.c').read_bytes()
            self.assertEqual(sha256(donor),digest)
            generated,edits=rewrite(donor.decode())
            self.assertEqual((directory/(name+'.c')).read_text(),generated)
            entry=next(p for p in report['programs'] if p['name']==name)
            self.assertEqual(entry['platform_edits'],edits)
            inputs.append(str(directory/(name+'.c')))
        with tempfile.TemporaryDirectory(prefix='af-insect-programs-') as temporary:
            executable=Path(temporary)/'programs'
            subprocess.run(['cc','-std=c11','-O1','-g','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all',
                '-Wall','-Wextra','-Werror','-Wno-unused-variable','-Wno-unused-parameter',
                '-I'+str(ROOT/'overlays/v3'),*inputs,
                str(ROOT/'overlays/v3/creature_insects.c'),
                str(ROOT/'overlays/v3/creature_insect_state.c'),
                str(ROOT/'tests/v3_creature_insects_test.c'),'-lm','-o',str(executable)],
                check=True,capture_output=True,text=True)
            result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Eight species:',result.stdout)


if __name__=='__main__':unittest.main()
