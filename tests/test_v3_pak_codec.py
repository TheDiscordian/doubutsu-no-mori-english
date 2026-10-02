"""Travel records and native I/O with device doubles; no installed visiting claim."""
import ctypes
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
from v3_player_travel import DEFINES as PLAYER_DEFINES
U8=ctypes.c_ubyte
U32=ctypes.c_uint


class Input(ctypes.Structure):
    _fields_=[('native',ctypes.POINTER(U8)),('records',ctypes.POINTER(U8)),
              ('kind',U32),('native_bytes',U32),('record_bytes',U32),
              ('binding',U8*32),('identity',U8*16)]


class PakCodecTests(unittest.TestCase):
    def decode_wire(self, wire):
        """Independent, bounded decoder; never calls the imported codec."""
        self.assertGreaterEqual(len(wire),256)
        h=struct.unpack_from('>10I',wire)
        self.assertEqual(h[:2],(0x4146504B,1))
        self.assertIn(h[2],(0,1));self.assertEqual(h[3],len(wire))
        self.assertEqual(len(wire)%256,0)
        self.assertEqual(h[4],0x6700 if h[2] else 0x1200)
        self.assertLessEqual(h[5],14204)
        self.assertEqual(h[9],zlib.crc32(wire[:36]+bytes(4)+wire[40:]))
        self.assertEqual(wire[88:96],bytes(8))
        self.assertGreater(h[6],0);self.assertLessEqual(h[6],len(wire)-96)
        stream=wire[96:96+h[6]];position=0;decoded=bytearray();total=h[4]+h[5]
        while len(decoded)<total:
            self.assertLess(position,len(stream))
            flags=stream[position];position+=1
            for bit in range(7,-1,-1):
                if len(decoded)==total:
                    self.assertEqual(flags&((1<<(bit+1))-1),0);break
                if flags&(1<<bit):
                    self.assertLess(position,len(stream))
                    decoded.append(stream[position]);position+=1
                else:
                    self.assertLessEqual(position+2,len(stream))
                    a,b=stream[position:position+2];position+=2
                    count=a>>4;distance=((a&15)<<8|b)+1
                    if count:count+=2
                    else:
                        self.assertLess(position,len(stream))
                        count=stream[position]+18;position+=1
                    self.assertLessEqual(distance,len(decoded))
                    self.assertLessEqual(len(decoded)+count,total)
                    for _ in range(count):decoded.append(decoded[-distance])
        self.assertEqual(position,len(stream))
        self.assertEqual(wire[96+h[6]:],bytes(len(wire)-96-h[6]))
        native,records=bytes(decoded[:h[4]]),bytes(decoded[h[4]:])
        self.assertEqual(h[7],zlib.crc32(native));self.assertEqual(h[8],zlib.crc32(records))
        return h,native,records

    @unittest.skipUnless(os.environ.get('V3_PLAYER_TRAVEL_PAK'),'requires actual native Pak export')
    def test_actual_native_pak_preserves_both_note_kinds_and_full_import_records(self):
        directory=ROOT/os.environ['V3_PLAYER_TRAVEL_PAK']
        raw=(directory/'test.pak').read_bytes()
        self.assertEqual(len(raw),0x8000);self.assertEqual(raw[0x3A],1)
        # Nintendo __OSDir and __OSInodeUnit: 16 directory entries at page 3,
        # bank-zero primary/mirror inode pages 1/2, EOF=1, data pages >=5.
        self.assertEqual(raw[0x100:0x200],raw[0x200:0x300])
        inode=struct.unpack_from('>128H',raw,0x100)
        allocated=set();notes={0:[],1:[]}
        for i in range(16):
            entry=raw[0x300+i*32:0x320+i*32]
            game,company,page=struct.unpack_from('>IHH',entry)
            if not game and not company:continue
            self.assertEqual((game,company),(0x4E41464A,0x3031))
            extension=entry[12:16];kind=extension[0]-0x1A
            self.assertIn(kind,(0,1));self.assertEqual(extension[1:3],b'\x1F\x03')
            self.assertIn(extension[3],(1,2))
            chunks=[]
            while page!=1:
                self.assertTrue(5<=page<128);self.assertNotIn(page,allocated)
                allocated.add(page);chunks.append(raw[page*256:(page+1)*256]);page=inode[page]
            note=b''.join(chunks);self.assertGreaterEqual(len(note),512)
            header=struct.unpack_from('>7I',note)
            self.assertEqual(header[:2],(0x41464A31,1));self.assertGreater(header[2],0)
            self.assertEqual(header[3],header[2]^0xFFFFFFFF)
            self.assertEqual(header[4:6],(kind,len(note)-256))
            self.assertEqual(header[6],zlib.crc32(note[:24]+bytes(4)+note[28:256]))
            self.assertEqual(note[28:256],bytes(228))
            h,native,records=self.decode_wire(note[256:])
            self.assertEqual(h[2],kind);self.assertEqual(h[5],14204)
            self.assertEqual(sum(struct.unpack('>'+str(len(native)//2)+'H',native))&65535,0)
            self.assertEqual(note[296:328],b'AFV3-PASSPORT-PLAYER-1'.ljust(32,b'\0'))
            self.assertEqual(note[328:344],records[16:32])
            if not kind:self.assertEqual(native[8:24],records[16:32])
            notes[kind].append((header[2],native,records))
        self.assertEqual(tuple(map(len,(notes[0],notes[1]))),(2,1))
        for kind,filename in ((0,'passport.bin'),(1,'backup.bin')):
            latest=max(notes[kind],key=lambda value:value[0])
            self.assertEqual(latest[1],(directory/filename).read_bytes())
            self.assertEqual(latest[2],(directory/'records.bin').read_bytes())

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
            checked,decoded_native,decoded_records=self.decode_wire(wire)
            self.assertEqual(checked,h);self.assertEqual(decoded_native,native)
            self.assertEqual(decoded_records,records)


if __name__=='__main__':unittest.main()
