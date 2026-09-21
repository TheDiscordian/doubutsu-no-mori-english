"""Changed installed password bindings; retain prior codec/policy equivalence."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom, sha256
from v3_asset_loader import BLOB, MODULE
from v3_furniture_install import inputs
import v3_password_runtime as pw

OUTPUT=ROOT/'build/v3-password-runtime-05'
BASE=ROOT/'build/v3-birth-scoring-runtime-02/build-lock.json'


class PasswordRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import v3_optional_composition as optional
        cls.composition_pin=optional.BASE,optional.BASE_SHA,optional.REPORT_SHA,optional.ABI
        cls.image,cls.report=inputs(OUTPUT/'build-lock.json')
        cls.base,cls.prior=inputs(BASE)

    @classmethod
    def tearDownClass(cls):
        import v3_optional_composition as optional
        optional.BASE,optional.BASE_SHA,optional.REPORT_SHA,optional.ABI=cls.composition_pin

    def test_complete_linked_resources_and_unchanged_native_owners(self):
        files=by_vrom(self.image);before=by_vrom(self.base)
        self.assertEqual(set(files),set(before))
        for v,entry in files.items():
            if v not in (BLOB,MODULE,0x19D40):self.assertEqual(entry.extract(self.image),before[v].extract(self.base),hex(v))
            if v != BLOB:self.assertEqual((entry.vstart,entry.vend),(before[v].vstart,before[v].vend))
        blob=files[BLOB].extract(self.image);e=self.report['equipment_resources'];p=e['passwords']
        packet=blob[p['blob_offset']:p['blob_offset']+pw.SIZE]
        ep=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
        old=self.prior['equipment_resources'];old_blob=before[BLOB].extract(self.base)
        predecessor=bytearray(old_blob[old['blob_offset']:old['blob_offset']+old['bytes']])
        code=(OUTPUT/'password_bootstrap/code.bin').read_bytes()
        predecessor[pw.BOOT-e['ram']:pw.BOOT-e['ram']+len(code)]=code
        self.assertEqual(ep,predecessor)
        self.assertEqual(sha256(ep),e['sha256']);self.assertEqual(zlib.crc32(ep),e['crc32'])
        self.assertEqual(sha256(packet),p['sha256']);self.assertEqual(zlib.crc32(packet),p['crc32'])
        self.assertEqual(packet[:p['code']['bytes']],(OUTPUT/'password_runtime/code.bin').read_bytes())
        self.assertLessEqual(p['code']['bytes'],pw.TABLES)
        for row in p['parts']:
            self.assertEqual(sha256(packet[row['offset']:row['offset']+row['bytes']]),row['sha256'])
        self.assertEqual(packet[-16:],struct.pack('>4I',*([0xAF5057DE]*4)))
        self.assertEqual(ep[pw.CACHE-e['ram']:pw.CACHE-e['ram']+4],bytes(4))
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertFalse(p['acquisition_installed']);self.assertFalse(p['keyboard_installed'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],pw.SIZE)
        for path,digest in p['sources'].items():self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)

    def test_source_packets_and_selected_composition_remain_bound(self):
        from v3_furniture_pipeline import Source
        import v3_optional_composition as optional
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        tables,permissions,mapping,receipt=pw.prepared(source,ROOT/'build/v3-password-policy-prepared-03',BASE)
        p=self.report['equipment_resources']['passwords'];blob=by_vrom(self.image)[BLOB].extract(self.image)
        packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(json.loads(json.dumps(receipt)),p['source'])
        for at,data in ((pw.TABLES,tables),(pw.POLICY,permissions),(pw.MAP,mapping)):
            self.assertEqual(packet[at:at+len(data)],data)
        optional.use_build_lock(OUTPUT/'build-lock.json')
        catalogue=optional.catalogue(self.image,self.report)
        self.assertEqual(len(catalogue),148)
        actual,_=pw.policy.destination_map(OUTPUT/'build-lock.json')
        self.assertEqual(actual,mapping)

    def test_loader_failure_and_cache_order_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-password-loader-',dir=ROOT/'build') as temp:
            binary=Path(temp)/'test'
            result=subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O1','-g',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_password_bootstrap_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            print(result.stdout.strip())

    def test_browser_none_all_and_individual_preserve_password_engine(self):
        import v3_optional_composition as optional
        import v3_browser_composition as browser
        optional.use_build_lock(OUTPUT/'build-lock.json')
        catalog=optional.catalogue(self.image,self.report)
        plan=browser.rules(self.image,self.report);cases=[]
        for name,ids in (('none',[]),('all',list(catalog)),('one',['GAFE01-r0/item/261A'])):
            selection=optional.resolve(catalog,ids)
            image,_,_=optional.compose(self.image,self.report,catalog,selection)
            if ids:
                p=self.report['equipment_resources']['passwords'];blob=by_vrom(image)[BLOB].extract(image)
                self.assertEqual(sha256(blob[p['blob_offset']:p['blob_offset']+p['bytes']]),p['sha256'])
            else:self.assertEqual(sha256(image),'a09373b051cbcd93991e5dd6cb17a238a2afb1e2e2d7694d75408d24a55d4eee')
            cases.append(dict(name=name,requested=ids,selection=selection,sha256=sha256(image)))
        with tempfile.TemporaryDirectory(prefix='v3-password-composition-',dir=ROOT/'build') as tmp:
            fixture=Path(tmp)/'fixture.json'
            fixture.write_bytes(optional.canonical(dict(plan=plan,cases=cases,
                base=str(OUTPUT/'animal-forest-v3-asset-loader.z64'),
                stable=str(optional.stable_reference(self.report)[0]))))
            result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(fixture)],
                capture_output=True,text=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(len(json.loads(result.stdout)['passed']),3)
