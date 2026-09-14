"""Current combined Punchy house/default construction, bounds, and dependencies."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256, u32
from v3_asset_loader import BLOB, MODULE, compose
import v3_villager_houses as houses
from v3_villager_defaults import imported_outfit

OUTPUT = ROOT/'build/v3-punchy-house-02'


class DefaultsTests(unittest.TestCase):
    def test_actual_sanitized_default_and_clothing_code(self):
        with tempfile.TemporaryDirectory(prefix='v3-punchy-') as temp:
            executable = Path(temp)/'check'
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_punchy_defaults_test.c'),'-o',str(executable)],check=True)
            result = subprocess.run([str(executable)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('actual garment checks, and no-write rejection pass',result.stdout)


class HouseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.files, cls.original = by_vrom(cls.rom), by_vrom(cls.native)
        cls.blob = cls.files[BLOB].extract(cls.rom)
        cls.donor = {'rel':(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                     'forest_2nd.arc':(ROOT/'build/gamecube/files/forest_2nd.arc').read_bytes()}
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()

    def test_complete_source_bound_house_conversion_and_rotations(self):
        code = bytearray(by_vrom(self.base)[CODE_VROM].extract(self.base))
        changes, report = houses.install(self.native,self.base,code,self.donor,self.symbols,
            {'imports':self.report['catalogue']['imports']},punchy=True)
        self.assertEqual(report,self.report['villager_houses'])
        for v,target in ((houses.HOUSE,houses.HOUSE),(houses.FOREGROUND,houses.EXPANDED_FOREGROUND)):
            actual = self.files[target].extract(self.rom)
            self.assertEqual(actual,changes[v])
            original = self.original[v].extract(self.native)
            self.assertEqual(actual[:len(original)],original)
            self.assertEqual(self.files[target].index,self.original[v].index)
        table = changes[houses.HOUSE]
        self.assertEqual(table[234*8:235*8],bytes.fromhex('00003f2103780379'))
        self.assertEqual(table[237*8:238*8],bytes.fromhex('02012714037e037f'))
        self.assertEqual(table[235*8:237*8],bytes(16))
        fg = changes[houses.FOREGROUND]
        self.assertEqual(len(fg),225848)
        layers = houses.layers(fg)
        self.assertEqual(set(layers)-set(houses.layers(self.original[houses.FOREGROUND].extract(self.native))),
                         {888,889,894,895})
        self.assertEqual(struct.unpack_from('>H',layers[894],2+(6+6*16)*2)[0],0x3352)
        self.assertEqual(struct.unpack_from('>H',layers[895],2+(1+5*16)*2)[0],0x2A23)
        actual_code = self.files[CODE_VROM].extract(self.rom)
        for row in report['code_patches']:
            at = int(row['address'],16)-CODE_RAM
            self.assertEqual(actual_code[at:at+4],code[at:at+4])

    def test_native_resource_retention_and_relocated_bounds(self):
        h = self.report['villager_houses']
        self.assertNotIn(houses.FOREGROUND,self.files)
        self.assertEqual(h['foreground_vrom'],'03F60000')
        self.assertEqual(h['foreground_extra_allocation_bytes'],2072)
        self.assertEqual(h['foreground_records'],436)
        code = self.files[CODE_VROM].extract(self.rom)
        pair = lambda hi,lo:(u32(code,hi-CODE_RAM)&65535)*65536 + struct.unpack_from('>h',code,lo-CODE_RAM+2)[0]
        start,end = pair(0x800860FC,0x80086108),pair(0x80086100,0x80086104)
        self.assertEqual((start,end),(0x03F60000,0x03F97238))
        self.assertLess(end,houses.FOREGROUND_LIMIT)
        for v in (0x011E2000,0x0182A000,0x017A1000,0x00B68000,0x00B88000):
            self.assertEqual(self.files[v].extract(self.rom),self.original[v].extract(self.native))

    def test_exact_outfit_profile_code_reservations_and_disabled_move_ins(self):
        previous = json.loads((ROOT/'build/v3-speed-bag-gameplay-02/build.json').read_text())
        self.assertEqual(self.report['save_runtime']['profile_hex'],previous['save_runtime']['profile_hex'])
        self.assertEqual(self.blob[0x1E60:0x1E74],bytes(20))
        self.assertEqual(self.blob[0x2E7E:0x2E80],bytes.fromhex('34BF'))
        self.assertEqual(self.report['villager_selection']['content_ready'],['E0EA','E0ED'])
        self.assertFalse(self.report['new_villager_ids_enabled'])
        self.assertTrue(self.report['clothing']['punchy_defaults_enabled'])
        self.assertEqual(u32(self.blob,4),50)
        for part,at,limit in (('villager',0x4000,0x4600),('villager_selection',0x3400,0x3A00)):
            code = (OUTPUT/part/'code.bin').read_bytes()
            self.assertEqual(self.blob[at:at+len(code)],code)
            self.assertLessEqual(at+len(code),limit)
        extra = (OUTPUT/'villager/defaults.bin').read_bytes()
        self.assertEqual(self.blob[0x32E0:0x32E0+len(extra)],extra)
        self.assertLessEqual(len(extra),0x120)
        old_rom = (ROOT/'build/v3-speed-bag-gameplay-02/animal-forest-v3-asset-loader.z64').read_bytes()
        old_blob = by_vrom(old_rom)[BLOB].extract(old_rom)
        for start,end in ((0x3000,0x32E0),(0x4600,0x4700),(0x3A00,0x4000),(0x6F00,0x7180),(0xC000,len(self.blob))):
            self.assertEqual(self.blob[start:end],old_blob[start:end])

    def test_reject_missing_rotated_item_without_mutating_code(self):
        metadata = copy.deepcopy(self.report['villager_houses'])
        code = bytearray(by_vrom(self.base)[CODE_VROM].extract(self.base)); before = bytes(code)
        with patch.object(houses,'metadata',return_value=metadata):
            with self.assertRaisesRegex(ValueError,'Punchy house dependency'):
                houses.install(self.native,self.base,code,self.donor,self.symbols,
                               self.report['furniture'],punchy=True)
        self.assertEqual(code,before)

    def test_reject_unselected_outfit_without_mutation(self):
        blob = bytearray(self.blob[:0xC000]);blob[0x2E7E:0x2E80]=bytes(2)
        text = copy.deepcopy(self.report['villager_text'])
        row = text['imports'][1];row['initial_defaults_applied']=False
        row['record_sha256']=sha256(blob[0x2E60:0x2E80])
        blob[0xD7]&=0x7F;before=bytes(blob)
        with self.assertRaisesRegex(ValueError,'selected clothing dependency'):
            imported_outfit(blob,text,self.blob[0xF000:0xF220],self.blob[0x2820:0x2840],
                            self.report['clothing']['imports'][0])
        self.assertEqual(blob,before)

    def test_current_compose_patch_and_exact_import_free_output(self):
        r = self.report
        moves = {int(v,16):int(t,16) for v,t in r['relocated_resources'].items()}
        changed = {int(v,16):self.files[moves.get(int(v,16),int(v,16))].extract(self.rom)
                   for v in r['changed_resources']}
        added = {int(v,16):self.files[int(v,16)].extract(self.rom) for v in r['added_resources']}
        resized = tuple(int(v,16) for v in r['resized_resources'])
        self.assertEqual(compose(self.native,self.base,changed,added,resized=resized,relocated=moves),self.rom)
        self.assertEqual(compose(self.native,self.base,{},{}),self.base)
        self.assertEqual(apply_ups(self.native,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(sha256(self.rom),r['output_sha256'])


if __name__=='__main__':unittest.main()
