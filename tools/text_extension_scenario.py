#!/usr/bin/env python3
"""Bounded native startup/field check using installed entries and isolated scratch."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, verified_rom
from extended_items import VROM as ITEMS_VROM, COUNTS
from text_extension import verify_installation


def scenario(native, built, report):
    verify_installation(built, verified_rom(native), report)
    window, buffer, source, cursor = 0x80142410, 0x8019B010, 0x8019B500, 0x8019B540
    actions = [{'wait': 8}, {'read': ['80000318', 4], 'expect': '00400000'},
               {'save_state': True}, {'pause_game_thread': True}]
    def write(at, data): actions.append({'write': [f'{at:08X}', data.hex()]})
    def check(at, data): actions.append({'read': [f'{at:08X}', len(data)], 'expect': data.hex()})
    def words(*values): return struct.pack('>'+'I'*len(values), *values)
    def call(at, args, expected=None):
        entry = {'address': f'{at:08X}', 'arguments': args}
        if expected is not None: entry['expect_return'] = expected
        actions.append({'call': entry})
    def insert(slot, name, colour=0):
        # Use the native wrapper, native command parser/move, and startup hooks.
        payload = b'X\x7f\x1eZ'
        write(buffer-16, words(1, 0, len(payload), 0)+payload.ljust(1024, b'!')+b'GUARD-FIELD-END! ')
        write(window+12, words(buffer-16)); write(cursor, words(1))
        if colour:
            call(0x800A1394, [window, cursor, slot, colour], 0)
            expected = b'X\x7f\x50\x32\x82\x46'+bytes((len(name),))+name+b'Z'
            check(cursor, words(7))
        else:
            call(0x800A134C, [window, 1, slot], 0)
            expected = b'X'+name+b'Z'
        check(buffer-8, words(len(expected))); check(buffer, expected)
        check(buffer+1024, b'GUARD-FIELD-END! ')
    write(source, b'abcdefghijklmnop')
    call(0x8009D6D0, [window, 19, source, 16])
    check(window+0x38+19*10, b'abcdefghij')
    insert(19, b'abcdefghijklmnop')
    # Use one actual complete cartridge item through the original and new bridges.
    resource = by_vrom(built)[ITEMS_VROM].extract(built)
    start = sum(COUNTS[:4])  # clothing bank 24; native item identity, no placement conversion
    candidates = [(0x2400+i, resource[32+(start+i)*16:48+(start+i)*16].rstrip(b' ')) for i in range(COUNTS[4])]
    item, name = next((item, name) for item, name in candidates if len(name) > 10 and all(32 <= b < 127 for b in name))
    call(0x800BB6F0, [item, 0]); insert(0, name)
    call(0x800BB6F0, [0, 0]); check(window+0x38, name[:10])
    call(0x800BB6F8, [0, 0]); insert(0, b'')
    call(0x800BB700, [item, 2, 2]); check(window+0x281, b'\x02'); insert(2, name, 2)
    # A rejected expansion must leave the complete native message untouched.
    payload = b'\x7f\x1e'+b'!'*1022
    write(buffer-16, words(1, 0, 1024, 0)+payload)
    call(0x800A134C, [window, 0, 19], 0)
    check(buffer-8, words(1024)); check(buffer, payload)
    check(0x8019C8D0, bytes.fromhex('AF32C0DE'*4))
    actions += [{'load_state': True}, {'resume': True}, {'wait': 2}]
    check(source, bytes(16))
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=Path('build/text-extension-pilot'))
    parser.add_argument('--output', type=Path, default=Path('build/text-extension-scenario.json'))
    args = parser.parse_args()
    actions = scenario(Path('local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                       (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                       json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'calls': sum('call' in a for a in actions),
                      'assertions': sum('expect' in a for a in actions)}))


if __name__ == '__main__': main()
