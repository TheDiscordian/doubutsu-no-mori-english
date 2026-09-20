"""Shared balloon release category: source, bounds, hooks and actual behaviour."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
import v3_balloon_release as release
from tests import test_v3_equipment_runtime as shared
OUTPUT=ROOT/os.environ.get('V3_BALLOON_RELEASE_BUILD','build/v3-shared-balloon-release-04')


class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_shared_release_fall_and_native_fallbacks(self):self.sanitized('v3_balloon_release_test.c')
    def test_shared_exchange_balloon_routing(self):
        self.sanitized('v3_reward_exchange_test.c',defines=('-DAF_V3_BALLOON_RELEASE',))


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current balloon release proposal required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.r=cls.e['player_actions']['balloon_release'];cls.blob=cls.files[BLOB].extract(cls.rom)
        cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_complete_source_and_native_api_binding(self):
        source=release.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        core=self.before[CODE_VROM].extract(self.base);owner=self.before[release.PLAYER_VROM].extract(self.base)
        self.assertEqual(json.loads(json.dumps(release.bindings(source,core,owner,original))),self.r['bindings'])
        bad=bytearray(owner);bad[0x808D73EC-release.PLAYER_RAM]^=1
        with self.assertRaises(ValueError):release.bindings(source,core,bad,original)

    def test_exact_hooks_code_bounds_retention_and_no_save_change(self):
        at=self.e['blob_offset'];n=self.e['bytes'];data=bytearray(self.blob[at:at+n]);old=self.oldblob[at:at+n]
        for name,row in self.r['codes'].items():
            a,size=row['offset'],row['code']['bytes']
            if name!='reward_exchange':self.assertFalse(any(old[a:row['end']]))
            self.assertLessEqual(a+size,row['end'])
            self.assertEqual(data[a:a+size],(OUTPUT/name/'code.bin').read_bytes());data[a:row['end']]=old[a:row['end']]
        for row in self.r['callbacks']:
            self.assertEqual(struct.unpack_from('>I',data,row['offset'])[0],row['after'])
            struct.pack_into('>I',data,row['offset'],row['before'])
        self.assertEqual(data,old)
        owner=bytearray(self.files[release.PLAYER_VROM].extract(self.rom))
        for row in self.r['patches']:
            a=row['address']-row['ram'];after=bytes.fromhex(row['after']);before=bytes.fromhex(row['before'])
            self.assertEqual(owner[a:a+len(after)],after);owner[a:a+len(before)]=before
        self.assertEqual(owner,self.before[release.PLAYER_VROM].extract(self.base))
        for v in self.files.keys()-{BLOB,MODULE,0x19D40,release.PLAYER_VROM,release.PLAYER_RELOC}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        rel=self.files[release.PLAYER_RELOC].extract(self.rom);oldrel=self.before[release.PLAYER_RELOC].extract(self.base)
        def entries(b):return list(struct.unpack_from('>'+str(int.from_bytes(b[16:20],'big'))+'I',b,20))
        self.assertEqual(entries(rel),[x for x in entries(oldrel) if x not in self.r['removed_relocations']])
        self.assertEqual(rel[:16],oldrel[:16]);self.assertEqual(len(rel),len(oldrel))
        for key in ('save_runtime','save_codec','save_warning','translation_baseline'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(self.e['optional_selection'],self.old['optional_selection'])
        self.assertEqual(self.e['held_rig_actions'],self.old['held_rig_actions'])

    def test_composition_patch_and_resource_tail(self):
        import v3_optional_composition as composer
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');choices=composer.catalogue(self.rom,self.report)
            self.assertEqual(len(choices),128)
            self.assertEqual(composer.compose(self.rom,self.report,choices,composer.resolve(choices,list(choices)))[0],self.rom)
            self.assertEqual(sha256(composer.compose(self.rom,self.report,choices,composer.resolve(choices,[]))[0]),
                             self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        reuse_resource_tail(self.rom,self.report,self.blob)


if __name__=='__main__':unittest.main()
