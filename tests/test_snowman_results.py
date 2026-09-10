"""Audit preserved Snowman evidence, including its incomplete first run."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from snowman_scenario import choice_for_seed
from snowman_actor import NEW_VROM,NEW_RELOCATION,METADATA,native_sources,metadata,validate
from snowman_snapshots import snapshots

BUILD = ROOT/'build/snowman-letters-pilot'
RUNS = [ROOT/'build'/name for name in ('smoke-snowman-02','smoke-snowman-03')]
DIGESTS = ('512a473559b0a4b77b7f7f7f435d1c3a7de485b51574c9e5607b345c1a4e6eb1',
           '1bfc02300595f697211e4b9ab067684591067baf146b0f7dc71de41f062628d3')


@unittest.skipUnless(all((p/'results.json').is_file() for p in RUNS),'Local complete Snowman evidence required')
class SnowmanResultsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.results = []
        for path,digest in zip(RUNS,DIGESTS):
            data = (path/'results.json').read_bytes()
            if sha256(data)!=digest: raise ValueError('Changed Snowman native results')
            cls.results.append(json.loads(data))

    def archived_scenario(self,edges=False):
        # Current source/installation approval is tested on the combined build
        # separately. Audit the exact scenario that actually produced this log.
        name = 'snowman-edges-scenario.json' if edges else 'snowman-scenario.json'
        digest = ('aefe84b62104474007932105b598a2104099cf6e7f873bae5ff97346d6c79de1' if edges else
                  'f4f2ff1a986788d5017af903f14cbd55cd6aa001462e8133932376cdf8fb9b37')
        data = (ROOT/'build'/name).read_bytes()
        self.assertEqual(sha256(data),digest)
        run = json.loads((RUNS[int(edges)]/'run.json').read_text())
        self.assertEqual(run['post_scenario_sha256'],digest)
        self.assertEqual(sha256(self.built),'dc650cea15d03bfb05b776b733f71c4914b7a2ce5cd4b258f2d4063b378ee7ee')
        self.assertEqual(sha256(self.built),self.report['output_sha256'])
        actions = json.loads(data);request = actions[3]['test_snowman_letters']
        self.assertEqual(request['module'],self.report['runtime_module'])
        self.assertEqual(request['report'],self.report['snowman_actor']['overlay'])
        files = by_vrom(self.built)
        catalog,items = (files[v].extract(self.built) for v in (0x030A0000,0x02A00000))
        _,prepared = snapshots(self.native,catalog,items)
        self.assertEqual([{k:v for k,v in c.items() if k not in ('seed','rng_end')}
                          for c in request['cases']],prepared['cases'])
        for c in request['cases']:
            self.assertEqual(choice_for_seed(c['seed']),(c['choice'],c['rng_end']))
        actor,reloc = (files[v].extract(self.built) for v in (NEW_VROM,NEW_RELOCATION))
        self.assertEqual(bytes.fromhex(request['data']),actor)
        self.assertEqual(bytes.fromhex(request['relocation']),reloc)
        validate(self.native,actor,reloc,request['report'],request['module'],catalog,items)
        self.assertEqual(tuple(bytes.fromhex(request[k]) for k in ('original','original_relocation')),
                         native_sources(self.native))
        code = files[CODE_VROM].extract(self.built)
        self.assertEqual(request['metadata'],metadata(len(actor)).hex())
        self.assertEqual(code[METADATA-CODE_RAM:METADATA-CODE_RAM+32],metadata(len(actor)))
        self.assertEqual(request['guards'],{f'{a:08X}':code[a-CODE_RAM:b-CODE_RAM].hex()
                         for a,b in ((0x8009519C,0x800951E4),(0x8009BFC0,0x8009C108),
                                     (0x8009C384,0x8009C6A0),(0x800B67C0,0x800B6AC8))})
        at = 0x1060+0x800262D0-0x80025C60
        self.assertEqual(request['loader'],self.native[at:at+0xF0].hex())
        self.assertEqual(self.built[at:at+0xF0],self.native[at:at+0xF0])
        if edges: self.assertEqual(request['group'],'edges')
        else: self.assertNotIn('group',request)
        return actions

    def test_all_bulk_cases_compare_original_metadata_rng_receipt_and_complete_reader(self):
        request = self.archived_scenario()[3]['test_snowman_letters']
        rows = self.results[0];self.assertEqual(len(rows),670)
        cases = [r for r in rows if 'native_snowman_case' in r]
        self.assertEqual([(r['native_snowman_case'],r['capital']) for r in cases],
                         [(c['choice'],c['capital']) for c in request['cases']])
        self.assertTrue(all(r['passed'] for r in cases))
        for label,count in (('original Snowman gift choice',24),('original single RNG draw',24),
                            ('complete record and native metadata',24),('original recipient sender gift font',24),
                            ('original Snowman type and paper',24),('retained single RNG draw',24),
                            ('complete English Snowman readback',48),
                            ('native owner queues only the complete selected reward',24),('owner single RNG draw',24)):
            self.assertEqual(sum(r.get('snowman_check')==label and r.get('assertion')=='passed' for r in rows),count)
        failed = [r for r in rows if r.get('assertion')=='failed']
        self.assertEqual(len(failed),1)
        self.assertEqual(failed[0]['snowman_check'],'native capacity policy and complete creation gate: foreign')
        self.assertFalse(any('complete_snowman_cases' in r or r.get('graceful_shutdown') for r in rows))
        # Do not convert this first run's fixture failure into whole-run success.

    def test_corrected_edges_restore_state_heap_checkpoint_and_blank_saves(self):
        self.archived_scenario(edges=True)
        self.assertEqual(sha256((ROOT/'tools/snowman_smoke.py').read_bytes()),
                         '399da93c9bccdf57dd2103922200639503083df0897e5b33e51a1381d2aa26b9')
        rows = self.results[1];self.assertEqual(len(rows),87)
        self.assertFalse(any(r.get('assertion')=='failed' or 'error' in r for r in rows))
        summary = next(r for r in rows if 'complete_snowman_cases' in r)
        self.assertEqual(summary['complete_snowman_cases'],0);self.assertEqual(summary['snowman_owner_cases'],5)
        self.assertEqual(summary['debugger_uploaded_creator_bytes'],0);self.assertEqual(summary['original_comparison_bytes'],16912)
        self.assertFalse(summary['normal_scheduling']);self.assertFalse(summary['hardware_verified'])
        self.assertFalse(summary['durable_full_mailbox_retry'])
        self.assertEqual([r['native_snowman_owner_case'] for r in rows if 'native_snowman_owner_case' in r],
                         ['full_home','full_queue','foreign','invalid_capital','disabled_catalog'])
        for label in ('Snowman heap accounting retained','live save restored','resident module guard',
                      'loaded actor and immutable snapshots retained','complete English Snowman readback'):
            self.assertEqual(sum(r.get('snowman_check')==label and r.get('assertion')=='passed' for r in rows),1)
        self.assertEqual(sum(r.get('snowman_check')=='Snowman fixture and stack guard' for r in rows),13)
        loaded = next(i for i,r in enumerate(rows) if r.get('loaded_state')=='test.bs1')
        self.assertTrue(any(r.get('read')==['8019B000',4] and r.get('assertion')=='passed' for r in rows[loaded+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for path,results,calls,assertions in zip(RUNS,self.results,(153,18),(324,52)):
            run = json.loads((path/'run.json').read_text())
            self.assertEqual(run['rom_sha256'],sha256(self.built));self.assertEqual(run['audio'],'disabled')
            for key in ('initial_screenshot','expansion_pak','allow_test_flash_write','allow_test_pak_write'):
                self.assertFalse(run[key])
            called = [r for r in results if 'test_only_function_call' in r]
            self.assertEqual(len(called),calls);self.assertTrue(all(r['stack_restored'] for r in called))
            self.assertEqual(sum(r.get('assertion')=='passed' for r in results),assertions)
            for name,digest in (('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                                ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
                self.assertEqual(sha256((path/name).read_bytes()),digest)
        seed = next(r for r in json.loads((RUNS[1]/'run.json').read_text())['seed_files'] if r['file']=='test.bs1')
        self.assertEqual(seed['sha256'],sha256((RUNS[0]/'test.bs1').read_bytes()))
        self.assertEqual(sha256((RUNS[1]/'test.bs1').read_bytes()),
                         '4cf5258cded8b02763e739abab42fb01a0926690373e8d477a24e44c0fa6e45f')


if __name__=='__main__': unittest.main()
