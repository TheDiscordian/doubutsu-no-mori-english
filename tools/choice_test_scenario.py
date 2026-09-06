#!/usr/bin/env python3
"""Generate local-only native choice tests from an expanded experimental ROM."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from english_runtime import ChoiceLayout
from runtime_module import MODULE_VROM
from textbanks import Bank


def scenario(rom):
    files = by_vrom(rom)
    module = files[MODULE_VROM].extract(rom)
    layout = ChoiceLayout(*struct.unpack_from(">4I", module, 40))
    if layout.capacity != 20:
        raise ValueError("This scenario requires the twenty-character runtime")
    bank = Bank("select", 0x02400000, 0xD06000,
                files[0x02400000].extract(rom), files[0xD06000].extract(rom))
    entries = bank.entries()
    if len(entries) != 460 or any(len(entry) > 20 for entry in entries):
        raise ValueError("Unexpected expanded choice bank")
    actions = [{"wait": 8}, {"save_state": True}, {"command": "?"}]
    def write(address, data):
        actions.append({"write": [f"{address:08X}", data.hex()]})
    def read(address, data):
        actions.append({"read": [f"{address:08X}", len(data)], "expect": data.hex()})
    def call(address, args, result=None):
        value = {"address": f"{address:08X}", "arguments": args}
        if result is not None:
            value["expect_return"] = result
        actions.append({"call": value})
    window, choice, buffer = 0x80197000, 0x801971B0, 0x80197800
    # Real cartridge DMA, including every long entry and its actual alignment.
    tested = []
    for index, entry in enumerate(entries):
        if len(entry) <= 16:
            continue
        write(buffer-8, b"G"*48)
        call(0x80065D90, [choice, buffer, index, 0])
        read(buffer-8, b"G"*8+entry.ljust(20, b" ")+b"G"*20)
        tested.append(index)
    if len(tested) != 13:
        raise ValueError("Expected thirteen long reference choices")
    # All four global rows, full twenty-byte capacity, and adjacent padding.
    payloads = [b"ABCDEFGHIJKLMNOPQRST", b"B"*20, b"C"*19+b" ", b"D"*17+b" "*3]
    for i, data in enumerate(payloads):
        write(buffer+i*32, data+b"G"*12)
    write(layout.rows, b"G"*160)
    setter_args = [choice]
    for i in range(4):
        setter_args += [buffer+i*32, 20]
    call(0x80065278, setter_args)
    read(choice+0x5C, struct.pack(">4I", 20, 20, 19, 17))
    read(choice+0x7C, struct.pack(">I", 4))
    expected_rows = b"".join(data.rstrip()+b"G"*(32-len(data.rstrip())) for data in payloads)
    read(layout.rows, expected_rows+b"G"*32)
    call(0x80065348, [choice], 120)
    call(0x800651A4, [choice, buffer, 20], 0xFFFFFFFF)  # Fifth row rejected.
    call(0x800651A4, [choice, buffer, 21], 0xFFFFFFFF)  # Overflow rejected.
    for index, payload in enumerate(payloads):
        write(choice+0x84, struct.pack(">I", index))
        call(0x80066130, [choice])
        length = len(payload.rstrip())
        read(choice+0x78, struct.pack(">3I", length, 4, index))
        read(layout.selected, payload[:length]+b"G"*(32-length))
        write(0x80197A00, b"X\x7f\x2eY"+b" "*60)
        call(0x8009F3A8, [window, 0x80197A00, 1, 4], length+2)
        read(0x80197A00, b"X"+payload[:length]+b"Y")
    read(layout.rows, expected_rows)
    actions += [{"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["80197000", 4], "expect": "00000000"}]
    return actions, tested


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions, tested = scenario(rom)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"rom_sha256": sha256(rom), "long_choice_ids": tested,
                      "actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
