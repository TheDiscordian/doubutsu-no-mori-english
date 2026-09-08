#!/usr/bin/env python3
"""Load reviewed English messages and execute their original native actor requests."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from reference_actor_requests import validate_actor_request_candidate
from reference_matches import load_matches
from reference_content import validate_content_candidate
from reference_animations import verify_native_consumer
from runtime_module import module_command_info
from textbanks import Bank, banks
from textcodec import encode, tokenize


def scenario(rom, source, edits, *, native_mood=False):
    source = verified_rom(source)
    files = by_vrom(rom)
    info = module_command_info(source)
    original_code = by_vrom(source)[CODE_VROM].extract(source)
    code = files[CODE_VROM].extract(rom)
    ranges = ((0x8007B44C, 0x8007B49C), (0x8009DF1C, 0x8009DFBC),
              (0x800A08F8, 0x800A0A04), (0x80107CD8, 0x80107CEC))
    for start, end in ranges:
        if code[start-CODE_RAM:end-CODE_RAM] != original_code[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError("Native actor-order handler, parser, setter, or dispatch table changed")
    sources = next(b for b in banks(source) if b.name == "message").entries()
    entries = Bank("message", 0x02000000, 0x00CF9000,
                   files[0x02000000].extract(rom), files[0x00CF9000].extract(rom)).entries()
    matches = load_matches(Path(__file__).resolve().parents[1]/"translations/reference_matches.json")
    approved = [r for r in matches.values() if
                ('native_mood' in r.get('complete_reference', {}) if native_mood else 'native_actor_request' in r)]
    if native_mood:
        verify_native_consumer(source, {vrom: files[vrom].extract(rom)
                                      for vrom in (CODE_VROM, 0x8681F0, 0x878550)})
    by_id = {r["id"]: r for r in edits}
    if not approved:
        raise ValueError("No approved actor-request messages")
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    window, data, cursor, orders = 0x8019B000, 0x8019B400, 0x8019B380, 0x8019B900

    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})

    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})

    def call(address, arguments, result):
        actions.append({"call": {"address": f"{address:08X}", "arguments": arguments, "expect_return": result}})

    for start, end in ranges:
        read(start, original_code[start-CODE_RAM:end-CODE_RAM])
    write(window, bytes(0x330))
    write(window+12, struct.pack(">I", data))
    # The whole machine is checkpointed and paused. No normal actor executes
    # with this temporary pointer; load_state restores it before resuming.
    write(0x80104A70, struct.pack(">I", orders))
    for record in approved:
        id = record["id"]
        number = int(id.split(":")[1], 16)
        entry = entries[number]
        if entry != encode(by_id[id]["translation"], info) or len(entry) > 0x400:
            raise ValueError("Built ROM differs from the complete approved message")
        if native_mood:
            validate_content_candidate(id, sources[number], entry, matches)
            pair = bytes.fromhex(record['complete_reference']['native_mood']['commands'])
            commands = [pair[:5], pair[5:]]
        else:
            validate_actor_request_candidate(id, sources[number], entry, matches)
            commands = [bytes.fromhex(record["native_actor_request"]["native_command"])]
        write(data-16, b"G"*0x440)
        call(0x8009E558, [data, number, 0], 1)
        read(data, struct.pack(">4I", 1, number, len(entry), 0)+entry)
        read(data-16, b"G"*16)
        read(data+0x410, b"G"*32)
        write(orders-16, b"G"*(16+216+16))
        # Header + ten rows of ten u16 entries, with adjacent guards. Only each
        # approved NPC0 row-four slot changes; all other rows stay untouched.
        expected = bytearray(b"G"*(16+216+16))
        for command in commands:
            targets = [t for t in tokenize(entry, info) if t.kind == 'cmd' and t.data == command]
            if len(targets) != 1 or command[:2] != b'\x7f\x09' or command[2] >= 10:
                raise ValueError('Expected exactly one approved bounded native NPC0 order')
            token = targets[0]
            write(cursor, struct.pack('>I', token.offset))
            call(0x800A21C0, [window, cursor], 0)
            read(cursor, struct.pack('>I', token.offset+5))
            offset = 16+16+4*20+command[2]*2
            expected[offset:offset+2] = command[3:5]
            read(orders-16, expected)
    read(0x8019C8D0, bytes.fromhex("AF32C0DE"*4))
    actions += [{"load_state": True}, {"resume": True}, {"wait": 2}]
    read(window, bytes(4))
    read(orders, bytes(216))
    return actions, [r["id"] for r in approved]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--source-rom", type=Path, default=Path("local/rom/Doubutsu no Mori (Japan).z64"))
    parser.add_argument("--translations", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument('--native-mood', action='store_true', help='Test complete restored native mood/timer pairs')
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions, ids = scenario(rom, args.source_rom.read_bytes(), json.loads(args.translations.read_text()),
                           native_mood=args.native_mood)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"rom_sha256": sha256(rom), "actions": len(actions),
                      "messages": ids, "output": str(args.output)}))


if __name__ == "__main__":
    main()
