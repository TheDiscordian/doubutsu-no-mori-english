"""Complete donor base points, bounded evaluator, and ordinary bulk integration."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_VROM, by_vrom, sha256, apply_ups
from v3_asset_loader import MODULE
from v3_furniture_install import inputs, scoring
from v3_furniture_scoring import install
from v3_furniture_pipeline import Source
from v3_hra_birth import donor_categories, checked_categories, extend_current, ENTRY, END
import v3_hra as hra
import v3_hra_mail as mail
import v3_hra_series as series
import v3_optional_composition as composer
import v3_browser_composition as browser

OUT = ROOT/'build/v3-birth-scoring-runtime-02'


class FurnitureScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.report = inputs(OUT/'build-lock.json')
        cls.base, cls.prior = inputs(OUT/'base-lock.json')
        cls.files, cls.before = by_vrom(cls.image), by_vrom(cls.base)
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_installation_preserves_all_previous_scoring_and_bounds(self):
        core = bytearray(self.before[CODE_VROM].extract(self.base))
        module = bytearray(self.before[MODULE].extract(self.base))
        owners, report = install(self.base, self.prior, core, module)
        for vrom, payload in owners.items():
            self.assertEqual(payload, self.files[vrom].extract(self.image))
        self.assertEqual(report['hra'], self.report['hra'])
        self.assertEqual(self.report['hra_birth'],self.report['hra']['birth_extension'])
        self.assertEqual(core, self.files[CODE_VROM].extract(self.image))
        self.assertEqual(module[0x48:0x68], self.files[MODULE].extract(self.image)[0x48:0x68])
        data, old = owners[hra.NEW_VROM], self.before[hra.NEW_VROM].extract(self.base)
        hr, previous = self.report['hra'], self.prior['hra']
        for key in ('metadata_address', 'metadata_sha256', 'imports', 'series', 'theme_extension', 'score_letters', 'pointer_changes'):
            self.assertEqual(hr[key], previous[key])
        ext=hr['birth_extension'];points,mapping=donor_categories(self.source)
        self.assertEqual((ext['count'],ext['stack_bytes']),(27,296))
        self.assertEqual(ext['added_points'],[1983,1300,1177,1400])
        self.assertEqual((ext['count']-3)%4,0);self.assertLessEqual(ext['count'],32)
        at=ext['points_address']-hra.RAM
        self.assertEqual(data[at:at+108],struct.pack('>27I',*points))
        original=previous['birth_extension']['points_address']-hra.RAM
        self.assertEqual(data[at:at+92],old[original:original+92])
        self.assertEqual(data[original:original+92],old[original:original+92])
        for p in ext['patches']:
            a = p['address']-hra.RAM; self.assertEqual(struct.unpack_from('>I', old, a)[0], p['before'])
            self.assertEqual(struct.unpack_from('>I', data, a)[0], p['after'])
        self.assertEqual(len(data)-len(old),112)
        self.assertLessEqual(len(data), 32768)
        self.assertLessEqual(len(data)+len(owners[hra.NEW_RELOC]), 0x8800)
        damaged = bytearray(old); damaged[ENTRY-hra.RAM] ^= 1
        with self.assertRaisesRegex(ValueError, 'complete native birth'):
            extend_current(damaged, self.before[hra.NEW_RELOC].extract(self.base), previous, self.source)
        changed=copy.deepcopy(hr);changed['birth_extension']['donor_to_native'][35]=3
        with self.assertRaisesRegex(ValueError,'complete birth category map'):checked_categories(data,changed,self.source)
        changed=bytearray(data);changed[ENTRY-hra.RAM+8]^=1
        changed_report=copy.deepcopy(hr);changed_report['output_sha256']=sha256(changed)
        with self.assertRaisesRegex(ValueError,'birth evaluator instruction'):checked_categories(changed,changed_report,self.source)
        self.assertEqual(checked_categories(data,hr,self.source)[0],mapping)
        window=hr['surface_scoring']['window'];a=window['address']-hra.RAM
        self.assertEqual(data[a:a+window['bytes']].hex(),window['after'])
        self.assertEqual(hr['surface_scoring']['evaluator_sha256'],sha256(data[ENTRY-hra.RAM:END-hra.RAM]))

    def test_source_mapping_and_real_donor_rows_use_the_ordinary_installer(self):
        points,mapping=donor_categories(self.source)
        donor=struct.unpack('>38I',self.source.raw('mMkRm_birth_point_table'))
        self.assertEqual(mapping[:23],list(range(23)))
        self.assertEqual((points[7],donor[7]),(2951,1029))
        for i in range(38):
            if i!=7:self.assertEqual(points[mapping[i]],donor[i])
        self.assertEqual(mapping[33],3);self.assertEqual(mapping[37],3)
        rows=[]
        for index in (1053,1204,1214,1127,1054):
            value=struct.unpack_from('>I',self.source.data,0x4FAFC+index*4)[0]
            birth=value>>8&63;category=mapping[birth];series=value>>26;surface=value>>6&3
            rows.append(dict(item_id=f'{0x3000+(index-1024)*4:04X}',runtime_index=index,
                donor_birth_category=birth,birth_category=category,series=series,surface=surface,
                donor_hra_hex=f'{value:08x}',native_hra_hex=f'{(value&0xFFFFC000)|(category<<9)|(surface<<7):08x}',
                donor_series_hex=self.source.raw('mMkRm_series_info')[series*3:series*3+3].hex(),
                feng_hex=self.source.data[0x4EBF0+index*2:0x4EBF0+index*2+2].hex()))
        changes,reports=scoring(self.image,self.report,rows,self.source)
        old=self.files[hra.NEW_VROM].extract(self.image);expected=bytearray(old)
        for row in rows:
            a=self.report['hra']['metadata_address']-hra.RAM+row['runtime_index']*4
            expected[a:a+4]=bytes.fromhex(row['native_hra_hex'])
        self.assertEqual(changes[hra.NEW_VROM],expected)
        self.assertTrue(all(not r['acquisition_category_changed'] for r in reports['hra']['automatic_scoring_aliases'][-len(rows):]))
        # Metadata preparation must never authorise a larger category on an
        # older evaluator, or accept an arbitrary low-bucket substitution.
        with self.assertRaisesRegex(ValueError,'installed native counter'):scoring(self.base,self.prior,rows,self.source)
        bad=copy.deepcopy(rows);bad[1]['birth_category']=3
        with self.assertRaisesRegex(ValueError,'installed native counter'):scoring(self.image,self.report,bad,self.source)
        bad=copy.deepcopy(rows);bad[1]['native_hra_hex']='d4050600'
        with self.assertRaisesRegex(ValueError,'complete donor birth conversion'):scoring(self.image,self.report,bad,self.source)

    def test_unchanged_selection_save_profiles_and_browser_composition(self):
        for key in ('save_runtime', 'save_codec', 'catalogue', 'equipment_resources'):
            self.assertEqual(self.report[key], self.prior[key])
        self.assertEqual({k:v for k,v in self.report['room_surfaces'].items() if k!='scoring'},
                         {k:v for k,v in self.prior['room_surfaces'].items() if k!='scoring'})
        self.assertEqual(self.files[mail.VROM].extract(self.image),self.before[mail.VROM].extract(self.base))
        pin = composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json')
            choices = composer.catalogue(self.image, self.report)
            self.assertEqual(len(choices), 148)
            cases = []
            for name, requested in (('none', []), ('all', list(choices)), ('one', ['GAFE01-r0/item/33A0'])):
                selection = composer.resolve(choices, requested)
                result = composer.compose(self.image, self.report, choices, selection)[0]
                if name == 'none': self.assertEqual(sha256(result), self.report['translation_baseline']['sha256'])
                if name == 'all': self.assertEqual(result, self.image)
                cases.append(dict(name=name, requested=requested, selection=selection, sha256=sha256(result)))
            with tempfile.TemporaryDirectory(prefix='v3-scoring-browser-') as temp:
                path = Path(temp)/'fixture.json'
                path.write_bytes(composer.canonical(dict(plan=browser.rules(self.image, self.report), cases=cases,
                    base=str(OUT/'animal-forest-v3-asset-loader.z64'), stable=str(composer.stable_reference(self.report)[0]))))
                run = subprocess.run(['node', '--experimental-global-webcrypto', str(ROOT/'tests/v3_browser_equivalence.mjs'), str(path)],
                    capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(len(json.loads(run.stdout)['passed']), 3)
        finally:
            composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI = pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), (OUT/'asset-loader.ups').read_bytes()), self.image)


if __name__ == '__main__': unittest.main()
