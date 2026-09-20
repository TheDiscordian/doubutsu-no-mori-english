"""Shared deferred exchange behaviour and exact native integration."""
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

OUTPUT=ROOT/os.environ.get('V3_REWARD_EXCHANGE_BUILD','build/v3-shared-reward-exchange-02')


class RewardExchangeHostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_deferred_request_setup_and_timing(self):self.sanitized('v3_reward_deferred_test.c')
    def test_exchange_conditions_placement_and_warnings(self):self.sanitized('v3_reward_exchange_test.c')


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current exchange proposal required')
class RewardExchangeCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.r=cls.e['player_actions']['reward_exchange'];cls.blob=cls.files[BLOB].extract(cls.rom)
        cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_source_and_complete_native_bindings(self):
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        data=[self.before[v].extract(self.base) for v in (CODE_VROM,actions.PLAYER_VROM,0x3950000)]
        binding=actions.reward_exchange_bindings(source,*data,original,self.old['player_actions'],self.old['wrapped_presents'])
        self.assertEqual(json.loads(json.dumps(binding)),self.r['bindings'])
        original_function=source.function
        def changed(at):
            raw,row=original_function(at);return bytes([raw[0]^1])+raw[1:],row
        with patch.object(source,'function',side_effect=changed),self.assertRaises(ValueError):
            actions.reward_exchange_bindings(source,*data,original,self.old['player_actions'],self.old['wrapped_presents'])
        for index,at,ram in ((0,0x800B2008,actions.CODE_RAM),(1,0x808D251C,actions.PLAYER_RAM),(2,0x80873ADC,0x8086F310)):
            bad=list(data);bad[index]=bytearray(bad[index]);bad[index][at-ram]^=1
            with self.assertRaises(ValueError):
                actions.reward_exchange_bindings(source,*bad,original,self.old['player_actions'],self.old['wrapped_presents'])

    def test_exact_code_hooks_callbacks_and_resource_retention(self):
        start=self.e['blob_offset'];module=bytearray(self.blob[start:start+self.e['bytes']])
        old=self.oldblob[start:start+self.old['bytes']]
        for name,row in self.r['codes'].items():
            at=row['offset'];code=(OUTPUT/name/'code.bin').read_bytes()
            self.assertEqual(module[at:at+len(code)],code);self.assertEqual(sha256(code),row['code']['sha256'])
            self.assertFalse(any(old[at:at+len(code)]));module[at:at+len(code)]=bytes(len(code))
        self.assertEqual(len(self.r['callbacks']),4)
        for row in self.r['callbacks']:
            at=row['offset'];self.assertEqual(struct.unpack_from('>I',module,at)[0],row['after'])
            struct.pack_into('>I',module,at,row['before'])
        self.assertEqual(module,old);self.assertEqual(len(self.blob),len(self.oldblob))
        for v in (CODE_VROM,actions.PLAYER_VROM,0x3950000):
            current=bytearray(self.files[v].extract(self.rom));previous=self.before[v].extract(self.base)
            for row in self.r['patches']:
                if row['vrom']!=v:continue
                at=row['address']-row['ram'];before=bytes.fromhex(row['before']);after=bytes.fromhex(row['after'])
                self.assertEqual(current[at:at+len(after)],after)
                self.assertEqual(previous[at:at+len(before)],before);current[at:at+len(before)]=before
            self.assertEqual(current,previous)
        for v in self.files.keys()-{BLOB,MODULE,0x19D40,CODE_VROM,actions.PLAYER_VROM,0x3950000}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        for key in ('save_runtime','save_codec','save_warning','translation_baseline'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(self.e['optional_selection'],self.old['optional_selection'])
        self.assertFalse(self.r['balloon_release_installed'])

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
