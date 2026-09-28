"""Complete optional static variants retain their original N64 counterparts."""
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
from aflib import by_vrom,sha256,u32,CODE_RAM,CODE_VROM,apply_ups
from v3_asset_loader import BLOB
from v3_import_storage import ROWS,ITEMS,slot
import v3_furniture_pipeline as pipeline
import v3_furniture_install as install
import v3_furniture_capacity as capacity
import v3_optional_composition as composer
import v3_browser_composition as browser
import v3_creature_choices as choices
OUT=ROOT/os.environ.get('V3_VARIANTS_BUILD','build/v3-native-variants-work-01/connected-02/cartridge')


class NativeVariantsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=install.inputs(OUT/'build-lock.json')
        cls.base,cls.prior=install.inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.blob=cls.files[BLOB].extract(cls.image)
        cls.rows=cls.report['automatic_furniture']['imports']
        cls.source=pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_whole_counterpart_category_uses_complete_shared_conversion(self):
        identities=pipeline.identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        counterparts={item:identity for item,identity in identities.items() if identity[1].get('C','-')!='-'}
        self.assertEqual(set(counterparts),{0x3208,0x3270})
        self.assertEqual({r['item_id'] for r in self.rows},{f'{i:04X}' for i in counterparts})
        art=ROOT/self.report['automatic_furniture']['art_directory']
        checked,_=install.checked_assets(art,self.source,ROOT/'build/item-identity-megasheet.xlsx')
        self.assertEqual(len(checked),2)
        self.assertEqual(json.loads((art/'art.json').read_text())['batch'],
                         dict(objects=2,reused=2,compiled=0,compiler_containers=0))
        for row,asset in checked:
            variant=row['native_artwork_variant'];native=variant['native_item_id']
            self.assertNotEqual(native,row['item_id'])
            self.assertNotEqual(variant['native_geometry']['positions_sha256'],
                                variant['donor_geometry']['positions_sha256'])
            self.assertTrue(variant['original_preserved'])
            for vrom,digest in ((variant['native_program_vrom'],variant['native_program_sha256']),
                                (variant['native_model_vrom'],variant['native_model_sha256'])):
                self.assertEqual(sha256(self.files[vrom].extract(self.image)),digest)
            current=next(r for r in self.rows if r['id']==row['id'])
            at=int(current['object_vrom'],16)-BLOB
            self.assertEqual(self.blob[at:at+len(asset)],asset)
            i=slot(int(row['item_id'],16));metadata=self.blob[ITEMS+i*32:ITEMS+(i+1)*32]
            self.assertEqual(metadata[8:24],row['name'].encode().ljust(16,b' '))
            self.assertEqual(struct.unpack_from('>H',metadata,4)[0],row['price'])
            self.assertEqual(u32(self.blob,ROWS+i*80+4),1)
        self.assertEqual(install.provenance_patch(self.rows),'')
        damaged=copy.copy(self.source)
        image,files=self.source.native_variant_input
        changed=bytearray(image);changed[files[0x82D7F0].pstart]^=1
        damaged.native_variant_input=changed,files
        with self.assertRaises(ValueError):
            pipeline.native_artwork_variant(damaged,pipeline.prepare(self.source,0x3208)[0],counterparts[0x3208])

    def test_current_allocation_stock_retention_and_save_contract(self):
        self.assertEqual(capacity.checked(self.image,self.report),0x3000)
        cat=self.report['catalogue'];pool=cat['category_pool_patch']
        core=self.files[CODE_VROM].extract(self.image)
        self.assertEqual(u32(core,pool['address']-CODE_RAM),pool['after'])
        self.assertEqual(pool,self.prior['catalogue']['category_pool_patch'])
        self.assertEqual(cat['category_pool_bytes'],128)
        self.assertLessEqual(cat['conservative_pool_required'],cat['pool_reserved'])
        for corruption in ('missing','short'):
            report=copy.deepcopy(self.report)
            if corruption=='missing':report['catalogue'].pop('category_pool_patch')
            else:report['catalogue']['category_pool_bytes']-=64
            with self.assertRaisesRegex(ValueError,'category submenu allocation'):
                capacity.checked(self.image,report)
        self.assertEqual(self.report['equipment_resources'],self.prior['equipment_resources'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['clothing'],self.prior['clothing'])
        self.assertEqual(self.report['furniture_palette_fade']['code'],self.prior['furniture_palette_fade']['code'])
        self.assertEqual(self.report['furniture']['expanded_tables']['expanded_code'],
                         self.prior['furniture']['expanded_tables']['expanded_code'])
        before=by_vrom(self.base)[BLOB].extract(self.base)
        for row in self.prior['furniture']['imports']+[self.prior['speed_bag']]:
            at=int(row['object_vrom'],16)-BLOB;n=row['object_bytes'];i=slot(int(row['item_id'],16))
            self.assertEqual(self.blob[at:at+n],before[at:at+n])
            self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],before[ROWS+i*80:ROWS+(i+1)*80])
        import v3_shops as shops
        goods=self.files[shops.VROM].extract(self.image)
        for row in self.rows:
            at=u32(goods,self.report['shops']['table_offset']+row['stock_group']*4)&0xFFFFFF
            group=[]
            for pos in range(at,len(goods),2):
                item=struct.unpack_from('>H',goods,pos)[0]
                if not item:break
                group.append(item)
            self.assertIn(int(row['item_id'],16),group)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_individual_both_all_and_empty_profiles_match_the_browser(self):
        saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json')
            catalog=composer.catalogue(self.image,self.report);plan=browser.rules(self.image,self.report)
            modes=choices.options(self.image,self.report);keys=[r['id'] for r in self.rows]
            self.assertEqual(len(catalog),191)
            for row in plan['options']:
                if row['id'] in keys:self.assertTrue(row['native_artwork_variant']['original_preserved'])
            cases=[]
            for name,selected in (('empty',[]),('all',list(catalog)),('both',keys),
                                  ('first',keys[:1]),('second',keys[1:])):
                selection=composer.resolve(catalog,selected,behaviour_options=modes)
                image,_,blob=composer.compose(self.image,self.report,catalog,selection)
                if name=='empty':self.assertEqual(sha256(image),plan['stable_sha256'])
                elif name=='all':self.assertEqual(image,self.image)
                if blob is not None:
                    for key in keys:self.assertEqual(u32(blob,catalog[key]['enable_offset']),int(key in selection['enabled']))
                    for field in plan['crc32']:
                        self.assertEqual(u32(image,field['offset']),zlib.crc32(image[field['start']:field['start']+field['length']]))
                cases.append(dict(name=name,requested=selected,behaviours={},selection=selection,sha256=sha256(image)))
            with tempfile.TemporaryDirectory(prefix='af-native-variants-') as temporary:
                path=Path(temporary)/'fixture.json'
                path.write_text(json.dumps(dict(base=str(OUT/'animal-forest-v3-asset-loader.z64'),
                    stable=str(composer.stable_reference(self.report)[0]),plan=plan,cases=cases)))
                result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(path)],
                    capture_output=True,text=True,timeout=60)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                self.assertEqual(len(json.loads(result.stdout)['passed']),5)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=saved


if __name__=='__main__':unittest.main()
