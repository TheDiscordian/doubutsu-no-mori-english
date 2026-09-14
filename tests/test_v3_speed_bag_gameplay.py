"""Current score-letter, catalogue, stock, and save-profile integration."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import apply_ups,by_vrom,sha256,u32
from v3_asset_loader import BLOB,compose
import v3_hra_mail as mail
import v3_shops as shops

OUTPUT=ROOT/'build/v3-speed-bag-gameplay-02'


class ProfileTests(unittest.TestCase):
    def test_actual_sanitized_profile_codec(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-speed-profile-') as directory:
            binary=Path(directory)/'test'
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_speed_bag_profile_test.c'),'-o',str(binary)],
                check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('missing-profile rejection pass',result.stdout)


@unittest.skipUnless((OUTPUT/'build.json').exists(),'Current speed-bag integration cartridge required')
class GameplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((OUTPUT/'build.json').read_text())
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.files=by_vrom(cls.rom)
        cls.previous=(ROOT/'build/v3-speed-bag-hra-01/animal-forest-v3-asset-loader.z64').read_bytes()
        cls.old=by_vrom(cls.previous)
        cls.base=(ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_complete_additive_letter_names_and_loader_reconstruction(self):
        module=bytearray(self.old[0x02800000].extract(self.previous))
        source=self.old[mail.VROM].extract(self.previous)
        data,report=mail.install(source,module,self.rel,self.symbols)
        self.assertEqual(data,self.files[mail.VROM].extract(self.rom))
        self.assertEqual(report,self.report['hra']['score_letters'])
        actual_module=self.files[0x02800000].extract(self.rom)
        self.assertEqual(module[0x48:0x68],actual_module[0x48:0x68])
        table=data[mail.IMAGE:report['image_bytes']]
        self.assertEqual(table[:1430],source[mail.TABLE:mail.TABLE+1430])
        self.assertEqual(table[1430:],b'boxing    boxing          ')
        self.assertEqual(u32(data,0x2A04),0x24020037)
        self.assertEqual(u32(actual_module,0x60),zlib.crc32(data))
        self.assertLessEqual(report['image_bytes'],65536)
        for at in (0x2600,0x2A28,0x2834,0x2848,0x2A10,0x2B68):
            self.assertNotEqual(data[at:at+4],source[at:at+4])

    def test_reject_changed_complete_creator_or_configuration(self):
        module=bytearray(self.old[0x02800000].extract(self.previous))
        source=bytearray(self.old[mail.VROM].extract(self.previous));source[0]^=1
        with self.assertRaises(ValueError):mail.install(source,module,self.rel,self.symbols)
        source=self.old[mail.VROM].extract(self.previous);module[0x48]^=1
        with self.assertRaises(ValueError):mail.install(source,module,self.rel,self.symbols)

    def test_actual_donor_order_stock_lists_and_original_retention(self):
        imports=self.report['catalogue']['imports']
        self.assertEqual([r['item_id'] for r in imports],['3350','3224','32B8'])
        self.assertEqual(imports[0]['donor_position'],175)
        cat=self.report['catalogue']
        self.assertEqual(cat['total_rows'],439)
        self.assertLessEqual(cat['conservative_pool_required'],cat['pool_reserved'])
        goods,table,rows=shops.goods(self.base,self.rel,self.symbols,imports)
        self.assertEqual(goods,self.files[shops.VROM].extract(self.rom))
        self.assertEqual(table,0x394)
        pointers=struct.unpack_from('>12I',goods,table)
        self.assertEqual(goods[0xCA:0xD0],bytes.fromhex('32B833500000'))
        self.assertEqual(pointers[1]&0xFFFFFF,0xD0)
        self.assertEqual([r for r in rows if r['item_id']=='3350'][0]['group'],0)
        old=self.old[shops.VROM].extract(self.previous)
        self.assertEqual(goods[:0xCA],old[:0xCA])
        with self.assertRaises(ValueError):shops.goods(self.base,self.rel,self.symbols,imports*2)

    def test_only_new_profile_bit_and_neutral_feng_shui(self):
        prior=json.loads((ROOT/'build/v3-speed-bag-hra-01/build.json').read_text())
        old=bytearray.fromhex(prior['save_runtime']['profile_hex'])
        self.assertEqual(old[58]&16,0);old[58]|=16
        actual=bytes.fromhex(self.report['save_runtime']['profile_hex'])
        self.assertEqual(actual,old)
        prefix=self.files[BLOB].extract(self.rom)[:0xC000]
        self.assertEqual(prefix[0x20:0xE0],actual)
        self.assertEqual(u32(prefix,0x7134),1) # Private gameplay is enabled; the patcher is not.
        self.assertTrue(self.report['speed_bag']['enabled'])
        self.assertFalse(self.report['speed_bag']['selectable'])
        self.assertTrue(self.report['speed_bag']['saved_profile_included'])
        row=next(r for r in self.report['feng_shui']['imports'] if r['item_id']=='3350')
        self.assertEqual((row['metadata'],row['colour']),('0000','none'))

    def test_current_cartridge_and_import_free_composition(self):
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        moved={int(v,16):int(t,16) for v,t in self.report['relocated_resources'].items()}
        changed={int(v,16):self.files[moved.get(int(v,16),int(v,16))].extract(self.rom)
                 for v in self.report['changed_resources']}
        added={int(v,16):self.files[int(v,16)].extract(self.rom) for v in self.report['added_resources']}
        resized=tuple(int(v,16) for v in self.report['resized_resources'])
        self.assertEqual(compose(native,self.base,changed,added,resized=resized,relocated=moved),self.rom)
        self.assertEqual(compose(native,self.base,{},{}),self.base)
        self.assertEqual(apply_ups(native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)

    def test_enablement_retains_native_tested_code_and_resources(self):
        tested=(ROOT/'build/v3-speed-bag-gameplay-01/animal-forest-v3-asset-loader.z64').read_bytes()
        tested_files=by_vrom(tested)
        expected=bytearray(tested_files[BLOB].extract(tested))
        struct.pack_into('>I',expected,4,49)
        struct.pack_into('>I',expected,0x7134,1)
        self.assertEqual(self.files[BLOB].extract(self.rom),expected)
        for v,entry in self.files.items():
            if v not in (0x02800000,BLOB):
                self.assertEqual(entry.extract(self.rom),tested_files[v].extract(tested))
        expected_module=bytearray(tested_files[0x02800000].extract(tested))
        self.assertEqual(u32(expected_module,0x60C0),0x24020030)
        struct.pack_into('>I',expected_module,0x60C0,0x24020031) # Compiled startup ABI check.
        struct.pack_into('>II',expected_module,0x63E8,zlib.crc32(expected[:0xC000]),49)
        self.assertEqual(self.files[0x02800000].extract(self.rom),expected_module)


if __name__=='__main__':unittest.main()
