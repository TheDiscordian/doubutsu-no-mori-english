"""Shared collection tails: source rules, exact native hooks, and optional output."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
import v3_player_actions as actions
from tests import test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_REWARD_PICKUP_BUILD','build/v3-shared-reward-pickup-01')


class RewardPickupHostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_completion_selection_priority_and_rejection(self):self.sanitized('v3_reward_pickup_test.c')


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current pickup proposal required')
class RewardPickupCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.r=cls.e['player_actions']['reward_pickup'];cls.blob=cls.files[BLOB].extract(cls.rom)
        cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_source_and_complete_native_bindings(self):
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        owner=self.before[actions.PLAYER_VROM].extract(self.base)
        start=self.old['blob_offset'];module=self.oldblob[start:start+self.old['bytes']]
        binding=actions.reward_pickup_bindings(source,owner,original,self.old['player_actions'],module)
        self.assertEqual(json.loads(json.dumps(binding)),self.r['bindings'])
        bad=bytearray(owner);bad[0x808D2A58-actions.PLAYER_RAM]^=1
        with self.assertRaises(ValueError):
            actions.reward_pickup_bindings(source,bad,original,self.old['player_actions'],module)
        original_function=source.function
        def changed(at):
            raw,row=original_function(at);return bytes([raw[0]^1])+raw[1:],row
        with patch.object(source,'function',side_effect=changed),self.assertRaises(ValueError):
            actions.reward_pickup_bindings(source,owner,original,self.old['player_actions'],module)
        bad=bytearray(module);row=next(r for r in self.old['player_actions']['tables'] if r['native_entry']==0x808DDA18)
        struct.pack_into('>I',bad,row['offset']+62*4,0x808D251C)
        with self.assertRaises(ValueError):
            actions.reward_pickup_bindings(source,owner,original,self.old['player_actions'],bad)

    def test_exact_tails_relocations_and_retained_resources(self):
        start=self.e['blob_offset'];module=bytearray(self.blob[start:start+self.e['bytes']])
        old=self.oldblob[start:start+self.old['bytes']];at=self.r['code_offset']
        code=(OUTPUT/'reward_pickup/code.bin').read_bytes()
        self.assertEqual(module[at:at+len(code)],code);self.assertEqual(sha256(code),self.r['code']['sha256'])
        self.assertFalse(any(old[at:at+len(code)]));module[at:at+len(code)]=bytes(len(code))
        self.assertEqual(module,old);self.assertEqual(len(self.blob),len(self.oldblob))
        owner=bytearray(self.files[actions.PLAYER_VROM].extract(self.rom))
        previous=self.before[actions.PLAYER_VROM].extract(self.base)
        for row in self.r['patches']:
            at=row['address']-actions.PLAYER_RAM;after=bytes.fromhex(row['after']);before=bytes.fromhex(row['before'])
            self.assertEqual(owner[at:at+28],after);self.assertEqual(previous[at:at+28],before)
            owner[at:at+28]=before
        self.assertEqual(owner,previous)
        oldrel=self.before[actions.PLAYER_RELOC].extract(self.base)
        rel=self.files[actions.PLAYER_RELOC].extract(self.rom)
        oldrows=actions.native_references(previous,oldrel)[2]
        newrows=actions.native_references(self.files[actions.PLAYER_VROM].extract(self.rom),rel)[2]
        self.assertEqual(len(self.r['removed_relocations']),8)
        self.assertEqual(newrows,[r for r in oldrows if r not in self.r['removed_relocations']])
        expected=bytearray(oldrel);struct.pack_into('>I',expected,16,len(newrows))
        expected[20:20+len(oldrows)*4]=struct.pack('>'+str(len(newrows))+'I',*newrows)+bytes(32)
        self.assertEqual(rel,expected)
        for v in self.files.keys()-{BLOB,MODULE,0x19D40,actions.PLAYER_VROM,actions.PLAYER_RELOC}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        for key in ('save_runtime','save_codec','save_warning','translation_baseline'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(self.e['optional_selection'],self.old['optional_selection'])
        self.assertEqual(self.e['player_actions']['tables'],self.old['player_actions']['tables'])

    def test_composition_patch_and_future_tail(self):
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
