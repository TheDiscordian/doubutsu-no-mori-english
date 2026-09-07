#!/usr/bin/env python3
"""Open a synthetic ordinary letter through the game's actual submenu loader."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom, sha256
from runtime_module import verify_test_module
from runtime_layout import TEST_RETURN, GUARD_ADDRESS, GUARD_WORD
from mail_viewer import RAM,VROM
from mail_view_patch import CALLS


def scenario(rom,module):
    verify_test_module(rom,module)
    board = by_vrom(rom)[VROM].extract(rom)
    words = {}
    for address,_,symbol in CALLS:
        expected = (0x0C000000|((int(module['symbols'][symbol],16)&0x0FFFFFFF)>>2)).to_bytes(4,'big')
        if board[address-RAM:address-RAM+4] != expected:
            raise ValueError('Real letter-open test requires installed read-layout calls')
        words[symbol] = expected.hex()
    source = TEST_RETURN+0x200
    mail = bytearray(164)
    mail[:6] = b'READER'
    mail[0x12:0x18] = b'WRITER'
    mail[0x26:0x2A] = bytes([0,3,4,0])
    mail[0x2A:0x34] = b'To '.ljust(10,b' ')
    body = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567\xcd'+b"iI'hello"
    mail[0x34:0x94] = body.ljust(96,b' ')
    mail[0x94:] = b"iI'hello".ljust(16,b' ')
    actions = [{'wait':2},{'save_state':True}]
    for key in ('b','a','Return'):
        actions += [{'pause_game_thread':True},
                    {'snapshot_submenu':True,'expect_submenu':{'program':0,'move_index':0}},
                    {'write':[f'{source:08X}',mail.hex()]},{'open_test_mail':f'{source:08X}'},
                    {'resume':True},{'wait':8},
                    {'snapshot_submenu':True,'expect_submenu':{'program':12,'move_index':3,'board_state':2,
                        'board_mode':1,'source':f'{source:08X}','body_length':len(body),'footer_length':8,
                        'body_call':words['af_mail_body_hook'],'footer_call':words['af_mail_footer_hook']}}]
        # Installing a breakpoint while running can hit before the following
        # continue packet and leave an extra stop reply queued. Establish the
        # verified paused frame boundary before adding either observed hook.
        actions += [{'pause_game_thread':True}]
        for symbol in ('af_mail_body_hook','af_mail_footer_hook'):
            address = module['symbols'][symbol].lower()
            actions += [{'command':f'Z0,{address},4','expect_result':'OK'},
                        {'command':'c','expect_result':'S05'},
                        {'command':'g','expect_pc':module['symbols'][symbol]},
                        {'command':f'z0,{address},4','expect_result':'OK'}]
        actions += [{'resume':True},{'wait':1},{'key':key,'duration':0.12},{'wait':5},
                    {'snapshot_submenu':True,'expect_submenu':{'program':0,'move_index':0}},
                    {'assert_test_mail_unchanged':True}]
    actions += [
                {'read':[f'{GUARD_ADDRESS:08X}',16],'expect':f'{GUARD_WORD:08X}'*4},
                {'load_state':True},{'resume':True},{'wait':2},
                {'read':[f'{source:08X}',4],'expect':'00000000'}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--module',type=Path,default=Path('build/runtime-module/module.json'))
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions = scenario(rom,json.loads(args.module.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'rom_sha256':sha256(rom)}))


if __name__ == '__main__':
    main()
