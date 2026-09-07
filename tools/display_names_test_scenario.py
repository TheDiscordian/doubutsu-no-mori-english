#!/usr/bin/env python3
"""Exercise every display-name row through the native cartridge DMA path."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from display_names import HEADER, VROM, special_table
from runtime_module import MODULE_VROM, verify_test_module


def scenario(rom, native, module, names):
    files = by_vrom(rom)
    data = files[VROM].extract(rom)
    if data[:32] != HEADER or sha256(data) != names["data_sha256"]:
        raise ValueError("Test ROM display-name resource mismatch")
    configured = bytearray(files[MODULE_VROM].extract(rom))
    if struct.unpack_from(">I", configured, 60)[0] != VROM:
        raise ValueError("Test display-name resource is not enabled")
    verify_test_module(rom, module)
    indices = {0xE000+i: i for i in range(216)}
    indices.update({row[0]: 216+i for i, row in enumerate(special_table(native))})
    symbols = module["symbols"]
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    def test(npc, capacity=8, enabled=True, null=False):
        index = indices.get(npc)
        valid = index is not None and capacity >= 8 and enabled and not null
        guard = b"G"*48
        expected = guard
        if valid:
            expected = guard[:17]+data[32+index*8:40+index*8]+guard[25:]
        actions.extend([
            {"write": ["8019B000", guard.hex()]},
            {"call": {"address": symbols["af_load_display_name"],
                      "arguments": [0 if null else 0x8019B011, capacity, npc], "expect_return": int(valid)}},
            {"read": ["8019B000", len(guard)], "expect": expected.hex()}])
    for npc, index in sorted(indices.items()):
        actions.append({"call": {"address": symbols["af_display_name_index"],
                                  "arguments": [npc], "expect_return": index}})
        test(npc)
    for npc in (0, 0xFFFF, 0xE0D8, 0xE0FE, 0xE0FF, 0xE100, 0x1E000):
        test(npc)
    for capacity in range(8):
        test(0xE052, capacity)
    test(0xE052, 16)
    test(0xE052, null=True)
    actions.append({"write": ["8019491C", "00000000"]})
    test(0xE052, enabled=False)
    actions.append({"write": ["8019491C", f"{VROM:08X}"]})
    for index in range(8):
        damaged = bytearray(HEADER)
        damaged[index*4+3] ^= 1
        actions.extend([{"write": ["8019B200", damaged.hex()]},
                        {"call": {"address": symbols["af_display_name_header_valid"],
                                  "arguments": [0x8019B200], "expect_return": 0}}])
    actions.extend([
        {"write": ["8019B200", HEADER.hex()]},
        {"call": {"address": symbols["af_display_name_header_valid"], "arguments": [0x8019B200], "expect_return": 1}},
        {"call": {"address": symbols["af_display_name_header_valid"], "arguments": [0], "expect_return": 0}},
        {"read": ["8019C8D0", 16], "expect": "AF32C0DE"*4},
        {"load_state": True}, {"resume": True}, {"wait": 2},
        {"read": ["8019B000", 4], "expect": "00000000"}])
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--module", type=Path, default=Path("build/runtime-module/module.json"))
    parser.add_argument("--names", type=Path, default=Path("build/display-names/names.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(), args.native.read_bytes(),
                       json.loads(args.module.read_text()), json.loads(args.names.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
