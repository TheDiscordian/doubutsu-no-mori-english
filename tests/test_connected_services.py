"""Native service actions, answer meanings, and complete twin echoes remain."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from font import make_halfwidth
from reference_candidates import select_drafts
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry, expanded_bound, layout_issues
from test_retail import ROM_PATH

IDS = '1722 172A 1737 1889 1CD7 1D27 2065 2077 23DC 2769 2798 2CD0 1502 1D3D 28EE'.split()
ECHOES = {'1722': ('...come!', '...you!'),
          '172A': ('...oh,', '...accept.', '...uses.', '...one!', '...with?'),
          '1737': ('...yes,', '...services!', '...with?')}


class ConnectedDraftSelectionTests(unittest.TestCase):
    def test_all_fifteen_complete_originals_are_available_in_basic_and_full(self):
        rows = json.loads((ROOT/'translations/n64-connected-services.json').read_text())
        self.assertEqual([r['id'][8:] for r in rows], IDS)
        self.assertTrue(all(r['status'] == 'draft' and isinstance(r['provenance'], str) for r in rows))
        for resident in (False, True):
            self.assertEqual(select_drafts(rows, resident_runtime=resident), (rows, []))


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM stays local')
class ConnectedDraftRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.entries = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.rows = json.loads((ROOT/'translations/n64-connected-services.json').read_text())
        cls.text = {r['id'][8:]: r['translation'] for r in cls.rows}
        _, font = make_halfwidth(cls.rom)
        cls.advances = {int(k, 16): v for k, v in font['advance_by_glyph'].items()}

    def test_source_hashes_complete_native_commands_capacities_and_layouts(self):
        for row in self.rows:
            number = row['id'][8:]; source = self.entries[int(number, 16)]
            raw = encode(row['translation'], self.info)
            self.assertEqual(sha256(source), row['source_sha256'])
            commands = lambda data: [t.data for t in tokenize(data, self.info)
                                     if t.kind == 'cmd' and not (number in ECHOES and t.data[1] in (0x50, 0x54))]
            self.assertEqual(commands(source), commands(raw), number)
            validate_entry(source, raw, self.info, 'message', row.get('control_policy', 'exact'))
            self.assertLessEqual(expanded_bound(raw, self.info), 1024)
            self.assertEqual(layout_issues(raw, self.info, self.advances),
                             ['explicit_layout_command_needs_review'] if number in ECHOES else [], number)

    def test_all_ten_echoes_are_complete_with_original_rgb_anchor_and_scale(self):
        for number, echoes in ECHOES.items():
            raw = encode(self.text[number], self.info)
            commands = [t.data for t in tokenize(raw, self.info) if t.kind == 'cmd']
            self.assertEqual([c for c in commands if c[1] in (0x5C, 0x5D)],
                             [b'\x7f\x5c', b'\x7f\x5d']*len(echoes))
            self.assertEqual([c for c in commands if c[1] == 0x53], [bytes.fromhex('7F5301')]*len(echoes))
            self.assertEqual([c for c in commands if c[1] == 0x50],
                             [bytes.fromhex('7F50198CDC')+bytes((len(s),)) for s in echoes])
            self.assertEqual([c for c in commands if c[1] == 0x54],
                             [bytes.fromhex('7F541A')]*sum(map(len, echoes)))
            for echo in echoes:
                expected = bytes.fromhex('7F53017F50198CDC')+bytes((len(echo),))
                expected += b''.join(bytes.fromhex('7F541A')+encode(c, self.info) for c in echo)
                self.assertEqual(raw.count(expected), 1)

    def test_native_moving_gift_and_catchphrase_answers_keep_their_destinations(self):
        self.assertIn('{cmd:7F1600EE017F}', self.text['1CD7'])
        self.assertIn('{cmd:7F0F1CD8}{cmd:7F101CD9}', self.text['1CD7'])
        self.assertEqual(self.entries[0x1CDA], b'\x7f\x00')
        self.assertIn('{cmd:7F1800AD00AE00AF004E}', self.text['2065'])
        self.assertIn('{cmd:7F122065}', self.text['2065'])
        self.assertNotIn('2068', self.text['2065'])
        self.assertEqual(self.entries[0x2068], b'\x7f\x00')
        self.assertIn('{cmd:7F16011E0128}', self.text['2077'])
        self.assertIn('{cmd:7F0F2774}{cmd:7F102775}', self.text['2077'])
        for n in ('172A', '1737'):
            self.assertIn('{cmd:7F180009000A01C4000B}', self.text[n])

    def test_full_native_topics_fields_requests_and_random_endings_remain(self):
        self.assertIn('falling rain', self.text['23DC']); self.assertNotIn('sky', self.text['23DC'])
        self.assertEqual(self.text['23DC'].count('{cmd:7F2E}'), 2)
        self.assertIn('brown', self.text['2769']); self.assertIn('forgot', self.text['2769'])
        self.assertIn('{cmd:7F14276A276B276C}', self.text['2769'])
        self.assertTrue(self.text['2798'].endswith('{cmd:7F132799279A}\n{cmd:7F19}\n{cmd:7F01}'))
        self.assertIn('{cmd:7F35}', self.text['2CD0']); self.assertIn('{cmd:7F3F}', self.text['2CD0'])
        self.assertNotIn('{cmd:7F0C02000C}', self.text['2CD0'])
        self.assertNotIn('{cmd:7F0C020001}', self.text['28EE'])
        self.assertNotIn('{cmd:7F0C050001}', self.text['1D27'])
        self.assertNotIn('{cmd:7F1C}', self.text['1889'])
        for n in ('1502', '1D3D'):
            self.assertNotIn('{cmd:7F0902', self.text[n]); self.assertNotIn('{cmd:7F0908', self.text[n])
