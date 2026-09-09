#!/usr/bin/env python3
"""Batch native board creation, all saved slots, and full-board shifting."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from mail_record import Record
from notice_record import pack
from notice_overlay import ROOT, INITIAL_IDS, INIT_START, verify_installation
from runtime_layout import TEST_STACK, GUARD_ADDRESS, GUARD_WORD

POSTS, DRAFT = 0x80129E0A, 0x8019B010
EDGE = b'EDGE'*4


def scenario(native, built, report):
    if sha256(built) != report['output_sha256']: raise ValueError('Changed notice cartridge')
    verify_installation(built, native, report['runtime_module'], report['noticeboard'])
    code = by_vrom(native)[CODE_VROM].extract(native)
    empty = b' '*96+code[0x80117AE0-CODE_RAM:0x80117AE8-CODE_RAM]
    actions = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]

    def write(at, data): actions.append({'write': [f'{at:08X}', data.hex()]})
    def check(at, data): actions.append({'read': [f'{at:08X}', len(data)], 'expect': data.hex()})
    def call(at, args=(), result=None):
        operation = {'address': f'{at:08X}', 'arguments': list(args)}
        if result is not None: operation['expect_return'] = result
        actions.append({'call': operation})

    edges = (POSTS-16, POSTS+15*104, DRAFT-16, DRAFT+104, TEST_STACK-0x1000, TEST_STACK+0x30)
    for at in edges: write(at, EDGE)
    write(POSTS, b'!'*(15*104))
    call(INIT_START)
    call(0x800A5CB0, result=4)
    for index, number in enumerate(INITIAL_IDS): check(POSTS+index*104, pack(Record(4, 0, (number,), ())))
    check(POSTS+4*104, empty*11)
    # Verify original clearing, then fill all slots with complete encoded and
    # ordinary manual records. The sixteenth append must shift the original
    # fourteen 104-byte records, including every timestamp, without truncation.
    call(0x800A5B50, (POSTS, 15))
    check(POSTS, empty*15)
    call(0x800A5CB0, result=0)
    records = []
    for index in range(16):
        wire = (f'Manual post {index+1}'.encode().ljust(96, b' ') if index % 5 == 4
                else pack(Record(4, 0, (INITIAL_IDS[index % 4],), (), bool(index & 1))))
        rtc = bytes((index, 12, 14, index+1, index % 7, 9, 7, 0xD1))
        record = wire+rtc
        write(DRAFT, record)
        call(0x800A5D30, (DRAFT,))
        records = (records+[record])[-15:]
        call(0x800A5CB0, result=len(records))
        check(POSTS, b''.join(records)+empty*(15-len(records)))
        check(DRAFT, record)
    for at in edges: check(at, EDGE)
    check(GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
    actions += [{'load_state': True}, {'resume': True}, {'wait': 2}]
    check(DRAFT-16, bytes(4))
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/noticeboard-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-reader/storage-scenario.json')
    args = parser.parse_args()
    actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'calls': sum('call' in a for a in actions),
                      'assertions': sum('expect' in a for a in actions), 'save_io': False}))


if __name__ == '__main__': main()
