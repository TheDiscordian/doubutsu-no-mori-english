"""Shared parent choices, actual profile bits, category packing, and unchanged code."""
import copy
import ctypes as c
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs
from v3_held_catalogue import select_installed
import v3_optional_composition as composer
from tests import test_v3_optional_composition as shared
from tests.test_v3_save_clothing import reference_pack
from tests.test_v3_save_codec import fixture
from v3_save_clothing import PROFILE,STATE

OUTPUT=ROOT/os.environ.get('V3_HELD_SELECTION_BUILD','build/v3-held-selection-02')

@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current parent-selection reference required')
class HeldSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        composer.use_build_lock(OUTPUT/'build-lock.json')
        shared.OptionalCompositionTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        shared.OptionalCompositionTests.tearDownClass.__func__(cls)
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.previous_pin

    select=shared.OptionalCompositionTests.select

    def test_shared_parent_choices_and_selected_category_counts(self):
        from v3_catalogue import VROM,RAM,UMBRELLA_COUNT
        held={k:r for k,r in self.catalog.items() if r['kind']=='equipment'}
        self.assertEqual(len(held),8)
        self.assertEqual({r['item_id'] for r in held.values()},{f'{i:04X}' for i in range(0x2254,0x225C)})
        chosen=[list(held)[1],list(held)[-1]];selection=self.select(*chosen)
        self.assertEqual(selection['required'],[])
        self.assertEqual(selection,self.select(chosen[1],chosen[0],chosen[1]))
        image,writes,blob=composer.compose(self.base,self.report,self.catalog,selection)
        data=by_vrom(image)[VROM].extract(image);cat=self.report['catalogue']['handheld'];at=cat['table_address']-RAM
        self.assertEqual(struct.unpack_from('>I',data,UMBRELLA_COUNT-RAM)[0],34)
        self.assertEqual(data[at+64:at+80],struct.pack('>8H',2132,2138,0,0,0,0,0,0))
        self.assertEqual(len(selection['enabled']),2)
        profile=bytes.fromhex(selection['profile_hex']);self.assertEqual(sum(n.bit_count() for n in profile),2)
        for key,row in held.items():
            index=(int(row['display_item_id'],16)-0x3000)//4
            self.assertEqual(bool(profile[32+index//8]&(1<<(index&7))),key in chosen)
            self.assertEqual(struct.unpack_from('>I',blob,row['enable_offset'])[0],int(key in chosen))
            with self.assertRaisesRegex(ValueError,'Unknown or unimplemented'):
                self.select(composer.item_key(int(row['display_item_id'],16)))
        self.assertEqual(image,composer.compose(self.base,self.report,self.catalog,self.select(*reversed(chosen)))[0])
        self.assertTrue(any(w['purpose']=='selected equipment iteration/completion count' for w in writes))

    def test_parent_profile_codec_upgrade_and_removal_rejection(self):
        held=[k for k,r in self.catalog.items() if r['kind']=='equipment']
        profile=bytes.fromhex(self.select(held[1],held[-1])['profile_hex'])
        extended=bytes.fromhex(self.select(*held)['profile_hex'])
        missing=bytes.fromhex(self.select(held[1])['profile_hex'])
        original=bytes.fromhex(self.report['save_runtime']['profile_hex'])
        source,_=fixture();state=bytearray(profile+bytes(STATE-PROFILE))
        for player in range(4):
            for key in (held[1],held[-1]):
                index=(int(self.catalog[key]['display_item_id'],16)-0x3000)//4
                state[PROFILE+player*128+index//8]|=1<<(index&7)
        blob=bytes(reference_pack(source,state))
        for current,expected in ((profile,1),(extended,1),(original,1),(missing,-7),(bytes(192),-7)):
            output=c.create_string_buffer(b'\xA5'*(STATE+32),STATE+32)
            bank=c.create_string_buffer(blob)
            result=self.codec.af_v3_save_check(bank,len(blob),c.create_string_buffer(current),c.byref(output,16))
            self.assertEqual(result,expected)
            self.assertEqual(bank.raw[:len(blob)],blob)
            self.assertEqual(output.raw[:16]+output.raw[-16:],b'\xA5'*32)
            self.assertEqual(output.raw[16:-16],current+state[PROFILE:] if result==1 else b'\xA5'*STATE)

    def test_activation_changes_only_profile_and_checked_startup(self):
        prior_rom,prior=inputs(composer.BASE/'base-lock.json');files=by_vrom(self.base);before=by_vrom(prior_rom)
        blob=files[BLOB].extract(self.base);old=before[BLOB].extract(prior_rom)
        expected=bytearray(old);equipment,changes,updates=select_installed(prior,expected)
        self.assertFalse(changes);self.assertEqual(updates['save_runtime'],self.report['save_runtime'])
        self.assertEqual(equipment,self.report['equipment_resources'])
        expected[4:8]=blob[4:8]
        self.assertEqual(expected,blob)
        for v in files.keys()-{BLOB,MODULE,0x19D40}:
            self.assertEqual(files[v].extract(self.base),before[v].extract(prior_rom),hex(v))
        old_module=before[MODULE].extract(prior_rom);module=bytearray(files[MODULE].extract(self.base))
        module[STARTUP:CONFIG+16]=old_module[STARTUP:CONFIG+16]
        self.assertEqual(module,old_module)
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(composer.BASE/'asset-loader.ups').read_bytes()),self.base)
        self.assertEqual(sha256(blob),self.report['blob_sha256'])
        for mutate in ('profile','tag','art','module','missing'):
            damaged=bytearray(old);receipt=copy.deepcopy(prior)
            r=prior['equipment_resources']['catalogue']['imports'][0]
            if mutate=='profile':damaged[0x20+42]|=8
            if mutate=='tag':damaged[int(r['profile_ram'],16)-8-0x80473000+0x200000+79]=2
            if mutate=='art':damaged[int(r['object_vrom'],16)-BLOB]^=1
            if mutate=='module':damaged[prior['equipment_resources']['blob_offset']]^=1
            if mutate=='missing':receipt['equipment_resources'].pop('ground_categories')
            with self.assertRaises(ValueError):select_installed(receipt,damaged)

    def test_copied_town_equipment_fixture_retains_other_saved_fields(self):
        from v3_clothing_gameplay_fixture import create
        from v3_save_codec import BANK, PAYLOAD
        source=(ROOT/'local/rc2-save-report-g3O4lU/test.flash').read_bytes()
        initial=sha256(source)
        rows=self.report['equipment_resources']['parent_readers']['rows']
        for row in (rows[1],rows[-1]):
            item=int(row['item_id'],16)
            data,receipt=create(source,self.base,self.report,equipment_item=item)
            self.assertEqual(receipt['item'],row['item_id'])
            self.assertFalse(receipt['ordinary_acquisition_tested'])
            self.assertFalse(receipt['source_save_modified'])
            self.assertEqual(len(data),len(source))
            for number in range(2):
                old=source[number*BANK:(number+1)*BANK];bank=data[number*BANK:(number+1)*BANK]
                self.assertEqual(bank[0x34:0x36],struct.pack('>H',item))
                self.assertEqual(sum(struct.unpack('>'+str(PAYLOAD//2)+'H',bank[:PAYLOAD]))&65535,0)
                allowed=set(range(4,8))|set(range(0x12,0x14))|{0x34,0x35}|set(range(0x54,0x58))
                self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(old[:PAYLOAD],bank[:PAYLOAD]))))
                state=c.create_string_buffer(STATE)
                profile=bytes.fromhex(self.report['save_runtime']['profile_hex'])
                self.assertEqual(self.codec.af_v3_save_check(c.create_string_buffer(bank),BANK,
                    c.create_string_buffer(profile),state),1)
                ownership=bytearray(STATE-PROFILE)
                index=(int(row['display_item_id'],16)-0x3000)//4
                ownership[index//8]|=1<<(index&7)
                self.assertEqual(state.raw,profile+ownership)
        self.assertEqual(sha256(source),initial)
        for item,shop in ((0x2200,False),(int(rows[0]['item_id'],16),True)):
            with self.assertRaises(ValueError):create(source,self.base,self.report,equipment_item=item,shop_stock=shop)

    def test_event_purchase_fixture_does_not_seed_goods_or_ownership(self):
        from v3_clothing_gameplay_fixture import create
        from v3_save_codec import BANK,PAYLOAD
        source=(ROOT/'local/rc2-save-report-g3O4lU/test.flash').read_bytes()
        data,receipt=create(source,self.base,self.report,event_shop=True)
        self.assertIsNone(receipt['item'])
        self.assertIsNone(receipt['pocket_slot'])
        self.assertFalse(receipt['seeded_ownership'])
        self.assertFalse(receipt['seeded_shop_stock'])
        self.assertFalse(receipt['ordinary_acquisition_tested'])
        profile=bytes.fromhex(self.report['save_runtime']['profile_hex'])
        for number in range(2):
            old=source[number*BANK:(number+1)*BANK];bank=data[number*BANK:(number+1)*BANK]
            self.assertEqual(bank[0x34:0x54],old[0x34:0x54])
            self.assertEqual(bank[0xED22:0xED32],old[0xED22:0xED32])
            self.assertEqual(struct.unpack_from('>I',bank,0x58)[0],10000)
            allowed=set(range(4,8))|set(range(0x12,0x14))|set(range(0x58,0x5C))
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(old[:PAYLOAD],bank[:PAYLOAD]))))
            state=c.create_string_buffer(STATE)
            self.assertEqual(self.codec.af_v3_save_check(c.create_string_buffer(bank),BANK,
                c.create_string_buffer(profile),state),1)
            self.assertEqual(state.raw,profile+bytes(STATE-PROFILE))
        for kwargs in (dict(event_shop=True,shop_stock=True),dict(event_shop=True,equipment_item=0x2255)):
            with self.assertRaises(ValueError):create(source,self.base,self.report,**kwargs)


CATEGORY_OUTPUT=ROOT/os.environ.get('V3_HELD_CATEGORY_BUILD','build/v3-held-category-02')

@unittest.skipUnless((CATEGORY_OUTPUT/'build-lock.json').is_file(),'Current category refresh required')
class CategorySelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.previous_pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        composer.use_build_lock(CATEGORY_OUTPUT/'build-lock.json')
        shared.OptionalCompositionTests.setUpClass.__func__(cls)

    @classmethod
    def tearDownClass(cls):
        shared.OptionalCompositionTests.tearDownClass.__func__(cls)
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.previous_pin

    select=shared.OptionalCompositionTests.select
    test_parent_profile_codec_upgrade_and_removal_rejection=HeldSelectionTests.test_parent_profile_codec_upgrade_and_removal_rejection

    def test_individual_category_selections_and_exact_empty_all(self):
        from v3_catalogue import VROM,RAM,UMBRELLA_COUNT
        held={key:row for key,row in self.catalog.items() if row['kind']=='equipment'}
        self.assertEqual(len(self.catalog),120);self.assertEqual(len(held),16)
        self.assertEqual({r['item_id'] for r in held.values()},{f'{i:04X}' for i in range(0x224C,0x225C)})
        chosen=['GAFE01-r0/item/224C','GAFE01-r0/item/2253','GAFE01-r0/item/2255']
        selected=self.select(*chosen);self.assertEqual(selected['required'],[])
        self.assertEqual(selected,self.select(*reversed(chosen),chosen[0]))
        image,_,blob=composer.compose(self.base,self.report,self.catalog,selected)
        data=by_vrom(image)[VROM].extract(image);cat=self.report['catalogue']['handheld'];at=cat['table_address']-RAM
        self.assertEqual(struct.unpack_from('>I',data,UMBRELLA_COUNT-RAM)[0],35)
        self.assertEqual(struct.unpack_from('>16H',data,at+64),(2132,2139,2146)+13*(0,))
        profile=bytes.fromhex(selected['profile_hex'])
        self.assertEqual(sum(x.bit_count() for x in profile),3)
        for key,row in held.items():
            self.assertEqual(struct.unpack_from('>I',blob,row['enable_offset'])[0],int(key in chosen))
            with self.assertRaises(ValueError):self.select(composer.item_key(int(row['display_item_id'],16)))
        self.assertEqual(composer.compose(self.base,self.report,self.catalog,self.select(*self.catalog))[0],self.base)
        empty=composer.compose(self.base,self.report,self.catalog,self.select())[0]
        self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])

if __name__=='__main__':unittest.main()
