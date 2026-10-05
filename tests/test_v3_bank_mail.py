"""Connected savings letters and native-mail adapters with bounded host doubles."""
from pathlib import Path
import copy
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))


class InstalledSavingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import v3_optional_composition as composer
        cls.saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(ROOT/'build/v3-savings-reward-imports-03/cartridge/build-lock.json')
        cls.image,cls.report=composer.inputs()
        cls.catalog=composer.catalogue(cls.image,cls.report)

    @classmethod
    def tearDownClass(cls):
        import v3_optional_composition as composer
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.saved

    def test_one_account_feature_owns_all_four_rewards_without_item_codes(self):
        import v3_optional_composition as composer
        from v3_feature_choices import options
        features=options(self.catalog,self.report)
        feature=next(row for row in features if row['id']=='feature/savings-account')
        keys={'GAFE01-r0/item/'+item for item in ('1FAC','1FB0','3020','3294')}
        self.assertEqual(set(feature['required_imports']),keys)
        selection=composer.resolve(self.catalog,[feature['id']],scope='v3-pipeline',report=self.report)
        self.assertEqual(selection['requested'],[feature['id']])
        self.assertEqual(set(selection['enabled']),keys)
        self.assertEqual(set(selection['required']),keys)
        self.assertEqual(selection['enabled_features'],[feature['id']])
        self.assertEqual(set(selection['requested'])&set(selection['enabled']),set())
        code=next(row for row in features if row['id']=='feature/item-codes')
        self.assertFalse(set(code['required_by_imports'])&keys)
        for key in keys:
            with self.assertRaisesRegex(ValueError,'Select the feature'):
                composer.resolve(self.catalog,[key],scope='v3-pipeline',report=self.report)

    def test_on_off_profiles_use_the_owned_mode_word_and_preserve_save_format(self):
        import v3_optional_composition as composer
        from aflib import sha256
        bank=self.report['equipment_resources']['bank'];packet=bank['packet']
        at=packet['physical']+bank['account_mode']['address']-packet['ram']
        for chosen,value in ((['feature/savings-account'],b'\x01\0\0\0'),
                             (['GAFE01-r0/item/2320'],bytes(4))):
            selection=composer.resolve(self.catalog,chosen,scope='v3-pipeline',report=self.report)
            image,_,_=composer.compose(self.image,self.report,self.catalog,selection)
            self.assertEqual(image[at:at+4],value)
            self.assertEqual(len(image),len(self.image))
        self.assertEqual(self.report['save_codec']['format_version'],21)
        selection=composer.resolve(self.catalog,[],scope='v3-pipeline',report=self.report)
        image,_,_=composer.compose(self.image,self.report,self.catalog,selection)
        self.assertEqual(sha256(image),composer.stable_reference(self.report)[1])

    def test_checked_provider_rejects_changed_packets_hooks_and_letters(self):
        from v3_furniture_pipeline import Source
        from v3_bank_mail import checked
        from aflib import CODE_RAM,CODE_VROM,by_vrom
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        contract=checked(source,self.image,self.report)
        self.assertEqual(len(contract['rewards']),4)
        self.assertEqual(len(contract['parts']),12)
        bank=self.report['equipment_resources']['bank'];files=by_vrom(self.image)
        for at in (bank['packet']['physical'],
                   files[CODE_VROM].pstart+bank['mail']['hook']['address']-CODE_RAM,
                   files[0x030A0000].pstart+400):
            image=bytearray(self.image);image[at]^=1
            with self.subTest(offset=at),self.assertRaises(ValueError):
                checked(source,image,self.report)
        report=copy.deepcopy(self.report)
        report['equipment_resources']['bank']['mail']['source']['rewards'][0]['balance']+=1
        with self.assertRaisesRegex(ValueError,'provider'):
            checked(source,self.image,report)

    def test_generated_browser_plan_has_the_combined_feature_and_no_empty_pending_list(self):
        import json
        import v3_browser_composition as browser
        plan=browser.rules(self.image,self.report,scope='v3-pipeline')
        self.assertNotIn('pending_options',plan)
        group=next(row for row in plan['runtime_groups'] if row['id']=='savings-account')
        self.assertEqual(group['any_features'],['feature/savings-account'])
        self.assertFalse(group['forced_disabled'])
        self.assertEqual(group['any_imports'],[])
        program="import {validatePlan} from './experimental/imports/composer.mjs'; let text=''; for await (const chunk of process.stdin) text+=chunk; validatePlan(JSON.parse(text));"
        run=subprocess.run(['node','--experimental-global-webcrypto','--input-type=module','-e',program],
            cwd=ROOT,input=json.dumps(plan),capture_output=True,text=True,timeout=30)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_acquisition_audit_uses_the_installed_original_savings_route(self):
        from v3_acquisition_audit import audit,donor_source
        result=audit(self.image,self.report,self.catalog,donor_source())
        rows=[row for row in result['rows'] if row['route']=='savings-account reward']
        self.assertEqual(len(rows),4)
        self.assertEqual({row['status'] for row in rows},{'installed'})
        self.assertEqual({row['evidence']['required_balance'] for row in rows},
            {1000000,10000000,100000000,999999999})


class SavingsMailTests(unittest.TestCase):
    def test_sanitized_connected_source_driver_and_native_adapter(self):
        prepared=ROOT/'build/v3-post-office-category-prepared-04'
        with tempfile.TemporaryDirectory(prefix='v3-savings-mail-') as directory:
            output=Path(directory)/'mail'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I',str(ROOT/'overlays/v3'),'-I',str(prepared),
                str(ROOT/'tests/v3_bank_mail_test.c'),str(ROOT/'overlays/v3/bank_mail.c'),
                str(ROOT/'overlays/v3/bank_account.c'),str(ROOT/'runtime/mail/record.c'),
                str(prepared/'bank_source.c'),'-o',str(output)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(output)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            print(result.stdout.strip())


if __name__=='__main__':unittest.main()
