"""One shared donor lifecycle check; no per-item emulator fixture."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_room_music import source_contract,native_contract,patch_native,HOOKS,RAM


class MusicTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.image,cls.report=inputs(ROOT/'build/v3-dual-motion-imports-01/profile-runtime/build-lock.json')

    def test_shared_audio_effect_and_complete_helper_bindings(self):
        self.assertEqual(len(source_contract(self.source)['functions']),9)
        contract=native_contract(self.image,self.report);music=contract['music']['rows'][0]
        self.assertEqual((music['source_sequence'],music['native_sequence'],music['native_bytes']),(218,181,4736))
        self.assertEqual([r['offset'] for r in music['native_mix']],[3,20])
        self.assertEqual(len(music['font']['samples']),4)
        self.assertEqual((contract['note']['models'],contract['note']['colours']),(3,5))
        changed=copy.copy(self.source);raw=bytearray(changed.rel)
        raw[changed.sections[1][0]+0x101A9C]^=1;changed.rel=bytes(raw)
        with self.assertRaises(ValueError):source_contract(changed)

    def test_actual_owner_hooks_relocate_without_changing_other_code(self):
        files=by_vrom(self.image);owner=files[0x82D7F0].extract(self.image);reloc=files[0x844400].extract(self.image)
        symbols=dict(af_v3_room_boot_music_disk_dt=0x804B1C00,af_v3_room_boot_music_apply=0x804B1C20)
        patched,binding=patch_native(owner,reloc,symbols)
        self.assertEqual(binding['owner_sha256'],sha256(patched));self.assertEqual(binding['relocation_sha256'],sha256(reloc))
        changed={i for address,_,_ in HOOKS for i in range(address-RAM,address-RAM+8)}
        self.assertTrue(all(a==b or i in changed for i,(a,b) in enumerate(zip(owner,patched,strict=True))))
        self.assertEqual(patched[0x809385B0-RAM:0x809385B8-RAM].hex(),'312b400800000000')
        with self.assertRaises(ValueError):patch_native(patched,reloc,symbols)
        with self.assertRaises(ValueError):patch_native(owner,reloc,{**symbols,'af_v3_room_boot_music_apply':0x809385E4})

    def test_core_and_native_bridge_against_actual_donor(self):
        contract=source_contract(self.source)
        text=(ROOT/'local/ac-decomp/src/actor/ac_my_room.c').read_text();functions=[]
        for name in contract['functions']:
            prefix='extern void ' if name=='aMR_RadioCommonMove' else 'static void '
            start=text.index('\n'+prefix+name+'(')+1
            if text.index(';',start)<text.index('{',start):start=text.index('\n'+prefix+name+'(',start)+1
            functions.append(text[start:text.index('\n}',start)+2])
        with tempfile.TemporaryDirectory(prefix='v3-room-music-') as temp:
            directory=Path(temp);binary=directory/'check'
            (directory/'donor_room_music.inc').write_text('\n\n'.join(functions))
            run=subprocess.run(['cc','-std=gnu11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I'+str(directory),str(ROOT/'tests/v3_room_music_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=15)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('actual-donor music comparisons; native owner, notes, and bounded drawing pass',run.stdout)
            print(run.stdout.strip())


class InstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from v3_asset_loader import BLOB
        cls.out=ROOT/'build/v3-room-music-imports-04/profile-runtime'
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-dual-motion-imports-01/profile-runtime/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)

    def test_installed_category_preserves_resources_and_keeps_missing_behaviour_disabled(self):
        from aflib import apply_ups
        from v3_asset_loader import BLOB
        from v3_furniture_pipeline import scan,rig_import_plan,identity_rows
        from v3_furniture_install import provenance_patch
        from v3_room_music import checked_binding,restore_owner
        from v3_room_rig_runtime import bind_profiles,encode_packet
        from v3_room_carry_native import checked_binding as carry_binding
        from v3_villager_houses import item_dependencies
        from v3_registry import furniture_identity,LEGACY_FURNITURE,LEGACY_ROOM_ALIASES,CLOTHING_DISPLAYS
        bindings=bind_profiles(self.source,self.image,self.report)
        runtime=self.report['equipment_resources']['room_rigs'];music=checked_binding(self.source,self.image,self.report)
        row=next(r for r in runtime['rows'] if r['source_item_id']=='1FCC')
        self.assertEqual((row['mode'],row['runtime_index'],row['item_id']),(12,1810,'3C48'))
        self.assertEqual(furniture_identity(0x1FCC),(1810,0x3C48))
        self.assertEqual(len(set(LEGACY_FURNITURE.values())),len(LEGACY_FURNITURE))
        self.assertFalse(set(LEGACY_FURNITURE.values())&(set(LEGACY_ROOM_ALIASES.values())|set(CLOTHING_DISPLAYS.values())))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        reviewed=item_dependencies(original,{'rel':self.source.rel},self.source.symbols,{0x1FCC})
        self.assertFalse(reviewed[0]['reviewed_native_items']);self.assertFalse(reviewed[0]['shared_identity_evidence'])
        self.assertTrue(bindings['1FCC']['staged']);self.assertTrue(row['profile_installed']);self.assertFalse(row['parent_selectable'])
        self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']],
            (ROOT/'build/v3-composite-rigs-prepared-01/1FCC.n64obj.bin').read_bytes())
        for change in ({'first':0x06000001},{'last':0x06002000},{'joints':1}):
            bad=copy.deepcopy(row);bad.update(change)
            with self.assertRaises(ValueError):encode_packet([bad])
        old=by_vrom(self.base);new=by_vrom(self.image)
        self.assertEqual(restore_owner(new[0x82D7F0].extract(self.image),music,runtime),old[0x82D7F0].extract(self.base))
        self.assertEqual(new[0x844400].extract(self.image),old[0x844400].extract(self.base))
        self.assertEqual(carry_binding(self.image,self.report),carry_binding(self.base,self.prior))
        old_blob=old[BLOB].extract(self.base)
        for prior_row in self.prior['equipment_resources']['room_rigs']['rows']:
            present=next(r for r in runtime['rows'] if r['source_item_id']==prior_row['source_item_id'])
            self.assertEqual(present,prior_row)
            at,n=present['blob_offset'],present['bytes'];self.assertEqual(self.blob[at:at+n],old_blob[at:at+n])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['1FCC'])
        self.assertTrue(all(not v for v in rig_import_plan(inventory,self.report,bindings,source=self.source).values()))
        self.assertIn('indoor player-aerobics',inventory['rows'][0]['reason'])
        staged=next(r for r in self.report['staged_furniture']['rows'] if r.get('donor_item_id')=='1FCC')
        self.assertEqual(provenance_patch([staged]),'')
        self.assertEqual(apply_ups(original,(self.out/'asset-loader.ups').read_bytes()),self.image)
        self.assertLessEqual(runtime['code']['bytes'],32768);self.assertLessEqual(runtime['bootstrap']['bytes'],1536)

    def test_current_private_composition_preserves_all_choices_and_translation_only(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        self.assertNotIn('1FCC',{r.get('donor_item_id') for r in self.rows})
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)
