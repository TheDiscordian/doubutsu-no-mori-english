"""Normal acquisition cannot be replaced by preparation or code permission."""
import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom
from v3_acquisition_audit import audit,donor_source,deferred_content
import v3_optional_composition as composer
from v3_feature_choices import options


class AcquisitionAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(ROOT/'build/v3-normal-acquisition-installed-07/build-lock.json')
        cls.image,cls.report=composer.inputs()
        cls.catalog=composer.catalogue(cls.image,cls.report)
        cls.source=donor_source()
        cls.result=audit(cls.image,cls.report,cls.catalog,cls.source)

    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.saved

    def test_covers_every_installed_choice_without_normal_acquisition_omissions(self):
        self.assertEqual(set(self.catalog),{r['id'] for r in self.result['rows']})
        missing=[r for r in self.result['rows'] if r['status']=='missing']
        self.assertEqual(missing,[])
        self.assertTrue(self.result['complete'])

    def test_diary_preparation_without_ordinary_stock_is_not_complete(self):
        broken=copy.deepcopy(self.report)
        del broken['equipment_resources']['normal_acquisition']['diaries']
        result=audit(self.image,broken,self.catalog,self.source)
        missing=[r for r in result['rows'] if r['status']=='missing']
        self.assertEqual(len(missing),16)
        self.assertEqual({r['kind'] for r in missing},{'diary'})
        self.assertFalse(result['complete'])

    def test_admission_requires_normal_stock_not_just_code_delivery(self):
        from v3_import_scope import availability
        broken=copy.deepcopy(self.report)
        del broken['equipment_resources']['normal_acquisition']
        admitted=availability(self.catalog,broken)
        for key in ('GAFE01-r0/item/2901','GAFE01-r0/item/2003','GAFE01-r0/item/2B07'):
            self.assertFalse(admitted[key]['selectable'])
            self.assertIn('normal shop stock',admitted[key]['reason'])

    def test_changed_diary_stock_table_is_rejected(self):
        broken=copy.deepcopy(self.report)
        broken['equipment_resources']['normal_acquisition']['diaries']['table_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'diary stock table'):
            audit(self.image,broken,self.catalog,self.source)

    def test_cedar_paths_are_normal_and_do_not_require_codes(self):
        cedar=[r for r in self.result['rows'] if r['id']=='GAFE01-r0/item/2901']
        self.assertEqual(len(cedar),2)
        self.assertTrue(all(r['status']=='installed' for r in cedar))
        features=options(self.catalog,self.report)
        codes=next(r for r in features if r['id']=='feature/item-codes')
        self.assertNotIn('GAFE01-r0/item/2901',codes['required_by_imports'])
        self.assertEqual(codes['required_imports'],[])
        selection=composer.resolve(self.catalog,['feature/cedar-trees'],scope='v3-pipeline',report=self.report)
        self.assertNotIn('feature/item-codes',selection['enabled_features'])
        image,_,_=composer.compose(self.image,self.report,self.catalog,selection)
        from v3_feature_choices import item_code_patches
        for patch in item_code_patches(self.image,self.report):
            value=bytes.fromhex(patch['after'])
            self.assertEqual(image[patch['offset']:patch['offset']+len(value)],value)
        self.assertEqual(len(image),len(self.image))

    def test_missing_cedar_native_hook_is_rejected(self):
        broken=bytearray(self.image)
        core=by_vrom(self.image)[CODE_VROM]
        hook=self.report['equipment_resources']['normal_acquisition']['hooks'][0]
        broken[core.pstart+hook['address']-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'normal-acquisition native hook'):
            audit(broken,self.report,self.catalog,self.source)

    def test_missing_shop_consumer_is_rejected(self):
        broken=bytearray(self.image)
        owner=self.report['equipment_resources']['normal_acquisition']['cedars']['consumers'][0]
        start=by_vrom(self.image)[owner['vrom']].pstart
        broken[start]^=1
        with self.assertRaisesRegex(ValueError,'shop consumer'):
            audit(broken,self.report,self.catalog,self.source)

    def test_original_savings_and_island_dependencies_are_not_personal_exceptions(self):
        rows=[r for r in self.result['rows'] if r['status']=='V4-dependency']
        self.assertEqual({r['id'] for r in rows},{'GAFE01-r0/item/3294','GAFE01-r0/item/2807'})
        self.assertTrue(all(r['personal_exception'] is False for r in rows))
        self.assertEqual(next(r for r in rows if r['id'].endswith('3294'))['evidence']['required_balance'],100000000)
        cases=[dict(id='GAFE01-r0/item/'+item,name=item,kind='furniture',selectable=False,imported=True)
            for item in ('1DC8','1DE4','1FA4','1FAC','3030','3070','31AC')]
        pending=deferred_content(self.source,cases)
        self.assertTrue(all(r['status']=='V4-dependency' for r in pending))
        self.assertEqual([r['dependency'] for r in pending if r['id'].endswith('1FA4')],['lighthouse quest'])

    def test_cedar_logic_with_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-normal-acquisition-') as directory:
            binary=Path(directory)/'cedars'
            subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                str(ROOT/'tests/v3_normal_acquisition_test.c'),'-o',str(binary)],check=True,timeout=30)
            subprocess.run([str(binary)],check=True,timeout=10)


if __name__=='__main__': unittest.main()
