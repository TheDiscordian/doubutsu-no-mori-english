"""Single shared transition check, with no native fixture or old-build replay."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from apply_translation import write_new
from v3_furniture_pipeline import Source
from v3_holiday_maps import discover,encode
from v3_holiday_transition import generate


class HolidayTransitionTests(unittest.TestCase):
    def test_connected_source_transition_and_geometry(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        graph=discover(source);packet=encode(graph);code,report=generate(source)
        self.assertEqual(len(report['functions']),6)
        self.assertEqual([r['shape'] for r in report['escape_tables']],[[2,28,2],[12,2]])
        self.assertEqual([r['bytes'] for r in report['escape_tables']],[448,96])
        expected=[]
        for row in graph['maps']:
            for variant,layout in enumerate(row.get('layouts',[])):
                for point in layout:
                    x,z=point['x'],point['z'];result=0
                    for actor in layout:
                        ux,uz=actor['x'],actor['z']
                        if actor['source_name']>>12==5:
                            if ux<=x<=ux+1 and uz<=z<=uz+1:result=2;break
                        elif abs(x-ux)<=1 and abs(z-uz)<=1:result=1;break
                    expected.append((row['event'],variant,x,z,result))
        with tempfile.TemporaryDirectory(prefix='v3-holiday-transition-') as temp:
            out=Path(temp);write_new(out/'source.c',code.encode())
            data='static const unsigned char maps[]={'+','.join(map(str,packet))+'};\n'
            data+='static const unsigned int expected[][5]={'+','.join('{'+','.join(map(str,r))+'}' for r in expected)+'};\n'
            write_new(out/'holiday-transition-data.h',data.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(out),'tests/v3_holiday_transition_test.c',
                'overlays/v3/holiday_transition.c','overlays/v3/holiday_transition_native.c',
                'overlays/v3/holiday_reserved.c',str(out/'source.c'),'-o',str(out/'check')]
            for cmd in (command,[str(out/'check')]):
                r=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                if r.stdout:print(r.stdout.strip())


if __name__=='__main__':unittest.main()
