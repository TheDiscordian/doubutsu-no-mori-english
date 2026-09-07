#!/usr/bin/env python3
"""Generate bounded normal inventory inputs for the isolated planting-job test."""

import argparse
import json
from pathlib import Path


def scenario(pockets, slots, direction="g"):
    if direction not in ("w", "s", "f", "g"):
        raise ValueError("Unsupported planting movement direction")
    if (len(pockets) != 15 or not slots or len(slots) != len(set(slots))
            or any(type(slot) is not int or not 0 <= slot < 15 for slot in slots)):
        raise ValueError("Expected fifteen pockets and unique valid planting slots")
    if any(pockets[slot] not in [f"29{i:02X}" for i in range(10)] for slot in slots):
        raise ValueError("Every selected pocket must contain a native sapling or flower seed")
    pockets = list(pockets)
    actions = [{"wait": 2}, {"snapshot_inventory": True, "expect_inventory": {"pockets": pockets.copy()}}]
    for slot in slots:
        # Reopening the native inventory resets the cursor to pocket zero.
        # Allow each cursor movement and menu transition to finish before A.
        actions += [{"key": direction, "duration": 0.22 if pockets[slot] == "2900" else 0.11},
                    {"wait": 1}, {"key": "Return", "duration": 0.08}, {"wait": 2}]
        for key, count in (("s", slot//5), ("g", slot % 5)):
            for _ in range(count):
                actions += [{"key": key, "duration": 0.04}, {"wait": 0.5}]
        actions += [{"key": "a", "duration": 0.08}, {"wait": 2},
                    {"key": "s", "duration": 0.03}, {"wait": 0.5},
                    {"key": "a", "duration": 0.08}, {"wait": 3},
                    {"capture": f"planted-pocket-{slot:02d}.png"}]
        pockets[slot] = "0000"
        actions += [{"snapshot_inventory": True, "expect_inventory": {"pockets": pockets.copy()}},
                    {"snapshot_player": True}, {"save_state": True}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-state", type=Path, required=True)
    parser.add_argument("--slots", type=int, nargs="+", required=True)
    parser.add_argument("--direction", choices=("w", "s", "f", "g"), default="g")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = json.loads((args.seed_state/"results.json").read_text())
    inventory = [row for row in rows if "pockets" in row and row.get("read_only")]
    if not inventory:
        raise ValueError("Seed test needs a read-only native inventory snapshot")
    actions = scenario(inventory[-1]["pockets"], args.slots, args.direction)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
