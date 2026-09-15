"""Current camper ownership, native hook, package retention, and cache checks."""
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
from aflib import CODE_RAM,CODE_VROM,DMA_START,DMA_END,by_vrom,sha256,n64_checksum
from v3_asset_loader import BLOB,MODULE,CONFIG
import v3_camper as runtime
OUTPUT=ROOT/'build/v3-camper-runtime-02'

class CamperTests(unittest.TestCase):
    def test_current_package_and_native_hook_preserve_other_owners(self):
        base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        report=json.loads((OUTPUT/'build.json').read_bytes())
        old,files=by_vrom(base),by_vrom(rom)
        self.assertEqual(files,old)
        self.assertEqual(rom[DMA_START:DMA_END],base[DMA_START:DMA_END])
        changed={v for v in files if files[v].extract(rom)!=old[v].extract(base)}
        self.assertEqual(changed,{BLOB,MODULE,CODE_VROM})
        code=bytearray(files[CODE_VROM].extract(rom)); hook=report['camper']['hook']
        at=hook['address']-CODE_RAM
        self.assertEqual(code[at:at+8],bytes.fromhex(hook['after']))
        code[at:at+8]=bytes.fromhex(hook['before'])
        self.assertEqual(code,old[CODE_VROM].extract(base))
        blob=files[BLOB].extract(rom); restored=bytearray(blob); previous=old[BLOB].extract(base)
        for address,folder,key in ((runtime.REGISTER,'register','registration'),(runtime.READER,'reader','reader')):
            data=(OUTPUT/folder/'code.bin').read_bytes(); at=runtime.PACKAGE+address-runtime.PACKAGE_RAM
            self.assertEqual(blob[at:at+len(data)],data)
            self.assertEqual(sha256(data),report['camper'][key]['sha256'])
            restored[at:at+len(data)]=bytes(len(data))
        at=runtime.PACKAGE+runtime.OWNER-runtime.PACKAGE_RAM
        self.assertEqual(struct.unpack_from('>4I',blob,at),(0x41464341,1,0x560,0xD08F))
        self.assertEqual(blob[at+0x20:at+0x548],bytes(0x528))
        self.assertEqual(blob[at+0x550:at+0x560],bytes.fromhex('AFCA11ED')*4)
        restored[at:at+runtime.OWNER_SIZE]=bytes(runtime.OWNER_SIZE)
        at=runtime.PACKAGE+runtime.TRAMPOLINE-runtime.PACKAGE_RAM
        self.assertEqual(blob[at:at+16],bytes.fromhex(report['camper']['trampoline_hex']))
        restored[at:at+16]=bytes(16); restored[4:8]=previous[4:8]; restored[0xF8:0xFC]=previous[0xF8:0xFC]
        self.assertEqual(restored,previous)
        package=blob[runtime.PACKAGE:runtime.PACKAGE+runtime.PACKAGE_SIZE]
        self.assertEqual(sha256(package),report['camper']['package_sha256'])
        self.assertEqual(struct.unpack_from('>4I',blob,0xF0),
            (BLOB+runtime.PACKAGE,runtime.PACKAGE_SIZE,zlib.crc32(package),runtime.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>4I',files[MODULE].extract(rom),CONFIG),
            (BLOB,0xC000,zlib.crc32(blob[:0xC000]),74))
        self.assertEqual(struct.unpack_from('>II',rom,0x10),n64_checksum(rom))
        self.assertEqual(sha256(rom),report['output_sha256'])

    def run_sanitized(self,sources,defines=()):
        with tempfile.TemporaryDirectory(prefix='af-camper-') as directory:
            binary=Path(directory)/'test'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                *('-D'+d for d in defines),*(str(ROOT/s) for s in sources),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('pass',result.stdout)

    def test_complete_owner_and_reader_sanitized(self):
        self.run_sanitized(('tests/v3_camper_test.c','overlays/v3/camper.c','overlays/v3/camper_reader.c'))

    def test_startup_covers_both_new_code_ranges_and_original_trampoline(self):
        self.run_sanitized(('tests/v3_accessory_startup_test.c','runtime/crc32.c'),
            ('AF_V3_ABI=74','AF_V3_ACCESSORY_BYTES=196608','AF_V3_ACCESSORY_VROM=0x02400000',
             'AF_V3_WESTERN_LARGE=1','AF_V3_CAMPSITE=1','AF_V3_CAMPER=1'))

if __name__=='__main__': unittest.main()
