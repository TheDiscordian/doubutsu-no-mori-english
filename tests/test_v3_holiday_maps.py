"""Complete layout/category check; no emulator fixture or old-build execution."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_furniture_pipeline import Source
from v3_holiday_maps import discover,encode,owner_source
from apply_translation import write_new


class HolidayMapsTests(unittest.TestCase):
    def test_native_binding_contract(self):
        from v3_holiday_maps import native_contract
        from v3_furniture_install import inputs
        from v3_holiday_placement import BINDINGS
        image,_=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-state-05/build-lock.json')
        contract=native_contract(image)
        self.assertEqual(contract['game_context'],0x8010EF90)
        self.assertEqual(BINDINGS['af_holiday_native_game'],contract['game_context'])

    def test_connected_layout_and_source_owners(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        report=discover(source);packet=encode(report);generated,owners=owner_source(source)
        self.assertEqual(len(report['maps']),17)
        self.assertEqual(sum(r.get('variants',0) for r in report['maps']),52)
        self.assertEqual(len(owners['owners']),14)
        expected=[]
        for row in report['maps']:
            for v,actors in enumerate(row.get('layouts',[])):
                for i,a in enumerate(actors):expected.append((row['event'],v,i,a['source_name'],a['x'],a['z']))
        with tempfile.TemporaryDirectory(prefix='v3-holiday-maps-') as temp:
            out=Path(temp)
            write_new(out/'owners.c',generated.encode())
            text='static const unsigned char maps[]={'+','.join(map(str,packet))+'};\n'
            text+='static const unsigned int expected[][6]={'+','.join('{'+','.join(map(str,r))+'}' for r in expected)+'};\n'
            write_new(out/'holiday-maps-data.h',text.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(out),'tests/v3_holiday_maps_test.c',
                'overlays/v3/holiday_reserved.c',str(out/'owners.c'),'-o',str(out/'check')]
            for cmd in (command,[str(out/'check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())
            # Same generated source and data; exercise the complete new native
            # adapter in this batch, without replaying a cartridge fixture.
            from v3_holiday_native import identities
            from v3_holiday_events import discover as event_discover,encode as event_encode
            ids,_=identities()
            arrays=(('af_holiday_native_ids',ids[:128]),('af_holiday_source_ids',ids[128:]),
                ('af_holiday_event_data',event_encode(event_discover(source))))
            native_data='#include "holiday-maps-data.h"\n'+'\n'.join('const unsigned char '+name+'[]={'+
                ','.join(map(str,data))+'};' for name,data in arrays)+'\n'
            write_new(out/'holiday-native-data.h',native_data.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections',
                '-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'overlays/v3'),'-I'+str(out),
                'tests/v3_holiday_dedicated_native_test.c',
                *(f'overlays/v3/{s}.c' for s in ('holiday_reserved','holiday_native','holiday_events')),
                str(out/'owners.c'),'-o',str(out/'native-check')]
            for cmd in (command,[str(out/'native-check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())


if __name__=='__main__':unittest.main()
