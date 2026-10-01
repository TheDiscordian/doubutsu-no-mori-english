"""Retained lower heap, exclusive scene ownership, complete guard boundaries."""
import ctypes as C
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class SceneMailHeapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='af-v3-mail-heap-')
        library=Path(cls.temp.name)/'guard.so'
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
            str(ROOT/'overlays/v3/npc_mail_heap.c'),str(ROOT/'tests/npc_mail_heap_mock.c'),
            '-o',str(library)],check=True,capture_output=True,text=True)
        cls.lib=C.CDLL(str(library));cls.fn=cls.lib.af_v3_npc_mail_heap_range
        cls.fn.argtypes=[C.c_uint,C.c_uint];cls.fn.restype=C.c_int

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def number(self,key):return C.c_uint.in_dll(self.lib,'af_mail_heap_test_'+key)

    def setUp(self):
        self.number('detected').value=0x800000
        self.number('title').value=0
        self.number('borrowed').value=1
        for key in ('front','end'):
            (C.c_uint*4).in_dll(self.lib,'af_mail_heap_test_'+key)[:]=[0xAF53434E]*4

    def test_retains_lower_heap_bounds_without_borrow(self):
        self.number('borrowed').value=0
        for address,size,result in ((0x8019C8E0,1,1),(0x80300000,0x100000,1),
                (0x8019C8DF,1,0),(0x80300000,0x100001,0),(0x80400000,1,0)):
            self.assertEqual(self.fn(address,size),result)

    def test_actual_failed_allocation_and_upper_boundaries(self):
        for address,size,result in ((0x8042C7D0,70671,1),
                (0x80400040,0x4FFB0,1),(0x8040003F,1,0),
                (0x80400040,0x4FFB1,0),(0x8044FFF0,1,0),
                (0x80450000,0,0),(0xFFFFFFFF,0xFFFFFFFF,0)):
            self.assertEqual(self.fn(address,size),result)

    def test_requires_every_exclusive_owner_condition(self):
        for key,value in (('detected',0x400000),('title',1),('borrowed',0),('borrowed',2)):
            self.setUp();self.number(key).value=value
            self.assertEqual(self.fn(0x8042C7D0,70671),0)

    def test_checks_every_word_of_both_workspace_guards(self):
        for key in ('front','end'):
            for index in range(4):
                self.setUp()
                (C.c_uint*4).in_dll(self.lib,'af_mail_heap_test_'+key)[index]^=1
                self.assertEqual(self.fn(0x8042C7D0,70671),0)


if __name__=='__main__':unittest.main()
