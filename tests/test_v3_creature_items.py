"""Connected creature room path and current cartridge, without gameplay claims."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
import v3_creature_items as creatures

OUTPUT=ROOT/os.environ.get('V3_CREATURE_ITEMS_BUILD','build/v3-creature-parent-imports-01/creature-parent-runtime')


class ParentTests(unittest.TestCase):
    def test_connected_readers_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-creature-parents-') as folder:
            for stem in ('v3_creature_items_test','v3_creature_startup_test'):
                binary=Path(folder)/stem
                subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                    str(ROOT/'tests'/f'{stem}.c'),'-o',str(binary)],check=True,capture_output=True)
                result=subprocess.run([str(binary)],check=True,capture_output=True,timeout=20)
                self.assertIn(b'pass',result.stdout)

    def test_source_identity_keeps_native_herabuna(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        rows,receipt=creatures.source_records(source)
        trout=next(r for r in rows if r['source_item_id']=='2301')
        self.assertEqual((trout['item_id'],trout['display_item_id'],trout['name']),('2328','3CB8','brook trout'))
        self.assertNotIn('2301',{r['item_id'] for r in rows})
        self.assertEqual(len(creatures.encode(rows)),492)
        for damage in ('identity','readiness','name'):
            bad=copy.deepcopy(rows)
            if damage=='identity':bad[0]['item_id']='2301'
            elif damage=='readiness':bad[0]['ready']=True
            else:bad[0]['name']='made up'
            with self.assertRaises(ValueError):creatures.encode(bad)


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current connected creature build required')
class CartridgeTests(unittest.TestCase):
    def test_complete_current_path_resources_hooks_and_reconstruction(self):
        image,report=inputs(OUTPUT/'build-lock.json');base,prior=inputs(OUTPUT/'base-lock.json')
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        r=creatures.checked(image,report,source)
        self.assertEqual(len(r['profiles']),17);self.assertEqual(sum(p['reused_asset'] for p in r['profiles']),16)
        self.assertEqual(sum(p['object_bytes'] for p in r['profiles']),78544)
        self.assertEqual(len(r['hooks']),5)
        from v3_room_rig_runtime import bind_profiles
        bind_profiles(source,image,report)
        for key in ('save_runtime','save_codec','translation_baseline','furniture','staged_furniture','catalogue'):
            self.assertEqual(report[key],prior[key],key)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),image)
        blob=by_vrom(image)[BLOB].extract(image)
        boot=report['equipment_resources']['surface_bootstrap'];code=boot['code']
        e=report['equipment_resources'];at=e['blob_offset']+boot['offset']
        self.assertEqual(sha256(blob[at:at+code['bytes']]),code['sha256'])
        self.assertLessEqual(code['bytes'],boot['capacity'])
        self.assertIn(f'-DAF_CREATURE_ITEMS_VROM=0x{r["packet"]["vrom"]:X}u',code['flags'])
        # Whole original conversion bodies still verify after restoring known wrappers.
        damaged=bytearray(by_vrom(image)[CODE_VROM].extract(image));damaged[0x800BF000-CODE_RAM]^=1
        with self.assertRaises(ValueError):creatures.native_contract(damaged,report)
        from v3_furniture_pipeline import rig_import_plan
        inventory=dict(rows=[dict(item_id=p['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=p['source']['profile']) for p in r['profiles']])
        pending=rig_import_plan(inventory,prior,{},category='creature-profile-assets',source=source)
        self.assertEqual(pending['creature_parents'],sorted(p['source_item_id'] for p in r['profiles']))
        absent=copy.deepcopy(prior)
        absent['equipment_resources']['room_rigs']['rows']=[row for row in absent['equipment_resources']['room_rigs']['rows'] if row.get('mode')!=13]
        partial=rig_import_plan(inventory,absent,{},selected=['1C48'],category='creature-profile-assets',source=source)
        self.assertEqual(partial['creature_parents'],pending['creature_parents'])
        self.assertEqual(len(partial['resources']),16)
        complete=rig_import_plan(inventory,report,{},category='creature-profile-assets',source=source)
        self.assertNotIn('creature_parents',complete)
        import v3_optional_composition as composer
        old=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json')
            catalogue=composer.catalogue(image,report)
            self.assertEqual(len(catalogue),167)
            self.assertFalse({row['id'] for row in r['rows']}&set(catalogue))
            full=composer.compose(image,report,catalogue,composer.resolve(catalogue,list(catalogue)))[0]
            self.assertEqual(full,image)
            empty=composer.compose(image,report,catalogue,composer.resolve(catalogue,[]))[0]
            self.assertEqual(sha256(empty),report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=old


if __name__=='__main__':unittest.main()
