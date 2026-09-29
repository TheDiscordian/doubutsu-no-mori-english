"""Current six-family selection, resource preservation, and composer agreement."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, u32
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
import v3_optional_composition as composition
import v3_browser_composition as browser
from v3_carried_selection import options, masks, checksum_fields, READY
from v3_carried_runtime import TABLE
from v3_holiday_selection import groups, active
from v3_creature_choices import options as behaviour_options

OUT = ROOT/os.environ.get('V3_CARRIED_SELECTION', 'build/v3-carried-selection-03')


class CarriedSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        composition.use_build_lock(OUT/'build-lock.json')
        cls.image, cls.report = composition.inputs()

    def test_current_cartridge_preserves_all_resources_except_admission_words(self):
        image, report = self.image, self.report
        base, prior = inputs(OUT/'base-lock.json')
        rows = options(image, report)
        self.assertEqual({r['family'] for r in rows.values()}, {0, 2, 3, 4, 5, 6})
        self.assertEqual(report['save_codec']['format_version'], 19)
        self.assertEqual(report['save_runtime']['profile_hex'], prior['save_runtime']['profile_hex'])
        d = report['equipment_resources']['carried_items']; p = d['packet']
        allowed = {p['physical']+TABLE-p['ram']+16, p['physical']+TABLE-p['ram']+20,
                   masks(image, report)[1]['offset']}
        allowed.update(f['offset'] for g in groups(image, report) if g['id']=='carried-quest' for f in g['fields'])
        for record in report['physical_resources']:
            old = next(r for r in prior['physical_resources'] if r['id'] == record['id'])
            self.assertEqual((record['physical'], record['bytes']), (old['physical'], old['bytes']))
            data = bytearray(image[record['physical']:record['physical']+record['bytes']])
            for at in allowed:
                if record['physical'] <= at < record['physical']+record['bytes']:
                    offset = at-record['physical']; data[offset:offset+4] = base[at:at+4]
            self.assertEqual(sha256(data), old['sha256'], record['id'])
        for field in checksum_fields(image, report):
            self.assertEqual(u32(image, field['offset']), zlib.crc32(image[field['start']:field['start']+field['length']]))
        bad = copy.deepcopy(report); bad['equipment_resources']['carried_items']['ready_mask'] |= 2
        with self.assertRaises(ValueError):options(image, bad)

    def test_six_independent_families_and_combined_browser_outputs(self):
        image, report = self.image, self.report
        catalog = composition.catalogue(image, report); rows = options(image, report)
        choices = behaviour_options(image, report); plan = browser.rules(image, report)
        self.assertEqual(len(catalog), 213)
        self.assertNotIn('GAFE01-r0/item/251E', catalog)
        profiles = [('empty', [], {}), ('all', list(catalog), {}),
                    ('six-carried', list(rows), {}),
                    ('six-packs', list(rows), {'paper-quantities':'GameCube'}),
                    ('pack-only', [], {'paper-quantities':'GameCube'})]
        profiles += [(row['name'], [key], {}) for key, row in rows.items()]
        cases = []
        for name, requested, behaviours in profiles:
            selection = composition.resolve(catalog, requested, behaviour_options=choices, behaviours=behaviours)
            result, _, blob = composition.compose(image, report, catalog, selection)
            expected = sum(r['carried_mask'] for key, r in rows.items() if key in selection['enabled'])
            self.assertEqual(selection['carried_mask'], expected)
            if blob is not None:
                fields = masks(image, report)
                self.assertEqual(u32(result, fields[0]['offset']), expected)
                self.assertEqual(u32(result, fields[1]['offset']), (expected >> 2) & 3)
                for group in groups(image, report):
                    on = active(group, selection['enabled'], selection['behaviours'])
                    if name not in ('all',):self.assertEqual(on, bool(expected & (64 if group['id']=='carried-quest' else 12)))
                    for field in group['fields']:
                        self.assertEqual(u32(result, field['offset']), field['enabled'] if on else field['disabled'])
                for field in checksum_fields(image, report):
                    self.assertEqual(u32(result, field['offset']), zlib.crc32(result[field['start']:field['start']+field['length']]))
                # A carried-only profile needs no furniture, villager, or diary bits.
                if name != 'all':self.assertFalse(any(bytes.fromhex(selection['profile_hex'])))
            else:
                self.assertEqual(sha256(result), composition.stable_reference(report)[1])
            cases.append(dict(name=name, requested=requested, behaviours=behaviours,
                              selection=selection, sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-carried-selection-') as temp:
            fixture = Path(temp)/'fixture.json'
            fixture.write_text(json.dumps(dict(plan=plan, cases=cases,
                base=str(OUT/'animal-forest-v3-asset-loader.z64'), stable=str(composition.stable_reference(report)[0]))))
            run = subprocess.run(['node', '--experimental-global-webcrypto',
                'tests/v3_browser_equivalence.mjs', str(fixture)], cwd=ROOT, capture_output=True, text=True, timeout=90)
            self.assertEqual(run.returncode, 0, run.stdout+run.stderr)
            print(run.stdout.strip())


if __name__ == '__main__':unittest.main()
