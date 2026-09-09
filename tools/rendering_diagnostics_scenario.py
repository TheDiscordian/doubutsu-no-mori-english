#!/usr/bin/env python3
"""Load complete English diagnostics without executing their state/sound tests."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom
from runtime_module import module_command_info, verify_test_module
from textbanks import Bank, banks
from textcodec import encode
from textvalidate import validate_entry

ROOT = Path(__file__).resolve().parents[1]
APPROVALS = ROOT/'translations/n64-rendering-diagnostics.json'
IDS = ('message:0005', 'message:000F', 'message:0010', 'message:0011')


def scenario(native, built, report):
    native = verified_rom(native)
    if sha256(built) != report['output_sha256']: raise ValueError('Changed diagnostic test ROM')
    verify_test_module(built, report['runtime_module'])
    files, info = by_vrom(built), module_command_info(native)
    installed = Bank('message', 0x2000000, 0xCF9000, files[0x2000000].extract(built),
                     files[0xCF9000].extract(built)).entries()
    originals = next(b for b in banks(native) if b.name == 'message').entries()
    drafts = json.loads(APPROVALS.read_text())
    if tuple(r['id'] for r in drafts) != IDS: raise ValueError('Incomplete diagnostic batch')
    actions = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]
    destination = 0x8019B400
    for row in drafts:
        number = int(row['id'][8:], 16); value = encode(row['translation'], info)
        if sha256(originals[number]) != row['source_sha256'] or value != installed[number]:
            raise ValueError('Diagnostic source or installed complete translation differs')
        validate_entry(originals[number], value, info, 'message')
        actions += [
            {'write': [f'{destination-16:08X}', (b'G'*0x440).hex()]},
            {'call': {'address': '8009E558', 'arguments': [destination, number, 0], 'expect_return': 1}},
            {'read': [f'{destination:08X}', 16+len(value)],
             'expect': (struct.pack('>4I', 1, number, len(value), 0)+value).hex()},
            {'read': [f'{destination-16:08X}', 16], 'expect': (b'G'*16).hex()},
            {'read': [f'{destination+0x410:08X}', 32], 'expect': (b'G'*32).hex()},
        ]
    actions += [{'read': ['8019C8D0', 16], 'expect': 'AF32C0DE'*4},
                {'load_state': True}, {'resume': True}, {'wait': 2},
                {'read': ['8019B400', 4], 'expect': bytes(4).hex()}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/rendering-diagnostics-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/rendering-diagnostics-scenario.json')
    args = parser.parse_args()
    plan = scenario((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                    (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                    json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps({'actions': len(plan), 'loads': len(IDS), 'diagnostic_commands_executed': False}))


if __name__ == '__main__': main()
