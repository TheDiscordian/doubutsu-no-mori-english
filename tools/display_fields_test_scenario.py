#!/usr/bin/env python3
"""Exercise wider names through native nameplate and main-dialogue consumers."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from display_names import HEADER, VROM, special_table
from runtime_module import verify_test_module


def scenario(rom, native, module, names, advances):
    verify_test_module(rom, module)
    files = by_vrom(rom)
    data = files[VROM].extract(rom)
    if data[:32] != HEADER or sha256(data) != names["data_sha256"]:
        raise ValueError("Display consumer resource mismatch")
    symbols = module["symbols"]
    indices = {0xE000+i: i for i in range(216)}
    indices.update({r[0]: 216+i for i, r in enumerate(special_table(native))})
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    actor, animal, window = 0x80197000, 0x80197180, 0x80197200
    output, cursor, text = 0x801971C0, 0x801971A0, 0x80197610
    game, graph, gfx = 0x80197A40, 0x80197A60, 0x80197D80
    guard = b"EDGE"*4
    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})
    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})
    def call(address, arguments, expected=None):
        address = symbols.get(address, address)
        record = {"address": f"{address:08X}" if isinstance(address, int) else address, "arguments": arguments}
        if expected is not None:
            record["expect_return"] = expected & 0xFFFFFFFF
        actions.append({"call": record})
    def actor_data(part, fg, npc=None):
        value = bytearray(0x178)
        value[2] = part
        struct.pack_into(">H", value, 6, fg)
        if npc is not None:
            struct.pack_into(">I", value, 0x174, animal)
            write(animal, struct.pack(">H", npc)+bytes(10))
        write(actor, value)
    def expected_name(npc):
        index = indices[npc]
        return data[32+index*8:40+index*8]
    def resolve(expected, pointer=actor):
        write(output-16, guard+b"!"*8+guard)
        call("af_get_display_name", [output, pointer])
        read(output-16, guard+expected+guard)
    def setup(expected):
        write(window-16, guard+bytes(0x300)+guard)
        write(0x80198874, b"EDGE")
        call(0x8009D308, [window, actor, 1])
        name = expected.rstrip(b" ")
        width = sum(advances[f"{c:02X}"] for c in name)
        width += width % 2
        read(window+0x20, struct.pack(">IIIff", actor, 1, len(name), 61+(72-width)/2, 64))
        read(0x8019886C, expected+b"EDGE")
        read(window-16, guard)
        read(window+0x300, guard)
    def insertion(expected, index=0, suffix=b"tail", pointer=actor, entry="af_copy_talk_name"):
        original = b"p"*index+b"\x7f\x1b"+suffix
        result = b"p"*index+expected.rstrip(b" ")+suffix
        write(text-16, guard+original.ljust(1024, b" ")+guard)
        if entry in ("main", "dispatch"):
            write(window+0x0C, struct.pack(">I", text-16))
            write(window+0x20, struct.pack(">I", pointer))
            write(text-16, struct.pack(">4I", 1, 1, len(original), 0))
            write(cursor, struct.pack(">I", index))
            if entry == "dispatch":
                write(window+0x28C, struct.pack(">I", 0x10000))
            call(0x800A21C0 if entry == "dispatch" else 0x800A10D8, [window, cursor], 0)
            read(text-8, struct.pack(">I", len(result)))
            if entry == "dispatch":
                read(window+0x28C, bytes(4))
        else:
            call(entry, [pointer, text, index, len(original)], len(result))
            read(text-16, guard)
        read(text, result)
        read(text+1024, guard)
    for npc in (0xE052, 0xE001, 0xE048):
        actor_data(3, 0xD008, npc)
        name = expected_name(npc)
        resolve(name)
        setup(name)
        insertion(name, entry="dispatch")
    for part, npc in ((3, 0xD008), (2, 0xD004), (0, 0xD064), (3, 0x800D)):
        actor_data(part, npc)
        name = expected_name(npc)
        resolve(name)
        setup(name)
        insertion(name, index=1)
    # Invalid branch identities must retain the native fallback rather than
    # cross from a malformed animal ID into the special-character table.
    default = by_vrom(native)[CODE_VROM].extract(native)[0x8010B810-CODE_RAM:0x8010B816-CODE_RAM]+b"  "
    for part, fg, npc in ((2, 0xE052, None), (3, 0xE052, None), (3, 0xD008, 0xD004), (3, 0xD008, 0xE0FF)):
        actor_data(part, fg, npc)
        resolve(default)
    resolve(default, 0)
    actor_data(3, 0xE052, 0xE052)
    name = expected_name(0xE052)
    for index in (0, 1, 100, 1012):
        insertion(name, index=index)
    insertion(b"", index=1012, pointer=0)
    original = b"p"*1013+b"\x7f\x1b"+b"tail"
    write(text-16, guard+original.ljust(1024, b" ")+guard)
    call("af_copy_talk_name", [actor, text, 1013, len(original)], len(original))
    read(text-16, guard+original.ljust(1024, b" ")+guard)
    # The shared native function still loads exactly six bytes for choice users.
    native_names = files[0xE04000].extract(rom)
    six = native_names[8+0x52*6:14+0x52*6]
    insertion(six, entry=0x8009ED14)
    write(0x8019491C, bytes(4))
    resolve(six+b"  ")
    insertion(six)
    write(0x8019491C, struct.pack(">I", VROM))
    # Execute the real draw consumer with an isolated graphics context/list.
    setup(name)
    write(window+0x176, b"\xff\xff\xff\xff")
    write(game, struct.pack(">I", graph))
    write(graph, bytes(0x300))
    # The native renderer allocates four vertices per glyph from the arena's
    # descending data pointer as well as appending display-list commands.
    write(graph+0x290, struct.pack(">4I", 1536, gfx, gfx, gfx+1536))
    write(gfx-16, guard+bytes(1536)+guard)
    write(0x80198880, b"EDGE")
    call(0x800A2BB0, [window, game, 0])
    read(0x80198878, name+b"EDGE")
    read(gfx-16, guard)
    read(gfx+1536, guard)
    read(graph+0x29C, struct.pack(">I", gfx+1536-8*64))
    read(graph+0x298, struct.pack(">I", gfx+24+8*72))
    actions += [{"read": [f"{gfx:08X}", 1536]},
                {"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["80197000", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--native", type=Path, required=True)
    parser.add_argument("--module", type=Path, default=Path("build/runtime-module/module.json"))
    parser.add_argument("--names", type=Path, default=Path("build/display-names/names.json"))
    parser.add_argument("--build", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(), args.native.read_bytes(), json.loads(args.module.read_text()),
                       json.loads(args.names.read_text()), json.loads(args.build.read_text())["advance_by_glyph"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
