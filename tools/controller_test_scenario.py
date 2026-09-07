#!/usr/bin/env python3
"""Native DMA and termination tests for approved controller instructions."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from reference_matches import load_matches
from textbanks import Bank


def scenario(rom):
    files = by_vrom(rom)
    entries = Bank("message", 0x02000000, 0x00CF9000,
                   files[0x02000000].extract(rom), files[0x00CF9000].extract(rom)).entries()
    matches = load_matches(Path(__file__).resolve().parents[1]/"translations/reference_matches.json")
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    window, data, cursor = 0x8019B000, 0x8019B400, 0x8019B380
    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})
    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})
    for record in matches.values():
        if "controller" not in record:
            continue
        number = int(record["id"].split(":")[1], 16)
        entry = entries[number]
        if (sha256(entry) != record["controller"]["adapted_sha256"]
                or entry[-2:] not in (b"\x7f\x00", b"\x7f\x01")):
            raise ValueError("ROM lacks the complete approved controller message")
        write(window, bytes(0x330))
        write(window+12, struct.pack(">I", data))
        write(data-16, b"G"*0x440)
        actions.append({"call": {"address": "8009E558", "arguments": [data, number, 0], "expect_return": 1}})
        read(data, struct.pack(">4I", 1, number, len(entry), 0)+entry)
        read(data-16, b"G"*16)
        read(data+0x410, b"G"*32)
        write(cursor, struct.pack(">I", len(entry)-2))
        for expected, flags in ((2, 8), (1, 0)):
            actions.append({"call": {"address": "800A21C0", "arguments": [window, cursor], "expect_return": expected}})
            read(window+0x28C, struct.pack(">I", flags))
    read(0x8019C8D0, bytes.fromhex("AF32C0DE"*4))
    actions += [{"load_state": True}, {"resume": True}, {"wait": 2}]
    read(window, bytes(4))
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
