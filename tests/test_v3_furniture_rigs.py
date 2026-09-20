"""Shared indexed room-rig discovery, complete conversion, and install boundary."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
import v3_furniture_pipeline as pipeline
import v3_furniture_rigs as rigs
import v3_keyframes as keyframes
import v3_furniture_install as install
from tests import test_v3_furniture_pipeline as furniture_tests

OUTPUT = ROOT/'build/v3-indexed-room-rigs-prepared-01'


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = pipeline.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.aliases = [r for r in pipeline.room_aliases(cls.source)['rows'] if r['category']=='balloon']

    def test_complete_category_crosses_source_ranges_without_native_identity_assignment(self):
        self.assertEqual(len(self.aliases),8)
        profiles = [self.source.profile(int(r['display_item_id'],16)) for r in self.aliases]
        self.assertEqual({r['callback_adapter']['selected_index'] for r in profiles},set(range(8)))
        self.assertEqual({r['callback_adapter']['index_origin'] for r in profiles},{1020})
        for row in profiles:
            self.assertEqual(row['kind'],'animated-room-model')
            adapter = row['callback_adapter']
            self.assertEqual(adapter['category'],rigs.CATEGORY)
            self.assertEqual((row['skeleton']['joints'],row['skeleton']['shown_joints']),(6,5))
            self.assertEqual(adapter['animation']['duration'],61)
            self.assertFalse(adapter['runtime_installed'])
            self.assertEqual(set(adapter['functions']),{'create','move','draw','destroy'})
            self.assertEqual(len(adapter['joint_callbacks']),2)
            self.assertEqual(len(row['models']),5)
        worksheet = ROOT/'build/item-identity-megasheet.xlsx'
        defaults = pipeline.identity_rows(worksheet)
        self.assertNotIn(0x1FF0,defaults)
        extra = {int(r['display_item_id'],16) for r in self.aliases}
        identities = pipeline.identity_rows(worksheet,extra_items=extra)
        self.assertEqual(set(identities)-set(defaults),{0x1FF0,0x1FF4,0x1FF8,0x1FFC})
        for alias in self.aliases:
            item = int(alias['display_item_id'],16)
            name = pipeline.name_metadata(self.source,item,identities[item])
            self.assertEqual(name['name'],alias['parent_name'])
            self.assertEqual(name['name_sha256'],alias['parent_name_sha256'])
            with self.assertRaises(pipeline.ReviewRequired):
                pipeline.metadata(self.source,item,self.source.profile(item),identities[item])
        for bad in (True,0x1FF1,0x2000,0x2FFC,0x33C8):
            with self.assertRaises(ValueError):pipeline.furniture_source_index(bad)

    def test_full_callback_code_and_relocated_dependencies_are_required(self):
        profile = self.source.profile(0x1FF0); adapter = profile['callback_adapter']
        for role,row in adapter['functions'].items():
            source = copy.copy(self.source); source.rel = bytearray(source.rel)
            source.rel[source.sections[1][0]+row['offset']] ^= 1
            with self.subTest(role=role), self.assertRaises(ValueError):source.profile(0x1FF0)
        for role,row in adapter['functions'].items():
            source = copy.copy(self.source); source.code_relocations = dict(source.code_relocations)
            source.code_relocations[row['offset']+2] = (4,1,5,0)
            with self.subTest(dependencies=role), self.assertRaises(ValueError):source.profile(0x1FF0)
        for row in adapter['joint_callbacks']:
            source = copy.copy(self.source); source.rel = bytearray(source.rel)
            source.rel[source.sections[1][0]+row['offset']+3] = 0
            with self.assertRaisesRegex(ValueError,'joint callback'):source.profile(0x1FF0)
        for constant in adapter['constants'].values():
            source = copy.copy(self.source); source.rel = bytearray(source.rel)
            source.rel[source.sections[constant['section']][0]+constant['offset']] ^= 1
            with self.assertRaisesRegex(ValueError,'speed constant'):source.profile(0x1FF0)
        for table in adapter['tables'].values():
            source = copy.copy(self.source); source.relocations = dict(source.relocations)
            del source.relocations[table['offset']+4]
            source.relocation_addresses = sorted(source.relocations)
            with self.assertRaisesRegex(ValueError,'incomplete rig table'):source.profile(0x1FF0)
        for index in (1019,1028):
            with self.assertRaisesRegex(ValueError,'selector index'):
                self.source.callback_models(profile['profile_offset'],index)

    def test_animation_suffix_offsets_keep_complete_arrays_and_native_pointers(self):
        motion = self.source.profile(0x1FF0)['callback_adapter']['animation']
        plain,original = keyframes.compile_animations(self.source,[motion])
        shifted,report = keyframes.compile_animations(self.source,[motion],start=0x2000)
        expected = bytearray(plain)
        for r in original['relocations']:
            struct.pack_into('>I',expected,r['offset'],0x06002000+r['target_offset'])
        self.assertEqual(shifted,expected)
        self.assertEqual(len(shifted),len(plain))
        for a,b in zip(original['arrays']+original['headers'],report['arrays']+report['headers']):
            self.assertEqual(b['native_offset'],a['native_offset']+0x2000)
            self.assertEqual(b['source_sha256'],a['source_sha256'])
        for bad in (-16,1,0x1000000,True):
            with self.assertRaises(ValueError):keyframes.compile_animations(self.source,[motion],start=bad)


@unittest.skipUnless((OUTPUT/'art.json').is_file(),'Current room-rig conversion required')
class PreparedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        SourceTests.setUpClass.__func__(cls)

    def test_complete_models_rigs_and_animations_match_real_source(self):
        report = json.loads((OUTPUT/'art.json').read_bytes())
        inventory = json.loads((OUTPUT/'inventory.json').read_bytes())
        self.assertEqual(report['format'],'AFV3-AUTO-FURNITURE-PREPARED-ASSETS-1')
        self.assertFalse(report['runtime_installed'])
        self.assertEqual({r['item_id'] for r in report['objects']},{r['display_item_id'] for r in self.aliases})
        for row in report['objects']:
            item = int(row['item_id'],16)
            asset = (OUTPUT/row['object_file']).read_bytes()
            profile,body,_,_,_,_,sections = pipeline.prepare(self.source,item)
            artwork_size = (len(body)+sum(n for _,n in sections)+15)&~15
            suffix,receipt = rigs.suffix(self.source,profile,row['model_offsets'],start=artwork_size)
            self.assertEqual(asset[artwork_size:],suffix)
            self.assertEqual(len(asset),artwork_size+rigs.estimated_suffix(self.source,profile,artwork_size))
            self.assertEqual(row['rig'],json.loads(json.dumps(receipt)))
            self.assertEqual(row['profile'],json.loads(json.dumps(profile)))
            self.assertEqual(sha256(asset),row['object_sha256'])
            self.assertLessEqual(len(asset),9216)
            self.assertFalse(row['import_ready']);self.assertTrue(row['pending_reason'])
            self.assertTrue(row['room_alias']['room_placement_uses_display'])
            for r in receipt['skeleton']['relocations']+receipt['animations']['relocations']:
                self.assertEqual(struct.unpack_from('>I',asset,r['offset'])[0],0x06000000+r['target_offset'])
            for r in receipt['animations']['arrays']:
                at,n,source = r['native_offset'],r['bytes'],r['donor_offset']
                self.assertEqual(asset[at:at+n],self.source.data[source:source+n])
            scanned = next(r for r in inventory['rows'] if r['item_id']==row['item_id'])
            self.assertTrue(scanned['asset_ready']);self.assertEqual(scanned['status'],'review')
            self.assertNotIn('static-materials',scanned['categories'])
            self.assertNotIn('static-ci4',scanned['categories'])
        furniture_tests.DonorTests.check_complete_artwork(self,OUTPUT,report)
        with self.assertRaisesRegex(ValueError,'Unknown converter/source revision'):
            install.checked_assets(OUTPUT,self.source,ROOT/'build/item-identity-megasheet.xlsx')
