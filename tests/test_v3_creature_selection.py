"""Focused complete-category selection and its actual reader/save connection."""
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
from aflib import by_vrom,sha256,u32,apply_ups
from v3_asset_loader import BLOB
from v3_import_storage import ROWS,slot
from v3_furniture_install import inputs
import v3_optional_composition as composer
import v3_browser_composition as browser
import v3_creature_selection as creatures
import v3_creature_choices as choices
OUT=ROOT/os.environ.get('V3_CREATURE_SELECTION_BUILD','build/v3-creature-world-work-01/connected-11')


class CreatureSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(OUT/'build-lock.json');cls.image,cls.report=composer.inputs()
        cls.catalog=composer.catalogue(cls.image,cls.report);cls.plan=browser.rules(cls.image,cls.report)
        cls.fish=[k for k,v in cls.catalog.items() if v['kind']=='fish']
        cls.behaviours=choices.options(cls.image,cls.report)

    @classmethod
    def tearDownClass(cls):composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.previous

    def test_complete_category_installation_and_preservation(self):
        from v3_furniture_pipeline import Source,rig_import_plan
        from v3_creature_items import checked,TABLE
        base,prior=inputs(OUT/'base-lock.json');files=by_vrom(self.image);blob=files[BLOB].extract(self.image)
        before=by_vrom(base)[BLOB].extract(base);e=self.report['equipment_resources'];old=prior['equipment_resources']
        self.assertEqual(len(self.catalog),176);self.assertEqual(len(self.fish),9)
        self.assertEqual(self.plan['creature_profile_hex'],'ff010000')
        self.assertEqual(self.catalog['GAFE01-r0/item/2301']['item_id'],'2328')
        r=e['creature_items'];p=r['packet'];packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        normalized=bytearray(packet)
        for i,row in enumerate(r['rows']):
            self.assertEqual(u32(packet,TABLE+16+i*28+8),int(i<9))
            if i<9:struct.pack_into('>I',normalized,TABLE+16+i*28+8,0)
        self.assertEqual(normalized,before[p['blob_offset']:p['blob_offset']+p['bytes']])
        for key in ('creature_field','console_images','room_goods','room_carry'):
            self.assertEqual(e[key]['packet'],old[key]['packet'])
        self.assertEqual(e['creature_fish']['world']['packet'],old['creature_fish']['world']['packet'])
        self.assertEqual(self.report['save_codec'],prior['save_codec'])
        self.assertEqual(self.report['physical_resources'],prior['physical_resources'])
        for row in r['profiles']:
            at=row['object_vrom']-BLOB
            self.assertEqual(blob[at:at+row['object_bytes']],before[at:at+row['object_bytes']])
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual(checked(self.image,self.report,source),r)
        inv=dict(rows=[dict(item_id=row['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=row['source']['profile']) for row in r['profiles']])
        self.assertTrue(rig_import_plan(inv,prior,{},category='creature-profile-assets',source=source)['creature_fish'])
        self.assertEqual(bool(rig_import_plan(inv,self.report,{},category='creature-profile-assets',source=source).get('creature_fish')),
            not bool(e['creature_items'].get('room_scoring')))
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_browser_offline_complete_partial_and_behaviour_profiles(self):
        cases=[]
        for name,selected,modes in (('none',[],{}),('all',list(self.catalog),{}),('fish',self.fish,{}),
                ('brook',['GAFE01-r0/item/2301'],{}),('mixed',self.fish[::2]+['GAFE01-r0/villager/00D8'],{}),
                ('gc-fish',self.fish,{'fish-population':'GameCube','coastal-fish-movement':'GameCube'})):
            selection=composer.resolve(self.catalog,selected,behaviours=modes,behaviour_options=self.behaviours)
            image,_,blob=composer.compose(self.image,self.report,self.catalog,selection)
            if blob is not None:
                for key in self.fish:
                    row=self.catalog[key];active=int(key in selection['enabled'])
                    self.assertEqual(u32(blob,row['enable_offset']),active)
                    self.assertEqual(u32(blob,row['carried_enable_offset']),active)
                for field in self.plan['crc32']:
                    self.assertEqual(u32(image,field['offset']),zlib.crc32(image[field['start']:field['start']+field['length']]))
                if self.report['equipment_resources']['creature_items'].get('room_scoring'):
                    import v3_hra as hra
                    data=by_vrom(image)[hra.NEW_VROM].extract(image);at=self.report['hra']['metadata_address']-hra.RAM
                    for row in self.report['equipment_resources']['creature_items']['room_scoring']['rows']:
                        expected=row['native_hra_hex'] if row['id'] in selection['enabled'] else 'fc000000'
                        self.assertEqual(data[at+row['runtime_index']*4:at+row['runtime_index']*4+4].hex(),expected)
                report=copy.deepcopy(self.report);creatures.update_report(blob,report,selection)
                self.assertEqual(creatures.selected_identities(report['equipment_resources']['creature_items']),set(selected)&set(self.fish))
            cases.append(dict(name=name,requested=selected,behaviours=modes,selection=selection,sha256=sha256(image)))
        with tempfile.TemporaryDirectory(prefix='af-fish-composition-') as directory:
            out=Path(directory);fixture=out/'fixture.json'
            fixture.write_text(json.dumps(dict(base=str(composer.BASE/'animal-forest-v3-asset-loader.z64'),
                stable=str(composer.stable_reference(self.report)[0]),plan=self.plan,cases=cases)))
            result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(fixture)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(len(json.loads(result.stdout)['passed']),len(cases))

    def test_actual_selected_tables_through_parent_catch_and_save_readers(self):
        r=self.report['equipment_resources']['creature_items'];p=r['packet']
        with tempfile.TemporaryDirectory(prefix='af-fish-readers-') as directory:
            out=Path(directory)
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                '-fno-omit-frame-pointer','-fno-pie','-no-pie','-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
                '-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1','-DAF_V3_SURFACE_PROFILE=1','-DAF_V3_CREATURE_PROFILE=1',
                '-Daf_creature_item_type=af_v3_creature_item_type','-Daf_creature_test_state=af_creature_collection_state',
                '-Daf_creature_save_collect=af_v3_save_collect']
            paths=('tests/v3_creature_selection_test.c','overlays/v3/creature_collection.c',
                'overlays/v3/creature_save.c','overlays/v3/save_codec.c')
            result=subprocess.run(['cc',*flags,*[str(ROOT/path) for path in paths],'-o',str(out/'check')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            for n,selected in enumerate((self.fish,['GAFE01-r0/item/2301'],self.fish[1::2])):
                selection=composer.resolve(self.catalog,selected)
                _,_,blob=composer.compose(self.image,self.report,self.catalog,selection)
                data=blob[p['blob_offset']+r['table_offset']:p['blob_offset']+r['table_offset']+r['table_bytes']]+blob[0x20:0xE0]
                by_parent={row['parent_item_id']:row for row in r['profiles']}
                for row in r['rows']:
                    at=ROWS+slot(int(by_parent[row['item_id']]['item_id'],16))*80;data+=blob[at:at+80]
                path=out/f'profile-{n}.bin';path.write_bytes(data)
                result=subprocess.run([str(out/'check'),str(path)],capture_output=True,text=True,timeout=10)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('save-profile rejection pass',result.stdout)


if __name__=='__main__':unittest.main()
