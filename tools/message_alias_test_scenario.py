#!/usr/bin/env python3
"""Verify native message aliases or original drafts through the cartridge loader."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, verified_rom
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import encode


def select_messages(edits, *, drafts=False, message_ids=None):
    if message_ids is not None:
        if drafts or not message_ids or len(set(message_ids)) != len(message_ids):
            raise ValueError("Explicit message IDs must be unique and cannot select drafts implicitly")
        selected = [edit for edit in edits if edit["id"] in message_ids]
        if {edit["id"] for edit in selected} != set(message_ids):
            raise ValueError("A requested message is absent from the translation batch")
    else:
        selected = ([edit for edit in edits if edit.get("status") == "draft"] if drafts else
                    [edit for edit in edits if isinstance(edit.get("provenance"), dict) and
                     edit["provenance"].get("match_basis") ==
                     "identical_complete_native_record_and_unanimous_reference_candidate"])
    if (not selected or len({r["id"] for r in selected}) != len(selected)
            or any(not r["id"].startswith("message:") for r in selected)):
        raise ValueError("Expected unique selected messages")
    return selected


def scenario(rom, edits, info, *, drafts=False, message_ids=None):
    files = by_vrom(rom)
    entries = Bank("message", 0x02000000, 0x00CF9000,
                   files[0x02000000].extract(rom), files[0x00CF9000].extract(rom)).entries()
    selected = select_messages(edits, drafts=drafts, message_ids=message_ids)
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    data = 0x8019B400
    for edit in selected:
        if not edit["id"].startswith("message:"):
            raise ValueError("Native message test cannot load another bank")
        number = int(edit["id"].split(":")[1], 16)
        entry = entries[number]
        if entry != encode(edit["translation"], info) or len(entry) > 0x400:
            raise ValueError("Built ROM differs from its complete selected message")
        actions += [{"write": [f"{data-16:08X}", (b"G"*0x440).hex()]},
                    {"call": {"address": "8009E558", "arguments": [data, number, 0], "expect_return": 1}},
                    {"read": [f"{data:08X}", 16+len(entry)],
                     "expect": (struct.pack(">4I", 1, number, len(entry), 0)+entry).hex()},
                    {"read": [f"{data-16:08X}", 16], "expect": (b"G"*16).hex()},
                    {"read": [f"{data+0x410:08X}", 32], "expect": (b"G"*32).hex()}]
    actions += [{"read": ["8019C8D0", 16], "expect": "AF32C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": [f"{data:08X}", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--source-rom", type=Path, default=Path("local/rom/Doubutsu no Mori (Japan).z64"))
    parser.add_argument("--translations", type=Path, required=True)
    parser.add_argument("--drafts", action="store_true", help="Test original drafts instead of native aliases")
    parser.add_argument("--message-id", action="append", help="Repeat to load an explicit batch of translated message IDs")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    info = module_command_info(verified_rom(args.source_rom.read_bytes()))
    actions = scenario(args.rom.read_bytes(), json.loads(args.translations.read_text()), info,
                       drafts=args.drafts, message_ids=args.message_id)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
