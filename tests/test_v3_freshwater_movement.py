"""Compare every ported freshwater callback to the actual donor source."""
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_freshwater_movement import source_contract,DONOR


def function(text,name):
    match=re.search(r'static\s+[^;{}]*?\b'+name+r'\([^;{}]*\)\s*\{',text)
    if match is None:raise ValueError('Missing donor definition: '+name)
    start=match.start();at=match.end();depth=1
    while depth:
        depth+=(text[at]=='{')-(text[at]=='}');at+=1
    return text[start:at]


class FreshwaterDonorTests(unittest.TestCase):
    def test_complete_donor_functions(self):
        proof=source_contract()
        self.assertEqual([r['symbol'] for r in proof],[r[0] for r in DONOR])

    def test_actual_donor_callbacks_under_sanitizers(self):
        source=(ROOT/'local/ac-decomp/src/actor/ac_gyo_test.c').read_text()
        names=('aGTT_speed_reset','aGTT_speed_calc','aGTT_chase_s_angle',
            'aGTT_swim_speed_check','aGTT_swim_speed_change','aGTT_flow_direction',
            'aGTT_swim_init','aGTT_wait_init','aGTT_escape_init','aGTT_swim','aGTT_wait','aGTT_escape')
        chunks=['static int aGTT_swim_speed_check(aGYO_CTRL_ACTOR *,f32,f32,f32);',
            'static int aGTT_swim_speed_change(aGYO_CTRL_ACTOR *,f32,f32,f32);']
        for name in names:
            raw=function(source,name)
            if name=='aGTT_swim_speed_check':raw=raw.replace(name,'donor60_speed_check')
            if name=='aGTT_swim_speed_change':raw=raw.replace(name,'donor60_speed_change')
            if name=='aGTT_flow_direction':raw=raw.replace('static s16 angl_add_table[]','flow_calls++;\n    static s16 angl_add_table[]')
            if name=='aGTT_escape':
                old='chase_f(&actorx->speed, 0.0f, 0.02f);'
                self.assertEqual(raw.count(old),1)
                raw=raw.replace(old,old+'\n                '+old)
            chunks.append(raw)
        with tempfile.TemporaryDirectory(prefix='v3-freshwater-donor-') as temp:
            header=Path(temp)/'donor.h';header.write_text('\n'.join(chunks))
            binary=Path(temp)/'check'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-DDONOR_HEADER="'+str(header)+'"',str(ROOT/'tests/v3_freshwater_movement_test.c'),
                '-lm','-o',str(binary)],check=True,capture_output=True,text=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=30)
            self.assertIn('99 complete freshwater donor/port cases passed',result.stdout)


if __name__=='__main__':unittest.main()
