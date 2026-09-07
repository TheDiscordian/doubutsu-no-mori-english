#!/usr/bin/env python3
"""Exercise native appearance requests, complete loads, and reviewed speaker fields."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from catchphrases import HEADER, VROM
from reference_fields import catchphrase_permit
from reference_matches import load_matches
from runtime_module import MODULE_VROM, module_command_info, verify_test_module
from textbanks import Bank, banks
from textcodec import encode, tokenize
from textvalidate import validate_entry


def consumer_guards(rom, source, module):
    original = by_vrom(source)[CODE_VROM].extract(source)
    if sha256(original) != "2639d08d6a3de000fa270ebd3837f86d546041cd4a00d40fbf817a63f7b13810":
        raise ValueError("Original speaker-path code changed")
    patched = bytearray(original)
    for address, symbol in ((0x8009D324, "af_get_display_name"), (0x800A114C, "af_copy_catchphrase")):
        target = int(module["symbols"][symbol], 16)
        struct.pack_into(">I", patched, address-CODE_RAM, 0x0C000000 | ((target & 0x0FFFFFFF) >> 2))
    struct.pack_into(">I", patched, 0x8009D334-CODE_RAM, 0x24050008)
    code = by_vrom(rom)[CODE_VROM].extract(rom)
    guards = [(start, bytes(patched[start-CODE_RAM:end-CODE_RAM])) for start, end in
              ((0x8007BF30, 0x8007BF6C), (0x8009D200, 0x8009D260),
               (0x8009D308, 0x8009D3B4), (0x8009D3E4, 0x8009D458),
               (0x8009FFB0, 0x800A010C), (0x800A1124, 0x800A1170))]
    for start, expected in guards:
        if code[start-CODE_RAM:start-CODE_RAM+len(expected)] != expected:
            raise ValueError("Native speaker request, appearance, or catchphrase consumer changed")
    return guards


def scenario(rom, source, edits, module, reference):
    source = verified_rom(source)
    verify_test_module(rom, module)
    files = by_vrom(rom)
    resource = files[VROM].extract(rom)
    if resource[:32] != HEADER or sha256(resource) != reference["data_sha256"]:
        raise ValueError("Catchphrase resource differs from its complete reference")
    if struct.unpack_from(">I", files[MODULE_VROM].extract(rom), 64)[0] != VROM:
        raise ValueError("Catchphrase resource is not enabled")
    guards = consumer_guards(rom, source, module)
    rows = [resource[i:i+16] for i in range(32, len(resource), 16)]
    long_rows = []
    for row in rows:
        if len(row[6:].rstrip(b" ")) == 10 and row[6:] not in [r[6:] for r in long_rows]:
            long_rows.append(row)
    if len(rows) != 216 or rows != sorted(rows) or len(long_rows) < 2:
        raise ValueError("Complete defaults and two distinct ten-character phrases required")
    sources = next(b for b in banks(source) if b.name == "message").entries()
    entries = Bank("message", 0x02000000, 0x00CF9000,
                   files[0x02000000].extract(rom), files[0x00CF9000].extract(rom)).entries()
    info = module_command_info(source)
    matches = load_matches(Path(__file__).resolve().parents[1]/"translations/reference_matches.json")
    approved = [r for r in matches.values() if "speaker_catchphrase" in r]
    by_id = {r["id"]: r for r in edits}
    if not approved:
        raise ValueError("No reviewed resident catchphrase messages")
    # Leave more than 2 KiB below the test SP for nested native DMA calls.
    # The test return breakpoint is at A8E0; all live fixtures start above it.
    actors, animals = (0x8019A980, 0x8019AB00), (0x8019AD00, 0x8019B240)
    window, data, cursor, colour = 0x8019B780, 0x8019BB00, 0x8019BF40, 0x8019BF50
    snapshots = []
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]

    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})

    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})

    def call(address, arguments, result=None):
        action = {"address": f"{address:08X}", "arguments": arguments}
        if result is not None:
            action["expect_return"] = result
        actions.append({"call": action})

    for start, expected in guards:
        read(start, expected)
    for actor, animal, row in zip(actors, animals, long_rows):
        actor_data, animal_data = bytearray(0x178), bytearray(0x528)
        actor_data[2] = 3
        struct.pack_into(">I", actor_data, 0x174, animal)
        animal_data[:2] = row[4:6]
        animal_data[0x4E5:0x4E9] = row[:4]
        snapshots.append((bytes(actor_data), bytes(animal_data)))
        write(actor, actor_data)
        write(animal, animal_data)
    write(colour, bytes.fromhex("AFFFFFFF"))
    write(0x8019BF60, b"G"*16)
    cases = [(record, i % 2, False) for i, record in enumerate(approved)]
    # The same complete first message must select two different actors, retain
    # custom four-byte input, and clear the previous actor for a null request.
    cases += [(approved[0], 1, False), (approved[0], 0, True), (approved[0], None, False)]
    insertions = 0
    for record, speaker, custom in cases:
        number = int(record["id"].split(":")[1], 16)
        source_entry, entry = sources[number], entries[number]
        if entry != encode(by_id[record["id"]]["translation"], info):
            raise ValueError("Built ROM differs from the complete reviewed message")
        permit = catchphrase_permit(record["id"], source_entry, entry, matches)
        validate_entry(source_entry, entry, info, "message", "reference_layout",
                       resident_runtime=True, catchphrase_permit=permit)
        pointer = 0 if speaker is None else actors[speaker]
        phrase = b"" if speaker is None else long_rows[speaker][6:]
        if custom:
            phrase = b"Yup!"
            write(animals[speaker]+0x4E5, phrase)
        write(window-16, b"G"*16+bytes(0x330)+b"G"*16)
        write(window+12, struct.pack(">I", data))
        write(data-16, b"G"*0x430)
        if speaker is None:
            call(0x8009D308, [window, actors[1], 1])
            read(window+0x20, struct.pack(">2I", actors[1], 1))
        # No direct writes to client actor +20 or requested actor +2E0.
        call(0x8009D3E4, [window, pointer, int(pointer != 0), colour, number, 5], 1)
        read(window+0x2E0, struct.pack(">3I", pointer, number, int(pointer != 0))+bytes.fromhex("AFFFFFFF"))
        read(window+0x20, bytes(8) if speaker is not None else struct.pack(">2I", actors[1], 1))
        call(0x8009FFB0, [window, 0])
        read(window+0x20, struct.pack(">2I", pointer, int(pointer != 0)))
        read(data, struct.pack(">4I", 1, number, len(entry), 0)+entry)
        expected = entry
        while True:
            targets = [t for t in tokenize(expected, info) if t.kind == "cmd" and t.data[1] == 0x1C]
            if not targets:
                break
            token = targets[0]
            write(cursor, struct.pack(">I", token.offset))
            write(window+0x28C, bytes(4))
            call(0x800A21C0, [window, cursor], 0)
            expected = expected[:token.offset]+phrase+expected[token.offset+2:]
            read(data, struct.pack(">4I", 1, number, len(expected), 0)+expected)
            read(cursor, struct.pack(">I", token.offset))
            insertions += 1
        if custom:
            read(animals[speaker]+0x4E5, phrase)
            write(animals[speaker]+0x4E5, long_rows[speaker][:4])
        for actor, animal, (actor_data, animal_data) in zip(actors, animals, snapshots):
            read(actor, actor_data)
            read(animal, animal_data)
        for address, value in ((window-16, b"G"*16), (window+0x330, b"G"*16),
                               (data-16, b"G"*16), (data+0x410, b"G"*16)):
            read(address, value)
    read(0x8019C8D0, bytes.fromhex("AF32C0DE"*4))
    read(0x8019BF60, b"G"*16)
    actions += [{"load_state": True}, {"resume": True}, {"wait": 2}]
    read(actors[0], bytes(4))
    read(window, bytes(4))
    return actions, [r["id"] for r in approved], insertions


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--source-rom", type=Path, default=Path("local/rom/Doubutsu no Mori (Japan).z64"))
    parser.add_argument("--translations", type=Path, required=True)
    parser.add_argument("--module", type=Path, required=True)
    parser.add_argument("--reference", type=Path, default=Path("build/catchphrases/catchphrases.json"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions, ids, insertions = scenario(rom, args.source_rom.read_bytes(),
                                       json.loads(args.translations.read_text()), json.loads(args.module.read_text()),
                                       json.loads(args.reference.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"rom_sha256": sha256(rom), "actions": len(actions), "messages": ids,
                      "insertions": insertions, "output": str(args.output)}))


if __name__ == "__main__":
    main()
