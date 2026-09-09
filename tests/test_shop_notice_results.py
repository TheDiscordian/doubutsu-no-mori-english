"""Bind completed shop notice execution to the ROM, sources, and saved state."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from shop_notice_scenario import scenario

BUILD = ROOT/'build/shop-notice-letters-pilot'
RUN = ROOT/'build/smoke-shop-notice-01'


@unittest.skipUnless((RUN/'results.json').is_file(),'Completed shop notice native evidence required')
class ShopNoticeResultsTests(unittest.TestCase):
    def test_full_native_delivery_fault_retries_and_checkpoint_restoration(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text());actions = scenario(native,built,report)
        request = actions[3]['test_shop_notices'];run = json.loads((RUN/'run.json').read_text())
        data = (RUN/'results.json').read_bytes()
        self.assertEqual(sha256(data),'418c194768778e285461bb5db3346dca38552fb457ec3b154f8f1f98ee7a5842')
        results = json.loads(data)
        self.assertEqual(run['rom_sha256'],sha256(built))
        scenario_data = (ROOT/'build/shop-notice-scenario.json').read_bytes()
        self.assertEqual(run['post_scenario_sha256'],sha256(scenario_data))
        self.assertEqual(json.loads(scenario_data),json.loads(json.dumps(actions)))
        self.assertEqual(sha256((ROOT/'tools/shop_notice_smoke.py').read_bytes()),
                         'f8a48e39d921c1590f117867ca62ebf10d51f3d7e4250e01e75c8bf030fb48dd')
        self.assertEqual(run['audio'],'disabled')
        for key in ('initial_screenshot','expansion_pak','allow_test_flash_write','allow_test_pak_write'):
            self.assertFalse(run[key])
        spotlight = [r for r in results if 'native_shop_spotlight' in r]
        self.assertEqual([(r['native_shop_spotlight'],r['template'],r['mode']) for r in spotlight],
                         [(i,c['template'],c['mode']) for i,c in enumerate(request['cases'])])
        reopening = [r for r in results if 'native_shop_reopening' in r]
        self.assertEqual([(r['native_shop_reopening'],r['shop'],r['template']) for r in reopening],
                         [(i,c['shop'],c['template']) for i,c in enumerate(request['reopening'])])
        faults = [r for r in results if 'native_shop_fault' in r]
        self.assertEqual({(r['native_shop_fault'],r.get('mode'),r['fault']) for r in faults},
                         {('spotlight',m,f) for m in (0,1) for f in ('disabled','capital','full','absent','working')}
                         |{('reopening',None,f) for f in ('disabled','capital','full','absent','working','not_pending','event')})
        self.assertTrue(all(r['passed'] for r in spotlight+reopening+faults))
        self.assertEqual(len(results),779)
        self.assertEqual(sum(r.get('assertion')=='passed' for r in results),376)
        self.assertFalse(any(r.get('assertion')=='failed' or 'error' in r for r in results))
        calls = [r for r in results if 'test_only_function_call' in r]
        self.assertEqual(len(calls),172);self.assertTrue(all(r['stack_restored'] for r in calls))
        for label,count in (('complete delivered shop text',64),('only spotlight receipt changes save state',32),
                            ('reopening complete homes and original notification bit',8),
                            ('reopening resource retry completes all homes',2),
                            ('reopening pending bit prevents duplicate notices',2),
                            ('shop creator heap retained',1),('resident module guard',1),('live save restored',1)):
            self.assertEqual(sum(r.get('shop_notice_check')==label and r.get('assertion')=='passed' for r in results),count)
        summary = next(r for r in results if 'complete_spotlight_cases' in r)
        self.assertEqual(summary['full_readbacks'],64);self.assertEqual(summary['debugger_uploaded_creator_bytes'],0)
        self.assertFalse(summary['normal_scheduling']);self.assertFalse(summary['hardware_verified'])
        loaded = next(i for i,r in enumerate(results) if r.get('loaded_state')=='test.bs1')
        self.assertTrue(any(r.get('read')==['8019B000',4] and r.get('assertion')=='passed' for r in results[loaded+1:]))
        self.assertEqual(sha256((RUN/'test.bs1').read_bytes()),'5f5f2f94126e786fd2c9178dd5e1b70e13a98f0ca2cae23ee8faaf3a821793fb')
        self.assertTrue(results[-1]['graceful_shutdown'])
        for name,digest in (('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()),digest)
            self.assertEqual(next(r['sha256'] for r in results[-1]['save_files'] if r['file']==name),digest)


if __name__=='__main__': unittest.main()
