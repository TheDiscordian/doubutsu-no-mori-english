"""Source-derived loose-item rotation, installed hooks, and optional composition."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups,DMA_START
from v3_asset_loader import BLOB,MODULE,CODE_VROM
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
import v3_room_goods as goods


class GoodsSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base,cls.prior=inputs(ROOT/'build/v3-switched-joint-imports-03/profile-runtime/build-lock.json')
        cls.files=by_vrom(cls.base);cls.native=cls.files[goods.VROM].extract(cls.base)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.contract=goods.rotation_contract(cls.source,cls.native)

    def test_complete_category_source_and_changed_input_guards(self):
        c=self.contract
        self.assertEqual(len(c['donor_rows']),90);self.assertEqual(len(c['native_rows']),34)
        self.assertEqual((c['mask_low'],c['mask_high']),(0xEF000FD9,3))
        self.assertEqual([r['index'] for r in c['native_rows'] if not r['source_rows']],[1,2,23])
        for row in c['functions'].values():
            bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
            bad.rel[self.source.sections[1][0]+row['offset']]^=1
            with self.assertRaisesRegex(ValueError,'dependency'):goods.rotation_contract(bad,self.native)
        bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
        bad.rel[self.source.sections[4][0]+goods.TABLE_AT+36]^=1
        with self.assertRaisesRegex(ValueError,'drawing table'):goods.rotation_contract(bad,self.native)
        bad=bytearray(self.native);bad[0xFB0]^=1
        with self.assertRaisesRegex(ValueError,'owner'):goods.rotation_contract(self.source,bad)

    def test_actual_donor_grid_and_native_adapters_under_sanitizers(self):
        text=(ROOT/'local/ac-decomp/src/actor/ac_shop_goods.c').read_text();functions=[]
        for prefix,name in [('static s16 ','Shop_Goods_Actor_single_get_angle_y'),
                            ('static void ','Shop_Goods_Actor_single_set_angle_y')]:
            start=text.index(prefix+name+'(');end=text.index('\n}',start)+2;functions.append(text[start:end])
        with tempfile.TemporaryDirectory(prefix='v3-room-goods-') as directory:
            directory=Path(directory);binary=directory/'test'
            (directory/'donor_goods.inc').write_text('\n'.join(functions))
            (directory/'goods_flags.inc').write_text(
                f'#define AF_GOODS_ROTATE_LOW 0x{self.contract["mask_low"]:X}u\n'
                f'#define AF_GOODS_ROTATE_HIGH 0x{self.contract["mask_high"]:X}u\n'
                'static const int expected_rotation[34]={'+','.join(str(int(r['rotate'])) for r in self.contract['native_rows'])+'};\n')
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                '-fno-omit-frame-pointer','-fno-pie','-no-pie','-I'+str(directory),
                str(ROOT/'tests/v3_room_goods_test.c'),'-o',str(binary)]
            result=subprocess.run(command,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('768 donor grid comparisons',result.stdout)


class GoodsInstalledTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_GOODS_BUILD','build/v3-room-goods-runtime-03')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.oldfiles=by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.image);cls.oldblob=cls.oldfiles[BLOB].extract(cls.base)

    def test_installed_hooks_loading_reservations_and_unchanged_content(self):
        e=self.report['equipment_resources'];g=e['room_goods'];p=g['packet']
        code=self.blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(code),p['sha256']);self.assertEqual(zlib.crc32(code),p['crc32'])
        self.assertEqual(p['ram'],goods.CODE_RAM);self.assertLessEqual(p['bytes'],4096)
        patched,relocation,binding=goods.patch_native(self.oldfiles[goods.VROM].extract(self.base),
            self.oldfiles[goods.RELOC].extract(self.base),g['compiled']['symbols'])
        self.assertEqual(self.files[goods.VROM].extract(self.image),patched)
        self.assertEqual(self.files[goods.RELOC].extract(self.image),relocation)
        self.assertEqual(sorted(binding['removed_relocations']),[0x44000A2C,0x44000B34])
        bad=bytearray(self.oldfiles[goods.RELOC].extract(self.base));bad[20]^=1
        with self.assertRaises(ValueError):goods.patch_native(self.oldfiles[goods.VROM].extract(self.base),bad,g['compiled']['symbols'])
        self.assertTrue(g['installed']);self.assertFalse(g['occupied_table_movement_enabled'])
        self.assertFalse(g['native_execution_tested'] or g['saved_format_changed'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],5120)
        self.assertEqual(self.report['runtime_abi'],self.prior['runtime_abi']+1)
        from v3_surface_items import BOOT,BOOT_END
        module=self.blob[e['blob_offset']:e['blob_offset']+e['bytes']]
        boot=self.report['room_surfaces']['items']['bootstrap']['code'];start=BOOT-e['ram']
        self.assertEqual(sha256(module[start:start+boot['bytes']]),boot['sha256'])
        self.assertFalse(any(module[start+boot['bytes']:BOOT_END-e['ram']]))
        self.assertEqual(e['surface_bootstrap'],self.report['room_surfaces']['items']['bootstrap'])
        self.assertEqual(sha256(module),e['sha256']);self.assertEqual(zlib.crc32(module),e['crc32'])
        for define in (f'-DAF_ROOM_GOODS_VROM=0x{p["vrom"]:X}u',f'-DAF_ROOM_GOODS_CRC=0x{p["crc32"]:X}u',
                       f'-DAF_ROOM_GOODS_BYTES=0x{p["bytes"]:X}u'):
            self.assertIn(define,boot['flags'])
        self.assertLessEqual(self.report['startup']['bytes'],992)
        for vrom,entry in self.oldfiles.items():
            if vrom<=DMA_START<entry.vend:
                self.assertEqual(self.files[vrom].extract(self.image)[:DMA_START-vrom],entry.extract(self.base)[:DMA_START-vrom])
                continue  # Resource addresses change in the guarded DMA directory.
            if vrom not in (BLOB,MODULE,goods.VROM,goods.RELOC):
                self.assertEqual(self.files[vrom].extract(self.image),entry.extract(self.base),hex(vrom))
        for key in ('save_codec','save_runtime','furniture','translation_baseline','staged_furniture'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(e['room_rigs'],self.prior['equipment_resources']['room_rigs'])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_optional_browser_composition_retains_loading_and_existing_choices(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
