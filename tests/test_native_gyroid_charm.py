"""Complete native gyroid/charm dialogue and full English police explanations."""

import json
from pathlib import Path
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
from reference_candidates import load_drafts, select_drafts
from reference_choices import adapt_choice_reference, validate_choice_candidate
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import expanded_bound, layout_issues, validate_entry
from test_retail import ROM_PATH

PATH = ROOT/'translations/n64-gyroid-charm-dialogue.json'
GYROID = {f'{i:04X}' for i in range(0x382,0x38C)}
CHARM = set('0761 0763 0767 0768 076A 076B 076C 076E 0770'.split())
IDS = GYROID | CHARM | {'02BD','02CC'}
POLICE = {'0777': (833, '0778'), '0778': (747, '0779')}


class GyroidCharmSelectionTests(unittest.TestCase):
    def test_all_twenty_one_complete_drafts_are_available_without_module(self):
        drafts = load_drafts([PATH])
        self.assertEqual({r['id'][8:] for r in drafts}, IDS)
        self.assertEqual(len(drafts), 21)
        self.assertEqual(select_drafts(drafts), (drafts, []))
        self.assertEqual(select_drafts(drafts, resident_runtime=True, english_dialogue_dates=True), (drafts, []))
        self.assertTrue(all(r['status']=='draft' and r.get('control_policy','exact')=='exact' for r in drafts))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM remains local')
class GyroidCharmRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.banks = {b.name:b.entries() for b in banks(cls.rom)}
        cls.drafts = load_drafts([PATH]); cls.text = {r['id'][8:]:r['translation'] for r in cls.drafts}
        cls.visible = {id:plain(text) for id,text in cls.text.items()}
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k,16):v for k,v in font['advance_by_glyph'].items()}

    def commands(self, raw):
        return [t.data for t in tokenize(raw,self.info) if t.kind=='cmd']

    def test_every_native_source_control_and_ending_is_exact(self):
        for row in self.drafts:
            native = self.banks['message'][int(row['id'][8:],16)]
            candidate = encode(row['translation'],self.info)
            self.assertEqual(sha256(native),row['source_sha256'],row['id'])
            self.assertEqual(self.commands(native),self.commands(candidate),row['id'])
            validate_entry(native,candidate,self.info,'message','exact')
            self.assertLessEqual(expanded_bound(candidate,self.info),1024)
        for id, request in (('02BD','6B'),('02CC','65')):
            self.assertTrue(self.text[id].startswith('{cmd:7F090500'+request+'}'))
            self.assertNotIn('{cmd:7F0C',self.text[id])

    def test_only_the_generic_owner_message_width_warning_remains(self):
        warned = {}
        for id,text in self.text.items():
            issues = layout_issues(encode(text,self.info),self.info,self.advances,resident_runtime=True)
            if issues: warned[id] = issues
        self.assertEqual(warned,{'0385':['page_1_line_1_width_816']})
        # This checks the surrounding English layout, not every possible custom
        # owner message. Native saved-owner wrapping has its separate tests.
        text = self.text['0385'].replace('{cmd:7F40}','An owner message\nwith manual lines.')
        self.assertEqual(layout_issues(encode(text,self.info),self.info,self.advances,resident_runtime=True),[])

    def test_gyroid_menus_owner_message_and_saving_warning_remain_native(self):
        self.assertIn('{cmd:7F17001300140015}{cmd:7F04}{cmd:7F0D}',self.text['0382'])
        self.assertNotIn('{cmd:7F0F',self.text['0382'])
        self.assertIn('{cmd:7F1600160015}{cmd:7F04}{cmd:7F0D}\n{cmd:7F09000001}',self.text['0386'])
        for id in ('0382','0386'): self.assertTrue(self.text[id].endswith('{cmd:7F01}'))
        self.assertIn('from my master',self.visible['0385'])
        self.assertIn('{cmd:7F40}\n{cmd:7F0E0386}\n{cmd:7F01}',self.text['0385'])
        notice = self.text['038A']
        self.assertIn('{cmd:7F050000C8}       Saving!',notice)
        self.assertIn('{cmd:7F05C80000}Do not turn the power off!',notice)
        self.assertLess(notice.index('power off'),notice.index('{cmd:7F01}'))
        self.assertIn('good rest',self.visible['038B'])
        self.assertIn('nothing',self.visible['0389'])
        self.assertNotEqual(self.text['0383'],self.text['0384'])
        self.assertNotEqual(self.text['0387'],self.text['0388'])

    def test_complete_native_charm_responses_keep_state_and_no_added_gc_branches(self):
        for id in CHARM:
            text = self.text[id]
            self.assertEqual(text.count('{cmd:7F41}'),1,id)
            self.assertTrue(text.endswith('{cmd:7F00}'),id)
            self.assertFalse(any(0x0E<=c[1]<=0x15 for c in self.commands(encode(text,self.info))),id)
        for id in ('0768','076B','076E'):
            self.assertTrue(self.text[id].endswith('{cmd:7F09020001}{cmd:7F0908000A}{cmd:7F0301}\n{cmd:7F00}'))
        for id,phrase in (('0761','closer inspection'),('0763','come to my senses'),
                          ('0767','tired of looking'),('076A',"doesn't feel special"),
                          ('076C','stopped caring'),('0770','lost interest')):
            self.assertIn(phrase,self.visible[id])

    def test_native_two_character_shout_highlights_and_pause_order_remain(self):
        for id in ('0768','076B'):
            raw = encode(self.text[id],self.info); tokens = list(tokenize(raw,self.info))
            at = next(i for i,t in enumerate(tokens) if t.kind=='cmd' and t.data[1]==0x50)
            self.assertEqual(tokens[at].data,bytes.fromhex('7F504B5F9B02'))
            following = [t.data for t in tokens[at+1:] if t.kind=='text']
            self.assertEqual(following[:2],[b'!',b'!'])

    def test_police_references_retain_entire_gc_payload_except_native_choice_ids(self):
        path = ROOT/'build/gamecube/text/message.jsonl'
        if not path.is_file(): self.skipTest('English extraction stays local')
        refs = {r['id']:r for r in map(json.loads,path.read_text().splitlines())}
        matches = load_matches(ROOT/'translations/reference_matches.json')
        with tempfile.TemporaryDirectory() as directory:
            edit_path = Path(directory)/'changed.json'
            for id,(bound,next_id) in POLICE.items():
                key = 'message:'+id; record = matches[key]; ref = refs[key]
                source = self.banks['message'][int(id,16)]
                original_ref = encode(ref['text'],self.info)
                text,changes = adapt_choice_reference(ref,source,record,self.info)
                candidate = encode(text,self.info); rule = record['native_choices']; at = rule['offset']
                self.assertEqual(candidate,original_ref[:at]+bytes.fromhex('7F16002F000B')+original_ref[at+6:])
                self.assertEqual(len(changes),1)
                text_after,adaptations = adapt_reference(text,source,self.info,'reference_layout',resident_runtime=True)
                self.assertEqual(text_after,text)
                self.assertTrue({r['operation'] for r in adaptations} <= {
                    'retain_gamecube_page_and_button_delivery', 'retain_gamecube_native_text_formatting'})
                validate_choice_candidate(key,source,candidate,matches)
                validate_entry(source,candidate,self.info,'message','reference_layout')
                self.assertEqual(expanded_bound(candidate,self.info),bound)
                self.assertIn('{cmd:7F0F'+next_id+'}{cmd:7F10077C}{cmd:7F19}',text)
                self.assertTrue(text.endswith('{cmd:7F01}'))
                for phrase in (('twenty','oldest items first','Do not delay') if id=='0777' else
                               ('no punishment','claiming recovered items','doorstop')):
                    self.assertIn(phrase,' '.join(plain(text).split()))
                edit = {'id':key,'source_sha256':sha256(source),'translation':text+' ',
                        'control_policy':'reference_layout','status':'reviewed'}
                edit_path.write_text(json.dumps([edit]))
                with self.assertRaisesRegex(ValueError,'Native-choice candidate'):
                    apply_translations(self.rom,{},edit_path)


if __name__=='__main__':
    unittest.main()
