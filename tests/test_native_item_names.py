"""Original N64 item names retain meaning, capacity, and honest provenance."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import apply_ups,by_vrom,sha256,verified_rom
from build import apply_translations
from extended_items import VROM,resource
from item_aliases import confirmed_aliases
from item_candidates import item_candidates
from item_matches import load_matches,validate_candidate
from native_item_names import SOURCE,approval_key,load_names
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/native-items-pilot'
PREVIOUS = ROOT/'build/gyroid-items-pilot'


class NativeItemSchemaTests(unittest.TestCase):
    def test_malformed_or_incomplete_original_approvals_are_rejected(self):
        valid = {'id':'item_22:0000','source_sha256':'1'*64,'native_name':'あみ',
                 'translation':'net','evidence':'Synthetic source-reviewed original name'}
        variants = [{},[valid,valid],
                    *[[{**valid,key:value}] for key,value in (
                        ('id','item_10:0001'),('id','message:0000'),('id',None),
                        ('source_sha256',None),('source_sha256',[]),('source_sha256','bad'),
                        ('native_name',''),('translation',''),('translation','12345678901234567'),
                        ('translation',' net'),('translation','net '),('translation','あみ'),
                        ('translation','net\n'),('evidence',''))]]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'names.json'
            path.write_text(json.dumps([valid]))
            names = load_names(path)
            self.assertEqual(names[valid['id']]['reference_id'],'native:item_22:0000')
            self.assertEqual(names[valid['id']]['reference_sha256'],sha256(b'net'.ljust(16,b' ')))
            for rows in variants:
                path.write_text(json.dumps(rows))
                with self.assertRaises(ValueError,msg=str(rows)):
                    load_names(path)


@unittest.skipUnless(ROM.is_file() and (ROOT/'build/gamecube/names/furniture.jsonl').is_file(),
                     'Local original ROM and English reference names required')
class NativeItemRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(ROM.read_bytes())
        cls.info = module_command_info(cls.native)
        cls.banks = {b.name:b for b in banks(cls.native)}
        cls.source = {name:b.entries() for name,b in cls.banks.items()}
        cls.originals = load_names()
        cls.matches = load_matches(include_resolved=False)

    def generate(self,width):
        result = []
        for name in sorted({k.split(':')[0] for k in self.originals}):
            bank = self.banks[name]
            inv = list(map(json.loads,(ROOT/f'build/inventory/{name}.jsonl').read_text().splitlines()))
            refs = list(map(json.loads,(ROOT/f"build/gamecube/names/{'furniture' if name=='item_10' else name}.jsonl").read_text().splitlines()))
            edits = item_candidates(bank,inv,refs,self.info,capacity=width,matches=self.matches,originals=self.originals)[0]
            result.extend(edits)
        result += confirmed_aliases(self.banks,result,self.info,capacity=width)
        return [r for r in result if 'native_item_name' in r]

    def test_every_complete_name_rotation_alias_and_original_provenance(self):
        self.assertEqual(len(self.originals),22)
        self.assertFalse(self.originals.keys() & self.matches.keys())
        for width,count in ((10,31),(16,63)):
            edits = self.generate(width)
            self.assertEqual(len(edits),count)
            for edit in edits:
                original = self.originals[edit['native_item_name']]
                self.assertEqual(edit['translation'],original['translation'])
                self.assertEqual(edit['provenance']['source'],SOURCE)
                self.assertTrue(edit['provenance']['reference_id'].startswith('native:item_'))
                self.assertNotIn('item_reference_match',edit)
                self.assertLessEqual(len(encode(edit['translation'],self.info)),width)
                validate_candidate(edit,self.source,self.info,self.matches,originals=self.originals)
        wide = {r['id']:r for r in self.generate(16)}
        for key,text in (('item_10:009C','unused zabuton'),('item_10:00B0','unused chest'),
                         ('item_10:00B4','unused rack'),('item_24:00BF','I love 64 shirt'),
                         ('item_24:00CB','N cube shirt'),('item_10:0D44','Disk System'),
                         ('item_25:000C','glasses'),('item_25:001D','town map'),
                         ('item_29:0004','yellow cosmos'),('item_2B:0000','empty')):
            self.assertEqual(wide[key]['translation'],text)
        self.assertEqual(approval_key('item_24:00BF',self.originals),'item_10:0AA8')
        self.assertEqual(approval_key('item_24:00CB',self.originals),'item_10:0AD8')

    def test_metadata_removal_changed_hash_shortening_and_alias_changes_fail(self):
        for edit in self.generate(16):
            variants = []
            for removed in (False,True):
                bad = deepcopy(edit)
                if removed:
                    bad.pop('native_item_name')
                bad['translation'] = bad['translation'][:-1]
                bad['provenance']['reference_sha256'] = sha256(encode(bad['translation'],self.info).ljust(16,b' '))
                variants.append(bad)
            for key,value in (('source','user-supplied GAFE01 revision 0 disc'),
                              ('reference_id','furniture:0000'),('reference_sha256','0'*64)):
                bad = deepcopy(edit);bad['provenance'][key]=value;variants.append(bad)
            variants += [{**edit,'item_reference_match':'item_10:0000'},
                         {**edit,'native_item_name':None},{**edit,'source_sha256':'0'*64},
                         {**edit,'control_policy':'presentation'}]
            if edit['id'].startswith('item_24:'):
                bad = deepcopy(edit);bad.pop('native_item_name');bad['provenance']['converted_item_id']='2400';variants.append(bad)
            for changed in variants:
                with self.assertRaises(ValueError,msg=edit['id']):
                    validate_candidate(changed,self.source,self.info,self.matches,originals=self.originals)
        original = self.generate(16)[0]
        for changed in ({**original,'id':'message:0000'}, {**original,'id':'item_22:0023'}):
            with self.assertRaises(ValueError):
                validate_candidate(changed,self.source,self.info,self.matches,originals=self.originals)

    def test_both_builders_reject_relabelled_or_shortened_complete_names(self):
        wide = self.generate(16)
        resource(self.native,wide)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'
            short = self.generate(10)
            path.write_text(json.dumps(short))
            self.assertEqual(apply_translations(self.native,{},path)[0],31)
            for edit in (short[0],next(r for r in wide if r['id']=='item_24:00BF')):
                changed = deepcopy(edit);changed.pop('native_item_name');changed['translation']='bad'
                changed['provenance']['reference_sha256']=sha256(b'bad'.ljust(16,b' '))
                with self.assertRaisesRegex(ValueError,'complete original'):
                    resource(self.native,[changed])
                path.write_text(json.dumps([changed]))
                with self.assertRaisesRegex(ValueError,'complete original'):
                    apply_translations(self.native,{},path)


@unittest.skipUnless((BUILD/'build.json').is_file(),'Local complete native-name ROM required')
class NativeItemArtifactTests(unittest.TestCase):
    def test_counter_adds_only_actual_native_originals_and_the_scenario_is_complete(self):
        from native_item_scenario import scenario
        from translation_progress import measure
        native = verified_rom(ROM.read_bytes())
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        names = json.loads((ROOT/'build/native-items-resource/names.json').read_text())
        old = measure(native,(PREVIOUS/'animal-forest-halfwidth.z64').read_bytes(),
                      json.loads((PREVIOUS/'build.json').read_text()))
        new = measure(native,built,report)
        a,b = [{k for k,v in ledger.rows.items() if v['replacements'] or v['pending_replacements']}
               for ledger in (old,new)]
        self.assertTrue(a<=b)
        self.assertEqual(b-a,{r['id'] for r in names['edits'] if 'native_item_name' in r})
        self.assertEqual(new.summary()['total_source_characters'],old.summary()['total_source_characters'])
        actions = scenario(native,built,report['runtime_module'],names)
        self.assertEqual(actions,json.loads((ROOT/'build/native-items-scenario.json').read_text()))
        originals = load_names()
        short = [a['call']['arguments'][1] for a in actions if a.get('call',{}).get('address')=='80096740']
        self.assertEqual(len(short),31)
        loader = report['runtime_module']['symbols']['af_load_item_name']
        wide = {a['call']['arguments'][2] for a in actions if a.get('call',{}).get('address')==loader}
        for key in originals:
            base = 0x1000 if key.startswith('item_10:') else int(key[5:7],16)<<8
            self.assertIn(base+int(key.split(':')[1],16),wide)
        bad = {**names,'edits':[r for r in names['edits'] if r['id']!='item_29:0004']}
        with self.assertRaisesRegex(ValueError,'all 63'):
            scenario(native,built,report['runtime_module'],bad)

    def test_complete_installed_names_retention_resources_and_ups(self):
        native = verified_rom(ROM.read_bytes())
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        files,oldfiles = by_vrom(built),by_vrom(previous)
        self.assertEqual(files.keys(),oldfiles.keys())
        self.assertEqual({v for v in files if files[v].extract(built)!=oldfiles[v].extract(previous)},
                         {0x010F4000,VROM})
        self.assertEqual(sha256(built),report['output_sha256'])
        self.assertEqual(apply_ups(native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),built)
        names = json.loads((ROOT/'build/native-items-resource/names.json').read_text())
        self.assertEqual(files[VROM].extract(built),resource(native,names['edits']))
        expected = {r['id'] for r in names['edits'] if 'native_item_name' in r}
        self.assertEqual(len(expected),63)
        for kind,field,oldcount,newcount in (('candidates/translations.json',None,13567,13598),
                                            ('resource/names.json','edits',3500,3563)):
            a,b = [json.loads((ROOT/f'build/{prefix}-items-{kind}').read_text()) for prefix in ('gyroid','native')]
            if field:a,b=a[field],b[field]
            a,b={r['id']:r for r in a},{r['id']:r for r in b}
            self.assertEqual((len(a),len(b)),(oldcount,newcount))
            self.assertTrue(all(b.get(k)==v for k,v in a.items()))
            self.assertEqual(len(b.keys()-a.keys()),newcount-oldcount)
            self.assertTrue(b.keys()-a.keys() <= expected)


@unittest.skipUnless((ROOT/'build/smoke-native-items-01/results.json').is_file(),
                     'Local native-original item evidence required')
class NativeItemResultsTests(unittest.TestCase):
    def test_all_planned_calls_full_buffers_restoration_and_blank_saves(self):
        run = ROOT/'build/smoke-native-items-01'
        raw = (run/'results.json').read_bytes()
        self.assertEqual(sha256(raw),'c583f9dbeddf423a8bf273aac736c24cb23c8303023ef469658ce07d1b47347d')
        rows = json.loads(raw)
        info = json.loads((run/'run.json').read_text())
        plan = json.loads((ROOT/'build/native-items-scenario.json').read_text())
        self.assertEqual(len(rows),429)
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        self.assertEqual(len(calls),143)
        for actual,expected in zip(calls,[a['call'] for a in plan if 'call' in a],strict=True):
            self.assertEqual(actual['test_only_function_call'],expected['address'])
            self.assertEqual(actual['arguments'],expected['arguments'])
            self.assertTrue(actual['stack_restored'])
            if 'expect_return' in expected:
                self.assertEqual(actual['return_value'],expected['expect_return'])
        reads = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual(len(reads),135)
        for actual,expected in zip(reads,[a for a in plan if 'expect' in a],strict=True):
            self.assertEqual(actual['read'],expected['read'])
            self.assertEqual(actual['data'].lower(),expected['expect'].lower())
        self.assertEqual(info['rom_sha256'],sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(info['scenario_sha256'],sha256((ROOT/'build/native-items-scenario.json').read_bytes()))
        self.assertEqual(info['audio'],'disabled')
        self.assertEqual(info['seed_files'],[])
        for key in ('initial_screenshot','expansion_pak','allow_test_flash_write','allow_test_pak_write'):
            self.assertFalse(info[key])
        restored = max(i for i,r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000',4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[restored+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name,digest in (('test.bs1','831660324d826efedfbf13789122d18e3fd376b7e214684829df75c94ddd814f'),
                            ('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((run/name).read_bytes()),digest)


if __name__ == '__main__':
    unittest.main()
