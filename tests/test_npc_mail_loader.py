"""Single-owner cartridge loading, verified code, and failure cleanup."""

import ctypes as C
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]


@unittest.skipUnless(shutil.which('gcc'),'Host GCC required')
class NpcMailLoaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-npc-mail-loader-')
        library = Path(cls.temporary.name)/'loader.so'
        flags = ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g'] if os.environ.get('AF_NPC_LOADER_SANITIZE') == '1' else []
        compiler_env = dict(os.environ);compiler_env.pop('LD_PRELOAD',None)
        result = subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',*flags,
                                str(ROOT/'runtime/mail/npc_loader.c'),str(ROOT/'tests/npc_mail_loader_mock.c'),
                                str(ROOT/'runtime/crc32.c'),
                                '-o',str(library)],capture_output=True,text=True,env=compiler_env)
        if result.returncode: raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_npc_mail_load.argtypes = [C.c_void_p]*4+[C.c_uint]*2
        cls.lib.af_npc_mail_load.restype = C.c_void_p

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def number(self,name): return C.c_uint.in_dll(self.lib,'af_npc_loader_'+name)

    def pointer(self,name): return C.c_void_p.in_dll(self.lib,'af_npc_loader_'+name)

    def setUp(self):
        self.config = (C.c_uint*8).in_dll(self.lib,'af_npc_loader_test_config')
        self.blob = (C.c_ubyte*0x9000).in_dll(self.lib,'af_npc_loader_blob')
        self.log = (C.c_ubyte*128).in_dll(self.lib,'af_npc_loader_log')
        self.active = C.c_void_p.in_dll(self.lib,'af_npc_mail_session');self.active.value = None
        self.capital = C.c_uint.in_dll(self.lib,'af_mail_generation_capital');self.capital.value = 0
        for name in ('calls','errors','fail_alloc','dma_failure','corrupt','mode','alignment','nested_at',
                     'nested_calls','size','freed','input_capital','condition','foreign'):
            self.number(name).value = 0
        self.number('heap').value = 0x80200000
        self.pointer('override').value = None
        self.player = C.create_string_buffer(b'PLAYER'+b'TOWN  '+bytes.fromhex('12343001'),16)
        self.animal = C.create_string_buffer(bytes.fromhex('e000')+bytes(10),12)
        self.remail = C.create_string_buffer(bytes(18),18)
        self.destination = C.create_string_buffer(b'!'*196,196)
        self.pointer('player').value = C.addressof(self.player)
        self.pointer('animal').value = C.addressof(self.animal)
        self.pointer('remail').value = None
        self.resource()

    def resource(self,image=128,reloc=32,text=64,entry=4):
        size = image+reloc
        data = bytes((i*19+3)&255 for i in range(size))
        self.blob[:size] = data
        self.config[:] = (0x03200000,size,image,reloc,entry,text,zlib.crc32(data),0x41464E01)

    def args(self):
        return [C.addressof(self.destination)+16,self.pointer('player').value,self.pointer('animal').value,
                self.pointer('remail').value,self.number('condition').value,self.number('foreign').value]

    def invoke(self,success,expected,args=None):
        capital = self.capital.value
        old = self.destination.raw,self.player.raw,self.animal.raw,self.remail.raw
        calls,freed = self.number('calls').value,self.number('freed').value
        arguments = self.args() if args is None else args
        self.assertEqual(self.lib.af_npc_mail_load(*arguments),arguments[0] if success else None)
        self.assertEqual(bytes(self.log[calls:self.number('calls').value]),bytes(expected))
        self.assertEqual(self.number('freed').value-freed,int(7 in expected))
        self.assertEqual(self.number('errors').value,0)
        self.assertIsNone(self.active.value)
        self.assertEqual((self.player.raw,self.animal.raw,self.remail.raw),old[1:])
        self.assertEqual(self.destination.raw[:16]+self.destination.raw[180:],b'!'*32)
        if success:
            self.assertEqual(self.destination.raw[16:180],bytes((i*17+capital)&255 for i in range(164)))
            self.assertEqual(self.capital.value,capital^1)
            self.assertEqual(self.number('input_capital').value,capital)
            self.assertEqual(self.number('size').value,self.config[1]+5344+15)
        else:
            self.assertEqual(self.destination.raw,old[0]);self.assertEqual(self.capital.value,capital)

    def test_complete_call_order_argument_forwarding_alignment_and_capital(self):
        for alignment in range(16):
            for foreign in range(2):
                for condition in range(2):
                    self.number('calls').value = 0
                    self.number('alignment').value = alignment
                    self.number('foreign').value = foreign;self.number('condition').value = condition
                    self.pointer('remail').value = C.addressof(self.remail) if foreign else None
                    with self.subTest(alignment=alignment,foreign=foreign,condition=condition):
                        self.invoke(True,range(1,8))
        self.assertEqual(self.number('freed').value,64)
        self.pointer('animal').value = None;self.number('calls').value = 0
        self.invoke(True,range(1,8))

    def test_configuration_boundaries_reject_before_allocation(self):
        good = tuple(self.config)
        invalid = {0:(0,0x03200010,0xFFFFFFFF),1:(0,good[1]-16,good[1]+16,0xFFFFFFFF),
                   2:(0,1,0x8001,0xFFFFFFFF),3:(0,16,24,33,0x1001,0xFFFFFFFF),
                   4:(1,2,3,good[5],0xFFFFFFFF),5:(0,1,good[2]+16,0xFFFFFFFF),
                   7:(0,0x41464E00,0x41464E02)}
        for field,values in invalid.items():
            for value in values:
                self.config[:] = good;self.config[field] = value
                with self.subTest(field=field,value=value): self.invoke(False,())
        self.config[:] = (0,)*8;self.invoke(False,())
        # Config checksum is independently approved, not read from the blob.
        self.config[:] = good;self.config[6] ^= 1;self.invoke(False,(1,2,7))
        for image,reloc,text,entry in ((16,32,16,0),(0x8000,0x1000,0x8000,0x7FFC)):
            self.resource(image,reloc,text,entry);self.number('calls').value = 0
            self.invoke(True,range(1,8))

    def test_allocation_failure_and_four_mib_bounds_release_exactly_once(self):
        self.number('fail_alloc').value = 1;self.invoke(False,(1,))
        self.number('fail_alloc').value = 0
        size = self.config[1]+5344+15
        for address in (0,0x8019C8DF,0x80400000-size+1,0x80400000,0xFFFFFFFF):
            self.number('heap').value = address
            with self.subTest(address=address): self.invoke(False,(1,7))
        for address in (0x8019C8E0,0x80400000-size):
            self.number('heap').value = address;self.invoke(True,range(1,8))

    def test_dma_and_corruption_never_relocate_or_execute(self):
        self.number('dma_failure').value = 1;self.invoke(False,(1,2,7))
        self.number('dma_failure').value = 0
        for index in range(self.config[1]):
            self.number('calls').value = 0;self.number('corrupt').value = index+1
            with self.subTest(byte=index): self.invoke(False,(1,2,7))
        self.number('corrupt').value = 0;self.invoke(True,range(1,8))

    def test_every_yield_boundary_rejects_reentry_without_losing_outer_ownership(self):
        for point in range(1,8):
            self.number('calls').value = 0;self.number('nested_at').value = point
            with self.subTest(point=point): self.invoke(True,range(1,8))
        self.assertEqual(self.number('nested_calls').value,7)

    def test_creator_failure_scope_cleanup_and_retries_retain_caller_state(self):
        for mode in range(1,5):
            self.number('calls').value = 0;self.number('mode').value = mode
            self.invoke(False,range(1,8))
            self.number('mode').value = 0;self.invoke(True,range(1,8))

    def test_invalid_inputs_active_session_and_overlapping_allocations(self):
        good = self.args()
        for index,value in ((0,None),(1,None),(2,None),(4,2),(5,1),(5,2),
                            (1,good[1]+1),(2,good[2]+1),(3,C.addressof(self.remail)+1),
                            (0,C.addressof(self.capital)),(0,C.addressof(self.active))):
            args = good.copy();args[index] = value
            with self.subTest(index=index,value=value): self.invoke(False,(),args)
        self.capital.value = 2;self.invoke(False,());self.capital.value = 1
        self.active.value = C.addressof(self.player)
        self.assertIsNone(self.lib.af_npc_mail_load(*good))
        self.assertEqual(self.active.value,C.addressof(self.player));self.active.value = None
        self.assertEqual(self.number('calls').value,0)
        for value in (good[0],good[1],good[2],C.addressof(self.remail)):
            self.pointer('override').value = value
            self.pointer('remail').value = C.addressof(self.remail);self.number('foreign').value = 1
            self.invoke(False,(1,7))
        self.pointer('override').value = None;self.invoke(True,range(1,8))


if __name__ == '__main__': unittest.main()
