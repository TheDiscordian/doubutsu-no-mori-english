"""Complete reversible resources, dispatch, installation, and private composition."""
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
from v3_furniture_pipeline import Source,prepare,PreparedAssets,scan,rig_import_plan
from v3_furniture_reversible import CATEGORY
from v3_furniture_rigs import suffix
from aflib import sha256,by_vrom,apply_ups,CODE_VROM
from v3_furniture_install import inputs
from v3_asset_loader import BLOB

ART=ROOT/os.environ.get('V3_REVERSIBLE_ART','build/v3-reversible-rigs-prepared-01')

class ReversibleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_source_and_prepared_models_motion_and_unavailable_gameplay(self):
        source=self.source;prepared=prepare(source,0x1FB8);a=prepared[0]['callback_adapter']
        self.assertEqual(a['category'],CATEGORY)
        self.assertEqual((a['skeleton']['joints'],a['skeleton']['shown_joints']),(11,5))
        self.assertEqual((a['animation']['duration'],a['trigger']['sound_word']),(46,0x7A))
        self.assertEqual(a['work']['joint_bytes']+a['work']['morph_bytes'],204)
        art=json.loads((ART/'art.json').read_bytes());row=art['objects'][0]
        self.assertEqual(row['item_id'],'1FB8');self.assertFalse(row['import_ready'])
        self.assertEqual(PreparedAssets(source,[ART]).reuse(source,'1FB8',prepared)[1]['object_sha256'],row['object_sha256'])
        blob=(ART/row['object_file']).read_bytes();start=(len(prepared[1])+sum(n for _,n in prepared[6])+15)&~15
        packed,receipt=suffix(source,prepared[0],row['model_offsets'],start=start)
        self.assertEqual(blob[start:],packed);self.assertEqual(sha256(blob),row['object_sha256'])
        from tests.test_v3_furniture_pipeline import DonorTests
        DonorTests.check_complete_artwork(self,ART,art)
        for r in receipt['animations']['arrays']:
            self.assertEqual(blob[r['native_offset']:r['native_offset']+r['bytes']],
                source.data[r['donor_offset']:r['donor_offset']+r['bytes']])
        inventory=scan(source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['1FB8'])
        self.assertTrue(inventory['rows'][0]['asset_ready']);self.assertNotEqual(inventory['rows'][0]['status'],'supported')
        self.assertEqual(rig_import_plan(inventory,{'equipment_resources':{'room_rigs':{'rows':[]}}},{},source=source),
            dict(resources=['1FB8'],audio=['1FB8'],loops=[],profiles=['1FB8']))
        for receipt in list(a['functions'].values())+[a['helpers']['sAdo_OngenTrgStart'],a['initializer']]:
            changed=copy.copy(source);data=bytearray(source.rel);data[source.sections[1][0]+receipt['offset']]^=1
            changed.rel=bytes(data)
            with self.subTest(function=receipt['symbol']),self.assertRaises(ValueError):prepare(changed,0x1FB8)

    def test_actual_donor_reversible_motion_and_extended_joint_work_under_sanitizers(self):
        text=(ROOT/'local/ac-decomp/src/furniture/ac_ike_jny_rosia01.c').read_text();functions=[]
        for name in ('aIkeJnyRosia01_ct','aIkeJnyRosia01_mv','aIkeJnyRosia01_dt'):
            start=text.index('static void '+name+'(')
            while text.index(';',start)<text.index('{',start):start=text.index('static void '+name+'(',start+1)
            functions.append(text[start:text.index('\n}',start)+2])
        with tempfile.TemporaryDirectory(prefix='v3-reversible-') as directory:
            directory=Path(directory);(directory/'donor_reversible.inc').write_text('\n\n'.join(functions))
            binary=directory/'test'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-I'+str(directory),str(ROOT/'tests/v3_reversible_rigs_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('4324 donor reversible comparisons',run.stdout)

    def test_complete_dispatch_and_capture_before_destruction(self):
        from v3_room_rig_runtime import prepared_categories,encode_packet
        rows,_,_=prepared_categories(self.source,[ART])
        with tempfile.TemporaryDirectory(prefix='v3-reversible-dispatch-') as d:
            directory=Path(d);table=directory/'table';binary=directory/'check'
            table.write_bytes(encode_packet(rows))
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_reversible_dispatch_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary),str(table),str(ART/'1FB8.n64obj.bin')],
                capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('1440 reversible dispatch frames',run.stdout)

    def test_shared_bootstrap_checks_every_callback_before_dispatch(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-bootstrap-') as d:
            binary=Path(d)/'check'
            # The fixed native addresses are mapped explicitly; ASan's shadow
            # mapping conflicts with this address range. This check uses UBSan.
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=undefined',str(ROOT/'tests/v3_room_bootstrap_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('11 bootstrap entries',run.stdout)

class InstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.batch=ROOT/os.environ.get('V3_REVERSIBLE_BATCH','build/v3-reversible-rig-imports-03')
        result=json.loads((cls.batch/'pipeline.json').read_bytes());cls.out=(ROOT/result['final_lock']).parent
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-material-rig-imports-01/cartridge/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)

    def test_full_rig_sound_profile_persistence_binding_and_retention(self):
        from v3_room_rig_runtime import bind_profiles
        from v3_furniture_reversible import native_contract
        from v3_sound_programs import installed_resource,trigger_program
        from v3_villager_audio import instrument
        from v3_import_storage import slot
        bindings=bind_profiles(self.source,self.image,self.report)
        e=self.report['equipment_resources'];room=e['room_rigs'];old=self.prior['equipment_resources']
        rig=next(r for r in room['rows'] if r['source_item_id']=='1FB8')
        self.assertEqual((rig['item_id'],rig['runtime_index'],rig['mode'],rig['joints'],rig['shown']),('3C44',1809,9,11,5))
        self.assertTrue(rig['profile_installed']);self.assertTrue(rig['parent_selectable']);self.assertFalse(bindings['1FB8']['staged'])
        self.assertEqual(self.blob[rig['blob_offset']:rig['blob_offset']+rig['bytes']],(ART/'1FB8.n64obj.bin').read_bytes())
        self.assertEqual(room['reversible_contract'],native_contract(self.image))
        callbacks=struct.unpack('>5I',bytes.fromhex(room['vtable_hex']))
        self.assertEqual(callbacks[3],room['bootstrap']['symbols']['af_v3_room_boot_dt'])
        audio=e['furniture_audio'];sound=next(r for r in room['sound_rows'] if r['source_item_id']=='1FB8')
        program=next(r for r in audio['programs'] if r['source_sound_word']==0x7A)
        self.assertEqual(program['native_sound_word'],sound['native_sound_word'])
        core=by_vrom(self.image)[CODE_VROM].extract(self.image)
        sequence,_,_=installed_resource(self.image,core,'seq',199)
        at=program['offset'];raw=sequence[at:at+program['bytes']];source=program['source_program']
        parsed=trigger_program(sequence,at,at+len(raw));self.assertEqual(parsed['events'],source['events'])
        self.assertEqual(parsed['envelope_bytes'],8)
        restored=bytearray(raw);restored[1:3]=bytes((source['selector'],source['instrument']))
        for p in source['pointers']:struct.pack_into('>H',restored,p,struct.unpack_from('>H',raw,p)[0]-at+source['origin'])
        self.assertEqual(sha256(restored),source['sha256'])
        font,header,_=installed_resource(self.image,core,'bank',140)
        wave,_,_=installed_resource(self.image,core,'wave',header[10])
        for r in audio['layout']['imports']:
            self.assertEqual(instrument(font,wave,r['native_instrument'],header[12],extended=True),r['identity'])
        imported=next(r for r in self.report['furniture']['imports'] if r.get('donor_item_id')=='1FB8')
        self.assertTrue(imported['enabled']);self.assertFalse(imported['ordinary_stock']);self.assertFalse(imported['catalogue_orderable'])
        self.assertEqual((imported['donor_list'],imported['stock_group'],imported['birth_category']),('ftr_listJonason',12,22))
        self.assertEqual(imported['name'],'matryoshka')
        self.assertIn(imported['id']+'/name',{r['id'] for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']})
        blob=by_vrom(self.base)[BLOB].extract(self.base)
        for key in ('rows','material_rows','sound_rows'):
            for r in old['room_rigs'][key]:
                kept=next(x for x in room[key] if x['source_item_id']==r['source_item_id'])
                self.assertEqual(kept,r)
                if 'blob_offset' in r:
                    at=r['blob_offset'];self.assertEqual(self.blob[at:at+r['bytes']],blob[at:at+r['bytes']])
        for key in ('room_goods','room_carry'):self.assertEqual(e[key],old[key])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        flags=bytearray.fromhex(self.prior['save_runtime']['profile_hex']);i=slot(0x3C44);flags[0x20+i//8]|=1<<(i&7)
        self.assertEqual(self.report['save_runtime']['profile_hex'],flags.hex())
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['1FB8'])
        self.assertTrue(all(not v for v in rig_import_plan(inventory,self.report,bindings,source=self.source).values()))
        self.assertLessEqual(room['code']['bytes'],32768);self.assertLessEqual(room['bootstrap']['bytes'],1536)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_private_browser_and_offline_composition(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=[r for r in self.report['furniture']['imports'] if r.get('donor_item_id')=='1FB8']
        self.assertEqual(len(self.rows),1)
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
