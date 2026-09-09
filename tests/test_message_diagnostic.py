"""Complete last native diagnostic, exact split, reserve, and installed output."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, CODE_RAM, CODE_VROM, sha256, verified_rom
from code_sections import code_segments
from reference_sequences import (commands, load_sequences, message_targets, reference_payloads,
                                 reference_sequence_edits, validate_sequences)
from runtime_module import module_command_info
from sequence_test_scenario import scenario
from textbanks import Bank, banks
from textcodec import encode, has_japanese
from textvalidate import expanded_bound, validate_entry

GROUP = 'native_message_diagnostic'
BUILD = ROOT/'build/message-diagnostic-pilot'
NATIVE = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


@unittest.skipUnless(NATIVE.is_file(), 'Original cartridge remains local')
class MessageDiagnosticSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(NATIVE.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.source = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.group = load_sequences()[GROUP]; cls.groups = {GROUP: cls.group}
        cls.edits, cls.permits = reference_sequence_edits({}, cls.source, cls.info, cls.groups,
                                                        resident_runtime=True)

    def test_complete_source_all_commands_exact_cut_and_bounded_parts(self):
        draft, = json.loads((ROOT/'translations/n64-message-diagnostic.json').read_text())
        full = encode(draft['translation'], self.info)
        self.assertEqual(self.group['original_translation'],
                         {'id': draft['id'], 'text': draft['translation'], 'sha256': sha256(full)})
        self.assertEqual(sha256(self.source[4]), draft['source_sha256'])
        self.assertEqual(commands(self.source[4], self.info), commands(full, self.info))
        self.assertEqual(len(commands(full, self.info)), 62)
        self.assertEqual(self.source[4].count(b'\xcd'), full.count(b'\xcd'))
        self.assertFalse(has_japanese(full, self.info))
        self.assertEqual((len(full), expanded_bound(full, self.info)), (961, 1581))
        with self.assertRaisesRegex(ValueError, '1024'):
            validate_entry(self.source[4], full, self.info, 'message')
        parts = reference_payloads(self.group, {}, self.info)
        self.assertEqual([m['id'] for m in self.group['members']], ['message:0004', 'message:2AEB'])
        self.assertEqual([m['reference_slice'] for m in self.group['members']], [[0, 416], [421, 961]])
        self.assertEqual(full[416:421], bytes.fromhex('7F04CD7F02'))
        self.assertEqual(parts[0][:-7]+full[416:421]+parts[1], full)
        self.assertEqual(parts[0][-7:], bytes.fromhex('7F0E2AEBCD7F01'))
        self.assertTrue(parts[1].startswith(b'Current date and time'))
        self.assertEqual([(len(p), expanded_bound(p, self.info)) for p in parts], [(423, 713), (540, 886)])
        for row, part in zip(self.edits, parts, strict=True):
            validate_entry(self.source[int(row['id'][8:], 16)], part, self.info, 'message',
                           'reviewed_sequence', resident_runtime=True, sequence_permit=self.permits[row['id']])
            self.assertNotIn('disc', row['provenance']['source'])
        self.assertEqual([c for c in commands(parts[0], self.info) if c[1] in (6, 7)],
                         [b'\x7f\x07', b'\x7f\x06'])
        self.assertFalse(any(c[1] in (6, 7) for c in commands(parts[1], self.info)))

    def test_partial_changed_stale_and_runtime_less_requests_fail(self):
        self.assertEqual(reference_sequence_edits({}, self.source, self.info, self.groups), ([], {}))
        with self.assertRaisesRegex(ValueError, 'resident runtime'):
            validate_sequences(self.edits, self.source, self.info, self.groups)
        with self.assertRaisesRegex(ValueError, 'Partial'):
            validate_sequences(self.edits[:1], self.source, self.info, self.groups, resident_runtime=True)
        changed = deepcopy(self.edits); changed[-1]['translation'] += 'Changed'
        with self.assertRaisesRegex(ValueError, 'translated bytes changed'):
            validate_sequences(changed, self.source, self.info, self.groups, resident_runtime=True)
        group = deepcopy(self.group); group['members'][-1]['source_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'source'):
            validate_sequences(self.edits, self.source, self.info, {GROUP: group}, resident_runtime=True)
        group = deepcopy(self.group); group['members'][0]['reference_slice'][1] -= 1
        with self.assertRaises(ValueError): reference_payloads(group, {}, self.info)

    def test_reserve_has_no_native_script_code_or_data_reference(self):
        slot = 0x2AEB
        self.assertEqual(self.source[slot], encode('きしゃのデモ\nよびのエリア\n{cmd:7F00}', self.info))
        self.assertEqual(sha256(self.source[slot]),
                         '0727aac8e3f598400dccbb8e9a23f39c10b3bc13e0dc1c168b93d03c0aa95609')
        self.assertFalse(any(slot in message_targets(raw, self.info) for raw in self.source))
        self.assertEqual([name for name, g in load_sequences().items()
                          if any(m['id'] == 'message:2AEB' for m in g['members'])], [GROUP])
        files = by_vrom(self.rom); hits = []
        for vrom, segment in code_segments()[0].items():
            if vrom not in files: continue
            data = files[vrom].extract(self.rom)
            for offset in range(0, len(data)-3, 4):
                word = int.from_bytes(data[offset:offset+4], 'big')
                if segment.is_text(offset) and word & 0xFFFF == slot and word >> 26 in range(8, 15):
                    hits.append((segment.name, offset, 'code'))
            for offset in range(0, len(data)-1, 2):
                if not segment.is_text(offset) and int.from_bytes(data[offset:offset+2], 'big') == slot:
                    hits.append((segment.name, offset, 'data'))
        self.assertEqual(hits, [])

    def test_native_transition_cancel_handlers_and_field_extents(self):
        code = by_vrom(self.rom)[CODE_VROM].extract(self.rom)
        for start, end, digest in (
                (0x8009E658, 0x8009E6B8, '07a8d7b9126da0520717ee86468f4b230b7a823d2b02bf93ff2af6516dc9185c'),
                (0x8009E344, 0x8009E374, '4fe183363fb34b26fc1b128c18d7e2407f40734b62bc6031a17e4c3d33b84831'),
                (0x8009E374, 0x8009E388, '0a9a5025eeade42104ff89eed845b1f63fa886e6b51b6d7cd22a9e526fa5d513'),
                (0x800A0864, 0x800A08B0, '7c080c1757fb36a2f181d204231ae310fb44e193b0b418ba493ef249191217f9'),
                (0x800A08B0, 0x800A08F8, '90b182bfd0bc0aa8704b429f286d6dcaf18d40a39ea237fedd6d9e5bd3adb49d')):
            self.assertEqual(sha256(code[start-CODE_RAM:end-CODE_RAM]), digest)
        for address, expected in ((0x8009D714, '24420038'), (0x8009DAC8, '24630132'),
                                  (0x8009DAB4, '24070044'), (0x800A0540, 'AC8002BC')):
            self.assertEqual(code[address-CODE_RAM:address-CODE_RAM+4], bytes.fromhex(expected))


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete diagnostic-sequence ROM required')
class MessageDiagnosticCartridgeTests(unittest.TestCase):
    def test_exact_installation_prior_retention_patch_and_native_plan(self):
        previous = ROOT/'build/rendering-diagnostics-pilot'
        before, after = [json.loads((ROOT/f'build/{p}-candidates/translations.json').read_text())
                         for p in ('rendering-diagnostics', 'message-diagnostic')]
        a, b = [{r['id']: r for r in rows} for rows in (before, after)]
        self.assertEqual((len(a), len(b)), (13767, 13768))
        self.assertEqual(b.keys()-a.keys(), {'message:0004'})
        relabelled = {'message:0487', 'message:0488', 'message:0489'}
        self.assertEqual({key for key in a if a[key] != b[key]}, {'message:2AEB'} | relabelled)
        # Allocating 2AEB removes the conflicting ordinary alias donor. These
        # three existing reserve labels now use the unanimous complete 0485
        # English reference; no gameplay wording or command changes.
        for key in relabelled:
            self.assertEqual(a[key]['translation'], 'Train Demo\nExtra Area\n{cmd:7F00}')
            self.assertEqual(b[key]['translation'], 'Train Demo\nExtra Space\n{cmd:7F00}')
            self.assertEqual(b[key]['provenance']['native_equivalent_ids'], ['message:0485'])
            self.assertEqual(b[key]['provenance']['reference_sha256'],
                             'fc16d80bd9a938d195fe15b5ca19eb9cddd01e94f48e011cdc6c6773f9120ace')
        old, new = [(p/'animal-forest-halfwidth.z64').read_bytes() for p in (previous, BUILD)]
        x, y = by_vrom(old), by_vrom(new)
        self.assertEqual(x.keys(), y.keys())
        self.assertEqual({key for key in x if x[key].extract(old) != y[key].extract(new)},
                         {0x19D40, 0x2000000, 0xCF9000})
        entries = [Bank('message', 0x2000000, 0xCF9000, files[0x2000000].extract(rom),
                        files[0xCF9000].extract(rom)).entries() for files, rom in ((x, old), (y, new))]
        self.assertEqual({i for i, (a, b) in enumerate(zip(*entries, strict=True)) if a != b},
                         {4, 0x2AEB, 0x0487, 0x0488, 0x0489})
        native = NATIVE.read_bytes(); report = json.loads((BUILD/'build.json').read_text())
        self.assertEqual(sha256(new), report['output_sha256'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), new)
        plan = scenario(new, GROUP, report['runtime_module'])
        calls = [r['call'] for r in plan if 'call' in r]
        self.assertEqual(sum(r['address'] == '8009E658' for r in calls), 2)
        self.assertEqual(sum(r['address'] == '800A04E4' for r in calls), 2)
        self.assertEqual(sum(r.get('read') == ['8019B038', 318] for r in plan), 4)
        self.assertEqual(sum('save_state' in r for r in plan), 1)
        self.assertEqual(sum('load_state' in r for r in plan), 1)

    def test_combined_credit_adds_only_complete_root_and_no_japanese_message_remains(self):
        from translation_progress import measure
        ledgers = []
        for name in ('rendering-diagnostics', 'message-diagnostic'):
            root = ROOT/('build/'+name+'-pilot')
            ledgers.append(measure(NATIVE.read_bytes(), (root/'animal-forest-halfwidth.z64').read_bytes(),
                                   json.loads((root/'build.json').read_text())))
        a, b = [{key for key, row in ledger.rows.items() if row['replacements']} for ledger in ledgers]
        self.assertEqual(b-a, {'message:0004'}); self.assertFalse(a-b)
        self.assertEqual([r.summary()['total_source_characters'] for r in ledgers], [751002]*2)
        remaining = [key for key, row in ledgers[-1].rows.items()
                     if key.startswith('message:') and row['source_characters'] and not row['replacements']]
        self.assertEqual(remaining, [])


if __name__ == '__main__': unittest.main()
