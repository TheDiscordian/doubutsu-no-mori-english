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
from v3_creature_insects import PROGRAMS,rewrite,install_controller


class CreatureInsectTests(unittest.TestCase):
    def test_complete_program_category(self):
        directory=ROOT/os.environ.get('V3_INSECT_PROGRAMS','build/v3-creature-insects-work-01/programs-06')
        report=json.loads((directory/'programs.json').read_text())
        self.assertEqual([r['source_index'] for r in report['rows']],list(range(32,40)))
        self.assertEqual(len(report['programs']),6)
        self.assertFalse(report['installed']);self.assertFalse(report['selectable'])
        self.assertEqual(report['native_abi']['stride'],0x280)
        self.assertEqual(report['native_abi']['slots'],3)
        self.assertEqual(report['native_abi']['collision_pipe_bytes'],0x1C)
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

    def test_connected_native_adapter(self):
        with tempfile.TemporaryDirectory(prefix='af-insect-engine-') as temporary:
            executable=Path(temporary)/'engine'
            inputs=['creature_insects','creature_insect_state','creature_insect_environment',
                    'creature_insect_engine','creature_insect_collision']
            result=subprocess.run(['cc','-std=c11','-O1','-g','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all','-Wall','-Wextra','-Werror',
                '-I'+str(ROOT/'overlays/v3'),
                *(str(ROOT/f'overlays/v3/{name}.c') for name in inputs),
                str(ROOT/'tests/v3_creature_insect_engine_test.c'),'-lm','-o',str(executable)],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Shared native adapter:',result.stdout)

    def test_controller_composition(self):
        from aflib import by_vrom,CODE_VROM,CODE_RAM,u32
        from v3_furniture_install import inputs
        directory=ROOT/os.environ.get('V3_INSECT_PROGRAMS','build/v3-creature-insects-work-01/programs-06')
        report=json.loads((directory/'programs.json').read_text())
        image,_=inputs(ROOT/'build/v3-creature-world-work-01/connected-15/build-lock.json')
        contract=report['native_abi']['controller'];files=by_vrom(image)
        # Synthetic resident addresses test composition/relocations only; no
        # cartridge is built and no synthetic function is run in an emulator.
        names=[r['symbol'] for r in contract['hooks']]+['af_insect_columns']
        symbols={name:0x80660000+64*i for i,name in enumerate(names)}
        changed,patches=install_controller(image,symbols,contract)
        self.assertEqual(len(patches),6)
        for vrom,ram in ((CODE_VROM,CODE_RAM),(0x8DEEC0,0x80A10210)):
            before=files[vrom].extract(image);restored=bytearray(changed[vrom])
            for patch in patches:
                if (patch['address']<0x80800000)!=(vrom==CODE_VROM): continue
                at=patch['address']-ram;n=patch['bytes']
                self.assertEqual(restored[at:at+n].hex(),patch['after'])
                if patch['retain_delay']:
                    self.assertEqual(restored[at+4:at+8],before[at+4:at+8])
                restored[at:at+n]=before[at:at+n]
            self.assertEqual(restored,before,'Unrelated native/resource hook changed')
        rel=changed[0x8E0870];previous=files[0x8E0870].extract(image)
        self.assertEqual(len(rel),len(previous))
        self.assertEqual(u32(rel,16),u32(previous,16)-len(contract['removed_relocations']))
        self.assertEqual(rel[:16],previous[:16]);self.assertEqual(rel[-4:],previous[-4:])
        symbols[names[0]]=0x80900000
        with self.assertRaises(ValueError): install_controller(image,symbols,contract)


if __name__=='__main__':unittest.main()
