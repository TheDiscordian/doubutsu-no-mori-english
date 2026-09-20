"""Complete source callback registration, shared request/wait flow, and retained resources."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
import v3_player_actions as actions
from tests import test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_REWARD_ACTIONS_BUILD','build/v3-shared-reward-actions-01')


class RewardActionHostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_requests_wait_and_source_continuation(self):self.sanitized('v3_reward_actions_test.c')


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current reward-action proposal required')
class RewardActionCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.r=cls.e['player_actions']['reward_actions'];cls.blob=cls.files[BLOB].extract(cls.rom)
        cls.oldblob=cls.before[BLOB].extract(cls.base)

    def test_source_native_and_complete_callback_registration(self):
        source=actions.Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        core=self.files[CODE_VROM].extract(self.rom);owner=self.files[actions.PLAYER_VROM].extract(self.rom)
        binding=actions.reward_action_bindings(source,core,owner,original,self.old['player_actions'])
        self.assertEqual(json.loads(json.dumps(binding)),self.r['bindings'])
        bad=bytearray(core);bad[0x800B1C84-CODE_RAM]^=1
        with self.assertRaises(ValueError):actions.reward_action_bindings(source,bad,owner,original,self.old['player_actions'])
        original_function=source.function
        def changed(at):
            raw,row=original_function(at);return bytes([raw[0]^1])+raw[1:],row
        with patch.object(source,'function',side_effect=changed),self.assertRaises(ValueError):
            actions.reward_action_bindings(source,core,owner,original,self.old['player_actions'])
        self.assertEqual(self.e['player_actions']['enabled_imported_actions'],[109,118,119,120])
        self.assertEqual(len(self.r['callbacks']),12)
        module=self.blob[self.e['blob_offset']:self.e['blob_offset']+self.e['bytes']]
        for row in self.r['callbacks']:
            self.assertEqual(struct.unpack_from('>I',module,row['offset'])[0],row['target'])
        for table in self.e['player_actions']['tables']:
            data=module[table['offset']:table['offset']+table['bytes']]
            self.assertEqual(sha256(data),table['sha256'])
            if table['width']==4:
                for index in self.e['player_actions']['disabled_indices']:
                    self.assertEqual(struct.unpack_from('>I',data,index*4)[0],0)
        self.assertFalse(self.r['ordinary_acquisition_installed'])

    def test_only_declared_code_and_callbacks_change(self):
        start=self.e['blob_offset'];module=bytearray(self.blob[start:start+self.e['bytes']])
        old=self.oldblob[start:start+self.old['bytes']]
        for key,offset,directory in (('requests','request_code_offset','reward_requests'),('wait','wait_code_offset','reward_wait')):
            code=(OUTPUT/directory/'code.bin').read_bytes();at=self.r[offset]
            self.assertEqual(module[at:at+len(code)],code);self.assertEqual(sha256(code),self.r[key]['sha256'])
            self.assertFalse(any(old[at:at+len(code)]));module[at:at+len(code)]=old[at:at+len(code)]
        for row in self.r['callbacks']:module[row['offset']:row['offset']+4]=bytes(4)
        self.assertEqual(module,old);self.assertEqual(len(self.blob),len(self.oldblob))
        for v in self.files.keys()-{BLOB,MODULE,0x19D40}:
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base),hex(v))
        for key in ('save_runtime','save_codec','save_warning','translation_baseline'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(self.e['optional_selection'],self.old['optional_selection'])

    def test_composition_patch_and_future_resource_tail(self):
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
