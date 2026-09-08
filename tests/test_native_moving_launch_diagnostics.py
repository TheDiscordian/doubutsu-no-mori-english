"""Native moving decisions, named game prompts, and complete diagnostic labels."""

from collections import Counter
import json
from pathlib import Path
import re
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256,verified_rom
from font import make_halfwidth
from gc_text import plain
from native_diagnostics import definition,native_definition,validate_diagnostic
from reference_candidates import load_drafts,select_drafts
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode,encode,tokenize
from text_coverage import classify
from textvalidate import expanded_bound,layout_issues,validate_entry
from test_retail import ROM_PATH

PATHS=[ROOT/'translations'/('n64-'+name+'.json') for name in
       ('moving-conversations','nes-launch-prompts','diagnostic-labels')]
MOVING=set('0FA5 0FA6 0FA7 0FA8 0FAC 2862 2863 2864'.split())
GAMES={f'{0x2B6B+i:04X}':name for i,name in enumerate(
       ('Clu Clu Land','Balloon Fight','Donkey Kong','DK Jr MATH','Pinball','Tennis','Golf'))}
JAPANESE_GAMES=('クルクルランド','バルーンファイト','ドンキーコング','さんすうあそび',
                'ピンボール','テニス','ゴルフ')
CORRECTED={f'message:{i:04X}' for i in range(0x2720,0x273A)}


class DiagnosticGuardTests(unittest.TestCase):
    def setUp(self):
        self.info=[(2,0)]*0x61
        self.info[3]=(3,0)

    def test_exact_recognition_and_printed_number_not_record_number(self):
        for text,kind,number in (('うわさパターン2','rumour_pattern','2'),
                                ('スクリプトバグ\nコワイあにき\n00123','script_bug','00123'),
                                ('このメッセージは\n2353 でヒ\nデバッグちゅうに\n'
                                 'このめっせーじがでたら\nおしらせくださいまヒ\nBy えぐち',
                                 'gyroid_debug_notice','2353')):
            result=definition(text)
            self.assertEqual((result.kind,result.number),(kind,number))
            self.assertIn(number,result.translation)
        for text in ('うわさ パターン3','スクリプトバグ コワイあにき',
                     'スクリプトバグ コワイあにき 123 おはよう',
                     'おはよう うわさ パターン1','うわさについて'):
            self.assertIsNone(definition(text),text)

    def test_partial_reference_wrong_number_and_changed_controls_are_rejected(self):
        original=encode('スクリプトバグ\nコワイあにき\n10016\n{cmd:7F00}',self.info)
        complete=encode(definition('スクリプトバグ コワイあにき 10016').translation,self.info)
        validate_entry(original,complete,self.info,'message','exact')
        for text in ('Cranky Guy extra\n{cmd:7F00}',
                     'Script bug\nCranky guy\n10017\n{cmd:7F00}',
                     'Script bug\nCranky guy\n10016\n{cmd:7F01}',
                     'Script bug\nCranky guy\n10016{cmd:7F0304}\n{cmd:7F00}'):
            for policy in ('exact','presentation','reference_text','reference_delivery','reference_layout'):
                with self.assertRaisesRegex(ValueError,'Native diagnostic'):
                    validate_entry(original,encode(text,self.info),self.info,'message',policy)
        with self.assertRaisesRegex(ValueError,'complete hash-bound approval'):
            validate_entry(original,complete,self.info,'message','reviewed_sequence')

    def test_guard_does_not_redefine_coverage_or_guess_unknown_tokens(self):
        for text in ('うわさ パターン1','スクリプトバグ コワイあにき 10016'):
            raw=encode(text+'\n{cmd:7F00}',self.info)
            self.assertIsNotNone(native_definition(raw,self.info))
            self.assertEqual(classify(raw,self.info)['category'],'japanese_static_text')
            self.assertIsNone(native_definition(raw+b'\x80\x42',self.info))
            self.assertIsNone(native_definition(raw+b'\x7f',self.info))
        raw=encode('うわさ パターン1{cmd:7F01}',self.info)
        with self.assertRaisesRegex(ValueError,'unsupported control structure'):
            validate_diagnostic(raw,encode('Rumour pattern 1\n{cmd:7F00}',self.info),self.info)

    def test_complete_batch_and_diagnostic_counts_in_both_modes(self):
        rows=load_drafts(PATHS)
        self.assertEqual(len(rows),114)
        self.assertEqual(len({r['id'] for r in rows}),114)
        self.assertEqual({r['id'][8:] for r in rows if 'diagnostic_kind' not in r},MOVING|GAMES.keys())
        self.assertEqual(Counter(r['diagnostic_kind'] for r in rows if 'diagnostic_kind' in r),
                         {'rumour_pattern':28,'script_bug':68,'gyroid_debug_notice':3})
        for resident in (False,True):
            self.assertEqual(select_drafts(rows,resident_runtime=resident),(rows,[]))
        self.assertTrue(all(r['status']=='draft' and not r.get('runtime_requirements') for r in rows))


