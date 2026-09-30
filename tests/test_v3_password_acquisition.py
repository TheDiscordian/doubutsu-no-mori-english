"""Source-wide password admission and retained-owner validation.

These checks do not establish ordinary controller entry or animated delivery.
"""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source,ReviewRequired
from v3_password_acquisition import checked,furniture

BASE=ROOT/os.environ.get('V3_PASSWORD_ACQUISITION_BASE','build/v3-nook-password-installed-11')
CURRENT=ROOT/os.environ.get('V3_PASSWORD_ACQUISITION_CURRENT','build/v3-password-only-imports-01/password-destinations')


class PasswordAcquisitionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(BASE/'build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.binding=checked(cls.source,cls.image,cls.report)

    def test_complete_source_categories_without_stock_substitution(self):
        self.source.password_acquisition=self.binding
        homepage=struct.unpack('>6H',self.source.raw('ftr_listHomePage'))
        self.assertEqual(homepage[-1],0)
        ids=[(item,(item-0x1000)//4,[('ftr_listHomePage','')]) for item in homepage[:-1]]
        for index,birth in enumerate(self.source.raw('mRmTp_birth_type')):
            if birth==34:
                ids.append((0x1000+index*4 if index<1024 else 0x3000+(index-1024)*4,index,[]))
        self.assertEqual(len(ids),16)
        for item,index,lists in ids:
            with self.subTest(item=f'{item:04X}'):
                row=furniture(self.source,item,index,lists)
                self.assertIsNotNone(row)
                self.assertFalse(row['ordinary_stock'])
                self.assertFalse(row['catalogue_orderable'])
                self.assertEqual(row['stock_group'],255)
                self.assertEqual(row['reward_route'],0)
                self.assertTrue(row['password_acquisition']['native_delivery_installed'])
                self.assertFalse(row['password_acquisition']['ordinary_gameplay_tested'])
                self.assertEqual(row['password_acquisition']['permission_mask'],self.binding['matrix'][item])
        self.source.password_acquisition=None
        with self.assertRaisesRegex(ReviewRequired,'complete native Nook'):
            furniture(self.source,homepage[0],(homepage[0]-0x1000)//4,[('ftr_listHomePage','')])

    def test_missing_frontend_never_grants_admission(self):
        r=copy.deepcopy(self.report)
        r['equipment_resources']['passwords']['conversation']['native_bindings_installed']=False
        with self.assertRaisesRegex(ValueError,'complete native frontend'):
            checked(self.source,self.image,r)
        r['equipment_resources']['passwords']['acquisition_installed']=False
        self.assertIsNone(checked(self.source,self.image,r))

    def test_font_cannot_overlap_carrying_or_storage(self):
        for owner in ('room_carry','console_storage'):
            r=copy.deepcopy(self.report)
            font=r['equipment_resources']['passwords']['nook']['font']
            size=font['pixels_end']-font['pixels_ram']
            font['pixels_ram']=r['equipment_resources'][owner]['packet']['ram']
            font['pixels_end']=font['pixels_ram']+size
            with self.assertRaisesRegex(ValueError,'overlaps a retained RAM owner'):
                checked(self.source,self.image,r)

    def test_changed_password_packet_rejects(self):
        r=self.report;p=r['equipment_resources']['passwords']
        at=by_vrom(self.image)[BLOB].pstart+p['blob_offset']
        image=bytearray(self.image);image[at]^=1
        with self.assertRaisesRegex(ValueError,'complete password acquisition packet'):
            checked(self.source,image,r)

    def test_catalogue_and_editor_reservations_remain_checked(self):
        from v3_furniture_capacity import checked as capacity
        self.assertEqual(capacity(self.image,self.report),12288)
        r=copy.deepcopy(self.report);r['password_editor']['additional_menu_pool_bytes']+=64
        with self.assertRaisesRegex(ValueError,'password-editor menu reservation'):
            capacity(self.image,r)
        r=copy.deepcopy(self.report)
        r['catalogue']['conservative_pool_required']=r['catalogue']['pool_reserved']+1
        with self.assertRaisesRegex(ValueError,'retained submenu reservation'):
            capacity(self.image,r)

    def test_checked_diary_hooks_preserve_original_contact_and_carrying(self):
        from v3_furniture_contact import native_contract
        from v3_room_carry_native import checked_binding
        self.assertEqual(len(native_contract(self.image,self.report)['blocks']),6)
        self.assertTrue(checked_binding(self.image,self.report)['exports'])
        with self.assertRaisesRegex(ValueError,'contact_layers'):
            native_contract(self.image)
        r=copy.deepcopy(self.report);r['equipment_resources']['diaries']['room']['target']+=4
        with self.assertRaisesRegex(ValueError,'diary contact binding'):
            native_contract(self.image,r)
        r=copy.deepcopy(self.report)
        r['equipment_resources']['room_goods']['compiled']['diary_dispatch'][0]['before']='0000000000000000'
        with self.assertRaises(ValueError):checked_binding(self.image,r)

    def test_checked_calendar_observer_preserves_exercise(self):
        from v3_player_exercise import checked_native
        self.assertTrue(checked_native(self.image,self.report))
        r=copy.deepcopy(self.report)
        r['equipment_resources']['npc_extra']['events']['calendar']['observers'][2]['target']+=4
        with self.assertRaisesRegex(ValueError,'shared-calendar observer'):
            checked_native(self.image,r)


class PasswordInstalledCategoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(CURRENT/'build-lock.json')
        cls.base,cls.prior=inputs(BASE/'build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_admission_map_and_unchanged_native_anchors(self):
        from v3_password_runtime import MAP
        from v3_password_policy import connected_destination_map
        from v3_room_rig_runtime import bind_profiles
        bind_profiles(self.source,self.image,self.report)
        p=self.report['equipment_resources']['passwords']
        old=self.prior['equipment_resources']['passwords']
        for name in ('af_v3_password_decode','af_nook_password_step','af_nook_password_begin'):
            self.assertEqual(p['code']['symbols'][name],old['code']['symbols'][name])
        self.assertEqual(p['nook'],old['nook'])
        self.assertTrue(p['conversation']['native_bindings_installed'])
        raw,proof=connected_destination_map(CURRENT/'build-lock.json')
        blob=by_vrom(self.image)[BLOB].extract(self.image)
        self.assertEqual(raw,blob[p['blob_offset']+MAP:p['blob_offset']+MAP+len(raw)])
        installed=p['source']['destinations']
        for key in proof:
            if key not in ('base_rom_sha256','base_report_sha256','runtime_abi'):
                self.assertEqual(proof[key],installed[key],key)
        pin=json.loads((CURRENT/'base-lock.json').read_bytes())
        self.assertEqual(installed['base_rom_sha256'],pin['rom_sha256'])
        self.assertEqual(installed['base_report_sha256'],pin['report_sha256'])
        self.assertEqual(installed['runtime_abi'],pin['runtime_abi'])
        self.assertEqual(proof['imports'],215)
        added=self.report['automatic_furniture']['imports']
        self.assertEqual(len(added),16)
        stock={r['item_id'] for r in self.report['shops']['imports']}
        for row in added:
            self.assertNotIn(row['item_id'],stock)
            self.assertFalse(row['ordinary_stock'])
            self.assertFalse(row['catalogue_orderable'])
            self.assertEqual(row['stock_group'],255)
            self.assertEqual(row['reward_route'],0)
            previous=next(r for r in self.prior['staged_furniture']['rows'] if r['id']==row['id'])
            self.assertEqual(int(row['object_vrom'],16),previous['object_vrom'])
            self.assertEqual(row['object_sha256'],previous['object_sha256'])
            matches=[r for r in proof['rows'] if r['id']==row['id']]
            self.assertEqual(len(matches),4)
            self.assertEqual([r['source_item'] for r in matches],list(range(int(row['id'].rsplit('/',1)[1],16),int(row['id'].rsplit('/',1)[1],16)+4)))
            self.assertEqual([r['item'] for r in matches],list(range(int(row['item_id'],16),int(row['item_id'],16)+4)))
            self.assertTrue(all(r['enable_ram'] and r['enable_bytes']==4 for r in matches))
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        for key,value in self.report['save_runtime'].items():
            if key not in ('profile_hex','profile_sha256'):
                self.assertEqual(value,self.prior['save_runtime'][key],key)
        old_profile=bytes.fromhex(self.prior['save_runtime']['profile_hex'])
        new_profile=bytes.fromhex(self.report['save_runtime']['profile_hex'])
        self.assertEqual(len(old_profile),len(new_profile))
        self.assertTrue(all(a&b==a for a,b in zip(old_profile,new_profile,strict=True)))
        self.assertEqual(sum((a^b).bit_count() for a,b in zip(old_profile,new_profile,strict=True)),16)

    def test_homepage_surfaces_keep_stock_and_artwork_unchanged(self):
        surface=self.report['room_surfaces'];old=self.prior['room_surfaces']
        self.assertEqual(surface['rows'],old['rows'])
        self.assertEqual(surface['banks'],old['banks'])
        self.assertEqual(surface['stock']['resources'],old['stock']['resources'])
        self.assertEqual(len(surface['stock']['passwords']),2)
        self.assertEqual(len(surface['optional_selection']['identities']),8)
        self.assertEqual(set(surface['optional_selection']['pending'].values()),{'Harvest rewards'})
        for row in surface['stock']['passwords']:
            self.assertFalse(row['ordinary_stock']);self.assertFalse(row['catalogue_orderable'])
            self.assertEqual(row['password_acquisition']['permission_mask'],4)
        for row in surface['menu']['tables']:self.assertEqual(row['rows'],68)

    def test_current_browser_offline_and_live_map_gates(self):
        import v3_optional_composition as composition
        import v3_browser_composition as browser
        from v3_creature_choices import options
        composition.use_build_lock(CURRENT/'build-lock.json')
        catalog=composition.catalogue(self.image,self.report)
        self.assertEqual(len(catalog),235)
        choices=options(self.image,self.report);plan=browser.rules(self.image,self.report)
        requests=(('empty',[]),('mario-only',['GAFE01-r0/item/331C']),
            ('console-only',['GAFE01-r0/item/1DCC']),
            ('surface-only',['GAFE01-r0/item/2640']),('all',list(catalog)))
        cases=[];p=self.report['equipment_resources']['passwords']
        new_ids={r['id'] for r in self.report['automatic_furniture']['imports']}
        new_ids.update(r['id'] for r in self.report['room_surfaces']['stock']['passwords'])
        rows=[r for r in p['source']['destinations']['rows'] if r['id'] in new_ids]
        for name,requested in requests:
            selected=composition.resolve(catalog,requested,behaviour_options=choices)
            result,_,blob=composition.compose(self.image,self.report,catalog,selected)
            if name=='empty':self.assertEqual(sha256(result),composition.stable_reference(self.report)[1])
            else:
                files=by_vrom(result);resource=files[BLOB].extract(result)
                for row in rows:
                    at=row['enable_offset'];width=row['enable_bytes']
                    self.assertEqual(int.from_bytes(resource[at:at+width],'big'),int(row['id'] in selected['enabled']))
            if name=='all':self.assertEqual(result,self.image)
            cases.append(dict(name=name,requested=requested,behaviours={},selection=selected,sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-password-composition-') as temp:
            fixture=Path(temp)/'fixture.json'
            fixture.write_text(json.dumps(dict(plan=plan,cases=cases,
                base=str(CURRENT/'animal-forest-v3-asset-loader.z64'),stable=str(composition.stable_reference(self.report)[0]))))
            run=subprocess.run(['node','--experimental-global-webcrypto','tests/v3_browser_equivalence.mjs',str(fixture)],
                cwd=ROOT,capture_output=True,text=True,timeout=180)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())


if __name__=='__main__':unittest.main()
