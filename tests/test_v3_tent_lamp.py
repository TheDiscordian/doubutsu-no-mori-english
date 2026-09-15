"""Actual lamp C and current cartridge ownership/startup integration."""
import copy
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
from aflib import CODE_VROM,CODE_RAM,by_vrom,sha256,n64_checksum
import v3_tent_lamp as runtime
OUTPUT=ROOT/'build/v3-tent-lamp-runtime-02'


class TentLampTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes());cls.lamp=cls.report['tent_lamp']
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.helper=(OUTPUT/'lamp/code.bin').read_bytes()

    def test_sanitized_actual_lamp_c(self):
        with tempfile.TemporaryDirectory(prefix='v3-lamp-') as directory:
            out=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_tent_lamp_test.c'),str(ROOT/'overlays/v3/tent_lamp.c'),
                '-lm','-o',str(out)],check=True,capture_output=True,text=True,timeout=30)
            result=subprocess.run([str(out)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('pass:',result.stdout)

    def test_exact_source_binding_and_relocated_original_owner(self):
        _,code,owner,reloc,extra,lamp=runtime.install(self.native,self.base,self.helper,self.lamp['code'])
        self.assertEqual(owner,self.files[runtime.VROM].extract(self.rom))
        self.assertEqual(reloc,self.files[runtime.RELOC].extract(self.rom))
        self.assertEqual(code,self.files[CODE_VROM].extract(self.rom))
        blob=self.files[runtime.BLOB].extract(self.rom);at=self.lamp['extra_vrom']-runtime.BLOB
        self.assertEqual(extra,blob[at:at+runtime.EXTRA_SIZE]);self.assertEqual(lamp['profile_hooks'],self.lamp['profile_hooks'])
        self.assertEqual(runtime.donor(),self.lamp['donor'])

    def test_sanitized_current_extended_startup(self):
        with tempfile.TemporaryDirectory(prefix='v3-lamp-startup-') as directory:
            out=Path(directory)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_tent_lamp_startup_test.c'),str(ROOT/'runtime/crc32.c'),
                '-o',str(out)],check=True,capture_output=True,text=True,timeout=30)
            result=subprocess.run([str(out)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr);self.assertIn('pass:',result.stdout)

    def test_save_code_retention_and_loaded_boundaries(self):
        blob=self.files[runtime.BLOB].extract(self.rom);old=self.old[runtime.BLOB].extract(self.base)
        source,n,crc,ram=struct.unpack_from('>4I',blob,0xE0);extra=blob[source-runtime.BLOB:source-runtime.BLOB+n]
        self.assertEqual((n,ram),(0x3000,0x8046D000));self.assertEqual(crc,zlib.crc32(extra))
        self.assertEqual(extra[:0xBA0],old[0xF400:0xF400+0xBA0])
        self.assertEqual(extra[0x2FC0:0x2FF0],bytes(48))
        self.assertEqual(extra[0xFF0:0x1000],runtime.words(*([0xAF1AC0DE]*4)))
        self.assertEqual(extra[-16:],runtime.words(*([0xAF1AC0DE]*4)))
        self.assertLessEqual(runtime.ENTRY+len(self.helper),runtime.STATE)
        self.assertEqual(ram+n,0x80470000) # Never touches the furniture tables.

    def test_all_unrelated_data_and_old_physical_owners_preserved(self):
        changed={runtime.BLOB,runtime.MODULE,runtime.VROM,runtime.RELOC,CODE_VROM,0x19D40}
        for v,e in self.old.items():
            if v not in changed:self.assertEqual(self.files[v].extract(self.rom),e.extract(self.base))
        blob=bytearray(self.files[runtime.BLOB].extract(self.rom));old=self.old[runtime.BLOB].extract(self.base)
        blob[4:8]=old[4:8];blob[0xE0:0xF0]=old[0xE0:0xF0];self.assertEqual(blob[:len(old)],old)
        for v in (runtime.VROM,runtime.RELOC):
            e=self.old[v];self.assertEqual(self.rom[e.pstart:e.pend],self.base[e.pstart:e.pend])
            self.assertEqual(self.files[v].index,e.index)
        self.assertFalse(self.lamp['saved_format_changed']);self.assertFalse(self.lamp['saved_profile_changed'])

    def test_invalid_source_bindings_and_code_bounds_fail_closed(self):
        changed=copy.deepcopy(self.lamp['code']);changed['symbols']['native_effect_loaded']+=4
        with self.assertRaises(ValueError):runtime.install(self.native,self.base,self.helper,changed)
        with self.assertRaises(ValueError):runtime.install(self.native,self.base,self.helper[:-4],self.lamp['code'])
        base=bytearray(self.base);base[self.old[CODE_VROM].pstart+0x800984D4-CODE_RAM]^=1
        with self.assertRaises(ValueError):runtime.install(self.native,base,self.helper,self.lamp['code'])

    def test_startup_and_current_cartridge_checksums(self):
        blob=self.files[runtime.BLOB].extract(self.rom);module=self.files[runtime.MODULE].extract(self.rom)
        self.assertEqual(struct.unpack_from('>4I',module,runtime.CONFIG),
            (runtime.BLOB,0xC000,zlib.crc32(blob[:0xC000]),83))
        self.assertLessEqual(self.report['startup']['bytes'],runtime.CONFIG-runtime.STARTUP)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))


if __name__=='__main__':unittest.main()
