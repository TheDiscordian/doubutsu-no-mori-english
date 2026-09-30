"""Bounded complete code-row expansion; no native rendering claim."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class CodeString(unittest.TestCase):
    def test_rows_and_bounds(self):
        with tempfile.TemporaryDirectory(prefix='afv3-nook-row-') as tmp:
            lib=Path(tmp)/'row.so'
            subprocess.run(['cc','-shared','-fPIC','-Wall','-Wextra','-Werror',
                str(ROOT/'overlays/v3/nook_code_string.c'),'-o',str(lib)],check=True)
            fn=ctypes.CDLL(str(lib)).af_np_code_string
            fn.argtypes=[ctypes.POINTER(ctypes.c_ubyte),ctypes.POINTER(ctypes.c_int),
                ctypes.c_int,ctypes.POINTER(ctypes.c_ubyte)]
            fn.restype=ctypes.c_int
            def run(data,index,code):
                text=(ctypes.c_ubyte*1040)(*data,*([0xCC]*(1040-len(data))))
                row=(ctypes.c_ubyte*14)(*code);length=ctypes.c_int(len(data))
                result=fn(text,ctypes.byref(length),index,row)
                self.assertEqual(bytes(text)[1024:],bytes([0xCC])*16)
                return result,length.value,bytes(text)
            for command in (0x34,0x35):
                source=b'prefix'+bytes((0x7F,command))+b' suffix\x7f\x01'
                for code in (b'ABCDEFGHIJKLMN',b'%&@0123456789#',b'#'*14):
                    result,n,text=run(source,6,code)
                    expected=b'prefix'+code.replace(b'#',b'\x80\xD1')+b' suffix\x7f\x01'
                    self.assertEqual((result,n,text[:n]),(1,len(expected),expected))
            full=b'X'*994+b'\x7f\x34\x7f\x01'
            result,n,text=run(full,994,b'#'*14)
            self.assertEqual((result,n),(1,1024))
            overflow=b'X'*995+b'\x7f\x35\x7f\x01'
            result,n,text=run(overflow,995,b'#'*14)
            self.assertEqual((result,n,text[:n]),(-1,len(overflow),overflow))
            for code in (b' '*14,b'ABCDEFGHIJKLM!',b'ABCDEFGHIJKLM\x7f'):
                source=b'\x7f\x34 tail';result,n,text=run(source,0,code)
                self.assertEqual((result,n,text[:n]),(0,len(source),source))


if __name__=='__main__':unittest.main()
