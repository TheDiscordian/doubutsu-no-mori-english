"""Bounded format-five envelope checks; no device I/O or cartridge installation."""
import json
from pathlib import Path
import random
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256,yaz0_decode
from flash_mail import checksum,locations

PAYLOAD=0xF980


def canonical(payload):
    bank=bytearray(payload[:PAYLOAD])+bytearray(0x680)
    bank[4:8]=b'NAF3';bank[8:10]=bank[0x2F68:0x2F6A]=b'\x30\x19'
    bank[0x12:0x14]=bytes(2)
    struct.pack_into('>4sHHII',bank,PAYLOAD,b'AFS3',4,0x680,3,zlib.crc32(bank[:PAYLOAD]))
    struct.pack_into('>I',bank,PAYLOAD+16,zlib.crc32(bank[PAYLOAD:]))
    struct.pack_into('>H',bank,0x12,(-checksum(bank[:PAYLOAD]))&65535)
    return bytes(bank)


class CompressedSaveTests(unittest.TestCase):
    def test_lossless_capacity_malformed_streams_and_atomic_pack(self):
        rng=random.Random(513)
        # Read existing storage as input DATA, without launching or retesting an old ROM.
        old=(ROOT/'build/rc2-existing-save-diagnostic-01/test.flash').read_bytes()[:65536]
        self.assertEqual(old[4:8],b'NAFJ');self.assertEqual(checksum(old[:PAYLOAD]),0)
        dense=bytearray(old[:PAYLOAD])
        for mail in locations():
            at=mail['offset'];dense[at:at+mail['bytes']]=bytes(rng.randrange(32,127) for _ in range(mail['bytes']))
        for at in range(0x62A8,0x9EA8,2):struct.pack_into('>H',dense,at,rng.randrange(0x4000))
        inputs=[('zero',canonical(bytes(PAYLOAD))),('town',canonical(old)),('dense',canonical(dense)),
                ('incompressible',canonical(rng.randbytes(PAYLOAD)))]
        with tempfile.TemporaryDirectory(prefix='v3-save-compressed-') as temp:
            out=Path(temp)
            for name,bank in inputs:(out/(name+'.bin')).write_bytes(bank)
            (out/'console.bin').write_bytes(rng.randbytes(6528))
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer']
            run=subprocess.run(['cc',*flags,str(ROOT/'tests/v3_save_compressed_test.c'),
                str(ROOT/'overlays/v3/save_compressed.c'),'-o',str(out/'check')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(out/'check'),str(out)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr);print(run.stdout.strip())
            for name,raw in inputs[:3]:
                packed=(out/(name+'.packed')).read_bytes()
                self.assertEqual(checksum(packed[:PAYLOAD]),0)
                stream=packed[20:0x2F68]+packed[0x2F6A:PAYLOAD]
                length=struct.unpack_from('>I',packed,PAYLOAD+16)[0]
                expected=raw+(out/'console.bin').read_bytes()
                decoded=yaz0_decode(b'Yaz0'+struct.pack('>I',len(expected))+bytes(8)+stream[:length])
                self.assertEqual(decoded,expected)
                self.assertEqual(stream[length:],bytes(len(stream)-length))

    def test_mips_preparation_receipt(self):
        out=ROOT/'build/v3-console-games-prepared-04'
        report=json.loads((out/'games.json').read_text())['storage_core']
        self.assertEqual(report['sha256'],sha256((out/'save_compressed/code.bin').read_bytes()))
        for path,digest in report['sources'].items():self.assertEqual(digest,sha256((ROOT/path).read_bytes()))
        self.assertFalse(report['native_storage_installed'])
        self.assertEqual(report['bank_bytes'],65536)


if __name__=='__main__':unittest.main()
