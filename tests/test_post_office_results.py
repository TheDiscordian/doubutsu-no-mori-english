"""Audit preserved postal execution, not a new run of the current cartridge."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from post_office_letters import START,END,GUARDS,verify_templates
from post_office_scenario import case
import mail_creator_catalog as creator_catalog

BUILD = ROOT/'build/post-office-letters-pilot'
RUN = ROOT/'build/smoke-post-office-01'


@unittest.skipUnless((RUN/'results.json').is_file(),'Completed local postal native evidence required')
class PostOfficeResultsTests(unittest.TestCase):
    def test_all_cases_receipts_stack_guards_state_and_silent_shutdown(self):
        native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes();report = json.loads((BUILD/'build.json').read_text())
        # This exact scenario was executed with the historical compiled creator.
        # Regenerating it through current source guards would misrepresent that
        # evidence. Bind the archived request to its approved digest and ROM;
        # current source/installation checks live in the scenario/install tests.
        scenario_data = (ROOT/'build/post-office-scenario.json').read_bytes()
        self.assertEqual(sha256(scenario_data),'03d957a108eaf69fae84d20220b18fc9eea6a42c83f955682e660a10c15fae54')
        actions = json.loads(scenario_data);request = actions[3]['test_post_office_letters']
        self.assertEqual(sha256(built),'44d3ecea7bf4688eb35afe66c918b4bf10fd5ee6be3ce577b2221d1969947ff8')
        self.assertEqual(sha256(built),report['output_sha256'])
        self.assertEqual(request['module'],report['runtime_module'])
        files = by_vrom(built)
        catalog = files[creator_catalog.vrom(creator_catalog.selected(request['module']))].extract(built)
        items = files[0x02A00000].extract(built)
        self.assertEqual(bytes.fromhex(request['catalog']),catalog)
        self.assertEqual(bytes.fromhex(request['items']),items)
        self.assertEqual(len(verify_templates(native,catalog)['parts']),15)
        expected = [case(catalog,items,n,0x11FC,c) for n in range(0x49,0x4D) for c in (0,1)]
        expected += [case(catalog,items,0x57,0x2C00+(month-1)*8+count-1,(month+count)%2)
                     for month in range(1,13) for count in range(1,6)]
        self.assertEqual(request['cases'],expected)
        original = by_vrom(native)[CODE_VROM].extract(native)
        code = files[CODE_VROM].extract(built)
        self.assertEqual(request['original_creator'],original[START-CODE_RAM:END-CODE_RAM].hex())
        self.assertEqual(request['guards'],{f'{a:08X}':code[a-CODE_RAM:b-CODE_RAM].hex() for a,b,_ in GUARDS})
        run = json.loads((RUN/'run.json').read_text());results_data = (RUN/'results.json').read_bytes()
        self.assertEqual(sha256(results_data),'0fb0275f9c52a9abc2f61b1258e103d8b3d6ce7950f29c831123c5c608084798')
        results = json.loads(results_data)
        self.assertEqual(sha256(built),run['rom_sha256'])
        self.assertEqual(run['post_scenario_sha256'],sha256(scenario_data))
        self.assertEqual(run['audio'],'disabled');self.assertFalse(run['initial_screenshot'])
        self.assertFalse(run['expansion_pak']);self.assertFalse(run['allow_test_flash_write']);self.assertFalse(run['allow_test_pak_write'])
        cases = [r for r in results if 'native_post_office_case' in r]
        self.assertEqual([(r['native_post_office_case'],r['gift']) for r in cases],
                         [(c['template'],c['gift']) for c in request['cases']])
        self.assertTrue(all(r['passed'] for r in cases))
        loops = [r for r in results if 'native_post_office_loop' in r]
        self.assertEqual({(r['native_post_office_loop'],r['fault']) for r in loops},
                         {(k,f) for k in ('orders','tickets') for f in ('none','disabled','full','partial','absent')})
        self.assertTrue(all(r['passed'] for r in loops))
        calls = [r for r in results if 'test_only_function_call' in r]
        self.assertEqual(len(calls),364);self.assertTrue(all(r['stack_restored'] for r in calls))
        self.assertFalse(any(r.get('assertion')=='failed' or 'error' in r for r in results))
        self.assertEqual(sum(r.get('assertion')=='passed' for r in results),615)
        for label,count in (('complete delivered postal text',68),('native recipient sender gift and font retained',68),
                            ('postal heap accounting retained',1),('live save restored',1),('resident module guard',1)):
            self.assertEqual(sum(r.get('post_office_check')==label and r.get('assertion')=='passed' for r in results),count)
        loaded = next(i for i,r in enumerate(results) if r.get('loaded_state')=='test.bs1')
        self.assertTrue(any(r.get('read')==['8019B000',4] and r.get('assertion')=='passed' for r in results[loaded+1:]))
        self.assertTrue(results[-1]['graceful_shutdown'])
        for name,digest in (('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((RUN/name).read_bytes()),digest)
            self.assertEqual(next(r['sha256'] for r in results[-1]['save_files'] if r['file']==name),digest)


if __name__=='__main__': unittest.main()
