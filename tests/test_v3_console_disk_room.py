"""Shared disk readiness, ordinary profile staging, and retained imports."""
import copy
import json
from pathlib import Path
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source,scan,rig_import_plan
from v3_import_storage import ROWS,ITEMS,TABLE_END,slot
from v3_room_rig_runtime import bind_profiles
import v3_console_room as console


class DiskRoomTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=ROOT/'build/v3-console-disk-room-imports-01'
        cls.plan=json.loads((cls.batch/'pipeline.json').read_bytes())
        cls.out=(ROOT/cls.plan['final_lock']).parent
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_category_stages_complete_disk_profile_without_recompiling_art_or_engine(self):
        self.assertEqual(self.plan['plan']['profiles'],['1DCC'])
        self.assertEqual([r['stage'] for r in self.plan['steps']],['profile-runtime'])
        self.assertEqual(self.plan['imported'],[])
        art=json.loads((self.batch/'prepared/art.json').read_bytes())
        self.assertEqual(art['batch'],dict(objects=1,reused=1,compiled=0,compiler_containers=0))
        e=self.report['equipment_resources'];before=self.prior['equipment_resources']
        rows=console.checked_runtime(e,self.blob,self.image)
        self.assertEqual(len(rows),12)
        self.assertTrue(all(r['engine_installed'] and r['profile_installed'] for r in rows.values()))
        bindings=bind_profiles(self.source,self.image,self.report)
        disk=rows['1DCC'];self.assertEqual((disk['game_index'],disk['image_kind']),(10,2))
        self.assertEqual(bindings['1DCC']['room_runtime']['vtable'],console.VTABLE)
        self.assertFalse(disk['parent_selectable'])
        prepared=art['objects'][0];data=(self.batch/'prepared'/prepared['object_file']).read_bytes()
        self.assertEqual(self.blob[disk['blob_offset']:disk['blob_offset']+disk['bytes']],data)
        self.assertEqual(len(data),4880);self.assertEqual(len(prepared['models']),3)
        for old in before['console_images']['room']['rows']:
            if old['source_item_id']!='1DCC':self.assertEqual(rows[old['source_item_id']],old)
        old_blob=by_vrom(self.base)[BLOB].extract(self.base)
        p=e['console_images']['packet'];q=before['console_images']['packet']
        packet=self.blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        old_packet=old_blob[q['blob_offset']:q['blob_offset']+q['bytes']]
        changed=[i for i,(a,b) in enumerate(zip(packet,old_packet,strict=True)) if a!=b]
        row_index=e['console_images']['room']['rows'].index(disk)
        self.assertEqual(changed,[console.TABLE-p['ram']+16+row_index*8+3])
        self.assertEqual((sha256(packet),zlib.crc32(packet)),(p['sha256'],p['crc32']))
        for key in ('compiled','emulator','pool','metadata'):
            self.assertEqual(e['console_images'][key],before['console_images'][key])
        for key in ('console_disk','console_storage','room_goods','room_carry','room_rigs'):
            current=copy.deepcopy(e[key]);old=copy.deepcopy(before[key])
            if 'startup' in current:
                current['startup'].pop('sha256');old['startup'].pop('sha256')
            self.assertEqual(current,old,key)
        i=slot(int(disk['item_id'],16));expected=bytearray(old_blob[ROWS:TABLE_END])
        for at,size in ((ROWS+i*80,80),(ITEMS+i*32,32)):
            expected[at-ROWS:at-ROWS+size]=self.blob[at:at+size]
        self.assertEqual(self.blob[ROWS:TABLE_END],expected)
        self.assertEqual(self.blob[ROWS+i*80+4:ROWS+i*80+8],bytes(4))
        self.assertFalse(self.blob[0x40+i//8]&(1<<(i&7)))
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['automatic_furniture']['imports'],self.prior['automatic_furniture']['imports'])
        files,old_files=by_vrom(self.image),by_vrom(self.base)
        self.assertEqual(set(files),set(old_files))
        for vrom in files:
            if vrom not in (BLOB,MODULE,0x19D40):
                self.assertEqual(files[vrom].extract(self.image),old_files[vrom].extract(self.base),hex(vrom))
        for row in self.report['physical_resources']:
            at=row['physical'];end=at+row['bytes']
            self.assertEqual(self.image[at:end],self.base[at:end])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_readiness_rejects_missing_or_changed_disk_dependencies_without_mutation(self):
        e=self.report['equipment_resources'];self.assertTrue(console.disk_engine_ready(e,self.blob,self.image))
        for damage in ('missing_hooks','native_owner','lower_call','image_kind','compiled','disk_data'):
            broken=copy.deepcopy(e);blob=bytearray(self.blob)
            if damage=='missing_hooks':
                broken['console_disk']['session_hooks_installed']=False
                broken['console_images']['emulator']['qd_engine_installed']=False
            elif damage=='native_owner':broken['console_images']['emulator']['native']['sha256']='0'*64
            elif damage=='lower_call':broken['console_disk']['shared_calls']['af_v3_console_frame']+=4
            elif damage=='image_kind':broken['console_images']['room']['rows'][2]['image_kind']=1
            elif damage=='compiled':broken['console_disk']['compiled']['sha256']='0'*64
            else:blob[broken['console_disk']['packet']['blob_offset']+0x6000]^=1
            snapshot=bytes(blob);receipt=copy.deepcopy(broken)
            with self.subTest(damage=damage),self.assertRaises(ValueError):
                console.bind_engines(broken,blob,self.image)
            self.assertEqual(bytes(blob),snapshot);self.assertEqual(broken,receipt)
        equipment=copy.deepcopy(e);blob=bytearray(self.blob)
        console.bind_engines(equipment,blob,self.image)
        self.assertEqual(equipment,e);self.assertEqual(blob,self.blob)

    def test_repeat_plan_skips_completed_profile_and_keeps_real_acquisition_pending(self):
        bindings=bind_profiles(self.source,self.image,self.report)
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',
            installed=[int(r['id'].rsplit('/',1)[1],16) for r in self.report['furniture']['imports']],
            selected=tuple(self.source.console_runtime_bindings))
        plan=rig_import_plan(inventory,self.report,bindings,category=console.CATEGORY,source=self.source)
        self.assertFalse(any(plan.values()),plan)
        disk=next(r for r in inventory['rows'] if r['item_id']=='1DCC')
        self.assertIn('ftr_listHomePage',disk['reason'])
        self.assertNotIn('engine',disk['reason'])

    def test_private_composition_preserves_inactive_disk_profile(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)

    def test_absent_donor_payload_is_not_reported_as_missing_engine_work(self):
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',selected=('1FBC',))
        row=inventory['rows'][0]
        self.assertEqual(row['profile']['callback_adapter']['console_launch']['payload_status'],'absent-from-donor')
        self.assertIn('payload is absent from this donor',row['reason'])
        self.assertIsNone(console.lifecycle(row['profile']))


if __name__=='__main__':unittest.main()
