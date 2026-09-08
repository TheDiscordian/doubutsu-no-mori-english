"""Complete native greetings, with unchanged field and page semantics."""

import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256,verified_rom
from font import make_halfwidth
from gc_text import plain
from reference_candidates import load_drafts,select_drafts
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode,encode,tokenize
from textvalidate import expanded_bound,layout_issues,validate_entry
from test_retail import ROM_PATH

PATH = ROOT/'translations/n64-daily-greetings.json'
IDS = {f'message:{i:04X}' for i in range(0x5B,0xB0)}
PAGE = '{cmd:7F04}\n{cmd:7F02}'
TOWN_WARNINGS = {'0062','0065','0067','006D','0070','0071'}


class DailyGreetingSelectionTests(unittest.TestCase):
    def test_complete_batch_is_available_in_both_runtime_modes(self):
        rows=load_drafts([PATH])
        self.assertEqual(len(rows),85)
        self.assertEqual({r['id'] for r in rows},IDS)
        for resident in (False,True):
            self.assertEqual(select_drafts(rows,resident_runtime=resident),(rows,[]))
        self.assertTrue(all(r['status']=='draft' and r.get('control_policy','exact')=='exact'
                            and not r.get('runtime_requirements') for r in rows))
        for start,end,count in ((0x5B,0x72,24),(0x73,0x8A,24),(0x8B,0xA2,24),(0xA3,0xAF,13)):
            self.assertEqual(sum(start<=int(r['id'][8:],16)<=end for r in rows),count)


