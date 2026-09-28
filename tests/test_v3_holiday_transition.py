"""Single shared transition check, with no native fixture or old-build replay."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import re
import os

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from apply_translation import write_new
from v3_furniture_pipeline import Source
from v3_holiday_maps import discover,encode
from v3_holiday_transition import generate
from v3_password_policy import function


class HolidayTransitionTests(unittest.TestCase):
    def test_bound_current_cartridge(self):
        import zlib
        from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
        from v3_furniture_install import inputs
        directory=ROOT/os.environ.get('V3_HOLIDAY_TRANSITION_BUILD',
            'build/v3-diary-category-work-01/event-transition-bound-02')
        image,r=inputs(directory/'build-lock.json');base,prior=inputs(directory/'base-lock.json')
        e=r['equipment_resources'];events=e['npc_extra']['events'];stage=events['transition']
        p=e['holiday_state']['packet'];self.assertEqual(p,e['holiday_fishing']['packet'])
        self.assertTrue(stage['installed']);self.assertTrue(stage['native_scene_services_bound'])
        self.assertFalse(stage['native_execution_verified'])
        raw=image[p['physical']:p['physical']+p['bytes']];old=base[p['physical']:p['physical']+p['bytes']]
        a,b=0x806FC000-p['ram'],0x806FE000-p['ram']
        self.assertEqual(raw[:a],old[:a]);self.assertEqual(raw[b:],old[b:])
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(zlib.crc32(raw),p['crc32'])
        code=stage['code'];self.assertLessEqual(code['bytes'],b-a)
        self.assertEqual(sha256(raw[a:a+code['bytes']]),code['sha256'])
        self.assertEqual(raw[a+code['bytes']:b],bytes(b-a-code['bytes']))
        symbols=events['native_directory']['code']['symbols']
        for name in ('af_holiday_native_type','af_holiday_native_days','af_holiday_native_index'):
            self.assertEqual(stage['bindings'][name],symbols[name])
            self.assertEqual(code['link_symbols'][name],symbols[name])
        self.assertNotEqual(stage['bindings']['af_holiday_native_index'],0x8013A098)
        self.assertEqual(stage['bindings']['af_decor_actor_resolve'],
            events['decorations']['controllers']['code']['symbols']['af_decor_actor_resolve'])
        self.assertEqual(stage['bindings']['af_holiday_scene_bind'],events['demo']['code']['symbols']['af_holiday_scene_bind'])
        self.assertEqual(code['symbols']['af_holiday_transition_run'],0x806FC000)
        self.assertIn('af_holiday_transition_live_fade',code['symbols'])
        files=by_vrom(image);before=by_vrom(base);core=files[CODE_VROM].extract(image)
        self.assertEqual(core,before[CODE_VROM].extract(base))
        for row in stage['live']['native_functions']:
            at=row['address']-CODE_RAM
            self.assertEqual(sha256(core[at:at+row['bytes']]),row['sha256'])
        self.assertEqual(r['save_codec']['format_version'],prior['save_codec']['format_version'])
        self.assertEqual(r['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])

    def test_live_identity_binding(self):
        from v3_holiday_native import identities
        ids,_=identities()
        with tempfile.TemporaryDirectory(prefix='v3-holiday-identities-') as temp:
            target=Path(temp)/'check'
            fixture='const unsigned char af_holiday_transition_maps[1496]={0};\n'
            for name,data in (('af_holiday_native_ids',ids[:128]),('af_holiday_source_ids',ids[128:])):
                fixture+='const unsigned char '+name+'[128]={'+','.join(map(str,data))+'};\n'
            write_new(Path(temp)/'holiday-identity-data.h',fixture.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections',
                '-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'overlays/v3'),'-I'+temp,
                'tests/v3_holiday_identity_test.c','overlays/v3/holiday_transition_identity.c',
                'overlays/v3/holiday_native.c','-o',str(target)]
            for cmd in (command,[str(target)]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_live_scene_services(self):
        with tempfile.TemporaryDirectory(prefix='v3-holiday-scene-native-') as temp:
            target=Path(temp)/'check'
            field=(ROOT/'local/ac-decomp/src/game/m_field_info.c').read_text()
            header=(ROOT/'local/ac-decomp/include/m_field_info.h').read_text()
            enum=re.search(r'enum\s*\{\s*mFI_CLIMATE_0[^}]+\};',header)[0]
            fixture='#define FALSE 0\n#define TRUE 1\n'+enum+'\nstatic int l_mFI_climate;\n'
            fixture+='static void mCoBG_InitBoatCollision(void) {}\n'
            fixture+='\n'.join(function(field,n) for n in (
                'mFI_GetClimate','mFI_SetClimate','mFI_CheckBeforeScenePerpetual','mFI_ChangeClimate_ForEventNotice'))
            write_new(Path(temp)/'holiday_scene_climate_source.h',fixture.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(ROOT/'overlays/v3'),'-I'+temp,'tests/v3_holiday_scene_native_test.c','-o',str(target)]
            for cmd in (command,[str(target)]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

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
