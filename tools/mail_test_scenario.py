#!/usr/bin/env python3
"""Check native mail substitution and complete fixed-record copying in isolation."""

import argparse
import json
from pathlib import Path
import struct

from mail_controls import NATIVE_CODES, native_handlers
from mail_record import Field, Record, pack
from runtime_module import verify_test_module


def scenario(rom, module):
    verify_test_module(rom, module)
    native_handlers(rom)
    text, source, split = 0x80197010, 0x80197110, 0x80197210
    mail, animal, copied = 0x80197410, 0x80197510, 0x80197610
    guard = b"EDGE"*4
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})
    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})
    def call(address, args, expected=None):
        value = {"address": f"{address:08X}", "arguments": args}
        if expected is not None:
            value["expect_return"] = expected
        actions.append({"call": value})
    for index in range(20):
        value = f"field-{index:02d}".encode()
        write(source, value)
        call(0x80092D10, [index, source, len(value)])
        read(0x80140680+index*10, value.ljust(10, b" "))
    for opcode in range(256):
        original = b"x\x7f"+bytes([opcode])+b"z"
        write(text-16, guard+original.ljust(96, b" ")+guard)
        if opcode in NATIVE_CODES:
            index = opcode-0x24 if opcode <= 0x2D else opcode-0x36+10
            expected = b"x"+f"field-{index:02d}".encode()+b"z"
        else:
            expected = original
        # Call the single dispatcher, not its non-advancing outer loop, for
        # unsupported opcodes. This verifies unchanged tokens without hanging.
        call(0x8009341C, [text, 96, 1, len(original), 2], len(expected))
        read(text-16, guard+expected.ljust(96, b" ")+guard)
    original = b"A\x7f\x24\xcdB\x7f\x3f!"
    expected = b"Afield-00\xcdBfield-19!"
    write(text-16, guard+original.ljust(96, b" ")+guard)
    call(0x80093478, [text, 96, len(original), 2])
    read(text-16, guard+expected.ljust(96, b" ")+guard)
    original = b"\x7f\x24-x-\x7f\x3f"
    expected = b"field-00-x-field-19"
    write(text-16, guard+original.ljust(96, b" ")+guard)
    write(split-16, guard+struct.pack(">I", 5)+guard)
    call(0x80093520, [text, 96, len(original), split, 2])
    read(text-16, guard+expected.ljust(96, b" ")+guard)
    read(split-16, guard+struct.pack(">I", 11)+guard)
    records = [Record(1, 0, (543,), ()),
               Record(1, 0, (10,), ((0, Field(b"town  ")), (19, Field(b"some item", 4))), True),
               Record(1, 1, (0, 32, 64, 96, 383),
                      tuple((i*3, Field(bytes(range(i*16, (i+1)*16)), i % 5)) for i in range(6)), True)]
    for record in records:
        envelope = pack(record)
        value = bytearray(b"M"*164)
        # No opaque-format discriminator is installed; these bytes must not
        # reach a text renderer. The complete machine is restored below.
        value[0x24:0x2A] = bytes.fromhex("123400020304")
        value[0x2A:] = envelope
        write(mail-16, guard+value+guard)
        write(copied-16, guard+b"!"*164+guard)
        call(0x8009C67C, [copied, mail])
        read(copied-16, guard+value+guard)
        write(animal-16, guard+b"!"*132+guard)
        call(0x800A82C8, [animal, mail])
        compact = bytes.fromhex("0004123402")+envelope+b"!"*5
        read(animal-16, guard+compact+guard)
        write(copied-16, guard+b"!"*164+guard)
        call(0x800A8344, [copied, animal, 0, 0])
        restored = b"!"*0x24+bytes.fromhex("12340002")+b"!"+bytes([4])+envelope
        read(copied-16, guard+restored+guard)
        read(mail-16, guard+value+guard)
    actions += [{"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": [f"{text:08X}", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--module", type=Path, default=Path("build/runtime-module/module.json"))
    parser.add_argument("--output", type=Path, default=Path("build/audits/mail-native.json"))
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(), json.loads(args.module.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
