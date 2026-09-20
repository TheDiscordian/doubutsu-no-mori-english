"""Current shared held-loop installation, retained resources, and optional composition."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,sha256
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
from v3_equipment_runtime import RAM,GUARD,PLAYER_VROM
import v3_sound_programs as sounds
import v3_optional_composition as composer

OUTPUT=ROOT/os.environ.get('V3_LEVEL_SOUND_BUILD','build/v3-held-rig-sound-04')


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current level sound cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUTPUT/'build-lock.json');cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.old_files=by_vrom(cls.image),by_vrom(cls.base)
        cls.core=cls.files[CODE_VROM].extract(cls.image);cls.old_core=cls.old_files[CODE_VROM].extract(cls.base)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.s=cls.e['sound_programs'];cls.r=cls.e['held_rig_actions'];cls.loop=cls.r['loop_sound']

    def test_complete_source_program_identity_dispatch_heap_and_retention(self):
        blob,_=reuse_resource_tail(self.base,self.prior,self.old_files[BLOB].extract(self.base))
        rebuilt=sounds.install_level(self.base,self.prior,blob,bytearray(self.old_core),[self.loop['native_sound_id']])
        self.assertEqual(json.loads(json.dumps(rebuilt)),self.s)
        seq,entry,physical=sounds.installed_resource(self.image,self.core,'seq',199)
        self.assertEqual((sha256(seq),entry.hex(),physical),
            (self.s['sequence']['sha256'],self.s['sequence']['header_after'],self.s['sequence']['physical']))
        row=self.s['imports'][-1];oldseq,_,_=sounds.installed_resource(self.base,self.old_core,'seq',199)
        self.assertEqual(self.s['imports'][:-1],self.old['sound_programs']['imports'])
        self.assertEqual((row['kind'],row['native_sound_id'],row['native_bank'],row['native_instrument']),('level',77,139,120))
        self.assertFalse(row['new_sample']);self.assertFalse(row['new_instrument'])
        self.assertEqual(row['instrument_identity']['samples'][1]['sample_bytes'],21880)
        restored=bytearray(seq[:len(oldseq)]);table=row['native_table']+2*row['native_sound_id']
        self.assertEqual(struct.unpack_from('>H',seq,table)[0],row['offset'])
        struct.pack_into('>H',restored,table,row['original_table_pointer']);self.assertEqual(restored,oldseq)
        data=seq[row['offset']:row['offset']+row['bytes']]
        desc=sounds.looping_layer(data,row['offset'],prefix=True)
        self.assertEqual((desc['duration'],desc['note'],desc['velocity']),(32000,46,60))
        self.assertEqual(self.s['after_budget'],sounds.permanent_budget(self.core))
        self.assertEqual(self.s['after_budget']['conservative_spare'],192)
        self.assertEqual(len(seq)-len(oldseq),32)

    def test_exact_code_changes_callback_rebinding_and_unchanged_owner(self):
        restored=bytearray(self.core);h=self.loop['hook'];at=h['address']-CODE_RAM
        self.assertEqual(restored[at:at+4].hex(),h['after']);restored[at:at+4]=bytes.fromhex(h['before'])
        seq=self.s['sequence'];at=seq['header_address']-CODE_RAM
        restored[at:at+16]=bytes.fromhex(seq['header_before']);self.assertEqual(restored,self.old_core)
        blob=self.files[BLOB].extract(self.image);oldblob=self.old_files[BLOB].extract(self.base)
        at=self.e['blob_offset'];module=bytearray(blob[at:at+self.e['bytes']])
        self.assertEqual((at,len(module)),(self.old['blob_offset'],self.old['bytes']))
        self.assertEqual(sha256(module),self.e['sha256']);self.assertEqual(zlib.crc32(module),self.e['crc32'])
        self.assertEqual(module[-16:],struct.pack('>4I',*(GUARD,)*4))
        code=self.r['code'];symbols=code['symbols']
        self.assertEqual(sha256(module[0xD000:0xD000+code['bytes']]),code['sha256'])
        self.assertLessEqual(code['bytes'],0xFE0)
        self.assertFalse(any(module[0xD000+code['bytes']:-16]))
        self.assertEqual(self.loop['level_ram'],RAM+0xDFE0)
        self.assertEqual(symbols['af_v3_held_setup'],self.old['held_rig_actions']['code']['symbols']['af_v3_held_setup'])
        for new,old,name in zip(self.e['player_actions']['held_dispatch']['tables'],
                               self.old['player_actions']['held_dispatch']['tables'],
                               ('af_v3_held_pinwheel_main','af_v3_held_pinwheel_draw')):
            p=new['offset'];self.assertEqual(sha256(module[p:p+new['bytes']]),new['sha256'])
            self.assertEqual(struct.unpack_from('>I',module,p+88)[0],symbols[name])
            module[p+88:p+92]=oldblob[at+p+88:at+p+92]
        self.assertEqual(module[:0xD000],oldblob[at:at+0xD000])
        for key in ('records','kind_readers','inventory_preview','animated_rigs','player_motion'):
            self.assertEqual(self.e[key],self.old[key])
        for v in set(self.files)-{CODE_VROM,BLOB,MODULE,0x19D40}:
            self.assertEqual(self.files[v].extract(self.image),self.old_files[v].extract(self.base),hex(v))
        reuse_resource_tail(self.image,self.report,blob)
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.image)

    def test_occupied_sound_slots_and_altered_interpreter_reject(self):
        for ids in ([],[77,77],[77],[67],[128]):
            with self.subTest(ids=ids),self.assertRaises(ValueError):
                sounds.install_level(self.image,self.report,bytearray(),bytearray(self.core),ids)
        broken=bytearray(self.old_core);broken[0x800F3994-CODE_RAM]^=1
        with self.assertRaises(ValueError):sounds.install_level(self.base,self.prior,bytearray(),broken,[77])

    def test_retained_saves_existing_selections_and_exact_translation_only(self):
        for key in ('save_runtime','furniture','translation_baseline','translation_updates'):
            self.assertEqual(self.report[key],self.prior[key])
        pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),112)
            self.assertFalse(any(f'GAFE01-r0/item/{i:04X}' in catalog for i in range(0x224C,0x2254)))
            empty=composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]
            self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


if __name__=='__main__':unittest.main()
