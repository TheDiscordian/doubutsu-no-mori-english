"""Installed bank ownership, retained acquisition consumers, and private profiles.

These checks inspect cartridge bytes and source/host composition. They do not
execute banking in the game or perform native FlashRAM I/O.
"""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from textbanks import Bank
from v3_asset_loader import BLOB
from v3_bank_link import RAM,ART,END
from v3_bank_resources import PAIRS,menu_allocation
from v3_furniture_install import inputs
from v3_furniture_capacity import checked as checked_capacity,MODEL_BYTES
from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE
import v3_physical_resources as physical

CURRENT=ROOT/'build/v3-post-office-bank-installed-05'
BASE=ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations'


class BankInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base,cls.prior=inputs(BASE/'build-lock.json')
        cls.image,cls.report=inputs(CURRENT/'build-lock.json')
        cls.files=by_vrom(cls.image);cls.before=by_vrom(cls.base)
        cls.e=cls.report['equipment_resources'];cls.bank=cls.e['bank']

    def test_complete_shared_startup_packet_and_unchanged_art(self):
        r=self.bank;p=r['packet'];old=r['previous_packet']
        raw=self.image[p['physical']:p['physical']+p['bytes']]
        self.assertEqual(len(raw),END-p['ram']);self.assertEqual(len(raw),245824)
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual(raw[RAM-p['ram']:],(ROOT/r['linked']/'bank-packet.bin').read_bytes())
        restored=bytearray(raw[:old['bytes']])
        self.assertEqual(len(r['saved_redirects']),46)
        for redirect in r['saved_redirects']:
            at=redirect['address']-p['ram']
            self.assertEqual(restored[at:at+8].hex(),redirect['after'])
            restored[at:at+8]=bytes.fromhex(redirect['before'])
        self.assertEqual(restored,self.base[old['physical']:old['physical']+old['bytes']])
        self.assertEqual(self.image[old['physical']:old['physical']+old['bytes']],restored)
        self.assertIn({k:old[k] for k in ('id','physical','bytes','sha256')},self.report['physical_resources'])
        for parent in (self.e['carried_items']['quest'],self.e['carried_items']['quest']['npc'],
                self.e['carried_items']['quest']['rewards'],self.e['carried_items']['spawning'],
                self.e['carried_items']['paper']['quantities']):
            self.assertEqual(parent['packet'],p)
        blob=self.files[BLOB].extract(self.image);boot=self.e['surface_bootstrap']['code']
        self.assertEqual((boot['bytes'],boot['packet_stride'],boot['packet_count']),(676,16,23))
        first=self.e['blob_offset']+boot['symbols']['packets']-self.e['ram']
        descriptors=[struct.unpack_from('>4I',blob,first+i*16) for i in range(23)]
        matches=[row for row in descriptors if row[0]==p['ram']]
        self.assertEqual(len(matches),1);ram,source,size,crc=matches[0]
        self.assertEqual((ram,source,size),(p['ram'],p['physical']|0x80000000,p['bytes']))
        self.assertEqual(u32(blob,self.e['blob_offset']+crc-self.e['ram']),p['crc32'])
        physical.verify(self.image,self.report['physical_resources'])
        self.assertFalse(r['native_execution_verified']);self.assertFalse(r['ordinary_gameplay_verified'])
        self.assertFalse(r['selectable']);self.assertFalse(r['account_mode']['profile_control_installed'])
        self.assertEqual(raw[r['account_mode']['address']-p['ram']],0)

    def test_format_twenty_one_native_redirects_and_independent_saved_owner(self):
        r=self.bank;active=self.report['save_codec']['active_storage_code']
        self.assertEqual(self.report['save_codec']['format_version'],21)
        self.assertEqual(self.report['clothing']['save_extension']['format_version'],21)
        self.assertEqual(self.report['room_surfaces']['save']['disk_format_version'],21)
        self.assertEqual(self.e['carried_items']['quest']['save_format'],21)
        self.assertEqual(self.e['carried_items']['quest']['wire_version'],7)
        self.assertEqual(active,r['code'])
        self.assertEqual(self.report['save_codec']['card_storage_code'],active)
        self.assertEqual(self.e['console_storage']['card_runtime'],active)
        self.assertEqual(self.e['diaries']['memory']['scratch'],dict(ram=0x80682000,bytes=120416))
        self.assertEqual(r['memory']['account'],dict(ram=0x807E9080,bytes=64,record_bytes=48,guard_bytes=16))
        self.assertIn('-DAF_V3_BANK_STORAGE=1',active['flags'])
        self.assertIn('-DAF_BANK_STATE_RAM=0x807E9080u',active['flags'])
        self.assertTrue(set(self.prior['save_codec']['active_storage_code']['flags'])<=set(active['flags']))
        self.assertEqual(active['symbols']['af_v3_card_state'],0x807C9000)
        self.assertTrue(all(RAM<=row['target']<RAM+active['bytes'] for row in r['saved_redirects']))
        self.assertEqual(self.bank['loaded_packet']['bytes'],END-RAM)
        self.assertIn('even with banking disabled',self.report['save_warning'])
        self.assertTrue(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertEqual(self.report['save_runtime']['state_bytes'],self.prior['save_runtime']['state_bytes'])
        self.assertEqual(self.report['save_runtime']['bank_account_bytes'],48)

    def test_real_native_resources_text_banks_and_complete_menu_capacity(self):
        r=self.bank;core=self.files[CODE_VROM].extract(self.image)
        self.assertEqual(checked_capacity(self.image,self.report),MODEL_BYTES)
        self.assertEqual(menu_allocation(self.image,self.report),r['menu_allocation'])
        for body,reloc,target,target_rel,_ in PAIRS:
            self.assertNotIn(body,self.files);self.assertNotIn(reloc,self.files)
            self.assertEqual(self.files[target].index,self.before[body].index)
            self.assertEqual(self.files[target_rel].index,self.files[target].index+1)
        for patch in r['april_entries']['core_patches']:
            at=patch['address']-CODE_RAM
            self.assertEqual(core[at:at+len(bytes.fromhex(patch['after']))].hex(),patch['after'])
        self.assertEqual(self.report['campsite_manager']['control_count'],76)
        self.assertEqual(r['april_entries']['daily_type_bound'],118)
        messages=Bank('messages',0,0,self.files[MESSAGE].extract(self.image),self.files[TABLE].extract(self.image)).entries()
        old=Bank('messages',0,0,self.before[MESSAGE].extract(self.base),self.before[TABLE].extract(self.base)).entries()
        cv=self.report['import_storage']['choice_vrom']
        choices=Bank('choices',0,0,self.files[cv].extract(self.image),self.files[CHOICE_TABLE].extract(self.image)).entries()
        previous=Bank('choices',0,0,self.before[cv].extract(self.base),self.before[CHOICE_TABLE].extract(self.base)).entries()
        text=r['text'];self.assertEqual((len(messages),len(choices)),(13248,548))
        self.assertEqual(messages[:13234],old);self.assertEqual(choices[:544],previous)
        for row in text['messages']:self.assertEqual(sha256(messages[row['id']]),row['sha256'])
        for row in text['choices']:self.assertEqual(sha256(choices[row['id']]),row['sha256'])
        for retained in (self.e['passwords']['nook']['dialogue'],self.e['harvest']['text']):
            for row in retained['resources']:
                self.assertEqual(sha256(self.files[row['vrom']].extract(self.image)),row['sha256'])
        for mutation in ('pool','native_resource','descriptor'):
            data=bytearray(self.image)
            at=(self.files[CODE_VROM].pstart+0x800C4B10-CODE_RAM if mutation=='pool' else
                self.files[PAIRS[0][2]].pstart if mutation=='native_resource' else
                self.files[0x7749C0].pstart+r['menu_allocation']['offset'])
            data[at]^=1
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):checked_capacity(data,self.report)

    def test_follow_on_category_retains_bank_allocation_without_recompiling_art(self):
        from v3_furniture_pipeline import Source
        from v3_furniture_install import STABLE,STABLE_SHA
        import v3_garden_runtime as garden
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        linked=self.report['catalogue']['linked_code']
        suffix=(ROOT/'build/v3-holiday-card-prize-imports-01/cartridge/catalogue/code.bin').read_bytes()
        self.assertEqual(sha256(suffix),linked['sha256']);stable=STABLE.read_bytes()
        self.assertEqual(sha256(stable),STABLE_SHA)
        with tempfile.TemporaryDirectory(prefix='v3-bank-category-',dir=ROOT/'build') as temp:
            with patch.object(garden,'compile_part',return_value=(suffix,copy.deepcopy(linked))):
                changes,catalogue=garden.install_catalogue(self.image,stable,self.report,
                    copy.deepcopy(self.report['furniture']['imports']+[self.report['speed_bag']]),
                    Path(temp),source.rel,source.symbols.encode(),
                    reviewed_rows=copy.deepcopy(self.report['catalogue']['imports']))
        self.assertNotIn(CODE_VROM,changes)
        self.assertEqual(catalogue['retained_submenu_pool_patches'],self.report['catalogue']['retained_submenu_pool_patches'])
        self.assertEqual(catalogue['category_pool_patch'],self.report['catalogue']['category_pool_patch'])

    def test_private_browser_offline_profiles_preserve_n64_default_and_staged_gates(self):
        import v3_optional_composition as composition
        import v3_browser_composition as browser
        from v3_creature_choices import options
        composition.use_build_lock(CURRENT/'build-lock.json')
        catalog=composition.catalogue(self.image,self.report);choices=options(self.image,self.report)
        self.assertEqual(len(catalog),298)
        self.assertEqual(len(self.report['staged_furniture']['rows']),23)
        self.assertTrue({row['id'] for row in self.report['staged_furniture']['rows']}.isdisjoint(catalog))
        self.assertFalse(any('bank' in row['id'] or 'post-office' in row['id'] for row in choices))
        requests=(('empty',[],{}),('ordinary',['GAFE01-r0/item/2320'],{}),
            ('holiday',['GAFE01-r0/item/30A8'],{}),('holiday-gc',['GAFE01-r0/item/3378'],{'holiday-calendar':'GameCube'}),
            ('all',list(catalog),{}))
        cases=[];p=self.bank['packet'];mode=p['physical']+self.bank['account_mode']['address']-p['ram']
        for name,requested,behaviours in requests:
            selection=composition.resolve(catalog,requested,behaviour_options=choices,behaviours=behaviours)
            result,_,_=composition.compose(self.image,self.report,catalog,selection)
            if name=='empty':self.assertEqual(sha256(result),composition.stable_reference(self.report)[1])
            else:self.assertEqual(result[mode],0)
            if name=='all':self.assertEqual(result,self.image)
            cases.append(dict(name=name,requested=requested,behaviours=behaviours,
                selection=selection,sha256=sha256(result)))
        plan=browser.rules(self.image,self.report)
        self.assertIn('Format-21',plan['save_compatibility'])
        with tempfile.TemporaryDirectory(prefix='v3-bank-browser-') as temp:
            fixture=Path(temp)/'fixture.json'
            write_new(fixture,json.dumps(dict(plan=plan,cases=cases,
                base=str(CURRENT/'animal-forest-v3-asset-loader.z64'),
                stable=str(composition.stable_reference(self.report)[0]))).encode())
            run=subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(fixture)],
                cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())


if __name__=='__main__':unittest.main()
