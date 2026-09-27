"""Focused checks for shared console dispatch and complete staged models."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source,rig_import_plan,scan
from v3_room_rig_runtime import bind_profiles
import v3_console_room as console


class ConsoleRoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=ROOT/'build/v3-console-room-imports-01'
        plan=json.loads((cls.batch/'pipeline.json').read_bytes())
        cls.out=(ROOT/plan['final_lock']).parent
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-console-emulator-native-01/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_dispatch_boundaries(self):
        with tempfile.TemporaryDirectory(prefix='v3-console-room-') as temp:
            binary=Path(temp)/'check'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                str(ROOT/'tests/v3_console_room_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())

    def test_complete_models_current_binding_and_unchanged_dependencies(self):
        files=by_vrom(self.image);old=by_vrom(self.base);blob=files[BLOB].extract(self.image)
        images=self.report['equipment_resources']['console_images'];previous=self.prior['equipment_resources']['console_images']
        rows=console.checked_runtime(self.report['equipment_resources'],blob,self.image)
        self.assertEqual(len(rows),12);self.assertEqual(sum(r['engine_installed'] for r in rows.values()),11)
        self.assertEqual(sum(r['profile_installed'] for r in rows.values()),11)
        prepared={r['item_id']:r for r in json.loads((self.batch/'prepared/art.json').read_bytes())['objects']}
        source_bindings=bind_profiles(self.source,self.image,self.report)
        for donor,r in rows.items():
            life=console.lifecycle(self.source.profile(int(donor,16)))
            self.assertEqual(life,r['room_lifecycle'])
            if not r['engine_installed']:
                self.assertEqual(r['image_kind'],2);self.assertNotIn(donor,source_bindings);continue
            art=prepared[donor];data=(self.batch/'prepared'/art['object_file']).read_bytes()
            self.assertEqual(data,blob[r['blob_offset']:r['blob_offset']+r['bytes']])
            self.assertEqual(r['bytes'],4880);self.assertEqual(len(art['models']),3)
            self.assertEqual(source_bindings[donor]['room_runtime']['vtable'],console.VTABLE)
            self.assertEqual(source_bindings[donor]['room_lifecycle'],life)
        p=images['packet'];q=previous['packet'];prior_blob=old[BLOB].extract(self.base)
        packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        prior_packet=prior_blob[q['blob_offset']:q['blob_offset']+q['bytes']]
        self.assertEqual(packet[:console.RAM-p['ram']],prior_packet[:console.RAM-p['ram']])
        self.assertEqual(packet[console.END-p['ram']:],prior_packet[console.END-p['ram']:])
        self.assertEqual(images['emulator'],previous['emulator'])
        for key in ('console_storage','room_goods','room_carry','room_rigs'):
            current=copy.deepcopy(self.report['equipment_resources'][key])
            before=copy.deepcopy(self.prior['equipment_resources'][key])
            if 'startup' in current:
                # Shared preload code embeds the changed complete packet CRC.
                # Only its digest changes in these retained-resource receipts.
                current['startup'].pop('sha256');before['startup'].pop('sha256')
            self.assertEqual(current,before)
        raw=images['pool'];a=raw['physical'];b=a+raw['bytes'];self.assertEqual(self.image[a:b],self.base[a:b])
        # No native room or emulator instructions change in this batch.
        for vrom in (console.ROOM_VROM,0x844400,0x7492E0,0x771900):
            self.assertEqual(files[vrom].extract(self.image),old[vrom].extract(self.base))
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_damaged_room_bindings_reject(self):
        blob=bytearray(by_vrom(self.image)[BLOB].extract(self.image));e=self.report['equipment_resources']
        broken=copy.deepcopy(e);broken['console_images']['room']['rows'][0]['game_index']=20
        with self.assertRaises(ValueError):console.checked_runtime(broken,blob,self.image)
        broken=copy.deepcopy(e);broken['console_images']['room']['rows'][2]['engine_installed']=True
        with self.assertRaises(ValueError):console.checked_runtime(broken,blob,self.image)
        p=e['console_images']['packet'];blob[p['blob_offset']+console.VTABLE-p['ram']]^=1
        with self.assertRaises(ValueError):console.checked_runtime(e,blob,self.image)

    def test_private_composition(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)

    def test_completed_console_profiles_do_not_schedule_again(self):
        bindings=bind_profiles(self.source,self.image,self.report)
        ids=tuple(self.source.console_runtime_bindings)
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',
            installed=[int(r['id'].rsplit('/',1)[1],16) for r in self.report['furniture']['imports']],selected=ids)
        plan=rig_import_plan(inventory,self.report,bindings,category=console.CATEGORY,source=self.source)
        self.assertFalse(any(plan.values()),plan)
        disk=next(r for r in inventory['rows'] if r['item_id']=='1DCC')
        self.assertIn('QD disk engine',disk['reason'])


if __name__=='__main__':unittest.main()
