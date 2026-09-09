#!/usr/bin/env python3
"""Bind native seasonal calendar, creation, and pending-publication checks."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from notice_overlay import verify_installation
from notice_seasonal import ROOT, GUARDS, compiled_resource


def scenario(native, built, report):
    verified_rom(native)
    if sha256(built) != report['output_sha256']: raise ValueError('Changed seasonal native test ROM')
    verify_installation(built, native, report['runtime_module'], report['noticeboard'])
    if not report['noticeboard'].get('seasonal_owner'): raise ValueError('Seasonal publication is not installed')
    source = by_vrom(native)[CODE_VROM].extract(native)
    files = by_vrom(built)
    code = files[CODE_VROM].extract(built)
    guards = {f'{lo:08X}': code[lo-CODE_RAM:hi-CODE_RAM].hex() for lo, hi, _ in GUARDS}
    for lo, hi in ((0x800D5090, 0x800D5104), (0x800D5CF8, 0x800D6218), (0x800C165C, 0x800C1674),
                   (0x800A5CB0, 0x800A5DF4), (0x8007D90C, 0x8007D930), (0x8009BFC0, 0x8009C108)):
        if code[lo-CODE_RAM:hi-CODE_RAM] != source[lo-CODE_RAM:hi-CODE_RAM]:
            raise ValueError('Changed native seasonal calendar, shop, writer, or allocator')
        guards[f'{lo:08X}'] = code[lo-CODE_RAM:hi-CODE_RAM].hex()
    resource = compiled_resource(native, files[0x030A0000].extract(built))
    request = {'module': report['runtime_module'], 'templates': resource['templates'],
               'shops': [value.hex() for value in resource['shops']], 'guards': guards,
               'dates': list(struct.unpack_from('>39H', source, 0x8010B4B0-CODE_RAM)),
               'empty_rtc': source[0x80117AE0-CODE_RAM:0x80117AE8-CODE_RAM].hex()}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True},
            {'test_notice_seasonal': request}, {'load_state': True}, {'resume': True},
            {'wait': 2}, {'read': ['8019B000', 4], 'expect': '00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/notice-seasonal-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/noticeboard-seasonal/native-owner-scenario.json')
    args = parser.parse_args()
    plan = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                    (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                    json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps({'scheduled_body_cases': 78, 'direct_extra_body_cases': 4,
                      'pending_prefix_failures': 5, 'actual_calendar_calls': True,
                      'save_io': False, 'hardware_verified': False}))


if __name__ == '__main__': main()
