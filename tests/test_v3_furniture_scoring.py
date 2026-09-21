"""Complete donor themes, official names, bounded owners, and optional output."""
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
from v3_furniture_install import inputs
from v3_furniture_scoring import install
from v3_furniture_pipeline import Source
import v3_hra as hra
import v3_hra_mail as mail
import v3_hra_series as series
import v3_optional_composition as composer
import v3_browser_composition as browser

OUT = ROOT/'build/v3-theme-scoring-runtime-02'


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
        self.assertEqual(core, self.files[CODE_VROM].extract(self.image))
        self.assertEqual(module[0x48:0x68], self.files[MODULE].extract(self.image)[0x48:0x68])
        data, old = owners[hra.NEW_VROM], self.before[hra.NEW_VROM].extract(self.base)
        hr, previous = self.report['hra'], self.prior['hra']
        sr = hr['series']; self.assertEqual(sr['count'], 63)
        self.assertEqual((sr['count']-3) % 4, 0); self.assertEqual((sr['count']-1) % 2, 0)
        info = data[sr['info_address']-hra.RAM:sr['info_address']-hra.RAM+63*3]
        self.assertEqual(info[:55*3], old[previous['series']['info_address']-hra.RAM:previous['series']['info_address']-hra.RAM+55*3])
        self.assertEqual(info[55*3:], bytes.fromhex('02004902004a01004d02004c02004b')+b'\xff\0\xff'*3)
        self.assertEqual(data[hra.START:hra.START+4], bytes.fromhex('2ca2003f'))
        # The metadata end and old info start shared an address. Expanding
        # themes must not move the metadata end or its 48 complete references.
        self.assertEqual(hr['pointer_changes'], previous['pointer_changes'])
        for key in ('metadata_address', 'metadata_sha256', 'imports', 'birth_extension', 'surface_scoring'):
            self.assertEqual(hr[key], previous[key])
        for p in hr['theme_extension']['patches']:
            a = p['offset']; self.assertEqual(struct.unpack_from('>I', old, a)[0], p['before'])
            self.assertEqual(struct.unpack_from('>I', data, a)[0], p['after'])
        self.assertLessEqual(len(data), 32768)
        self.assertLessEqual(len(data)+len(owners[hra.NEW_RELOC]), 0x8800)
        damaged = bytearray(old); damaged[0] ^= 1
        with self.assertRaisesRegex(ValueError, 'complete theme'):
            series.extend_current(damaged, self.before[hra.NEW_RELOC].extract(self.base), previous, self.source, self.prior['room_surfaces'])
        changed = copy.deepcopy(self.prior['room_surfaces']); changed['rows'][0]['destination_index'] ^= 1
        with self.assertRaisesRegex(ValueError, 'floor/wall pair'):
            series.extend_current(old, self.before[hra.NEW_RELOC].extract(self.base), previous, self.source, changed)

    def test_official_names_reach_full_letter_table_with_single_catalogue_credit(self):
        lr = self.report['hra']['score_letters']; previous = self.prior['hra']['score_letters']
        data = self.files[mail.VROM].extract(self.image); old = self.before[mail.VROM].extract(self.base)
        at = lr['name_table_address']-mail.RAM
        table = data[at:at+lr['name_rows']*26]
        self.assertEqual(lr['name_rows'], 60)
        self.assertEqual(table[:previous['name_rows']*26], old[at:at+previous['name_rows']*26])
        self.assertEqual(sha256(table), lr['name_table_sha256'])
        provenance = {r['id']: r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
        for index in range(55, 60):
            name = self.source.raw('mMkRm_series_name')[index*16:(index+1)*16]
            self.assertEqual([table[i:i+26] for i in range(0, len(table), 26)].count(name[:10]+name), 1)
            credit = provenance[f'GAFE01-r0/hra/theme/{index}/name']['locales']['en']
            self.assertEqual(credit['credit'], 'official')
            self.assertEqual(credit['source']['reference_sha256'], sha256(name))
        self.assertEqual(data[lr['image_bytes']+20:], old[previous['image_bytes']+20:])
        self.assertEqual(data[0x2A04:0x2A08], bytes.fromhex('24020037'))
        self.assertLessEqual(lr['image_bytes'], 65536)

    def test_unchanged_selection_save_profiles_and_browser_composition(self):
        for key in ('save_runtime', 'save_codec', 'room_surfaces', 'catalogue', 'equipment_resources'):
            self.assertEqual(self.report[key], self.prior[key])
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
