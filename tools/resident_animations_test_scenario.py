#!/usr/bin/env python3
"""Generate complete reference loads and native resident animation-selection tests."""

import argparse
import json
from pathlib import Path

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from reference_animations import NPC_VROM, NPC_RELOCATION, verify_native_consumer, animation_permit
from reference_matches import load_matches
from runtime_module import module_command_info, verify_test_module
from textbanks import Bank, banks
from textcodec import encode


def scenario(rom, native, module, edits):
    native = verified_rom(native)
    verify_test_module(rom, module)
    files = by_vrom(rom)
    data, reloc = verify_native_consumer(native, {
        vrom: files[vrom].extract(rom) for vrom in (NPC_VROM, NPC_RELOCATION, CODE_VROM)})
    code = by_vrom(native)[CODE_VROM].extract(native)
    guards = {f'{start:08X}': code[start-CODE_RAM:end-CODE_RAM].hex()
              for start, end in ((0x8007B44C, 0x8007B4EC), (0x8009DF1C, 0x8009DFBC),
                                 (0x800A08F8, 0x800A0A04), (0x80107CD8, 0x80107CEC))}
    loader = native[0x800262D0-0x80025C60+0x1060:0x800263C0-0x80025C60+0x1060]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Original overlay loader changed')
    entries = Bank('message', 0x02000000, 0x00CF9000,
                   files[0x02000000].extract(rom), files[0x00CF9000].extract(rom)).entries()
    sources = next(b for b in banks(native) if b.name == 'message').entries()
    by_id = {e['id']: e for e in edits}
    matches = load_matches(Path(__file__).resolve().parents[1]/'translations/reference_matches.json')
    info, messages = module_command_info(native), {}
    for record in matches.values():
        if 'resident_animations' not in record:
            continue
        number = int(record['id'][8:], 16)
        entry = entries[number]
        if entry != encode(by_id[record['id']]['translation'], info):
            raise ValueError('Built animation dialogue differs from the complete candidate')
        animation_permit(record['id'], sources[number], entry, matches)
        messages[f'{number:04X}'] = entry.hex()
    if not messages:
        raise ValueError('No approved resident animation messages')
    request = {'source': data.hex(), 'relocation': reloc.hex(), 'loader': loader.hex(),
               'guards': guards, 'messages': messages, 'info': info}
    return [{'wait': 8}, {'save_state': True}, {'pause_game_thread': True},
            {'test_resident_animations': request}, {'load_state': True}, {'resume': True}, {'wait': 2},
            {'read': ['8019B000', 4], 'expect': '00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--native-rom', type=Path, default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module', type=Path, required=True)
    parser.add_argument('--translations', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(), args.native_rom.read_bytes(), json.loads(args.module.read_text()),
                       json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(actions, indent=2)+'\n')
    print(json.dumps({'actions': len(actions), 'output': str(args.output)}))


if __name__ == '__main__':
    main()
