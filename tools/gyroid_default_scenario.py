#!/usr/bin/env python3
"""Bind one silent cartridge-loaded gyroid-default acceptance batch."""

import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from gyroid_default import DEFAULT, native_sources
from gyroid_default_actor import ROOT, NEW_VROM, NEW_RELOCATION, verify_installation
from font import WIDTH_TABLE
from textbanks import Bank


def scenario(native, built, report):
    if sha256(built) != report['output_sha256']: raise ValueError('Changed gyroid-default cartridge')
    verify_installation(built, native, report['runtime_module'], report['gyroid_default'])
    files = by_vrom(built); code = files[CODE_VROM].extract(built)
    original_code = by_vrom(native)[CODE_VROM].extract(native)
    loader_at = 0x1060+0x800262D0-0x80025C60
    loader = native[loader_at:loader_at+0xF0]
    if (sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00'
            or built[loader_at:loader_at+0xF0] != loader):
        raise ValueError('Changed native gyroid overlay loader')
    guards = {}
    for lo, hi in ((0x8007B5C0, 0x8007B5F4), (0x80094BF4, 0x80094C44),
                   (0x800B77C4, 0x800B7820), (0x800B7914, 0x800B795C),
                   (0x8009D1F0, 0x8009D200), (0x8009E658, 0x8009E6B8)):
        expected = bytearray(original_code[lo-CODE_RAM:hi-CODE_RAM])
        if lo == 0x8009E658:
            # The installed English runtime includes its two existing helper
            # message IDs. This bound change is unrelated to the gyroid slot.
            if expected[16:20] != bytes.fromhex('28A12DE8'):
                raise ValueError('Changed original native message-count bound')
            struct.pack_into('>I', expected, 16, 0x28A12DEA)
        if code[lo-CODE_RAM:hi-CODE_RAM] != expected:
            raise ValueError('Changed native gyroid state, identity, or continuation helper')
        guards[f'{lo:08X}'] = code[lo-CODE_RAM:hi-CODE_RAM].hex()
    entries = Bank('message', 0x02000000, 0xCF9000, files[0x02000000].extract(built),
                   files[0xCF9000].extract(built)).entries()
    request = {'module': report['runtime_module'], 'actor': files[NEW_VROM].extract(built).hex(),
               'relocation': files[NEW_RELOCATION].extract(built).hex(), 'loader': loader.hex(),
               'saved_default': native_sources(native)['string'][DEFAULT].hex(), 'guards': guards,
               'font_cuts': code[WIDTH_TABLE:WIDTH_TABLE+256].hex(),
               'messages': {f'{n:04X}': entries[n].hex() for n in (0x928, 0x929, 0x2AE7)}}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True}, {'test_gyroid_default': request},
            {'load_state': True}, {'resume': True}, {'wait': 2}, {'read': ['8019B000', 4], 'expect': '00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, default=ROOT/'build/gyroid-default-pilot')
    parser.add_argument('--output', type=Path, default=ROOT/'build/gyroid-default-scenario.json')
    args = parser.parse_args()
    plan = scenario(verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()),
                    (args.build/'animal-forest-halfwidth.z64').read_bytes(),
                    json.loads((args.build/'build.json').read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, indent=2)+'\n')
    print(json.dumps({'actions': len(plan), 'scenario_sha256': sha256(args.output.read_bytes())}))


if __name__ == '__main__': main()
