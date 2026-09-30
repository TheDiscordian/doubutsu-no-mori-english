"""Shared seasonal stock runtime and current installed-cartridge bindings."""
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256, u32
import v3_optional_composition as composer
from v3_asset_loader import BLOB
from v3_creature_choices import options as behaviour_options
from v3_import_scope import PIPELINE, availability
from v3_seasonal_stock import CONTRACTS, END, GUARD, RAM, checksum_field, option, update_report


class SeasonalStockHostTests(unittest.TestCase):
    def test_shared_modes_selection_boundaries_rng_and_guards(self):
        with tempfile.TemporaryDirectory(prefix='v3-seasonal-host-') as directory:
            exe = Path(directory)/'stock'
            subprocess.run(['cc','-std=c11','-O1','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                str(ROOT/'overlays/v3/seasonal_stock.c'),
                str(ROOT/'tests/fixtures/v3_seasonal_stock_host.c'),'-o',str(exe)],
                check=True,capture_output=True,timeout=30)
            result = subprocess.run([str(exe)],check=True,capture_output=True,text=True,timeout=10)
            self.assertIn('7680 cases pass',result.stdout)


class SeasonalStockCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lock = ROOT/os.environ.get('V3_SEASONAL_STOCK_LOCK',
            'build/v3-seasonal-stock-installed-03/build-lock.json')
        if not cls.lock.exists(): raise unittest.SkipTest('Current seasonal cartridge required')
        cls.previous = (composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI)
        composer.use_build_lock(cls.lock)
        cls.image, cls.report = composer.inputs()
        cls.owner = cls.report['equipment_resources']['seasonal_stock']
        cls.catalog = composer.catalogue(cls.image, cls.report)
        cls.choices = behaviour_options(cls.image, cls.report)
        cls.base = (ROOT/'build/v3-scene-arena-installed-03/animal-forest-v3-asset-loader.z64').read_bytes()
        cls.prior = json.loads((ROOT/'build/v3-scene-arena-installed-03/build.json').read_bytes())

    @classmethod
    def tearDownClass(cls):
        composer.BASE, composer.BASE_SHA, composer.REPORT_SHA, composer.ABI = cls.previous

    def test_exact_call_preserves_complete_native_functions_and_delay_slot(self):
        core = bytearray(by_vrom(self.image)[CODE_VROM].extract(self.image))
        hook = self.owner['hook']; at = hook['address']-CODE_RAM
        self.assertEqual(u32(core,at),hook['after'])
        self.assertEqual(u32(core,at+4),hook['delay_slot'])
        struct.pack_into('>I',core,at,hook['before'])
        for start,end,digest in CONTRACTS:
            self.assertEqual(sha256(core[start-CODE_RAM:end-CODE_RAM]),digest)

    def test_packet_crc_aliases_guard_and_every_retained_byte(self):
        e = self.report['equipment_resources']; p = self.owner['packet']; old = self.prior['equipment_resources']['console_storage']['packet']
        raw = bytearray(self.image[p['physical']:p['physical']+p['bytes']])
        self.assertEqual(sha256(raw),p['sha256'])
        self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual(raw[END-16-p['ram']:END-p['ram']],struct.pack('>4I',*([GUARD]*4)))
        raw[RAM-p['ram']:END-p['ram']] = bytes(END-RAM)
        self.assertEqual(raw,self.base[old['physical']:old['physical']+old['bytes']])
        self.assertEqual(e['console_storage']['packet'],p)
        self.assertEqual(e['private_save_bank']['packet'],p)
        self.assertEqual(e['scene_arena']['packet'],p)
        boot = e['surface_bootstrap']['code']
        self.assertEqual((boot['symbols']['harvest_crc']-boot['symbols']['packets'])//16,23)
        self.assertFalse(self.owner['artwork_changed'])
        self.assertFalse(self.owner['saved_format_changed'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(checksum_field(self.image,self.report)[0]['start'],p['physical'])
        self.assertEqual(option(self.image,self.report)['ram'],0x804F37F0)

    def test_independent_selections_modes_and_missing_provider(self):
        rows = self.owner['source']['imports']; keys = [r['id'] for r in rows]
        self.assertEqual({r['donor_item_id'] for r in rows},{'327C','3298'})
        self.assertEqual(self.owner['source']['native_fallback'],[0x1220,0x1224])
        self.assertEqual(self.owner['source']['donor_single_slot_probability_hex'],'3f000000')
        self.assertTrue(all(availability(self.catalog,self.report)[key]['selectable'] for key in keys))
        bad = copy.deepcopy(self.report); bad['equipment_resources']['seasonal_stock']['installed'] = False
        self.assertTrue(all(not availability(self.catalog,bad)[key]['selectable'] for key in keys))
        field = option(self.image,self.report); crc = checksum_field(self.image,self.report)[0]
        for mode in ('N64','GameCube'):
            for selected in ([keys[0]], [keys[1]], keys):
                selection = composer.resolve(self.catalog,selected,scope=PIPELINE,report=self.report,
                    behaviour_options=self.choices,behaviours={'late-december-stock':mode})
                result, _, _ = composer.compose(self.image,self.report,self.catalog,selection)
                self.assertEqual(u32(result,field['offset']),field['values'][mode])
                packet = result[crc['start']:crc['start']+crc['length']]
                self.assertEqual(u32(result,crc['offset']),zlib.crc32(packet))
                receipt = copy.deepcopy(self.report)
                update_report(result,receipt,selection['behaviours'])
                e = receipt['equipment_resources']; p = e['seasonal_stock']['packet']
                self.assertEqual(p['sha256'],sha256(packet))
                self.assertEqual(p['crc32'],zlib.crc32(packet))
                self.assertEqual(e['console_storage']['packet'],p)
                self.assertEqual(e['private_save_bank']['packet'],p)
                self.assertEqual(e['scene_arena']['packet'],p)
                self.assertEqual(e['seasonal_stock']['choice']['resolved'],mode)
                self.assertEqual(next(r for r in receipt['physical_resources'] if r['id']==p['id'])['sha256'],p['sha256'])
        damaged = bytearray(self.image); damaged[field['offset']+3] = 1
        with self.assertRaisesRegex(ValueError,'seasonal stock choice'):
            option(damaged,self.report)

    def test_complete_patch_reconstruction(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(self.lock.parent/'asset-loader.ups').read_bytes()),self.image)


if __name__ == '__main__': unittest.main()
