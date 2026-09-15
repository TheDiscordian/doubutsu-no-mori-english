"""Current copied-town fixture retains content and uses the real saved codec."""
import ctypes
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_campsite_gameplay import create,BANK,PROFILE,STATE
from v3_optional_composition import inputs


class CampsiteFixtureTests(unittest.TestCase):
    def test_current_seed_full_native_codec_and_source_retention(self):
        source=(ROOT/'local/rc2-save-report-g3O4lU/test.flash').read_bytes()
        rom,report=inputs();result,receipt=create(source,rom,report)
        self.assertFalse(receipt['seeded_campsite']);self.assertFalse(receipt['seeded_camper'])
        self.assertFalse(receipt['seeded_rewards'])
        with tempfile.TemporaryDirectory(prefix='v3-summer-fixture-') as directory:
            path=Path(directory)/'codec.so'
            subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',
                '-DAF_V3_CLOTHING_PROFILE=1',str(ROOT/'overlays/v3/save_codec.c'),'-o',str(path)],
                check=True,capture_output=True,text=True,timeout=30)
            lib=ctypes.CDLL(str(path));lib.af_v3_save_check.argtypes=(ctypes.c_void_p,ctypes.c_uint,ctypes.c_void_p,ctypes.c_void_p)
            profile=bytes.fromhex(report['save_runtime']['profile_hex'])
            for number in range(2):
                bank=ctypes.create_string_buffer(result[number*BANK:(number+1)*BANK])
                current=ctypes.create_string_buffer(profile);out=ctypes.create_string_buffer(STATE)
                self.assertEqual(lib.af_v3_save_check(bank,BANK,current,out),1)
                self.assertEqual(out.raw,profile+bytes(STATE-PROFILE))
        bad=bytearray(source);bad[0x100]^=1
        with self.assertRaises(ValueError):create(bad,rom,report)
        wrong=dict(report,output_sha256='0'*64)
        with self.assertRaises(ValueError):create(source,rom,wrong)
        self.assertEqual(source,(ROOT/'local/rc2-save-report-g3O4lU/test.flash').read_bytes())


if __name__=='__main__':unittest.main()
