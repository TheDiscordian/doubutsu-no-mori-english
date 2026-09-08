"""Native introductions/reunions retain full content and page/field semantics."""

from collections import Counter
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

PATH = ROOT/'translations/n64-reunion-greetings.json'
IDS = {f'message:{i:04X}' for i in range(0x13,0x5B)}
PAGE = '{cmd:7F04}\n{cmd:7F02}'
TOWN_WARNINGS = {'0034','0045','0046','0049','004E','0050','0057','0059','005A'}


class ReunionGreetingSelectionTests(unittest.TestCase):
    def test_all_three_groups_are_available_in_both_runtime_modes(self):
        rows=load_drafts([PATH])
        self.assertEqual(len(rows),72)
        self.assertEqual({r['id'] for r in rows},IDS)
        for resident in (False,True):
            self.assertEqual(select_drafts(rows,resident_runtime=resident),(rows,[]))
        self.assertTrue(all(r['status']=='draft' and r.get('control_policy','exact')=='exact'
                            and not r.get('runtime_requirements') for r in rows))
        for start in (0x13,0x2B,0x43):
            self.assertEqual(sum(start<=int(r['id'][8:],16)<start+24 for r in rows),24)


@unittest.skipUnless(ROM_PATH.is_file(),'Retail ROM stays local')
class ReunionGreetingRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=verified_rom(ROM_PATH.read_bytes());cls.info=module_command_info(cls.rom)
        cls.source=next(b for b in banks(cls.rom) if b.name=='message').entries()
        cls.rows=load_drafts([PATH]);cls.text={r['id'][8:]:r['translation'] for r in cls.rows}
        _,font=make_halfwidth(cls.rom)
        cls.advances={int(k,16):v for k,v in font['advance_by_glyph'].items()}

    def commands(self,data):
        return [t.data for t in tokenize(data,self.info) if t.kind=='cmd']

    def topics(self,required):
        for id,phrases in required.items():
            visible=plain(self.text[id])
            for phrase in phrases:self.assertIn(phrase,visible,id)

    def test_source_controls_endings_encoding_and_full_bounds(self):
        for row in self.rows:
            source=self.source[int(row['id'][8:],16)];candidate=encode(row['translation'],self.info)
            self.assertEqual(sha256(source),row['source_sha256'],row['id'])
            self.assertEqual(self.commands(source),self.commands(candidate),row['id'])
            validate_entry(source,candidate,self.info,'message','exact')
            self.assertEqual(decode(candidate,self.info),row['translation'])
            self.assertTrue(candidate.endswith(bytes.fromhex('7F01')),row['id'])
            self.assertLessEqual(expanded_bound(candidate,self.info),1024,row['id'])

    def test_every_page_field_and_line_count_except_explicit_five_line_page(self):
        differences=[]
        for row in self.rows:
            source=decode(self.source[int(row['id'][8:],16)],self.info)
            before,after=source.split(PAGE),row['translation'].split(PAGE)
            self.assertEqual(len(before),len(after),row['id'])
            for page,(native,english) in enumerate(zip(before,after)):
                self.assertEqual(self.commands(encode(native,self.info)),
                                 self.commands(encode(english,self.info)),(row['id'],page))
                if native.count('\n')!=english.count('\n'):
                    differences.append((row['id'],page,native.count('\n'),english.count('\n')))
        self.assertEqual(differences,[('message:002C',0,5,4)])
        first=self.text['002C'].split(PAGE)[0]
        self.assertTrue(first.startswith('Hello... Oh!\n'))
        self.assertIn('forgotten me?',first)
        self.assertEqual(first.count('{cmd:7F1A}'),1)
        self.assertEqual(first.count('{cmd:7F1B}'),1)

    def test_nine_generic_town_warnings_fit_native_town_limit_only(self):
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
            bounded=encode(text.replace('{cmd:7F2F}','ア'*6),self.info)
            self.assertEqual(layout_issues(bounded,self.info,self.advances,
                                          resident_runtime=True),[],row['id'])
        self.assertEqual(warned,TOWN_WARNINGS)

    def test_names_catchphrases_and_old_current_towns_stay_distinct(self):
        for id,command,count in (('0021','1C',4),('001C','1C',3),('0036','1C',3),
                                 ('0036','1A',2),('0037','1A',3),('0040','1B',2),
                                 ('0042','1A',2),('0045','1A',2),('004E','1A',2)):
            self.assertEqual(self.text[id].count('{cmd:7F'+command+'}'),count,id)
        for id in ('0034','0049','0050','0051','0057','005A'):
            self.assertIn('{cmd:7F2A}',self.text[id],id)
            self.assertIn('{cmd:7F2F}',self.text[id],id)
        self.assertIn('three lookalikes',plain(self.text['0042']))
        self.assertIn('kidnap',plain(self.text['002A']))

    def test_month_week_and_literal_absence_wording_remain_distinct(self):
        for id in ('002D','0030'):
            self.assertIn('more than a month',plain(self.text[id]),id)
            self.assertNotIn('{cmd:7F2B}',self.text[id],id)
            self.assertNotIn('{cmd:7F2C}',self.text[id],id)
        month_ids={'0037','0038','0039','003A','003B','003C','003D','003F','0041'}
        week_ids={'0048','0049','004A','004B','004C','004D','004F','0050','0051',
                  '0052','0053','0054','0056','0057','0059','005A'}
        self.assertEqual({k for k,v in self.text.items() if '{cmd:7F2B}' in v},month_ids)
        self.assertEqual({k for k,v in self.text.items() if '{cmd:7F2C}' in v},week_ids)
        for id in month_ids:self.assertIn('{cmd:7F2B} months',self.text[id],id)
        for id in week_ids:self.assertIn('{cmd:7F2C} weeks',self.text[id],id)
        self.assertIn('about',self.text['003D'])
        self.assertIn('About',self.text['004A'])
        self.assertIn('about',self.text['005A'])

    def test_first_introduction_topics_and_voices(self):
        self.topics({
            '0013':['early','happy'], '0014':['first meeting','forever'],
            '0015':['stranger','feeling'], '0016':['frightening','bad people'],
            '0017':["don't look",'friend'], '0018':['nervous','never met'],
            '0019':['house there','anytime'], '001A':['pushy','restraint','forgive'],
            '001B':['What time','who are you'], '001C':['very close','play again'],
            '001D':['proper hello','N-n-nice'], '001E':['much good','up to you'],
            '001F':['early bird','luckier'], '0020':['funny name','easy to remember'],
            '0021':['habit','slips out','Bear with me'], '0022':['funny people'],
            '0023':['grumpy','Sorry'], '0024':['working','sleeves','fated'],
            '0025':['meddling','long friendship'], '0026':['strangers anymore','sleep'],
            '0027':['more friends'], '0028':['religion','welcome'],
            '0029':['newspaper','leave it to me'],
            '002A':['suspicious','kidnap','prepare myself','lonely']})

    def test_long_reunion_stories_and_delayed_recognition(self):
        self.topics({
            '002B':['remember me','coincidence'], '002C':['forgotten','God'],
            '002D':['No wonder','more than a month'], '002E':['time of night','forgotten'],
            '002F':['memories','coincidence'], '0030':['ME','month','No wonder'],
            '0031':['startled','little blue'], '0032':['suspicious','miracle'],
            '0033':['woke me','never even dreamed'], '0034':['sort of familiar','how long'],
            '0035':["Don't tell me",'got it right'], '0036':['inconsiderate','ONE','been well'],
            '0037':['shake each other','having fun'], '0038':['never come','moved'],
            '0039':['fate','like before'], '003A':['decent person',"I'd forgotten"],
            '003B':['weight','Just joking','drifter'], '003C':['grown','same as ever'],
            '003D':["couldn't get a word",'special bond','blushing'],
            '003E':['carnivore','helped me','without telling'],
            '003F':['old friend','by chance'], '0040':['trouble','honour','forgive'],
            '0041':['almost forgot','never meet again'], '0042':['lookalikes','missed','Promise']})

    def test_short_reunion_stories_and_complete_qualifiers(self):
        self.topics({
            '0043':['little while ago','anytime'], '0044':['Did you know','friends again'],
            '0045':["don't have many",'friends yet'], '0046':['at this hour','recently moved'],
            '0047':['AND long time','really like'], '0048':["weren't looking",'NAVY'],
            '0049':['since then','used to live'], '004A':['other day','delinquent'],
            '004B':['Did you know','waiting'], '004C':['after I moved','Promise'],
            '004D':['must not know','glad'], '004E':['new friends','lonely'],
            '004F':['without telling','shake each other'], '0050':['even more fun'],
            '0051':['since then','always'], '0052':['handful','first time','eventually'],
            '0053':['early worthwhile',"look after you"], '0054':['hopes up','excited'],
            '0055':['business','slowpoke','good furniture','looking nice'],
            '0056':['eat you','considerate','relax'], '0057':['quite a nice place'],
            '0058':['how long',"I mean it"], '0059':["haven't any friends"],
            '005A':['wide awake','never meet again']})

    def test_empty_english_slots_legacy_agreement_and_no_visible_native_duplicate(self):
        native_path=ROOT/'build/inventory/message.jsonl'
        reference_path=ROOT/'build/gamecube/text/message.jsonl'
        if not (native_path.is_file() and reference_path.is_file()):
            self.skipTest('Supplied native/English extraction stays local')
        native={r['id']:r for r in map(json.loads,native_path.read_text().splitlines())}
        reference={r['id']:r for r in map(json.loads,reference_path.read_text().splitlines())}
        visible=lambda s:re.sub(r'\s+','',re.sub(r'\{cmd:[0-9A-F]+\}','',s))
        counts=Counter(visible(r['source']) for r in native.values())
        for row in self.rows:
            self.assertEqual(native[row['id']]['source_sha256'],row['source_sha256'])
            self.assertEqual(native[row['id']]['legacy'],native[row['id']]['source'])
            self.assertEqual(reference[row['id']]['text'],'{cmd:7F00}')
            self.assertEqual(counts[visible(native[row['id']]['source'])],1,row['id'])


if __name__=='__main__':unittest.main()
