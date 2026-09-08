#!/usr/bin/env python3
"""Source-bound actual cartridge fortune preparation and text insertion batch."""

import argparse
import json
from pathlib import Path

from aflib import by_vrom, sha256, verified_rom
from birthday_smoke import RNG_START, RNG_END, RNG_SHA256
from fortune_strings import (VROM, RELOC_VROM, FIRST, END, STRING_RELOCATION,
                             permits, patch, verify_values)
from runtime_module import module_command_info, verify_test_module
from textbanks import Bank
from textcodec import encode


def scenario(rom, native, module, edits):
    native = verified_rom(native)
    verify_test_module(rom,module)
    info = module_command_info(native)
    permits(native,edits,info)
    source, files = by_vrom(native), by_vrom(rom)
    original, reloc = source[VROM].extract(native), source[RELOC_VROM].extract(native)
    if files[VROM].extract(rom) != patch(original,reloc) or files[RELOC_VROM].extract(rom) != reloc:
        raise ValueError('Fortune test requires the complete cartridge caller patch')
    entries = Bank('string',STRING_RELOCATION[0],0xD18000,
                   files[STRING_RELOCATION[0]].extract(rom),files[0xD18000].extract(rom)).entries()
    verify_values(entries[FIRST:END],info)
    by_id = {e['id']:e for e in edits}
    for index,value in enumerate(entries):
        id = f'string:{index:04X}'
        if id in by_id and value != encode(by_id[id]['translation'],info):
            raise ValueError('Installed general string differs from the candidate')
    messages = Bank('message',0x02000000,0xCF9000,
                    files[0x02000000].extract(rom),files[0xCF9000].extract(rom)).entries()
    entry = encode(by_id['message:0973']['translation'],info)
    if messages[0x973] != entry: raise ValueError('Installed complete fortune message differs')
    loader_at = 0x1060+0x800262D0-0x80025C60
    loader = native[loader_at:loader_at+0xF0]
    if sha256(loader) != '2c3176abe096fa667cd77599844acff5e0f46507ddbe1e95bbc1caf90a7d2b00':
        raise ValueError('Unexpected native overlay loader')
    rng_at = 0x1060+RNG_START-0x80025C60
    rng = native[rng_at:rng_at+RNG_END-RNG_START]
    if sha256(rng) != RNG_SHA256 or rom[rng_at:rng_at+len(rng)] != rng:
        raise ValueError('Unexpected native RNG')
    request = {'source':original.hex(),'relocation':reloc.hex(),'loader':loader.hex(),
               'rng':rng.hex(),'strings':[value.hex() for value in entries],
               'message':entry.hex(),'info':info}
    return [{'wait':8},{'save_state':True},{'pause_game_thread':True},{'test_fortunes':request},
            {'load_state':True},{'resume':True},{'wait':2},
            {'read':['8019B000',4],'expect':'00000000'}]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,required=True)
    parser.add_argument('--native-rom',type=Path,default=Path('local/rom/Doubutsu no Mori (Japan).z64'))
    parser.add_argument('--module',type=Path,required=True)
    parser.add_argument('--translations',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    actions = scenario(args.rom.read_bytes(),args.native_rom.read_bytes(),
                       json.loads(args.module.read_text()),json.loads(args.translations.read_text()))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(actions,indent=2)+'\n')
    print(json.dumps({'actions':len(actions),'phrases':128,'native_preparations':128,
                      'complete_readings':32,'output':str(args.output)}))


if __name__ == '__main__': main()
