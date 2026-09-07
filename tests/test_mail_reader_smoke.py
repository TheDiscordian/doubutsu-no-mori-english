"""Native snapshot observations reject malformed caches and incomplete traversals."""

from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import Mock, patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from mail_reader_smoke import snapshot, graphics, all_pages
from runtime_layout import TEST_RETURN


class Memory:
    def __init__(self):
        self.data = bytearray(4*1024*1024)

    def write(self,address,value):
        self.data[address-0x80000000:address-0x80000000+len(value)] = value

    def read_memory(self,address,size):
        return bytes(self.data[address-0x80000000:address-0x80000000+size])


class ReaderSmokeTests(unittest.TestCase):
    def test_cache_offsets_and_spans_follow_the_native_abi(self):
        debug = Memory()
        address = 0x80198A40
        debug.write(address,struct.pack('>7I',0x803B9B40,1,0,1,3,4,3))
        debug.write(address+28,struct.pack('>2I',1,3)+struct.pack('>12I',0,0,3,0,1,0,4,28,2,0,3,136))
        debug.write(address+164,b'To ')
        debug.write(address+1196,struct.pack('>6H',0,3,7,3,4,3)+bytes(4)+b'HDRBODYEnd')
        result = snapshot(debug,address)
        self.assertEqual(tuple(bytes.fromhex(result[f]) for f in ('header','body','footer')),(b'To ',b'BODY',b'End'))
        self.assertEqual([s['y'] for s in result['spans']],[0,28,136])
        self.assertEqual(result['owner'],'803B9B40')
        for offset,value in ((4,struct.pack('>I',3)),(12,bytes(4)),(16,struct.pack('>I',1033)),
                              (32,struct.pack('>I',9)),(36,struct.pack('>I',3)),
                              (1198,struct.pack('>H',1023)),(1196+16+3,b'\xcd')):
            before = debug.read_memory(address+offset,len(value))
            debug.write(address+offset,value)
            with self.assertRaises(ValueError): snapshot(debug,address)
            debug.write(address+offset,before)
        for invalid in (0,address+1,TEST_RETURN-16):
            with self.assertRaises(ValueError): snapshot(debug,invalid)

    def test_graphics_front_and_tail_must_remain_inside_the_actual_arena(self):
        debug = Memory()
        debug.write(0x8010EF90,struct.pack('>I',0x80200000))
        debug.write(0x80200000,struct.pack('>I',0x80210000))
        debug.write(0x80210290,struct.pack('>4I',0x10000,0x80220000,0x80221000,0x8022F000))
        self.assertEqual(graphics(debug)['size'],65536)
        debug.write(0x80210298,struct.pack('>I',0x8022F001))
        with self.assertRaisesRegex(ValueError,'overflow'): graphics(debug)

    def test_page_driver_checks_complete_content_and_backward_input(self):
        initial = {'owner':'803B9B40','status':1,'page':0,'total':2,
                   'header':b'H'.hex(),'body':b'abc\xcddef'.hex(),'footer':b'End'.hex(),
                   'spans':[{'section':1,'text':b'abc'.hex()}]}
        last = {**initial,'page':1,'spans':[{'section':1,'text':b'def'.hex()},{'section':2,'text':b'End'.hex()}]}
        spec = {**initial,'reader':'80198A40','hook':'80194CB0'}
        for bad in (False,True):
            debug,keyboard,record = Mock(),Mock(),Mock()
            final = {**last,'spans':[]} if bad else last
            with patch('mail_reader_smoke.snapshot',side_effect=[initial,initial]), \
                    patch('mail_reader_smoke.observe_draw',side_effect=[initial,final]), \
                    patch('mail_reader_smoke.time.sleep'):
                if bad:
                    with self.assertRaisesRegex(ValueError,'omitted'): all_pages(debug,keyboard,spec,record)
                else:
                    all_pages(debug,keyboard,spec,record)
                    self.assertEqual([c.args[0] for c in keyboard.press.call_args_list],['Right','Left'])
                    self.assertTrue(record.call_args.args[0]['complete_mail_page_traversal'])


if __name__ == '__main__':
    unittest.main()
