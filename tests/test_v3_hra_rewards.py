"""Source-faithful HRA acquisition, compiled calls, and cartridge admission."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_furniture_install import inputs,catalogue_record,order_mask
from v3_furniture_pipeline import Source,ReviewRequired
from v3_asset_loader import BLOB,MODULE
import v3_hra_rewards as rewards


class HraSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rel=ROOT/'build/gamecube/files/foresta.rel.szs.decoded'
        if not rel.is_file():raise unittest.SkipTest('Local donor required')
        cls.source=Source(rel.read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_original_reward_contract(self):
        contract=rewards.donor_contract(self.source)
        self.assertEqual(contract['rewards'],[
            dict(item=0x3024,index=1033,points=70000,flag=8,template=0x221),
            dict(item=0x3028,index=1034,points=100000,flag=4,template=0x222)])
        self.assertFalse(contract['catalogue_orderable'])
        self.assertEqual(len(contract['functions']),3)

    def test_unbound_rewards_are_not_shop_substitutes(self):
        source=copy.copy(self.source);source.hra_acquisition=None
        for reward in rewards.donor_contract(source)['rewards']:
            with self.assertRaisesRegex(ReviewRequired,'original HRA reward delivery'):
                rewards.furniture(source,reward['item'],reward['index'],[])

    def test_bound_original_reward_metadata_and_nonordering(self):
        source=copy.copy(self.source);source.hra_acquisition=rewards.donor_contract(source)
        for reward in source.hra_acquisition['rewards']:
            row=rewards.furniture(source,reward['item'],reward['index'],[])
            self.assertEqual(row['stock_group'],255)
            self.assertEqual(row['reward_route'],0)
            self.assertFalse(row['ordinary_stock'])
            self.assertFalse(row['catalogue_orderable'])
            self.assertEqual(row['hra_acquisition']['dependencies'],[])
            record=dict(item_id=f'{reward["item"]:04X}',
                donor_acquisition_list=row['donor_list'],catalogue_orderable=False,
                hra_acquisition=row['hra_acquisition'])
            self.assertTrue(rewards.catalogue_source(source,reward['item'],reward['index'],record))
            self.assertEqual(order_mask(record),0)
            record['catalogue_orderable']=True
            self.assertFalse(rewards.catalogue_source(source,reward['item'],reward['index'],record))
            with self.assertRaises(ValueError):
                rewards.furniture(source,reward['item'],reward['index'],[('ftr_listA','invalid')])

    def test_changed_compiled_donor_is_rejected(self):
        source=copy.copy(self.source);original=source.function
        def changed(at):
            raw,receipt=original(at)
            return bytes([raw[0]^1])+raw[1:],receipt
        source.function=changed
        with self.assertRaisesRegex(ValueError,'complete source HRA'):
            rewards.donor_contract(source)


class HraInstalledTests(HraSourceTests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        lock=Path(os.environ.get('V3_HRA_REWARD_LOCK',
            ROOT/'build/v3-travel-hra-rewards-installed-05/build-lock.json'))
        if not lock.is_file():raise unittest.SkipTest('Current HRA reward cartridge required')
        cls.image,cls.report=inputs(lock)
        cls.files=by_vrom(cls.image)

    def test_complete_connected_installed_controller_and_creator(self):
        binding=rewards.checked(self.source,self.image,self.report)
        self.assertEqual(binding['rewards'],rewards.donor_contract(self.source)['rewards'])
        self.assertTrue(binding['native_delivery_installed'])
        self.assertEqual(rewards.verify_installed_items(self.image,self.report),
                         rewards.installed_items(self.report))

    def test_selection_calls_use_indices_not_item_ids(self):
        control=self.report['hra']['model_rewards']['controller']
        data=self.files[rewards.owner.NEW_VROM].extract(self.image)
        calls=[r for r in control['calls'] if r['symbol']=='af_hra_import_selected']
        self.assertEqual(len(calls),2)
        self.assertEqual([u32(data,r['offset']+4) for r in calls],
                         [0x34040409,0x3404040A])
        self.assertEqual(control['code']['bytes'],516)
        self.assertEqual(len(data),32592)

    def test_changed_native_dependency_is_rejected(self):
        core=bytearray(self.files[CODE_VROM].extract(self.image))
        core[0x8009CBDC-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'native HRA reward dependency'):
            rewards.native_contract(core)

    def test_changed_actual_reader_is_rejected(self):
        image=bytearray(self.image);image[self.files[BLOB].pstart+0x5800]^=1
        with self.assertRaisesRegex(ValueError,'import-selection reader'):
            rewards.checked(self.source,image,self.report)

    def test_changed_creator_loader_is_rejected(self):
        image=bytearray(self.image);image[self.files[MODULE].pstart+0x48+4]^=1
        with self.assertRaisesRegex(ValueError,'letter creator or loader'):
            rewards.checked(self.source,image,self.report)

    def test_checked_scene_guard_is_required_for_real_creator_allocations(self):
        import v3_npc_mail_heap as heap
        receipt=heap.checked(self.image,self.report)
        self.assertFalse(receipt['mail_rules_changed'])
        self.assertFalse(receipt['saved_format_changed'])
        self.assertTrue(receipt['exclusive_borrow_required'])
        image=bytearray(self.image)
        image[self.files[MODULE].pstart+heap.START-0x801948E0]^=1
        with self.assertRaisesRegex(ValueError,'scene-allocation guard'):
            rewards.checked(self.source,image,self.report)

    def test_loader_guard_retains_native_failure_and_cleanup(self):
        import v3_npc_mail_heap as heap
        words=struct.unpack('>13I',heap.patch())
        self.assertEqual((words[0],words[2]),(0x02602025,0x02002825))
        self.assertEqual((words[1]&0x3FFFFFF)<<2,heap.RAM&0x0FFFFFFF)
        self.assertEqual(heap.START+16+(words[3]&65535)*4,heap.FAIL)
        self.assertEqual(heap.START+24+(words[5]&65535)*4,heap.END)
        self.assertEqual(words[4],0x3C028009)

    def test_retained_creator_has_no_unrelated_changes(self):
        mail=self.report['hra']['score_letters'];extension=mail['reward_creator']
        creator=self.files[rewards.mail.VROM].extract(self.image)
        original=bytearray(creator[:extension['prefix_bytes']])
        original[rewards.SCORE_ENTRY:rewards.SCORE_ENTRY+8]=bytes.fromhex(extension['before'])
        original+=bytes.fromhex(extension['previous_relocation'])
        self.assertEqual(sha256(original),rewards.CREATOR_SHA)
        self.assertLessEqual(len(creator),65536)

    def test_retained_room_audio_compiler_receipt_is_authenticated(self):
        from v3_room_creature_audio import checked_binding
        self.assertTrue(checked_binding(self.source,self.image,self.report))
        changed=copy.deepcopy(self.report)
        changed['equipment_resources']['creature_audio']['table']['compiled_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'startup-loaded creature sound arrays'):
            checked_binding(self.source,self.image,changed)


if __name__=='__main__':unittest.main()
