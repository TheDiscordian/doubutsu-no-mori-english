#!/usr/bin/env python3
"""Test native text-formatting consumers without changing font assets."""

import argparse
import json
from pathlib import Path
import struct


def scenario():
    actions = [{"wait": 8}, {"save_state": True}, {"command": "?"}]
    sentence, text, graph, gfx_pp, gfx = 0x80197000, 0x80197200, 0x80197300, 0x80197310, 0x80197400
    char = sentence+0x48
    guard = b"FONT"*4

    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})

    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})

    def call(address, args, result=None):
        value = {"address": f"{address:08X}", "arguments": args}
        if result is not None:
            value["expect_return"] = result
        actions.append({"call": value})

    def floats(*values):
        return struct.pack(">"+"f"*len(values), *values)

    def dispatch(command):
        write(sentence, bytes(0x88))
        write(sentence, struct.pack(">II", text, len(command)))
        write(sentence+0x0C, floats(25, 100))
        write(sentence+0x18, b"\x32\x3c\x32\xff")
        write(sentence+0x1C, floats(2, 3, 0.5, 1/3))
        write(sentence+0x34, floats(11, 1, 1))
        write(char+5, b"\x81")
        write(text, command)
        write(gfx_pp, struct.pack(">I", gfx))
        call(0x8009034C, [text], len(command))
        call(0x800903CC, [command[1]], 5 if command[1] in (0x50, 0x54) else 4)
        call(0x80091C98, [sentence, graph, gfx_pp])
        read(sentence+0x2C, struct.pack(">I", len(command)))
        read(sentence+0x34, floats(11))
        read(sentence-16, guard)
        read(sentence+0x88, guard)

    write(sentence-16, guard)
    write(sentence+0x88, guard)
    write(graph, bytes(4))
    write(gfx-16, guard)
    write(gfx+64, guard)
    for argument in (0, 128, 255):
        dispatch(bytes([0x7F, 0x52, argument]))
        read(sentence+0x30, floats(argument-128))
        read(char+0x0C, floats(100+argument-128))
    for argument in (0, 1, 2):
        dispatch(bytes([0x7F, 0x53, argument]))
        read(sentence+0x14, struct.pack(">I", argument))
        read(char+0x30, floats(argument*8))
    for code in (0x54, 0x5A):
        for argument in (1, 20, 32, 64, 255):
            dispatch(bytes([0x7F, code, argument]))
            scale = argument/32
            if code == 0x54:
                read(char+0x10, floats(scale, scale, 1/scale, 1/scale))
                read(char+5, b"\x8d")
                call(0x800913D4, [char, sentence, gfx_pp])
                read(char+0x10, floats(1, 1, 1, 1))
                read(char+5, b"\x89")
            else:
                read(sentence+0x38, floats(scale, 1/scale))
                read(char+5, b"\x89")
    dispatch(b"\x7f\x50\x12\x34\x56\x02")
    read(char+0x34, b"\x12\x34\x56\xff\x02")
    read(gfx, b"\xfa\x00\x00\x00\x12\x34\x56\xff")
    call(0x800913D4, [char, sentence, gfx_pp])
    read(char+0x34, b"\x12\x34\x56\xff\x01")
    call(0x800913D4, [char, sentence, gfx_pp])
    read(char+0x34, b"\x32\x3c\x32\xff\x00")
    read(gfx+8, b"\xfa\x00\x00\x00\x32\x3c\x32\xff")
    for count in (0, 255):
        dispatch(bytes([0x7F, 0x50, 255, 0, 255, count]))
        call(0x800913D4, [char, sentence, gfx_pp])
        read(char+0x34, bytes([255, 0, 255, 255, max(0, count-1)]))
    write(sentence+0x1C, floats(2, 4, 0.5, 0.25))
    write(sentence+0x38, floats(0.5, 2))
    write(char+0x10, floats(0.25, 0.5, 4, 2))
    write(char+5, b"\x89")
    call(0x80091470, [char, sentence])
    read(char+0x20, floats(0.25, 1, 4, 1))
    read(char+5, b"\x81")
    read(gfx-16, guard)
    read(gfx+64, guard)
    actions += [{"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["80197000", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    actions = scenario()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
