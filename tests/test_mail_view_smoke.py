"""Real-window probes stay isolated, reject unsafe mail, and detect writes."""

from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from mail_view_smoke import OPEN, OPEN_BYTES, snapshot, open_test_mail, verify_unchanged
from runtime_layout import TEST_RETURN
from mail_open_test_scenario import scenario, CALLS, RAM, VROM


class Debugger:
    def __init__(self):
        self.data = bytearray(4*1024*1024)
        self.calls = []
        self.put(0x8010EF90,struct.pack('>I',0x80200000))
        self.put(0x80136FD8,struct.pack('>I',0x80300000))
        self.put(OPEN,OPEN_BYTES)

    def put(self,address,data):
        self.data[address-0x80000000:address-0x80000000+len(data)] = data

    def read_memory(self,address,size):
        return bytes(self.data[address-0x80000000:address-0x80000000+size])

    def call(self,address,args):
        self.calls.append((address,args))
        return {'test_only_function_call':address}


class MailWindowProbeTests(unittest.TestCase):
    def test_execution_probes_pause_before_installing_and_check_every_reply(self):
        module = {'symbols':{'af_mail_body_hook':'80194C5C','af_mail_footer_hook':'80194C80'}}
        board = bytearray(0x1300)
        for address,_,symbol in CALLS:
            target = int(module['symbols'][symbol],16)
            struct.pack_into('>I',board,address-RAM,0x0C000000|((target&0x0FFFFFFF)>>2))
        files = {VROM:SimpleNamespace(extract=lambda rom:bytes(board))}
        with patch('mail_open_test_scenario.verify_test_module'), \
                patch('mail_open_test_scenario.by_vrom',return_value=files):
            actions = scenario(b'',module)
        self.assertEqual([a['key'] for a in actions if 'key' in a],['b','a','Return'])
        observed = [i for i,a in enumerate(actions) if a.get('expect_submenu',{}).get('board_mode') == 1]
        self.assertEqual(len(observed),3)
        for index in observed:
            self.assertEqual(actions[index+1],{'pause_game_thread':True})
            for offset,symbol in ((2,'af_mail_body_hook'),(6,'af_mail_footer_hook')):
                address = module['symbols'][symbol]
                self.assertEqual(actions[index+offset:index+offset+4],[
                    {'command':f'Z0,{address.lower()},4','expect_result':'OK'},
                    {'command':'c','expect_result':'S05'},
                    {'command':'g','expect_pc':address},
                    {'command':f'z0,{address.lower()},4','expect_result':'OK'}])

    def test_only_native_open_call_and_unchanged_source_preferences(self):
        debug = Debugger()
        source = TEST_RETURN+0x200
        before = bytes(debug.data)
        opened = open_test_mail(debug,source)
        self.assertEqual(debug.calls,[(f'{OPEN:08X}',[0x80201CBC,12,1,0,source,0])])
        self.assertEqual(bytes(debug.data),before)
        self.assertTrue(verify_unchanged(debug,opened)['test_mail_and_preferences_unchanged'])
        for address in (source,0x803003EE):
            debug.put(address,b'!')
            with self.assertRaisesRegex(ValueError,'changed'):
                verify_unchanged(debug,opened)
            debug.put(address,b'\0')
        with self.assertRaisesRegex(ValueError,'active'):
            verify_unchanged(debug,None)

    def test_invalid_addresses_metadata_open_state_and_instructions_fail(self):
        source = TEST_RETURN+0x200
        for address in (0,TEST_RETURN,source+1,0x80400000,True):
            debug = Debugger()
            with self.assertRaises(ValueError): open_test_mail(debug,address)
            self.assertFalse(debug.calls)
        for address,value in ((0x8010EF90,bytes(4)),(0x80136FD8,bytes(4)),
                              (source+0x26,b'\xff'),(source+0x27,b'\x80'),(source+0x29,b'\x40'),
                              (0x80201CC0,struct.pack('>I',12)),(0x80201CC8,struct.pack('>I',3)),
                              (OPEN,bytes(4))):
            debug = Debugger()
            debug.put(address,value)
            with self.assertRaises(ValueError): open_test_mail(debug,source)
            self.assertFalse(debug.calls)

    def test_snapshot_tag_requires_an_explicit_isolated_probe(self):
        debug = Debugger()
        source = TEST_RETURN+0x200
        debug.put(source+0x27,b'\x80')
        with self.assertRaises(ValueError): open_test_mail(debug,source)
        self.assertFalse(debug.calls)
        open_test_mail(debug,source,snapshot_probe=True)
        self.assertEqual(len(debug.calls),1)
        with self.assertRaises(ValueError): open_test_mail(debug,source,open_mode=2)
        open_test_mail(debug,source,snapshot_probe=True,open_mode=2)
        self.assertEqual(debug.calls[-1][1][2],2)
        for mode in (0,3,True):
            with self.assertRaises(ValueError): open_test_mail(debug,source,snapshot_probe=True,open_mode=mode)
        debug.put(source+0x27,b'\x81')
        with self.assertRaises(ValueError): open_test_mail(debug,source,snapshot_probe=True)

    def test_live_board_snapshot_reads_actual_loaded_call_words(self):
        debug = Debugger()
        submenu,overlay,board = 0x80201CBC,0x80210000,0x80230000
        debug.put(submenu+4,struct.pack('>3I',12,12,3))
        debug.put(submenu+0x2C,struct.pack('>I',overlay))
        debug.put(overlay+0x106E4,struct.pack('>I',board))
        debug.put(overlay+0x103EC,struct.pack('>I',2))
        debug.put(overlay+0x10420,struct.pack('>I',1))
        debug.put(board+5,bytes([3,42,8]))
        debug.put(board+0xAC,struct.pack('>I',TEST_RETURN+0x200))
        debug.put(board-0x1D70+0x1210,bytes.fromhex('0C065317'))
        result = snapshot(debug)
        self.assertEqual((result['board_mode'],result['board_state'],result['body_length']), (1,2,42))
        self.assertEqual(result['body_call'],'0c065317')
        self.assertEqual(result['source'],f'{TEST_RETURN+0x200:08X}')
        self.assertTrue(result['read_only'])