@unittest.skipUnless(ROM_PATH.is_file(),'Retail ROM stays local')
class DailyGreetingRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=verified_rom(ROM_PATH.read_bytes());cls.info=module_command_info(cls.rom)
        cls.source=next(b for b in banks(cls.rom) if b.name=='message').entries()
        cls.rows=load_drafts([PATH]);cls.text={r['id'][8:]:r['translation'] for r in cls.rows}
        _,font=make_halfwidth(cls.rom)
        cls.advances={int(k,16):v for k,v in font['advance_by_glyph'].items()}

    def commands(self,data):
        return [t.data for t in tokenize(data,self.info) if t.kind=='cmd']

    def test_all_sources_controls_and_continuing_endings_remain_exact(self):
        for row in self.rows:
            source=self.source[int(row['id'][8:],16)];candidate=encode(row['translation'],self.info)
            self.assertEqual(sha256(source),row['source_sha256'],row['id'])
            self.assertEqual(self.commands(source),self.commands(candidate),row['id'])
            validate_entry(source,candidate,self.info,'message','exact')
            self.assertEqual(decode(candidate,self.info),row['translation'])
            self.assertTrue(candidate.endswith(bytes.fromhex('7F01')),row['id'])
            self.assertLessEqual(expanded_bound(candidate,self.info),1024,row['id'])

    def test_every_page_line_count_and_field_page_sequence_remains(self):
        for row in self.rows:
            source=decode(self.source[int(row['id'][8:],16)],self.info)
            before,after=source.split(PAGE),row['translation'].split(PAGE)
            self.assertEqual(len(before),len(after),row['id'])
            self.assertEqual([p.count('\n') for p in before],[p.count('\n') for p in after],row['id'])
            for native,english in zip(before,after):
                fields=lambda s:[c for c in self.commands(encode(s,self.info)) if 0x1A<=c[1]<=0x3F]
                self.assertEqual(fields(native),fields(english),row['id'])

    def test_six_explicit_generic_warnings_fit_the_native_current_town_limit(self):
        header=ROOT/'upstream/af/include/m_land.h'
        if header.is_file():
            self.assertRegex(header.read_text(),r'#define\s+LAND_NAME_SIZE\s+6\b')
        warned=set()
        for row in self.rows:
            text=row['translation'];raw=encode(text,self.info)
            issues=layout_issues(raw,self.info,self.advances,resident_runtime=True)
            if issues:
                warned.add(row['id'][8:])
                self.assertTrue(all(re.fullmatch(r'page_\d+_line_\d+_width_\d+',x) for x in issues))
            # Only current-town 2F is narrowed for this independent layout probe.
            # Old-town 2A, month counts, player/speaker names, and catchphrases
            # keep their unchanged conservative bounds.
            bounded=encode(text.replace('{cmd:7F2F}','ア'*6),self.info)
            self.assertEqual(layout_issues(bounded,self.info,self.advances,
                                          resident_runtime=True),[],row['id'])
        self.assertEqual(warned,TOWN_WARNINGS)

    def test_old_current_towns_and_repeated_name_fields_stay_distinct(self):
        for id in ('0065','0067','0068','006D','0070'):
            self.assertIn('{cmd:7F2A}',self.text[id],id)
            self.assertIn('{cmd:7F2F}',self.text[id],id)
        self.assertEqual(self.text['0065'].count('{cmd:7F2A}'),2)
        self.assertEqual(self.text['006F'].count('{cmd:7F1A}'),2)
        self.assertEqual(self.text['00AE'].count('{cmd:7F1A}'),2)
        self.assertEqual(self.text['008E'].count('{cmd:7F1C}'),2)
        self.assertEqual(self.text['0061'].count('{cmd:7F1B}'),1)
        month_ids={'00A3','00A4','00A5','00A7','00A8','00A9','00AA','00AB','00AC','00AE','00AF'}
        self.assertEqual({k for k,v in self.text.items() if '{cmd:7F2B}' in v},month_ids)
        self.assertTrue(all('{cmd:7F2C}' not in r['translation'] for r in self.rows))
        for id in month_ids:self.assertIn('{cmd:7F2B} months',self.text[id],id)
        self.assertIn('more than\n{cmd:7F2B}',self.text['00AF'])

    def test_recent_move_meanings_and_distinct_responses_remain(self):
        required={
            '005B':['Surprised','other day'], '005C':["Don't forget"],
            '005D':['moved away','wrong place'], '005E':["shouldn't",'staying here'],
            '005F':['few days ago','secret','found me'], '0060':['nobody','Just kidding'],
            '0061':['never said where','mood struck'], '0062':['peppy','need me'],
            '0063':["won't find me"], '0064':['taken a liking','stay awhile'],
            '0065':['no fun','Remember'], '0066':['unpacking','worn out'],
            '0067':['change of pace'], '0068':['by mistake'], '0069':['old pals','bored'],
            '006A':["I'm allowed",'exploring'], '006B':['more sleep','sort out'],
            '006C':["don't want to eat you",'nice place','wasn\'t like me'],
            '006D':['far apart','adventurer'], '006E':['Grown-ups','deal with'],
            '006F':['territory','mistake','Only joking'], '0070':['starting my life over'],
            '0071':['real comfort'], '0072':['unpacking']}
        for id,phrases in required.items():
            visible=plain(self.text[id])
            for phrase in phrases:self.assertIn(phrase,visible,id)

    def test_daily_repeat_and_absence_topics_remain(self):
        required={
            '0073':['lovely day'], '0074':['great mood'], '0075':['during the day','missed'],
            '0076':['risky'], '0077':['carefree','jealous'], '0078':["today's snack"],
            '0079':['getting so late'], '007A':['hopeless'], '007B':['more sleep'],
            '007C':['nap'], '007D':['bored'], '007E':['walks'], '007F':['give it my all'],
            '0080':["That's great"], '0081':['never came'], '0082':['fright'],
            '0083':['drank too much last night','head hurts'], '0084':['job'],
            '0085':["night's just starting"], '0086':['decent adult'],
            '0087':['morning walk'], '0088':['Eating properly','energy'],
            '0089':['while it was light'], '008A':['early start tomorrow'],
            '008B':['busy'], '008C':['tired'], '008D':['head home'], '008E':['my business','bed'],
            '008F':['again'], '0090':['hello'], '0091':['night out'], '0092':['get up tomorrow'],
            '0093':['just say good morning'], '0094':['hungry','Lunch'], '0095':['hello, hello'],
            '0096':['sleeeepy'], '0097':['back again'], '0098':['Nothing to do'],
            '0099':['dark'], '009A':['up too late'], '009B':['racket'], '009C':['Pester'],
            '009D':['nothing else'], '009E':['Respectable folks','bed'], '009F':['Back again'],
            '00A0':['visits'], '00A1':['head home'], '00A2':['bed early'],
            '00A3':['liked to go'], '00A4':['3 kilos','weight'], '00A5':['worried','something else'],
            '00A6':['party animal','handful'], '00A7':['collapsed','worried'],
            '00A8':['remember me','forgotten'], '00A9':['furniture every day','lovely room'],
            '00AA':['No excuses','forget'], '00AB':['forgotten'], '00AC':['all alone','mean'],
            '00AD':['fun game','Let me play too'], '00AE':['travelling','no one to play'],
            '00AF':['behind my back','Darn it']}
        for id,phrases in required.items():
            visible=plain(self.text[id])
            for phrase in phrases:self.assertIn(phrase,visible,id)

    def test_supplied_same_id_english_is_empty_and_legacy_retains_japanese(self):
        native_path=ROOT/'build/inventory/message.jsonl'
        reference_path=ROOT/'build/gamecube/text/message.jsonl'
        if not (native_path.is_file() and reference_path.is_file()):
            self.skipTest('Supplied native/English extraction stays local')
        native={r['id']:r for r in map(json.loads,native_path.read_text().splitlines())}
        reference={r['id']:r for r in map(json.loads,reference_path.read_text().splitlines())}
        for row in self.rows:
            self.assertEqual(native[row['id']]['source_sha256'],row['source_sha256'])
            self.assertEqual(native[row['id']]['legacy'],native[row['id']]['source'])
            self.assertEqual(reference[row['id']]['text'],'{cmd:7F00}')


if __name__=='__main__':unittest.main()
