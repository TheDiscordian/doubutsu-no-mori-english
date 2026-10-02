"""Explicit feature dependencies and actual carried-item acquisition bindings."""
import copy
import ctypes
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import v3_optional_composition as composer
from v3_feature_choices import options,requests
from v3_password_acquisition import checked,carried_items
from v3_furniture_pipeline import Source
from v3_password_runtime import MAP,POLICY
from v3_asset_loader import BLOB
from aflib import by_vrom


class FeatureChoicesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(ROOT/'build/v3-new-year-checkboxes-installed-03/build-lock.json')
        cls.image,cls.report=composer.inputs()
        cls.catalog=composer.catalogue(cls.image,cls.report)
        cls.features=options(cls.catalog,cls.report)

    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.saved

    def test_feature_drives_items_and_not_the_reverse(self):
        for feature in self.features:
            selection=composer.resolve(self.catalog,[feature['id']],scope='v3-pipeline',report=self.report)
            self.assertEqual(selection['requested'],[feature['id']])
            self.assertTrue(set(feature['required_imports'])<=set(selection['required']))
            for key in feature['required_imports']:
                self.assertIn(feature['id'],selection['dependency_reasons'][key])
                with self.assertRaisesRegex(ValueError,'Select the feature'):
                    composer.resolve(self.catalog,[key],scope='v3-pipeline',report=self.report)
        full=requests(self.catalog,self.features,list(self.catalog))
        for feature in self.features:
            self.assertIn(feature['id'],full)
            self.assertFalse(set(feature['required_imports'])&set(full))

    def test_coconut_and_cedar_use_real_selected_password_destinations(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                      (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        binding=checked(source,self.image,self.report)
        self.assertTrue(binding['native_delivery_installed'])
        keys={'GAFE01-r0/item/2807','GAFE01-r0/item/2901'}
        self.assertTrue(keys<=carried_items(self.report))
        passwords=self.report['equipment_resources']['passwords']
        blob=by_vrom(self.image)[BLOB].extract(self.image)
        packet=blob[passwords['blob_offset']:passwords['blob_offset']+passwords['bytes']]
        with tempfile.TemporaryDirectory(prefix='v3-carried-codes-') as temp:
            library=Path(temp)/'policy.so'
            subprocess.run(['cc','-shared','-fPIC','-O2','-I',str(ROOT/'overlays/v3'),
                str(ROOT/'overlays/v3/password_policy.c'),'-o',str(library)],check=True,capture_output=True)
            lib=ctypes.CDLL(str(library))
            read_type=ctypes.CFUNCTYPE(ctypes.c_uint32,ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32)
            resolve=lib.af_v3_password_resolve
            resolve.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,read_type,ctypes.c_void_p]
            allowed=lib.af_v3_password_allowed
            allowed.argtypes=[ctypes.c_void_p,ctypes.c_uint32,ctypes.c_uint32,ctypes.c_uint32]
            map_bytes=struct.unpack_from('>H',packet,MAP+10)[0]
            policy_bytes=struct.unpack_from('>H',packet,POLICY+8)[0]
            wire=ctypes.create_string_buffer(packet[MAP:MAP+map_bytes])
            policy=ctypes.create_string_buffer(packet[POLICY:POLICY+policy_bytes])
            for row in passwords['source']['destinations']['rows']:
                if row['id'] not in keys:continue
                self.assertEqual(allowed(policy,len(policy)-1,row['source_item'],3),1)
                for enabled in (False,True):
                    read=read_type(lambda _,ram,width: row['enable_mask'] if enabled and ram==row['enable_ram'] and width==row['enable_bytes'] else 0)
                    self.assertEqual(resolve(wire,len(wire)-1,row['source_item'],read,None),row['item'] if enabled else 0)
        missing=copy.deepcopy(self.report)
        missing['equipment_resources']['passwords']['conversation']['native_bindings_installed']=False
        self.assertEqual(carried_items(missing),set())


if __name__=='__main__':unittest.main()
