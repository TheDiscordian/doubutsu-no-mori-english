"""Every complete gyroid identity, source, rotation, and installed resource."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, verified_rom
from extended_items import COUNTS, VROM, resource
from item_candidates import item_candidates
from item_matches import load_matches, validate_candidate
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/gyroid-items-pilot'
PREVIOUS = ROOT/'build/song-names-pilot'
GROUPS = range(364,491)
KEYS = {f'item_10:{i*4:04X}' for i in GROUPS}
SLOTS = {f'item_10:{i*4+r:04X}' for i in GROUPS for r in range(4)}


@unittest.skipUnless(ROM.is_file() and (ROOT/'build/gamecube/names/furniture.jsonl').is_file(),
                     'Local original ROM and supplied English names required')
class GyroidItemNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(ROM.read_bytes())
        cls.info = module_command_info(cls.native)
        cls.bank = next(b for b in banks(cls.native) if b.name == 'item_10')
        cls.source = {'item_10':cls.bank.entries()}
        cls.matches = {k:v for k,v in load_matches().items() if k in KEYS}
        cls.inventory = list(map(json.loads, (ROOT/'build/inventory/item_10.jsonl').read_text().splitlines()))
        cls.refs = list(map(json.loads, (ROOT/'build/gamecube/names/furniture.jsonl').read_text().splitlines()))

    def test_all_127_names_four_rotations_both_capacities_and_no_shortening(self):
        self.assertEqual(self.matches.keys(), KEYS)
        for width,count in ((10,124),(16,508)):
            old = item_candidates(self.bank,self.inventory,self.refs,self.info,capacity=width)[0]
            new = item_candidates(self.bank,self.inventory,self.refs,self.info,capacity=width,matches=self.matches)[0]
            indexed = {r['id']:r for r in new}
            self.assertTrue(all(indexed[r['id']] == r for r in old))
            selected = [r for r in new if r['id'] in SLOTS]
            self.assertEqual(len(selected), count)
            self.assertEqual(len(new)-len(old), count)
            for edit in selected:
                group = int(edit['id'].split(':')[1],16)//4
                self.assertEqual(edit['translation'], self.refs[group]['text'])
                self.assertEqual(edit['provenance']['reference_id'], self.refs[group]['id'])
                validate_candidate(edit,self.source,self.info,self.matches)
                changed = deepcopy(edit)
                changed['translation'] = edit['translation'][:-1]
                changed['provenance']['reference_sha256'] = sha256(encode(changed['translation'],self.info).ljust(16,b' '))
                with self.assertRaisesRegex(ValueError,'complete exact'):
                    validate_candidate(changed,self.source,self.info,self.matches)

    def test_bilingual_family_size_identity_and_explicit_spelling_exceptions(self):
        import collections
        import html
        import re
        path = ROOT/'build/gyroid-bilingual-reference.html'
        if not path.is_file():
            self.skipTest('Local corroborating reference snapshot required')
        raw = path.read_bytes()
        self.assertEqual(sha256(raw),'7c184bd0d2ddb6207211132100d610deb0616c3e0b754b4dcd3953892746734e')
        pairs = re.findall(r'<span class="name"[^>]*>([^<]+)</span>.*?alt="English"[^>]*>([^<]+)</span>',raw.decode(),re.S)
        names = collections.defaultdict(set)
        for jp,en in pairs:
            names[html.unescape(jp).strip()].add(html.unescape(en).strip())
        exceptions = {379,382,401,406,413,423,424,428,430,434,445,456,472,474}
        for i in GROUPS:
            match = self.matches[f'item_10:{i*4:04X}']
            en = self.refs[i]['text']
            if i in exceptions:
                url = 'https://nookipedia.com/wiki/Item:'+en[0].upper()+en[1:].replace(' ','_')+'_(Animal_Crossing)'
                self.assertIn(url,match['evidence'])
            else:
                self.assertEqual(names[match['native_name']],{en})
        for i,name in ((365,'mega gongoid'),(425,'squat dingloid'),(430,'wee dingloid'),
                       (456,'slim quazoid'),(481,'squat nebuloid'),(484,'slim nebuloid'),
                       (383,'mini gargloid'),(445,'mini warbloid')):
            self.assertEqual(self.refs[i]['text'],name)


@unittest.skipUnless((BUILD/'build.json').is_file(),'Local complete gyroid ROM required')
class GyroidItemArtifactTests(unittest.TestCase):
    def test_native_batch_covers_each_identity_and_all_short_rotations(self):
        from gyroid_item_scenario import scenario
        native = verified_rom(ROM.read_bytes())
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        module = json.loads((BUILD/'runtime-module.json').read_text())
        names = json.loads((ROOT/'build/gyroid-items-resource/names.json').read_text())
        actions = scenario(native,built,module,names)
        self.assertEqual(actions,json.loads((ROOT/'build/gyroid-items-scenario.json').read_text()))
        calls = [a['call'] for a in actions if 'call' in a]
        wide = [r['arguments'][2] for r in calls if r['address'] == module['symbols']['af_load_item_name']]
        self.assertTrue({0x1000+i*4 for i in GROUPS} <= set(wide))
        short = [r['arguments'][1] for r in calls if r['address'] == '80096740']
        selected = [r for r in names['edits'] if r['id'] in SLOTS and len(r['translation'])<=10]
        self.assertEqual(short,[0x1000+int(r['id'].split(':')[1],16) for r in selected])
        self.assertEqual(len(short),124)
        bad = {**names,'edits':[r for r in names['edits'] if r['id'] != 'item_10:05B0']}
        with self.assertRaisesRegex(ValueError,'127 identities'):
            scenario(native,built,module,bad)

    def test_counter_inventories_all_rotations_and_retains_earlier_text(self):
        from translation_progress import measure
        native = verified_rom(ROM.read_bytes())
        old = measure(native,(PREVIOUS/'animal-forest-halfwidth.z64').read_bytes(),
                      json.loads((PREVIOUS/'build.json').read_text()))
        new = measure(native,(BUILD/'animal-forest-halfwidth.z64').read_bytes(),
                      json.loads((BUILD/'build.json').read_text()))
        old_keys = {k for k,v in old.rows.items() if v['replacements'] or v['pending_replacements']}
        new_keys = {k for k,v in new.rows.items() if v['replacements'] or v['pending_replacements']}
        self.assertTrue(old_keys <= new_keys)
        self.assertEqual(new_keys-old_keys,SLOTS)
        self.assertEqual(new.summary()['total_source_characters'],old.summary()['total_source_characters'])

    def test_all_installed_names_old_candidates_nonitem_payloads_and_complete_patch(self):
        native = verified_rom(ROM.read_bytes())
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        names = json.loads((ROOT/'build/gyroid-items-resource/names.json').read_text())
        files,oldfiles = by_vrom(built),by_vrom(previous)
        self.assertEqual(files.keys(),oldfiles.keys())
        self.assertEqual({v for v in files if files[v].extract(built) != oldfiles[v].extract(previous)},
                         {0x010F4000,VROM})
        self.assertEqual(files[VROM].extract(built),resource(native,names['edits']))
        self.assertEqual(sha256(built),report['output_sha256'])
        self.assertEqual(apply_ups(native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),built)
        for oldpath,newpath,field,counts,added in (
            ('ordinary-items-candidates/translations.json','gyroid-items-candidates/translations.json',None,(13443,13567),124),
            ('ordinary-items-resource/names.json','gyroid-items-resource/names.json','edits',(2992,3500),508)):
            old,new = [json.loads((ROOT/'build'/p).read_text()) for p in (oldpath,newpath)]
            if field:
                old,new = old[field],new[field]
            old,new = {r['id']:r for r in old},{r['id']:r for r in new}
            self.assertEqual((len(old),len(new)),counts)
            self.assertTrue(all(new.get(k) == v for k,v in old.items()))
            self.assertEqual(len(new.keys()-old.keys()),added)
            self.assertTrue(new.keys()-old.keys() <= SLOTS)
        source = next(b for b in banks(native) if b.name == 'item_10')
        info = module_command_info(native)
        refs = list(map(json.loads,(ROOT/'build/gamecube/names/furniture.jsonl').read_text().splitlines()))
        wide = files[VROM].extract(built)
        short = files[0x010F4000].extract(built)
        oldshort = oldfiles[0x010F4000].extract(previous)
        for i in GROUPS:
            name = encode(refs[i]['text'],info)
            for rotation in range(4):
                slot = i*4+rotation
                at = 32+(sum(COUNTS[:-1])+slot)*16
                self.assertEqual(wide[at:at+16],name.ljust(16,b' '))
                at = source.data_offset+slot*10
                self.assertEqual(short[at:at+10],name.ljust(10,b' ') if len(name)<=10 else oldshort[at:at+10])


@unittest.skipUnless((ROOT/'build/smoke-gyroid-items-01/results.json').is_file(),
                     'Local gyroid native evidence required')
class GyroidItemResultsTests(unittest.TestCase):
    def test_all_planned_calls_buffers_guards_and_checkpoint_restoration(self):
        run = ROOT/'build/smoke-gyroid-items-01'
        raw = (run/'results.json').read_bytes()
        self.assertEqual(sha256(raw),'6ab0fcd50499beae61467d43a944f7dc2a8269dc8c199fd4d451dbb9803cf347')
        rows = json.loads(raw)
        info = json.loads((run/'run.json').read_text())
        plan = json.loads((ROOT/'build/gyroid-items-scenario.json').read_text())
        self.assertEqual(len(rows),1032)
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        calls = [r for r in rows if 'test_only_function_call' in r]
        self.assertEqual(len(calls),344)
        for actual,expected in zip(calls,[a['call'] for a in plan if 'call' in a],strict=True):
            self.assertEqual(actual['test_only_function_call'],expected['address'])
            self.assertEqual(actual['arguments'],expected['arguments'])
            self.assertTrue(actual['stack_restored'])
            if 'expect_return' in expected:
                self.assertEqual(actual['return_value'],expected['expect_return'])
        reads = [r for r in rows if r.get('assertion') == 'passed']
        self.assertEqual(len(reads),336)
        for actual,expected in zip(reads,[a for a in plan if 'expect' in a],strict=True):
            self.assertEqual(actual['read'],expected['read'])
            self.assertEqual(actual['data'].lower(),expected['expect'].lower())
        self.assertEqual(info['rom_sha256'],sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(info['scenario_sha256'],sha256((ROOT/'build/gyroid-items-scenario.json').read_bytes()))
        self.assertEqual(info['audio'],'disabled')
        self.assertEqual(info['seed_files'],[])
        for key in ('initial_screenshot','expansion_pak','allow_test_flash_write','allow_test_pak_write'):
            self.assertFalse(info[key])
        restored = max(i for i,r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000',4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[restored+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name,digest in (('test.bs1','9fddaf7b8734c5f1f0616e75e238e5262d5fdf4ea7910448ff10e4d056a9bbd4'),
                            ('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((run/name).read_bytes()),digest)


if __name__ == '__main__':
    unittest.main()
