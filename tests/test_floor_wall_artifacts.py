"""Actual ROM installation of complete interior names without unrelated changes."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import apply_ups,by_vrom,sha256,verified_rom
from extended_items import COUNTS,WIDTH,VROM,resource
from extended_items_test_scenario import scenario
from item_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode
from translation_progress import measure

BUILD = ROOT/'build/interior-items-pilot'
PREVIOUS = ROOT/'build/mail-glyph-letters-pilot'


@unittest.skipUnless((BUILD/'build.json').is_file() and (PREVIOUS/'build.json').is_file(),
                     'Local complete interior-name and preceding glyph ROMs required')
class FloorWallArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.info = module_command_info(cls.native)
        cls.names = json.loads((ROOT/'build/interior-items-resource/names.json').read_text())
        cls.matches = {k:v for k,v in load_matches(include_sheet=False).items() if k.startswith(('item_26:','item_27:'))}

    def test_all_previous_candidates_are_retained_and_only_ten_short_names_are_added(self):
        old = {r['id']:r for r in json.loads((ROOT/'build/native-credits-candidates/translations.json').read_text())}
        new = {r['id']:r for r in json.loads((ROOT/'build/interior-items-candidates/translations.json').read_text())}
        self.assertEqual(len(old),13383);self.assertEqual(len(new),13393)
        self.assertTrue(all(new[k]==v for k,v in old.items()))
        self.assertEqual(new.keys()-old.keys(),{
            'item_26:000D','item_26:0013','item_26:002E','item_26:0031',
            'item_27:000D','item_27:000E','item_27:0013','item_27:0015','item_27:0016','item_27:0028'})
        oldwide = {r['id']:r for r in json.loads((ROOT/'build/mapped-items-final-resource/names.json').read_text())['edits']}
        newwide = {r['id']:r for r in self.names['edits']}
        self.assertEqual(len(oldwide),2713);self.assertEqual(len(newwide),2783)
        self.assertTrue(all(newwide[k]==v for k,v in oldwide.items()))
        self.assertEqual(newwide.keys()-oldwide.keys(),self.matches.keys())

    def test_only_two_existing_dma_resources_change_and_patch_reconstructs_rom(self):
        old,new = by_vrom(self.previous),by_vrom(self.built)
        self.assertEqual(old.keys(),new.keys())
        changed = {v for v in old if old[v].extract(self.previous)!=new[v].extract(self.built)}
        self.assertEqual(changed,{0x010F4000,VROM})
        self.assertEqual(sha256(self.built),self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),self.built)

    def test_all_seventy_installed_complete_names_and_unchanged_short_destinations(self):
        files = by_vrom(self.built);data = files[VROM].extract(self.built)
        self.assertEqual(data,resource(self.native,self.names['edits']))
        source = {b.name:b for b in banks(self.native)}
        native_names = files[0x010F4000].extract(self.built)
        previous_names = by_vrom(self.previous)[0x010F4000].extract(self.previous)
        refs = {r['id']:r for bank in ('item_26','item_27') for r in
                map(json.loads,(ROOT/f'build/gamecube/names/{bank}.jsonl').read_text().splitlines())}
        self.assertEqual(len(self.matches),70)
        for key,match in self.matches.items():
            bank,index = key.split(':');index = int(index,16)
            text = encode(refs[match['reference_id']]['text'],self.info)
            group = int(bank[5:],16)-0x20
            at = 32+(sum(COUNTS[:group])+index)*WIDTH
            self.assertEqual(data[at:at+16],text.ljust(16,b' '),key)
            self.assertEqual(sha256(data[at:at+16]),match['reference_sha256'])
            at = source[bank].data_offset+index*10
            expected = text.ljust(10,b' ') if len(text)<=10 else previous_names[at:at+10]
            self.assertEqual(native_names[at:at+10],expected,key)
        ledger = measure(self.native,self.built,self.report)
        self.assertEqual(ledger.summary()['total_source_characters'],751002)
        for key in self.matches:
            self.assertTrue(any(r['route']=='extended_items' for r in ledger.rows[key]['replacements']),key)

    def test_targeted_batch_retains_boundary_guards_and_complete_reference_cases(self):
        selected = ('item_26','item_27')
        actions = scenario(self.built,self.report['runtime_module'],self.names,selected)
        filtered = {**self.names,'edits':[r for r in self.names['edits'] if r['id'].startswith(selected)]}
        self.assertEqual(actions,scenario(self.built,self.report['runtime_module'],filtered))
        tested = {a['call']['arguments'][2] for a in actions if 'call' in a and len(a['call']['arguments'])==3}
        self.assertTrue(all(int(k[5:7]+k[-2:],16) in tested for k in self.matches))
        self.assertTrue({0,0x2600,0x263F,0x2640,0x2700,0x273F,0x2740,0xFFFF}<=tested)
        for invalid in ([],['item_26','item_26'],['item_30'],['message']):
            with self.assertRaisesRegex(ValueError,'unique known'):
                scenario(self.built,self.report['runtime_module'],self.names,invalid)


if __name__=='__main__': unittest.main()