@unittest.skipUnless(ROM_PATH.is_file(),'Retail ROM remains local')
class MovingLaunchDiagnosticRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=verified_rom(ROM_PATH.read_bytes());cls.info=module_command_info(cls.rom)
        cls.banks={b.name:b.entries() for b in banks(cls.rom)}
        cls.rows=load_drafts(PATHS);cls.by_id={r['id'][8:]:r for r in cls.rows}
        _,font=make_halfwidth(cls.rom)
        cls.advances={int(k,16):v for k,v in font['advance_by_glyph'].items()}

    def commands(self,data):
        return [t.data for t in tokenize(data,self.info) if t.kind=='cmd']

    def test_all_sources_controls_encoding_and_endings(self):
        for row in self.rows:
            short=row['id'][8:];original=self.banks['message'][int(short,16)]
            candidate=encode(row['translation'],self.info)
            self.assertEqual(sha256(original),row['source_sha256'],short)
            self.assertEqual(decode(candidate,self.info),row['translation'],short)
            expected=self.commands(original)
            if short in GAMES:
                expected=[c[:-1]+bytes([len(GAMES[short]) if c[2:5]==bytes.fromhex('324BE1') else 1])
                          if c[1]==0x50 else c for c in expected]
            self.assertEqual(self.commands(candidate),expected,short)
            self.assertEqual(candidate[-2:],original[-2:],short)
            validate_entry(original,candidate,self.info,'message',row.get('control_policy','exact'),
                           resident_runtime=True)
            self.assertLessEqual(expanded_bound(candidate,self.info),1024,short)

    def test_native_moving_pages_and_field_assignments(self):
        for short in MOVING:
            native=decode(self.banks['message'][int(short,16)],self.info)
            text=self.by_id[short]['translation']
            before,after=native.split('{cmd:7F02}'),text.split('{cmd:7F02}')
            self.assertEqual(len(before),len(after),short)
            for a,b in zip(before,after):
                self.assertEqual(self.commands(encode(a,self.info)),self.commands(encode(b,self.info)),short)
            self.assertEqual(text.count('{cmd:7F04}'),native.count('{cmd:7F04}'),short)

    def test_native_satisfaction_menu_and_no_gc_only_moving_actions(self):
        question=self.by_id['0FA5']['translation']
        self.assertIn('{cmd:7F1601030104}',question)
        self.assertIn('{cmd:7F0F0FA8}{cmd:7F100FA9}{cmd:7F19}',question)
        self.assertIn('happy with it?',question)
        reply=self.by_id['0FA8']['translation']
        self.assertIn('"somewhat"',reply)
        self.assertIn('wishy-washy',reply)
        connected=next(r for r in load_drafts([ROOT/'translations/n64-town-advice.json'])
                       if r['id']=='message:0FA9')
        self.assertIn('slightly dissatisfied',connected['translation'])
        for short in ('0FA6','0FA7','2862','2863','2864'):
            commands=self.commands(encode(self.by_id[short]['translation'],self.info))
            self.assertFalse(any(0x0E<=c[1]<=0x19 for c in commands),short)
            self.assertEqual(commands[-1],bytes.fromhex('7F00'),short)
        for index in (0x2865,0x2866):
            self.assertEqual(self.banks['message'][index],bytes.fromhex('7F00'))

    def test_complete_native_moving_and_nook_meanings(self):
        required={'0FA5':['far away',"isn't a bad place",'happy'],
                  '0FA6':['same scenery',"don't know",'take me there','Even if','anyway'],
                  '0FA7':["you're young",'different people','shell','one place','somewhere else'],
                  '0FA8':['somewhat',"If you're happy",'If you\'re not','wishy-washy'],
                  '0FAC':["Tom Nook's dream",'lots of money','bigger and bigger','your house','example'],
                  '2862':['slump','quiet life',"doesn't fit",'somewhere else'],
                  '2863':['Adventure','Romance','Courage','silly grin','body and mind','move'],
                  '2864':['too long','drifter','another town','might tag along']}
        for short,phrases in required.items():
            visible=plain(self.by_id[short]['translation'])
            for phrase in phrases:self.assertIn(phrase,visible,short)

    def test_seven_full_gc_titles_and_exact_colour_lengths(self):
        reference_path=ROOT/'build/gamecube/names/furniture.jsonl'
        if not reference_path.is_file():self.skipTest('Supplied GameCube names stay local')
        names={r['id']:r for r in map(json.loads,reference_path.read_text().splitlines())}
        for i,(short,name) in enumerate(GAMES.items()):
            self.assertEqual(names[f'furniture:{0x36A+i:04X}']['text'],name,short)
            native=decode(self.banks['message'][int(short,16)],self.info)
            self.assertIn(JAPANESE_GAMES[i],native,short)
            text=self.by_id[short]['translation']
            self.assertIn('{cmd:7F50324BE1'+f'{len(name):02X}'+'}'+name,text,short)
            self.assertIn('{cmd:7F504B1E1401}?',text,short)
            self.assertIn('{cmd:7F1601AA01AB}{cmd:7F04}{cmd:7F0D}{cmd:7F0F17B5}',text,short)
        self.assertEqual(decode(self.banks['select'][0x1AA],self.info),'あそぶ')
        self.assertEqual(decode(self.banks['select'][0x1AB],self.info),'あそばない')

    def test_all_ninety_nine_diagnostics_and_preserved_printed_numbers(self):
        actual={f'{i:04X}':native_definition(raw,self.info)
                for i,raw in enumerate(self.banks['message']) if native_definition(raw,self.info)}
        rows={k:r for k,r in self.by_id.items() if 'diagnostic_kind' in r}
        self.assertEqual(actual.keys(),rows.keys())
        self.assertEqual(len(actual),99)
        for short,diagnostic in actual.items():
            self.assertEqual(rows[short]['translation'],diagnostic.translation,short)
            self.assertEqual(str(rows[short]['printed_number']),diagnostic.number,short)
            self.assertEqual(rows[short]['diagnostic_kind'],diagnostic.kind,short)
        self.assertEqual(rows['2956']['printed_number'],10581)
        self.assertNotEqual(rows['2956']['printed_number'],int('2956',16))
        for id in CORRECTED:
            self.assertIn('Script bug\nCranky guy\n',rows[id[8:]]['translation'])

    def test_gyroid_notices_retain_credit_pages_and_no_imported_save_actions(self):
        for short in ('092F','0930','0931'):
            original=self.banks['message'][int(short,16)];row=self.by_id[short]
            self.assertEqual(self.commands(original),[bytes.fromhex(c) for c in ('7F04','7F02','7F00')])
            first,second=row['translation'].split('{cmd:7F02}')
            self.assertIn(str(row['printed_number']),first)
            self.assertIn('while debugging',second)
            self.assertIn('please report it',second)
            self.assertIn('By Eguchi',second)
            self.assertNotIn('save',row['translation'].lower())

    def test_layout_except_two_explicit_current_town_warnings(self):
        warned=set()
        for row in self.rows:
            text=row['translation']
            issues=layout_issues(encode(text,self.info),self.info,self.advances,resident_runtime=True)
            if issues:warned.add(row['id'][8:])
            self.assertEqual(layout_issues(encode(text.replace('{cmd:7F2F}','ア'*6),self.info),
                                          self.info,self.advances,resident_runtime=True),[],row['id'])
        self.assertEqual(warned,{'0FA5','2862'})


if __name__=='__main__':unittest.main()
