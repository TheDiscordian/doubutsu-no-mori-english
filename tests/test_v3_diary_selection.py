"""One connected current-build diary selection/save check; no native execution."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256
import v3_optional_composition as composition
import v3_browser_composition as browser
from v3_diary_selection import bindings, catalogue_key

OUT = ROOT/os.environ.get('V3_DIARY_SELECTION', 'build/v3-diary-category-work-01/catalogue-03')


class DiarySelectionTests(unittest.TestCase):
    def test_complete_bindings_and_current_browser_offline_equivalence(self):
        composition.use_build_lock(OUT/'build-lock.json')
        image, report = composition.inputs()
        rows = bindings(image, report)
        self.assertEqual(len(rows), 16)
        catalog = composition.catalogue(image, report)
        self.assertFalse(rows.keys() & catalog.keys())
        # Exercise the shared resolver on installed bindings, without claiming
        # readiness or bypassing compose's authoritative selectable catalogue.
        all_bits = bytearray(192)
        for style, row in enumerate(rows.values()):
            resolved = composition.resolve({row['id']: row}, [row['id']])
            bits = bytearray(192); bits[32+(63+style)//8] = 1 << ((63+style)&7)
            self.assertEqual(resolved['profile_hex'], bits.hex())
            all_bits[row['profile_byte']] |= row['profile_mask']
        self.assertEqual(composition.resolve(rows, list(rows))['profile_hex'], all_bits.hex())
        # Parent selection drives both complete catalogue packing and scoring;
        # the covers themselves are never independent user choices.
        _, selected_cat = composition.catalogue_selection(image, report, set(rows))
        self.assertEqual({catalogue_key(r) for r in selected_cat['imports']}, set(rows))
        _, selected_scores = composition.scoring_selection(image, report, rows, set(rows))
        self.assertEqual({r['runtime_index'] for r in selected_scores}, set(range(1087,1103)))
        with self.assertRaisesRegex(ValueError, 'unimplemented'):
            composition.resolve(catalog, list(rows))
        forged = {**catalog, **rows}
        with self.assertRaisesRegex(ValueError, 'actual installed bindings'):
            composition.compose(image, report, forged, composition.resolve(forged, list(rows)))
        corrupted = copy.deepcopy(report)
        corrupted['equipment_resources']['diary_items']['profiles'][0]['parent_item_id']='2B00'
        with self.assertRaisesRegex(ValueError, 'binding'):
            bindings(image, corrupted)
        for cat in report['equipment_resources']['diary_items']['catalogue']['imports']:
            self.assertIn(catalogue_key(cat), rows)
            wrong = dict(cat, selection_id='GAFE01-r0/item/30FC')
            with self.assertRaises(ValueError):catalogue_key(wrong)
        plan = browser.rules(image, report)
        self.assertEqual({r['id'] for r in plan['pending_options']}, set(rows))
        self.assertTrue(all(not r['selectable'] for r in plan['pending_options']))
        cases = []
        from v3_creature_choices import options
        choices = options(image, report)
        for name, requested in (('empty', []), ('all-supported', list(catalog)),
                                ('mixed', ['GAFE01-r0/villager/00EB', 'GAFE01-r0/item/2320'])):
            selection = composition.resolve(catalog, requested, behaviour_options=choices)
            result, _, _ = composition.compose(image, report, catalog, selection)
            if requested:
                blob = by_vrom(result)[composition.BLOB].extract(result)
                for r in rows.values():
                    self.assertEqual(blob[r['enable_offset']:r['enable_offset']+4], bytes(4))
                    self.assertFalse(blob[0x20+r['profile_byte']] & r['profile_mask'])
                _, cat = composition.catalogue_selection(image, report, set(selection['enabled']))
                self.assertFalse(any(r.get('representation')=='diary' for r in cat['imports']))
            cases.append(dict(name=name, requested=requested, selection=selection, sha256=sha256(result)))
        self.assertEqual(plan['all_selected_sha256'], cases[1]['sha256'])
        with tempfile.TemporaryDirectory(prefix='v3-diary-selection-') as temp:
            fixture = Path(temp)/'fixture.json'
            fixture.write_text(json.dumps(dict(plan=plan, cases=cases,
                base=str(OUT/'animal-forest-v3-asset-loader.z64'),
                stable=str(composition.stable_reference(report)[0]))))
            run = subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(fixture)],
                cwd=ROOT,capture_output=True,text=True,timeout=90)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_real_carried_readers_save_profile_and_format_eleven_reload(self):
        with tempfile.TemporaryDirectory(prefix='v3-diary-profile-') as temp:
            out=Path(temp)
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections','-fdata-sections',
                '-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1','-DAF_V3_SURFACE_PROFILE=1',
                '-DAF_V3_CREATURE_PROFILE=1','-DAF_V3_INSECT_SEASONS=1','-DAF_V3_DIARY_STORAGE=1']
            commands=[['cc',*flags,'-Daf_v3_save_check=af_console_canonical_check',
                '-Daf_v3_save_pack=af_console_canonical_pack','-c','overlays/v3/save_codec.c','-o',str(out/'codec.o')],
                ['cc',*flags,'-DAF_V3_CONSOLE_STORAGE=1','-Wl,--gc-sections',
                '-Daf_test_diary_item_state=af_save_runtime','-Daf_test_diary_item_players=af_console_players',
                'tests/v3_diary_profile_test.c','overlays/v3/save_runtime.c','overlays/v3/console_storage.c',
                'overlays/v3/save_compressed.c','overlays/v3/diary.c','overlays/v3/diary_items.c',
                'overlays/v3/diary_native.c',str(out/'codec.o'),'-o',str(out/'check')], [str(out/'check')]]
            for command in commands:
                run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(run.returncode,0,run.stdout+run.stderr)
                if run.stdout: print(run.stdout.strip())


if __name__=='__main__':unittest.main()
