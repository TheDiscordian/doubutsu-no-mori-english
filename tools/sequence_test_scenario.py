#!/usr/bin/env python3
"""Generate native DMA and branch tests for the approved home explanation."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_VROM, by_vrom, sha256
from reference_sequences import load_sequences
from textbanks import Bank
from textcodec import command_info, tokenize


def scenario(rom, group_name="nook_home_explanation"):
    files = by_vrom(rom)
    info = command_info(files[CODE_VROM].extract(rom))
    bank = Bank("message", 0x02000000, 0x00CF9000,
                files[0x02000000].extract(rom), files[0x00CF9000].extract(rom))
    entries = bank.entries()
    if group_name not in ("nook_home_explanation", "nook_work_offer", "nook_house_purchase"):
        raise ValueError("No native scenario exists for this sequence")
    members = load_sequences()[group_name]["members"]
    numbers = [int(member["id"].split(":")[1], 16) for member in members]
    for member, number in zip(members, numbers):
        if sha256(entries[number]) != member["encoded_sha256"]:
            raise ValueError("Test ROM does not contain the approved sequence")
    actions = [{"wait": 8}, {"save_state": True}, {"command": "?"}]
    window, data, index = 0x80197000, 0x80197400, 0x80197380

    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})

    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})

    def call(address, args, result):
        actions.append({"call": {"address": f"{address:08X}", "arguments": args, "expect_return": result}})

    def load(number):
        entry = entries[number]
        write(data-16, b"G"*0x440)
        call(0x8009E558, [data, number, 0], 1)
        read(data, struct.pack(">4I", 1, number, len(entry), 0)+entry)
        read(data-16, b"G"*16)
        read(data+0x410, b"G"*32)

    def dispatch(token, result=0):
        write(index, struct.pack(">I", token.offset))
        call(0x800A21C0, [window, index], result)
        if token.data[1] not in (0, 1):
            read(index, struct.pack(">I", token.offset+len(token.data)))

    write(window, bytes(0x330))
    write(window+12, struct.pack(">I", data))
    for position, number in enumerate(numbers):
        load(number)
        commands = [t for t in tokenize(entries[number], info) if t.kind == "cmd"]
        if position+1 < len(numbers) or group_name == "nook_house_purchase":
            link = next(t for t in commands if t.data[1] == 0x0E)
            dispatch(link)
            target = numbers[position+1] if position+1 < len(numbers) else 0x07EA
            read(window+0x2C4, struct.pack(">I", target))
            write(window+0x28C, bytes(4))
            dispatch(commands[-1], 2)
            read(window+0x28C, struct.pack(">I", 8))
            read(window+0x2A0, struct.pack(">I", commands[-1].offset))
            dispatch(commands[-1], 1)
            read(window+0x28C, bytes(4))
        elif group_name == "nook_home_explanation":
            # Native conditional handlers consult the singleton's last selection.
            # All writes are test-only and the complete checkpoint is restored.
            for selection, target in ((0, 0x081E), (1, 0x081D)):
                write(0x80142640, struct.pack(">I", selection))
                write(window+0x2C4, b"\xff"*4)
                for token in commands:
                    if token.data[1] in (0x0F, 0x10):
                        dispatch(token)
                read(window+0x2C4, struct.pack(">I", target))
        else:
            if commands[-1].data != b"\x7f\x00":
                raise ValueError("Work-offer sequence must finish with the native final terminator")
            write(window+0x28C, bytes(4))
            dispatch(commands[-1], 2)
            read(window+0x28C, struct.pack(">I", 8))
            dispatch(commands[-1], 1)
            read(window+0x28C, bytes(4))
    if group_name == "nook_home_explanation":
        # Follow the native repeat response back to the explanation's root.
        load(0x081D)
        repeat = [t for t in tokenize(entries[0x081D], info) if t.kind == "cmd" and t.data[1] == 0x0E]
        if len(repeat) != 1 or repeat[0].data != b"\x7f\x0e\x07\xea":
            raise ValueError("Native repeat response no longer returns to the root")
        dispatch(repeat[0])
        read(window+0x2C4, struct.pack(">I", 0x07EA))
    actions += [{"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["80197000", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sequence", default="nook_home_explanation")
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions = scenario(rom, args.sequence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"rom_sha256": sha256(rom), "actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
