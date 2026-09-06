#!/usr/bin/env python3
"""Generate silent native tests for B selection and closing-sound suppression."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from runtime_module import MODULE_RAM, MODULE_VROM


def scenario(rom):
    files = by_vrom(rom)
    module = files[MODULE_VROM].extract(rom)
    code = files[CODE_VROM].extract(rom)
    used = struct.unpack_from(">I", module, 12)[0]
    hook = struct.unpack_from(">I", code, 0x800667C0-CODE_RAM)[0]
    close = 0x80000000 | (hook & 0x3FFFFFF)*4
    if hook >> 26 != 3 or not MODULE_RAM+0x300 <= close < MODULE_RAM+used:
        raise ValueError("Missing resident choice-close hook")
    actions = [{"wait": 8}, {"save_state": True}, {"command": "?"}]
    window, choice, index = 0x80197000, 0x801971B0, 0x80197380
    global_flags = 0x8014269C

    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})

    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})

    def call(address, args, result=None):
        value = {"address": f"{address:08X}", "arguments": args}
        if result is not None:
            value["expect_return"] = result
        actions.append({"call": value})

    write(window, bytes(0x330))
    write(window+12, struct.pack(">I", 0x80197400))
    write(0x80197400, struct.pack(">4I", 1, 1, 4, 0)+b"\x7f\x62\x7f\x00")
    write(choice+0xB7, b"G"*5)
    write(index, bytes(4))
    call(0x800A21C0, [window, index], 0)
    read(index, struct.pack(">I", 2))
    read(choice+0xB7, b"G\x01\x01GG")
    call(0x80065064, [choice, 0])
    read(choice+0xB8, b"\x00\x00GG")

    # Exercise the actual native controller path, not just a simulated outcome.
    write(0x80104F94, bytes(4))
    write(0x8010EF90, struct.pack(">I", 0x80197C00))
    write(0x80197C00, bytes(0x100))
    write(0x80197C20, b"\x40\x00")  # B trigger.
    write(choice+0xB8, b"\x01\x01")
    write(choice+0x7C, struct.pack(">3I", 4, 0, 1))
    call(0x80066194, [choice, 0], 1)
    read(choice+0x80, struct.pack(">2I", 3, 3))
    write(choice+0xB8, bytes(2))
    write(choice+0x80, struct.pack(">2I", 1, 1))
    call(0x80066194, [choice, 0], 0)
    read(choice+0x80, struct.pack(">2I", 1, 1))
    write(0x80197C20, b"\x80\x00")  # A chooses the current row.
    call(0x80066194, [choice, 0], 1)
    read(choice+0x80, struct.pack(">2I", 1, 1))

    # Helpers return their sound decision for assertions. Their production caller
    # ignores the return; emulator audio output remains disabled throughout.
    for flags, cursor, expected in ((b"\0\0", 3, 0x0D), (b"\1\0", 3, 5),
                                     (b"\1\1", 3, 0x15), (b"\1\1", 1, 0x0D)):
        write(global_flags, struct.pack(">I", 0x30000))
        write(choice+0xB8, flags)
        write(choice+0x84, struct.pack(">I", cursor))
        call(close, [choice], expected)
        value = 0x30800 if expected == 0x15 else 0x30000
        read(global_flags, struct.pack(">I", value))

    write(global_flags, struct.pack(">I", 0x30800))
    call(0x8009FA18, [], 0)
    call(0x8009FA38, [], 0)
    write(global_flags, struct.pack(">I", 0x30000))
    call(0x8009FA18, [], 5)
    call(0x8009FA38, [], 0x15)

    # Preserve every native disappearance setup field and keep the new flag until
    # the message enters WAIT. Clearing one window must not alter another window.
    write(choice+0xB8, b"\x01\x01")
    write(choice+0x84, struct.pack(">I", 3))
    call(0x800667B4, [choice, 0])
    read(choice+0x98, struct.pack(">5I", 0x3F800000, 3, 0xFFFFFFFF, 1, 0))
    read(choice+0xB4, bytes(4))
    read(global_flags, struct.pack(">I", 0x30800))
    write(window+0x28C, struct.pack(">I", 0x34800))
    write(window+0x2E0, struct.pack(">I", 4))
    call(0x800A289C, [window, 0])
    read(window+0x28C, struct.pack(">I", 0x34000))
    read(window+0x290, bytes(4))
    read(window+0x2A4, bytes(8))
    read(window+0x2AC, struct.pack(">4I", 0xFFFFFFFF, 4, 6, 0))
    read(window+0x2D8, struct.pack(">I", 4))
    read(global_flags, struct.pack(">I", 0x30800))
    write(global_flags, struct.pack(">I", 0x348C0))
    call(0x8009E6F8, [0])
    read(global_flags, struct.pack(">I", 0x30000))

    actions += [{"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["80197000", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions = scenario(rom)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"rom_sha256": sha256(rom), "actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
