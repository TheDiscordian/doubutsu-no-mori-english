"""Changed complete-model limits and the ordinary import/composition path."""
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
from aflib import by_vrom, sha256, apply_ups, CODE_VROM, CODE_RAM
from v3_asset_loader import BLOB
from v3_furniture_install import inputs, profile
from v3_furniture_pipeline import Source
from v3_import_storage import ROWS, slot
import v3_furniture_capacity as capacity
import v3_room_rig_runtime as room


class CompleteModelCapacityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        cls.directory = ROOT/os.environ.get('V3_MODEL_CAPACITY_BATCH', 'build/v3-large-model-imports-01')
        cls.batch = json.loads((cls.directory/'pipeline.json').read_bytes())
        cls.out = (ROOT/cls.batch['final_lock']).parent
        cls.image, cls.report = inputs(cls.out/'build-lock.json')
        cls.base, cls.prior = inputs(ROOT/'build/v3-scrolling-category-imports-01/profile-runtime/build-lock.json')
        cls.blob = by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.rows = cls.report['automatic_furniture']['imports']
        cls.source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_model_and_previous_resources_survive_ordinary_import(self):
        from tests.test_v3_furniture_pipeline import DonorTests
        art = json.loads((self.directory/'assets/art.json').read_bytes())
        DonorTests.check_complete_artwork(self, self.directory/'assets', art)
        self.assertEqual(self.batch['imported'], ['31C4'])
        self.assertEqual(self.batch['pending'], [])
        self.assertEqual([r['stage'] for r in self.batch['steps']], ['ordinary-import'])
        row, = self.rows
        self.assertEqual(row['object_bytes'], 10448)
        self.assertEqual(sum(m['triangles'] for m in row['models']), 259)
        self.assertEqual(sum(r['kind'] == 'texture' for r in row['resources']), 13)
        self.assertEqual(row['donor_list'], 'ftr_listKamakura')
        self.assertFalse(row['catalogue_orderable'])
        asset = (self.directory/'assets'/row['object_file']).read_bytes()
        at = int(row['object_vrom'], 16)-BLOB
        self.assertEqual(self.blob[at:at+len(asset)], asset)
        with self.assertRaisesRegex(ValueError, 'bounds'):
            profile(row, int(row['object_vrom'], 16), limit=self.report['import_storage']['virtual_limit'])
        native = profile(row, int(row['object_vrom'], 16),
            limit=self.report['import_storage']['virtual_limit'], model_capacity=capacity.MODEL_BYTES)
        start = ROWS+slot(int(row['item_id'], 16))*80
        self.assertEqual(self.blob[start+8:start+76], native)
        # Large models must not overwrite any earlier complete imported object.
        old_blob = by_vrom(self.base)[BLOB].extract(self.base)
        for old in self.prior['furniture']['imports']:
            if 'object_vrom' in old:
                at = int(old['object_vrom'], 16)-BLOB
                self.assertEqual(self.blob[at:at+old['object_bytes']], old_blob[at:at+old['object_bytes']])
        self.assertEqual(self.report['equipment_resources'], self.prior['equipment_resources'])
        self.assertEqual(self.report['save_codec'], self.prior['save_codec'])
        self.assertEqual({k:v for k,v in self.report['save_runtime'].items() if not k.startswith('profile_')},
            {k:v for k,v in self.prior['save_runtime'].items() if not k.startswith('profile_')})
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()), self.image)

    def test_installed_capacity_and_retained_native_catalogue_allocation(self):
        self.assertEqual(capacity.checked(self.base, self.prior), 9216)
        self.assertEqual(capacity.checked(self.image, self.report), 12288)
        room.bind_profiles(self.source, self.image, self.report)
        self.assertEqual(self.source.model_bank_capacity, 12288)
        receipt = self.report['furniture_capacity']
        self.assertEqual(receipt['additional_resident_bytes'], 307200)
        self.assertEqual(receipt['additional_pool_bytes'], 6144)
        self.assertEqual(self.report['catalogue']['pool_reserved']-self.prior['catalogue']['pool_reserved'], 6144)
        self.assertEqual(self.report['furniture']['bank_pool']['end'], 0x8062C020)
        for mutate in ('flag', 'guard', 'pool', 'digest', 'receipt'):
            bad = copy.deepcopy(self.report)
            if mutate == 'flag': bad['furniture']['expanded_tables']['expanded_code']['flags'].remove('-D'+capacity.FLAG)
            if mutate == 'guard': bad['furniture']['bank_pool']['guard'] -= 16
            if mutate == 'pool': bad['furniture_capacity']['pool_patch']['after'] += 64
            if mutate == 'digest': bad['furniture']['expanded_tables']['expanded_code']['sha256'] = '0'*64
            if mutate == 'receipt': del bad['furniture_capacity']
            with self.assertRaises(ValueError, msg=mutate): capacity.checked(self.image, bad)
        cat = by_vrom(self.image)[capacity.catalogue.VROM].extract(self.image)
        stride = capacity.STRIDE-capacity.catalogue.RAM
        self.assertEqual(struct.unpack_from('>I', cat, stride)[0], 0x24633000)
        native = capacity.catalogue_stride(cat, 12288, 9216)
        retained, _ = capacity.retain_catalogue(self.report, native, {})
        self.assertEqual(retained, cat)
        changed = bytearray(native); changed[capacity.ALLOC_FIRST-capacity.catalogue.RAM] ^= 1
        with self.assertRaisesRegex(ValueError, 'allocation loop'):
            capacity.catalogue_stride(changed, 9216, 12288)
        with self.assertRaisesRegex(ValueError, 'allocation stride'):
            capacity.catalogue_stride(cat, 9216, 12288)
        core = by_vrom(self.image)[CODE_VROM].extract(self.image)
        self.assertEqual(struct.unpack_from('>I', core, capacity.POOL_WORD-CODE_RAM)[0], receipt['pool_patch']['after'])

    def test_changed_dma_limits_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-model-capacity-') as temporary:
            binary = Path(temporary)/'test'
            result = subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_model_capacity_test.c'), '-o', str(binary)],
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn('failed-DMA state pass', result.stdout)

    def test_current_browser_and_offline_selections(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)
