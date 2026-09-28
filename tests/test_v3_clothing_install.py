"""Complete current clothing installation and shared optional composition."""
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
from aflib import by_vrom,sha256,u32,CODE_VROM,CODE_RAM,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs,reuse_resource_tail
from v3_import_storage import ROWS,ITEMS,slot
import v3_clothing_install as clothing
import v3_clothing_stock as stock
import v3_optional_composition as composer
import v3_browser_composition as browser
import v3_creature_choices as choices
import v3_physical_resources as physical
import v3_catalogue as catalogue
OUT=ROOT/os.environ.get('V3_CLOTHING_BUILD','build/v3-clothing-category-work-01/connected-09')


class ClothingInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(OUT/'build-lock.json');cls.image,cls.report=composer.inputs()
        cls.catalog=composer.catalogue(cls.image,cls.report);cls.plan=browser.rules(cls.image,cls.report)
        cls.modes=choices.options(cls.image,cls.report)
        cls.files=by_vrom(cls.image);cls.blob=cls.files[BLOB].extract(cls.image)

    @classmethod
    def tearDownClass(cls):composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.saved

    def test_connected_resources_stock_displays_and_persistence(self):
        base,prior=inputs(OUT/'base-lock.json');old=by_vrom(base);before=old[BLOB].extract(base)
        r=self.report['clothing'];p=r['batch']['packet'];raw=self.blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual(raw[-16:],bytes.fromhex('41464342')*4)
        self.assertEqual(len(r['imports']),8);self.assertEqual(len(self.catalog),189)
        self.assertEqual(self.report['save_codec'],prior['save_codec'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        prepared=json.loads((ROOT/r['batch']['prepared_directory']/'art.json').read_bytes())
        source={row['donor_item_id']:row for row in prepared['rows']}
        profile=bytes.fromhex(self.report['save_runtime']['profile_hex'])
        for row in r['imports']:
            at=clothing.metadata_offset(self.blob,self.report,row);record=self.blob[at:at+32]
            self.assertEqual(sha256(record),row['metadata_sha256'])
            self.assertEqual(record[12:28].decode().rstrip(),row['name'])
            self.assertEqual(struct.unpack_from('>H',record,8)[0],source[row['donor_item_id']]['price'])
            at=int(row['vrom'],16)-BLOB
            self.assertEqual(sha256(self.blob[at:at+544]),row['resource_sha256'])
            item=int(row['item_id'],16)
            self.assertTrue(profile[160+(item&255)//8]&(1<<(item&7)))
        for row in prior['clothing']['imports']:
            at=int(row['vrom'],16)-BLOB
            self.assertEqual(self.blob[at:at+544],before[at:at+544])
        for row in r['display']['imports']:
            item=int(row['item_id'],16);at=ITEMS+slot(item)*32
            self.assertEqual(struct.unpack_from('>HH',self.blob,at+28),(int(row['pocket_item_id'],16),0x17AC))
            if row['donor_item_id'] in r['batch']['added']:
                self.assertEqual(self.blob[ROWS+slot(item)*80+8:ROWS+slot(item)*80+76],before[0x6608:0x664C])
        for hook in r['batch']['hooks']:
            self.assertEqual(self.blob[hook['blob_offset']:hook['blob_offset']+8].hex(),hook['after'])
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        native_stock=by_vrom(native)[stock.VROM].extract(native)
        current_stock=self.files[stock.VROM].extract(self.image);sr=r['stock']
        self.assertEqual(sha256(current_stock),sr['output_sha256'])
        self.assertEqual(current_stock[:sr['resource_prefix_bytes']],old[stock.VROM].extract(base))
        for group,descriptor in enumerate(sr['groups']):
            pointer=descriptor['segment']&0xFFFFFF
            self.assertEqual(u32(current_stock,sr['pointer_table']+group*4),descriptor['segment'])
            rows=list(struct.unpack_from('>'+str(sum(descriptor['counts']))+'H',current_stock,pointer))
            self.assertEqual(rows,descriptor['items'])
            original=list(struct.unpack_from('>71H',native_stock,group*0x90))
            self.assertEqual([i for i in rows if i<0x3000],original)
            actual={(f'{item-0x1000:04X}',season) for season in range(5)
                for item in rows[sum(descriptor['counts'][:season]):sum(descriptor['counts'][:season+1])] if item>=0x3000}
            expected={(row['donor_item_id'],('all','spring','summer','autumn','winter').index(route['season']))
                for row in r['imports'] for route in source[row['donor_item_id']]['stock']
                if route['symbol']==('cloth_listA','cloth_listB','cloth_listC')[group]}
            self.assertEqual(actual,expected)
        code=self.files[CODE_VROM].extract(self.image)
        self.assertEqual(struct.unpack_from('>3I',code,stock.DESCRIPTOR-CODE_RAM),
            (stock.VROM,stock.VROM+len(current_stock),0x06000000+sr['pointer_table']))
        cat=self.report['catalogue'];cat_old=prior['catalogue'];data=self.files[catalogue.VROM].extract(self.image)
        self.assertEqual(cat['clothing']['total_rows'],253)
        self.assertEqual(data[cat['clothing']['table_address']-catalogue.RAM:cat['clothing']['table_address']-catalogue.RAM+496],
            old[catalogue.VROM].extract(base)[cat_old['clothing']['table_address']-catalogue.RAM:cat_old['clothing']['table_address']-catalogue.RAM+496])
        for key in ('creature_field','console_images','room_goods','room_carry'):
            q=self.report['equipment_resources'][key]['packet']
            self.assertEqual(q,prior['equipment_resources'][key]['packet'])
            self.assertEqual(self.blob[q['blob_offset']:q['blob_offset']+q['bytes']],before[q['blob_offset']:q['blob_offset']+q['bytes']])
        physical.verify(self.image,self.report['physical_resources'])
        _,tail=reuse_resource_tail(self.image,self.report,self.blob)
        self.assertGreater(tail['reused_bytes'],0)
        self.assertEqual(apply_ups(native,(OUT/'asset-loader.ups').read_bytes()),self.image)
        self.assertLessEqual(self.report['equipment_resources']['surface_bootstrap']['code']['bytes'],688)
        equipment=self.report['equipment_resources'];boot=equipment['surface_bootstrap']['code']
        start=equipment['blob_offset']+boot['symbols']['packets']-equipment['ram']
        descriptors=list(struct.iter_unpack('>5I',self.blob[start:start+12*20]))
        self.assertEqual(descriptors[-1][:3],(p['ram'],p['vrom'],p['bytes']))
        for destination,source_vrom,size,crc_at,clear in descriptors:
            self.assertTrue(0x80400000<=destination<destination+size<=0x80800000)
            if source_vrom&0x80000000:resource=self.image[source_vrom&0x7FFFFFFF:(source_vrom&0x7FFFFFFF)+size]
            else:
                owner=next(f for f in self.files.values() if f.vstart<=source_vrom<source_vrom+size<=f.vend)
                resource=owner.extract(self.image)[source_vrom-owner.vstart:source_vrom-owner.vstart+size]
            self.assertEqual(u32(self.blob,equipment['blob_offset']+crc_at-equipment['ram']),zlib.crc32(resource))
            self.assertIn(clear,(0,0x804DC000,0x804DC400))
        from v3_furniture_room import VROM as room_vrom,RAM as room_ram
        hook=self.report['furniture']['bank_pool']['hook'];room=self.files[room_vrom].extract(self.image)
        self.assertEqual(room[hook['address']-room_ram:hook['address']-room_ram+len(bytes.fromhex(hook['after']))].hex(),hook['after'])
        pool=cat['category_pool_patch']
        self.assertEqual(u32(code,pool['address']-CODE_RAM),pool['after'])
        self.assertEqual(pool['after']-pool['before'],128)
        self.assertLessEqual(cat['conservative_pool_required'],cat['pool_reserved'])

    def test_shared_readers_and_startup_under_sanitizers(self):
        rows=self.report['clothing']['imports'];groups=self.report['clothing']['stock']['groups']
        records=[];identities=[];descriptors=[]
        for row in rows:
            item=int(row['item_id'],16);index=row['resource_index'];vrom=int(row['vrom'],16)
            name='{'+','.join(map(str,row['name'].encode().ljust(16,b' ')))+'}'
            records.append('{%d,%d,%d,%d,1,0,%s,0}'%(item,index,vrom,row['price'],name))
            identities.append('{%d,%d,%d}'%(item,index,vrom))
        for row in groups:descriptors.append('{%d,{%s},{0}}'%(row['segment'],','.join(map(str,row['counts']))))
        header='const struct Clothing af_v3_batch_clothing[8]={'+','.join(records)+'};\n'
        header+='const struct ClothingIdentity af_v3_batch_identities[8]={'+','.join(identities)+'};\n'
        header+='const struct ClothingStock af_v3_batch_stock[3]={'+','.join(descriptors)+'};\n'
        header+='static const u16 fixture_lists[3][80]={'+','.join('{'+','.join(map(str,r['items']))+'}' for r in groups)+'};\n'
        with tempfile.TemporaryDirectory(prefix='af-clothing-runtime-') as temporary:
            folder=Path(temporary);(folder/'clothing_fixture.h').write_text(header)
            for name in ('v3_clothing_batch_test','v3_creature_startup_test'):
                binary=folder/name
                result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer','-I',str(folder),
                    str(ROOT/'tests'/f'{name}.c'),'-o',str(binary)],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertIn('pass',result.stdout)

    def test_individual_all_and_empty_browser_profiles(self):
        garments=[key for key,row in self.catalog.items() if row['kind']=='clothing'];cases=[]
        for name,selected in (('empty',[]),('all',list(self.catalog)),('all-clothing',garments),
                ('summer-shirt',[composer.item_key(0x24CB)]),('donor-variant',[composer.item_key(0x24E3)])):
            selection=composer.resolve(self.catalog,selected,behaviour_options=self.modes)
            image,_,blob=composer.compose(self.image,self.report,self.catalog,selection)
            if blob is not None:
                for key in garments:
                    row=self.catalog[key];active=int(key in selection['enabled'])
                    self.assertEqual(blob[row['enable_offset']],active)
                    self.assertEqual(u32(blob,row['display_enable_offset']),active)
                for field in self.plan['crc32']:
                    self.assertEqual(u32(image,field['offset']),zlib.crc32(image[field['start']:field['start']+field['length']]))
                report=copy.deepcopy(self.report);clothing.update_report(blob,report)
                for row in report['clothing']['imports']:clothing.metadata_offset(blob,report,row)
            cases.append(dict(name=name,requested=selected,behaviours={},selection=selection,sha256=sha256(image)))
        with tempfile.TemporaryDirectory(prefix='af-clothing-composition-') as temporary:
            fixture=Path(temporary)/'fixture.json'
            fixture.write_text(json.dumps(dict(base=str(composer.BASE/'animal-forest-v3-asset-loader.z64'),
                stable=str(composer.stable_reference(self.report)[0]),plan=self.plan,cases=cases)))
            result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(fixture)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertEqual(len(json.loads(result.stdout)['passed']),len(cases))


if __name__=='__main__':unittest.main()
