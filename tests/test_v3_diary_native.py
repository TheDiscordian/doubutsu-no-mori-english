"""One combined check for the real calendar and room-to-menu data bindings."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_RAM,CODE_VROM,sha256
from v3_furniture_install import inputs
from v3_diary_events import prepare,RULES


class DiaryNativeTests(unittest.TestCase):
    def test_native_calendar_and_entry_under_sanitizers(self):
        base,_=inputs(ROOT/'build/v3-native-variants-work-01/connected-02/cartridge/build-lock.json')
        data,report=prepare(base)
        self.assertEqual(len(report['rules']),19)
        self.assertEqual(len(report['labels']),20)
        self.assertEqual([r['key'] for r in report['labels'][:-1]],[r[0] for r in RULES])
        with tempfile.TemporaryDirectory(prefix='v3-diary-native-') as tmp:
            tmp=Path(tmp)
            (tmp/'events.c').write_bytes(data)
            # Actual N64 lunar functions/table; only their platform includes are
            # replaced by equivalent host types in the fixture.
            lunar=(ROOT/'upstream/af/src/code/lb_reki.c').read_text()
            (tmp/'reference-reki.inc').write_text('\n'.join(line for line in lunar.splitlines()
                if not line.startswith('#include'))+'\n')
            core=by_vrom(base)[CODE_VROM].extract(base)
            schedule=core[0x80104B60-CODE_RAM:0x80104F2C-CODE_RAM]
            import struct
            master='const unsigned int af_diary_event_master[81][3]={\n'+''.join(
                '{'+','.join(hex(v) for v in row)+'},\n' for row in struct.iter_unpack('>3I',schedule))+'};\n'
            profiles='const unsigned char af_diary_native_profiles[79][80]={\n'+''.join(
                f'[{63+i}]={{'+','.join(str(v) for v in struct.pack('>HHI',1087+i,0x30FC+i*4,1))+'},\n'
                for i in range(16))+'};\n'
            (tmp/'native-data.c').write_text(master+profiles)
            sources=['tests/v3_diary_native_test.c','overlays/v3/diary_events.c',
                'overlays/v3/diary_native.c','overlays/v3/diary_screen.c',
                'overlays/v3/diary_calendar.c','overlays/v3/diary_menu.c','overlays/v3/diary.c']
            compile=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
                '-Ioverlays/v3','-I'+str(tmp),*sources,str(tmp/'events.c'),str(tmp/'native-data.c'),
                '-o',str(tmp/'check')],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(compile.returncode,0,compile.stdout+compile.stderr)
            run=subprocess.run([str(tmp/'check')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_linked_native_entry_and_disjoint_state(self):
        path=ROOT/'build/v3-diary-category-work-01/ui-06'
        r=json.loads((path/'ui.json').read_bytes());c=r['compiled'];b=c['bindings']
        self.assertEqual(sha256((path/'resident/code.bin').read_bytes()),c['sha256'])
        for name in ('af_diary_room_move','af_diary_native_open','af_diary_native_visit','af_diary_native_attend'):
            self.assertTrue(0x806A0000<=c['symbols'][name]<0x806A7FF0)
        self.assertEqual(b['af_diary_native_screen'],0x806A8000)
        self.assertLessEqual(c['state_bytes'],0x900)
        self.assertEqual(b['af_diary_native_context'],0x806A8900)
        self.assertLessEqual(c['context_bytes'],0x6F0)
        self.assertEqual(b['af_diary_native_candidate'],0x806D4000)
        self.assertEqual(b['af_diary_native_candidate_guard'],0x806D4000+48048)
        visit=r['hooks']['visit']
        self.assertEqual(visit['address'],0x8007FA20)
        self.assertEqual(visit['original'],0x800815F0)
        self.assertEqual(visit['before'][8:],visit['after'][8:])
        self.assertEqual(visit['target'],c['symbols']['af_diary_native_live_player'])
        for name,digest in r['sources'].items():self.assertEqual(sha256((ROOT/name).read_bytes()),digest,name)
        self.assertFalse(r['installed']);self.assertFalse(r['native_execution_tested'])


if __name__=='__main__':unittest.main()
