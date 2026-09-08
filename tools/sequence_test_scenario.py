#!/usr/bin/env python3
"""Generate bounded native DMA, continuation, and termination sequence tests."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_VROM, by_vrom, sha256
from reference_sequences import load_sequences
from runtime_module import module_command_info, verify_test_module
from textbanks import Bank
from textcodec import command_info, encode, tokenize

LONG_ADVICE_GROUPS = ('rover_repeat_phone', 'resident_lazy_furniture_advice',
                      'resident_cranky_furniture_advice', 'resident_snooty_furniture_advice',
                      'resident_cranky_letter_advice')
SPECIAL_ACTOR_GROUPS = ('gracie_fashion_intro', 'redd_return_greeting', 'redd_complaint_story',
                        'jingle_holiday_intro', 'sound_settings_complete', 'gulliver_squid_story',
                        'gulliver_overseas_joke', 'gulliver_sailor_uniform', 'gulliver_life_at_sea',
                        'rover_first_housing_offer', 'rover_repeat_housing_offer')
CONTEXTUAL_ACTOR_GROUPS = ('booker_lost_property_complete', 'gulliver_weekly_falls_complete',
                           'gulliver_sea_tales_complete', 'rover_seat_refusal_complete',
                           'rover_poor_arrival_complete')
TRAIN_PHONE_GROUPS = ('rover_first_train_phone', 'rover_repeat_train_phone')
CONTINUING_END_GROUPS = ('nook_planting_complete', 'gulliver_squid_story',
                         'gulliver_overseas_joke', 'gulliver_sailor_uniform',
                         'rover_seat_refusal_complete')


def scenario(rom, group_name="nook_home_explanation", module=None):
    files = by_vrom(rom)
    info = command_info(files[CODE_VROM].extract(rom))
    bank = Bank("message", 0x02000000, 0x00CF9000,
                files[0x02000000].extract(rom), files[0x00CF9000].extract(rom))
    entries = bank.entries()
    if group_name not in ("nook_home_explanation", "nook_work_offer", "nook_house_purchase", "nook_planting_complete",
                          "resident_late_night_introduction", "native_normal_travel_advice",
                          "nook_first_renovation_invoice", *LONG_ADVICE_GROUPS,
                          *SPECIAL_ACTOR_GROUPS, *CONTEXTUAL_ACTOR_GROUPS, *TRAIN_PHONE_GROUPS):
        raise ValueError("No native scenario exists for this sequence")
    group = load_sequences()[group_name]
    if group.get('requires_resident_runtime', False):
        if module is None:
            raise ValueError('Sequence test requires the verified resident module')
        verify_test_module(rom, module)
        info = module_command_info(rom)
    members = group["members"]
    numbers = [int(member["id"].split(":")[1], 16) for member in members]
    for member, number in zip(members, numbers):
        if sha256(entries[number]) != member["encoded_sha256"]:
            raise ValueError("Test ROM does not contain the approved sequence")
    actions = [{"wait": 8}, {"save_state": True}, {"pause_game_thread": True}]
    window, data, index = 0x8019B000, 0x8019B400, 0x8019B380

    def write(address, value):
        actions.append({"write": [f"{address:08X}", value.hex()]})

    def read(address, value):
        actions.append({"read": [f"{address:08X}", len(value)], "expect": value.hex()})

    def call(address, args, result):
        actions.append({"call": {"address": f"{address:08X}", "arguments": args, "expect_return": result}})

    def load(number):
        entry = entries[number]
        write(data-16, b"G"*0x440)
        call(0x8009E558, [data, number, 0], 1)
        read(data, struct.pack(">4I", 1, number, len(entry), 0)+entry)
        read(data-16, b"G"*16)
        read(data+0x410, b"G"*32)

    def dispatch(token, result=0):
        write(index, struct.pack(">I", token.offset))
        call(0x800A21C0, [window, index], result)
        if token.data[1] not in (0, 1):
            read(index, struct.pack(">I", token.offset+len(token.data)))

    write(window, bytes(0x330))
    write(window+12, struct.pack(">I", data))
    for position, number in enumerate(numbers):
        load(number)
        commands = [t for t in tokenize(entries[number], info) if t.kind == "cmd"]
        links = [t for t in commands if t.data[1] == 0x0E]
        if position+1 < len(numbers) or links:
            if len(links) != 1:
                raise ValueError('Sequence part requires one approved continuation')
            link = links[0]
            dispatch(link)
            target = numbers[position+1] if position+1 < len(numbers) else int.from_bytes(link.data[2:], 'big')
            read(window+0x2C4, struct.pack(">I", target))
            write(window+0x28C, bytes(4))
            dispatch(commands[-1], 2)
            read(window+0x28C, struct.pack(">I", 8))
            read(window+0x2A0, struct.pack(">I", commands[-1].offset))
            dispatch(commands[-1], 1)
            read(window+0x28C, bytes(4))
        elif group_name == "nook_home_explanation":
            # Native conditional handlers consult the singleton's last selection.
            # All writes are test-only and the complete checkpoint is restored.
            for selection, target in ((0, 0x081E), (1, 0x081D)):
                write(0x80142640, struct.pack(">I", selection))
                write(window+0x2C4, b"\xff"*4)
                for token in commands:
                    if token.data[1] in (0x0F, 0x10):
                        dispatch(token)
                read(window+0x2C4, struct.pack(">I", target))
        else:
            expected_end = b"\x7f\x01" if group_name in CONTINUING_END_GROUPS else b"\x7f\x00"
            if commands[-1].data != expected_end:
                raise ValueError("Sequence must finish with its approved native terminator")
            write(window+0x28C, bytes(4))
            dispatch(commands[-1], 2)
            read(window+0x28C, struct.pack(">I", 8))
            dispatch(commands[-1], 1)
            read(window+0x28C, bytes(4))
    if group_name == "nook_home_explanation":
        # Follow the native repeat response back to the explanation's root.
        load(0x081D)
        repeat = [t for t in tokenize(entries[0x081D], info) if t.kind == "cmd" and t.data[1] == 0x0E]
        if len(repeat) != 1 or repeat[0].data != b"\x7f\x0e\x07\xea":
            raise ValueError("Native repeat response no longer returns to the root")
        dispatch(repeat[0])
        read(window+0x2C4, struct.pack(">I", 0x07EA))
    if group_name == 'nook_first_renovation_invoice':
        drafts = json.loads((Path(__file__).resolve().parents[1]/
                             'translations/n64-renovations.json').read_text())
        targets = {0x107F: (0x1080, 0x1081), 0x1081: (0x1085, 0x1085, 0x1085, 0x1086)}
        if {int(draft['id'][8:], 16) for draft in drafts} != targets.keys():
            raise ValueError('Renovation branch fixture requires its two native drafts')
        for draft in drafts:
            number = int(draft['id'][8:], 16)
            if entries[number] != encode(draft['translation'], info):
                raise ValueError('Test ROM differs from the complete native renovation draft')
            load(number)
            commands = [t for t in tokenize(entries[number], info) if t.kind == 'cmd']
            branches = [t for t in commands if 0x0F <= t.data[1] <= 0x12]
            expected = [bytes((0x7F, 0x0F+i))+target.to_bytes(2, 'big')
                        for i, target in enumerate(targets[number])]
            if [t.data for t in branches] != expected or commands[-1].data != b'\x7f\x01':
                raise ValueError('Renovation draft changes its native branch choices or terminator')
            for selection, target in enumerate(targets[number]):
                write(0x80142640, struct.pack('>I', selection))
                write(window+0x2C4, b'\xff'*4)
                for token in branches:
                    dispatch(token)
                read(window+0x2C4, struct.pack('>I', target))
            write(window+0x28C, bytes(4))
            dispatch(commands[-1], 2)
            read(window+0x28C, struct.pack('>I', 8))
            dispatch(commands[-1], 1)
            read(window+0x28C, bytes(4))
    if group_name in TRAIN_PHONE_GROUPS:
        # Exercise the real native message-change path, not only the DMA loader.
        # Page handling resets current cancellation; the persistent enable word
        # must survive a continuation with either current cancellation state.
        if len(numbers) != 2 or module is None:
            raise ValueError('Train phone state test requires two complete resident-runtime parts')
        for active_cancel in (0, 1):
            write(window, bytes(0x330))
            write(window+12, struct.pack('>I', data))
            load(numbers[0])
            first = {t.data[1]: t for t in tokenize(entries[numbers[0]], info)
                     if t.kind == 'cmd' and t.data[1] in (0x72, 0x73, 6)}
            if set(first) != {0x72, 0x73, 6}:
                raise ValueError('Train phone opening loses pacing/cancellation controls')
            dispatch(first[0x72]); read(window+0x28C, struct.pack('>I', 0x4000))
            dispatch(first[0x73]); read(window+0x28C, bytes(4))
            dispatch(first[6]); read(window+0x2C0, struct.pack('>I', 1))
            write(window+0x2BC, struct.pack('>I', active_cancel))
            call(0x8009E658, [window, numbers[1]], 1)
            entry = entries[numbers[1]]
            read(data, struct.pack('>4I', 1, numbers[1], len(entry), 0)+entry)
            read(data-16, b'G'*16); read(data+0x410, b'G'*32)
            read(window+0x2BC, struct.pack('>2I', active_cancel, 1))
            read(window+0x28C, bytes(4))
            read(window+0x29C, bytes(8))
            read(window+0x294, struct.pack('>f', 10.0))
            actions.append({'call': {'address': '800A04E4', 'arguments': [window, 0]}})
            read(window+0x2BC, struct.pack('>2I', 0, 1))
            write(window+0x2BC, struct.pack('>I', active_cancel))
            last = [t for t in tokenize(entry, info) if t.kind == 'cmd' and t.data[1] == 7]
            if len(last) != 1:
                raise ValueError('Train phone ending loses native cancellation reset')
            dispatch(last[0]); read(window+0x2BC, bytes(8))
    actions += [{"read": ["8019C8D0", 16], "expect": "AF32C0DE"*4},
                {"load_state": True}, {"resume": True}, {"wait": 2},
                {"read": ["8019B000", 4], "expect": "00000000"}]
    return actions


def batch_scenario(rom, group_names, module=None):
    """Check several approved sequences in one isolated machine checkpoint."""
    if not group_names or len(set(group_names)) != len(group_names):
        raise ValueError('Sequence batch requires distinct named groups')
    result, prefix, suffix = [], None, None
    for name in group_names:
        actions = scenario(rom, name, module)
        if prefix is None:
            prefix, suffix = actions[:3], actions[-5:]
            result.extend(prefix)
        elif actions[:3] != prefix or actions[-5:] != suffix:
            raise ValueError('Sequence checkpoint setup or restoration differs')
        result.extend(actions[3:-5])
    return result+suffix


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--sequence", action='append', help='Repeat to batch approved groups in one checkpoint')
    parser.add_argument('--module', type=Path)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions = batch_scenario(rom, args.sequence or ['nook_home_explanation'],
                             json.loads(args.module.read_text()) if args.module else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+"\n")
    print(json.dumps({"rom_sha256": sha256(rom), "actions": len(actions), "output": str(args.output)}))


if __name__ == "__main__":
    main()
