#!/usr/bin/env python3
"""Exercise every default catchphrase and bounded native main-message insertion."""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from catchphrases import HEADER, VROM
from runtime_module import verify_test_module


def scenario(rom, module, reference):
    verify_test_module(rom, module)
    data = by_vrom(rom)[VROM].extract(rom)
    if data[:32] != HEADER or sha256(data) != reference["data_sha256"]:
        raise ValueError("Native catchphrase test resource mismatch")
    rows = [data[i:i+16] for i in range(32, len(data), 16)]
    if len(rows) != 216 or rows != sorted(rows):
        raise ValueError("Native catchphrase test requires all sorted rows")
    by_id = {int.from_bytes(r[4:6], "big"): r for r in rows}
    groups = defaultdict(list)
    for row in rows:
        groups[row[:4]].append(row)
    actor, output, cursor, animal = 0x80197000, 0x80197190, 0x801971C0, 0x80197200
    saved, text, window, header = animal+0x4E5, 0x80197810, 0x80197D00, 0x80198020
    guard = b"EDGE"*4
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})
    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})
    def call(symbol, arguments, expected=None):
        address = module["symbols"].get(symbol, symbol)
        record = {"address": f"{address:08X}" if isinstance(address, int) else address,
                  "arguments": [value & 0xFFFFFFFF for value in arguments]}
        if expected is not None:
            record["expect_return"] = expected & 0xFFFFFFFF
        actions.append({"call": record})
    def setup(npc, key):
        write(animal, struct.pack(">H", npc))
        write(saved, key)
    def load(npc, key, expected=None, capacity=10):
        setup(npc, key)
        write(output-16, guard+b"!"*10+guard)
        call("af_load_catchphrase", [output, capacity, npc, saved], int(expected is not None))
        read(output-16, guard+(expected if expected is not None else b"!"*10)+guard)
        read(saved-1, b"\0"+key+b"\0")
    def resolve(expected, pointer=actor):
        write(output-16, guard+b"!"*10+guard)
        call("af_get_catchphrase", [output, pointer])
        read(output-16, guard+expected+guard)
    def insertion(expected, index=0, entry="af_copy_catchphrase", pointer=actor, capitalize=False):
        original = b"p"*index+b"\x7f\x1c"+b"tail"
        phrase = expected.rstrip(b" ")
        inserted = phrase+b"tail"
        if capitalize:
            # The reference capitalizes the first output byte even when the
            # catchphrase is empty, so this can be the following text.
            inserted = inserted[:1].upper()+inserted[1:]
        result = b"p"*index+inserted
        write(text-16, guard+original.ljust(1024, b" ")+guard)
        if entry == "dispatch":
            write(window, bytes(0x300))
            write(window+0x0C, struct.pack(">I", text-16))
            write(window+0x20, struct.pack(">I", pointer))
            write(window+0x28C, struct.pack(">I", 0x10000 if capitalize else 0))
            write(text-16, struct.pack(">4I", 1, 1, len(original), 0))
            write(cursor, struct.pack(">I", index))
            call(0x800A21C0, [window, cursor], 0)
            read(text-8, struct.pack(">I", len(result)))
            read(window+0x28C, bytes(4))
        else:
            call(entry, [pointer, text, index, len(original)], len(result))
            read(text-16, guard)
        read(text, result)
        read(text+1024, guard)
    value = bytearray(0x178)
    value[2] = 3
    struct.pack_into(">I", value, 0x174, animal)
    write(actor, value)
    write(animal, bytes(0x528))
    for npc, row in sorted(by_id.items()):
        load(npc, row[:4], row[6:])
    # Borrowed defaults follow their saved key, not the current actor's own row.
    # The one ambiguous key resolves for either original owner but not a third.
    for key, values in groups.items():
        if len(values) > 1:
            expected = values[0][6:] if len({r[6:] for r in values}) == 1 else None
            load(0xE052, key, expected)
    row = by_id[0xE052]
    setup(0xE052, row[:4])
    resolve(row[6:])
    insertion(row[6:], entry="dispatch", capitalize=True)
    read(saved, row[:4])
    # Shared dynamic-choice insertion still uses the original four-byte phrase.
    insertion(row[:4], entry=0x8009EDBC)
    for npc in (0, 0xDFFF, 0xE0D8, 0xFFFF, 0x1E000):
        # The saved animal ID stays sixteen bits even for an invalid API value.
        write(output, b"!"*10)
        call("af_load_catchphrase", [output, 10, npc, saved], 0)
        read(output, b"!"*10)
    for capacity in (0, 9):
        load(0xE052, row[:4], capacity=capacity)
    call("af_load_catchphrase", [0, 10, 0xE052, saved], 0)
    call("af_load_catchphrase", [output, 10, 0xE052, 0], 0)
    for key in (b"Yup!", b"mew ", b"    "):
        setup(0xE052, key)
        resolve(key+b" "*6)
        insertion(key, entry="dispatch", capitalize=True)
        read(saved, key)
    long_row = next(r for r in rows if len(r[6:].rstrip(b" ")) == 10)
    setup(int.from_bytes(long_row[4:6], "big"), long_row[:4])
    for index in (0, 1, 100, 1010):
        insertion(long_row[6:], index=index)
    original = b"p"*1011+b"\x7f\x1c"+b"tail"
    write(text-16, guard+original.ljust(1024, b" ")+guard)
    call("af_copy_catchphrase", [actor, text, 1011, len(original)], len(original))
    read(text-16, guard+original.ljust(1024, b" ")+guard)
    for index, length in ((-1, 10), (10, 10), (9, 10), (0, 1025), (0, -1), (0, 2)):
        write(text-16, guard+b"\x7f\x50"+b"!"*1022+guard)
        call("af_copy_catchphrase", [actor, text, index, length], length)
        read(text-16, guard+b"\x7f\x50"+b"!"*1022+guard)
    insertion(b"", pointer=0)
    resolve(b" "*10, 0)
    write(0x80194920, bytes(4))
    resolve(long_row[:4]+b" "*6)
    insertion(long_row[:4])
    write(0x80194920, struct.pack(">I", VROM))
    write(header, HEADER)
    call("af_catchphrase_header_valid", [header], 1)
    for offset in range(0, 32, 4):
        damaged = bytearray(HEADER)
        damaged[offset+3] ^= 1
        write(header, damaged)
        call("af_catchphrase_header_valid", [header], 0)
    call("af_catchphrase_header_valid", [0], 0)
    actions += [{"read": ["801988D0", 16], "expect": "AF16C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": [f"{actor:08X}", 4], "expect": "00000000"}]
    return actions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--module", type=Path, default=Path("build/runtime-module/module.json"))
    parser.add_argument("--reference", type=Path, default=Path("build/catchphrases/catchphrases.json"))
    parser.add_argument("--output", type=Path, default=Path("build/catchphrases/native.json"))
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(), json.loads(args.module.read_text()), json.loads(args.reference.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
