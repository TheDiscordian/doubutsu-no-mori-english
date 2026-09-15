"""Current additive tent actor, complete assets, and bounded native integration."""
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
import v3_campsite_exterior as runtime

OUTPUT = ROOT / 'build/v3-campsite-exterior-runtime-01'


class CampsiteExteriorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT / 'build.json').read_bytes())
        cls.base = (runtime.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.rom)
        cls.previous = cls.old[BLOB].extract(cls.base)
        cls.package = cls.blob[runtime.PACKAGE:runtime.PACKAGE + runtime.PACKAGE_SIZE]
        at = runtime.PACKET - runtime.PACKAGE_RAM
        cls.packet = cls.package[at:at + 0x1F0]

    def test_sanitized_complete_callbacks_and_startup(self):
        with tempfile.TemporaryDirectory(prefix='af-v3-campsite-exterior-') as directory:
            directory = Path(directory)
            exterior, shadow = 0x0248A000 - BLOB, 0x0248C000 - BLOB
            inputs = [('packet', self.packet), ('exterior', self.blob[exterior:exterior + 6960]),
                      ('shadow', self.blob[shadow:shadow + 800])]
            for name, data in inputs:
                (directory / name).write_bytes(data)
            for name, extras, args in (
                ('v3_campsite_exterior_test.c', [], [str(directory / n) for n, _ in inputs]),
                ('v3_accessory_startup_test.c', ['-DAF_V3_ABI=72', '-DAF_V3_ACCESSORY_BYTES=192528',
                 '-DAF_V3_ACCESSORY_VROM=0x02400000', '-DAF_V3_WESTERN_LARGE=1',
                 '-DAF_V3_CAMPSITE=1', str(ROOT / 'runtime/crc32.c')], [])):
                binary = directory / name
                compiled = subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-omit-frame-pointer', str(ROOT / 'tests' / name),
                    *extras, '-o', str(binary)], capture_output=True, text=True)
                self.assertEqual(compiled.returncode, 0, compiled.stderr)
                run = subprocess.run([str(binary), *args], capture_output=True, text=True, timeout=20)
                self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
                self.assertIn('pass', run.stdout)

    def test_complete_resident_packet_and_unchanged_originals(self):
        self.assertEqual(struct.unpack_from('>4I', self.packet), (0x41465445,1,0xCA,0x5849))
        self.assertEqual(struct.unpack_from('>8I', self.packet, 0x20), (0,0,0,0,0,runtime.PACKET+0x40,0,0))
        symbols = self.report['campsite_exterior']['code']['symbols']
        self.assertEqual(struct.unpack_from('>HHIHH6I', self.packet, 0x40), (0xCA,0,0,0x5849,3,0x2D8,
            symbols['af_v3_campsite_exterior_ct'], symbols['af_v3_campsite_exterior_dt'],
            symbols['af_v3_campsite_exterior_init'], symbols['af_v3_campsite_exterior_dw'],0))
        self.assertEqual(self.packet[0x80:0x94].hex(), '00000023040000000078000000dc000001000000')
        self.assertEqual(self.packet[-16:], bytes.fromhex('AFC7E17E') * 4)
        old = self.previous[runtime.PACKAGE:runtime.PACKAGE + runtime.PACKAGE_SIZE]
        restored = bytearray(self.package)
        for address, size in ((runtime.ENTRY, self.report['campsite_exterior']['code']['bytes']),
                              (runtime.PACKET, len(self.packet))):
            at = address - runtime.PACKAGE_RAM
            self.assertEqual(old[at:at+size], bytes(size))
            restored[at:at+size] = bytes(size)
        self.assertEqual(restored, old)
        self.assertLessEqual(runtime.ENTRY + self.report['campsite_exterior']['code']['bytes'], 0x804A1000)
        self.assertEqual(self.report['campsite_exterior']['additional_resident_bytes'], 0)
        for row in self.report['campsite']['resources']:
            at = row['vrom'] - BLOB
            self.assertEqual(sha256(self.blob[at:at+row['bytes']]), row['sha256'])
        code, old_code = self.files[CODE_VROM].extract(self.rom), self.old[CODE_VROM].extract(self.base)
        at = 0x80100C90 - CODE_RAM
        self.assertEqual(code[at:at+201*32], old_code[at:at+201*32])
        native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(self.files[0x8D3D00].extract(self.rom), by_vrom(native)[0x8D3D00].extract(native))
        self.assertEqual(self.blob[0x20:0xE0], self.previous[0x20:0xE0])

    def test_reviewed_hooks_relocation_and_dma_ownership(self):
        changed = {v for v in self.files if self.files[v].extract(self.rom) != self.old[v].extract(self.base)}
        self.assertEqual(changed, {0x19D40,BLOB,MODULE,CODE_VROM,runtime.STRUCTURE,runtime.RELOC})
        for vrom, ram in ((CODE_VROM,CODE_RAM), (runtime.STRUCTURE,runtime.STRUCTURE_RAM)):
            data = bytearray(self.files[vrom].extract(self.rom))
            for row in self.report['campsite_exterior']['hooks']:
                if ram <= row['address'] < ram + len(data):
                    at, after, before = row['address']-ram, bytes.fromhex(row['after']), bytes.fromhex(row['before'])
                    self.assertEqual(data[at:at+len(after)], after)
                    data[at:at+len(before)] = before
            self.assertEqual(data, self.old[vrom].extract(self.base))
        original, changed = (self.old[runtime.RELOC].extract(self.base), self.files[runtime.RELOC].extract(self.rom))
        count = struct.unpack_from('>I',original,16)[0]
        words = list(struct.unpack_from('>'+str(count)+'I', original,20))
        self.assertEqual(self.report['campsite_exterior']['removed_relocations'], [0x45001528,0x46001530])
        keep = [v for v in words if v not in (0x45001528,0x46001530)]
        self.assertEqual(struct.unpack_from('>I',changed,16)[0],len(keep))
        self.assertEqual(list(struct.unpack_from('>'+str(len(keep))+'I',changed,20)),keep)
        self.assertEqual(changed[:16],original[:16]); self.assertEqual(changed[-4:],original[-4:])
        self.assertEqual(changed[20+4*len(keep):-4],bytes(len(changed)-24-4*len(keep)))
        directory = bytearray(self.files[0x19D40].extract(self.rom))
        old_directory = self.old[0x19D40].extract(self.base)
        for vrom in (BLOB,runtime.STRUCTURE,runtime.RELOC):
            at = DMA_START - 0x19D40 + self.files[vrom].index*16
            directory[at:at+16] = old_directory[at:at+16]
        self.assertEqual(directory,old_directory)

    def test_checksums_bounds_and_accurate_capabilities(self):
        self.assertEqual(struct.unpack_from('>4I',self.blob,0xF0),
            (BLOB+runtime.PACKAGE,runtime.PACKAGE_SIZE,zlib.crc32(self.package),runtime.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>4I',self.files[MODULE].extract(self.rom),CONFIG),
            (BLOB,0xC000,zlib.crc32(self.blob[:0xC000]),72))
        self.assertEqual(sha256(self.packet),self.report['campsite_exterior']['packet_sha256'])
        self.assertEqual(sha256(self.package),self.report['campsite']['package_sha256'])
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>II',self.rom,0x10),n64_checksum(self.rom))
        self.assertEqual(len(self.files),3389); self.assertEqual(self.rom[DMA_END-16:DMA_END],bytes(16))
        for key in ('event_installed','acquisition_installed','web_patcher_enabled',
                    'saved_format_changed','saved_profile_changed'):
            self.assertFalse(self.report['campsite_exterior'][key])


if __name__ == '__main__':
    unittest.main()
