#!/usr/bin/env python3
"""Generate guarded real-DMA item loads, including every furniture rotation."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom, sha256, verified_rom
from item_candidates import FURNITURE_COUNT
from item_aliases import ordinary_item
from textbanks import banks


def scenario(original, rom, only_items=None):
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
    items += [0, 0x3000, 0xFFFF]
    if only_items is not None:
        if not only_items or len(only_items) != len(set(only_items)) or set(only_items)-set(items):
            raise ValueError("Requested native test items must be unique known cases")
        items = list(only_items)
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    for item in items:
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
        actions += [{"write": ["8019B000", (b"G"*42).hex()]},
                    {"call": {"address": "80096740", "arguments": [0x8019B010, item]}},
                    {"read": ["8019B000", 42], "expect": (b"G"*16+expected+b"G"*16).hex()}]
    actions += [{"read": ["8019C8D0", 16], "expect": "AF32C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["8019B000", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, help="Bound each isolated scenario to this many item loads")
    parser.add_argument("--item", type=lambda value: int(value, 0), action="append",
                        help="Repeat to run only explicit native item cases")
    args = parser.parse_args()
    original, rom = verified_rom(args.source.read_bytes()), args.rom.read_bytes()
    actions = scenario(original, rom, args.item)
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
