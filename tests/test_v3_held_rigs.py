"""Shared animated-held behaviour, allocation, installation, and composition."""
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_furniture_install import inputs,reuse_resource_tail
from v3_equipment_runtime import PLAYER_RAM,PLAYER_VROM,PLAYER_RELOC,RAM,GUARD
import v3_player_actions as actions
import v3_optional_composition as composer

OUTPUT=ROOT/'build/v3-held-rig-actions-03'


class BehaviourTests(unittest.TestCase):
    def run_behaviour(self, *flags):
        with tempfile.TemporaryDirectory(prefix='v3-held-rigs-') as directory:
            binary=str(Path(directory)/'test')
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',*flags,
                str(ROOT/'tests/v3_held_rigs_test.c'),'-lm','-o',binary],check=True,capture_output=True,timeout=30)
            subprocess.run([binary],check=True,capture_output=True,timeout=10)

    def test_complete_shared_behaviour_under_sanitizers(self):
        self.run_behaviour()

    def test_complete_shared_behaviour_and_level_sound_under_sanitizers(self):
        self.run_behaviour('-DAF_V3_PINWHEEL_SOUND=0x4D')


@unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current rig-action cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUTPUT/'build-lock.json')
        cls.before,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.old_files=by_vrom(cls.image),by_vrom(cls.before)
        cls.e=cls.report['equipment_resources'];cls.old=cls.prior['equipment_resources']
        cls.rigs=cls.e['held_rig_actions'];cls.blob=cls.files[BLOB].extract(cls.image)
        cls.old_blob=cls.old_files[BLOB].extract(cls.before)
        cls.module=cls.blob[cls.e['blob_offset']:cls.e['blob_offset']+cls.e['bytes']]

    def test_exact_owner_allocation_changes_and_retained_resources(self):
        core=bytearray(self.files[CODE_VROM].extract(self.image))
        allocation=self.rigs['player_allocation'];at=allocation['address']-CODE_RAM
        self.assertEqual(struct.unpack_from('>I',core,at)[0],0x1310)
        self.assertLessEqual(allocation['state_offset']+allocation['state_bytes'],0x1310)
        struct.pack_into('>I',core,at,0x12D8)
        self.assertEqual(core,self.old_files[CODE_VROM].extract(self.before))
        owner=bytearray(self.files[PLAYER_VROM].extract(self.image));hook=self.rigs['setup_hook']
        at=hook['entry']-PLAYER_RAM
        self.assertEqual(owner[at:at+8].hex(),hook['after']);owner[at:at+8]=bytes.fromhex(hook['before'])
        self.assertEqual(owner,self.old_files[PLAYER_VROM].extract(self.before))
        self.assertEqual(self.files[PLAYER_RELOC].extract(self.image),self.old_files[PLAYER_RELOC].extract(self.before))
        allowed={CODE_VROM,MODULE,BLOB,PLAYER_VROM,0x19D40}
        self.assertEqual(set(self.files),set(self.old_files))
        for v in set(self.files)-allowed:
            self.assertEqual(self.files[v].extract(self.image),self.old_files[v].extract(self.before),hex(v))
        for key in ('records','kind_readers','inventory_preview','animated_rigs'):
            self.assertEqual(self.e[key],self.old[key])
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.image)

    def test_callbacks_code_and_containing_reservation(self):
        module=bytearray(self.module);previous=self.old_blob[self.old['blob_offset']:self.old['blob_offset']+self.old['bytes']]
        self.assertEqual((len(module),self.old['bytes']),(0xE000,0xD000))
        self.assertEqual(sha256(module),self.e['sha256']);self.assertEqual(zlib.crc32(module),self.e['crc32'])
        self.assertEqual(struct.unpack_from('>4I',module,len(module)-16),(GUARD,)*4)
        self.assertLessEqual(RAM+len(module),self.report['furniture']['bank_pool']['start'])
        self.assertIn('-DAF_V3_EQUIPMENT_BYTES=0xE000u',self.report['startup']['flags'])
        symbols=self.rigs['code']['symbols']
        for table,name in zip(self.e['player_actions']['held_dispatch']['tables'],
                               ('af_v3_held_pinwheel_main','af_v3_held_pinwheel_draw')):
            at=table['offset'];self.assertEqual(sha256(module[at:at+table['bytes']]),table['sha256'])
            self.assertEqual(struct.unpack_from('>I',module,at+88)[0],symbols[name])
            self.assertEqual(struct.unpack_from('>I',module,at+84)[0],0)
            module[at+88:at+92]=bytes(4)
        self.assertEqual(module[:len(previous)],previous)
        n=self.rigs['code']['bytes'];code=(OUTPUT/'held_rigs/code.bin').read_bytes()
        self.assertEqual(module[0xD000:0xD000+n],code)
        self.assertFalse(any(module[0xD000+n:-16]))
        bridge=symbols['af_v3_held_setup_original']-RAM
        displacement=actions.CTOR-(self.rigs['setup_hook']['entry']+8)
        self.assertEqual(symbols['af_v3_held_setup_displacement'],displacement)
        words=(0x3C198014,0x8F393900,0x3C180000|((displacement+0x8000)>>16),
               0x27180000|(displacement&65535),0x0338C823,0x27BDFFD0,0x03200008,0xAFB00024)
        self.assertEqual(module[bridge:bridge+32],struct.pack('>8I',*words))
        for row in self.rigs['source_functions']:
            self.assertTrue(row['sha256']);self.assertGreater(row['bytes'],0)
        stripped,_=reuse_resource_tail(self.image,self.report,self.blob)
        self.assertGreaterEqual(len(stripped),self.e['blob_offset']+self.e['bytes'])

    def test_existing_selections_saves_and_exact_translation_only(self):
        for key in ('save_runtime','furniture','translation_baseline','translation_updates'):
            self.assertEqual(self.report[key],self.prior[key])
        pin=(composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI)
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json')
            catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),112)
            self.assertFalse(any(f'GAFE01-r0/item/{i:04X}' in catalog for i in range(0x224C,0x2254)))
            empty=composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]
            self.assertEqual(sha256(empty),self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin


if __name__=='__main__':unittest.main()
