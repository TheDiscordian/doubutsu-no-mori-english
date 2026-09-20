"""Complete flying-balloon category: bounded host behaviour and actual cartridge."""
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
import v3_balloon_actor as actor
from tests import test_v3_equipment_runtime as shared
OUTPUT=ROOT/os.environ.get('V3_BALLOON_ACTOR_BUILD','build/v3-shared-balloon-actor-04')


class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_complete_shared_state_and_failures(self):self.sanitized('v3_balloon_actor_test.c')


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current flying-balloon proposal required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.r=cls.e['player_actions']['balloon_actor'];cls.blob=cls.files[BLOB].extract(cls.rom)
        cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_actual_source_and_complete_resources(self):
        source=actor.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        core=self.before[CODE_VROM].extract(self.base);owner=self.before[actor.PLAYER_VROM].extract(self.base)
        self.assertEqual(json.loads(json.dumps(actor.bindings(source,core,owner,original))),
                         {k:v for k,v in self.r['bindings'].items() if k!='resource_apis'})
        self.assertEqual([(x['entry'],x['helper']) for x in self.r['bindings']['resource_apis']],
            [(0x800B12C8,'af_v3_equipment_pointer'),(0x800B131C,'af_v3_equipment_size'),(0x800B1650,'af_v3_equipment_vrom')])
        bad=bytearray(owner);bad[0x808DD79C-actor.PLAYER_RAM]^=1
        with self.assertRaises(ValueError):actor.bindings(source,core,bad,original)
        self.assertEqual([r['index'] for r in self.r['resources']],list(range(40,50)))
        for row in self.r['resources']:
            a,n=row['blob_offset'],row['bytes'];self.assertEqual(self.blob[a:a+n],self.oldblob[a:a+n])
            self.assertEqual(sha256(self.blob[a:a+n]),row['sha256'])

    def test_exact_installation_and_retained_native_owners(self):
        at=self.e['blob_offset'];n=self.e['bytes'];data=bytearray(self.blob[at:at+n]);old=self.oldblob[at:at+n]
        for a,size in ((self.r['offset'],self.r['code']['bytes']),(self.r['packet_offset'],self.r['packet_bytes'])):
            self.assertFalse(any(old[a:a+size]));data[a:a+size]=bytes(size)
        self.assertEqual(data,old)
        self.assertEqual(self.blob[at+actor.CODE:at+actor.CODE+self.r['code']['bytes']],(OUTPUT/'balloon_actor/code.bin').read_bytes())
        packet=self.blob[at+actor.PACKET:at+actor.PACKET+0x60]
        self.assertEqual(struct.unpack_from('>HHIHHI',packet,32),(0xCB,0x400,0x30,0x2244,3,0x2080))
        for v in (CODE_VROM,actor.PLAYER_VROM):
            data=bytearray(self.files[v].extract(self.rom))
            for row in self.r['patches']:
                if row['vrom']!=v:continue
                a=row['address']-row['ram'];after=bytes.fromhex(row['after']);before=bytes.fromhex(row['before'])
                self.assertEqual(data[a:a+len(after)],after);data[a:a+len(before)]=before
            self.assertEqual(data,self.before[v].extract(self.base))
        for v in self.files.keys()-{BLOB,MODULE,0x19D40,CODE_VROM,actor.PLAYER_VROM,actor.PLAYER_RELOC}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        rel=self.files[actor.PLAYER_RELOC].extract(self.rom);oldrel=self.before[actor.PLAYER_RELOC].extract(self.base)
        def entries(b):return list(struct.unpack_from('>'+str(int.from_bytes(b[16:20],'big'))+'I',b,20))
        self.assertEqual(entries(rel),[x for x in entries(oldrel) if x not in self.r['removed_relocations']])
        self.assertEqual(rel[:16],oldrel[:16]);self.assertEqual(len(rel),len(oldrel))
        for key in ('save_runtime','save_codec','save_warning','translation_baseline'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(self.e['optional_selection'],self.old['optional_selection'])

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
