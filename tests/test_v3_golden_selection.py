"""Connected held selection and data-only catalogue expansion on the current ROM."""
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
from aflib import by_vrom,sha256,u32
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_held_catalogue import parent_readiness,refresh_selection
import v3_catalogue as catalogue
import v3_optional_composition as composition
import v3_browser_composition as browser
from v3_creature_choices import options as behaviour_options

OUT=ROOT/os.environ.get('V3_GOLDEN_SELECTION','build/v3-golden-tools-selection-03')
SHOVEL='GAFE01-r0/item/223B'


class GoldenSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        composition.use_build_lock(OUT/'build-lock.json')
        cls.image,cls.report=composition.inputs()
        cls.base,cls.prior=inputs(OUT/'base-lock.json')

    def test_complete_retained_resources_and_only_ordering_changes(self):
        image,report=self.image,self.report;base,prior=self.base,self.prior
        files,before=by_vrom(image),by_vrom(base)
        self.assertEqual(report['physical_resources'],prior['physical_resources'])
        for r in report['physical_resources']:
            self.assertEqual(image[r['physical']:r['physical']+r['bytes']],
                             base[r['physical']:r['physical']+r['bytes']],r['id'])
        e=report['equipment_resources'];old=prior['equipment_resources']
        blob=files[BLOB].extract(image);previous=before[BLOB].extract(base)
        self.assertEqual(blob[e['blob_offset']:e['blob_offset']+e['bytes']],
                         previous[old['blob_offset']:old['blob_offset']+old['bytes']])
        scene=e['scenery'];oldscene=old['scenery']
        self.assertEqual(blob[scene['blob_offset']:scene['blob_offset']+scene['bytes']],
                         previous[oldscene['blob_offset']:oldscene['blob_offset']+oldscene['bytes']])
        old_data=before[catalogue.VROM].extract(base)
        data=bytearray(files[catalogue.VROM].extract(image));held=report['catalogue']['handheld']
        self.assertEqual(len(data),len(old_data)+128)
        self.assertEqual(held['capacity'],64)
        for address in (catalogue.UMBRELLA_POINTER,catalogue.UMBRELLA_COUNT):
            at=address-catalogue.RAM;data[at:at+4]=old_data[at:at+4]
        self.assertEqual(data[:len(old_data)],old_data)
        at=held['table_address']-catalogue.RAM
        self.assertEqual(at,len(old_data))
        self.assertEqual(data[at:at+64],old_data[prior['catalogue']['handheld']['table_address']-catalogue.RAM:][:64])
        self.assertEqual(sha256(data[at:at+held['total_rows']*2]),held['table_sha256'])
        rel=bytearray(files[catalogue.RELOC].extract(image));oldrel=before[catalogue.RELOC].extract(base)
        self.assertEqual(u32(rel,0),len(data));rel[:4]=oldrel[:4]
        self.assertEqual(rel,oldrel)
        parent=bytearray(files[catalogue.PARENT].extract(image));oldparent=before[catalogue.PARENT].extract(base)
        self.assertEqual(struct.unpack_from('>4I',parent,catalogue.OWNER),
            (catalogue.VROM,catalogue.VROM+len(data),catalogue.RAM,catalogue.RAM+len(data)))
        parent[catalogue.OWNER:catalogue.OWNER+16]=oldparent[catalogue.OWNER:catalogue.OWNER+16]
        self.assertEqual(parent,oldparent)
        self.assertLessEqual(report['catalogue']['conservative_pool_required'],report['catalogue']['pool_reserved'])
        profile=bytes.fromhex(report['save_runtime']['profile_hex'])
        oldprofile=bytes.fromhex(prior['save_runtime']['profile_hex'])
        self.assertEqual(sum((a^b).bit_count() for a,b in zip(profile,oldprofile)),1)
        self.assertEqual(report['save_codec'],prior['save_codec'])

    def test_selection_requires_complete_reward_and_tree_path(self):
        ready,pending=parent_readiness(self.report['equipment_resources'])
        self.assertIn(SHOVEL,ready)
        self.assertEqual(set(pending),{f'GAFE01-r0/item/{item}' for item in ('2239','223A','223C')})
        raw=by_vrom(self.base)[BLOB].extract(self.base)
        for path in (('scenery','tree_effects','installed'),
                     ('scenery','tree_states','planting_conversion_installed'),
                     ('player_actions','reward_exchange','balloon_release_installed'),
                     ('player_actions','reward_controls','persistent_settlement_installed')):
            bad=copy.deepcopy(self.prior);value=bad['equipment_resources']
            for key in path[:-1]:value=value[key]
            value[path[-1]]=False
            with self.assertRaisesRegex(ValueError,'Incomplete golden-tool'):
                refresh_selection(self.base,bad,bytearray(raw),OUT)
        bad=copy.deepcopy(self.prior)
        bad['equipment_resources']['scenery']['families']['behaviour']['drops']=[
            r for r in bad['equipment_resources']['scenery']['families']['behaviour']['drops'] if r[0]!=0x867]
        with self.assertRaisesRegex(ValueError,'planting/growth/drop'):
            refresh_selection(self.base,bad,bytearray(raw),OUT)

    def test_independent_and_combined_browser_profiles(self):
        image,report=self.image,self.report
        catalog=composition.catalogue(image,report);plan=browser.rules(image,report)
        choices=behaviour_options(image,report);cases=[]
        self.assertEqual(len(catalog),214)
        self.assertIn(SHOVEL,catalog)
        for item in ('2239','223A','223C','251E'):
            self.assertNotIn('GAFE01-r0/item/'+item,catalog)
        profiles=[('empty',[],{}),('shovel',[SHOVEL],{}),('all',list(catalog),{}),
            ('shovel-packs',[SHOVEL],{'paper-quantities':'GameCube'}),
            ('all-trees',[SHOVEL,'GAFE01-r0/item/2807','GAFE01-r0/item/2901'],{}),
            ('carried-without-shovel',[k for k,r in catalog.items() if r['kind']=='carried'],{})]
        parent=next(r for r in report['equipment_resources']['parent_readers']['rows'] if r['id']==SHOVEL)
        for name,requested,behaviours in profiles:
            selected=composition.resolve(catalog,requested,behaviour_options=choices,behaviours=behaviours)
            result,_,blob=composition.compose(image,report,catalog,selected)
            if blob is not None:
                self.assertEqual(bool(blob[0x20+parent['profile_byte']]&parent['profile_mask']),SHOVEL in selected['enabled'])
                current=by_vrom(result)[catalogue.VROM].extract(result)
                at=report['catalogue']['handheld']['table_address']-catalogue.RAM
                count=u32(current,catalogue.UMBRELLA_COUNT-catalogue.RAM)
                self.assertEqual(count,32+sum(catalog[k]['kind']=='equipment' for k in selected['enabled']))
                values=struct.unpack_from('>'+str(count)+'H',current,at)
                row=next(r for r in report['catalogue']['handheld']['imports'] if r['parent_item_id']=='223B')
                self.assertEqual(row['catalogue_index'] in values,SHOVEL in selected['enabled'])
            else:self.assertEqual(sha256(result),composition.stable_reference(report)[1])
            cases.append(dict(name=name,requested=requested,behaviours=behaviours,
                              selection=selected,sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-golden-selection-') as temp:
            fixture=Path(temp)/'fixture.json'
            fixture.write_text(json.dumps(dict(plan=plan,cases=cases,
                base=str(OUT/'animal-forest-v3-asset-loader.z64'),stable=str(composition.stable_reference(report)[0]))))
            run=subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(fixture)],
                cwd=ROOT,capture_output=True,text=True,timeout=90)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_current_profile_save_and_missing_shovel_rejection(self):
        from tests.test_v3_carried_storage import CarriedStorageTests
        parent=next(r for r in self.report['equipment_resources']['parent_readers']['rows'] if r['id']==SHOVEL)
        CarriedStorageTests().save_transaction(True,0,rewards=True,golden=parent)


if __name__=='__main__':unittest.main()
