#!/usr/bin/env python3
"""Native sixteen-byte item loads for every confirmed reference identity."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from extended_items import COUNTS, HEADER, VROM
from item_names_test_scenario import ordinary_item
from runtime_module import MODULE_VROM


def scenario(rom, module, names):
    files = by_vrom(rom)
    data = files[VROM].extract(rom)
    if data[:32] != HEADER or sha256(data) != names["data_sha256"]:
        raise ValueError("Native test ROM does not contain the expected name resource")
    configured = bytearray(files[MODULE_VROM].extract(rom))
    if struct.unpack_from(">I", configured, 56)[0] != VROM:
        raise ValueError("Native test ROM has no enabled name resource")
    configured[56:60] = bytes(4)
    if sha256(configured) != module["module_sha256"]:
        raise ValueError("Native test module symbols do not match the ROM")
    loader = module["symbols"]["af_load_item_name"]
    header_check = module["symbols"]["af_item_header_valid"]
    indices, offset, items = {}, 0, []
    for group, count in zip([*range(0x20, 0x30), 0x10], COUNTS):
        base = 0x1000 if group == 0x10 else group << 8
        indices.update({base+i: offset+i for i in range(count)})
        items += [base, base+count-1, base+count]
        offset += count
    seen = set()
    for edit in names["edits"]:
        reference = edit["provenance"]["reference_id"]
        if reference in seen:
            continue
        seen.add(reference)
        bank, index = edit["id"].split(":")
        items.append((0x1000 if bank == "item_10" else int(bank.split("_")[1], 16) << 8)+int(index, 16))
    actions = [{"wait": 8}, {"save_state": True}, {"command": "?"}]
    def test(item, capacity=16, enabled=True, null=False):
        index = indices.get(ordinary_item(item))
        valid = enabled and capacity >= 16 and not null and (item == 0 or index is not None)
        expected = data[32+index*16:48+index*16] if valid and item else b" "*16
        guard = b"G"*72
        actions.extend([
            {"write": ["80197000", guard.hex()]},
            {"call": {"address": loader, "arguments": [0 if null else 0x80197011, capacity, item],
                      "expect_return": int(valid)}},
            {"read": ["80197000", len(guard)],
             "expect": (guard[:17]+expected+guard[33:] if valid else guard).hex()}])
    for item in sorted(set(items+[0, 0x3000, 0xFFFF, 0x12200, 0x17AC, 0x1BA7, 0x1BA8,
                                   0x1C27, 0x1C28, 0x1CA7, 0x1CA8, 0x1D27])):
        test(item)
    for capacity in [*range(16), 17, 32]:
        test(0x2200, capacity)
    test(0x2200, null=True)
    actions.append({"write": ["80194918", "00000000"]})
    test(0x2200, enabled=False)
    test(0, enabled=False)
    actions.append({"write": ["80194918", f"{VROM:08X}"]})
    for index in range(8):
        damaged = bytearray(HEADER)
        damaged[index*4+3] ^= 1
        actions += [{"write": ["80197200", damaged.hex()]},
                    {"call": {"address": header_check, "arguments": [0x80197200], "expect_return": 0}}]
    actions += [{"write": ["80197200", HEADER.hex()]},
                {"call": {"address": header_check, "arguments": [0x80197200], "expect_return": 1}},
                {"call": {"address": header_check, "arguments": [0], "expect_return": 0}},
                {"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["80197000", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--module", type=Path, default=Path("build/runtime-module/module.json"))
    parser.add_argument("--names", type=Path, default=Path("build/extended-items/names.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(), json.loads(args.module.read_text()), json.loads(args.names.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
