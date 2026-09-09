#!/usr/bin/env python3
"""Bind the silent native notice-owner and full-body drawing batch."""

import argparse
import json
from pathlib import Path
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from audit_noticeboard import INITIAL_IDS, initial_body
from mail_catalog import parse
from mail_record import Record
from notice_record import pack
from notice_overlay import (ROOT, NEW_VROM, NEW_RELOCATION, OWNER_VROM,
                            OWNER_RELOCATION, verify_installation)


def scenario(native, built, report, *, skip_initial=0, edges_only=False):
    if type(skip_initial) is not int or not 0 <= skip_initial <= 8:
        raise ValueError('Invalid completed initial-body count')
    if type(edges_only) is not bool or (edges_only and skip_initial != 8):
        raise ValueError('Edge-only continuation requires all eight initial cases completed')
    if sha256(built) != report['output_sha256']:
        raise ValueError('Changed notice-reader cartridge')
    verify_installation(built, native, report['runtime_module'], report['noticeboard'])
    files = by_vrom(built)
    catalog = parse(files[0x030A0000].extract(built))[1]
    cases = []
    for number in INITIAL_IDS:
        for capital in (False, True):
            value = Record(4, 0, (number,), (), capital)
            cases.append({'template': number, 'capital': int(capital),
                          'wire': pack(value).hex(), 'body': initial_body(value, catalog).hex()})
    loader_at = 0x1060+0x800262D0-0x80025C60
    loader = native[loader_at:loader_at+0xF0]
    if (sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00'
            or built[loader_at:loader_at+0xF0] != loader):
        raise ValueError('Changed native overlay loader')
    code = files[CODE_VROM].extract(built)
    old_code = by_vrom(native)[CODE_VROM].extract(native)
    guards = {}
    for lo, hi in ((0x8009BFC0, 0x8009C108), (0x80078DAC, 0x80078E2C),
                   (0x8007D90C, 0x8007D930), (0x800A5CB0, 0x800A5D30)):
        if code[lo-CODE_RAM:hi-CODE_RAM] != old_code[lo-CODE_RAM:hi-CODE_RAM]:
            raise ValueError('Changed native notice helper')
        guards[f'{lo:08X}'] = code[lo-CODE_RAM:hi-CODE_RAM].hex()
    request = {'module': report['runtime_module'], 'report': report['noticeboard']['overlay'],
               'skip_initial': skip_initial,
               'edges_only': edges_only,
               'cases': cases, 'guards': guards, 'loader': loader.hex(),
               'data': files[NEW_VROM].extract(built).hex(),
               'relocation': files[NEW_RELOCATION].extract(built).hex(),
               'owner': files[OWNER_VROM].extract(built).hex(),
               'owner_relocation': files[OWNER_RELOCATION].extract(built).hex(),
               'assets': files[0x00ABA000].extract(built).hex(),
               'empty_post': (b' '*96+code[0x80117AE0-CODE_RAM:0x80117AE8-CODE_RAM]).hex()}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True},
            {'test_notice_reader': request}, {'load_state': True}, {'resume': True},
            {'wait': 2}, {'read': ['8019B000', 4], 'expect': '00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/noticeboard-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-reader/reader-scenario.json')
    parser.add_argument('--skip-initial', type=int, default=0,
                        help='Continue after this many completed initial cases; retain prior evidence')
    parser.add_argument('--edges-only', action='store_true',
                        help='Run remaining controls, labels, and cleanup after completed body evidence')
    args = parser.parse_args()
    actions = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()),
                       skip_initial=8 if args.edges_only else args.skip_initial, edges_only=args.edges_only)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'initial_body_cases': 0 if args.edges_only else 8-args.skip_initial,
                      'edges_only': args.edges_only, 'save_io': False}))


if __name__ == '__main__': main()
