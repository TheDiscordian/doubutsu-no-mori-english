#!/usr/bin/env python3
"""Generate guarded real-DMA item loads, including every furniture rotation."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom, sha256, verified_rom
from item_candidates import FURNITURE_COUNT
from textbanks import banks


def ordinary_item(item):
    for start, end, base in ((0x17AC, 0x1BA8, 0x2400), (0x1BA8, 0x1C28, 0x2D00),
                              (0x1C28, 0x1CA8, 0x2300), (0x1CA8, 0x1D28, 0x2204)):
        if start <= item < end:
            return base+((item-start) >> 2)
    return item


def scenario(original, rom):
    data = by_vrom(rom)[0x10F4000].extract(rom)
    source = by_vrom(original)[0x10F4000].extract(original)
    if len(data) != len(source):
        raise ValueError("Item DMA file dimensions changed")
    selected = {b.name: b for b in banks(original) if b.name.startswith("item_")}
    items = []
    for name, bank in selected.items():
        group = int(name.split("_")[1], 16)
        items += ([0x1000+i for i in range(FURNITURE_COUNT*4)] if group == 0x10 else
                  [(group << 8)+i for i in range(len(bank.entries()))])
    actions = [{"wait": 8}, {"save_state": True}, {"command": "?"}]
    for item in [*items, 0, 0x3000, 0xFFFF]:
        converted = ordinary_item(item)
        if converted == 0:
            expected = b" "*10
        elif converted >> 12 not in (1, 2):
            expected = b"G"*10
        else:
            name = "item_10" if converted >> 12 == 1 else f"item_{converted >> 8:02X}"
            index = converted & (0xFFF if name == "item_10" else 0xFF)
            bank = selected[name]
            if index >= len(bank.entries()):
                raise ValueError("Converted item index exceeds its native bank")
            offset = bank.data_offset+index*10
            expected = data[offset:offset+10]
        actions += [{"write": ["80197000", (b"G"*42).hex()]},
                    {"call": {"address": "80096740", "arguments": [0x80197010, item]}},
                    {"read": ["80197000", 42], "expect": (b"G"*16+expected+b"G"*16).hex()}]
    actions += [{"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["80197000", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, help="Bound each isolated scenario to this many item loads")
    args = parser.parse_args()
    original, rom = verified_rom(args.source.read_bytes()), args.rom.read_bytes()
    actions = scenario(original, rom)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    outputs = []
    if args.batch_size is not None:
        if not 1 <= args.batch_size <= 512:
            parser.error("batch-size must be between 1 and 512")
        calls = actions[3:-5]
        if len(calls) % 3:
            raise ValueError("Unexpected item scenario boundaries")
        for batch, start in enumerate(range(0, len(calls), args.batch_size*3)):
            path = args.output.with_stem(args.output.stem+f"-{batch}")
            part = actions[:3]+calls[start:start+args.batch_size*3]+actions[-5:]
            path.write_text(json.dumps(part, indent=2)+"\n")
            outputs.append({"path": str(path), "loads": len(part[3:-5])//3, "actions": len(part)})
    else:
        args.output.write_text(json.dumps(actions, indent=2)+"\n")
        outputs.append({"path": str(args.output), "actions": len(actions)})
    print(json.dumps({"rom_sha256": sha256(rom), "actions": len(actions), "outputs": outputs}))


if __name__ == "__main__":
    main()
