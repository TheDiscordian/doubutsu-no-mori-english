"""Current combined cartridge and shared browser/offline selection consumers."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,u32,CODE_VROM,CODE_RAM
from v3_asset_loader import BLOB
from v3_furniture_install import inputs,reuse_resource_tail
import v3_optional_composition as composer
import v3_browser_composition as browser
import v3_creature_choices as choices
import v3_creature_selection as creatures
import v3_physical_resources as physical
OUT=ROOT/os.environ.get('V3_INSECT_BUILD','build/v3-creature-insects-work-01/connected-04')


class InsectInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(OUT/'build-lock.json');cls.image,cls.report=composer.inputs()
        cls.catalog=composer.catalogue(cls.image,cls.report);cls.plan=browser.rules(cls.image,cls.report)
        cls.modes=choices.options(cls.image,cls.report)

    @classmethod
    def tearDownClass(cls):composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.saved

    def test_connected_installation_and_retained_resources(self):
        from v3_furniture_pipeline import Source,rig_import_plan
        from v3_creature_items import checked
        base,prior=inputs(OUT/'base-lock.json');files=by_vrom(self.image);old=by_vrom(base)
        e=self.report['equipment_resources'];r=e['creature_insects'];p=r['packet'];blob=files[BLOB].extract(self.image)
        code=files[CODE_VROM].extract(self.image);before=old[BLOB].extract(base)
        packet=self.image[p['physical']:p['physical']+p['bytes']]
        self.assertEqual(packet,(OUT/'insect-runtime.bin').read_bytes())
        self.assertEqual(sha256(packet),p['sha256']);self.assertEqual(zlib.crc32(packet),p['crc32'])
        self.assertEqual(packet[-16:].hex(),p['guard']);self.assertFalse(any(packet[r['compiled']['bss_start']-p['ram']:-16]))
        self.assertEqual(len(self.catalog),184);self.assertEqual(self.plan['creature_profile_hex'],'ffff0100')
        self.assertEqual(len([v for v in self.catalog.values() if v['kind']=='insect']),8)
        self.assertEqual(len(self.modes),3);self.assertTrue(r['installed']);self.assertFalse(r['native_execution_tested'])
        self.assertEqual(self.report['save_codec']['format_version'],9)
        self.assertIn('cannot load new saves',self.plan['save_compatibility'])
        boot=e['surface_bootstrap']['code'];self.assertLessEqual(boot['bytes'],688)
        self.assertIn(f'-DAF_INSECT_PHYSICAL=0x{p["physical"]:X}u',boot['flags'])
        self.assertIn(f'-DAF_INSECT_BYTES=0x{p["bytes"]:X}u',boot['flags'])
        owner=files[r['population']['owner_vrom']].extract(self.image)
        for patch in r['population']['patches']:
            self.assertEqual(u32(owner,patch['address']-r['population']['owner_ram']),patch['after'])
        for patch in r['controller']:
            data,ram=(code,CODE_RAM) if patch['address']<0x80800000 else (owner,0x80A10210)
            self.assertEqual(data[patch['address']-ram:patch['address']-ram+patch['bytes']].hex(),patch['after'])
        for patch in [*r['player'],r['effects']]:
            data=files[patch['vrom']].extract(self.image)
            self.assertEqual(data[patch['offset']:patch['offset']+4].hex(),patch['after'])
        for key in ('creature_field','console_images','room_goods','room_carry'):
            q=e[key]['packet'];self.assertEqual(q,prior['equipment_resources'][key]['packet'])
            self.assertEqual(blob[q['blob_offset']:q['blob_offset']+q['bytes']],before[q['blob_offset']:q['blob_offset']+q['bytes']])
        for row in e['creature_items']['profiles']:
            at=row['object_vrom']-BLOB
            self.assertEqual(blob[at:at+row['object_bytes']],before[at:at+row['object_bytes']])
        for row in r['mosquito']['text']['resources']:
            self.assertEqual(sha256(files[row['vrom']].extract(self.image)),row['sha256'])
        for row in r['mosquito']['motions']:
            self.assertEqual(sha256(blob[row['blob_offset']:row['blob_offset']+row['bytes']]),row['sha256'])
        for row in self.report['physical_resources']:
            physical.verify(self.image,[row])
        _,tail=reuse_resource_tail(self.image,self.report,blob)
        self.assertEqual(tail['retired_resources'],[]);self.assertGreater(tail['reused_bytes'],0)
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual(checked(self.image,self.report,source),e['creature_items'])
        inventory=dict(rows=[dict(item_id=row['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=row['source']['profile'])
            for row in e['creature_items']['profiles']])
        self.assertTrue(rig_import_plan(inventory,prior,{},category='creature-profile-assets',source=source)['creature_insects'])
        self.assertNotIn('creature_insects',rig_import_plan(inventory,self.report,{},category='creature-profile-assets',source=source))
        self.assertTrue(self.report['shared_runtime_refresh']['saved_profile_changed'])

    def test_category_and_population_choices_match_browser(self):
        added=[key for key,row in self.catalog.items() if row['kind']=='insect'];cases=[]
        for name,selected,modes in (
                ('empty',[],{}),('all',list(self.catalog),{}),('insects-n64',added,{}),
                ('insects-gc',added,{'insect-population':'GameCube'}),
                ('one-insect',[added[-1]],{}),('population-only',[],{'insect-population':'GameCube'})):
            selection=composer.resolve(self.catalog,selected,behaviours=modes,behaviour_options=self.modes)
            image,_,blob=composer.compose(self.image,self.report,self.catalog,selection)
            if blob is not None:
                for key in added:
                    row=self.catalog[key];active=int(key in selection['enabled'])
                    self.assertEqual(u32(blob,row['enable_offset']),active)
                    self.assertEqual(u32(blob,row['carried_enable_offset']),active)
                for row in self.modes:self.assertEqual(u32(image,row['offset']),row['values'][selection['behaviours'][row['id']]])
                for field in self.plan['crc32']:
                    self.assertEqual(u32(image,field['offset']),zlib.crc32(image[field['start']:field['start']+field['length']]))
                report=copy.deepcopy(self.report);choices.update_report(image,blob,report,selection['behaviours'])
                creatures.update_report(blob,report,selection);physical.verify(image,report['physical_resources'])
                self.assertEqual(creatures.selected_identities(report['equipment_resources']['creature_items']),
                    set(selection['enabled'])&set(self.report['equipment_resources']['creature_items']['optional_selection']['identities']))
            cases.append(dict(name=name,requested=selected,behaviours=modes,selection=selection,sha256=sha256(image)))
        with tempfile.TemporaryDirectory(prefix='af-insect-composition-') as temporary:
            fixture=Path(temporary)/'fixture.json'
            fixture.write_text(json.dumps(dict(base=str(composer.BASE/'animal-forest-v3-asset-loader.z64'),
                stable=str(composer.stable_reference(self.report)[0]),plan=self.plan,cases=cases)))
            result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(fixture)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(len(json.loads(result.stdout)['passed']),len(cases))


if __name__=='__main__':unittest.main()
