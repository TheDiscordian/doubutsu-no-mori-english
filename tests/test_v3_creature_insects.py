"""One connected host check for all converted insect behaviour programs."""
import json
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_creature_insects import PROGRAMS,rewrite,install_controller,install_spawn_manager,install_colony
PROGRAM_DIRECTORY=ROOT/os.environ.get('V3_INSECT_PROGRAMS','build/v3-creature-insects-work-01/programs-14')


class CreatureInsectTests(unittest.TestCase):
    def test_colony_lifecycle_and_drawing(self):
        with tempfile.TemporaryDirectory(prefix='af-insect-colony-') as temporary:
            executable=Path(temporary)/'colony'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all','-Wall','-Wextra','-Werror',
                '-I'+str(ROOT/'overlays/v3'),str(ROOT/'overlays/v3/creature_insect_colony.c'),
                str(ROOT/'overlays/v3/creature_insect_colony_draw.c'),
                str(ROOT/'tests/v3_creature_insect_colony_test.c'),'-lm','-o',str(executable)],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('catch handoff, bee preservation',result.stdout)

    def test_native_spawn_manager(self):
        directory=PROGRAM_DIRECTORY
        data=(directory/'insect-calendar.bin').read_bytes()
        with tempfile.TemporaryDirectory(prefix='af-insect-manager-') as temporary:
            temp=Path(temporary);exe=temp/'manager'
            (temp/'calendar.h').write_text('const u8 af_insect_calendar[]={'+
                ','.join(str(b) for b in data)+'};\nconst u32 af_insect_calendar_bytes='+str(len(data))+';\n')
            result=subprocess.run(['cc','-std=c11','-O1','-g','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all','-Wall','-Wextra','-Werror',
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(temp),
                str(ROOT/'overlays/v3/creature_insect_spawns.c'),
                str(ROOT/'overlays/v3/creature_insect_manager.c'),
                str(ROOT/'tests/v3_creature_insect_manager_test.c'),'-lm','-o',str(exe)],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(exe)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('Native insect manager:',result.stdout)

    def test_complete_spawn_path(self):
        from v3_creature_spawns import insect_calendars
        from v3_furniture_pipeline import Source
        directory=PROGRAM_DIRECTORY
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        data,report=insect_calendars(source)
        self.assertEqual((directory/'insect-calendar.bin').read_bytes(),data)
        self.assertEqual(json.loads((directory/'programs.json').read_text())['spawning'],
                         json.loads(json.dumps(report)))
        schedule=report['calendars'];cases=[]
        # Every source month/time list, a complete seasonal blend, and individual
        # source masks. No native/emulator replay or per-species fixture.
        inputs=[(m,m,t,255,0,1.0) for m in range(12) for t in range(6)]
        inputs += [(0,0,t,255,1,1.0) for t in range(6)]
        inputs += [(m,(m+1)%12,2,255,0,0.5) for m in range(12)]
        inputs += [(6,7,2,mask,0,0.5) for mask in [0,*[1<<i for i in range(8)]]]
        for m,n,t,mask,island,rate in inputs:
            lists=[(schedule[72+t if island else m*6+t],rate)]
            if rate!=1 and not island: lists.append((schedule[n*6+t],1-rate))
            expected=[(actor,area,weight*r) for rows,r in lists for actor,area,weight in rows]
            expected+=report['additional_spawns']
            expected=[row for row in expected if not 32<=row[0]<=39 or mask&(1<<(row[0]-32))]
            case=struct.pack('>5IfI',m,n,t,mask,island,rate,len(expected))
            case+=b''.join(struct.pack('>IIf',*row) for row in expected);cases.append(case)
        payload=struct.pack('>I',len(data))+data+struct.pack('>I',len(cases))+b''.join(cases)
        with tempfile.TemporaryDirectory(prefix='af-insect-spawns-') as temporary:
            exe=Path(temporary)/'spawns';fixture=Path(temporary)/'calendar.bin';fixture.write_bytes(payload)
            result=subprocess.run(['cc','-std=c11','-O1','-g','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-sanitize-recover=all','-Wall','-Wextra','-Werror',
                '-I'+str(ROOT/'overlays/v3'),str(ROOT/'overlays/v3/creature_insect_spawns.c'),
                str(ROOT/'tests/v3_creature_insect_spawns_test.c'),'-lm','-o',str(exe)],
                capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(exe),str(fixture)],capture_output=True,text=True,timeout=15)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('complete shared habitat/creation',result.stdout)

    def test_complete_program_category(self):
        directory=PROGRAM_DIRECTORY
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
        directory=PROGRAM_DIRECTORY
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
        contract=report['native_abi']['spawn_manager']
        changed,patch=install_spawn_manager(image,{'af_v3_insect_spawn':0x80660000},contract)
        original=files[0x821B40].extract(image);restored=bytearray(changed[0x821B40])
        at=patch['address']-patch['owner_ram']
        self.assertEqual(restored[at:at+8].hex(),patch['after'])
        restored[at:at+8]=bytes.fromhex(patch['before'])
        self.assertEqual(restored,original,'Existing gold-tree and native manager paths changed')
        with self.assertRaises(ValueError):
            install_spawn_manager(image,{'af_v3_insect_spawn':0x80900000},contract)
        contract=report['native_abi']['colony']
        symbols={'af_insect_colony_profile':0x80660000,'af_insect_hook_net_index':0x80660100}
        changed,patch=install_colony(image,symbols,contract)
        original=files[CODE_VROM].extract(image);restored=bytearray(changed[CODE_VROM])
        at=contract['table_address']-CODE_RAM
        self.assertEqual(restored[at:at+0x14],bytes(0x14))
        self.assertEqual(u32(restored,at+0x14),symbols['af_insect_colony_profile'])
        restored[at:at+0x20]=bytes(0x20)
        self.assertEqual(restored,original,'Existing additive actor lookup changed')
        original=files[contract['owner_vrom']].extract(image)
        restored=bytearray(changed[contract['owner_vrom']]);at=contract['address']-contract['owner_ram']
        self.assertEqual(restored[at:at+28].hex(),patch['after'])
        restored[at:at+28]=bytes.fromhex(contract['before'])
        self.assertEqual(restored,original,'Existing catch text/collection or player hooks changed')
        symbols['af_insect_colony_profile']=0x80900000
        with self.assertRaises(ValueError):install_colony(image,symbols,contract)
        colony=report['colony'];asset=(directory/'colony.bin').read_bytes()
        self.assertEqual(sha256(asset),colony['object_sha256'])
        self.assertEqual(len(asset),colony['object_bytes'])
        self.assertEqual(sum(m['triangles'] for m in colony['models']),12)
        self.assertEqual(colony['native_rates'],[[2,1],[1,-2]])
        model=asset[colony['model_offset']:]
        commands=list(struct.iter_unpack('>II',model))
        self.assertIn((0xFCFFE3FF,0xFF0DF43F),commands)
        self.assertIn((0xE200001C,0xC8104B50),commands)
        self.assertIn((0xDE000000,0x08000000),commands)


if __name__=='__main__':unittest.main()
