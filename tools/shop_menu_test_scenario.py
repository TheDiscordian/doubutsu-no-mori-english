#!/usr/bin/env python3
"""Batch native cartridge loads for approved shop dialogue and its actual labels."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom
from english_runtime import ChoiceLayout
from message_alias_test_scenario import scenario as message_scenario
from reference_matches import load_matches
from runtime_module import MODULE_VROM, module_command_info
from textbanks import Bank
from textcodec import encode


def scenario(rom, edits, info):
    matches = load_matches(Path(__file__).resolve().parents[1]/"translations/reference_matches.json")
    reviewed = [r for r in matches.values() if "native_choices" in r]
    ids = [r["id"] for r in reviewed]
    actions = message_scenario(rom, edits, info, message_ids=ids)
    files = by_vrom(rom)
    layout = ChoiceLayout(*struct.unpack_from(">4I", files[MODULE_VROM].extract(rom), 40))
    if layout.capacity != 20:
        raise ValueError("Shop-label batch requires the approved twenty-byte runtime")
    labels = Bank("select", 0x02400000, 0x00D06000,
                  files[0x02400000].extract(rom), files[0x00D06000].extract(rom)).entries()
    selected = sorted({int.from_bytes(command[offset:offset+2], "big")
                       for r in reviewed
                       for command in [bytes.fromhex(r["native_choices"]["native_command"])]
                       for offset in range(2, len(command), 2)})
    by_id = {r["id"]: r for r in edits}
    extra = []
    choice, buffer = 0x8019B1B0, 0x8019B800
    for index in selected:
        entry = labels[index]
        if entry != encode(by_id[f"select:{index:04X}"]["translation"], info) or len(entry) > 20:
            raise ValueError("ROM does not contain the complete selected shop label")
        extra += [{"write": [f"{choice:08X}", bytes(0xC0).hex()]},
                  {"write": [f"{buffer-8:08X}", (b"G"*48).hex()]},
                  {"call": {"address": "80065D90", "arguments": [choice, buffer, index, 0]}},
                  {"read": [f"{buffer-8:08X}", 48],
                   "expect": (b"G"*8+entry.ljust(20, b" ")+b"G"*20).hex()}]
    return actions[:-5]+extra+actions[-5:], ids, selected


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--source-rom", type=Path, default=Path("local/rom/Doubutsu no Mori (Japan).z64"))
    parser.add_argument("--translations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    info = module_command_info(verified_rom(args.source_rom.read_bytes()))
    actions, ids, selected = scenario(rom, json.loads(args.translations.read_text()), info)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"rom_sha256": sha256(rom), "actions": len(actions), "messages": ids,
                      "choice_ids": selected, "output": str(args.output)}))


if __name__ == "__main__":
    main()
