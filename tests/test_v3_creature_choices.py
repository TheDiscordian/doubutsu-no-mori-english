"""Both installed fish settings use the same offline/browser composition rules."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,u32
from v3_asset_loader import BLOB
import v3_optional_composition as composer
import v3_browser_composition as browser
import v3_creature_choices as choices
OUT=ROOT/os.environ.get('V3_CREATURE_CHOICES_BUILD','build/v3-creature-world-work-01/connected-10')


class CreatureChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(OUT/'build-lock.json');cls.image,cls.report=composer.inputs()
        cls.catalogue=composer.catalogue(cls.image,cls.report)
        cls.plan=browser.rules(cls.image,cls.report);cls.options=choices.options(cls.image,cls.report)

    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.saved

    def test_shared_bindings_and_no_resource_save_or_consumer_loss(self):
        from v3_furniture_install import inputs
        from v3_furniture_pipeline import Source,rig_import_plan
        base,prior=inputs(OUT/'base-lock.json')
        e=self.report['equipment_resources'];old=prior['equipment_resources']
        world=e['creature_fish']['world']
        self.assertEqual(world['packet'],old['creature_fish']['world']['packet'])
        self.assertEqual(world['ui'],old['creature_fish']['world']['ui'])
        for key in ('creature_items','creature_field','console_images','room_goods','room_carry'):
            self.assertEqual(e[key]['packet'],old[key]['packet'])
        for v in (0x785700,0x7898C0,0x3950000,0x3960000,0x7AC420,0x7D9BA0,
                  0x1FA0000,0xCF9000,0x29E0000,0xD06000):
            self.assertEqual(by_vrom(base)[v].extract(base),by_vrom(self.image)[v].extract(self.image))
        self.assertEqual(self.report['save_codec'],prior['save_codec'])
        self.assertEqual(self.report['physical_resources'],prior['physical_resources'])
        self.assertEqual([r['id'] for r in self.options],['fish-population','coastal-fish-movement'])
        self.assertEqual(self.plan['behaviours'],self.options)
        for row in self.options:self.assertEqual(u32(self.image,row['offset']),0)
        for field in choices.checksum_fields(self.image,self.report):
            self.assertEqual(u32(self.image,field['offset']),zlib.crc32(self.image[field['start']:field['start']+field['length']]))
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        inv=dict(rows=[dict(item_id=r['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=r['source']['profile']) for r in e['creature_items']['profiles']])
        self.assertTrue(rig_import_plan(inv,prior,{},category='creature-profile-assets',source=source)['creature_fish'])
        self.assertNotIn('creature_fish',rig_import_plan(inv,self.report,{},category='creature-profile-assets',source=source))

    def test_both_modes_match_browser_and_only_change_declared_data(self):
        cases=[];stable_path,_,_=composer.stable_reference(self.report)
        with tempfile.TemporaryDirectory(prefix='af-creature-choices-') as directory:
            out=Path(directory)
            for name,requested,modes in (
                ('translation-only',[],{}),('all-default',list(self.catalogue),{}),
                ('population-only',[],{'fish-population':'GameCube'}),
                ('movement-only',[next(iter(self.catalogue))],{'coastal-fish-movement':'GameCube'}),
                ('both-modes',[next(iter(self.catalogue))],{'fish-population':'GameCube','coastal-fish-movement':'GameCube'})):
                selection=composer.resolve(self.catalogue,requested,behaviours=modes,behaviour_options=self.options)
                image,writes,blob=composer.compose(self.image,self.report,self.catalogue,selection)
                if blob is not None:
                    for row in self.options:
                        self.assertEqual(u32(image,row['offset']),row['values'][selection['behaviours'][row['id']]])
                    for field in self.plan['crc32']:
                        self.assertEqual(u32(image,field['offset']),zlib.crc32(image[field['start']:field['start']+field['length']]))
                    report=copy.deepcopy(self.report);choices.update_report(image,blob,report,selection['behaviours'])
                    p=report['equipment_resources']['creature_fish']['world']['packet']
                    self.assertEqual(sha256(blob[p['blob_offset']:p['blob_offset']+p['bytes']]),p['sha256'])
                cases.append(dict(name=name,requested=requested,behaviours=modes,selection=selection,sha256=sha256(image)))
            fixture=dict(base=str(OUT/'animal-forest-v3-asset-loader.z64'),stable=str(stable_path),plan=self.plan,cases=cases)
            (out/'fixture.json').write_text(json.dumps(fixture))
            result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(out/'fixture.json')],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(len(json.loads(result.stdout)['passed']),len(cases))

    def test_invalid_values_and_forged_receipts_reject(self):
        for invalid in ({'missing':'N64'},{'fish-population':'Unknown'},{'fish-population':1},[]):
            with self.assertRaises(ValueError):choices.resolve(self.options,invalid)
        selection=composer.resolve(self.catalogue,[],behaviour_options=self.options)
        selection['behaviours_changed']=True
        with self.assertRaisesRegex(ValueError,'resolution'):
            composer.compose(self.image,self.report,self.catalogue,selection)
        damaged=copy.deepcopy(self.report);damaged['equipment_resources']['creature_fish']['world']['behaviour_choices']['options'][0]['ram']+=4
        with self.assertRaises(ValueError):choices.options(self.image,damaged)


if __name__=='__main__':unittest.main()
