"""Installed parent-sensitive joint category and optional composition."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs,checked_assets
from v3_furniture_pipeline import Source,prepare,rig_import_plan
import v3_furniture_needle as needle
import v3_room_carry_native as carry
import v3_room_rig_runtime as runtime


class NeedleDispatcherTests(unittest.TestCase):
    def test_shared_dispatch_and_actual_carrying_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-needle-binding-') as directory:
            binary=Path(directory)/'test'
            args=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-ffp-contract=off',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-DAF_GOODS_ROTATE_LOW=0xEF000FD9u','-DAF_GOODS_ROTATE_HIGH=3u','-DAF_V3_ROOM_NEEDLE',
                'tests/v3_room_carry_native_test.c','overlays/v3/room_carry_native.c',
                'overlays/v3/room_carry.c','overlays/v3/room_goods.c','-lm','-o',str(binary)]
            run=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('preview, and matrix lifetime pass',run.stdout)


class NeedleInstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_NEEDLE_BUILD','build/v3-parent-needle-imports-02/cartridge')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-room-carry-native-runtime-01/build-lock.json')
        cls.files=by_vrom(cls.image);cls.blob=cls.files[BLOB].extract(cls.image)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.rows=cls.report['automatic_furniture']['imports']

    def test_complete_installed_category_and_preserved_resources(self):
        bindings=runtime.bind_profiles(self.source,self.image,self.report)
        e=self.report['equipment_resources'];room=e['room_rigs'];packet=room['packet']
        self.assertEqual(room['needle_contract'],needle.native_contract(self.image,self.report))
        self.assertTrue(room['needle_contract']['parent_binding_installed'])
        row=next(r for r in room['rows'] if r['source_item_id']=='3064')
        self.assertEqual((row['mode'],row['first'],row['last']),(6,4,0))
        self.assertTrue(row['profile_installed'] and row['parent_selectable'])
        self.assertFalse(bindings['3064']['staged'])
        self.assertEqual(row['bytes'],3008)
        self.assertEqual(sha256(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']]),row['sha256'])
        prepared=json.loads((ROOT/'build/v3-joint-callback-rigs-prepared-01/art.json').read_bytes())
        art=next(r for r in prepared['objects'] if r['item_id']=='3064')
        self.assertEqual(row['sha256'],art['object_sha256'])
        self.assertEqual(sha256(self.blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]),packet['sha256'])
        self.assertLessEqual(room['code']['bytes'],32768)
        self.assertLessEqual(room['bootstrap']['bytes'],1536)
        self.assertEqual(e['room_carry'],self.prior['equipment_resources']['room_carry'])
        self.assertEqual(e['room_goods'],self.prior['equipment_resources']['room_goods'])
        for r in self.prior['equipment_resources']['room_rigs']['rows']:
            retained=next(x for x in room['rows'] if x['source_item_id']==r['source_item_id'])
            self.assertEqual(retained,r)
        for vrom in (carry.VROM,carry.RELOC,0x8576C0,0x858960):
            self.assertEqual(self.files[vrom].extract(self.image),by_vrom(self.base)[vrom].extract(self.base))
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['save_codec']['format_version'],4)
        item=next(r for r in self.rows if r['item_id']=='3064')
        self.assertEqual(item['name'],'compass');self.assertFalse(item['catalogue_orderable'])
        self.assertEqual(item['donor_list'],'ftr_listJonason')
        self.assertIn(item['id']+'/name',{r['id'] for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']})
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_missing_parent_dependency_and_changed_installed_bytes_reject(self):
        binding=carry.checked_binding(self.image,self.report)
        self.assertEqual(set(binding['exports']),{'af_v3_carry_parent','af_v3_carry_angle'})
        bad=copy.deepcopy(self.report);del bad['equipment_resources']['room_carry']
        with self.assertRaisesRegex(ValueError,'moving-table'):needle.native_contract(self.image,bad)
        for vrom,offset in ((carry.VROM,0x809471CC-carry.RAM),
                (BLOB,self.report['equipment_resources']['room_carry']['packet']['blob_offset'])):
            self.assertFalse(self.files[vrom].pend)
            bad=bytearray(self.image);bad[self.files[vrom].pstart+offset]^=1
            with self.assertRaises(ValueError):carry.checked_binding(bad,self.report)
        parts=prepare(self.source,0x3064)
        inventory={'rows':[dict(item_id='3064',asset_ready=True,installed=False,
            profile=parts[0],categories=['joint-callback-rig-assets'])]}
        plan=rig_import_plan(inventory,self.prior,{},source=self.source)
        self.assertIn('3064',plan['profiles'])
        old=copy.deepcopy(self.prior);del old['equipment_resources']['room_carry']
        blocked=rig_import_plan(inventory,old,{},source=self.source)
        self.assertNotIn('3064',blocked['profiles'])
        runtime.bind_profiles(self.source,self.image,self.report)
        # Full source metadata is compared in the same JSON representation as
        # the generated record, including integer relocation keys.
        rows,_=checked_assets(self.out.parent/'assets',self.source,ROOT/'build/item-identity-megasheet.xlsx')
        self.assertEqual(rows[0][0]['item_id'],'3064')

    def test_private_browser_and_offline_selections_match(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
