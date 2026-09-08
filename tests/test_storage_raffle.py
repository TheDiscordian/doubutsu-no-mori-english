"""Complete native menus/prizes and four fully formatted twin-speaker echoes."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256, verified_rom
from font import make_halfwidth
from reference_candidates import select_drafts
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry, expanded_bound, layout_issues
from test_retail import ROM_PATH

IDS = ('0A0B','10D9','10DA','10DB','112C','10E1')
BOUNDS = (98,166,146,175,86,312)
ECHOES = ('...Welcome!','...day!','...But,','...1st floor!')


class StorageRaffleSelectionTests(unittest.TestCase):
    def test_every_original_is_available_with_or_without_the_resident_module(self):
        rows = json.loads((ROOT/'translations/n64-storage-raffle.json').read_text())
        self.assertEqual([r['id'][8:] for r in rows],list(IDS))
        self.assertTrue(all(r['status']=='draft' and isinstance(r['provenance'],str) for r in rows))
        for enabled in (False,True):
            self.assertEqual(select_drafts(rows,resident_runtime=enabled),(rows,[]))


@unittest.skipUnless(ROM_PATH.is_file(),'Retail ROM stays local')
class StorageRaffleNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes());cls.info = module_command_info(cls.rom)
        cls.entries = next(b for b in banks(cls.rom) if b.name=='message').entries()
        cls.rows = json.loads((ROOT/'translations/n64-storage-raffle.json').read_text())
        cls.text = {r['id'][8:]:r['translation'] for r in cls.rows}
        _,font = make_halfwidth(cls.rom)
        cls.advances = {int(k,16):v for k,v in font['advance_by_glyph'].items()}

    def test_all_six_complete_source_controls_and_bounds(self):
        commands = lambda d:[t.data for t in tokenize(d,self.info) if t.kind=='cmd']
        for row,bound in zip(self.rows,BOUNDS):
            number=int(row['id'][8:],16);src=self.entries[number];raw=encode(row['translation'],self.info)
            self.assertEqual(sha256(src),row['source_sha256'])
            before,after=commands(src),commands(raw)
            if number==0x10E1:
                before=[c for c in before if c[1] not in (0x50,0x54)]
                after=[c for c in after if c[1] not in (0x50,0x54)]
            self.assertEqual(before,after,row['id'])
            self.assertEqual(expanded_bound(raw,self.info),bound)
            validate_entry(src,raw,self.info,'message',row.get('control_policy','exact'))
            self.assertEqual(layout_issues(raw,self.info,self.advances),
                ['explicit_layout_command_needs_review'] if number==0x10E1 else [])

    def test_storage_and_offering_keep_complete_native_answers_and_destinations(self):
        self.assertIn('{cmd:7F31}',self.text['0A0B'])
        self.assertIn('{cmd:7F17007E000D00E9}',self.text['0A0B'])
        self.assertIn('{cmd:7F16001100F7}',self.text['112C'])
        self.assertIn('{cmd:7F0F112D}{cmd:7F10112E}',self.text['112C'])
        self.assertIn('offering',self.text['112C'])
        self.assertNotIn('well',self.text['112C'].lower())
        self.assertTrue(self.text['0A0B'].endswith('{cmd:7F01}'))
        self.assertTrue(self.text['112C'].endswith('{cmd:7F01}'))

    def test_every_prize_rank_item_and_native_player_reference_remains(self):
        for number,rank in (('10D9','first'),('10DA','second'),('10DB','third')):
            text=self.text[number]
            self.assertIn(rank+' prize',text);self.assertEqual(text.count('{cmd:7F31}'),1)
            self.assertTrue(text.endswith('{cmd:7F00}'))
            self.assertNotIn('{cmd:7F09090001}',text)
        self.assertIn("You've hit the jackpot!",self.text['10D9'])
        self.assertIn('{cmd:7F1A}',self.text['10DB'])

    def test_four_complete_echoes_keep_rgb_anchor_and_per_character_scale(self):
        raw=encode(self.text['10E1'],self.info)
        controls=[t.data for t in tokenize(raw,self.info) if t.kind=='cmd']
        self.assertEqual([c for c in controls if c[1] in (0x5C,0x5D)],
                         [bytes.fromhex('7F5C'),bytes.fromhex('7F5D')]*4)
        self.assertEqual([c for c in controls if c[1]==0x53],[bytes.fromhex('7F5301')]*4)
        self.assertEqual([c for c in controls if c[1]==0x50],
                         [bytes.fromhex('7F50198CDC')+bytes((len(s),)) for s in ECHOES])
        self.assertEqual([c for c in controls if c[1]==0x54],
                         [bytes.fromhex('7F541A')]*sum(map(len,ECHOES)))
        for echo in ECHOES:
            full=bytes.fromhex('7F53017F50198CDC')+bytes((len(echo),))
            full+=b''.join(bytes.fromhex('7F541A')+encode(c,self.info) for c in echo)
            self.assertEqual(raw.count(full),1)
        self.assertIn('{cmd:7F5C}But,{cmd:7F5D}',self.text['10E1'])
        self.assertIn('on the 1st floor!',self.text['10E1'])
