#!/usr/bin/env python3
"""Load complete reviewed dialogue and dispatch its added player/town-name fields."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from english_runtime import TOWN_RETURN
from reference_fields import field_permit
from reference_matches import load_matches
from runtime_module import module_command_info, verify_test_module
from textbanks import Bank, banks
from textcodec import encode, tokenize
from textvalidate import validate_entry


def scenario(rom, source, edits, module):
    source = verified_rom(source)
    verify_test_module(rom, module)
    files = by_vrom(rom)
    info = module_command_info(source)
    original_code = by_vrom(source)[CODE_VROM].extract(source)
    code = files[CODE_VROM].extract(rom)
    guards = [(start, original_code[start-CODE_RAM:end-CODE_RAM]) for start, end in
              ((0x800950D8, 0x800950E8), (0x8009EBB0, 0x8009ED14),
               (0x8009F428, 0x8009F4A4), (0x800A1078, 0x800A10D8),
               (0x800A1774, 0x800A17B8), (0x80107B70, 0x80107B76))]
    guards.append((0x8009F4A4, TOWN_RETURN+b" "*80+bytes(4)))
    for start, expected in guards:
        if code[start-CODE_RAM:start-CODE_RAM+len(expected)] != expected:
            raise ValueError("Player/town-name consumer or English suffix guard changed")
    sources = next(b for b in banks(source) if b.name == "message").entries()
    entries = Bank("message", 0x02000000, 0x00CF9000,
                   files[0x02000000].extract(rom), files[0x00CF9000].extract(rom)).entries()
    matches = load_matches(Path(__file__).resolve().parents[1]/"translations/reference_matches.json")
    approved = [r for r in matches.values() if "available_fields" in r]
    by_id = {r["id"]: r for r in edits}
    if not approved:
        raise ValueError("No reviewed player/town-field messages")
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    window, data, cursor, player, town = 0x8019B000, 0x8019B400, 0x8019B380, 0x8019B900, 0x80129E00
    player_name, town_name = b"Orchid", b"Maple "
    inserted = {0x1A: bytes.fromhex("7F504B5F9B06")+player_name, 0x2F: town_name.rstrip(b" ")}
    insertions = 0

    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})

    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})

    def call(address, arguments, result):
        actions.append({"call": {"address": f"{address:08X}", "arguments": arguments, "expect_return": result}})

    for start, expected in guards:
        read(start, expected)
    write(window, bytes(0x330))
    write(window+12, struct.pack(">I", data))
    write(player-16, b"G"*16+player_name+b"G"*16)
    write(0x80136FD8, struct.pack(">I", player))
    write(town, town_name)
    # These are temporary checkpointed inputs, not new saved-name formats.
    # Neither actor state nor free-string preparation supplies these names.
    for record in approved:
        id = record["id"]
        number = int(id.split(":")[1], 16)
        original, entry = sources[number], entries[number]
        if entry != encode(by_id[id]["translation"], info):
            raise ValueError("Built ROM differs from the complete reviewed message")
        permit = field_permit(id, original, entry, matches)
        validate_entry(original, entry, info, "message", "reference_layout",
                       resident_runtime=True, field_permit=permit)
        write(data-16, b"G"*0x440)
        call(0x8009E558, [data, number, 0], 1)
        read(data, struct.pack(">4I", 1, number, len(entry), 0)+entry)
        expected = entry
        while True:
            targets = [t for t in tokenize(expected, info) if t.kind == "cmd" and t.data[1] in permit.fields]
            if not targets:
                break
            token = targets[0]
            write(cursor, struct.pack(">I", token.offset))
            write(window+0x28C, bytes(4))
            call(0x800A21C0, [window, cursor], 0)
            value = inserted[token.data[1]]
            expected = expected[:token.offset]+value+expected[token.offset+2:]
            read(data, struct.pack(">4I", 1, number, len(expected), 0)+expected)
            read(cursor, struct.pack(">I", token.offset+(6 if token.data[1] == 0x1A else 0)))
            insertions += 1
        read(data-16, b"G"*16)
        read(data+0x410, b"G"*32)
        read(player-16, b"G"*16+player_name+b"G"*16)
        read(town, town_name)
    read(0x8019C8D0, bytes.fromhex("AF32C0DE"*4))
    actions += [{"load_state": True}, {"resume": True}, {"wait": 2}]
    read(window, bytes(4))
    read(player, bytes(6))
    return actions, [r["id"] for r in approved], insertions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--source-rom", type=Path, default=Path("local/rom/Doubutsu no Mori (Japan).z64"))
    parser.add_argument("--translations", type=Path, required=True)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions, ids, insertions = scenario(rom, args.source_rom.read_bytes(),
                                       json.loads(args.translations.read_text()), json.loads(args.module.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"rom_sha256": sha256(rom), "actions": len(actions),
                      "messages": ids, "insertions": insertions, "output": str(args.output)}))


if __name__ == "__main__":
    main()
