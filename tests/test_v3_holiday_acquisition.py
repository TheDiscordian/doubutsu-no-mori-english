"""Whole source gift admission, retained resources, and private composition."""
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
from aflib import by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import BLOB
from v3_furniture_install import inputs,catalogue_record,order_mask
from v3_furniture_pipeline import Source,ReviewRequired
from v3_holiday_acquisition import checked,furniture,catalogue_source

BASE=ROOT/'build/v3-harvest-category-imports-01/password-destinations'
CURRENT=ROOT/os.environ.get('V3_HOLIDAY_CATEGORY_CURRENT',
    'build/v3-holiday-gift-category-imports-03/password-destinations')


class HolidayAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base,cls.prior=inputs(BASE/'build-lock.json')
        cls.image,cls.report=inputs(CURRENT/'build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.binding=checked(cls.source,cls.image,cls.report)

    def test_complete_source_admission_ordering_and_failure_guards(self):
        self.source.holiday_acquisition=self.binding
        imports=[r for r in self.report['furniture']['imports'] if r.get('holiday_acquisition')]
        self.assertEqual(len(imports),50)
        self.assertEqual(sum(r['catalogue_orderable'] for r in imports),12)
        for row in imports:
            item=int(row.get('donor_item_id',row['item_id']),16)
            lists=[(row['donor_list'],'')] if row['catalogue_orderable'] else []
            metadata=furniture(self.source,item,row.get('donor_runtime_index',row['runtime_index']),lists)
            self.assertFalse(metadata['ordinary_stock']);self.assertEqual(metadata['stock_group'],255)
            self.assertEqual(metadata['holiday_acquisition'],row['holiday_acquisition'])
            self.assertTrue(catalogue_source(self.source,item,0,catalogue_record(row)))
            self.assertEqual(order_mask(catalogue_record(row)),8 if lists else 0)
        self.source.holiday_acquisition=None
        with self.assertRaisesRegex(ReviewRequired,'native holiday delivery'):
            furniture(self.source,0x30A8,0,[])
        for name,key in (('calendar','actor_admission_bound'),('festivals','native_services_bound')):
            report=copy.deepcopy(self.report)
            report['equipment_resources']['npc_extra']['events'][name][key]=False
            with self.assertRaisesRegex(ValueError,'complete connected'):checked(self.source,self.image,report)
        image=bytearray(self.image);p=self.report['equipment_resources']['npc_extra']['packet']
        image[p['physical']+123]^=1
        with self.assertRaisesRegex(ValueError,'complete holiday acquisition packet'):
            checked(self.source,image,self.report)

    def test_all_profiles_assets_and_physical_owners_are_reused(self):
        from v3_import_storage import ROWS,ITEMS,slot
        from v3_holiday_selection import groups
        old={r['id']:r for r in self.prior['staged_furniture']['rows']}
        imports=[r for r in self.report['furniture']['imports'] if r.get('holiday_acquisition')]
        stock={r['item_id'] for r in self.report['shops']['imports']}
        blob=by_vrom(self.image)[BLOB].extract(self.image)
        for row in imports:
            previous=old[row['id']];self.assertNotIn(row['item_id'],stock)
            self.assertEqual(int(row['object_vrom'],16),previous['object_vrom'])
            self.assertEqual(row['object_sha256'],previous['object_sha256'])
            at=slot(int(row['item_id'],16));self.assertEqual(blob[ITEMS+at*32+7],1)
            self.assertEqual(struct.unpack_from('>I',blob,ROWS+at*80+4)[0],1)
            self.assertEqual(blob[ITEMS+at*32+24],8 if row['catalogue_orderable'] else 0)
        self.assertEqual(self.report['room_surfaces'],self.prior['room_surfaces'])
        self.assertEqual(self.report['save_codec']['format_version'],20)
        self.assertEqual(self.report['physical_resources'],self.prior['physical_resources'])
        for p in self.report['physical_resources']:
            at=p['physical'];self.assertEqual(self.image[at:at+p['bytes']],self.base[at:at+p['bytes']])
        group=next(g for g in groups(self.image,self.report) if g['id']=='diary-holidays')
        self.assertTrue({r['id'] for r in imports}<=set(group['any_imports']))
        # Complete catalogue/relocation growth is covered by the actual native
        # menu allocation, without discarding another owner's allowance.
        from aflib import CODE_RAM,CODE_VROM
        before=by_vrom(self.base)[CODE_VROM].extract(self.base)
        after=by_vrom(self.image)[CODE_VROM].extract(self.image)
        at=0x800C4B10-CODE_RAM
        self.assertEqual(struct.unpack_from('>I',after,at)[0]-struct.unpack_from('>I',before,at)[0],64)
        self.assertEqual(self.report['catalogue']['category_pool_bytes']-
            self.prior['catalogue']['category_pool_bytes'],64)
        self.assertGreaterEqual(self.report['catalogue']['pool_reserved'],
            self.report['catalogue']['conservative_pool_required'])
        self.assertEqual(self.report['catalogue']['retained_submenu_pool_patches'],
            self.prior['catalogue']['retained_submenu_pool_patches'])
        from v3_furniture_capacity import checked as checked_capacity,MODEL_BYTES
        self.assertEqual(checked_capacity(self.image,self.report),MODEL_BYTES)
        invalid=copy.deepcopy(self.report)
        invalid['catalogue']['menu_category_pool_origin']+=64
        with self.assertRaises(ValueError):checked_capacity(self.image,invalid)
        invalid_image=bytearray(self.image);core=by_vrom(invalid_image)[CODE_VROM]
        invalid_image[core.pstart+at+3]^=64
        with self.assertRaises(ValueError):checked_capacity(invalid_image,self.report)
        # A subsequent ordinary category must retain the new allowance. Reuse
        # the checked identical linked suffix; no toolchain or assets rerun.
        from unittest.mock import patch
        import v3_garden_runtime as garden
        from v3_furniture_install import STABLE,STABLE_SHA
        suffix=(CURRENT.parent/'cartridge/catalogue/code.bin').read_bytes()
        linked=self.report['catalogue']['linked_code']
        self.assertEqual(sha256(suffix),linked['sha256'])
        stable=STABLE.read_bytes();self.assertEqual(sha256(stable),STABLE_SHA)
        with tempfile.TemporaryDirectory(prefix='v3-current-catalogue-',dir=ROOT/'build') as temp:
            with patch.object(garden,'compile_part',return_value=(suffix,copy.deepcopy(linked))):
                changed,rebuilt=garden.install_catalogue(self.image,stable,self.report,
                    copy.deepcopy(self.report['furniture']['imports']+[self.report['speed_bag']]),
                    Path(temp),self.source.rel,self.source.symbols.encode(),
                    reviewed_rows=copy.deepcopy(self.report['catalogue']['imports']))
        self.assertNotIn(CODE_VROM,changed)
        self.assertEqual(rebuilt['category_pool_bytes'],448)
        self.assertEqual(rebuilt['menu_category_pool_origin'],384)
        self.assertEqual(rebuilt['category_pool_patch'],self.report['catalogue']['category_pool_patch'])

    def test_independent_gifts_activate_real_providers_without_diary_imports(self):
        import v3_optional_composition as composition
        import v3_browser_composition as browser
        from v3_creature_choices import options
        from v3_holiday_selection import groups,active
        composition.use_build_lock(CURRENT/'build-lock.json')
        catalog=composition.catalogue(self.image,self.report);self.assertEqual(len(catalog),297)
        gifts=[r['id'] for r in self.report['furniture']['imports'] if r.get('holiday_acquisition')]
        choices=options(self.image,self.report);plan=browser.rules(self.image,self.report)
        requests=(('empty',[],{}),('station-only',['GAFE01-r0/item/30A8'],{}),
            ('flower-only',['GAFE01-r0/item/3378'],{}),('ship-only',['GAFE01-r0/item/1FC0'],{}),
            ('unrelated',['GAFE01-r0/item/2320'],{}),('gifts',gifts,{'holiday-calendar':'GameCube'}),
            ('all',list(catalog),{}))
        cases=[]
        for name,requested,behaviours in requests:
            selection=composition.resolve(catalog,requested,behaviour_options=choices,behaviours=behaviours)
            result,_,_=composition.compose(self.image,self.report,catalog,selection)
            if name=='empty':self.assertEqual(sha256(result),composition.stable_reference(self.report)[1])
            else:
                if name=='all':self.assertEqual(result,self.image)
                if name.endswith('-only'):
                    self.assertEqual(selection['enabled'],requested);self.assertEqual(selection['required'],[])
                group=next(g for g in groups(self.image,self.report) if g['id']=='diary-holidays')
                on=active(group,selection['enabled'],selection['behaviours'])
                self.assertEqual(on,name!='unrelated')
                for field in group['fields']:
                    self.assertEqual(struct.unpack_from('>I',result,field['offset'])[0],
                        field['enabled'] if on else field['disabled'])
            cases.append(dict(name=name,requested=requested,behaviours=behaviours,
                selection=selection,sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-holiday-gift-composition-') as temp:
            path=Path(temp)/'fixture.json'
            write_new(path,json.dumps(dict(plan=plan,cases=cases,
                base=str(CURRENT/'animal-forest-v3-asset-loader.z64'),
                stable=str(composition.stable_reference(self.report)[0]))).encode())
            run=subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(path)],
                cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())


class ExerciseAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory=ROOT/os.environ.get('V3_EXERCISE_CATEGORY_CURRENT',
            'build/v3-holiday-card-prize-imports-01/password-destinations')
        cls.base,cls.prior=inputs(ROOT/'build/v3-holiday-gift-category-imports-03/password-destinations/build-lock.json')
        cls.image,cls.report=inputs(cls.directory/'build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.binding=checked(cls.source,cls.image,cls.report)

    def test_complete_card_source_and_prize_admission(self):
        from v3_holiday_acquisition import exercise_contract
        self.source.holiday_acquisition=self.binding
        row=next(r for r in self.report['furniture']['imports'] if r['id']=='GAFE01-r0/item/1FCC')
        metadata=furniture(self.source,0x1FCC,1011,[])
        self.assertEqual(metadata['holiday_acquisition'],row['holiday_acquisition'])
        self.assertEqual(metadata['holiday_acquisition']['dependencies'],['GAFE01-r0/item/2523'])
        self.assertEqual(metadata['holiday_acquisition']['route'],'exercise-card')
        self.assertFalse(metadata['catalogue_orderable']);self.assertFalse(metadata['ordinary_stock'])
        self.assertTrue(catalogue_source(self.source,0x1FCC,1011,catalogue_record(row)))
        self.assertEqual(order_mask(catalogue_record(row)),0)
        invalid=catalogue_record(row);invalid['holiday_acquisition']=copy.deepcopy(invalid['holiday_acquisition'])
        invalid['holiday_acquisition']['dependencies']=[]
        self.assertFalse(catalogue_source(self.source,0x1FCC,1011,invalid))
        self.source.holiday_acquisition=None
        with self.assertRaisesRegex(ReviewRequired,'native holiday delivery'):
            furniture(self.source,0x1FCC,1011,[])
        source=copy.copy(self.source)
        del source.holiday_exercise_contract
        raw=bytearray(source.rel);raw[source.sections[1][0]+0x7C8BC+0x3BB]^=4;source.rel=bytes(raw)
        with self.assertRaisesRegex(ValueError,'complete summer-exercise'):exercise_contract(source)
        source=copy.copy(self.source)
        raw=bytearray(source.rel);raw[source.sections[1][0]+509384]^=1;source.rel=bytes(raw)
        with self.assertRaisesRegex(ValueError,'exercise functions differ'):checked(source,self.image,self.report)

    def test_real_profile_and_unchanged_owners(self):
        from v3_import_storage import ROWS,ITEMS,slot
        from v3_furniture_capacity import checked as checked_capacity
        from v3_holiday_selection import groups
        row=next(r for r in self.report['furniture']['imports'] if r['id']=='GAFE01-r0/item/1FCC')
        old=next(r for r in self.prior['staged_furniture']['rows'] if r['id']==row['id'])
        self.assertEqual(int(row['object_vrom'],16),old['object_vrom'])
        self.assertEqual(row['object_sha256'],old['object_sha256'])
        self.assertEqual(row['room_runtime'],old['room_runtime'])
        self.assertEqual(row['room_lifecycle'],old['room_lifecycle'])
        automatic=self.report['automatic_furniture'];art=ROOT/automatic['art_directory']/'art.json'
        self.assertEqual(sha256(art.read_bytes()),automatic['art_report_sha256'])
        self.assertEqual(json.loads(art.read_bytes())['batch'],
            dict(objects=1,compiled=0,reused=1,compiler_containers=0))
        blob=by_vrom(self.image)[BLOB].extract(self.image);at=slot(0x3C48)
        self.assertEqual(struct.unpack_from('>I',blob,ROWS+at*80+4)[0],1)
        self.assertEqual(blob[ITEMS+at*32+7],1);self.assertEqual(blob[ITEMS+at*32+24],0)
        self.assertNotIn(row['item_id'],{r['item_id'] for r in self.report['shops']['imports']})
        self.assertEqual(self.report['room_surfaces'],self.prior['room_surfaces'])
        self.assertEqual(self.report['physical_resources'],self.prior['physical_resources'])
        for p in self.report['physical_resources']:
            at=p['physical'];self.assertEqual(self.image[at:at+p['bytes']],self.base[at:at+p['bytes']])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(checked_capacity(self.image,self.report),checked_capacity(self.base,self.prior))
        group=next(g for g in groups(self.image,self.report) if g['id']=='diary-holidays')
        self.assertIn(row['id'],group['any_imports'])

    def test_radio_requires_only_card_browser_and_offline(self):
        import v3_optional_composition as composition
        import v3_browser_composition as browser
        from v3_creature_choices import options
        from v3_holiday_selection import groups,active
        composition.use_build_lock(self.directory/'build-lock.json')
        catalog=composition.catalogue(self.image,self.report);self.assertEqual(len(catalog),298)
        radio='GAFE01-r0/item/1FCC';card='GAFE01-r0/item/2523'
        self.assertEqual(catalog[radio]['dependencies'],[card])
        choices=options(self.image,self.report);plan=browser.rules(self.image,self.report)
        requests=(('empty',[],{}),('radio-only',[radio],{}),('card-only',[card],{}),
            ('radio-gc',[radio],{'holiday-calendar':'GameCube'}),
            ('unrelated',['GAFE01-r0/item/2320'],{}),('all',list(catalog),{}))
        cases=[]
        for name,requested,behaviours in requests:
            selection=composition.resolve(catalog,requested,behaviour_options=choices,behaviours=behaviours)
            result,_,_=composition.compose(self.image,self.report,catalog,selection)
            if name=='empty':self.assertEqual(sha256(result),composition.stable_reference(self.report)[1])
            else:
                if name=='all':self.assertEqual(result,self.image)
                if name.startswith('radio'):
                    self.assertEqual(set(selection['enabled']),{card,radio});self.assertEqual(selection['required'],[card])
                if name=='card-only':
                    self.assertEqual(selection['enabled'],[card]);self.assertEqual(selection['required'],[])
                group=next(g for g in groups(self.image,self.report) if g['id']=='diary-holidays')
                on=active(group,selection['enabled'],selection['behaviours'])
                self.assertEqual(on,name!='unrelated')
                for field in group['fields']:
                    self.assertEqual(struct.unpack_from('>I',result,field['offset'])[0],
                        field['enabled'] if on else field['disabled'])
            cases.append(dict(name=name,requested=requested,behaviours=behaviours,
                selection=selection,sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-exercise-prize-composition-') as temp:
            path=Path(temp)/'fixture.json'
            write_new(path,json.dumps(dict(plan=plan,cases=cases,
                base=str(self.directory/'animal-forest-v3-asset-loader.z64'),
                stable=str(composition.stable_reference(self.report)[0]))).encode())
            run=subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(path)],
                cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())


if __name__=='__main__':unittest.main()
