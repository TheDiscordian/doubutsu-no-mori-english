#!/usr/bin/env python3
"""Verify cartridge date preparation and its complete native festival messages."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from dialogue_dates import SPEC, patch
from npc_mail_show import source
from runtime_module import module_command_info, verify_test_module
from textbanks import Bank
from textcodec import encode


def scenario(rom, native, module, edits):
    native = verified_rom(native)
    verify_test_module(rom, module)
    data, reloc = source(native, 'ordinary')
    expected, expected_reloc = patch(data, reloc, module)
    files = by_vrom(rom)
    if files[SPEC.vrom].extract(rom) != expected or files[SPEC.relocation].extract(rom) != expected_reloc:
        raise ValueError('Native date test requires both complete cartridge patches')
    original = by_vrom(native)[CODE_VROM].extract(native)
    code = files[CODE_VROM].extract(rom)
    guards = {}
    for start, end in ((0x8009D6D0, 0x8009D7E8), (0x800A134C, 0x800A1390),
                       (0x800A1690, 0x800A16E0), (0x800D5D00, 0x800D64E0)):
        value = original[start-CODE_RAM:end-CODE_RAM]
        if code[start-CODE_RAM:end-CODE_RAM] != value:
            raise ValueError('Native calendar or free-string consumer changed')
        guards[f'{start:08X}'] = value.hex()
    loader = native[0x800262D0-0x80025C60+0x1060:0x800263C0-0x80025C60+0x1060]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Original overlay loader changed')
    entries = Bank('message', 0x02000000, 0x00CF9000,
                   files[0x02000000].extract(rom), files[0x00CF9000].extract(rom)).entries()
    by_id = {r['id']: r for r in edits}
    info = module_command_info(native)
    messages = {}
    for number in (0x119C, 0x27C0, 0x11AC, 0x180B):
        if entries[number] != encode(by_id[f'message:{number:04X}']['translation'], info):
            raise ValueError('Native festival cartridge text differs from the candidate')
        messages[f'{number:04X}'] = entries[number].hex()
    request = {'source': data.hex(), 'relocation': reloc.hex(), 'module': module,
               'loader': loader.hex(), 'guards': guards, 'messages': messages, 'info': info}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True},
            {'test_dialogue_dates': request}, {'load_state': True}, {'resume': True}, {'wait': 2},
            {'read': ['8019B000', 4], 'expect': '00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rom = args.rom.read_bytes()
    actions = scenario(rom, args.native_rom.read_bytes(), json.loads(args.module.read_text()),
                       json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'rom_sha256': sha256(rom), 'actions': len(actions), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
