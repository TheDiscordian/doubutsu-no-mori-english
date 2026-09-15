"""Changed calendar/index/startup owners and current cartridge composition."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, DMA_END, by_vrom, n64_checksum, sha256
from v3_asset_loader import BLOB, MODULE, CONFIG
import v3_campsite_calendar as runtime

OUTPUT = ROOT / 'build/v3-campsite-calendar-runtime-02'


class CampsiteCalendarTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (runtime.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_bytes())
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob, cls.previous = cls.files[BLOB].extract(cls.rom), cls.old[BLOB].extract(cls.base)
        cls.package = cls.blob[runtime.PACKAGE:runtime.PACKAGE+runtime.PACKAGE_SIZE]

    def test_native_index_consumers_and_retained_holidays(self):
        code = bytearray(self.files[CODE_VROM].extract(self.rom))
        old = self.old[CODE_VROM].extract(self.base)
        hooks = self.report['campsite_calendar']['hooks']
        self.assertEqual(len(hooks), 40)
        for row in hooks:
            at = row['address'] - CODE_RAM
            self.assertEqual(code[at:at+4], bytes.fromhex(row['after']))
            code[at:at+4] = bytes.fromhex(row['before'])
        self.assertEqual(code, old)
        self.assertEqual(self.rom[DMA_START:DMA_END], self.base[DMA_START:DMA_END])
        changed = {v for v in self.files if self.files[v].extract(self.rom) != self.old[v].extract(self.base)}
        self.assertEqual(changed, {BLOB, MODULE, CODE_VROM})
        self.assertEqual(len(self.files), 3389)
        for start, end in ((0x80104B60,0x80104F2C), (0x8007E60C,0x8007E714),
                           (0x8007DD84,0x8007DF04)):
            self.assertEqual(self.files[CODE_VROM].extract(self.rom)[start-CODE_RAM:end-CODE_RAM],
                             old[start-CODE_RAM:end-CODE_RAM])

    def test_complete_package_extension_and_bounds(self):
        old = self.previous[runtime.PACKAGE:runtime.PACKAGE+runtime.OLD_SIZE]
        retained = bytearray(self.package[:runtime.OLD_SIZE])
        struct.pack_into('>I',retained,8,runtime.OLD_SIZE)
        self.assertEqual(retained, old)
        self.assertEqual(self.blob[runtime.PACKAGE+runtime.PACKAGE_SIZE:],
                         self.previous[runtime.PACKAGE+runtime.PACKAGE_SIZE:])
        self.assertEqual(self.package[-16:],old[-16:])
        self.assertEqual(struct.unpack_from('>4I',self.blob,0xF0),
            (BLOB+runtime.PACKAGE,runtime.PACKAGE_SIZE,zlib.crc32(self.package),runtime.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>4I',self.files[MODULE].extract(self.rom),CONFIG),
            (BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),73))
        for address, folder in ((runtime.EVENT_CODE,'event'),(runtime.CALENDAR_CODE,'calendar')):
            data = (OUTPUT / folder / 'code.bin').read_bytes()
            at = address-runtime.PACKAGE_RAM
            self.assertEqual(self.package[at:at+len(data)],data)
        at = runtime.INDEX-runtime.PACKAGE_RAM
        self.assertEqual(self.package[at:at+128],b'\xFF'*128)
        at = runtime.PACKET-runtime.PACKAGE_RAM
        self.assertEqual(struct.unpack_from('>4I',self.package,at),(0x41464345,1,70,runtime.INDEX))
        self.assertEqual(self.package[at+0x20:at+0x2C].hex(),'06be004906b8000e00000018')
        self.assertEqual(sha256(self.package[at:at+256]),self.report['campsite_calendar']['packet_sha256'])
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>II',self.rom,0x10),n64_checksum(self.rom))
        self.assertEqual(self.report['campsite_calendar']['additional_resident_bytes'],4080)
        self.assertFalse(self.report['campsite_calendar']['manager_installed'])
        self.assertFalse(self.report['campsite_calendar']['acquisition_installed'])

    def test_sanitized_expanded_startup_and_instruction_cache(self):
        with tempfile.TemporaryDirectory(prefix='af-camper-calendar-') as directory:
            binary = Path(directory) / 'startup'
            result = subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-DAF_V3_ABI=73','-DAF_V3_ACCESSORY_BYTES=196608','-DAF_V3_ACCESSORY_VROM=0x02400000',
                '-DAF_V3_WESTERN_LARGE=1','-DAF_V3_CAMPSITE=1','-DAF_V3_CAMPER_CALENDAR=1',
                str(ROOT/'tests/v3_accessory_startup_test.c'),str(ROOT/'runtime/crc32.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            run = subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            self.assertIn('pass',run.stdout)


if __name__ == '__main__':
    unittest.main()
