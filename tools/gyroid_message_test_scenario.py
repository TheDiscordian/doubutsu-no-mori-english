#!/usr/bin/env python3
"""Exercise the installed gyroid formatter and actual dialogue insertion on N64."""

import argparse
import json
from pathlib import Path
import random
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from font import WIDTH_TABLE
from gyroid_message import SETTER
from runtime_layout import TEST_RETURN, TEST_STACK, GUARD_ADDRESS, GUARD_WORD
from runtime_module import verify_test_module

WINDOW = TEST_RETURN+0x100
SOURCE = TEST_RETURN+0x500
BUFFER = TEST_RETURN+0x700
LOW_STACK = TEST_STACK-0x600
EDGE = b'EDGE'*4


def expected_message(text, length, cuts):
    output = bytearray()
    pixels = rows = 0
    for code in text[:max(0, min(length, 68))]:
        output.append(code)
        if code == 205:
            pixels = 0
            rows += 1
        else:
            pixels += 12-cuts[code]
            if len(output) < 68 and pixels > 186:
                output.append(205)
                pixels = 0
                rows += 1
        if len(output) >= 68 or rows == 5:
            break
    return bytes(output).ljust(68, b' ')


def scenario(rom, module):
    verify_test_module(rom, module)
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    target = int(module['symbols']['af_set_gyroid_message'], 16)
    if struct.unpack_from('>2I', code, SETTER-CODE_RAM) != (0x08000000 | ((target & 0x0FFFFFFF) >> 2), 0):
        raise ValueError('Gyroid message scenario requires the installed entry hook')
    if sha256(code[0x8009F670-CODE_RAM:0x8009F730-CODE_RAM]) != 'c9b41837e194e02d785fb77d7cfde40173c8b20c18691bf947fbc0b3435d38b2':
        raise ValueError('Gyroid message scenario requires unchanged native dialogue insertion')
    cuts = code[WIDTH_TABLE:WIDTH_TABLE+256]
    if len(cuts) != 256 or any(c > 11 for c in cuts):
        raise ValueError('Unexpected native glyph widths')
    if BUFFER+1024+16 >= LOW_STACK:
        raise ValueError('Gyroid message fixture/stack overlap')
    actions = [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}]
    def write(address, value):
        actions.append({'write': [f'{address:08X}', value.hex()]})
    def read(address, value):
        actions.append({'read': [f'{address:08X}', len(value)], 'expect': value.hex()})
    def call(address, args, expected=None):
        value = {'address': f'{address:08X}', 'arguments': [arg & 0xFFFFFFFF for arg in args]}
        if expected is not None:
            value['expect_return'] = expected
        actions.append({'call': value})
    write(LOW_STACK, EDGE)
    write(TEST_STACK+0x30, EDGE)
    texts = [b'', b'a'*31, b'a'*32, b'i'*46, b'i'*47, b"I'i"*21,
             b'a'*64, b'i'*64, b'\xa1'*64, b'  a\xcd\xcd  z ', b'\xcd'*64]
    texts.extend(bytes(range(start, start+64)) for start in range(0, 256, 64))
    rng = random.Random(6102)
    texts.extend(bytes(rng.choice(b" iIl'aa\xcd\xa1!? ") for _ in range(length))
                 for length in (1, 15, 16, 17, 32, 48, 63, 64, 68))
    cases = [(text, len(text)) for text in texts]
    cases += [(b'a'*68, length) for length in (-2147483648, -1, 0, 69, 2147483647)]
    for text, length in cases:
        window = bytearray(b'!'*0x300)
        expected = expected_message(text, length, cuts)
        window[0x132:0x176] = expected
        write(WINDOW, b'!'*0x300)
        write(SOURCE-16, EDGE+text+EDGE)
        call(SETTER, [WINDOW, 0, SOURCE, length])
        read(WINDOW, bytes(window))
        read(SOURCE-16, EDGE+text+EDGE)
        # Actual native insertion preserves every formatted byte except the
        # existing trailing-space trim. No substitute copy implementation.
        if text in (b'a'*64, b'i'*64, b'  a\xcd\xcd  z '):
            value = expected.rstrip(b' ')
            for index in (0, 7, 1024-len(value)-4):
                original = b'p'*index+b'\x7f\x36tail'
                inserted = b'p'*index+value+b'tail'
                write(BUFFER-16, EDGE+original.ljust(1024, b' ')+EDGE)
                call(0x8009F670, [WINDOW, 0, BUFFER, index, len(original)], len(inserted))
                read(BUFFER, inserted)
                read(BUFFER-16, EDGE)
                read(BUFFER+1024, EDGE)
                read(WINDOW, bytes(window))
        read(LOW_STACK, EDGE)
        read(TEST_STACK+0x30, EDGE)
    for window, slot, source in ((WINDOW, -1, SOURCE), (WINDOW, 1, SOURCE),
                                  (WINDOW, 2147483647, SOURCE), (0, 0, SOURCE), (WINDOW, 0, 0)):
        write(WINDOW, b'!'*0x300)
        call(SETTER, [window, slot, source, 1])
        read(WINDOW, b'!'*0x300)
    for shift in (-1, 0, 1, 16):
        window = bytearray(b'!'*0x300)
        text = b'a'*64
        window[0x132+shift:0x132+shift+64] = text
        write(WINDOW, bytes(window))
        call(SETTER, [WINDOW, 0, WINDOW+0x132+shift, 64])
        window[0x132:0x176] = expected_message(text, 64, cuts)
        read(WINDOW, bytes(window))
    read(LOW_STACK, EDGE)
    read(TEST_STACK+0x30, EDGE)
    read(GUARD_ADDRESS, struct.pack('>4I', *([GUARD_WORD]*4)))
    actions += [{'load_state': True}, {'resume': True}, {'wait': 2}]
    read(WINDOW, bytes(4))
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--module', type=Path, default=Path('build/runtime-module/module.json'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions = scenario(rom, json.loads(args.module.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'calls': sum('call' in a for a in actions),
                      'assertions': sum('expect' in a for a in actions), 'rom_sha256': sha256(rom)}, indent=2))


if __name__ == '__main__':
    main()
