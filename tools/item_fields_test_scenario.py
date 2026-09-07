#!/usr/bin/env python3
"""Exercise complete item fields through native setter and message entry points."""

import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from extended_items import COUNTS, HEADER, VROM
from item_names_test_scenario import ordinary_item
from runtime_module import MODULE_VROM, verify_test_module


def scenario(rom, module, names):
    files = by_vrom(rom)
    resource = files[VROM].extract(rom)
    configured = bytearray(files[MODULE_VROM].extract(rom))
    if (resource[:32] != HEADER or sha256(resource) != names["data_sha256"]
            or struct.unpack_from(">I", configured, 56)[0] != VROM):
        raise ValueError("Unexpected native test resource")
    verify_test_module(rom, module)
    symbols = module["symbols"]
    rows = int(symbols["item_rows"], 16)
    main, other, source, buffer, cursor = 0x80142410, 0x80197000, 0x80197340, 0x80197410, 0x80197300
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    def write(address, data):
        actions.append({"write": [f"{address:08X}", data.hex()]})
    def read(address, data):
        actions.append({"read": [f"{address:08X}", len(data)], "expect": data.hex()})
    def call(address, arguments, expected=None):
        record = {"address": address, "arguments": arguments}
        if expected is not None:
            record["expect_return"] = expected & 0xFFFFFFFF
        actions.append({"call": record})
    def setter(slot, name, window=main, length=None):
        write(source, name.ljust(32, b" "))
        call("8009D88C", [window, slot & 0xFFFFFFFF, source, len(name) if length is None else length & 0xFFFFFFFF])
    def insertion(slot, name, index=0, window=main, suffix=b"tail", native_handler=False):
        original = b"p"*index+bytes([0x7F, 0x31+max(0, min(4, slot))])+suffix
        expected = b"p"*index+name.rstrip(b" ")+suffix
        write(buffer-16, b"!"*16+original.ljust(1024, b" ")+b"!"*16)
        if native_handler:
            write(main+12, struct.pack(">I", buffer-16))
            write(buffer-16, struct.pack(">4I", 1, 1, len(original), 0))
            call("800A17FC", [window, index, slot & 0xFFFFFFFF], 0)
            read(buffer-8, struct.pack(">I", len(expected)))
        else:
            call(symbols["af_copy_item_string"], [window, slot & 0xFFFFFFFF, buffer, index, len(original)], len(expected))
            read(buffer-16, b"!"*16)
        read(buffer, expected)
        read(buffer+1024, b"!"*16)
    write(main+0xFC, b"G"*58)
    read(main+0x132, b"G"*4)
    for slot in range(5):
        for size in (16, 11, 10, 1, 0):
            name = b"abcdefghijklmnop"[:size]
            setter(slot, name)
            read(main+0x132, b"G"*4)
            read(main+0x100+slot*10, name[:10].ljust(10, b" "))
            read(rows+slot*16, name.ljust(16, b" "))
            for index in (0, 1, 990):
                insertion(slot, name, index)
            insertion(slot, name, native_handler=True)
            read(main+0x132, b"G"*4)
    read(main+0xFC, b"G"*4)
    read(main+0x132, b"G"*4)
    setter(0, b"abcdefghijklmnop")
    for slot, length in ((-1, 1), (5, 1), (0, 17)):
        setter(slot, b"x"*17, length=length)
        read(rows, b"abcdefghijklmnop")
    for window, pointer in ((0, source), (main, 0)):
        call("8009D88C", [window, 0, pointer, 1])
        read(rows, b"abcdefghijklmnop")
    insertion(-1, b"abcdefghijklmnop")
    insertion(5, b"abcdefghijklmnop")
    insertion(0, b"abcdefghijklmnop", 1004)
    original = (b"p"*1005+b"\x7f\x31tail").ljust(1024, b" ")
    write(buffer-16, b"!"*16+original+b"!"*16)
    call(symbols["af_copy_item_string"], [main, 0, buffer, 1005, 1011], 1011)
    read(buffer-16, b"!"*16+original+b"!"*16)
    write(other, b"G"*0x300)
    setter(2, b"abcdefghijklmnop", window=other)
    read(other, b"G"*0x300)
    setter(2, b"short", window=other)
    insertion(2, b"short", window=other)
    # All confirmed reference identities travel through the real item-ID hook.
    offsets, start = {}, 0
    for group, count in zip([*range(0x20, 0x30), 0x10], COUNTS):
        offsets[group] = start
        start += count
    seen = set()
    for edit in names["edits"]:
        reference = edit["provenance"]["reference_id"]
        if reference in seen:
            continue
        seen.add(reference)
        bank, index = edit["id"].split(":")
        group, index = int(bank.split("_")[1], 16), int(index, 16)
        item = (0x1000 if group == 0x10 else group << 8)+index
        # Match retail's placed-object conversion, including any untranslated
        # destination alias. This tests the wrapper, not translation completeness.
        converted = ordinary_item(item)
        group = 0x10 if converted >> 12 == 1 else converted >> 8
        index = converted & (0xFFF if group == 0x10 else 0xFF)
        expected = resource[32+(offsets[group]+index)*16:48+(offsets[group]+index)*16]
        call("800BB6A0", [item, 4])
        read(rows+64, expected)
        read(main+0x128, expected[:10])
    # Capitalization passes through the actual native item insertion handler.
    setter(0, b"abcdefghijklmnop")
    write(main+12, struct.pack(">I", buffer-16))
    write(main+0x28C, bytes(4))
    write(buffer-16, struct.pack(">4I", 1, 1, 6, 0)+b"\x7f\x75\x7f\x31\x7f\x00")
    write(cursor, bytes(4))
    call("800A21C0", [main, cursor], 0)
    read(cursor, struct.pack(">I", 2))
    call("800A21C0", [main, cursor], 0)
    read(buffer, b"\x7f\x75Abcdefghijklmnop\x7f\x00")
    read(main+0x28C, bytes(4))
    read(rows, b"abcdefghijklmnop")
    # Absent resource uses the unchanged ten-byte loader, padded in the row.
    write(0x80194918, bytes(4))
    write(source, b"G"*32)
    call("80096740", [source, 0x2200])
    call("800BB6A0", [0x2200, 4])
    # Compare using the actual built native bank's first plant entry.
    native = files[0x10F4000].extract(rom)
    pointer = struct.unpack_from(">I", files[0x675720].extract(rom), 0x801076BC-0x80051A80+8)[0]
    offset = pointer-0x06000000
    expected = native[offset:offset+10]
    read(source, expected)
    read(rows+64, expected+b" "*6)
    for item, slot in ((0, 4), (0xFFFF, 4), (0x2200, 5), (0x2200, 0xFFFFFFFF)):
        call("800BB6A0", [item, slot])
        read(rows+64, expected+b" "*6)
    read(0x801988D0, bytes.fromhex("AF16C0DE"*4))
    actions += [{"load_state": True}, {"resume": True}, {"wait": 2}]
    read(source, bytes(4))
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
