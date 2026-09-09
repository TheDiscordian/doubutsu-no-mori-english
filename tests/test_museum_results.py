"""Bind completed museum native evidence to the actual cartridge and cases."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from museum_scenario import scenario

BUILD = ROOT/'build/museum-letters-pilot'
RUN = ROOT/'build/smoke-museum-01'


@unittest.skipUnless((RUN/'results.json').is_file(),'Completed local museum native evidence required')
class MuseumResultsTests(unittest.TestCase):
    def test_complete_cases_original_metadata_pending_loops_and_restored_state(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes();report = json.loads((BUILD/'build.json').read_text())
        actions = scenario(native,built,report);request = actions[3]['test_museum_letters']
        run = json.loads((RUN/'run.json').read_text());results_data = (RUN/'results.json').read_bytes()
        self.assertEqual(sha256(results_data),'e947e22d0013c41317e1695826b11e5c8a26e2d0de9c2722a8267eaa52b346ee')
        results = json.loads(results_data)
        self.assertEqual(sha256(built),run['rom_sha256'])
        self.assertEqual(run['post_scenario_sha256'],sha256((ROOT/'build/museum-scenario.json').read_bytes()))
        self.assertEqual(json.loads((ROOT/'build/museum-scenario.json').read_text()),json.loads(json.dumps(actions)))
        self.assertEqual(sha256((ROOT/'tools/museum_smoke.py').read_bytes()),'8ed848a5f3721279b9a94d7909819a9ae026658c5916ee313fc3b38d911efdf7')
        self.assertEqual(run['audio'],'disabled');self.assertFalse(run['initial_screenshot'])
        self.assertFalse(run['expansion_pak']);self.assertFalse(run['allow_test_flash_write']);self.assertFalse(run['allow_test_pak_write'])
        cases = [r for r in results if 'native_museum_case' in r]
        self.assertEqual([(r['native_museum_case'],r['gift'],r['capital']) for r in cases],
                         [(c['template'],c['gift'],c['capital']) for c in request['cases']])
        self.assertTrue(all(r['passed'] for r in cases))
        loops = [r for r in results if 'native_museum_loop' in r]
        self.assertEqual({(r['native_museum_loop'],r['fault']) for r in loops},
                         {(k,f) for k in ('intro','wrong','fossils','combined') for f in ('none','disabled','full','partial','absent')})
        self.assertTrue(all(r['passed'] for r in loops))
        fallback = [r for r in results if 'native_museum_fallback' in r]
        self.assertEqual([r['native_museum_fallback'] for r in fallback],['none','disabled','full_queue','full_home','owner'])
        self.assertTrue(all(r['passed'] for r in fallback))
        calls = [r for r in results if 'test_only_function_call' in r]
        self.assertEqual(len(calls),313);self.assertTrue(all(r['stack_restored'] for r in calls))
        self.assertEqual(len(results),1226)
        self.assertFalse(any(r.get('assertion')=='failed' or 'error' in r for r in results))
        self.assertEqual(sum(r.get('assertion')=='passed' for r in results),666)
        for label,count in (('complete delivered museum text',75),('native recipient sender gift and font retained',54),
                            ('museum creation retains native RNG',54),('museum loop preserves original fossil RNG sequence',20),
                            ('museum notice is not sent twice',4),('museum heap accounting retained',1),
                            ('live save restored',1),('resident module guard',1)):
            self.assertEqual(sum(r.get('museum_check')==label and r.get('assertion')=='passed' for r in results),count)
        summary = next(r for r in results if 'complete_museum_cases' in r)
        self.assertEqual(summary['debugger_uploaded_creator_bytes'],0)
        self.assertEqual(summary['original_comparison_bytes'],140)
        self.assertFalse(summary['normal_scheduling']);self.assertFalse(summary['hardware_verified'])
        loaded = next(i for i,r in enumerate(results) if r.get('loaded_state')=='test.bs1')
        self.assertTrue(any(r.get('read')==['8019B000',4] and r.get('assertion')=='passed' for r in results[loaded+1:]))
        self.assertEqual(sha256((RUN/'test.bs1').read_bytes()),'4bad251a18c595cdc91b4ee8c51b8579bba6c6cb0cbc3ef5f7f80d19067be323')
        self.assertTrue(results[-1]['graceful_shutdown'])
        for name,digest in (('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()),digest)
            self.assertEqual(next(r['sha256'] for r in results[-1]['save_files'] if r['file']==name),digest)


if __name__=='__main__': unittest.main()
