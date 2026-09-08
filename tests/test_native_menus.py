"""Native menu identities, complete reference presentation, and connected text."""

import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from build import apply_translations
from font import make_halfwidth
from gc_adapter import adapt_reference
from gc_text import plain
from reference_choices import adapt_choice_reference, validate_choice_candidate
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import FONT_PRESENTATION, expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

IDS = set('087C 098B 0991 0997 099D 09A3 09A9 09B5 0A0A 0A14 0AD8 0AD9 0ADA 0ADD 0ADF 0B04 0B05 0B1E 0B1F 0B20 0B4D 0B4F 0B67 0B68 0B6A 0B6C 0B6D 0B6E 0B6F 0B71 0EE8 0EE9 0EEA 0EEE 0F00 0F05 0F0B 0F0E 0F16 0F2C 0F36 0F3A 0F51 0F76 0F8E 0F8F 0F90 0F92 107B 11F2 11F4 11FB 1208 1210 1217 12FE 139F 13A8 13B0 13C7 13DE 13E1 14FA 150E 153F 169C 16BE 16C1 16E2 16E4 16E7 1767 177D 17CB 17D4 17DC 1842 186B 18AE 1B94 1B95 1BAC 1BC5 1C88 1C8C 1C91 1CA6 1D1F 1D29 1D4B 1DD7 1F71 1F89 1F97 1F98 1FFE 2049 204D 2052 2079 2099 209B 20C4 20C9 2378 23A1 23D3 23D5 2426 2427 2428 246A 246B 246E 246F 2471 2525 2582 2597 25F0 25F5 262A 262D 2636 2648 2869 286A 286C 2904 292A 2949 2975 29F4 2CB8 2CF4'.split())
DRAFTS = ROOT/'translations/n64-native-menus.json'


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM stays local')
class NativeMenuTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.sources = {b.name: b.entries() for b in banks(cls.rom)}
        cls.info = module_command_info(cls.rom)
        cls.reference_info = list(cls.info); cls.reference_info[0x74] = (2, 0)
        cls.matches = load_matches(ROOT/'translations/reference_matches.json')
        cls.drafts = json.loads(DRAFTS.read_text())
        cls.originals = {r['id'][8:]: r for r in cls.drafts if r['id'].startswith('message:')}
        cls.labels = {r['id'][7:]: r for r in cls.drafts if r['id'].startswith('select:')}

    def commands(self, data):
        return [t.data for t in tokenize(data,self.info) if t.kind=='cmd']

    def references(self):
        path = ROOT/'build/gamecube/text/message.jsonl'
        if not path.is_file(): self.skipTest('English disc extraction stays local')
        return {r['id']:r for r in map(json.loads,path.read_text().splitlines())}

    def test_all_135_full_references_keep_native_choices_actions_and_delivery(self):
        refs = self.references()
        self.assertEqual(len(IDS),135)
        article_count = 0
        for number in sorted(IDS):
            id = 'message:'+number; record = self.matches[id]; reference = refs[id]
            source = self.sources['message'][int(number,16)]
            text, changes = adapt_choice_reference(reference,source,record,self.info)
            raw = encode(reference['text'],self.reference_info); rule = record['native_choices']
            at = rule['offset']; before = bytes.fromhex(rule['reference_command'])
            after = bytes.fromhex(rule['native_command'])
            self.assertEqual(encode(text,self.reference_info),raw[:at]+after+raw[at+len(before):],id)
            self.assertEqual(len(changes),1)
            text, adaptations = adapt_reference(text,source,self.info,'reference_layout',resident_runtime=True)
            output = encode(text,self.info)
            validate_choice_candidate(id,source,output,self.matches)
            validate_entry(source,output,self.info,'message','reference_layout',resident_runtime=True)
            self.assertEqual(plain(text),plain(reference['text']),id)
            # Every reference newline and presentation command remains in order.
            presentation = FONT_PRESENTATION | {2,3,4,5,0x67,0x72,0x73,0x75}
            sequence = lambda data,info: [t.data for t in tokenize(data,info)
                if (t.kind=='cmd' and t.data[1] in presentation) or t.data==b'\xcd']
            self.assertEqual(sequence(output,self.info),sequence(raw,self.reference_info),id)
            flow = lambda data: [c for c in self.commands(data) if 0x0e<=c[1]<=0x19]
            self.assertEqual(flow(source),flow(output),id)
            article_count += sum(r['operation']=='remove_redundant_cutarticle' for r in adaptations)
            self.assertTrue({r['operation'] for r in adaptations} <= {
                'remove_redundant_cutarticle','preserve_n64_demo_arguments',
                'retain_gamecube_page_and_button_delivery','retain_gamecube_native_text_formatting'})
            self.assertLessEqual(expanded_bound(output,self.info),1024)
        self.assertGreater(article_count,0)

    def test_builder_rejects_changed_full_reference_even_without_edit_provenance(self):
        refs = self.references()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'altered.json'
            for number in ('0AD8','0B04','0B67','1B94','2052','2949'):
                id='message:'+number; record=self.matches[id]
                source=self.sources['message'][int(number,16)]
                text,_=adapt_choice_reference(refs[id],source,record,self.info)
                text,_=adapt_reference(text,source,self.info,'reference_layout',resident_runtime=True)
                edit={'id':id,'source_sha256':sha256(source),'translation':text+' ',
                      'control_policy':'reference_layout'}
                path.write_text(json.dumps([edit]))
                with self.assertRaisesRegex(ValueError,'Native-choice candidate'):
                    apply_translations(self.rom,{},path)

    def test_all_ten_native_drafts_keep_complete_controls_and_fit(self):
        self.assertEqual(set(self.originals),set('077E 152B 1783 1784 29B0 2CF3 0AE5 1212 1218 1219'.split()))
        _,font=make_halfwidth(self.rom)
        advances={int(k,16):v for k,v in font['advance_by_glyph'].items()}
        warnings={}
        for number,row in self.originals.items():
            source=self.sources['message'][int(number,16)]; output=encode(row['translation'],self.info)
            self.assertEqual(sha256(source),row['source_sha256'])
            self.assertEqual(self.commands(source),self.commands(output),number)
            validate_entry(source,output,self.info,'message','exact')
            self.assertLessEqual(expanded_bound(output,self.info),1024)
            issues=layout_issues(output,self.info,advances,resident_runtime=True)
            if issues:warnings[number]=issues
        self.assertEqual(warnings,{'077E':['explicit_layout_command_needs_review'],
                                   '29B0':['explicit_layout_command_needs_review']})

    def test_corrected_event_answers_match_native_quiz_options_and_continuations(self):
        text={id:row['translation'] for id,row in self.originals.items()}
        self.assertIn('fireworks',text['0AE5'])
        self.assertIn('fireworks',text['1212'])
        self.assertIn('April and October',text['1218'])
        self.assertIn('Moon viewing',text['1219'])
        self.assertIn('twice a year',text['1219'])
        for number,target in (('0AE5','0AE0'),('1212','121C'),('1218','121B'),('1219','121B')):
            self.assertIn('{cmd:7F0E'+target+'}',text[number])
            self.assertNotRegex(text[number],r'(?i)meteor|March|September|fishing')
        self.assertEqual(self.labels['00C1']['translation'],'Christmas Eve')
        self.assertEqual(self.labels['00BF']['translation'],'Moon Viewing')

    def test_native_question_polarity_date_and_correct_eye_chart_index(self):
        text={id:row['translation'] for id,row in self.originals.items()}
        self.assertIn('take it home?',text['077E'])
        self.assertIn('{cmd:7F160033000D}{cmd:7F5E}',text['077E'])
        self.assertIn('What should I do?',text['152B'])
        self.assertIn('Yesterday',text['1784'])
        self.assertIn('take a bath',text['1784'])
        self.assertNotRegex(text['1783'],r'(?i)mint|morning|today')
        self.assertIn('forget sometimes',text['1783'])
        self.assertIn('{cmd:7F0E1789}',text['1783'])
        self.assertIn('could afford it',text['2CF3'])
        self.assertIn('{cmd:7F5410}M{cmd:7F1801A301A401A501A6}',text['29B0'])
        self.assertIn('{cmd:7F1129B2}{cmd:7F0F29B1}{cmd:7F1029B1}{cmd:7F1229B1}',text['29B0'])

    def test_shared_label_sources_capacities_and_all_native_use_counts(self):
        counts={'0036':9,'00C1':3,'00BF':4,'002F':34,'00F8':3,'0103':8,'0130':4,'011F':1}
        self.assertEqual(set(self.labels),set(counts))
        uses={key:0 for key in counts}
        for source in self.sources['message']:
            for command in self.commands(source):
                if 0x16<=command[1]<=0x18:
                    for at in range(2,len(command),2):
                        key=command[at:at+2].hex().upper()
                        if key in uses:uses[key]+=1
        self.assertEqual(uses,counts)
        for number,row in self.labels.items():
            source=self.sources['select'][int(number,16)]
            output=encode(row['translation'],self.info)
            self.assertEqual(sha256(source),row['source_sha256'])
            validate_entry(source,output,self.info,'select',choice_bytes=16)
            self.assertTrue(all(t.kind=='text' for t in tokenize(output,self.info)))

    def test_shared_circle_and_x_are_not_globally_changed_to_truth_labels(self):
        self.assertNotIn('00CD',self.labels); self.assertNotIn('00CE',self.labels)
        count=0
        for source in self.sources['message']:
            for command in self.commands(source):
                if 0x16<=command[1]<=0x18:
                    ids=[int.from_bytes(command[at:at+2],'big') for at in range(2,len(command),2)]
                    count+=0xcd in ids
        self.assertEqual(count,35)
        # Both the symbol-guessing game and a true/false quiz share the IDs.
        for number in (0x0B38,0x0B67):
            self.assertTrue(any(c[1] in (0x16,0x17,0x18) and b'\x00\xcd\x00\xce' in c
                                for c in self.commands(self.sources['message'][number])))


if __name__=='__main__':
    unittest.main()
