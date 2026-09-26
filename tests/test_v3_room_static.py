"""Focused direct-model callbacks and complete town-tune resource preservation."""
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
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_pipeline import Source,scan,rig_import_plan
from v3_furniture_install import inputs
from v3_villager_audio import instrument
from v3_sound_programs import installed_resource
import v3_furniture_static as static
import v3_furniture_melody as melody
import v3_room_rig_runtime as room


class StaticSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_callback_shapes_are_not_item_switches(self):
        found=set()
        for offset,definitions in self.source.functions.items():
            if len(definitions)!=1 or definitions[0][1]!=68:continue
            _,receipt=self.source.function(offset)
            adapter=static.discover(self.source,receipt)
            if adapter:found.add(adapter['parameter'])
        self.assertEqual(found,set(range(16)))
        wallet=self.source.profile(0x1FAC)['callback_adapter']
        self.assertEqual((wallet['mode'],wallet['parameter'],wallet['trigger']['sound_word']),(1,1,124))
        self.assertEqual(wallet['excluded_states'],[])
        for item,mode,kind in ((0x3244,3,'steam'),(0x3324,4,'projectile')):
            adapter=self.source.profile(item)['callback_adapter']
            self.assertEqual((adapter['category'],adapter['mode'],adapter['effects']),
                ('static-interaction',mode,[kind]))
            self.assertEqual(adapter['excluded_states'],[13,14,15,12])

    def test_periodic_and_directional_emitters_under_sanitizers(self):
        from tests.test_v3_equipment_runtime import HostTests
        HostTests.sanitized(self,'v3_room_emitters_test.c')

    def test_actual_shared_dispatch_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='afv3-static-') as directory:
            executable=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror','-O1','-g',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
                '-DAF_V3_ROOM_RIG_PACKET','-DAF_V3_ROOM_TRIGGER_SOUND','-DAF_V3_ROOM_STATIC',
                '-Ioverlays/v3','tests/v3_room_static_test.c','overlays/v3/room_static.c',
                'overlays/v3/room_rigs.c','-o',str(executable)],cwd=ROOT,check=True)
            subprocess.run([str(executable)],check=True,timeout=10)


class InstalledStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_STATIC_BUILD','build/v3-static-interaction-imports-02/profile-runtime')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-material-colour-lifecycle-imports-05/profile-runtime/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_profiles_and_artwork(self):
        bindings=room.bind_profiles(self.source,self.image,self.report)
        blob=by_vrom(self.image)[BLOB].extract(self.image)
        rows=static.checked_binding(self.image,self.report,blob)
        self.assertEqual(set(rows),{'1FAC','31CC'})
        prepared=ROOT/'build/v3-static-callback-resources-prepared-01'
        art=json.loads((prepared/'art.json').read_text())
        for identity,row in rows.items():
            source=next(r for r in art['objects'] if r['item_id']==identity)
            self.assertEqual(blob[row['blob_offset']:row['blob_offset']+row['bytes']],
                (prepared/source['object_file']).read_bytes())
            self.assertTrue(bindings[identity]['staged'])
            self.assertEqual(bindings[identity]['room_runtime']['vtable'],room.SOUND_VTABLE)
        inventory=scan(self.source,ROOT/'build/item-identity-megasheet.xlsx',[],selected=['1FAC','31CC'])
        plan=rig_import_plan(inventory,self.report,bindings,source=self.source)
        self.assertTrue(all(not values for values in plan.values()))
        for row in inventory['rows']:
            self.assertEqual(row['status'],'review')
            self.assertTrue(row['reason'].startswith('acquisition needs an adapter:'),row['reason'])

    def test_complete_melody_and_all_original_font_instruments(self):
        audio=melody.checked_binding(self.image,self.report)
        oldcode=by_vrom(self.base)[CODE_VROM].extract(self.base)
        code=by_vrom(self.image)[CODE_VROM].extract(self.image)
        oldbank,oldh,_=installed_resource(self.base,oldcode,'bank',0)
        oldwave,_,_=installed_resource(self.base,oldcode,'wave',0)
        bank,header,_=installed_resource(self.image,code,'bank',0)
        wave,_,_=installed_resource(self.image,code,'wave',0)
        self.assertEqual((oldh[12],header[12]),(71,72))
        self.assertEqual(wave[:len(oldwave)],oldwave)
        for i in range(71):
            self.assertEqual(instrument(bank,wave,i,72,extended=True,minimum_envelope_steps=1),
                instrument(oldbank,oldwave,i,71,extended=True,minimum_envelope_steps=1))
        self.assertEqual(audio['layout']['imports'][0]['identity']['samples'][1]['sample_bytes'],6534)
        self.assertEqual(len(audio['programs'][0]['source']['tracks']),19)
        damaged=bytearray(self.image)
        damaged[audio['wave']['physical']+len(oldwave)+3]^=1
        with self.assertRaisesRegex(ValueError,'town-melody resource'):
            melody.checked_binding(bytes(damaged),self.report)

    def test_save_selection_and_patch_preservation(self):
        for key in ('furniture','save_codec','save_runtime','translation_baseline'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)
        self.assertLessEqual(self.report['equipment_resources']['room_rigs']['code']['bytes'],16384)
        self.assertLessEqual(self.report['equipment_resources']['room_rigs']['bootstrap']['bytes'],1536)

    def test_current_browser_and_offline_composition(self):
        import v3_optional_composition as composer
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json')
            catalogue=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalogue),155)
            self.assertNotIn('GAFE01-r0/item/1FAC',catalogue)
            self.assertNotIn('GAFE01-r0/item/31CC',catalogue)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.rows=[r for r in self.report['furniture']['imports'] if r.get('donor_item_id')=='1FD8']
        self.assertEqual(len(self.rows),1)
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)

    def test_external_wave_binding_survives_shared_archive_relocation(self):
        from v3_sound_programs import audio_archive
        from v3_villager_audio import NATIVE_HEADERS
        equipment=copy.deepcopy(self.report['equipment_resources'])
        code=bytearray(by_vrom(self.image)[CODE_VROM].extract(self.image))
        base=audio_archive(self.image,code,'wave').pstart+0x1000
        struct.pack_into('>2I',code,0x800D28DC-CODE_RAM,
            0x3C0E0000|((base+0x8000)>>16),0x25CE0000|(base&65535))
        address=NATIVE_HEADERS['wave']+16-CODE_RAM
        physical=equipment['furniture_melody_audio']['wave']['physical']
        struct.pack_into('>I',code,address,(physical-base)&0xFFFFFFFF)
        melody.rebind_wave_header(equipment,code)
        self.assertEqual(equipment['furniture_melody_audio']['wave']['header_after'],code[address:address+16].hex())
        code[address+3]^=1
        with self.assertRaisesRegex(ValueError,'samples moved or changed'):
            melody.rebind_wave_header(equipment,code)


if __name__=='__main__':unittest.main()
