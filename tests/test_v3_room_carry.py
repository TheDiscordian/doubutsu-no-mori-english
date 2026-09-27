"""Moving-table core comparisons; native owner hooks are not installed yet."""
from pathlib import Path
import copy
import subprocess
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_furniture_pipeline import Source
from v3_furniture_install import inputs
import v3_room_carry as carry


class CarryTests(unittest.TestCase):
    def test_complete_source_bindings(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        contract=carry.source_contract(source)
        self.assertEqual(contract['state_bytes'],152)
        self.assertEqual(contract['slots'],4)
        self.assertFalse(contract['callback_installed'])
        for row in contract['functions'].values():
            bad=copy.copy(source);bad.rel=bytearray(source.rel)
            bad.rel[source.sections[1][0]+row['offset']]^=1
            with self.assertRaisesRegex(ValueError,'dependency'):carry.source_contract(bad)
            if row['relocations']:
                at=next(iter(row['relocations']));ref=row['relocations'][at]
                bad=copy.copy(source);bad.code_relocations=dict(source.code_relocations)
                bad.code_relocations[row['offset']+at]=(*ref[:3],ref[3]+4)
                with self.assertRaisesRegex(ValueError,'dependency'):carry.source_contract(bad)
        for at in carry.CONSTANTS:
            bad=copy.copy(source);bad.rel=bytearray(source.rel)
            bad.rel[source.sections[4][0]+at]^=1
            with self.assertRaisesRegex(ValueError,'constant'):carry.source_contract(bad)
        for at in (0x3CB40,0x3CB60,0x3CB88,0x3CBA0):
            bad=copy.copy(source);bad.data=bytearray(source.data);bad.data[at]^=1
            with self.assertRaisesRegex(ValueError,'footprint'):carry.source_contract(bad)
        bad=copy.copy(source);bad.relocations=dict(source.relocations)
        bad.relocations[0x3CB88]=bad.relocations[0x3CB8C]
        with self.assertRaisesRegex(ValueError,'footprint'):carry.source_contract(bad)

    def test_native_owner_and_missing_loose_item_support(self):
        from aflib import by_vrom
        image,_=inputs(ROOT/'build/v3-switched-joint-imports-03/profile-runtime/build-lock.json')
        contract=carry.native_contract(image)
        self.assertEqual(contract['movement_calls'],[0x8093F18C,0x8093F598,0x80941524])
        self.assertFalse(contract['installed'])
        self.assertFalse(contract['loose_item_rotation_present'])
        for row in contract['blocks']:
            resource=by_vrom(image)[row['vrom']];raw=bytearray(resource.extract(image))
            raw[row['address']-row['origin']]^=1
            # Mutate the extracted resource, including compressed Shop_Goods,
            # without manufacturing another full 64-MiB cartridge.
            files=by_vrom(image);files[row['vrom']]=SimpleNamespace(extract=lambda _:raw)
            with patch.object(carry,'by_vrom',return_value=files):
                with self.assertRaisesRegex(ValueError,'native dependency'):carry.native_contract(image)

    def test_actual_donor_carrying_under_sanitizers(self):
        move=(ROOT/'local/ac-decomp/src/actor/ac_my_room_move.c_inc').read_text()
        functions=[move[:move.index('static void aMR_RegistItemToFitFurniture(')]]
        for path,names in (
            ('local/ac-decomp/src/actor/ac_my_room_move.c_inc',[
                ('static void ','aMR_RegistItemToFitFurniture'),('static int ','aMR_RequestItemToFitFurniture'),
                ('static void ','aMR_RequestItemToUnFitFurniture'),('static void ','aMR_GetItemPosOnMovingFurniture')]),
            ('local/ac-decomp/src/actor/ac_my_room.c',[
                ('extern FTR_ACTOR* ','aMR_GetParentFactor'),('extern s16 ','aMR_GetParentAngleOffset')]),
            ('local/ac-decomp/src/actor/ac_my_room_draw.c_inc',[('static void ','aMR_DrawItemOnMovingFurniture')])):
            text=(ROOT/path).read_text()
            for prefix,name in names:
                start=text.index(prefix+name+'(')
                while text.index(';',start)<text.index('{',start):start=text.index(prefix+name+'(',start+1)
                end=text.index('\n}',start)+2;functions.append(text[start:end])
        with tempfile.TemporaryDirectory(prefix='v3-room-carry-') as directory:
            directory=Path(directory);(directory/'donor_carry.inc').write_text('\n\n'.join(functions))
            binary=directory/'test'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-ffp-contract=off','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-fno-pie','-no-pie','-I'+str(directory),str(ROOT/'tests/v3_room_carry_test.c'),
                '-lm','-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('90 donor carrying cases, 1890 transformed/drawn frames',result.stdout)


if __name__=='__main__':unittest.main()
