"""Complete native return greetings, without inventing absent English donors."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from font import make_halfwidth
from gc_text import plain
from reference_candidates import load_drafts, select_drafts
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

PATH = ROOT/'translations/n64-return-greetings.json'
IDS = {f'message:{i:04X}' for i in range(0xB0, 0xD3)}
PAGE = '{cmd:7F04}\n{cmd:7F02}'


class ReturnGreetingSelectionTests(unittest.TestCase):
    def test_all_native_originals_are_selected_in_both_runtime_modes(self):
        rows = load_drafts([PATH])
        self.assertEqual(len(rows), 35)
        self.assertEqual({r['id'] for r in rows}, IDS)
        for resident in (False, True):
            self.assertEqual(select_drafts(rows, resident_runtime=resident), (rows, []))
        self.assertTrue(all(r['status']=='draft' and r.get('control_policy', 'exact')=='exact'
                            for r in rows))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM stays local')
class ReturnGreetingRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes())
        cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name=='message').entries()
        cls.rows = load_drafts([PATH])
        cls.text = {r['id'][8:]:r['translation'] for r in cls.rows}
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k,16):v for k,v in font['advance_by_glyph'].items()}

    def commands(self, data):
        return [t.data for t in tokenize(data, self.info) if t.kind=='cmd']

    def test_complete_source_commands_and_continuing_endings_remain(self):
        for row in self.rows:
            native = self.source[int(row['id'][8:],16)]
            candidate = encode(row['translation'],self.info)
            self.assertEqual(sha256(native),row['source_sha256'],row['id'])
            self.assertEqual(self.commands(candidate),self.commands(native),row['id'])
            validate_entry(native,candidate,self.info,'message','exact')
            self.assertEqual(decode(candidate,self.info),row['translation'])
            self.assertTrue(candidate.endswith(bytes.fromhex('7F01')),row['id'])

    def test_native_page_line_counts_and_field_page_assignments_remain(self):
        for row in self.rows:
            native = decode(self.source[int(row['id'][8:],16)],self.info)
            before, after = native.split(PAGE), row['translation'].split(PAGE)
            self.assertEqual(len(before),len(after),row['id'])
            self.assertEqual([p.count('\n') for p in before],
                             [p.count('\n') for p in after],row['id'])
            for source_page, english_page in zip(before,after):
                self.assertEqual(re.findall(r'\{cmd:7F(?:1A|1C|2B|2C)\}',source_page),
                                 re.findall(r'\{cmd:7F(?:1A|1C|2B|2C)\}',english_page),row['id'])

    def test_full_expansion_bounds_and_conservative_layout_fit(self):
        for row in self.rows:
            candidate = encode(row['translation'],self.info)
            self.assertLessEqual(expanded_bound(candidate,self.info),1024,row['id'])
            self.assertEqual(layout_issues(candidate,self.info,self.advances,
                                          resident_runtime=True),[],row['id'])

    def test_months_weeks_and_repeated_catchphrases_are_not_conflated(self):
        months = {'00B0','00B1','00B6','00B8','00B9'}
        weeks = {'00BD','00C0','00C3','00C4','00C5','00C8','00C9',
                 '00CB','00CD','00D0','00D1','00D2'}
        self.assertEqual({k for k,v in self.text.items() if '{cmd:7F2B}' in v},months)
        self.assertEqual({k for k,v in self.text.items() if '{cmd:7F2C}' in v},weeks)
        for id in months: self.assertIn('{cmd:7F2B} months',self.text[id])
        for id in weeks: self.assertIn('{cmd:7F2C} weeks',self.text[id])
        self.assertEqual(self.text['00BD'].count('{cmd:7F1C}'),3)
        self.assertEqual(self.text['00B1'].count('{cmd:7F1C}'),1)

    def test_native_topics_are_preserved_instead_of_generic_greetings(self):
        required = {
            '00B0': ['cold-hearted', 'kidding'], '00B1': ['grown', 'haven\'t'],
            '00B2': ['debt collectors', 'sneak out'], '00B3': ['spears', 'sky'],
            '00B4': ['room layout', 'effort'], '00B5': ['ground', 'stomachache', 'keel over'],
            '00B7': ['fallen ill', 'relief'], '00B8': ['accident', 'one bit'],
            '00B9': ['taste in clothes', 'Another joke'], '00BA': ['suspicious', 'surprise'],
            '00BB': ['dieting', 'lose weight'], '00BD': ['lonely', 'every day'],
            '00BE': ['usually asleep', 'coincidence'], '00BF': ['close friend', 'fresh'],
            '00C0': ['hot spring', 'unwind'], '00C1': ['sick in bed', 'worried'],
            '00C2': ['sunshine', 'kidding'], '00C3': ['asleep', 'long time'],
            '00C4': ['ate too much', 'groaning'], '00C5': ['delinquent', 'kidding'],
            '00C6': ['grounded', 'late'], '00C7': ['training', 'sickness'],
            '00C8': ['working hard', 'business'], '00C9': ['sleep', 'furniture'],
            '00CA': ['another night out'], '00CB': ['mornings', 'my wife'],
            '00CC': ['good furniture'], '00CD': ['never even met'],
            '00CE': ['come out and get you'], '00CF': ['souvenirs', 'cheapskate'],
            '00D0': ['bored', 'die'], '00D1': ['behind my back', 'kidding'],
            '00D2': ['slacking off', 'tomorrow', 'decorating your room']}
        for id,phrases in required.items():
            visible = ' '.join(plain(self.text[id]).split())
            for phrase in phrases: self.assertIn(phrase,visible,id)

    def test_empty_gc_slots_and_no_identical_native_prose_donor(self):
        reference = ROOT/'build/gamecube/text/message.jsonl'
        if not reference.is_file(): self.skipTest('Supplied English extraction stays local')
        refs = {r['id']:r['text'] for r in map(json.loads,reference.read_text().splitlines())}
        normalize = lambda text: re.sub(r'\s+','',plain(text))
        counts = {}
        for raw in self.source:
            text = normalize(decode(raw,self.info))
            counts[text] = counts.get(text,0)+1
        for row in self.rows:
            self.assertEqual(refs[row['id']],'{cmd:7F00}',row['id'])
            native = normalize(decode(self.source[int(row['id'][8:],16)],self.info))
            self.assertEqual(counts[native],1,row['id'])


if __name__=='__main__':
    unittest.main()
