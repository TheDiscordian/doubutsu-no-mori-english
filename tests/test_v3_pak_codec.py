"""Travel records and native I/O with device doubles; no installed visiting claim."""
import ctypes
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_player_travel import DEFINES as PLAYER_DEFINES
U8=ctypes.c_ubyte
U32=ctypes.c_uint


class Input(ctypes.Structure):
    _fields_=[('native',ctypes.POINTER(U8)),('records',ctypes.POINTER(U8)),
              ('kind',U32),('native_bytes',U32),('record_bytes',U32),
              ('binding',U8*32),('identity',U8*16)]


class PakCodecTests(unittest.TestCase):
    def test_sanitized_actual_collection_consumers_acquire_and_return(self):
        with tempfile.TemporaryDirectory(prefix='af-travel-consumers-') as directory:
            binary=Path(directory)/'check'
            sources=('tests/v3_travel_native_test.c','overlays/v3/travel_native.c',
                'overlays/v3/travel_player.c','overlays/v3/pak_native.c','overlays/v3/pak_codec.c',
                'overlays/v3/diary.c','overlays/v3/diary_calendar.c',
                'overlays/v3/holiday_cards.c','overlays/v3/bank_account.c',
                'overlays/v3/collection.c','overlays/v3/surface_save.c',
                'overlays/v3/held_collection.c','overlays/v3/carried_collection.c',
                'overlays/v3/diary_items.c','overlays/v3/save_codec.c')
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
                '-DAF_V3_PLAYER_TRAVEL=1','-DAF_TEST_COLLECTIONS=1',
                *['-D'+d+'=1' for d in PLAYER_DEFINES],
                *[str(ROOT/p) for p in sources],'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Actual collection consumers',result.stdout)
            print(result.stdout.strip())

    def test_sanitized_connected_native_player_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='af-travel-native-') as directory:
            binary=Path(directory)/'check'
            sources=('tests/v3_travel_native_test.c','overlays/v3/travel_native.c',
                'overlays/v3/travel_player.c','overlays/v3/pak_native.c','overlays/v3/pak_codec.c',
                'overlays/v3/diary.c','overlays/v3/diary_calendar.c',
                'overlays/v3/holiday_cards.c','overlays/v3/bank_account.c')
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
                *['-D'+d+'=1' for d in PLAYER_DEFINES],
                *[str(ROOT/p) for p in sources],'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('Connected native departure/arrival',result.stdout)
            print(result.stdout.strip())

    def test_sanitized_native_pak_callers_and_device_failures(self):
        with tempfile.TemporaryDirectory(prefix='af-pak-native-') as directory:
            binary=Path(directory)/'check'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                *[str(ROOT/p) for p in ('tests/v3_pak_native_test.c',
                    'overlays/v3/pak_native.c','overlays/v3/pak_codec.c')],'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('original-note preservation passed',result.stdout)
            print(result.stdout.strip())

    def test_sanitized_player_export_visiting_acquisition_and_isolated_return(self):
        with tempfile.TemporaryDirectory(prefix='af-travel-player-') as directory:
            binary=Path(directory)/'check'
            sources=('tests/v3_travel_player_test.c','overlays/v3/travel_player.c',
                'overlays/v3/pak_codec.c','overlays/v3/diary.c','overlays/v3/diary_calendar.c',
                'overlays/v3/holiday_cards.c','overlays/v3/bank_account.c')
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
                *['-D'+d+'=1' for d in PLAYER_DEFINES],
                *[str(ROOT/p) for p in sources],'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('shared town state preservation',result.stdout)
            print(result.stdout.strip())

    def test_sanitized_lossless_notes_rejections_and_output_atomicity(self):
        with tempfile.TemporaryDirectory(prefix='af-pak-codec-') as directory:
            binary=Path(directory)/'check'
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                str(ROOT/'tests/v3_pak_codec_test.c'),str(ROOT/'overlays/v3/pak_codec.c'),
                '-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('lossless page-sized round trips',result.stdout)
            print(result.stdout.strip())

    def test_independent_wire_decoder_preserves_complete_months_and_game_progress(self):
        with tempfile.TemporaryDirectory(prefix='af-pak-wire-') as directory:
            library=Path(directory)/'codec.so'
            result=subprocess.run(['cc','-std=c11','-O2','-shared','-fPIC','-Wall','-Wextra','-Werror',
                str(ROOT/'overlays/v3/pak_codec.c'),'-o',str(library)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            codec=ctypes.CDLL(str(library))
            codec.af_v3_pak_encode.argtypes=[ctypes.POINTER(U8),U32,ctypes.POINTER(Input),ctypes.POINTER(U32),U32]
            codec.af_v3_pak_encode.restype=ctypes.c_int
            native=bytes((i*31+7)%256 for i in range(0x1200))
            # Full 12,008-byte diary plus 1,632-byte console save and category
            # records. This is framing evidence, not semantic runtime admission.
            records=bytes((i*13+5)%251 for i in range(12008+1632+512))
            n=(U8*len(native)).from_buffer_copy(native)
            r=(U8*len(records)).from_buffer_copy(records)
            inputs=Input(n,r,0,len(native),len(records),(U8*32)(*range(32)),
                         (U8*16).from_buffer_copy(native[8:24]))
            note=(U8*0x7B00)();workspace=(U32*4096)()
            size=codec.af_v3_pak_encode(note,len(note),ctypes.byref(inputs),workspace,ctypes.sizeof(workspace))
            self.assertGreater(size,0);self.assertEqual(size%256,0)
            wire=bytes(note[:size]);h=struct.unpack_from('>10I',wire)
            self.assertEqual(h[:6],(0x4146504B,1,0,size,len(native),len(records)))
            self.assertEqual(wire[40:72],bytes(range(32)));self.assertEqual(wire[72:88],native[8:24])
            self.assertEqual(h[9],zlib.crc32(wire[:36]+bytes(4)+wire[40:]))
            self.assertEqual(h[7],zlib.crc32(native));self.assertEqual(h[8],zlib.crc32(records))
            stream=wire[96:96+h[6]];position=0;decoded=bytearray()
            while len(decoded)<len(native)+len(records):
                flags=stream[position];position+=1
                for bit in range(7,-1,-1):
                    if len(decoded)==len(native)+len(records):
                        self.assertEqual(flags&((1<<(bit+1))-1),0);break
                    if flags&(1<<bit):
                        decoded.append(stream[position]);position+=1
                    else:
                        a,b=stream[position:position+2];position+=2
                        count=a>>4;distance=((a&15)<<8|b)+1
                        if count:count+=2
                        else:count=stream[position]+18;position+=1
                        self.assertLessEqual(distance,len(decoded))
                        self.assertLessEqual(len(decoded)+count,len(native)+len(records))
                        for _ in range(count):decoded.append(decoded[-distance])
            self.assertEqual(position,len(stream));self.assertEqual(decoded,native+records)
            self.assertEqual(wire[96+h[6]:],bytes(size-96-h[6]))


if __name__=='__main__':unittest.main()
