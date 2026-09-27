"""Focused needle conversion checks; no claim of installed room carrying."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_furniture_pipeline import Source,prepare,PreparedAssets
from v3_furniture_install import inputs
from v3_furniture_joint_rigs import lifecycle
import v3_furniture_needle as needle


class NeedleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_source_motion_guards_and_prepared_art_reuse(self):
        source=self.source;parts=prepare(source,0x3064);profile=parts[0];before=copy.deepcopy(profile)
        contract=needle.source_contract(source,profile)
        self.assertTrue(contract['parent_required'])
        self.assertFalse(contract['callback_installed'])
        self.assertEqual(contract['native_rotation_states'],[3,4])
        self.assertEqual(contract['source_steps_per_native_update'],2)
        self.assertIsNone(lifecycle(source,profile))
        self.assertIsNone(needle.source_contract(source,prepare(source,0x3070)[0]))
        self.assertEqual(profile,before)
        cache=PreparedAssets(source,[ROOT/'build/v3-joint-callback-rigs-prepared-01'])
        self.assertIsNotNone(cache.reuse(source,'3064',parts))
        for row in contract['functions'].values():
            bad=copy.copy(source);bad.rel=bytearray(source.rel)
            bad.rel[source.sections[1][0]+row['offset']]^=1
            with self.assertRaises(ValueError,msg=row['symbol']):needle.source_contract(bad,profile)
            if row['relocations']:
                at=next(iter(row['relocations']));ref=row['relocations'][at]
                bad=copy.copy(source);bad.code_relocations=dict(source.code_relocations)
                bad.code_relocations[row['offset']+at]=(*ref[:3],ref[3]+4)
                with self.assertRaises(ValueError,msg=row['symbol']):needle.source_contract(bad,profile)
        for at in needle.CONSTANTS:
            bad=copy.copy(source);bad.rel=bytearray(source.rel)
            bad.rel[source.sections[4][0]+at]^=1
            with self.assertRaisesRegex(ValueError,'constant'):needle.source_contract(bad,profile)
        bad=copy.copy(source);bad.relocations=dict(source.relocations)
        bad.relocations[0x88CC0+9*4]=bad.relocations[0x88CC0+11*4]
        with self.assertRaisesRegex(ValueError,'status dispatch'):needle.source_contract(bad,profile)

    def test_native_rotation_mapping_on_current_cartridge(self):
        image,_=inputs(ROOT/'build/v3-switched-joint-imports-03/profile-runtime/build-lock.json')
        result=needle.native_contract(image)
        self.assertEqual(result['source_left_native'],3)
        self.assertEqual(result['source_right_native'],4)
        self.assertFalse(result['parent_binding_installed'])
        from aflib import by_vrom
        owner=by_vrom(image)[0x82D7F0];self.assertFalse(owner.pend)
        for row in result['blocks']:
            bad=bytearray(image);bad[owner.pstart+row['address']-0x80936710]^=1
            with self.assertRaisesRegex(ValueError,'native dependency'):needle.native_contract(bad)

    def test_actual_donor_motion_and_joint_rotation_under_sanitizers(self):
        sources=[('local/ac-decomp/src/game/m_lib.c',[('extern f32 ','add_calc')]),
            ('local/ac-decomp/src/actor/ac_my_room.c',
                [('extern FTR_ACTOR* ','aMR_GetParentFactor'),('extern s16 ','aMR_GetParentAngleOffset')]),
            ('local/ac-decomp/src/furniture/ac_ike_jny_houi01.c',
                [('static void ','fIJHOUI_ct'),('static void ','fIJHOUI_Status2SetMode'),
                 ('static void ','fIJHOUI_mv'),('static int ','fIJHOUI_DrawBefore')])]
        functions=[]
        for path,names in sources:
            text=(ROOT/path).read_text()
            for prefix,name in names:
                # Skip the forward declarations; retain each definition unchanged.
                start=text.index(prefix+name+'(')
                while text.index(';',start)<text.index('{',start):
                    start=text.index(prefix+name+'(',start+1)
                end=text.index('\n}',start)+2;functions.append(text[start:end])
        with tempfile.TemporaryDirectory(prefix='v3-room-needle-') as directory:
            directory=Path(directory);(directory/'donor_needle.inc').write_text('\n\n'.join(functions))
            binary=directory/'test'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-ffp-contract=off','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-fno-pie','-no-pie','-I'+str(directory),str(ROOT/'tests/v3_room_needle_test.c'),
                '-lm','-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('19232 donor needle comparisons',run.stdout)


if __name__=='__main__':unittest.main()
