#!/usr/bin/env python3
"""Generate guarded real-DMA loads of all native villager-name positions."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom, sha256
from name_candidates import NPC_COUNT


def scenario(rom):
    data = by_vrom(rom)[0xE04000].extract(rom)
    if len(data) < 8+NPC_COUNT*6:
        raise ValueError("Truncated native villager-name file")
    entries = [data[8+i*6:14+i*6] for i in range(NPC_COUNT)]
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    destination = 0x8019B010
    for index in [*range(NPC_COUNT), 0xFF]:
        expected = b"G"*16+(entries[index] if index != 0xFF else b"G"*6)+b"G"*16
        actions += [{"write": ["8019B000", (b"G"*38).hex()]},
                    {"call": {"address": "800ACC38", "arguments": [destination, index]}},
                    {"read": ["8019B000", 38], "expect": expected.hex()}]
    actions += [{"read": ["8019C8D0", 16], "expect": "AF32C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["8019B000", 4], "expect": "00000000"}]
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
