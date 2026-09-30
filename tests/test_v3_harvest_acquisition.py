"""Connected source reward admission and current browser/offline profiles.

Uses the existing composition checker; no new native scenario or gameplay claim.
"""
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
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source,ReviewRequired
from v3_harvest_acquisition import checked,furniture

BASE=ROOT/'build/v3-harvest-installed-08'
CURRENT=ROOT/os.environ.get('V3_HARVEST_CATEGORY_CURRENT','build/v3-harvest-category-imports-01/password-destinations')


class HarvestAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base,cls.prior=inputs(BASE/'build-lock.json')
        cls.image,cls.report=inputs(CURRENT/'build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.binding=checked(cls.source,cls.image,cls.report)

    def test_complete_source_admission_and_missing_owner_rejection(self):
        self.source.harvest_acquisition=self.binding
        items=self.binding['lists']['ftr_listHarvest']['items']
        self.assertEqual(len(items),10)
        for item in items:
            row=furniture(self.source,item,0,[('ftr_listHarvest','')])
            self.assertFalse(row['ordinary_stock']);self.assertFalse(row['catalogue_orderable'])
            self.assertEqual(row['stock_group'],255);self.assertEqual(row['reward_route'],0)
            self.assertEqual(row['harvest_acquisition']['dependencies'],['GAFE01-r0/item/2530'])
        self.source.harvest_acquisition=None
        with self.assertRaisesRegex(ReviewRequired,'complete native Harvest'):
            furniture(self.source,items[0],0,[('ftr_listHarvest','')])
        for part in ('hiding','registry','manager','text'):
            r=copy.deepcopy(self.report);r['equipment_resources']['harvest'][part]['installed']=False
            with self.assertRaises(ValueError):checked(self.source,self.image,r)
        r=copy.deepcopy(self.report)
        r['equipment_resources']['harvest']['object_table']['native_model_reservations'][0]['reserved_model_bytes']=10240
        with self.assertRaisesRegex(ValueError,'model capacity'):checked(self.source,self.image,r)

    def test_actual_native_model_caller_and_owned_packet_guard(self):
        h=self.report['equipment_resources']['harvest']
        row=h['object_table']['native_model_reservations'][0]
        image=bytearray(self.image);owner=by_vrom(image)[row['vrom']]
        at=owner.pstart+row['patches'][0]['address']-row['ram'];image[at+3]^=1
        with self.assertRaisesRegex(ValueError,'actual native Harvest'):checked(self.source,image,self.report)
        image=bytearray(self.image);p=h['packet'];image[p['physical']+p['bytes']-1]^=1
        with self.assertRaisesRegex(ValueError,'complete installed owner'):checked(self.source,image,self.report)

    def test_complete_family_reuses_profiles_resources_and_storage(self):
        from v3_import_storage import ITEMS,slot
        from v3_surface_stock import list_items
        h=self.report['equipment_resources']['harvest'];old=self.prior['equipment_resources']['harvest']
        self.assertTrue(h['reward_selection_installed']);self.assertEqual(len(h['reward_choices']),12)
        self.assertFalse(h['ordinary_gameplay_verified']);self.assertFalse(h['native_execution_verified'])
        self.assertEqual(self.report['save_codec']['format_version'],self.prior['save_codec']['format_version'])
        for name in ('packet','code','pool','manager','object_table','hiding','text','registry','shared_motions'):
            self.assertEqual(h[name],old[name],name)
        stock={r['item_id'] for r in self.report['shops']['imports']}
        prior={r['id']:r for r in self.prior['staged_furniture']['rows']}
        imported=[r for r in self.report['furniture']['imports'] if r.get('harvest_acquisition')]
        self.assertEqual(len(imported),10)
        blob=by_vrom(self.image)[BLOB].extract(self.image)
        for row in imported:
            previous=prior[row['id']]
            self.assertEqual(int(row['object_vrom'],16),previous['object_vrom'])
            self.assertEqual(row['object_sha256'],previous['object_sha256'])
            self.assertNotIn(row['item_id'],stock)
            self.assertFalse(row['catalogue_orderable']);self.assertFalse(row['ordinary_stock'])
            # The native catalogue reads this actual six-list availability mask.
            self.assertEqual(blob[ITEMS+slot(int(row['item_id'],16))*32+24],0)
        surface=self.report['room_surfaces'];old_surface=self.prior['room_surfaces']
        self.assertEqual(surface['banks'],old_surface['banks']);self.assertEqual(surface['rows'],old_surface['rows'])
        self.assertEqual(len(surface['stock']['harvest']),2);self.assertEqual(surface['stock']['pending'],[])
        for row in surface['stock']['harvest']:
            self.assertFalse(row['catalogue_orderable']);self.assertFalse(row['ordinary_stock'])
            self.assertEqual(row['harvest_acquisition']['destination_item'],row['item_id'])
        self.assertEqual(surface['stock']['resources'],old_surface['stock']['resources'])
        reward_items={int(r['item_id'],16) for r in surface['stock']['harvest']}
        # Native stock/availability consumers retain their eleven real groups.
        # No admitted reward is inserted into any of those actual lists.
        for resource in surface['stock']['resources']:
            at=resource['blob_offset'];data=blob[at:at+resource['bytes']]
            for pointer in struct.unpack_from('>11I',data,resource['table_offset']):
                if pointer:self.assertFalse(reward_items&set(list_items(data,pointer&0xFFFFFF)))
        for before,after in zip(self.prior['physical_resources'],self.report['physical_resources']):
            self.assertEqual(before,after)
            at,size=before['physical'],before['bytes']
            self.assertEqual(self.base[at:at+size],self.image[at:at+size])

    def test_current_browser_offline_reward_dependencies_and_live_map(self):
        import v3_optional_composition as composition
        import v3_browser_composition as browser
        from v3_creature_choices import options
        from v3_password_policy import connected_destination_map
        from v3_password_runtime import MAP
        composition.use_build_lock(CURRENT/'build-lock.json')
        catalog=composition.catalogue(self.image,self.report);self.assertEqual(len(catalog),247)
        h=self.report['equipment_resources']['harvest'];cutlery='GAFE01-r0/item/2530'
        for key in h['reward_choices']:self.assertEqual(catalog[key]['dependencies'],[cutlery])
        raw,proof=connected_destination_map(CURRENT/'build-lock.json')
        p=self.report['equipment_resources']['passwords'];blob=by_vrom(self.image)[BLOB].extract(self.image)
        self.assertEqual(raw,blob[p['blob_offset']+MAP:p['blob_offset']+MAP+len(raw)])
        self.assertEqual(proof['imports'],227)
        choices=options(self.image,self.report);plan=browser.rules(self.image,self.report)
        requests=(('empty',[]),('lamp-only',['GAFE01-r0/item/32D0']),
            ('floor-only',['GAFE01-r0/item/2642']),('wall-only',['GAFE01-r0/item/2742']),
            ('cutlery-only',[cutlery]),('family',h['reward_choices']),('all',list(catalog)))
        cases=[]
        for name,requested in requests:
            selected=composition.resolve(catalog,requested,behaviour_options=choices)
            result,_,_=composition.compose(self.image,self.report,catalog,selected)
            if name=='empty':self.assertEqual(sha256(result),composition.stable_reference(self.report)[1])
            elif name!='cutlery-only':self.assertIn(cutlery,selected['enabled'])
            if name in ('lamp-only','floor-only','wall-only'):
                self.assertEqual(selected['required'],[cutlery])
                self.assertEqual(set(selected['enabled']),set(requested)|{cutlery})
            if name=='all':self.assertEqual(result,self.image)
            if name!='empty':
                data=by_vrom(result)[BLOB].extract(result)
                for key in h['reward_choices']:
                    row=catalog[key];at=row['enable_offset']
                    self.assertEqual(struct.unpack_from('>I',data,at)[0],int(key in selected['enabled']))
            cases.append(dict(name=name,requested=requested,behaviours={},selection=selected,sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-harvest-composition-') as temp:
            fixture=Path(temp)/'fixture.json'
            write_new(fixture,json.dumps(dict(plan=plan,cases=cases,
                base=str(CURRENT/'animal-forest-v3-asset-loader.z64'),
                stable=str(composition.stable_reference(self.report)[0]))).encode())
            result=subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(fixture)],
                cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            print(result.stdout.strip())


if __name__=='__main__':unittest.main()
