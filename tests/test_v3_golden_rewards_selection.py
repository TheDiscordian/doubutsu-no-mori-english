"""Connected four-tool admission and independent birthday composition."""
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
from v3_furniture_install import inputs,reuse_resource_tail
from v3_held_catalogue import parent_readiness,refresh_selection
from v3_creature_choices import options as behaviour_options
import v3_catalogue as catalogue
import v3_optional_composition as composition
import v3_browser_composition as browser

OUT=ROOT/os.environ.get('V3_GOLDEN_REWARDS_SELECTION','build/v3-golden-tools-selection-06')
TOOLS=tuple('GAFE01-r0/item/'+item for item in ('2239','223A','223B','223C'))


class GoldenRewardSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        composition.use_build_lock(OUT/'build-lock.json')
        cls.image,cls.report=composition.inputs()
        cls.base,cls.prior=inputs(OUT/'base-lock.json')

    def test_data_only_admission_retains_all_connected_code_and_resources(self):
        image,report=self.image,self.report;base,prior=self.base,self.prior
        files,before=by_vrom(image),by_vrom(base)
        self.assertEqual(report['physical_resources'],prior['physical_resources'])
        for r in report['physical_resources']:
            self.assertEqual(image[r['physical']:r['physical']+r['bytes']],
                             base[r['physical']:r['physical']+r['bytes']],r['id'])
        e,old=report['equipment_resources'],prior['equipment_resources']
        blob,previous=files[BLOB].extract(image),before[BLOB].extract(base)
        retained,reused=reuse_resource_tail(image,report,blob)
        self.assertEqual(retained,blob[:len(retained)])
        self.assertFalse(any(blob[len(retained):]))
        self.assertEqual(reused['reused_bytes'],len(blob)-len(retained))
        self.assertEqual(len(reused['external_resources']),3)
        for section in (e, e['scenery']):
            at,n=section['blob_offset'],section['bytes']
            self.assertEqual(blob[at:at+n],previous[at:at+n])
        current=bytearray(files[catalogue.VROM].extract(image));original=before[catalogue.VROM].extract(base)
        held=report['catalogue']['handheld'];previous_held=prior['catalogue']['handheld']
        self.assertEqual(len(current),len(original))
        self.assertEqual(held['table_address'],previous_held['table_address'])
        self.assertEqual((held['capacity'],held['total_rows']-previous_held['total_rows']),(64,3))
        at=held['table_address']-catalogue.RAM
        self.assertEqual(current[at:at+64],original[at:at+64])
        self.assertEqual(sha256(current[at:at+held['total_rows']*2]),held['table_sha256'])
        current[at:at+128]=original[at:at+128]
        count=catalogue.UMBRELLA_COUNT-catalogue.RAM
        current[count:count+4]=original[count:count+4]
        self.assertEqual(current,original)
        self.assertEqual(files[catalogue.VROM].pstart,before[catalogue.VROM].pstart)
        for owner in (catalogue.RELOC,catalogue.PARENT):
            self.assertEqual(files[owner].extract(image),before[owner].extract(base))
        self.assertEqual(report['catalogue']['conservative_pool_required'],prior['catalogue']['conservative_pool_required'])
        profile=bytes.fromhex(report['save_runtime']['profile_hex'])
        oldprofile=bytes.fromhex(prior['save_runtime']['profile_hex'])
        self.assertEqual(sum((a^b).bit_count() for a,b in zip(profile,oldprofile)),3)
        self.assertEqual(report['save_codec'],prior['save_codec'])
        ready,pending=parent_readiness(e)
        self.assertTrue(set(TOOLS)<=ready)
        self.assertFalse(pending)
        self.assertEqual(len(e['carried_items']['quest']['rewards']['installed_hooks']),13)

    def test_admission_rejects_missing_or_changed_actual_providers(self):
        raw=by_vrom(self.base)[BLOB].extract(self.base)
        for path in (('installed',),('text','count'),('wire_version',),('speech','native_hooks_installed')):
            bad=copy.deepcopy(self.prior)
            value=bad['equipment_resources']['carried_items']['quest']['rewards']
            for key in path[:-1]:value=value[key]
            value[path[-1]]=False
            with self.assertRaisesRegex(ValueError,'Incomplete golden-tool'):
                refresh_selection(self.base,bad,bytearray(raw),OUT)
        reward=self.prior['equipment_resources']['carried_items']['quest']['rewards']
        changed=bytearray(self.base);changed[reward['packet']['physical']+32]^=1
        with self.assertRaisesRegex(ValueError,'Changed complete golden reward'):
            refresh_selection(changed,self.prior,bytearray(raw),OUT)
        hook=reward['installed_hooks'][0];owner=by_vrom(self.base)[hook['vrom']]
        self.assertFalse(owner.pend)
        changed=bytearray(self.base);changed[owner.pstart+hook['address']-hook['ram']]^=1
        with self.assertRaisesRegex(ValueError,'Changed installed golden-tool consumer'):
            refresh_selection(changed,self.prior,bytearray(raw),OUT)

    def test_independent_tools_birthday_only_and_browser_equivalence(self):
        image,report=self.image,self.report
        catalog=composition.catalogue(image,report);plan=browser.rules(image,report)
        choices=behaviour_options(image,report)
        self.assertEqual(len(catalog),217)
        self.assertTrue(set(TOOLS)<=catalog.keys())
        self.assertNotIn('GAFE01-r0/item/251E',catalog)
        birthday=next(r for r in choices if r['id']=='birthday-presentation')
        self.assertEqual(birthday['default'],'N64')
        self.assertEqual(u32(image,birthday['offset']),0)
        cases=[]
        profiles=[('empty',[],{}),*(('tool-'+key[-4:],[key],{}) for key in TOOLS),
            ('birthday-only',[],{'birthday-presentation':'GameCube'}),
            ('birthday-tools',list(TOOLS),{'birthday-presentation':'GameCube'}),
            ('axe-packs',[TOOLS[1]],{'paper-quantities':'GameCube'}),
            ('all',list(catalog),{})]
        parents={r['id']:r for r in report['equipment_resources']['parent_readers']['rows']}
        for name,requested,behaviours in profiles:
            selected=composition.resolve(catalog,requested,behaviour_options=choices,behaviours=behaviours)
            result,_,blob=composition.compose(image,report,catalog,selected)
            if blob is None:
                self.assertEqual(sha256(result),composition.stable_reference(report)[1])
            else:
                for key in TOOLS:
                    row=parents[key]
                    self.assertEqual(bool(blob[0x20+row['profile_byte']]&row['profile_mask']),key in selected['enabled'])
                self.assertEqual(u32(result,birthday['offset']),birthday['values'][selected['behaviours'][birthday['id']]])
                current=by_vrom(result)[catalogue.VROM].extract(result)
                at=report['catalogue']['handheld']['table_address']-catalogue.RAM
                count=u32(current,catalogue.UMBRELLA_COUNT-catalogue.RAM)
                self.assertEqual(count,32+sum(catalog[k]['kind']=='equipment' for k in selected['enabled']))
                values=struct.unpack_from('>'+str(count)+'H',current,at)
                for key in TOOLS:
                    row=next(r for r in report['catalogue']['handheld']['imports'] if r['parent_item_id']==key[-4:])
                    self.assertEqual(row['catalogue_index'] in values,key in selected['enabled'])
            cases.append(dict(name=name,requested=requested,behaviours=behaviours,selection=selected,sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-golden-rewards-selection-') as temp:
            fixture=Path(temp)/'fixture.json'
            fixture.write_text(json.dumps(dict(plan=plan,cases=cases,
                base=str(OUT/'animal-forest-v3-asset-loader.z64'),stable=str(composition.stable_reference(report)[0]))))
            run=subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(fixture)],
                cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_birthday_only_export_keeps_actual_shared_packet_receipts(self):
        with tempfile.TemporaryDirectory(prefix='v3-birthday-receipts-',dir=ROOT/'build') as temp:
            output=Path(temp)/'composition'
            composition.build(output,behaviours={'birthday-presentation':'GameCube'})
            report=json.loads((output/'build.json').read_bytes())
            image=(output/'animal-forest-v3-asset-loader.z64').read_bytes()
            quest=report['equipment_resources']['carried_items']['quest']
            reward=quest['rewards'];packet=reward['packet']
            self.assertEqual(packet,quest['packet'])
            raw=image[packet['physical']:packet['physical']+packet['bytes']]
            self.assertEqual(sha256(raw),packet['sha256'])
            code=reward['code'];at=code['ram']-packet['ram']
            self.assertEqual(sha256(raw[at:at+code['bytes']]),code['sha256'])
            row=reward['birthday_choice']
            self.assertEqual(row['resolved'],'GameCube')
            self.assertEqual(u32(raw,row['ram']-packet['ram']),1)
            self.assertFalse(report['composition']['enabled'])


if __name__=='__main__':unittest.main()
