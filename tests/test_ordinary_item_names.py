"""Complete ordinary item identities, capacities, and installed-ROM retention."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, verified_rom
from extended_items import COUNTS, WIDTH, VROM, resource
from item_candidates import item_candidates
from item_matches import load_matches, validate_candidate
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode
from translation_progress import measure

GROUP_COUNTS = {'20':30, '21':3, '22':6, '25':6, '28':2, '29':8,
                '2A':52, '2C':96, '2E':2, '2F':4}
BUILD = ROOT/'build/ordinary-items-pilot'
PREVIOUS = ROOT/'build/quest-reply-letters-pilot'
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


@unittest.skipUnless(ROM.is_file() and (ROOT/'build/gamecube/names/item_2A.jsonl').is_file(),
                     'Local original ROM and supplied English names required')
class OrdinaryItemNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(ROM.read_bytes())
        cls.info = module_command_info(cls.native)
        cls.banks = {b.name:b for b in banks(cls.native)}
        cls.source = {k:b.entries() for k,b in cls.banks.items()}
        cls.matches = {k:v for k,v in load_matches(include_sheet=False).items() if k[5:7] in GROUP_COUNTS}

    def test_all_209_complete_names_exact_sources_and_fifty_short_fields(self):
        self.assertEqual(len(self.matches), 209)
        short_count = 0
        for group, count in GROUP_COUNTS.items():
            bank = 'item_'+group
            rows = list(map(json.loads, (ROOT/f'build/inventory/{bank}.jsonl').read_text().splitlines()))
            refs = list(map(json.loads, (ROOT/f'build/gamecube/names/{bank}.jsonl').read_text().splitlines()))
            approved = {k:v for k,v in self.matches.items() if k.startswith(bank+':')}
            self.assertEqual(len(approved), count)
            for capacity in (10, 16):
                old = item_candidates(self.banks[bank], rows, refs, self.info, capacity=capacity)[0]
                new = item_candidates(self.banks[bank], rows, refs, self.info,
                                      capacity=capacity, matches=self.matches)[0]
                indexed = {r['id']:r for r in new}
                self.assertTrue(all(indexed[r['id']] == r for r in old))
                added = [r for r in new if r['id'] in approved]
                if capacity == 16:
                    self.assertEqual(len(added), count)
                else:
                    short_count += len(added)
                for edit in added:
                    validate_candidate(edit, self.source, self.info, self.matches)
                    changed = deepcopy(edit)
                    changed['translation'] = edit['translation'][:-1]
                    changed['provenance']['reference_sha256'] = sha256(encode(changed['translation'], self.info).ljust(16, b' '))
                    with self.assertRaisesRegex(ValueError, 'complete exact'):
                        validate_candidate(changed, self.source, self.info, self.matches)
        self.assertEqual(short_count, 50)

    def test_displaced_names_species_colours_and_glyph_exclusions(self):
        pairs = {'item_2A:0000':'K.K. Chorale', 'item_2A:0001':'K.K. March',
                 'item_28:0005':'mushroom', 'item_28:0006':'candy',
                 'item_29:0001':'white pansy bag', 'item_29:0002':'purple pansy bag',
                 'item_29:0003':'yellow pansy bag', 'item_29:0005':'pink cosmos bag',
                 'item_29:0006':'blue cosmos bag', 'item_29:0007':'red tulip bag',
                 'item_29:0008':'white tulip bag', 'item_29:0009':'yellow tulip bag'}
        for key, name in pairs.items():
            self.assertEqual(self.matches[key]['reference_sha256'], sha256(encode(name, self.info).ljust(16, b' ')))
        months = ('January', 'February', 'March', 'April', 'May', 'June', 'July',
                  'August', 'September', 'October', 'November', 'December')
        for month, name in enumerate(months, 1):
            for slot in range(8):
                match = self.matches[f'item_2C:{(month-1)*8+slot:04X}']
                self.assertEqual(match['native_name'], f'{month}がつふくびきけん')
                self.assertEqual(match['reference_sha256'], sha256(encode(name+' ticket', self.info).ljust(16, b' ')))
        for key in ('item_29:0004', 'item_2A:0031', 'item_2A:0033', 'item_25:0005',
                    'item_25:0000', 'item_25:0013', 'item_20:0003', 'item_20:0011',
                    'item_20:0012', 'item_20:0015', 'item_20:0028'):
            self.assertNotIn(key, self.matches)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Local complete ordinary-item ROM required')
class OrdinaryItemArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(ROM.read_bytes())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.names = json.loads((ROOT/'build/ordinary-items-resource/names.json').read_text())
        cls.info = module_command_info(cls.native)
        cls.matches = {k:v for k,v in load_matches(include_sheet=False).items() if k[5:7] in GROUP_COUNTS}

    def test_all_old_candidates_retained_and_only_two_resources_change(self):
        for oldpath, newpath, field, counts in (
            ('interior-items-candidates/translations.json', 'ordinary-items-candidates/translations.json', None, (13393, 13443)),
            ('interior-items-resource/names.json', 'ordinary-items-resource/names.json', 'edits', (2783, 2992))):
            old, new = [json.loads((ROOT/'build'/p).read_text()) for p in (oldpath, newpath)]
            if field:
                old, new = old[field], new[field]
            old, new = {r['id']:r for r in old}, {r['id']:r for r in new}
            self.assertEqual((len(old), len(new)), counts)
            self.assertTrue(all(new.get(k) == v for k,v in old.items()))
            self.assertTrue(new.keys()-old.keys() <= self.matches.keys())
            if field:
                self.assertEqual(new.keys()-old.keys(), self.matches.keys())
        old, new = by_vrom(self.previous), by_vrom(self.built)
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual({v for v in old if old[v].extract(self.previous) != new[v].extract(self.built)},
                         {0x010F4000, VROM})
        self.assertEqual(sha256(self.built), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), self.built)

    def test_every_complete_installed_name_and_combined_credit(self):
        files = by_vrom(self.built)
        data = files[VROM].extract(self.built)
        self.assertEqual(data, resource(self.native, self.names['edits']))
        source = {b.name:b for b in banks(self.native)}
        native_names = files[0x010F4000].extract(self.built)
        previous_names = by_vrom(self.previous)[0x010F4000].extract(self.previous)
        refs = {r['id']:r for group in GROUP_COUNTS for r in map(json.loads,
                (ROOT/f'build/gamecube/names/item_{group}.jsonl').read_text().splitlines())}
        for key, match in self.matches.items():
            bank, index = key.split(':')
            index = int(index, 16)
            text = encode(refs[match['reference_id']]['text'], self.info)
            group = int(bank[5:], 16)-0x20
            at = 32+(sum(COUNTS[:group])+index)*WIDTH
            self.assertEqual(data[at:at+16], text.ljust(16, b' '), key)
            self.assertEqual(sha256(data[at:at+16]), match['reference_sha256'])
            at = source[bank].data_offset+index*10
            expected = text.ljust(10, b' ') if len(text) <= 10 else previous_names[at:at+10]
            self.assertEqual(native_names[at:at+10], expected, key)
        old = measure(self.native, self.previous, json.loads((PREVIOUS/'build.json').read_text()))
        ledger = measure(self.native, self.built, self.report)
        self.assertEqual(ledger.summary()['total_source_characters'], 751002)
        self.assertEqual({k for k,r in ledger.rows.items() if r['replacements']} -
                         {k for k,r in old.rows.items() if r['replacements']}, self.matches.keys()-{'item_25:0008'})
        for key in self.matches:
            self.assertTrue(any(r['route'] == 'extended_items' for r in ledger.rows[key]['replacements']), key)

    def test_reproducible_native_batch_and_all_new_short_names(self):
        from ordinary_item_scenario import scenario
        actions = scenario(self.native, self.built, self.report['runtime_module'], self.names)
        self.assertEqual(actions, json.loads((ROOT/'build/ordinary-items-scenario.json').read_text()))
        self.assertEqual(sum('call' in a for a in actions), 392)
        self.assertEqual(sum('read' in a and 'expect' in a for a in actions), 384)
        short = [a['call']['arguments'][1] for a in actions if a.get('call', {}).get('address') == '80096740']
        self.assertEqual(len(short), 50)
        self.assertEqual(len(set(short)), 50)
        incomplete = deepcopy(self.names)
        incomplete['edits'] = [r for r in incomplete['edits'] if r['id'] != 'item_29:0001']
        with self.assertRaisesRegex(ValueError, '209 complete'):
            scenario(self.native, self.built, self.report['runtime_module'], incomplete)


@unittest.skipUnless((ROOT/'build/smoke-ordinary-items-01/results.json').is_file(), 'Local native ordinary-name evidence required')
class OrdinaryItemResultsTests(unittest.TestCase):
    def test_every_planned_native_call_guards_and_checkpoint_restore(self):
        run = ROOT/'build/smoke-ordinary-items-01'
        raw = (run/'results.json').read_bytes()
        self.assertEqual(sha256(raw), '4f74c131e349123ec51e97e04fbb38354ae2c302fa4c489aa78955ae44562c7f')
        rows = json.loads(raw)
        actions = json.loads((ROOT/'build/ordinary-items-scenario.json').read_text())
        info = json.loads((run/'run.json').read_text())
        self.assertEqual(len(rows), 1337)
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        self.assertEqual(sum(r.get('assertion') == 'passed' for r in rows), 385)
        calls = [r for r in rows if 'test_only_function_call' in r]
        expected = [a['call'] for a in actions if 'call' in a]
        self.assertEqual(len(calls), 392)
        for actual, planned in zip(calls, expected):
            self.assertEqual(actual['test_only_function_call'], planned['address'])
            self.assertEqual(actual['arguments'], planned['arguments'])
            self.assertTrue(actual['stack_restored'])
            if 'expect_return' in planned:
                self.assertEqual(actual['return_value'], planned['expect_return'])
        self.assertEqual(info['post_scenario_sha256'], sha256((ROOT/'build/ordinary-items-scenario.json').read_bytes()))
        self.assertEqual(info['rom_sha256'], sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(info['audio'], 'disabled')
        self.assertEqual(info['seed_files'], [])
        for key in ('initial_screenshot', 'expansion_pak', 'allow_test_flash_write', 'allow_test_pak_write'):
            self.assertFalse(info[key])
        loaded = next(i for i,r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000',4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[loaded+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name, digest in (
            ('test.bs1','bfdb6a84e7ea7a6db626c75d14a42d7686941ae1a08d9a7bca3e8aaee0dacd33'),
            ('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((run/name).read_bytes()), digest)


if __name__ == '__main__':
    unittest.main()
