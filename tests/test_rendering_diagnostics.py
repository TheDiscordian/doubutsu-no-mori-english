"""Complete diagnostic originals retain tested controls and bounded storage."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, verified_rom
from rendering_diagnostics_scenario import APPROVALS, IDS, scenario
from runtime_module import module_command_info
from textbanks import Bank, banks
from textcodec import encode, decode, has_japanese, control_signature
from textvalidate import validate_entry, expanded_bound

BUILD = ROOT/'build/rendering-diagnostics-pilot'


class RenderingDiagnosticSourceTests(unittest.TestCase):
    def test_exact_sources_all_controls_lines_symbols_and_capacity(self):
        rom = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        info = module_command_info(rom)
        source = next(b for b in banks(rom) if b.name == 'message').entries()
        drafts = json.loads(APPROVALS.read_text())
        self.assertEqual(tuple(r['id'] for r in drafts), IDS)
        for row, size, bound in zip(drafts, (330, 389, 835, 584), (346, 405, 851, 750), strict=True):
            old = source[int(row['id'][8:], 16)]; new = encode(row['translation'], info)
            self.assertEqual(sha256(old), row['source_sha256'])
            self.assertEqual(control_signature(old, info), control_signature(new, info))
            self.assertFalse(has_japanese(new, info))
            self.assertEqual((len(new), expanded_bound(new, info)), (size, bound))
            self.assertEqual(new.count(b'\xCD'), old.count(b'\xCD'))
            for glyph in ('♪', '♥'):
                self.assertEqual(decode(old, info).count(glyph), row['translation'].count(glyph))
            validate_entry(old, new, info, 'message')
            broken = new.replace(b'\x7f\x04', b'\x7f\x06', 1)
            with self.assertRaises(ValueError): validate_entry(old, broken, info, 'message')

    def test_complete_last_draft_cannot_be_installed_in_one_buffer(self):
        rom = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        info = module_command_info(rom)
        old = next(b for b in banks(rom) if b.name == 'message').entries()[4]
        row, = json.loads((ROOT/'translations/n64-message-diagnostic.json').read_text())
        new = encode(row['translation'], info)
        self.assertEqual(row['id'], 'message:0004')
        self.assertEqual(sha256(old), row['source_sha256'])
        self.assertEqual(control_signature(old, info), control_signature(new, info))
        self.assertEqual(len(control_signature(new, info)), 62)
        self.assertFalse(has_japanese(new, info))
        self.assertEqual((len(new), expanded_bound(new, info)), (961, 1581))
        self.assertEqual(sha256(new), '529a97e4cb7429444d483e0a6eacb0e38f7db22818bfa40b5ee2f3446c164eba')
        self.assertEqual(row['status'], 'sequence_source')
        with self.assertRaisesRegex(ValueError, '1024'):
            validate_entry(old, new, info, 'message')


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete diagnostic ROM required')
class RenderingDiagnosticCartridgeTests(unittest.TestCase):
    def test_every_previous_edit_and_nonmessage_resource_is_retained(self):
        before, after = [json.loads((ROOT/f'build/{p}-candidates/translations.json').read_text())
                         for p in ('design-items', 'rendering-diagnostics')]
        a, b = [{r['id']: r for r in rows} for rows in (before, after)]
        self.assertEqual((len(a), len(b)), (13763, 13767))
        self.assertEqual(b.keys()-a.keys(), set(IDS))
        self.assertTrue(all(b[key] == row for key, row in a.items()))
        old, new = [(ROOT/f'build/{p}-pilot/animal-forest-halfwidth.z64').read_bytes()
                    for p in ('design-items', 'rendering-diagnostics')]
        x, y = by_vrom(old), by_vrom(new)
        self.assertEqual(x.keys(), y.keys())
        self.assertEqual({key for key in x if x[key].extract(old) != y[key].extract(new)},
                         {0x19D40, 0x2000000, 0xCF9000})
        entries = [Bank('message', 0x2000000, 0xCF9000, files[0x2000000].extract(rom),
                        files[0xCF9000].extract(rom)).entries() for files, rom in ((x, old), (y, new))]
        self.assertEqual({f'message:{i:04X}' for i, (a, b) in enumerate(zip(*entries, strict=True)) if a != b}, set(IDS))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        self.assertEqual(sha256(new), report['output_sha256'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), new)
        plan = scenario(native, new, report)
        self.assertEqual(sum('call' in r for r in plan), 4)
        self.assertEqual({r['call']['address'] for r in plan if 'call' in r}, {'8009E558'})

    def test_combined_credit_adds_only_four_installed_records_not_the_pending_draft(self):
        from translation_progress import measure
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        ledgers = []
        for name in ('design-items', 'rendering-diagnostics'):
            root = ROOT/('build/'+name+'-pilot')
            ledgers.append(measure(native, (root/'animal-forest-halfwidth.z64').read_bytes(),
                                   json.loads((root/'build.json').read_text())))
        a, b = [{key for key, row in ledger.rows.items() if row['replacements']} for ledger in ledgers]
        self.assertEqual(b-a, set(IDS)); self.assertFalse(a-b)
        self.assertNotIn('message:0004', b)
        self.assertEqual([r.summary()['total_source_characters'] for r in ledgers], [751284]*2)


if __name__ == '__main__': unittest.main()
