"""Focused current-build checks for the shared start-disabled placement rule."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs,profile
from v3_furniture_pipeline import Source,prepare,metadata,identity_rows
from v3_import_storage import ROWS,ITEMS,slot
import v3_furniture_behaviours as behaviour
import v3_room_rig_runtime as room
import v3_optional_composition as composer

OUT=ROOT/'build/v3-start-disabled-imports-01/cartridge'


class InitialSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-start-disabled-profiles-01/base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_native_helper_under_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-initial-switch-') as temporary:
            binary=Path(temporary)/'test'
            compile=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-DAF_V3_INITIAL_SWITCH=1','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_furniture_behaviours_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(compile.returncode,0,compile.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('original defaults, and actor bounds pass',run.stdout)

    def test_complete_owner_binding_and_ordinary_import(self):
        from v3_furniture_runtime import VROM,RELOC,RAM
        binding=behaviour.checked_initial_switch(self.image,self.report,self.blob)
        self.assertEqual(binding['mask'],0x1000)
        current=by_vrom(self.image)[VROM].extract(self.image);original=by_vrom(self.base)[VROM].extract(self.base)
        at=behaviour.SWITCH_PATCH-RAM;restored=bytearray(current);restored[at:at+20]=behaviour.SWITCH_BEFORE
        self.assertEqual(restored,original)
        self.assertEqual(by_vrom(self.image)[RELOC].extract(self.image),by_vrom(self.base)[RELOC].extract(self.base))
        self.assertEqual(self.report['furniture_initial_switch']['source'],
                         json.loads(json.dumps(behaviour.initial_switch_source(self.source))))
        self.assertLessEqual(self.report['furniture_behaviours']['code']['bytes'],behaviour.LIMIT-behaviour.RAM)
        for key in ('furniture_level_audio','furniture_audio','scenery'):
            self.assertEqual(self.report['equipment_resources'][key],self.prior['equipment_resources'][key])
        for key in ('packet','code'):
            self.assertEqual(self.report['equipment_resources']['room_rigs']['scrolling'][key],
                             self.prior['equipment_resources']['room_rigs']['scrolling'][key])
        bindings=room.bind_profiles(self.source,self.image,self.report)
        self.assertEqual(len(bindings),32)
        added=self.report['automatic_furniture']['imports'];self.assertEqual([r['item_id'] for r in added],['3368'])
        row=added[0];descriptor=prepare(self.source,0x3368)[0]
        identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        expected=metadata(self.source,0x3368,descriptor,identities[0x3368])
        self.assertEqual(expected['room_placement'],binding);self.assertEqual(row['room_placement'],binding)
        self.assertEqual(row['interaction_flags'],0x1000)
        resource=next(r for r in self.report['equipment_resources']['room_rigs']['scrolling']['rows'] if r['source_item_id']=='3368')
        self.assertTrue(resource['parent_selectable']);self.assertTrue(resource['profile_installed'])
        self.assertEqual(int(row['object_vrom'],16),resource['vrom'])
        self.assertEqual(self.blob[resource['blob_offset']:resource['blob_offset']+resource['bytes']],
                         by_vrom(self.base)[BLOB].extract(self.base)[resource['blob_offset']:resource['blob_offset']+resource['bytes']])
        native=profile(row,resource['vrom'],limit=0x2800000)
        self.assertEqual(struct.unpack_from('>H',native,62)[0],0x1000)
        bad=copy.deepcopy(row);bad.pop('room_placement')
        with self.assertRaisesRegex(ValueError,'native lifecycle'):profile(bad,resource['vrom'],limit=0x2800000)
        bad=copy.deepcopy(self.report);bad['furniture_initial_switch']['mask']=0
        with self.assertRaisesRegex(ValueError,'fresh-placement rule'):
            behaviour.checked_initial_switch(self.image,bad,self.blob)
        self.assertEqual(len(self.report['staged_furniture']['rows']),27)
        self.assertNotIn('3368',{r['source_item_id'] for r in self.report['staged_furniture']['deferred_resources']})
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                  (OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_optional_selection_and_exact_browser_composition(self):
        import v3_browser_composition as browser
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalogue=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalogue),141);plan=browser.rules(self.image,self.report)
            self.assertFalse(plan['web_patcher_enabled']);cases=[]
            for label,requested in (('empty',[]),('all',list(catalogue)),
                    ('start-disabled',['GAFE01-r0/item/3368']),('existing-loop',['GAFE01-r0/item/31A0'])):
                selection=composer.resolve(catalogue,requested);image,_,blob=composer.compose(self.image,self.report,catalogue,selection)
                if label=='empty':self.assertEqual(sha256(image),self.report['translation_baseline']['sha256'])
                elif label=='all':self.assertEqual(image,self.image)
                else:
                    enabled=label=='start-disabled';i=slot(0x3368)
                    self.assertEqual(struct.unpack_from('>I',blob,ROWS+i*80+4)[0],enabled)
                    # Metadata marks a complete installed record; the native
                    # readers also require the selected profile word above.
                    self.assertEqual(blob[ITEMS+i*32:ITEMS+(i+1)*32],self.blob[ITEMS+i*32:ITEMS+(i+1)*32])
                    self.assertEqual(bool(blob[0x40+i//8]&(1<<(i&7))),enabled)
                cases.append(dict(name=label,requested=requested,selection=selection,sha256=sha256(image)))
            with tempfile.TemporaryDirectory(prefix='v3-initial-switch-composition-') as directory:
                fixture=Path(directory)/'fixture.json';fixture.write_bytes(composer.canonical(dict(plan=plan,cases=cases,
                    base=str(OUT/'animal-forest-v3-asset-loader.z64'),stable=str(composer.stable_reference(self.report)[0]))))
                result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(fixture)],
                                      check=True,capture_output=True,text=True,timeout=60)
                self.assertEqual(len(json.loads(result.stdout)['passed']),4)
            self.assertEqual(self.report['save_codec']['format_version'],3)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
